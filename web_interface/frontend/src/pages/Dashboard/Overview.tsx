import React, { useEffect, useState } from 'react'
import { Card, Row, Col, Statistic, Progress, Table, Tag, Typography, Space, Button } from 'antd'
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  DollarOutlined,
  LineChartOutlined,
  RobotOutlined,
  DatabaseOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
} from '@ant-design/icons'
import { Line, Column } from '@ant-design/plots'

import { useAppSelector } from '@/store'
import { format } from '@/utils'

const { Title, Text } = Typography

// Mock data - in real app, this would come from API
const mockStats = {
  totalProfit: 125840.50,
  todayProfit: 2580.20,
  profitChange: 12.5,
  totalStrategies: 8,
  activeStrategies: 5,
  totalDatasets: 12,
  totalTrades: 1245,
}

const mockStrategies = [
  {
    id: '1',
    name: 'MA交叉策略',
    type: '算法交易',
    status: 'active',
    profit: 15680.50,
    profitRate: 8.5,
    trades: 125,
  },
  {
    id: '2',
    name: '动量策略',
    type: '高频交易',
    status: 'active',
    profit: 12450.30,
    profitRate: 6.2,
    trades: 89,
  },
  {
    id: '3',
    name: '套利策略',
    type: '投资组合',
    status: 'paused',
    profit: -2150.80,
    profitRate: -1.5,
    trades: 45,
  },
]

const mockEquityData = Array.from({ length: 30 }, (_, i) => ({
  date: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toLocaleDateString(),
  value: 100000 + Math.random() * 50000 + i * 1000,
}))

const mockTradeData = Array.from({ length: 7 }, (_, i) => ({
  date: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][i],
  trades: Math.floor(Math.random() * 50) + 20,
}))

const Overview: React.FC = () => {
  const { user } = useAppSelector(state => state.auth)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Simulate loading
    const timer = setTimeout(() => setLoading(false), 1000)
    return () => clearTimeout(timer)
  }, [])

  const strategyColumns = [
    {
      title: '策略名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string) => <Text strong>{text}</Text>,
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => <Tag color="blue">{type}</Tag>,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusConfig = {
          active: { color: 'success', text: '运行中', icon: <PlayCircleOutlined /> },
          paused: { color: 'warning', text: '已暂停', icon: <PauseCircleOutlined /> },
          stopped: { color: 'default', text: '已停止', icon: <PauseCircleOutlined /> },
        }
        const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.stopped
        return (
          <Tag color={config.color} icon={config.icon}>
            {config.text}
          </Tag>
        )
      },
    },
    {
      title: '收益',
      dataIndex: 'profit',
      key: 'profit',
      render: (profit: number) => (
        <Text type={profit >= 0 ? 'success' : 'danger'}>
          {profit >= 0 ? '+' : ''}{format.currency(profit)}
        </Text>
      ),
    },
    {
      title: '收益率',
      dataIndex: 'profitRate',
      key: 'profitRate',
      render: (rate: number) => (
        <Text type={rate >= 0 ? 'success' : 'danger'}>
          {rate >= 0 ? '+' : ''}{rate}%
        </Text>
      ),
    },
    {
      title: '交易次数',
      dataIndex: 'trades',
      key: 'trades',
    },
  ]

  const equityConfig = {
    data: mockEquityData,
    xField: 'date',
    yField: 'value',
    smooth: true,
    color: '#1890ff',
    point: {
      size: 2,
      shape: 'circle',
    },
    area: {
      style: {
        fill: 'l(270) 0:#ffffff 0.5:#7ec2f3 1:#1890ff',
        fillOpacity: 0.3,
      },
    },
  }

  const tradeConfig = {
    data: mockTradeData,
    xField: 'date',
    yField: 'trades',
    color: '#52c41a',
    columnStyle: {
      radius: [4, 4, 0, 0],
    },
  }

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>
          欢迎回来，{user?.username}！
        </Title>
        <Text type="secondary">
          这是您的交易概览，祝您交易愉快！
        </Text>
      </div>

      {/* Statistics Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic
              title="总收益"
              value={mockStats.totalProfit}
              precision={2}
              valueStyle={{ color: '#3f8600' }}
              prefix={<DollarOutlined />}
              suffix="¥"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic
              title="今日收益"
              value={mockStats.todayProfit}
              precision={2}
              valueStyle={{ color: mockStats.profitChange >= 0 ? '#3f8600' : '#cf1322' }}
              prefix={mockStats.profitChange >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
              suffix="¥"
            />
            <div style={{ marginTop: 8 }}>
              <Text type={mockStats.profitChange >= 0 ? 'success' : 'danger'} style={{ fontSize: '12px' }}>
                {mockStats.profitChange >= 0 ? '+' : ''}{mockStats.profitChange}% 较昨日
              </Text>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic
              title="运行策略"
              value={mockStats.activeStrategies}
              suffix={`/ ${mockStats.totalStrategies}`}
              prefix={<RobotOutlined />}
            />
            <Progress 
              percent={(mockStats.activeStrategies / mockStats.totalStrategies) * 100} 
              showInfo={false} 
              strokeColor="#1890ff"
              style={{ marginTop: 8 }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic
              title="数据集"
              value={mockStats.totalDatasets}
              prefix={<DatabaseOutlined />}
            />
            <div style={{ marginTop: 8 }}>
              <Text type="secondary" style={{ fontSize: '12px' }}>
                {mockStats.totalTrades} 笔历史交易
              </Text>
            </div>
          </Card>
        </Col>
      </Row>

      {/* Charts */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={16}>
          <Card title="资产曲线" loading={loading}>
            <Line {...equityConfig} height={300} />
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="近7天交易量" loading={loading}>
            <Column {...tradeConfig} height={300} />
          </Card>
        </Col>
      </Row>

      {/* Strategy Table */}
      <Card
        title="策略概览"
        loading={loading}
        extra={
          <Space>
            <Button type="primary">查看全部</Button>
            <Button>创建策略</Button>
          </Space>
        }
      >
        <Table
          columns={strategyColumns}
          dataSource={mockStrategies}
          rowKey="id"
          pagination={false}
          size="middle"
        />
      </Card>
    </div>
  )
}

export default Overview