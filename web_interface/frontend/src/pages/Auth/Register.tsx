import React, { useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Form, Input, Button, Typography, message, Alert, Checkbox } from 'antd'
import { UserOutlined, LockOutlined, MailOutlined } from '@ant-design/icons'

import { useAppDispatch, useAppSelector } from '@/store'
import { registerAsync, clearError } from '@/store/auth/authSlice'
import { ROUTES } from '@/constants'
import { validate } from '@/utils'
import { RegisterRequest } from '@/types'

const { Title, Text } = Typography

interface RegisterFormData extends RegisterRequest {
  confirm_password: string
}

const Register: React.FC = () => {
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

  const handleSubmit = async (values: RegisterFormData) => {
    try {
      await dispatch(registerAsync({
        username: values.username,
        email: values.email,
        password: values.password,
        full_name: values.full_name,
        agree_terms: values.agree_terms,
      })).unwrap()
      
      message.success('注册成功！请登录您的账户')
      navigate(ROUTES.LOGIN)
    } catch (error: any) {
      // Error is handled by the slice but we can show specific messages
      if (typeof error === 'string') {
        message.error(error)
      } else if (typeof error === 'object' && error.message) {
        message.error(error.message)
      } else {
        message.error('注册失败，请稍后重试')
      }
    }
  }

  return (
    <div>
      <div style={{ textAlign: 'center', marginBottom: 32 }}>
        <Title level={2} style={{ marginBottom: 8 }}>
          创建账户
        </Title>
        <Text type="secondary">
          注册您的 TradeMaster 账户
        </Text>
      </div>

      {error && (
        <Alert
          message={typeof error === 'object' && error.message ? error.message : error}
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
          closable
          onClose={() => dispatch(clearError())}
        />
      )}
      
      <Form
        form={form}
        name="register"
        size="large"
        onFinish={handleSubmit}
        autoComplete="off"
        scrollToFirstError
        initialValues={{
          agree_terms: false,
        }}
      >
        <Form.Item
          name="username"
          rules={[
            { required: true, message: '请输入用户名' },
            { min: 3, message: '用户名至少3个字符' },
            { max: 50, message: '用户名最多50个字符' },
            {
              pattern: /^[a-zA-Z0-9_-]+$/,
              message: '用户名只能包含字母、数字、下划线和短横线',
            },
          ]}
        >
          <Input
            prefix={<UserOutlined />}
            placeholder="用户名"
            autoComplete="username"
          />
        </Form.Item>

        <Form.Item
          name="email"
          rules={[
            { required: true, message: '请输入邮箱地址' },
            { type: 'email', message: '请输入有效的邮箱地址' },
            {
              validator: (_, value) => {
                if (!value || validate.email(value)) {
                  return Promise.resolve()
                }
                return Promise.reject(new Error('请输入有效的邮箱地址'))
              },
            },
          ]}
        >
          <Input
            prefix={<MailOutlined />}
            placeholder="邮箱地址"
            autoComplete="email"
          />
        </Form.Item>

        <Form.Item
          name="full_name"
          rules={[
            { max: 100, message: '姓名最多100个字符' },
          ]}
        >
          <Input
            placeholder="真实姓名（可选）"
            autoComplete="name"
          />
        </Form.Item>

        <Form.Item
          name="password"
          rules={[
            { required: true, message: '请输入密码' },
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
            placeholder="密码"
            autoComplete="new-password"
          />
        </Form.Item>

        <Form.Item
          name="confirm_password"
          dependencies={['password']}
          rules={[
            { required: true, message: '请确认密码' },
            ({ getFieldValue }) => ({
              validator(_, value) {
                if (!value || getFieldValue('password') === value) {
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
            placeholder="确认密码"
            autoComplete="new-password"
          />
        </Form.Item>

        <Form.Item
          name="agree_terms"
          valuePropName="checked"
          rules={[
            {
              validator: (_, value) =>
                value ? Promise.resolve() : Promise.reject(new Error('请同意服务条款')),
            },
          ]}
        >
          <Checkbox>
            我已阅读并同意{' '}
            <Link to="/terms" target="_blank">
              服务条款
            </Link>
            {' '}和{' '}
            <Link to="/privacy" target="_blank">
              隐私政策
            </Link>
          </Checkbox>
        </Form.Item>

        <Form.Item>
          <Button
            type="primary"
            htmlType="submit"
            loading={loading}
            style={{ width: '100%', height: 48 }}
          >
            注册
          </Button>
        </Form.Item>

        <div style={{ textAlign: 'center' }}>
          <Text type="secondary">
            已有账户？{' '}
            <Link to={ROUTES.LOGIN}>
              立即登录
            </Link>
          </Text>
        </div>
      </Form>
    </div>
  )
}

export default Register