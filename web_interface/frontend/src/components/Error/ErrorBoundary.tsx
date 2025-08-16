import React, { Component, ErrorInfo, ReactNode } from 'react'
import { Result, Button, Card, Typography, Collapse, Space } from 'antd'
import { BugOutlined, ReloadOutlined, HomeOutlined } from '@ant-design/icons'

const { Text, Paragraph } = Typography
const { Panel } = Collapse

interface Props {
  children: ReactNode
  fallback?: ReactNode
  onError?: (error: Error, errorInfo: ErrorInfo) => void
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null
  }

  public static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null
    }
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo)
    
    this.setState({
      error,
      errorInfo
    })

    // 调用父组件的错误处理函数
    if (this.props.onError) {
      this.props.onError(error, errorInfo)
    }

    // 可以在这里添加错误上报逻辑
    // reportError(error, errorInfo)
  }

  private handleReload = () => {
    window.location.reload()
  }

  private handleGoHome = () => {
    window.location.href = '/'
  }

  private handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    })
  }

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div style={{ padding: '24px', minHeight: '100vh', backgroundColor: '#f5f5f5' }}>
          <Card style={{ maxWidth: 800, margin: '0 auto', marginTop: '60px' }}>
            <Result
              status="error"
              icon={<BugOutlined style={{ color: '#ff4d4f' }} />}
              title="页面出现了错误"
              subTitle="抱歉，页面遇到了意外错误。您可以尝试刷新页面或返回首页。"
              extra={
                <Space>
                  <Button type="primary" icon={<ReloadOutlined />} onClick={this.handleReload}>
                    刷新页面
                  </Button>
                  <Button icon={<HomeOutlined />} onClick={this.handleGoHome}>
                    返回首页
                  </Button>
                  <Button onClick={this.handleReset}>
                    重试
                  </Button>
                </Space>
              }
            />

            {process.env.NODE_ENV === 'development' && this.state.error && (
              <div style={{ marginTop: 24 }}>
                <Collapse>
                  <Panel header="错误详情 (仅开发环境显示)" key="1">
                    <div style={{ marginBottom: 16 }}>
                      <Text strong>错误信息:</Text>
                      <Paragraph 
                        code 
                        copyable
                        style={{ 
                          backgroundColor: '#fff2f0', 
                          padding: 8, 
                          marginTop: 8,
                          border: '1px solid #ffccc7',
                          borderRadius: 4
                        }}
                      >
                        {this.state.error.message}
                      </Paragraph>
                    </div>

                    <div style={{ marginBottom: 16 }}>
                      <Text strong>错误堆栈:</Text>
                      <Paragraph 
                        code 
                        copyable
                        style={{ 
                          backgroundColor: '#f6f6f6', 
                          padding: 8, 
                          marginTop: 8,
                          border: '1px solid #d9d9d9',
                          borderRadius: 4,
                          fontSize: '12px',
                          lineHeight: '1.4',
                          maxHeight: '200px',
                          overflow: 'auto'
                        }}
                      >
                        {this.state.error.stack}
                      </Paragraph>
                    </div>

                    {this.state.errorInfo && (
                      <div>
                        <Text strong>组件堆栈:</Text>
                        <Paragraph 
                          code 
                          copyable
                          style={{ 
                            backgroundColor: '#f6f6f6', 
                            padding: 8, 
                            marginTop: 8,
                            border: '1px solid #d9d9d9',
                            borderRadius: 4,
                            fontSize: '12px',
                            lineHeight: '1.4',
                            maxHeight: '200px',
                            overflow: 'auto'
                          }}
                        >
                          {this.state.errorInfo.componentStack}
                        </Paragraph>
                      </div>
                    )}
                  </Panel>
                </Collapse>
              </div>
            )}
          </Card>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary