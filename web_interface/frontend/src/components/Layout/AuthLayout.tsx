import React from 'react'
import { Layout, Typography, theme } from 'antd'

import { APP_CONFIG } from '@/constants'

const { Header, Content, Footer } = Layout
const { Title, Text } = Typography

interface AuthLayoutProps {
  children: React.ReactNode
}

const AuthLayout: React.FC<AuthLayoutProps> = ({ children }) => {
  const {
    token: { colorBgContainer },
  } = theme.useToken()

  return (
    <Layout style={{ minHeight: '100vh', background: '#f0f2f5' }}>
      <Header
        style={{
          background: colorBgContainer,
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.06)',
          padding: '0 24px',
          display: 'flex',
          alignItems: 'center',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <div
            style={{
              width: 32,
              height: 32,
              background: '#1890ff',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginRight: 12,
              color: 'white',
              fontSize: '16px',
              fontWeight: 'bold',
            }}
          >
            T
          </div>
          <Title level={3} style={{ margin: 0, color: '#1890ff' }}>
            {APP_CONFIG.TITLE}
          </Title>
        </div>
      </Header>

      <Content
        style={{
          padding: '48px 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flex: 1,
        }}
      >
        <div
          style={{
            width: '100%',
            maxWidth: 400,
            background: colorBgContainer,
            borderRadius: 8,
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
            padding: '32px',
          }}
        >
          {children}
        </div>
      </Content>

      <Footer
        style={{
          textAlign: 'center',
          background: 'transparent',
          padding: '24px',
        }}
      >
        <Text type="secondary">{APP_CONFIG.COPYRIGHT}</Text>
      </Footer>
    </Layout>
  )
}

export default AuthLayout