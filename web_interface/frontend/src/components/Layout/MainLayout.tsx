import React, { useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { Layout, theme } from 'antd'

import { useAppSelector } from '@/store'
import Header from './Header'
import Sidebar from './Sidebar'
import Breadcrumb from './Breadcrumb'

const { Content } = Layout

const MainLayout: React.FC = () => {
  const location = useLocation()
  const { sidebarCollapsed } = useAppSelector(state => state.common)
  const {
    token: { colorBgContainer },
  } = theme.useToken()

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sidebar />
      <Layout style={{ marginLeft: sidebarCollapsed ? 80 : 256, transition: 'margin-left 0.3s' }}>
        <Header />
        <Content
          style={{
            margin: '0 16px',
            padding: '16px 0',
            minHeight: 'calc(100vh - 64px)',
            background: colorBgContainer,
            borderRadius: 8,
            overflow: 'auto',
          }}
        >
          <div style={{ padding: '0 24px' }}>
            <Breadcrumb />
            <div
              style={{
                padding: '24px 0',
                minHeight: 'calc(100vh - 180px)',
              }}
            >
              <Outlet />
            </div>
          </div>
        </Content>
      </Layout>
    </Layout>
  )
}

export default MainLayout