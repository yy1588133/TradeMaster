import React from 'react'
import { Spin } from 'antd'
import { LoadingOutlined } from '@ant-design/icons'

interface LoadingSpinnerProps {
  size?: 'small' | 'default' | 'large'
  tip?: string
  spinning?: boolean
  children?: React.ReactNode
  className?: string
  style?: React.CSSProperties
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'default',
  tip,
  spinning = true,
  children,
  className,
  style
}) => {
  const antIcon = <LoadingOutlined style={{ fontSize: size === 'large' ? 32 : size === 'small' ? 14 : 24 }} spin />

  if (children) {
    return (
      <Spin 
        indicator={antIcon} 
        spinning={spinning} 
        tip={tip}
        className={className}
        style={style}
      >
        {children}
      </Spin>
    )
  }

  return (
    <div 
      className={`loading-spinner ${className || ''}`}
      style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        minHeight: '200px',
        ...style 
      }}
    >
      <Spin 
        indicator={antIcon} 
        spinning={spinning} 
        tip={tip}
        size={size}
      />
    </div>
  )
}

export default LoadingSpinner