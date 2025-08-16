import React from 'react'
import { Card, Typography } from 'antd'

const { Title, Text } = Typography

const Analysis: React.FC = () => {
  return (
    <div>
      <Title level={2}>分析评估</Title>
      <Card>
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <Text type="secondary">分析评估页面正在开发中...</Text>
        </div>
      </Card>
    </div>
  )
}

export default Analysis