import React, { useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Form, Input, Button, Checkbox, Typography, message, Alert } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'

import { useAppDispatch, useAppSelector } from '@/store'
import { loginAsync, clearError } from '@/store/auth/authSlice'
import { ROUTES } from '@/constants'
import { LoginRequest } from '@/types'

const { Title, Text } = Typography

interface LoginFormData extends LoginRequest {
  remember_me: boolean
}

const Login: React.FC = () => {
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const { loading, error, isAuthenticated } = useAppSelector(state => state.auth)
  const [form] = Form.useForm()

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate(ROUTES.DASHBOARD)
    }
  }, [isAuthenticated, navigate])

  // Clear error when component unmounts
  useEffect(() => {
    return () => {
      dispatch(clearError())
    }
  }, [dispatch])

  const handleSubmit = async (values: LoginFormData) => {
    try {
      await dispatch(loginAsync({
        username: values.username,
        password: values.password,
        remember_me: values.remember_me,
      })).unwrap()
      
      message.success('登录成功')
      navigate(ROUTES.DASHBOARD)
    } catch (error: any) {
      // Error is handled by the slice but we can show specific messages
      if (typeof error === 'string') {
        message.error(error)
      } else {
        message.error('登录失败，请检查用户名和密码')
      }
    }
  }

  return (
    <div>
      <div style={{ textAlign: 'center', marginBottom: 32 }}>
        <Title level={2} style={{ marginBottom: 8 }}>
          欢迎回来
        </Title>
        <Text type="secondary">
          登录您的 TradeMaster 账户
        </Text>
      </div>

      {error && (
        <Alert
          message={error}
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
          closable
          onClose={() => dispatch(clearError())}
        />
      )}
      
      <Form
        form={form}
        name="login"
        size="large"
        onFinish={handleSubmit}
        autoComplete="off"
        initialValues={{
          remember_me: false,
        }}
      >
        <Form.Item
          name="username"
          rules={[
            { required: true, message: '请输入用户名或邮箱' },
            { min: 3, message: '用户名至少3个字符' },
          ]}
        >
          <Input
            prefix={<UserOutlined />}
            placeholder="用户名或邮箱"
            autoComplete="username"
          />
        </Form.Item>

        <Form.Item
          name="password"
          rules={[
            { required: true, message: '请输入密码' },
            { min: 1, message: '请输入密码' },
          ]}
        >
          <Input.Password
            prefix={<LockOutlined />}
            placeholder="密码"
            autoComplete="current-password"
          />
        </Form.Item>

        <Form.Item>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Form.Item name="remember_me" valuePropName="checked" noStyle>
              <Checkbox>记住我</Checkbox>
            </Form.Item>
            <Link to="/forgot-password" style={{ fontSize: '14px' }}>
              忘记密码？
            </Link>
          </div>
        </Form.Item>

        <Form.Item>
          <Button
            type="primary"
            htmlType="submit"
            loading={loading}
            style={{ width: '100%', height: 48 }}
          >
            登录
          </Button>
        </Form.Item>

        <div style={{ textAlign: 'center' }}>
          <Text type="secondary">
            还没有账户？{' '}
            <Link to={ROUTES.REGISTER}>
              立即注册
            </Link>
          </Text>
        </div>
      </Form>
    </div>
  )
}

export default Login