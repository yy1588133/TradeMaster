import React, { useState } from 'react'
import { Form, Input, Button, Typography, message, Card, Alert, Progress } from 'antd'
import { LockOutlined } from '@ant-design/icons'

import { useAppDispatch, useAppSelector } from '@/store'
import { changePasswordAsync } from '@/store/auth/authSlice'
import { validate } from '@/utils'

const { Title, Text } = Typography

interface ChangePasswordFormData {
  current_password: string
  new_password: string
  confirm_password: string
}

const ChangePassword: React.FC = () => {
  const dispatch = useAppDispatch()
  const { passwordLoading } = useAppSelector(state => state.auth)
  const [form] = Form.useForm()
  const [passwordStrength, setPasswordStrength] = useState(0)
  const [strengthLabel, setStrengthLabel] = useState('')

  const calculatePasswordStrength = (password: string): number => {
    let score = 0
    
    // Length score
    if (password.length >= 8) score += 25
    if (password.length >= 12) score += 15
    if (password.length >= 16) score += 10
    
    // Character type scores
    if (/[a-z]/.test(password)) score += 15
    if (/[A-Z]/.test(password)) score += 15
    if (/[0-9]/.test(password)) score += 15
    if (/[^a-zA-Z0-9]/.test(password)) score += 15
    
    return Math.min(score, 100)
  }

  const getStrengthLabel = (score: number): string => {
    if (score < 30) return '弱'
    if (score < 60) return '一般'
    if (score < 80) return '强'
    return '很强'
  }

  const getStrengthColor = (score: number): string => {
    if (score < 30) return '#ff4d4f'
    if (score < 60) return '#faad14'
    if (score < 80) return '#1890ff'
    return '#52c41a'
  }

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const password = e.target.value
    const strength = calculatePasswordStrength(password)
    const label = getStrengthLabel(strength)
    
    setPasswordStrength(strength)
    setStrengthLabel(label)
  }

  const handleSubmit = async (values: ChangePasswordFormData) => {
    try {
      await dispatch(changePasswordAsync({
        current_password: values.current_password,
        new_password: values.new_password,
      })).unwrap()
      
      message.success('密码修改成功，请重新登录')
      form.resetFields()
      setPasswordStrength(0)
      setStrengthLabel('')
      
      // 延迟后重定向到登录页面
      setTimeout(() => {
        window.location.href = '/login'
      }, 2000)
      
    } catch (error: any) {
      if (typeof error === 'string') {
        message.error(error)
      } else {
        message.error('密码修改失败，请稍后重试')
      }
    }
  }

  return (
    <Card title="修改密码" style={{ maxWidth: 600 }}>
      <Alert
        message="安全提示"
        description="为了您的账户安全，请定期更换密码。新密码应包含大小写字母、数字和特殊字符。"
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />

      <Form
        form={form}
        name="change-password"
        layout="vertical"
        onFinish={handleSubmit}
        autoComplete="off"
        scrollToFirstError
      >
        <Form.Item
          label="当前密码"
          name="current_password"
          rules={[
            { required: true, message: '请输入当前密码' },
          ]}
        >
          <Input.Password
            prefix={<LockOutlined />}
            placeholder="请输入当前密码"
            autoComplete="current-password"
          />
        </Form.Item>

        <Form.Item
          label="新密码"
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
            placeholder="请输入新密码"
            autoComplete="new-password"
            onChange={handlePasswordChange}
          />
        </Form.Item>

        {passwordStrength > 0 && (
          <div style={{ marginBottom: 16 }}>
            <Text type="secondary">密码强度：</Text>
            <Progress
              percent={passwordStrength}
              strokeColor={getStrengthColor(passwordStrength)}
              showInfo={false}
              size="small"
              style={{ marginLeft: 8, width: 200, display: 'inline-block' }}
            />
            <Text 
              style={{ 
                marginLeft: 8, 
                color: getStrengthColor(passwordStrength),
                fontWeight: 'bold'
              }}
            >
              {strengthLabel}
            </Text>
          </div>
        )}

        <Form.Item
          label="确认新密码"
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
            placeholder="请再次输入新密码"
            autoComplete="new-password"
          />
        </Form.Item>

        <div style={{ marginBottom: 24 }}>
          <Text type="secondary" style={{ fontSize: '14px' }}>
            密码安全建议：
          </Text>
          <ul style={{ 
            margin: '8px 0', 
            paddingLeft: '20px', 
            fontSize: '13px', 
            color: '#666',
            lineHeight: '1.6'
          }}>
            <li>使用至少8个字符，推荐12个或更多</li>
            <li>包含大写字母、小写字母和数字</li>
            <li>包含特殊字符（如 !@#$%^&*）</li>
            <li>避免使用个人信息或常见密码</li>
            <li>不要在多个网站使用相同密码</li>
          </ul>
        </div>

        <Form.Item>
          <Button
            type="primary"
            htmlType="submit"
            loading={passwordLoading}
            style={{ width: '100%' }}
            size="large"
          >
            修改密码
          </Button>
        </Form.Item>
      </Form>
    </Card>
  )
}

export default ChangePassword