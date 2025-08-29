/**
 * 实时监控组件
 * 
 * 显示策略训练的实时状态、进度和性能指标
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  Progress,
  Statistic,
  Row,
  Col,
  Timeline,
  Badge,
  Button,
  Space,
  Spin,
  Alert,
  Tabs,
  Table,
  message
} from 'antd';
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  StopOutlined,
  SyncOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  CloseCircleOutlined
} from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';

import { websocketManager, SessionStatusData, TrainingProgressData, PerformanceMetricsData, ResourceUsageData } from '../../services/websocket';

interface RealTimeMonitorProps {
  sessionId: number;
  strategyId: number;
  onSessionStopped?: () => void;
}

interface MetricHistory {
  timestamp: string;
  [key: string]: any;
}

const { TabPane } = Tabs;

const RealTimeMonitor: React.FC<RealTimeMonitorProps> = ({
  sessionId,
  strategyId,
  onSessionStopped
}) => {
  const [sessionStatus, setSessionStatus] = useState<SessionStatusData | null>(null);
  const [trainingProgress, setTrainingProgress] = useState<TrainingProgressData | null>(null);
  const [performanceMetrics, setPerformanceMetrics] = useState<PerformanceMetricsData>({});
  const [resourceUsage, setResourceUsage] = useState<ResourceUsageData>({});
  const [metricsHistory, setMetricsHistory] = useState<MetricHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  /**
   * 处理WebSocket连接状态
   */
  const handleConnectionStatus = useCallback(() => {
    setIsConnected(websocketManager.isConnected);
    
    if (!websocketManager.isConnected) {
      setError('WebSocket连接已断开');
    } else {
      setError(null);
    }
  }, []);

  /**
   * 处理会话状态更新
   */
  const handleSessionStatusUpdate = useCallback((message: any) => {
    if (message.session_id === sessionId) {
      setSessionStatus(message.data);
      setLoading(false);
      setError(null);
    }
  }, [sessionId]);

  /**
   * 处理训练进度更新
   */
  const handleTrainingProgress = useCallback((message: any) => {
    if (message.session_id === sessionId) {
      setTrainingProgress(message.data);
    }
  }, [sessionId]);

  /**
   * 处理性能指标更新
   */
  const handlePerformanceMetrics = useCallback((message: any) => {
    if (message.session_id === sessionId) {
      const newMetrics = message.data;
      setPerformanceMetrics(newMetrics);
      
      // 更新历史数据
      setMetricsHistory(prev => {
        const newEntry = {
          timestamp: new Date().toLocaleTimeString(),
          ...newMetrics
        };
        
        // 只保留最近50个数据点
        const updated = [...prev, newEntry].slice(-50);
        return updated;
      });
    }
  }, [sessionId]);

  /**
   * 处理资源使用更新
   */
  const handleResourceUsage = useCallback((message: any) => {
    if (message.session_id === sessionId) {
      setResourceUsage(message.data);
    }
  }, [sessionId]);

  /**
   * 停止训练会话
   */
  const handleStopSession = async () => {
    try {
      const response = await fetch(`/api/v1/strategies/${strategyId}/stop`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ session_id: sessionId })
      });

      if (response.ok) {
        message.success('会话停止成功');
        onSessionStopped?.();
      } else {
        const errorData = await response.json();
        message.error(errorData.detail || '停止会话失败');
      }
    } catch (error) {
      console.error('停止会话失败:', error);
      message.error('停止会话失败');
    }
  };

  /**
   * 获取状态颜色和图标
   */
  const getStatusInfo = (status: string) => {
    switch (status) {
      case 'pending':
        return { color: 'gold', icon: <SyncOutlined spin /> };
      case 'running':
        return { color: 'blue', icon: <PlayCircleOutlined /> };
      case 'completed':
        return { color: 'green', icon: <CheckCircleOutlined /> };
      case 'failed':
        return { color: 'red', icon: <CloseCircleOutlined /> };
      case 'cancelled':
        return { color: 'gray', icon: <ExclamationCircleOutlined /> };
      default:
        return { color: 'default', icon: <SyncOutlined /> };
    }
  };

  /**
   * 格式化时间
   */
  const formatDuration = (seconds: number): string => {
    if (seconds < 60) return `${seconds}秒`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}分${seconds % 60}秒`;
    return `${Math.floor(seconds / 3600)}小时${Math.floor((seconds % 3600) / 60)}分`;
  };

  useEffect(() => {
    // 订阅WebSocket消息
    websocketManager.on('session_status_update', handleSessionStatusUpdate);
    websocketManager.on('current_session_status', handleSessionStatusUpdate);
    websocketManager.on('training_progress', handleTrainingProgress);
    websocketManager.on('performance_metrics', handlePerformanceMetrics);
    websocketManager.on('resource_usage', handleResourceUsage);

    // 订阅会话更新
    websocketManager.subscribeToSession(sessionId);
    
    // 检查连接状态
    handleConnectionStatus();
    
    // 监听连接状态变化
    const checkConnection = setInterval(handleConnectionStatus, 1000);

    return () => {
      // 取消订阅
      websocketManager.unsubscribeFromSession(sessionId);
      websocketManager.off('session_status_update', handleSessionStatusUpdate);
      websocketManager.off('current_session_status', handleSessionStatusUpdate);
      websocketManager.off('training_progress', handleTrainingProgress);
      websocketManager.off('performance_metrics', handlePerformanceMetrics);
      websocketManager.off('resource_usage', handleResourceUsage);
      
      clearInterval(checkConnection);
    };
  }, [sessionId, handleSessionStatusUpdate, handleTrainingProgress, handlePerformanceMetrics, handleResourceUsage, handleConnectionStatus]);

  if (loading) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <Spin size="large" />
          <div style={{ marginTop: 16 }}>正在连接实时监控...</div>
        </div>
      </Card>
    );
  }

  if (error && !sessionStatus) {
    return (
      <Card>
        <Alert
          message="连接错误"
          description={error}
          type="error"
          showIcon
          action={
            <Button size="small" onClick={() => window.location.reload()}>
              重新加载
            </Button>
          }
        />
      </Card>
    );
  }

  const statusInfo = getStatusInfo(sessionStatus?.status || 'unknown');
  const progress = trainingProgress?.progress_percentage || sessionStatus?.progress || 0;

  return (
    <div>
      {/* 连接状态提示 */}
      {!isConnected && (
        <Alert
          message="实时连接已断开"
          description="正在尝试重新连接..."
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      {/* 状态概览 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="会话状态"
              value={sessionStatus?.status || '未知'}
              prefix={statusInfo.icon}
            />
          </Card>
        </Col>
        
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="训练进度"
              value={progress}
              suffix="%"
              precision={1}
            />
            <Progress percent={progress} size="small" style={{ marginTop: 8 }} />
          </Card>
        </Col>
        
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="当前轮次"
              value={`${sessionStatus?.current_epoch || 0}/${sessionStatus?.total_epochs || '?'}`}
            />
          </Card>
        </Col>
        
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Space>
              {(sessionStatus?.status === 'running' || sessionStatus?.status === 'pending') && (
                <Button
                  type="primary"
                  danger
                  icon={<StopOutlined />}
                  onClick={handleStopSession}
                >
                  停止训练
                </Button>
              )}
              
              <Badge status={isConnected ? 'success' : 'error'} />
              {isConnected ? '已连接' : '连接断开'}
            </Space>
          </Card>
        </Col>
      </Row>

      {/* 详细信息标签页 */}
      <Tabs defaultActiveKey="metrics">
        <TabPane tab="性能指标" key="metrics">
          <Row gutter={[16, 16]}>
            {/* 实时指标卡片 */}
            {Object.entries(performanceMetrics).map(([key, value]) => (
              <Col xs={24} sm={12} md={8} lg={6} key={key}>
                <Card size="small">
                  <Statistic
                    title={key}
                    value={typeof value === 'number' ? value : 0}
                    precision={4}
                  />
                </Card>
              </Col>
            ))}
          </Row>
          
          {/* 指标历史图表 */}
          {metricsHistory.length > 0 && (
            <Card title="指标趋势" style={{ marginTop: 16 }}>
              <ReactECharts
                option={{
                  title: {
                    text: '指标趋势',
                    show: false
                  },
                  tooltip: {
                    trigger: 'axis',
                    axisPointer: {
                      type: 'cross'
                    }
                  },
                  legend: {
                    data: Object.keys(performanceMetrics),
                    bottom: 0
                  },
                  grid: {
                    left: '3%',
                    right: '4%',
                    bottom: '10%',
                    containLabel: true
                  },
                  xAxis: {
                    type: 'category',
                    boundaryGap: false,
                    data: metricsHistory.map(item => item.timestamp)
                  },
                  yAxis: {
                    type: 'value'
                  },
                  series: Object.keys(performanceMetrics).map((key, index) => ({
                    name: key,
                    type: 'line',
                    symbol: 'none',
                    smooth: true,
                    data: metricsHistory.map(item => item[key] || 0),
                    lineStyle: {
                      width: 2
                    },
                    itemStyle: {
                      color: `hsl(${index * 60}, 70%, 50%)`
                    }
                  }))
                }}
                style={{ height: '300px', width: '100%' }}
                opts={{ renderer: 'canvas' }}
              />
            </Card>
          )}
        </TabPane>
        
        <TabPane tab="资源监控" key="resources">
          <Row gutter={[16, 16]}>
            {resourceUsage.cpu_percent && (
              <Col xs={24} sm={12} md={6}>
                <Card>
                  <Statistic
                    title="CPU使用率"
                    value={resourceUsage.cpu_percent}
                    suffix="%"
                    precision={1}
                  />
                  <Progress percent={resourceUsage.cpu_percent} size="small" />
                </Card>
              </Col>
            )}
            
            {resourceUsage.memory_mb && (
              <Col xs={24} sm={12} md={6}>
                <Card>
                  <Statistic
                    title="内存使用"
                    value={resourceUsage.memory_mb}
                    suffix="MB"
                  />
                </Card>
              </Col>
            )}
            
            {resourceUsage.gpu_percent && (
              <Col xs={24} sm={12} md={6}>
                <Card>
                  <Statistic
                    title="GPU使用率"
                    value={resourceUsage.gpu_percent}
                    suffix="%"
                    precision={1}
                  />
                  <Progress percent={resourceUsage.gpu_percent} size="small" />
                </Card>
              </Col>
            )}
            
            {resourceUsage.gpu_memory_mb && (
              <Col xs={24} sm={12} md={6}>
                <Card>
                  <Statistic
                    title="GPU内存"
                    value={resourceUsage.gpu_memory_mb}
                    suffix="MB"
                  />
                </Card>
              </Col>
            )}
          </Row>
        </TabPane>
        
        <TabPane tab="会话详情" key="details">
          <Card title="会话信息">
            <Row gutter={[16, 16]}>
              <Col span={12}>
                <p><strong>会话ID:</strong> {sessionId}</p>
                <p><strong>策略ID:</strong> {strategyId}</p>
                <p><strong>状态:</strong> 
                  <Badge color={statusInfo.color} />
                  {sessionStatus?.status}
                </p>
              </Col>
              <Col span={12}>
                <p><strong>开始时间:</strong> {sessionStatus?.started_at ? new Date(sessionStatus.started_at).toLocaleString() : '未知'}</p>
                <p><strong>当前轮次:</strong> {sessionStatus?.current_epoch || 0}</p>
                <p><strong>总轮次:</strong> {sessionStatus?.total_epochs || '未知'}</p>
              </Col>
            </Row>
            
            {/* 最近指标 */}
            {sessionStatus?.recent_metrics && sessionStatus.recent_metrics.length > 0 && (
              <div style={{ marginTop: 16 }}>
                <h4>最近指标</h4>
                <Table
                  size="small"
                  dataSource={sessionStatus.recent_metrics}
                  columns={[
                    {
                      title: '指标名称',
                      dataIndex: 'metric_name',
                      key: 'metric_name'
                    },
                    {
                      title: '指标值',
                      dataIndex: 'metric_value',
                      key: 'metric_value',
                      render: (value: number) => value.toFixed(4)
                    },
                    {
                      title: '轮次',
                      dataIndex: 'epoch',
                      key: 'epoch'
                    },
                    {
                      title: '记录时间',
                      dataIndex: 'recorded_at',
                      key: 'recorded_at',
                      render: (time: string) => new Date(time).toLocaleTimeString()
                    }
                  ]}
                  pagination={false}
                  scroll={{ y: 200 }}
                />
              </div>
            )}
          </Card>
        </TabPane>
      </Tabs>
    </div>
  );
};

export default RealTimeMonitor;