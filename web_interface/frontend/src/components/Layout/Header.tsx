import React from 'react'
import { Layout, Button, Dropdown, Avatar, Badge, Space, Typography, theme } from 'antd'
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  BellOutlined,
  UserOutlined,
  SettingOutlined,
  LogoutOutlined,
  SunOutlined,
  MoonOutlined,
} from '@ant-design/icons'
import type { MenuProps } from 'antd'

import { useAppDispatch, useAppSelector } from '@/store'
import { toggleSidebar, toggleTheme } from '@/store/common/commonSlice'
import { logoutAsync } from '@/store/auth/authSlice'

const { Header: AntHeader } = Layout
const { Text } = Typography

const Header: React.FC = () => {
  const dispatch = useAppDispatch()
  const { sidebarCollapsed, theme: currentTheme, notifications } = useAppSelector(state => state.common)
  const { user } = useAppSelector(state => state.auth)
  const {
    token: { colorBgContainer },
  } = theme.useToken()

  // Count unread notifications
  const unreadCount = notifications.filter(n => !n.read).length

  // Handle logout
  const handleLogout = () => {
    dispatch(logoutAsync())
  }

  // User dropdown menu
  const userMenuItems: MenuProps['items'] = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人资料',
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '设置',
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ]

  // Notification dropdown menu
  const notificationMenuItems: MenuProps['items'] = notifications.slice(0, 5).map(notification => ({
    key: notification.id,
    label: (
      <div style={{ width: 250 }}>
        <div style={{ fontWeight: notification.read ? 'normal' : 'bold' }}>
          {notification.title}
        </div>
        {notification.message && (
          <div style={{ fontSize: '12px', color: '#666', marginTop: 4 }}>
            {notification.message}
          </div>
        )}
        <div style={{ fontSize: '12px', color: '#999', marginTop: 4 }}>
          {new Date(notification.timestamp).toLocaleString()}
        </div>
      </div>
    ),
  }))

  if (notificationMenuItems.length === 0) {
    notificationMenuItems.push({
      key: 'empty',
      label: (
        <div style={{ textAlign: 'center', padding: '16px', color: '#999' }}>
          暂无通知
        </div>
      ),
    })
  } else {
    notificationMenuItems.push(
      {
        type: 'divider',
      },
      {
        key: 'viewAll',
        label: (
          <div style={{ textAlign: 'center', color: '#1890ff' }}>
            查看全部通知
          </div>
        ),
      },
    )
  }

  return (
    <AntHeader
      style={{
        padding: '0 16px',
        background: colorBgContainer,
        borderBottom: '1px solid #f0f0f0',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center' }}>
        <Button
          type="text"
          icon={sidebarCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          onClick={() => dispatch(toggleSidebar())}
          style={{
            fontSize: '16px',
            width: 64,
            height: 64,
          }}
        />
      </div>

      <Space size="middle">
        {/* Theme toggle */}
        <Button
          type="text"
          icon={currentTheme === 'light' ? <MoonOutlined /> : <SunOutlined />}
          onClick={() => dispatch(toggleTheme())}
          style={{ fontSize: '16px' }}
        />

        {/* Notifications */}
        <Dropdown
          menu={{ items: notificationMenuItems }}
          trigger={['click']}
          placement="bottomRight"
        >
          <Button type="text" style={{ fontSize: '16px' }}>
            <Badge count={unreadCount} size="small">
              <BellOutlined />
            </Badge>
          </Button>
        </Dropdown>

        {/* User menu */}
        <Dropdown
          menu={{ items: userMenuItems }}
          trigger={['click']}
          placement="bottomRight"
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              cursor: 'pointer',
              padding: '4px 8px',
              borderRadius: '6px',
              transition: 'background-color 0.3s',
            }}
          >
            <Avatar
              size="small"
              icon={<UserOutlined />}
              src={user?.avatar}
              style={{ marginRight: 8 }}
            />
            <Text strong>{user?.username || '用户'}</Text>
          </div>
        </Dropdown>
      </Space>
    </AntHeader>
  )
}

export default Header