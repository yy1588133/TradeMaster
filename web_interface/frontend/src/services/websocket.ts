/**
 * WebSocket连接管理器
 * 
 * 提供WebSocket连接管理、消息处理和实时数据推送功能
 */

import { message } from 'antd';

export interface WebSocketMessage {
  type: string;
  session_id?: number;
  data?: any;
  message?: string;
  timestamp: string;
  connection_id?: string;
}

export interface SessionStatusData {
  session_id: number;
  status: string;
  progress: number;
  current_epoch: number;
  total_epochs?: number;
  started_at?: string;
  recent_metrics?: Array<{
    metric_name: string;
    metric_value: number;
    epoch?: number;
    recorded_at: string;
  }>;
}

export interface TrainingProgressData {
  current_epoch: number;
  total_epochs?: number;
  progress_percentage: number;
  estimated_remaining?: number;
}

export interface PerformanceMetricsData {
  [key: string]: number;
}

export interface ResourceUsageData {
  cpu_percent?: number;
  memory_mb?: number;
  gpu_percent?: number;
  gpu_memory_mb?: number;
  disk_io_mb?: number;
  network_io_mb?: number;
}

export type MessageHandler = (message: WebSocketMessage) => void;

class WebSocketManager {
  private websocket: WebSocket | null = null;
  private connectionId: string | null = null;
  private userId: number | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectInterval = 3000; // 3秒
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private messageHandlers: Map<string, MessageHandler[]> = new Map();
  private isConnecting = false;
  private subscribedSessions: Set<number> = new Set();

  constructor() {
    this.setupMessageHandlers();
  }

  /**
   * 连接WebSocket
   */
  async connect(userId: number, token?: string): Promise<boolean> {
    if (this.isConnecting || (this.websocket && this.websocket.readyState === WebSocket.OPEN)) {
      return true;
    }

    this.isConnecting = true;
    this.userId = userId;

    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      const wsUrl = `${protocol}//${host}/api/v1/ws/ws?user_id=${userId}${token ? `&token=${token}` : ''}`;

      console.log('连接WebSocket:', wsUrl);

      this.websocket = new WebSocket(wsUrl);

      return new Promise((resolve, reject) => {
        if (!this.websocket) {
          reject(new Error('WebSocket创建失败'));
          return;
        }

        const timeout = setTimeout(() => {
          reject(new Error('WebSocket连接超时'));
        }, 10000);

        this.websocket.onopen = () => {
          console.log('WebSocket连接已建立');
          clearTimeout(timeout);
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.startHeartbeat();
          resolve(true);
        };

        this.websocket.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('解析WebSocket消息失败:', error);
          }
        };

        this.websocket.onclose = (event) => {
          console.log('WebSocket连接已关闭:', event.code, event.reason);
          clearTimeout(timeout);
          this.isConnecting = false;
          this.stopHeartbeat();

          if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.scheduleReconnect();
          }
        };

        this.websocket.onerror = (error) => {
          console.error('WebSocket连接错误:', error);
          clearTimeout(timeout);
          this.isConnecting = false;
          reject(error);
        };
      });
    } catch (error) {
      this.isConnecting = false;
      throw error;
    }
  }

  /**
   * 断开WebSocket连接
   */
  disconnect(): void {
    this.stopHeartbeat();
    
    if (this.websocket) {
      this.websocket.close(1000, '手动断开连接');
      this.websocket = null;
    }
    
    this.connectionId = null;
    this.subscribedSessions.clear();
  }

  /**
   * 订阅会话更新
   */
  subscribeToSession(sessionId: number): void {
    if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
      const message = {
        type: 'subscribe',
        session_id: sessionId
      };
      
      this.websocket.send(JSON.stringify(message));
      this.subscribedSessions.add(sessionId);
      console.log(`已订阅会话 ${sessionId}`);
    } else {
      console.warn('WebSocket未连接，无法订阅会话');
    }
  }

  /**
   * 取消订阅会话
   */
  unsubscribeFromSession(sessionId: number): void {
    if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
      const message = {
        type: 'unsubscribe',
        session_id: sessionId
      };
      
      this.websocket.send(JSON.stringify(message));
      this.subscribedSessions.delete(sessionId);
      console.log(`已取消订阅会话 ${sessionId}`);
    }
  }

  /**
   * 添加消息处理器
   */
  on(messageType: string, handler: MessageHandler): void {
    if (!this.messageHandlers.has(messageType)) {
      this.messageHandlers.set(messageType, []);
    }
    this.messageHandlers.get(messageType)!.push(handler);
  }

  /**
   * 移除消息处理器
   */
  off(messageType: string, handler: MessageHandler): void {
    const handlers = this.messageHandlers.get(messageType);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  /**
   * 获取连接状态
   */
  get isConnected(): boolean {
    return this.websocket?.readyState === WebSocket.OPEN;
  }

  /**
   * 获取连接ID
   */
  get getConnectionId(): string | null {
    return this.connectionId;
  }

  /**
   * 处理WebSocket消息
   */
  private handleMessage(message: WebSocketMessage): void {
    console.log('收到WebSocket消息:', message);

    // 处理连接建立消息
    if (message.type === 'connection_established') {
      this.connectionId = message.connection_id || null;
      
      // 重新订阅之前订阅的会话
      for (const sessionId of this.subscribedSessions) {
        this.subscribeToSession(sessionId);
      }
    }

    // 触发对应的处理器
    const handlers = this.messageHandlers.get(message.type);
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(message);
        } catch (error) {
          console.error('消息处理器执行失败:', error);
        }
      });
    }
  }

  /**
   * 设置默认消息处理器
   */
  private setupMessageHandlers(): void {
    // 错误消息处理
    this.on('error', (message) => {
      console.error('WebSocket错误:', message.message);
      message.error(message.message || '发生未知错误');
    });

    // 系统广播消息处理
    this.on('system_broadcast', (message) => {
      console.log('系统广播:', message.message);
      message.info(message.message || '系统消息');
    });

    // 会话状态更新处理
    this.on('session_status_update', (message) => {
      console.log('会话状态更新:', message.data);
    });

    // 训练进度更新处理
    this.on('training_progress', (message) => {
      console.log('训练进度更新:', message.data);
    });

    // 性能指标更新处理
    this.on('performance_metrics', (message) => {
      console.log('性能指标更新:', message.data);
    });

    // 资源使用更新处理
    this.on('resource_usage', (message) => {
      console.log('资源使用更新:', message.data);
    });
  }

  /**
   * 开始心跳检测
   */
  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
        this.websocket.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000); // 30秒心跳
  }

  /**
   * 停止心跳检测
   */
  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  /**
   * 计划重连
   */
  private scheduleReconnect(): void {
    this.reconnectAttempts++;
    console.log(`计划重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

    setTimeout(() => {
      if (this.userId) {
        this.connect(this.userId).catch(error => {
          console.error('重连失败:', error);
        });
      }
    }, this.reconnectInterval * this.reconnectAttempts);
  }
}

// 全局WebSocket管理器实例
export const websocketManager = new WebSocketManager();

// 导出类型和管理器
export default WebSocketManager;