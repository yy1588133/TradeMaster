import React, { useMemo } from 'react'
import { useLocation, Link } from 'react-router-dom'
import { Breadcrumb as AntBreadcrumb } from 'antd'
import { HomeOutlined } from '@ant-design/icons'

import { ROUTES } from '@/constants'

interface BreadcrumbItem {
  title: string
  path?: string
  icon?: React.ReactNode
}

const Breadcrumb: React.FC = () => {
  const location = useLocation()

  // Route to breadcrumb mapping
  const routeBreadcrumbMap: Record<string, BreadcrumbItem[]> = {
    [ROUTES.DASHBOARD]: [
      { title: '首页', path: ROUTES.DASHBOARD, icon: <HomeOutlined /> },
      { title: '仪表板' },
    ],
    [ROUTES.STRATEGIES]: [
      { title: '首页', path: ROUTES.DASHBOARD, icon: <HomeOutlined /> },
      { title: '策略管理' },
      { title: '策略列表' },
    ],
    [ROUTES.STRATEGY_CREATE]: [
      { title: '首页', path: ROUTES.DASHBOARD, icon: <HomeOutlined /> },
      { title: '策略管理' },
      { title: '策略列表', path: ROUTES.STRATEGIES },
      { title: '创建策略' },
    ],
    [ROUTES.DATASETS]: [
      { title: '首页', path: ROUTES.DASHBOARD, icon: <HomeOutlined /> },
      { title: '数据管理' },
    ],
    [ROUTES.TRAINING]: [
      { title: '首页', path: ROUTES.DASHBOARD, icon: <HomeOutlined /> },
      { title: '训练管理' },
    ],
    [ROUTES.ANALYSIS]: [
      { title: '首页', path: ROUTES.DASHBOARD, icon: <HomeOutlined /> },
      { title: '分析评估' },
    ],
    [ROUTES.PROFILE]: [
      { title: '首页', path: ROUTES.DASHBOARD, icon: <HomeOutlined /> },
      { title: '用户中心' },
      { title: '个人资料' },
    ],
    [ROUTES.SETTINGS]: [
      { title: '首页', path: ROUTES.DASHBOARD, icon: <HomeOutlined /> },
      { title: '用户中心' },
      { title: '系统设置' },
    ],
  }

  // Generate breadcrumb items
  const breadcrumbItems = useMemo(() => {
    const path = location.pathname
    
    // Handle dynamic routes
    let breadcrumbKey = path
    
    // Handle strategy detail route
    if (path.match(/^\/strategies\/[^/]+$/)) {
      breadcrumbKey = '/strategies/:id'
    }
    
    // Get breadcrumb items from mapping
    let items = routeBreadcrumbMap[breadcrumbKey] || [
      { title: '首页', path: ROUTES.DASHBOARD, icon: <HomeOutlined /> },
      { title: '页面' },
    ]
    
    // Handle strategy detail page
    if (path.match(/^\/strategies\/[^/]+$/)) {
      items = [
        { title: '首页', path: ROUTES.DASHBOARD, icon: <HomeOutlined /> },
        { title: '策略管理' },
        { title: '策略列表', path: ROUTES.STRATEGIES },
        { title: '策略详情' },
      ]
    }

    // Convert to Ant Design breadcrumb items format
    return items.map((item, index) => ({
      key: index,
      title: item.path ? (
        <Link to={item.path} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          {item.icon}
          {item.title}
        </Link>
      ) : (
        <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          {item.icon}
          {item.title}
        </span>
      ),
    }))
  }, [location.pathname])

  // Don't show breadcrumb on login/register pages
  if ([ROUTES.LOGIN, ROUTES.REGISTER].includes(location.pathname)) {
    return null
  }

  return (
    <AntBreadcrumb
      items={breadcrumbItems}
      style={{
        margin: '16px 0',
        fontSize: '14px',
      }}
    />
  )
}

export default Breadcrumb