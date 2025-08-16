import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Card,
  Row,
  Col,
  Button,
  Space,
  Typography,
  Tag,
  Statistic,
  Tabs,
  Table,
  Alert,
  Descriptions,
  Progress,
  Tooltip,
  Modal,
  message,
  Divider,
  Timeline,
  Empty,
  Spin,
} from 'antd'
import {
  ArrowLeftOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  StopOutlined,
  EditOutlined,
  DeleteOutlined,
  BarChartOutlined,
  SettingOutlined,
  HistoryOutlined,
  ReloadOutlined,
  DownloadOutlined,
  ShareAltOutlined,
  CopyOutlined,
} from '@ant-design/icons'
import { Line, Column, Pie } from '@ant-design/plots'
import type { ColumnsType } from 'antd/es/table'

import { useAppDispatch, useAppSelector } from '@/store'
import { 
  getStrategyAsync, 
  startStrategyAsync, 
  stopStrategyAsync, 
  deleteStrategyAsync 
} from '@/store/strategy/strategySlice'
import { ROUTES, STRATEGY_STATUS } from '@/constants'
import { Strategy } from '@/types'
import { format } from '@/utils'

const { Title, Text, Paragraph } = Typography
const { TabPane } = Tabs

interface Trade {
  id: string
  timestamp: string
  symbol: string
  side: 'buy' | 'sell'
  quantity: number
  price: number
  commission: number
  pnl: number
}

interface PerformanceMetrics {
  totalReturn: number
  annualizedReturn: number
  sharpeRatio: number
  maxDrawdown: number
  winRate: number
  profitFactor: number
  averageWin: number
  averageLoss: number
  totalTrades: number
  winningTrades: number
  losingTrades: number
  largestWin: number
  largestLoss: number
}

const StrategyDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const dispatch = useAppDispatch()
  const { currentStrategy, loading } = useAppSelector(state => state.strategy)

  // Local state
  const [activeTab, setActiveTab] = useState('overview')
  const [performanceLoading, setPerformanceLoading] = useState(false)
  const [tradesLoading, setTradesLoading] = useState(false)

  // Mock data - in real app, fetch from API
  const [performanceMetrics] = useState<PerformanceMetrics>({
    totalReturn: 0.158,
    annualizedReturn: 0.126,
    sharpeRatio: 1.45,
    maxDrawdown: 0.082,
    winRate: 0.634,
    profitFactor: 1.85,
    averageWin: 245.50,
    averageLoss: -132.80,
    totalTrades: 245,
    winningTrades: 155,
    losingTrades: 90,
    largestWin: 1250.00,
    largestLoss: -680.00,
  })

  const [equityData] = useState(
    Array.from({ length: 30 }, (_, i) => ({
      date: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      equity: 100000 + Math.random() * 20000 + i * 500,
      benchmark: 100000 + Math.random() * 15000 + i * 300,
    }))
  )

  const [recentTrades] = useState<Trade[]>([
    {
      id: '1',
      timestamp: '2024-01-15T10:30:00Z',
      symbol: 'BTCUSDT',
      side: 'buy',
      quantity: 0.1,
      price: 42500,
      commission: 4.25,
      pnl: 0,
    },
    {
      id: '2',
      timestamp: '2024-01-15T14:20:00Z',
      symbol: 'BTCUSDT',
      side: 'sell',
      quantity: 0.1,
      price: 43200,
      commission: 4.32,
      pnl: 691.43,
    },
    {
      id: '3',
      timestamp: '2024-01-15T16:45:00Z',
      symbol: 'ETHUSDT',
      side: 'buy',
      quantity: 2.5,
      price: 2580,
      commission: 6.45,
      pnl: 0,
    },
  ])

  const [executionHistory] = useState([
    {
      timestamp: '2024-01-15T10:00:00Z',
      event: '策略启动',
      description: '策略成功启动，开始执行交易逻辑',
      status: 'success',
    },
    {
      timestamp: '2024-01-15T10:30:00Z',
      event: '买入信号',
      description: '检测到买入信号，执行 BTCUSDT 买入订单',
      status: 'info',
    },
    {
      timestamp: '2024-01-15T14:20:00Z',
      event: '卖出信号',
      description: '检测到卖出信号，执行 BTCUSDT 卖出订单，获利 $691.43',
      status: 'success',
    },
    {
      timestamp: '2024-01-15T16:45:00Z',
      event: '风险控制',
      description: '持仓风险检查通过，执行 ETHUSDT 买入订单',
      status: 'warning',
    },
  ])

  useEffect(() => {
    if (id) {
      dispatch(getStrategyAsync(id))
    }
  }, [dispatch, id])

  const handleStart = async () => {
    if (!id) return
    try {
      await dispatch(startStrategyAsync(id)).unwrap()
      message.success('策略启动成功')
      dispatch(getStrategyAsync(id))
    } catch (error: any) {
      message.error(`启动失败：${error.message || error}`)
    }
  }

  const handleStop = async () => {
    if (!id) return
    try {
      await dispatch(stopStrategyAsync(id)).unwrap()
      message.success('策略停止成功')
      dispatch(getStrategyAsync(id))
    } catch (error: any) {
      message.error(`停止失败：${error.message || error}`)
    }
  }

  const handleDelete = async () => {
    if (!id) return
    Modal.confirm({
      title: '确认删除策略？',
      content: `将删除策略"${currentStrategy?.name}"，此操作不可恢复`,
      okText: '删除',
      okType: 'danger',
      onOk: async () => {
        try {
          await dispatch(deleteStrategyAsync(id)).unwrap()
          message.success('策略删除成功')
          navigate(ROUTES.STRATEGIES)
        } catch (error: any) {
          message.error(`删除失败：${error.message || error}`)
        }
      },
    })
  }

  const getStatusTag = (status: string) => {
    const statusConfig = STRATEGY_STATUS[status?.toUpperCase() as keyof typeof STRATEGY_STATUS]
    if (!statusConfig) return <Tag>{status}</Tag>

    const icons = {
      active: <PlayCircleOutlined />,
      paused: <PauseCircleOutlined />,
      stopped: <StopOutlined />,
      draft: <EditOutlined />,
    }

    return (
      <Tag color={statusConfig.color} icon={icons[status as keyof typeof icons]} size="large">
        {statusConfig.label}
      </Tag>
    )
  }

  const tradeColumns: ColumnsType<Trade> = [
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 150,
      render: (timestamp: string) => format.datetime(timestamp),
    },
    {
      title: '标的',
      dataIndex: 'symbol',
      key: 'symbol',
      width: 100,
    },
    {
      title: '方向',
      dataIndex: 'side',
      key: 'side',
      width: 80,
      render: (side: string) => (
        <Tag color={side === 'buy' ? 'green' : 'red'}>
          {side === 'buy' ? '买入' : '卖出'}
        </Tag>
      ),
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      key: 'quantity',
      width: 100,
      align: 'right',
      render: (quantity: number) => quantity.toFixed(4),
    },
    {
      title: '价格',
      dataIndex: 'price',
      key: 'price',
      width: 120,
      align: 'right',
      render: (price: number) => `$${price.toLocaleString()}`,
    },
    {
      title: '手续费',
      dataIndex: 'commission',
      key: 'commission',
      width: 100,
      align: 'right',
      render: (commission: number) => `$${commission.toFixed(2)}`,
    },
    {
      title: '盈亏',
      dataIndex: 'pnl',
      key: 'pnl',
      width: 120,
      align: 'right',
      render: (pnl: number) => (
        <Text type={pnl > 0 ? 'success' : pnl < 0 ? 'danger' : undefined}>
          {pnl > 0 ? '+' : ''}${pnl.toFixed(2)}
        </Text>
      ),
    },
  ]

  const equityChartConfig = {
    data: equityData.reduce((acc, item) => {
      acc.push(
        { date: item.date, value: item.equity, category: '策略净值' },
        { date: item.date, value: item.benchmark, category: '基准净值' }
      )
      return acc
    }, [] as any[]),
    xField: 'date',
    yField: 'value',
    seriesField: 'category',
    smooth: true,
    color: ['#1890ff', '#52c41a'],
  }

  const returnDistributionData = Array.from({ length: 20 }, (_, i) => ({
    return: (i - 10) * 0.5,
    frequency: Math.random() * 50 + 10,
  }))

  const distributionChartConfig = {
    data: returnDistributionData,
    xField: 'return',
    yField: 'frequency',
    color: '#1890ff',
    columnStyle: {
      radius: [2, 2, 0, 0],
    },
  }

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size="large" />
      </div>
    )
  }

  if (!currentStrategy) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Empty description="策略不存在或已被删除" />
      </div>
    )
  }

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: 8 }}>
              <Button
                icon={<ArrowLeftOutlined />}
                onClick={() => navigate(ROUTES.STRATEGIES)}
                style={{ marginRight: 16 }}
              >
                返回
              </Button>
              <Title level={2} style={{ margin: 0, marginRight: 16 }}>
                {currentStrategy.name}
              </Title>
              {getStatusTag(currentStrategy.status)}
            </div>
            <Text type="secondary">{currentStrategy.description}</Text>
          </div>
          
          <Space>
            <Button icon={<ReloadOutlined />} onClick={() => dispatch(getStrategyAsync(id!))}>
              刷新
            </Button>
            <Button icon={<ShareAltOutlined />}>分享</Button>
            <Button icon={<CopyOutlined />}>克隆</Button>
            <Button icon={<DownloadOutlined />}>导出</Button>
            {currentStrategy.status === 'stopped' || currentStrategy.status === 'paused' ? (
              <Button type="primary" icon={<PlayCircleOutlined />} onClick={handleStart}>
                启动
              </Button>
            ) : (
              <Button danger icon={<StopOutlined />} onClick={handleStop}>
                停止
              </Button>
            )}
            <Button icon={<EditOutlined />} onClick={() => navigate(`${ROUTES.STRATEGIES}/${id}/edit`)}>
              编辑
            </Button>
            <Button danger icon={<DeleteOutlined />} onClick={handleDelete}>
              删除
            </Button>
          </Space>
        </div>
      </div>

      {/* Performance Overview */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={8} lg={6}>
          <Card>
            <Statistic
              title="总收益率"
              value={performanceMetrics.totalReturn}
              precision={2}
              valueStyle={{ color: performanceMetrics.totalReturn >= 0 ? '#3f8600' : '#cf1322' }}
              suffix="%"
              formatter={(value) => `${Number(value) * 100}`}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8} lg={6}>
          <Card>
            <Statistic
              title="夏普比率"
              value={performanceMetrics.sharpeRatio}
              precision={2}
              valueStyle={{ color: performanceMetrics.sharpeRatio >= 1 ? '#3f8600' : '#cf1322' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8} lg={6}>
          <Card>
            <Statistic
              title="最大回撤"
              value={performanceMetrics.maxDrawdown}
              precision={2}
              valueStyle={{ color: '#cf1322' }}
              suffix="%"
              formatter={(value) => `-${Number(value) * 100}`}
            />
          </Card>
        </Col>
        <Col xs={24} sm={24} lg={6}>
          <Card>
            <Statistic
              title="胜率"
              value={performanceMetrics.winRate}
              precision={1}
              valueStyle={{ color: performanceMetrics.winRate >= 0.5 ? '#3f8600' : '#cf1322' }}
              suffix="%"
              formatter={(value) => `${Number(value) * 100}`}
            />
          </Card>
        </Col>
      </Row>

      {/* Main Content */}
      <Card>
        <Tabs activeKey={activeTab} onChange={setActiveTab} size="large">
          <TabPane tab="概览" key="overview">
            <Row gutter={24}>
              <Col xs={24} lg={16}>
                <Card title="净值曲线" style={{ marginBottom: 24 }}>
                  <Line {...equityChartConfig} height={300} />
                </Card>
                
                <Card title="收益分布">
                  <Column {...distributionChartConfig} height={200} />
                </Card>
              </Col>
              
              <Col xs={24} lg={8}>
                <Card title="策略信息" style={{ marginBottom: 24 }}>
                  <Descriptions column={1} size="small">
                    <Descriptions.Item label="策略类型">
                      {currentStrategy.type}
                    </Descriptions.Item>
                    <Descriptions.Item label="创建时间">
                      {format.datetime(currentStrategy.createdAt)}
                    </Descriptions.Item>
                    <Descriptions.Item label="最后更新">
                      {format.datetime(currentStrategy.updatedAt)}
                    </Descriptions.Item>
                    <Descriptions.Item label="运行时长">
                      <Text>72小时15分钟</Text>
                    </Descriptions.Item>
                  </Descriptions>
                </Card>
                
                <Card title="风险指标" style={{ marginBottom: 24 }}>
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                        <Text type="secondary">波动率</Text>
                        <Text>12.5%</Text>
                      </div>
                      <Progress percent={62.5} showInfo={false} strokeColor="#faad14" />
                    </div>
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                        <Text type="secondary">Beta系数</Text>
                        <Text>0.85</Text>
                      </div>
                      <Progress percent={85} showInfo={false} strokeColor="#52c41a" />
                    </div>
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                        <Text type="secondary">相关性</Text>
                        <Text>0.72</Text>
                      </div>
                      <Progress percent={72} showInfo={false} strokeColor="#1890ff" />
                    </div>
                  </Space>
                </Card>
                
                <Card title="持仓概览">
                  <div style={{ textAlign: 'center', padding: '20px 0' }}>
                    <Text type="secondary">暂无持仓数据</Text>
                  </div>
                </Card>
              </Col>
            </Row>
          </TabPane>

          <TabPane tab="交易记录" key="trades">
            <Card title="最近交易" extra={
              <Button size="small">导出全部</Button>
            }>
              <Table
                columns={tradeColumns}
                dataSource={recentTrades}
                rowKey="id"
                loading={tradesLoading}
                pagination={{
                  pageSize: 10,
                  showSizeChanger: true,
                  showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
                }}
              />
            </Card>
          </TabPane>

          <TabPane tab="性能分析" key="performance">
            <Row gutter={24}>
              <Col xs={24} lg={12}>
                <Card title="详细指标" style={{ marginBottom: 24 }}>
                  <Descriptions column={2} size="small">
                    <Descriptions.Item label="总收益">
                      <Text type={performanceMetrics.totalReturn >= 0 ? 'success' : 'danger'}>
                        {performanceMetrics.totalReturn >= 0 ? '+' : ''}{(performanceMetrics.totalReturn * 100).toFixed(2)}%
                      </Text>
                    </Descriptions.Item>
                    <Descriptions.Item label="年化收益">
                      <Text type={performanceMetrics.annualizedReturn >= 0 ? 'success' : 'danger'}>
                        {performanceMetrics.annualizedReturn >= 0 ? '+' : ''}{(performanceMetrics.annualizedReturn * 100).toFixed(2)}%
                      </Text>
                    </Descriptions.Item>
                    <Descriptions.Item label="盈利因子">
                      {performanceMetrics.profitFactor.toFixed(2)}
                    </Descriptions.Item>
                    <Descriptions.Item label="平均盈利">
                      <Text type="success">+${performanceMetrics.averageWin.toFixed(2)}</Text>
                    </Descriptions.Item>
                    <Descriptions.Item label="平均亏损">
                      <Text type="danger">${performanceMetrics.averageLoss.toFixed(2)}</Text>
                    </Descriptions.Item>
                    <Descriptions.Item label="最大盈利">
                      <Text type="success">+${performanceMetrics.largestWin.toFixed(2)}</Text>
                    </Descriptions.Item>
                    <Descriptions.Item label="最大亏损">
                      <Text type="danger">${performanceMetrics.largestLoss.toFixed(2)}</Text>
                    </Descriptions.Item>
                    <Descriptions.Item label="总交易数">
                      {performanceMetrics.totalTrades}
                    </Descriptions.Item>
                    <Descriptions.Item label="盈利交易">
                      <Text type="success">{performanceMetrics.winningTrades}</Text>
                    </Descriptions.Item>
                    <Descriptions.Item label="亏损交易">
                      <Text type="danger">{performanceMetrics.losingTrades}</Text>
                    </Descriptions.Item>
                  </Descriptions>
                </Card>
              </Col>
              
              <Col xs={24} lg={12}>
                <Card title="收益构成">
                  <div style={{ textAlign: 'center', padding: '50px 0' }}>
                    <Text type="secondary">收益分析图表开发中...</Text>
                  </div>
                </Card>
              </Col>
            </Row>
          </TabPane>

          <TabPane tab="执行历史" key="history">
            <Card title="执行历史">
              <Timeline mode="left">
                {executionHistory.map((item, index) => (
                  <Timeline.Item
                    key={index}
                    color={
                      item.status === 'success' ? 'green' :
                      item.status === 'warning' ? 'orange' :
                      item.status === 'error' ? 'red' : 'blue'
                    }
                    label={format.datetime(item.timestamp)}
                  >
                    <div>
                      <Text strong>{item.event}</Text>
                      <br />
                      <Text type="secondary">{item.description}</Text>
                    </div>
                  </Timeline.Item>
                ))}
              </Timeline>
            </Card>
          </TabPane>

          <TabPane tab="配置" key="config">
            <Card title="策略配置">
              <div style={{ background: '#f5f5f5', padding: 16, borderRadius: 4 }}>
                <pre style={{ margin: 0, fontSize: '12px', overflow: 'auto' }}>
                  {JSON.stringify(currentStrategy.config, null, 2)}
                </pre>
              </div>
            </Card>
          </TabPane>
        </Tabs>
      </Card>
    </div>
  )
}

export default StrategyDetail