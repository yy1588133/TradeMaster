import React from 'react'
import { useNavigate } from 'react-router-dom'
import { Result, Button } from 'antd'

import { ROUTES } from '@/constants'

const NotFound: React.FC = () => {
  const navigate = useNavigate()

  return (
    <div style={{ 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center', 
      minHeight: '100vh',
      background: '#f0f2f5'
    }}>
      <Result
        status="404"
        title="404"
        subTitle="抱歉，您访问的页面不存在。"
        extra={
          <Button type="primary" onClick={() => navigate(ROUTES.DASHBOARD)}>
            返回首页
          </Button>
        }
      />
    </div>
  )
}

export default NotFound