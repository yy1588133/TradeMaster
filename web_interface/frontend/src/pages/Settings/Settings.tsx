/**
 * 设置页面组件
 * 
 * 提供系统配置、用户偏好设置和TradeMaster集成配置管理
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Form,
  Input,
  Select,
  Switch,
  Button,
  Tabs,
  Space,
  message,
  Divider,
  InputNumber,
  Row,
  Col,
  Alert,
  Spin
} from 'antd';
import {
  SaveOutlined,
  ReloadOutlined,
  SettingOutlined,
  UserOutlined,
  ApiOutlined,
  BellOutlined,
  SecurityScanOutlined
} from '@ant-design/icons';

import { websocketManager } from '../../services/websocket';

const { TabPane } = Tabs;
const { Option } = Select;

interface UserSettings {
  username: string;
  email: string;
  timezone: string;
  language: string;
  theme: string;
  notifications_enabled: boolean;
  email_notifications: boolean;
}

interface TradeMasterSettings {
  api_endpoint: string;
  timeout: number;
  max_concurrent_sessions: number;
  default_initial_capital: number;
  default_commission_rate: number;
  enable_gpu: boolean;
  log_level: string;
}

interface SystemSettings {
  websocket_enabled: boolean;
  websocket_reconnect: boolean;
  cache_enabled: boolean;
  session_timeout: number;
  max_file_size: number;
}

const Settings: React.FC = () => {
  const [userForm] = Form.useForm();
  const [tradeMasterForm] = Form.useForm();
  const [systemForm] = Form.useForm();
  
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [userSettings, setUserSettings] = useState<UserSettings | null>(null);
  const [tradeMasterSettings, setTradeMasterSettings] = useState<TradeMasterSettings | null>(null);
  const [systemSettings, setSystemSettings] = useState<SystemSettings | null>(null);
  const [wsConnected, setWsConnected] = useState(false);

  /**
   * 加载设置数据
   */
  const loadSettings = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      
      // 加载用户设置
      const userResponse = await fetch('/api/v1/users/settings', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (userResponse.ok) {
        const userData = await userResponse.json();
        setUserSettings(userData);
        userForm.setFieldsValue(userData);
      }
      
      // 加载TradeMaster设置
      const tradeMasterResponse = await fetch('/api/v1/settings/trademaster', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (tradeMasterResponse.ok) {
        const tradeMasterData = await tradeMasterResponse.json();
        setTradeMasterSettings(tradeMasterData);
        tradeMasterForm.setFieldsValue(tradeMasterData);
      }
      
      // 加载系统设置
      const systemResponse = await fetch('/api/v1/settings/system', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (systemResponse.ok) {
        const systemData = await systemResponse.json();
        setSystemSettings(systemData);
        systemForm.setFieldsValue(systemData);
      }
      
    } catch (error) {
      console.error('加载设置失败:', error);
      message.error('加载设置失败');
    } finally {
      setLoading(false);
    }
  };

  /**
   * 保存用户设置
   */
  const saveUserSettings = async (values: UserSettings) => {
    setSaving(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/v1/users/settings', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(values)
      });

      if (response.ok) {
        setUserSettings(values);
        message.success('用户设置保存成功');
      } else {
        const errorData = await response.json();
        message.error(errorData.detail || '保存用户设置失败');
      }
    } catch (error) {
      console.error('保存用户设置失败:', error);
      message.error('保存用户设置失败');
    } finally {
      setSaving(false);
    }
  };

  /**
   * 保存TradeMaster设置
   */
  const saveTradeMasterSettings = async (values: TradeMasterSettings) => {
    setSaving(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/v1/settings/trademaster', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(values)
      });

      if (response.ok) {
        setTradeMasterSettings(values);
        message.success('TradeMaster设置保存成功');
      } else {
        const errorData = await response.json();
        message.error(errorData.detail || '保存TradeMaster设置失败');
      }
    } catch (error) {
      console.error('保存TradeMaster设置失败:', error);
      message.error('保存TradeMaster设置失败');
    } finally {
      setSaving(false);
    }
  };

  /**
   * 保存系统设置
   */
  const saveSystemSettings = async (values: SystemSettings) => {
    setSaving(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/v1/settings/system', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(values)
      });

      if (response.ok) {
        setSystemSettings(values);
        message.success('系统设置保存成功');
        
        // 如果WebSocket设置发生变化，重新连接
        if (values.websocket_enabled !== systemSettings?.websocket_enabled) {
          if (values.websocket_enabled) {
            const user = JSON.parse(localStorage.getItem('user') || '{}');
            await websocketManager.connect(user.id, localStorage.getItem('token') || '');
          } else {
            websocketManager.disconnect();
          }
        }
      } else {
        const errorData = await response.json();
        message.error(errorData.detail || '保存系统设置失败');
      }
    } catch (error) {
      console.error('保存系统设置失败:', error);
      message.error('保存系统设置失败');
    } finally {
      setSaving(false);
    }
  };

  /**
   * 测试TradeMaster连接
   */
  const testTradeMasterConnection = async () => {
    try {
      const values = tradeMasterForm.getFieldsValue();
      const token = localStorage.getItem('token');
      
      const response = await fetch('/api/v1/settings/trademaster/test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(values)
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          message.success('TradeMaster连接测试成功');
        } else {
          message.error(`TradeMaster连接测试失败: ${result.error}`);
        }
      } else {
        const errorData = await response.json();
        message.error(errorData.detail || 'TradeMaster连接测试失败');
      }
    } catch (error) {
      console.error('TradeMaster连接测试失败:', error);
      message.error('TradeMaster连接测试失败');
    }
  };

  /**
   * 检查WebSocket连接状态
   */
  const checkWebSocketStatus = () => {
    setWsConnected(websocketManager.isConnected);
  };

  useEffect(() => {
    loadSettings();
    
    // 检查WebSocket状态
    checkWebSocketStatus();
    const wsStatusInterval = setInterval(checkWebSocketStatus, 1000);
    
    return () => {
      clearInterval(wsStatusInterval);
    };
  }, []);

  if (loading) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <Spin size="large" />
          <div style={{ marginTop: 16 }}>正在加载设置...</div>
        </div>
      </Card>
    );
  }






  return (
    <div style={{ padding: '24px' }}>
      <Card title={
        <Space>
          <SettingOutlined />
          系统设置
        </Space>
      }>
        <Tabs defaultActiveKey="user">
          {/* 用户设置 */}
          <TabPane 
            tab={
              <Space>
                <UserOutlined />
                用户设置
              </Space>
            } 
            key="user"
          >
            <Form
              form={userForm}
              layout="vertical"
              onFinish={saveUserSettings}
            >
              <Row gutter={[16, 16]}>
                <Col xs={24} md={12}>
                  <Form.Item
                    label="用户名"
                    name="username"
                    rules={[
                      { required: true, message: '请输入用户名' },
                      { min: 3, message: '用户名至少3个字符' }
                    ]}
                  >
                    <Input placeholder="请输入用户名" />
                  </Form.Item>
                </Col>
                
                <Col xs={24} md={12}>
                  <Form.Item
                    label="邮箱"
                    name="email"
                    rules={[
                      { required: true, message: '请输入邮箱' },
                      { type: 'email', message: '请输入有效的邮箱地址' }
                    ]}
                  >
                    <Input placeholder="请输入邮箱" />
                  </Form.Item>
                </Col>
                
                <Col xs={24} md={12}>
                  <Form.Item
                    label="时区"
                    name="timezone"
                    rules={[{ required: true, message: '请选择时区' }]}
                  >
                    <Select placeholder="请选择时区">
                      <Option value="Asia/Shanghai">Asia/Shanghai (UTC+8)</Option>
                      <Option value="America/New_York">America/New_York (UTC-5)</Option>
                      <Option value="Europe/London">Europe/London (UTC+0)</Option>
                      <Option value="Asia/Tokyo">Asia/Tokyo (UTC+9)</Option>
                    </Select>
                  </Form.Item>
                </Col>
                
                <Col xs={24} md={12}>
                  <Form.Item
                    label="语言"
                    name="language"
                    rules={[{ required: true, message: '请选择语言' }]}
                  >
                    <Select placeholder="请选择语言">
                      <Option value="zh-CN">中文简体</Option>
                      <Option value="zh-TW">中文繁体</Option>
                      <Option value="en-US">English</Option>
                    </Select>
                  </Form.Item>
                </Col>
                
                <Col xs={24} md={12}>
                  <Form.Item
                    label="主题"
                    name="theme"
                    rules={[{ required: true, message: '请选择主题' }]}
                  >
                    <Select placeholder="请选择主题">
                      <Option value="light">浅色主题</Option>
                      <Option value="dark">深色主题</Option>
                      <Option value="auto">自动切换</Option>
                    </Select>
                  </Form.Item>
                </Col>
                
                <Col xs={24}>
                  <Divider>通知设置</Divider>
                </Col>
                
                <Col xs={24} md={12}>
                  <Form.Item
                    label="启用通知"
                    name="notifications_enabled"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
                
                <Col xs={24} md={12}>
                  <Form.Item
                    label="邮件通知"
                    name="email_notifications"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
              </Row>
              
              <Form.Item>
                <Button
                  type="primary"
                  icon={<SaveOutlined />}
                  htmlType="submit"
                  loading={saving}
                >
                  保存用户设置
                </Button>
              </Form.Item>
            </Form>
          </TabPane>

          {/* TradeMaster设置 */}
          <TabPane 
            tab={
              <Space>
                <ApiOutlined />
                TradeMaster设置
              </Space>
            } 
            key="trademaster"
          >
            <Form
              form={tradeMasterForm}
              layout="vertical"
              onFinish={saveTradeMasterSettings}
            >
              <Row gutter={[16, 16]}>
                <Col xs={24}>
                  <Alert
                    message="TradeMaster核心配置"
                    description="这些设置将影响策略训练和回测的执行方式，请谨慎修改。"
                    type="info"
                    showIcon
                    style={{ marginBottom: 16 }}
                  />
                </Col>
                
                <Col xs={24}>
                  <Form.Item
                    label="API端点"
                    name="api_endpoint"
                    rules={[{ required: true, message: '请输入API端点' }]}
                  >
                    <Input placeholder="http://localhost:8080/api" />
                  </Form.Item>
                </Col>
                
                <Col xs={24} md={12}>
                  <Form.Item
                    label="请求超时时间 (秒)"
                    name="timeout"
                    rules={[
                      { required: true, message: '请输入超时时间' },
                      { type: 'number', min: 1, max: 3600, message: '超时时间必须在1-3600秒之间' }
                    ]}
                  >
                    <InputNumber
                      min={1}
                      max={3600}
                      style={{ width: '100%' }}
                      placeholder="30"
                    />
                  </Form.Item>
                </Col>
                
                <Col xs={24} md={12}>
                  <Form.Item
                    label="最大并发会话数"
                    name="max_concurrent_sessions"
                    rules={[
                      { required: true, message: '请输入最大并发会话数' },
                      { type: 'number', min: 1, max: 100, message: '并发会话数必须在1-100之间' }
                    ]}
                  >
                    <InputNumber
                      min={1}
                      max={100}
                      style={{ width: '100%' }}
                      placeholder="5"
                    />
                  </Form.Item>
                </Col>
                
                <Col xs={24} md={12}>
                  <Form.Item
                    label="默认初始资金"
                    name="default_initial_capital"
                    rules={[
                      { required: true, message: '请输入默认初始资金' },
                      { type: 'number', min: 1000, message: '初始资金不能少于1000' }
                    ]}
                  >
                    <InputNumber
                      min={1000}
                      step={1000}
                      style={{ width: '100%' }}
                      placeholder="100000"
                      formatter={value => `¥ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                      parser={value => value!.replace(/\¥\s?|(,*)/g, '')}
                    />
                  </Form.Item>
                </Col>
                
                <Col xs={24} md={12}>
                  <Form.Item
                    label="默认手续费率"
                    name="default_commission_rate"
                    rules={[
                      { required: true, message: '请输入默认手续费率' },
                      { type: 'number', min: 0, max: 0.01, message: '手续费率必须在0-1%之间' }
                    ]}
                  >
                    <InputNumber
                      min={0}
                      max={0.01}
                      step={0.0001}
                      style={{ width: '100%' }}
                      placeholder="0.001"
                      formatter={value => `${(Number(value) * 100).toFixed(4)}%`}
                      parser={value => (Number(value!.replace('%', '')) / 100).toString()}
                    />
                  </Form.Item>
                </Col>
                
                <Col xs={24} md={12}>
                  <Form.Item
                    label="启用GPU加速"
                    name="enable_gpu"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
                
                <Col xs={24} md={12}>
                  <Form.Item
                    label="日志级别"
                    name="log_level"
                    rules={[{ required: true, message: '请选择日志级别' }]}
                  >
                    <Select placeholder="请选择日志级别">
                      <Option value="DEBUG">DEBUG (调试)</Option>
                      <Option value="INFO">INFO (信息)</Option>
                      <Option value="WARNING">WARNING (警告)</Option>
                      <Option value="ERROR">ERROR (错误)</Option>
                    </Select>
                  </Form.Item>
                </Col>
              </Row>
              
              <Form.Item>
                <Space>
                  <Button
                    type="primary"
                    icon={<SaveOutlined />}
                    htmlType="submit"
                    loading={saving}
                  >
                    保存TradeMaster设置
                  </Button>
                  
                  <Button
                    icon={<ApiOutlined />}
                    onClick={testTradeMasterConnection}
                  >
                    测试连接
                  </Button>
                </Space>
              </Form.Item>
            </Form>
          </TabPane>

          {/* 系统设置 */}
          <TabPane 
            tab={
              <Space>
                <SecurityScanOutlined />
                系统设置
              </Space>
            } 
            key="system"
          >
            <Form
              form={systemForm}
              layout="vertical"
              onFinish={saveSystemSettings}
            >
              <Row gutter={[16, 16]}>
                <Col xs={24}>
                  <Alert
                    message="系统核心配置"
                    description="这些设置将影响整个系统的运行方式，修改后可能需要重启服务。"
                    type="warning"
                    showIcon
                    style={{ marginBottom: 16 }}
                  />
                </Col>
                
                <Col xs={24}>
                  <Divider>实时通信设置</Divider>
                </Col>
                
                <Col xs={24} md={12}>
                  <Form.Item
                    label="启用WebSocket"
                    name="websocket_enabled"
                    valuePropName="checked"
                    extra={`WebSocket状态: ${wsConnected ? '已连接' : '未连接'}`}
                  >
                    <Switch />
                  </Form.Item>
                </Col>
                
                <Col xs={24} md={12}>
                  <Form.Item
                    label="自动重连"
                    name="websocket_reconnect"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
                
                <Col xs={24}>
                  <Divider>性能设置</Divider>
                </Col>
                
                <Col xs={24} md={12}>
                  <Form.Item
                    label="启用缓存"
                    name="cache_enabled"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
                
                <Col xs={24} md={12}>
                  <Form.Item
                    label="会话超时时间 (分钟)"
                    name="session_timeout"
                    rules={[
                      { required: true, message: '请输入会话超时时间' },
                      { type: 'number', min: 5, max: 1440, message: '会话超时时间必须在5-1440分钟之间' }
                    ]}
                  >
                    <InputNumber
                      min={5}
                      max={1440}
                      style={{ width: '100%' }}
                      placeholder="30"
                    />
                  </Form.Item>
                </Col>
                
                <Col xs={24} md={12}>
                  <Form.Item
                    label="最大文件大小 (MB)"
                    name="max_file_size"
                    rules={[
                      { required: true, message: '请输入最大文件大小' },
                      { type: 'number', min: 1, max: 1024, message: '文件大小必须在1-1024MB之间' }
                    ]}
                  >
                    <InputNumber
                      min={1}
                      max={1024}
                      style={{ width: '100%' }}
                      placeholder="50"
                    />
                  </Form.Item>
                </Col>
              </Row>
              
              <Form.Item>
                <Space>
                  <Button
                    type="primary"
                    icon={<SaveOutlined />}
                    htmlType="submit"
                    loading={saving}
                  >
                    保存系统设置
                  </Button>
                  
                  <Button
                    icon={<ReloadOutlined />}
                    onClick={() => {
                      loadSettings();
                      message.info('设置已重新加载');
                    }}
                  >
                    重新加载
                  </Button>
                </Space>
              </Form.Item>
            </Form>
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
};

export default Settings