import React from 'react'
import { Grid } from 'antd'

const { useBreakpoint } = Grid

interface ResponsiveContainerProps {
  children: React.ReactNode
  className?: string
  style?: React.CSSProperties
  maxWidth?: number
  padding?: {
    xs?: number
    sm?: number
    md?: number
    lg?: number
    xl?: number
    xxl?: number
  }
}

const ResponsiveContainer: React.FC<ResponsiveContainerProps> = ({
  children,
  className,
  style,
  maxWidth = 1200,
  padding = {
    xs: 16,
    sm: 20,
    md: 24,
    lg: 24,
    xl: 24,
    xxl: 24
  }
}) => {
  const screens = useBreakpoint()

  // 根据屏幕尺寸确定padding
  const getPadding = () => {
    if (screens.xxl) return padding.xxl || 24
    if (screens.xl) return padding.xl || 24
    if (screens.lg) return padding.lg || 24
    if (screens.md) return padding.md || 24
    if (screens.sm) return padding.sm || 20
    return padding.xs || 16
  }

  const containerStyle: React.CSSProperties = {
    maxWidth,
    margin: '0 auto',
    padding: `0 ${getPadding()}px`,
    width: '100%',
    ...style
  }

  return (
    <div 
      className={`responsive-container ${className || ''}`}
      style={containerStyle}
    >
      {children}
    </div>
  )
}

export default ResponsiveContainer