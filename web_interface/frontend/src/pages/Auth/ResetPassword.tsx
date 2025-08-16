import React, { useState, useEffect } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { Form, Input, Button, Typography, message, Result, Alert } from 'antd'
import { LockOutlined, CheckCircleOutlined } from '@ant-design/icons'

import { authService } from '@/services'
import { ROUTES } from '@/constants'
import { validate } from '@/utils'

const { Title, Text } = Typography

interface ResetPasswordFormData {
  new_password: string
  confirm_password: string
}

const ResetPassword: React.FC = () => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState('')
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()

  const token = searchParams.get('token')

  useEffect(() => {
    if (!token) {
      message.error('重置令牌无效或已过期')
      navigate(ROUTES.LOGIN)
    }
  }, [token, navigate])

  const handleSubmit = async (values: ResetPasswordFormData) => {
    if (!token) {
      message.error('重置令牌无效')
      return
    }

    setLoading(true)
    setError('')

    try {
      await authService.resetPassword({
        token,
        new_password: values.new_password,
      })
      setSuccess(true)
      message.success('密码重置成功')
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || '密码重置失败'
      setError(errorMessage)
      message.error(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  if (success) {
    return (
      <div>
        <Result
          icon={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
          status="success"
          title="密码重置成功"
          subTitle="您的密码已成功重置，请使用新密码登录您的账户。"
          extra={[
            <Button type="primary" key="login" onClick={() => navigate(ROUTES.LOGIN)}>
              立即登录
            </Button>,
          ]}
        />
      </div>
    )
  }

  return (
    <div>
      <div style={{ textAlign: 'center', marginBottom: 32 }}>
        <Title level={2} style={{ marginBottom: 8 }}>
          设置新密码
        </Title>
        <Text type="secondary">
          请输入您的新密码
        </Text>
      </div>

      {error && (
        <Alert
          message={error}
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
          closable
          onClose={() => setError('')}
        />
      )}
      
      <Form
        form={form}
        name="reset-password"
        size="large"
        onFinish={handleSubmit}
        autoComplete="off"
        scrollToFirstError
      >
        <Form.Item
          name="new_password"
          rules={[
            { required: true, message: '请输入新密码' },
            { min: 8, message: '密码至少8个字符' },
            {
              validator: (_, value) => {
                if (!value || validate.password(value)) {
                  return Promise.resolve()
                }
                return Promise.reject(
                  new Error('密码必须包含大小写字母和数字，至少8个字符')
                )
              },
            },
          ]}
          hasFeedback
        >
          <Input.Password
            prefix={<LockOutlined />}
            placeholder="新密码"
            autoComplete="new-password"
          />
        </Form.Item>

        <Form.Item
          name="confirm_password"
          dependencies={['new_password']}
          rules={[
            { required: true, message: '请确认新密码' },
            ({ getFieldValue }) => ({
              validator(_, value) {
                if (!value || getFieldValue('new_password') === value) {
                  return Promise.resolve()
                }
                return Promise.reject(new Error('两次输入的密码不一致'))
              },
            }),
          ]}
          hasFeedback
        >
          <Input.Password
            prefix={<LockOutlined />}
            placeholder="确认新密码"
            autoComplete="new-password"
          />
        </Form.Item>

        <div style={{ marginBottom: 16 }}>
          <Text type="secondary" style={{ fontSize: '14px' }}>
            密码要求：
          </Text>
          <ul style={{ 
            margin: '8px 0', 
            paddingLeft: '20px', 
            fontSize: '12px', 
            color: '#666' 
          }}>
            <li>至少8个字符</li>
            <li>包含大写字母</li>
            <li>包含小写字母</li>
            <li>包含数字</li>
            <li>建议包含特殊字符</li>
          </ul>
        </div>

        <Form.Item>
          <Button
            type="primary"
            htmlType="submit"
            loading={loading}
            style={{ width: '100%', height: 48 }}
          >
            重置密码
          </Button>
        </Form.Item>

        <div style={{ textAlign: 'center' }}>
          <Text type="secondary">
            想起密码了？{' '}
            <Link to={ROUTES.LOGIN}>
              立即登录
            </Link>
          </Text>
        </div>
      </Form>
    </div>
  )
}

export default ResetPassword