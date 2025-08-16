import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { Form, Input, Button, Typography, message, Result } from 'antd'
import { MailOutlined, ArrowLeftOutlined } from '@ant-design/icons'

import { authService } from '@/services'
import { ROUTES } from '@/constants'
import { validate } from '@/utils'

const { Title, Text } = Typography

interface ForgotPasswordFormData {
  email: string
}

const ForgotPassword: React.FC = () => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [emailSent, setEmailSent] = useState(false)
  const [emailAddress, setEmailAddress] = useState('')

  const handleSubmit = async (values: ForgotPasswordFormData) => {
    setLoading(true)
    try {
      await authService.forgotPassword({ email: values.email })
      setEmailAddress(values.email)
      setEmailSent(true)
      message.success('密码重置邮件已发送')
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || '发送失败，请稍后重试'
      message.error(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  if (emailSent) {
    return (
      <div>
        <Result
          status="success"
          title="邮件已发送"
          subTitle={
            <div>
              <p>我们已向 <strong>{emailAddress}</strong> 发送了密码重置邮件。</p>
              <p>请检查您的邮箱（包括垃圾邮件文件夹），并按照邮件中的说明重置密码。</p>
              <p style={{ marginTop: 16, color: '#666', fontSize: '14px' }}>
                如果您在几分钟内没有收到邮件，请检查邮箱地址是否正确，或重新发送。
              </p>
            </div>
          }
          extra={[
            <Button type="primary" key="resend" onClick={() => setEmailSent(false)}>
              重新发送
            </Button>,
            <Link to={ROUTES.LOGIN} key="login">
              <Button>返回登录</Button>
            </Link>,
          ]}
        />
      </div>
    )
  }

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Link 
          to={ROUTES.LOGIN} 
          style={{ 
            display: 'inline-flex', 
            alignItems: 'center', 
            color: '#1890ff',
            fontSize: '14px'
          }}
        >
          <ArrowLeftOutlined style={{ marginRight: 8 }} />
          返回登录
        </Link>
      </div>

      <div style={{ textAlign: 'center', marginBottom: 32 }}>
        <Title level={2} style={{ marginBottom: 8 }}>
          重置密码
        </Title>
        <Text type="secondary">
          输入您的邮箱地址，我们将发送密码重置链接
        </Text>
      </div>
      
      <Form
        form={form}
        name="forgot-password"
        size="large"
        onFinish={handleSubmit}
        autoComplete="off"
      >
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

        <Form.Item>
          <Button
            type="primary"
            htmlType="submit"
            loading={loading}
            style={{ width: '100%', height: 48 }}
          >
            发送重置邮件
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

export default ForgotPassword