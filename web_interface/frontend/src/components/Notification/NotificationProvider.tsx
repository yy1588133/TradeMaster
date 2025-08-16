import React, { createContext, useContext, useCallback } from 'react'
import { notification } from 'antd'
import { 
  CheckCircleOutlined, 
  ExclamationCircleOutlined, 
  InfoCircleOutlined, 
  CloseCircleOutlined 
} from '@ant-design/icons'

interface NotificationContextType {
  success: (message: string, description?: string, duration?: number) => void
  error: (message: string, description?: string, duration?: number) => void
  warning: (message: string, description?: string, duration?: number) => void
  info: (message: string, description?: string, duration?: number) => void
  close: (key: string) => void
  destroy: () => void
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined)

interface NotificationProviderProps {
  children: React.ReactNode
}

export const NotificationProvider: React.FC<NotificationProviderProps> = ({ children }) => {
  // 配置全局通知样式
  React.useEffect(() => {
    notification.config({
      placement: 'topRight',
      duration: 4.5,
      rtl: false,
      maxCount: 3,
    })
  }, [])

  const success = useCallback((message: string, description?: string, duration?: number) => {
    notification.success({
      message,
      description,
      duration,
      icon: <CheckCircleOutlined style={{ color: '#52c41a' }} />,
      style: {
        borderLeft: '4px solid #52c41a',
      },
    })
  }, [])

  const error = useCallback((message: string, description?: string, duration?: number) => {
    notification.error({
      message,
      description,
      duration: duration || 6, // 错误消息显示更久
      icon: <CloseCircleOutlined style={{ color: '#ff4d4f' }} />,
      style: {
        borderLeft: '4px solid #ff4d4f',
      },
    })
  }, [])

  const warning = useCallback((message: string, description?: string, duration?: number) => {
    notification.warning({
      message,
      description,
      duration,
      icon: <ExclamationCircleOutlined style={{ color: '#faad14' }} />,
      style: {
        borderLeft: '4px solid #faad14',
      },
    })
  }, [])

  const info = useCallback((message: string, description?: string, duration?: number) => {
    notification.info({
      message,
      description,
      duration,
      icon: <InfoCircleOutlined style={{ color: '#1890ff' }} />,
      style: {
        borderLeft: '4px solid #1890ff',
      },
    })
  }, [])

  const close = useCallback((key: string) => {
    notification.close(key)
  }, [])

  const destroy = useCallback(() => {
    notification.destroy()
  }, [])

  const value: NotificationContextType = {
    success,
    error,
    warning,
    info,
    close,
    destroy,
  }

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  )
}

export const useNotification = (): NotificationContextType => {
  const context = useContext(NotificationContext)
  if (context === undefined) {
    throw new Error('useNotification must be used within a NotificationProvider')
  }
  return context
}

export default NotificationProvider