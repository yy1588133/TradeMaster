import React, { useState } from 'react'
import {
  Card,
  Row,
  Col,
  Typography,
  Tabs,
  Table,
  Button,
  Space,
  Tag,
  Form,
  Input,
  Select,
  Switch,
  InputNumber,
  Statistic,
  Progress,
  Alert,
  List,
  Avatar,
  Modal,
  message,
  Descriptions,
} from 'antd'
import {
  SettingOutlined,
  UserOutlined,
  SecurityScanOutlined,
  MonitorOutlined,
  DatabaseOutlined,
  BellOutlined,
  SafetyOutlined,
  DeleteOutlined,
  EditOutlined,
  ReloadOutlined,
  ExportOutlined,
  ImportOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'

import { format } from '@/utils'

const { Title, Text, Paragraph } = Typography
const { TabPane } = Tabs
const { Option } = Select
const { TextArea } = Input

interface SystemUser {
  id: string
  username: string
  email: string
  role: string
  status: 'active' | 'inactive' | 'banned'
  lastLogin: string
  createdAt: string
}

interface SystemLog {
  id: string
  level: 'info' | 'warn' | 'error'
  message: string
  timestamp: string
  module: string
}

interface SystemConfig {
  key: string
  value: any
  description: string
  type: 'string' | 'number' | 'boolean' | 'json'
}

const SystemSettings: React.FC = () => {
  const [activeTab, setActiveTab] = useState('users')
  const [loading, setLoading] = useState(false)

  // Mock data
  const [systemUsers] = useState<SystemUser[]>([
    {
      id: '1',
      username: 'admin',
      email: 'admin@trademaster.com',
      role: 'admin',
      status: 'active',
      lastLogin: '2024-01-15T10:30:00Z',
      createdAt: '2024-01-01T00:00:00Z',
    },
    {
      id: '2',
      username: 'trader001',
      email: 'trader001@example.com',
      role: 'user',
      status: 'active',
      lastLogin: '2024-01-15T09:15:00Z',
      createdAt: '2024-01-05T00:00:00Z',
    },
    {
      id: '3',
      username: 'analyst001',
      email: 'analyst001@example.com',
      role: 'analyst',
      status: 'inactive',
      lastLogin: '2024-01-10T16:20:00Z',
      createdAt: '2024-01-08T00:00:00Z',
    },
  ])

  const [systemLogs] = useState<SystemLog[]>([
    {
      id: '1',
      level: 'info',
      message: '系统启动成功',
      timestamp: '2024-01-15T10:00:00Z',
      module: 'system',
    },
    {
      id: '2',
      level: 'warn',
      message: '策略执行超时警告',
      timestamp: '2024-01-15T09:45:00Z',
      module: 'strategy',
    },
    {
      id: '3',
      level: 'error',
      message: '数据库连接失败',
      timestamp: '2024-01-15T09:30:00Z',
      module: 'database',
    },
  ])

  const [systemConfigs] = useState<SystemConfig[]>([
    {
      key: 'max_concurrent_strategies',
      value: 10,
      description: '最大并发策略数量',
      type: 'number',
    },
    {
      key: 'default_commission',
      value: 0.001,
      description: '默认手续费率',
      type: 'number',
    },
    {
      key: 'enable_email_notifications',
      value: true,
      description: '启用邮件通知',
      type: 'boolean',
    },
    {
      key: 'smtp_server',
      value: 'smtp.example.com',
      description: 'SMTP服务器地址',
      type: 'string',
    },
  ])

  const systemStats = {
    totalUsers: systemUsers.length,
    activeUsers: systemUsers.filter(u => u.status === 'active').length,
    totalStrategies: 25,
    runningStrategies: 8,
    systemUptime: '15天 8小时 30分钟',
    memoryUsage: 68,
    cpuUsage: 45,
    diskUsage: 32,
  }

  const userColumns: ColumnsType<SystemUser> = [
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
      render: (username: string, record: SystemUser) => (
        <Space>
          <Avatar icon={<UserOutlined />} size="small" />
          <div>
            <div>{username}</div>
            <Text type="secondary" style={{ fontSize: '12px' }}>
              {record.email}
            </Text>
          </div>
        </Space>
      ),
    },
    {
      title: '角色',
      dataIndex: 'role',
      key: 'role',
      render: (role: string) => {
        const roleConfig = {
          admin: { color: 'red', text: '管理员' },
          user: { color: 'blue', text: '用户' },
          analyst: { color: 'green', text: '分析师' },
          viewer: { color: 'default', text: '观察者' },
        }
        const config = roleConfig[role as keyof typeof roleConfig] || roleConfig.user
        return <Tag color={config.color}>{config.text}</Tag>
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusConfig = {
          active: { color: 'success', text: '活跃' },
          inactive: { color: 'default', text: '不活跃' },
          banned: { color: 'error', text: '禁用' },
        }
        const config = statusConfig[status as keyof typeof statusConfig]
        return <Tag color={config.color}>{config.text}</Tag>
      },
    },
    {
      title: '最后登录',
      dataIndex: 'lastLogin',
      key: 'lastLogin',
      render: (lastLogin: string) => format.datetime(lastLogin),
    },
    {
      title: '创建时间',
      dataIndex: 'createdAt',
      key: 'createdAt',
      render: (createdAt: string) => format.date(createdAt),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record: SystemUser) => (
        <Space>
          <Button size="small" icon={<EditOutlined />}>编辑</Button>
          <Button size="small" danger icon={<DeleteOutlined />}>删除</Button>
        </Space>
      ),
    },
  ]

  const logColumns: ColumnsType<SystemLog> = [
    {
      title: '级别',
      dataIndex: 'level',
      key: 'level',
      width: 80,
      render: (level: string) => {
        const levelConfig = {
          info: { color: 'blue', text: 'INFO' },
          warn: { color: 'orange', text: 'WARN' },
          error: { color: 'red', text: 'ERROR' },
        }
        const config = levelConfig[level as keyof typeof levelConfig]
        return <Tag color={config.color}>{config.text}</Tag>
      },
    },
    {
      title: '模块',
      dataIndex: 'module',
      key: 'module',
      width: 100,
    },
    {
      title: '消息',
      dataIndex: 'message',
      key: 'message',
    },
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 160,
      render: (timestamp: string) => format.datetime(timestamp),
    },
  ]

  const configColumns: ColumnsType<SystemConfig> = [
    {
      title: '配置项',
      dataIndex: 'key',
      key: 'key',
      render: (key: string) => <Text code>{key}</Text>,
    },
    {
      title: '当前值',
      dataIndex: 'value',
      key: 'value',
      render: (value: any, record: SystemConfig) => {
        if (record.type === 'boolean') {
          return <Tag color={value ? 'green' : 'red'}>{value ? '启用' : '禁用'}</Tag>
        }
        return <Text>{String(value)}</Text>
      },
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => <Tag>{type.toUpperCase()}</Tag>,
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record: SystemConfig) => (
        <Button size="small" icon={<EditOutlined />}>编辑</Button>
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>系统设置</Title>
        <Text type="secondary">管理系统配置、用户和监控</Text>
      </div>

      {/* System Overview */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="总用户数"
              value={systemStats.totalUsers}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="活跃用户"
              value={systemStats.activeUsers}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="运行策略"
              value={systemStats.runningStrategies}
              suffix={`/ ${systemStats.totalStrategies}`}
              prefix={<MonitorOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="系统运行时间"
              value={systemStats.systemUptime}
              prefix={<MonitorOutlined />}
              valueStyle={{ color: '#1890ff', fontSize: '14px' }}
            />
          </Card>
        </Col>
      </Row>

      {/* System Resources */}
      <Card style={{ marginBottom: 24 }}>
        <Title level={4}>系统资源</Title>
        <Row gutter={24}>
          <Col span={8}>
            <div style={{ marginBottom: 16 }}>
              <Text strong>CPU使用率</Text>
              <Progress percent={systemStats.cpuUsage} strokeColor="#1890ff" />
            </div>
          </Col>
          <Col span={8}>
            <div style={{ marginBottom: 16 }}>
              <Text strong>内存使用率</Text>
              <Progress percent={systemStats.memoryUsage} strokeColor="#52c41a" />
            </div>
          </Col>
          <Col span={8}>
            <div style={{ marginBottom: 16 }}>
              <Text strong>磁盘使用率</Text>
              <Progress percent={systemStats.diskUsage} strokeColor="#faad14" />
            </div>
          </Col>
        </Row>
      </Card>

      {/* Main Settings */}
      <Card>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane tab={<span><UserOutlined />用户管理</span>} key="users">
            <div style={{ marginBottom: 16 }}>
              <Space>
                <Button type="primary" icon={<UserOutlined />}>
                  添加用户
                </Button>
                <Button icon={<ImportOutlined />}>
                  批量导入
                </Button>
                <Button icon={<ExportOutlined />}>
                  导出用户
                </Button>
                <Button icon={<ReloadOutlined />} onClick={() => setLoading(true)}>
                  刷新
                </Button>
              </Space>
            </div>
            
            <Table
              columns={userColumns}
              dataSource={systemUsers}
              rowKey="id"
              loading={loading}
              pagination={{
                pageSize: 10,
                showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
              }}
            />
          </TabPane>

          <TabPane tab={<span><SettingOutlined />系统配置</span>} key="config">
            <Alert
              message="配置修改提醒"
              description="修改系统配置可能会影响系统运行，请谨慎操作。建议在维护窗口期间进行配置更改。"
              type="warning"
              showIcon
              style={{ marginBottom: 16 }}
            />
            
            <Table
              columns={configColumns}
              dataSource={systemConfigs}
              rowKey="key"
              pagination={false}
            />
          </TabPane>

          <TabPane tab={<span><MonitorOutlined />系统监控</span>} key="monitoring">
            <Row gutter={16}>
              <Col span={12}>
                <Card title="系统信息" size="small">
                  <Descriptions column={1} size="small">
                    <Descriptions.Item label="系统版本">TradeMaster v1.0.0</Descriptions.Item>
                    <Descriptions.Item label="Python版本">3.9.16</Descriptions.Item>
                    <Descriptions.Item label="数据库版本">PostgreSQL 14.5</Descriptions.Item>
                    <Descriptions.Item label="Redis版本">7.0.5</Descriptions.Item>
                    <Descriptions.Item label="启动时间">
                      {format.datetime('2024-01-01T10:00:00Z')}
                    </Descriptions.Item>
                  </Descriptions>
                </Card>
              </Col>
              
              <Col span={12}>
                <Card title="性能指标" size="small">
                  <Descriptions column={1} size="small">
                    <Descriptions.Item label="并发连接数">128</Descriptions.Item>
                    <Descriptions.Item label="每秒请求数">45.2</Descriptions.Item>
                    <Descriptions.Item label="平均响应时间">120ms</Descriptions.Item>
                    <Descriptions.Item label="错误率">0.02%</Descriptions.Item>
                    <Descriptions.Item label="数据库连接池">8/20</Descriptions.Item>
                  </Descriptions>
                </Card>
              </Col>
            </Row>
          </TabPane>

          <TabPane tab={<span><DatabaseOutlined />系统日志</span>} key="logs">
            <div style={{ marginBottom: 16 }}>
              <Space>
                <Select defaultValue="all" style={{ width: 120 }}>
                  <Option value="all">全部级别</Option>
                  <Option value="info">INFO</Option>
                  <Option value="warn">WARN</Option>
                  <Option value="error">ERROR</Option>
                </Select>
                <Select defaultValue="all" style={{ width: 120 }}>
                  <Option value="all">全部模块</Option>
                  <Option value="system">系统</Option>
                  <Option value="strategy">策略</Option>
                  <Option value="database">数据库</Option>
                </Select>
                <Button icon={<ReloadOutlined />}>刷新</Button>
                <Button icon={<ExportOutlined />}>导出日志</Button>
              </Space>
            </div>
            
            <Table
              columns={logColumns}
              dataSource={systemLogs}
              rowKey="id"
              pagination={{
                pageSize: 20,
                showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
              }}
            />
          </TabPane>

          <TabPane tab={<span><SecurityScanOutlined />安全设置</span>} key="security">
            <Space direction="vertical" style={{ width: '100%' }} size="large">
              <Card title="访问控制" size="small">
                <Form layout="vertical">
                  <Row gutter={16}>
                    <Col span={12}>
                      <Form.Item label="登录失败锁定次数">
                        <InputNumber min={1} max={10} defaultValue={5} />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item label="锁定时间（分钟）">
                        <InputNumber min={1} max={60} defaultValue={30} />
                      </Form.Item>
                    </Col>
                  </Row>
                  
                  <Form.Item label="允许的IP地址（一行一个）">
                    <TextArea rows={4} placeholder="192.168.1.0/24&#10;10.0.0.0/8" />
                  </Form.Item>
                  
                  <Form.Item>
                    <Button type="primary">保存设置</Button>
                  </Form.Item>
                </Form>
              </Card>
              
              <Card title="密码策略" size="small">
                <Form layout="vertical">
                  <Row gutter={16}>
                    <Col span={12}>
                      <Form.Item label="最小密码长度">
                        <InputNumber min={6} max={20} defaultValue={8} />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item label="密码有效期（天）">
                        <InputNumber min={30} max={365} defaultValue={90} />
                      </Form.Item>
                    </Col>
                  </Row>
                  
                  <Form.Item label="密码复杂度要求">
                    <Space direction="vertical">
                      <Switch defaultChecked /> 包含大写字母
                      <Switch defaultChecked /> 包含小写字母
                      <Switch defaultChecked /> 包含数字
                      <Switch /> 包含特殊字符
                    </Space>
                  </Form.Item>
                  
                  <Form.Item>
                    <Button type="primary">保存设置</Button>
                  </Form.Item>
                </Form>
              </Card>
            </Space>
          </TabPane>
        </Tabs>
      </Card>
    </div>
  )
}

export default SystemSettings