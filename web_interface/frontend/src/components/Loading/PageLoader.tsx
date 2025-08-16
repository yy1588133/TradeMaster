import React from 'react'
import { Card, Result } from 'antd'
import { ExclamationCircleOutlined } from '@ant-design/icons'
import LoadingSpinner from './LoadingSpinner'

interface PageLoaderProps {
  loading?: boolean
  error?: string | null
  children: React.ReactNode
  minHeight?: number
  showCard?: boolean
}

const PageLoader: React.FC<PageLoaderProps> = ({
  loading = false,
  error = null,
  children,
  minHeight = 400,
  showCard = true
}) => {
  const content = () => {
    if (loading) {
      return (
        <LoadingSpinner 
          size="large" 
          tip="加载中..."
          style={{ minHeight }}
        />
      )
    }

    if (error) {
      return (
        <Result
          status="error"
          icon={<ExclamationCircleOutlined />}
          title="加载失败"
          subTitle={error}
          style={{ minHeight }}
        />
      )
    }

    return children
  }

  if (showCard) {
    return (
      <Card 
        bordered={false}
        style={{ minHeight }}
      >
        {content()}
      </Card>
    )
  }

  return <div style={{ minHeight }}>{content()}</div>
}

export default PageLoader