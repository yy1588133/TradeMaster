import React, { useEffect, useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { Layout, Menu, Typography } from 'antd'
import {
  DashboardOutlined,
  RobotOutlined,
  DatabaseOutlined,
  ExperimentOutlined,
  BarChartOutlined,
  UserOutlined,
  SettingOutlined,
} from '@ant-design/icons'
import type { MenuProps } from 'antd'

import { useAppSelector } from '@/store'
import { ROUTES, APP_CONFIG } from '@/constants'

const { Sider } = Layout
const { Title } = Typography

type MenuItem = Required<MenuProps>['items'][number]

const Sidebar: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const { sidebarCollapsed } = useAppSelector(state => state.common)
  const [selectedKeys, setSelectedKeys] = useState<string[]>([])

  // Menu items configuration
  const menuItems: MenuItem[] = [
    {
      key: ROUTES.DASHBOARD,
      icon: <DashboardOutlined />,
      label: '仪表板',
    },
    {
      key: 'strategies',
      icon: <RobotOutlined />,
      label: '策略管理',
      children: [
        {
          key: ROUTES.STRATEGIES,
          label: '策略列表',
        },
        {
          key: ROUTES.STRATEGY_CREATE,
          label: '创建策略',
        },
      ],
    },
    {
      key: ROUTES.DATASETS,
      icon: <DatabaseOutlined />,
      label: '数据管理',
    },
    {
      key: ROUTES.TRAINING,
      icon: <ExperimentOutlined />,
      label: '训练管理',
    },
    {
      key: ROUTES.ANALYSIS,
      icon: <BarChartOutlined />,
      label: '分析评估',
    },
    {
      key: 'user',
      icon: <UserOutlined />,
      label: '用户中心',
      children: [
        {
          key: ROUTES.PROFILE,
          label: '个人资料',
        },
        {
          key: ROUTES.SETTINGS,
          label: '系统设置',
        },
      ],
    },
  ]

  // Update selected keys based on current route
  useEffect(() => {
    const path = location.pathname
    
    // Handle nested routes
    if (path.startsWith('/strategies/')) {
      if (path.includes('/create')) {
        setSelectedKeys([ROUTES.STRATEGY_CREATE])
      } else {
        setSelectedKeys([ROUTES.STRATEGIES])
      }
    } else {
      setSelectedKeys([path])
    }
  }, [location.pathname])

  // Handle menu click
  const handleMenuClick: MenuProps['onClick'] = ({ key }) => {
    navigate(key)
  }

  // Get default open keys for menu
  const getDefaultOpenKeys = () => {
    const path = location.pathname
    const openKeys: string[] = []
    
    if (path.startsWith('/strategies')) {
      openKeys.push('strategies')
    }
    if (path.startsWith('/profile') || path.startsWith('/settings')) {
      openKeys.push('user')
    }
    
    return openKeys
  }

  return (
    <Sider
      trigger={null}
      collapsible
      collapsed={sidebarCollapsed}
      width={256}
      style={{
        overflow: 'auto',
        height: '100vh',
        position: 'fixed',
        left: 0,
        top: 0,
        bottom: 0,
        zIndex: 100,
      }}
      theme="dark"
    >
      {/* Logo and title */}
      <div
        style={{
          height: 64,
          padding: '16px',
          display: 'flex',
          alignItems: 'center',
          borderBottom: '1px solid #002140',
        }}
      >
        <div
          style={{
            width: 32,
            height: 32,
            background: '#1890ff',
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontSize: '16px',
            fontWeight: 'bold',
            marginRight: sidebarCollapsed ? 0 : 12,
            transition: 'margin 0.3s',
          }}
        >
          T
        </div>
        {!sidebarCollapsed && (
          <Title
            level={4}
            style={{
              margin: 0,
              color: 'white',
              fontSize: '18px',
              transition: 'opacity 0.3s',
            }}
          >
            {APP_CONFIG.TITLE}
          </Title>
        )}
      </div>

      {/* Navigation menu */}
      <Menu
        theme="dark"
        mode="inline"
        selectedKeys={selectedKeys}
        defaultOpenKeys={getDefaultOpenKeys()}
        onClick={handleMenuClick}
        items={menuItems}
        style={{
          border: 'none',
          height: 'calc(100vh - 64px)',
        }}
      />
    </Sider>
  )
}

export default Sidebar