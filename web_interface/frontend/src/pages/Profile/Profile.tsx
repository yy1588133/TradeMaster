import React, { useState } from 'react'
import {
  Card,
  Form,
  Input,
  Button,
  Upload,
  Avatar,
  Row,
  Col,
  Tabs,
  Table,
  Tag,
  Typography,
  Space,
  Divider,
  message,
  Modal,
  Descriptions,
  List,
  Statistic,
} from 'antd'
import {
  UserOutlined,
  UploadOutlined,
  EditOutlined,
  HistoryOutlined,
  SettingOutlined,
  KeyOutlined,
  BellOutlined,
  ShieldOutlined,
  EyeOutlined,
  DeleteOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'

import { useAppDispatch, useAppSelector } from '@/store'
import { updateProfileAsync, changePasswordAsync } from '@/store/auth/authSlice'
import { format } from '@/utils'

const { Title, Text, Paragraph } = Typography
const { TabPane } = Tabs
const { TextArea } = Input

interface ActivityLog {
  id: string
  action: string
  description: string
  timestamp: string
  ip: string
  userAgent: string
}

interface ApiKey {
  id: string
  name: string
  key: string
  permissions: string[]
  createdAt: string
  lastUsed?: string
  status: 'active' | 'inactive'
}

const Profile: React.FC = () => {
  const dispatch = useAppDispatch()
  const { user, loading, passwordLoading } = useAppSelector(state => state.auth)
  
  const [form] = Form.useForm()
  const [passwordForm] = Form.useForm()
  const [activeTab, setActiveTab] = useState('profile')
  const [avatarLoading, setAvatarLoading] = useState(false)

  // Mock data
  const [activityLogs] = useState<ActivityLog[]>([
    {
      id: '1',
      action: '登录',
      description: '用户成功登录系统',
      timestamp: '2024-01-15T10:30:00Z',
      ip: '192.168.1.100',
      userAgent: 'Chrome/120.0.0.0',
    },
    {
      id: '2',
      action: '创建策略',
      description: '创建了新的交易策略：MA双均线策略',
      timestamp: '2024-01-15T09:15:00Z',
      ip: '192.168.1.100',
      userAgent: 'Chrome/120.0.0.0',
    },
    {
      id: '3',
      action: '修改密码',
      description: '用户修改了登录密码',
      timestamp: '2024-01-14T16:20:00Z',
      ip: '192.168.1.100',
      userAgent: 'Chrome/120.0.0.0',
    },
  ])

  const [apiKeys] = useState<ApiKey[]>([
    {
      id: '1',
      name: '主API密钥',
      key: 'tm_ak_1234567890abcdef',
      permissions: ['read', 'write'],
      createdAt: '2024-01-01T00:00:00Z',
      lastUsed: '2024-01-15T10:30:00Z',
      status: 'active',
    },
    {
      id: '2',
      name: '只读API密钥',
      key: 'tm_ak_fedcba0987654321',
      permissions: ['read'],
      createdAt: '2024-01-10T00:00:00Z',
      lastUsed: '2024-01-14T15:45:00Z',
      status: 'active',
    },
  ])

  const handleProfileUpdate = async (values: any) => {
    try {
      await dispatch(updateProfileAsync(values)).unwrap()
      message.success('个人信息更新成功')
    } catch (error: any) {
      message.error(`更新失败：${error.message || error}`)
    }
  }

  const handlePasswordChange = async (values: any) => {
    try {
      await dispatch(changePasswordAsync({
        current_password: values.currentPassword,
        new_password: values.newPassword,
      })).unwrap()
      message.success('密码修改成功')
      passwordForm.resetFields()
    } catch (error: any) {
      message.error(`密码修改失败：${error.message || error}`)
    }
  }

  const handleAvatarUpload = async (file: File) => {
    setAvatarLoading(true)
    try {
      // In real app, upload avatar
      message.success('头像上传成功')
    } catch (error) {
      message.error('头像上传失败')
    } finally {
      setAvatarLoading(false)
    }
  }

  const activityColumns: ColumnsType<ActivityLog> = [
    {
      title: '操作',
      dataIndex: 'action',
      key: 'action',
      width: 100,
      render: (action: string) => <Tag color="blue">{action}</Tag>,
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
    },
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 160,
      render: (timestamp: string) => format.datetime(timestamp),
    },
    {
      title: 'IP地址',
      dataIndex: 'ip',
      key: 'ip',
      width: 120,
    },
  ]

  const apiKeyColumns: ColumnsType<ApiKey> = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: 'API密钥',
      dataIndex: 'key',
      key: 'key',
      render: (key: string) => (
        <Text code style={{ fontSize: '12px' }}>
          {key.substring(0, 20)}...
        </Text>
      ),
    },
    {
      title: '权限',
      dataIndex: 'permissions',
      key: 'permissions',
      render: (permissions: string[]) => (
        <Space>
          {permissions.map(permission => (
            <Tag key={permission} color={permission === 'write' ? 'orange' : 'green'}>
              {permission === 'read' ? '只读' : '读写'}
            </Tag>
          ))}
        </Space>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'active' ? 'green' : 'red'}>
          {status === 'active' ? '活跃' : '禁用'}
        </Tag>
      ),
    },
    {
      title: '最后使用',
      dataIndex: 'lastUsed',
      key: 'lastUsed',
      render: (lastUsed?: string) => lastUsed ? format.datetime(lastUsed) : '-',
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record: ApiKey) => (
        <Space>
          <Button size="small" icon={<EyeOutlined />}>查看</Button>
          <Button size="small" danger icon={<DeleteOutlined />}>删除</Button>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>个人中心</Title>
        <Text type="secondary">管理您的个人信息和账户设置</Text>
      </div>

      <Row gutter={24}>
        <Col xs={24} lg={8}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <Avatar
                size={120}
                src={user?.avatar_url}
                icon={<UserOutlined />}
                style={{ marginBottom: 16 }}
              />
              
              <Upload
                showUploadList={false}
                beforeUpload={(file) => {
                  handleAvatarUpload(file)
                  return false
                }}
                accept="image/*"
              >
                <Button 
                  icon={<UploadOutlined />} 
                  loading={avatarLoading}
                  style={{ marginBottom: 16 }}
                >
                  更换头像
                </Button>
              </Upload>
              
              <div>
                <Title level={4} style={{ marginBottom: 4 }}>
                  {user?.full_name || user?.username}
                </Title>
                <Text type="secondary">{user?.email}</Text>
              </div>
              
              <Divider />
              
              <Row gutter={16}>
                <Col span={12}>
                  <Statistic title="策略数量" value={8} />
                </Col>
                <Col span={12}>
                  <Statistic title="运行天数" value={125} />
                </Col>
              </Row>
            </div>
          </Card>
        </Col>

        <Col xs={24} lg={16}>
          <Card>
            <Tabs activeKey={activeTab} onChange={setActiveTab}>
              <TabPane tab={<span><EditOutlined />基本信息</span>} key="profile">
                <Form
                  form={form}
                  layout="vertical"
                  onFinish={handleProfileUpdate}
                  initialValues={{
                    username: user?.username,
                    email: user?.email,
                    full_name: user?.full_name,
                  }}
                >
                  <Row gutter={16}>
                    <Col span={12}>
                      <Form.Item
                        name="username"
                        label="用户名"
                        rules={[
                          { required: true, message: '请输入用户名' },
                          { min: 3, message: '用户名至少3个字符' },
                        ]}
                      >
                        <Input disabled />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item
                        name="email"
                        label="邮箱地址"
                        rules={[
                          { required: true, message: '请输入邮箱地址' },
                          { type: 'email', message: '请输入有效的邮箱地址' },
                        ]}
                      >
                        <Input />
                      </Form.Item>
                    </Col>
                  </Row>

                  <Form.Item
                    name="full_name"
                    label="真实姓名"
                    rules={[{ max: 100, message: '姓名最多100个字符' }]}
                  >
                    <Input />
                  </Form.Item>

                  <Form.Item>
                    <Button type="primary" htmlType="submit" loading={loading}>
                      保存更改
                    </Button>
                  </Form.Item>
                </Form>
              </TabPane>

              <TabPane tab={<span><KeyOutlined />修改密码</span>} key="password">
                <Form
                  form={passwordForm}
                  layout="vertical"
                  onFinish={handlePasswordChange}
                >
                  <Form.Item
                    name="currentPassword"
                    label="当前密码"
                    rules={[{ required: true, message: '请输入当前密码' }]}
                  >
                    <Input.Password />
                  </Form.Item>

                  <Form.Item
                    name="newPassword"
                    label="新密码"
                    rules={[
                      { required: true, message: '请输入新密码' },
                      { min: 8, message: '密码至少8个字符' },
                    ]}
                  >
                    <Input.Password />
                  </Form.Item>

                  <Form.Item
                    name="confirmPassword"
                    label="确认新密码"
                    dependencies={['newPassword']}
                    rules={[
                      { required: true, message: '请确认新密码' },
                      ({ getFieldValue }) => ({
                        validator(_, value) {
                          if (!value || getFieldValue('newPassword') === value) {
                            return Promise.resolve()
                          }
                          return Promise.reject(new Error('两次输入的密码不一致'))
                        },
                      }),
                    ]}
                  >
                    <Input.Password />
                  </Form.Item>

                  <Form.Item>
                    <Button type="primary" htmlType="submit" loading={passwordLoading}>
                      修改密码
                    </Button>
                  </Form.Item>
                </Form>
              </TabPane>

              <TabPane tab={<span><ShieldOutlined />API密钥</span>} key="api">
                <div style={{ marginBottom: 16 }}>
                  <Button type="primary" icon={<KeyOutlined />}>
                    创建API密钥
                  </Button>
                </div>
                
                <Table
                  columns={apiKeyColumns}
                  dataSource={apiKeys}
                  rowKey="id"
                  pagination={false}
                />
              </TabPane>

              <TabPane tab={<span><HistoryOutlined />活动日志</span>} key="activity">
                <Table
                  columns={activityColumns}
                  dataSource={activityLogs}
                  rowKey="id"
                  pagination={{
                    pageSize: 10,
                    showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
                  }}
                />
              </TabPane>

              <TabPane tab={<span><BellOutlined />通知设置</span>} key="notifications">
                <div>
                  <Title level={4}>邮件通知</Title>
                  <List
                    itemLayout="horizontal"
                    dataSource={[
                      { key: 'strategy_alert', title: '策略告警', description: '当策略出现异常时发送邮件通知' },
                      { key: 'trade_notification', title: '交易通知', description: '重要交易执行时发送邮件通知' },
                      { key: 'system_update', title: '系统更新', description: '系统更新和维护通知' },
                    ]}
                    renderItem={(item) => (
                      <List.Item
                        actions={[
                          <Button key="toggle" size="small">
                            开启
                          </Button>
                        ]}
                      >
                        <List.Item.Meta
                          title={item.title}
                          description={item.description}
                        />
                      </List.Item>
                    )}
                  />
                </div>
              </TabPane>
            </Tabs>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Profile