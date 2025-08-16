import React, { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  Card,
  Row,
  Col,
  Typography,
  Statistic,
  Table,
  Tag,
  Button,
  Space,
  Select,
  DatePicker,
  Tabs,
  Alert,
  Descriptions,
  Tooltip,
  Progress,
  message,
} from 'antd'
import {
  TrophyOutlined,
  RiseOutlined,
  FallOutlined,
  DollarOutlined,
  PercentageOutlined,
  BarChartOutlined,
  LineChartOutlined,
  PieChartOutlined,
  DownloadOutlined,
  ShareAltOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import { Line, Column, Pie, Scatter } from '@ant-design/plots'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'

import { format } from '@/utils'

const { Title, Text } = Typography
const { RangePicker } = DatePicker
const { TabPane } = Tabs
const { Option } = Select

interface BacktestResult {
  strategyId: string
  strategyName: string
  startDate: string
  endDate: string
  initialCash: number
  finalValue: number
  totalReturn: number
  annualizedReturn: number
  sharpeRatio: number
  sortinoRatio: number
  maxDrawdown: number
  maxDrawdownDuration: number
  winRate: number
  profitFactor: number
  averageWin: number
  averageLoss: number
  largestWin: number
  largestLoss: number
  totalTrades: number
  winningTrades: number
  losingTrades: number
  averageTradeDuration: number
  volatility: number
  beta: number
  alpha: number
  calmarRatio: number
}

interface Trade {
  id: string
  entryTime: string
  exitTime: string
  symbol: string
  side: 'long' | 'short'
  entryPrice: number
  exitPrice: number
  quantity: number
  pnl: number
  pnlPercent: number
  duration: number
  commission: number
}

interface EquityPoint {
  date: string
  strategyValue: number
  benchmarkValue: number
  drawdown: number
}

const BacktestResult: React.FC = () => {
  const [searchParams] = useSearchParams()
  const strategyId = searchParams.get('strategy')

  // Local state
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('summary')
  const [timeRange, setTimeRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null)
  const [benchmark, setBenchmark] = useState('SPY')

  // Mock data - in real app, fetch from API
  const [backtestResult] = useState<BacktestResult>({
    strategyId: strategyId || 'strategy-1',
    strategyName: 'MA双均线策略',
    startDate: '2023-01-01',
    endDate: '2024-01-01',
    initialCash: 100000,
    finalValue: 125840,
    totalReturn: 0.2584,
    annualizedReturn: 0.2584,
    sharpeRatio: 1.45,
    sortinoRatio: 2.1,
    maxDrawdown: 0.082,
    maxDrawdownDuration: 45,
    winRate: 0.634,
    profitFactor: 1.85,
    averageWin: 245.50,
    averageLoss: -132.80,
    largestWin: 1250.00,
    largestLoss: -680.00,
    totalTrades: 245,
    winningTrades: 155,
    losingTrades: 90,
    averageTradeDuration: 3.2,
    volatility: 0.178,
    beta: 0.85,
    alpha: 0.12,
    calmarRatio: 3.15,
  })

  const [equityData] = useState<EquityPoint[]>(
    Array.from({ length: 252 }, (_, i) => {
      const date = dayjs('2023-01-01').add(i, 'day').format('YYYY-MM-DD')
      const strategyValue = 100000 + Math.random() * 30000 + i * 100
      const benchmarkValue = 100000 + Math.random() * 20000 + i * 80
      const drawdown = -(Math.random() * 0.1)
      return { date, strategyValue, benchmarkValue, drawdown }
    })
  )

  const [trades] = useState<Trade[]>([
    {
      id: '1',
      entryTime: '2023-03-15T09:30:00Z',
      exitTime: '2023-03-18T15:30:00Z',
      symbol: 'AAPL',
      side: 'long',
      entryPrice: 152.50,
      exitPrice: 158.20,
      quantity: 100,
      pnl: 570.00,
      pnlPercent: 3.74,
      duration: 3.25,
      commission: 2.00,
    },
    {
      id: '2',
      entryTime: '2023-03-20T10:15:00Z',
      exitTime: '2023-03-22T14:45:00Z',
      symbol: 'MSFT',
      side: 'long',
      entryPrice: 280.30,
      exitPrice: 275.80,
      quantity: 50,
      pnl: -225.00,
      pnlPercent: -1.61,
      duration: 2.18,
      commission: 1.50,
    },
    // ... more trades
  ])

  useEffect(() => {
    loadBacktestData()
  }, [strategyId])

  const loadBacktestData = async () => {
    setLoading(true)
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000))
      // Data is already set above
    } catch (error) {
      message.error('加载回测结果失败')
    } finally {
      setLoading(false)
    }
  }

  const handleExport = () => {
    // In real app, generate and download report
    message.success('报告导出成功')
  }

  const handleShare = () => {
    // In real app, generate share link
    message.success('分享链接已复制到剪贴板')
  }

  // Chart configurations
  const equityChartData = equityData.reduce((acc, item) => {
    acc.push(
      { date: item.date, value: item.strategyValue, type: '策略净值' },
      { date: item.date, value: item.benchmarkValue, type: '基准净值' }
    )
    return acc
  }, [] as any[])

  const equityChartConfig = {
    data: equityChartData,
    xField: 'date',
    yField: 'value',
    seriesField: 'type',
    smooth: true,
    color: ['#1890ff', '#52c41a'],
    slider: {
      start: 0,
      end: 1,
    },
  }

  const drawdownChartConfig = {
    data: equityData.map(item => ({ date: item.date, drawdown: item.drawdown * 100 })),
    xField: 'date',
    yField: 'drawdown',
    color: '#f5222d',
    area: {
      style: {
        fill: 'l(270) 0:#ffffff 0.5:#ffccc7 1:#f5222d',
      },
    },
  }

  const monthlyReturnsData = Array.from({ length: 12 }, (_, i) => ({
    month: `${i + 1}月`,
    return: (Math.random() - 0.5) * 20,
  }))

  const monthlyReturnsConfig = {
    data: monthlyReturnsData,
    xField: 'month',
    yField: 'return',
    color: (datum: any) => datum.return > 0 ? '#52c41a' : '#f5222d',
    columnStyle: {
      radius: [4, 4, 0, 0],
    },
  }

  const tradeAnalysisData = [
    { type: '盈利交易', value: backtestResult.winningTrades },
    { type: '亏损交易', value: backtestResult.losingTrades },
  ]

  const tradeAnalysisConfig = {
    data: tradeAnalysisData,
    angleField: 'value',
    colorField: 'type',
    radius: 0.8,
    color: ['#52c41a', '#f5222d'],
    label: {
      type: 'spider',
      labelHeight: 28,
      content: '{name}\n{percentage}',
    },
  }

  const tradeColumns: ColumnsType<Trade> = [
    {
      title: '入场时间',
      dataIndex: 'entryTime',
      key: 'entryTime',
      width: 140,
      render: (time: string) => format.datetime(time),
    },
    {
      title: '出场时间',
      dataIndex: 'exitTime',
      key: 'exitTime',
      width: 140,
      render: (time: string) => format.datetime(time),
    },
    {
      title: '标的',
      dataIndex: 'symbol',
      key: 'symbol',
      width: 80,
    },
    {
      title: '方向',
      dataIndex: 'side',
      key: 'side',
      width: 80,
      render: (side: string) => (
        <Tag color={side === 'long' ? 'green' : 'red'}>
          {side === 'long' ? '多头' : '空头'}
        </Tag>
      ),
    },
    {
      title: '入场价',
      dataIndex: 'entryPrice',
      key: 'entryPrice',
      width: 100,
      align: 'right',
      render: (price: number) => `$${price.toFixed(2)}`,
    },
    {
      title: '出场价',
      dataIndex: 'exitPrice',
      key: 'exitPrice',
      width: 100,
      align: 'right',
      render: (price: number) => `$${price.toFixed(2)}`,
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      key: 'quantity',
      width: 80,
      align: 'right',
    },
    {
      title: '盈亏',
      dataIndex: 'pnl',
      key: 'pnl',
      width: 120,
      align: 'right',
      render: (pnl: number, record: Trade) => (
        <div>
          <Text type={pnl > 0 ? 'success' : 'danger'}>
            {pnl > 0 ? '+' : ''}${pnl.toFixed(2)}
          </Text>
          <br />
          <Text type={record.pnlPercent > 0 ? 'success' : 'danger'} style={{ fontSize: '12px' }}>
            ({record.pnlPercent > 0 ? '+' : ''}{record.pnlPercent.toFixed(2)}%)
          </Text>
        </div>
      ),
    },
    {
      title: '持仓时长',
      dataIndex: 'duration',
      key: 'duration',
      width: 100,
      align: 'right',
      render: (duration: number) => `${duration.toFixed(1)}天`,
    },
  ]

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div>
            <Title level={2} style={{ margin: 0 }}>
              回测结果分析
            </Title>
            <Text type="secondary">
              {backtestResult.strategyName} • {backtestResult.startDate} 至 {backtestResult.endDate}
            </Text>
          </div>
          <Space>
            <Select
              value={benchmark}
              onChange={setBenchmark}
              style={{ width: 120 }}
            >
              <Option value="SPY">标普500</Option>
              <Option value="QQQ">纳斯达克</Option>
              <Option value="IWM">罗素2000</Option>
            </Select>
            <RangePicker
              value={timeRange}
              onChange={setTimeRange}
              style={{ width: 240 }}
            />
            <Button icon={<ReloadOutlined />} onClick={loadBacktestData} loading={loading}>
              刷新
            </Button>
            <Button icon={<ShareAltOutlined />} onClick={handleShare}>
              分享
            </Button>
            <Button type="primary" icon={<DownloadOutlined />} onClick={handleExport}>
              导出报告
            </Button>
          </Space>
        </div>

        {/* Key Metrics */}
        <Row gutter={16}>
          <Col xs={24} sm={6}>
            <Card>
              <Statistic
                title="总收益率"
                value={backtestResult.totalReturn}
                precision={2}
                valueStyle={{ color: backtestResult.totalReturn >= 0 ? '#3f8600' : '#cf1322' }}
                prefix={backtestResult.totalReturn >= 0 ? <RiseOutlined /> : <FallOutlined />}
                suffix="%"
                formatter={(value) => `${Number(value) * 100}`}
              />
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card>
              <Statistic
                title="夏普比率"
                value={backtestResult.sharpeRatio}
                precision={2}
                valueStyle={{ color: backtestResult.sharpeRatio >= 1 ? '#3f8600' : '#cf1322' }}
                prefix={<TrophyOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card>
              <Statistic
                title="最大回撤"
                value={backtestResult.maxDrawdown}
                precision={2}
                valueStyle={{ color: '#cf1322' }}
                prefix={<FallOutlined />}
                suffix="%"
                formatter={(value) => `-${Number(value) * 100}`}
              />
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card>
              <Statistic
                title="胜率"
                value={backtestResult.winRate}
                precision={1}
                valueStyle={{ color: backtestResult.winRate >= 0.5 ? '#3f8600' : '#cf1322' }}
                prefix={<PercentageOutlined />}
                suffix="%"
                formatter={(value) => `${Number(value) * 100}`}
              />
            </Card>
          </Col>
        </Row>
      </div>

      {/* Main Content */}
      <Card>
        <Tabs activeKey={activeTab} onChange={setActiveTab} size="large">
          <TabPane tab="策略概要" key="summary">
            <Row gutter={24}>
              <Col xs={24} lg={16}>
                <Card title="净值曲线" style={{ marginBottom: 24 }}>
                  <Line {...equityChartConfig} height={300} />
                </Card>
                
                <Card title="回撤分析">
                  <Line {...drawdownChartConfig} height={200} />
                </Card>
              </Col>
              
              <Col xs={24} lg={8}>
                <Card title="绩效指标" style={{ marginBottom: 16 }}>
                  <Descriptions column={1} size="small">
                    <Descriptions.Item label="初始资金">
                      ${backtestResult.initialCash.toLocaleString()}
                    </Descriptions.Item>
                    <Descriptions.Item label="最终价值">
                      <Text type={backtestResult.finalValue > backtestResult.initialCash ? 'success' : 'danger'}>
                        ${backtestResult.finalValue.toLocaleString()}
                      </Text>
                    </Descriptions.Item>
                    <Descriptions.Item label="年化收益率">
                      <Text type={backtestResult.annualizedReturn >= 0 ? 'success' : 'danger'}>
                        {(backtestResult.annualizedReturn * 100).toFixed(2)}%
                      </Text>
                    </Descriptions.Item>
                    <Descriptions.Item label="Sortino比率">
                      {backtestResult.sortinoRatio.toFixed(2)}
                    </Descriptions.Item>
                    <Descriptions.Item label="Calmar比率">
                      {backtestResult.calmarRatio.toFixed(2)}
                    </Descriptions.Item>
                    <Descriptions.Item label="波动率">
                      {(backtestResult.volatility * 100).toFixed(2)}%
                    </Descriptions.Item>
                    <Descriptions.Item label="Beta系数">
                      {backtestResult.beta.toFixed(2)}
                    </Descriptions.Item>
                    <Descriptions.Item label="Alpha">
                      {(backtestResult.alpha * 100).toFixed(2)}%
                    </Descriptions.Item>
                  </Descriptions>
                </Card>

                <Card title="交易统计">
                  <Descriptions column={1} size="small">
                    <Descriptions.Item label="总交易数">
                      {backtestResult.totalTrades}
                    </Descriptions.Item>
                    <Descriptions.Item label="盈利交易">
                      <Text type="success">{backtestResult.winningTrades}</Text>
                    </Descriptions.Item>
                    <Descriptions.Item label="亏损交易">
                      <Text type="danger">{backtestResult.losingTrades}</Text>
                    </Descriptions.Item>
                    <Descriptions.Item label="盈利因子">
                      {backtestResult.profitFactor.toFixed(2)}
                    </Descriptions.Item>
                    <Descriptions.Item label="平均盈利">
                      <Text type="success">+${backtestResult.averageWin.toFixed(2)}</Text>
                    </Descriptions.Item>
                    <Descriptions.Item label="平均亏损">
                      <Text type="danger">${backtestResult.averageLoss.toFixed(2)}</Text>
                    </Descriptions.Item>
                    <Descriptions.Item label="最大盈利">
                      <Text type="success">+${backtestResult.largestWin.toFixed(2)}</Text>
                    </Descriptions.Item>
                    <Descriptions.Item label="最大亏损">
                      <Text type="danger">${backtestResult.largestLoss.toFixed(2)}</Text>
                    </Descriptions.Item>
                  </Descriptions>
                </Card>
              </Col>
            </Row>
          </TabPane>

          <TabPane tab="收益分析" key="returns">
            <Row gutter={24}>
              <Col xs={24} lg={12}>
                <Card title="月度收益分布" style={{ marginBottom: 24 }}>
                  <Column {...monthlyReturnsConfig} height={300} />
                </Card>
              </Col>
              
              <Col xs={24} lg={12}>
                <Card title="交易结果分布" style={{ marginBottom: 24 }}>
                  <Pie {...tradeAnalysisConfig} height={300} />
                </Card>
              </Col>
            </Row>

            <Card title="收益统计">
              <Row gutter={16}>
                <Col span={6}>
                  <Statistic
                    title="最佳月份"
                    value={15.2}
                    precision={1}
                    valueStyle={{ color: '#3f8600' }}
                    suffix="%"
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="最差月份"
                    value={-8.5}
                    precision={1}
                    valueStyle={{ color: '#cf1322' }}
                    suffix="%"
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="盈利月份占比"
                    value={75}
                    precision={0}
                    valueStyle={{ color: '#3f8600' }}
                    suffix="%"
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="连续盈利月数"
                    value={6}
                    precision={0}
                    valueStyle={{ color: '#1890ff' }}
                    suffix="个月"
                  />
                </Col>
              </Row>
            </Card>
          </TabPane>

          <TabPane tab="交易明细" key="trades">
            <Card title="交易记录" extra={
              <Button size="small" icon={<DownloadOutlined />}>
                导出交易记录
              </Button>
            }>
              <Table
                columns={tradeColumns}
                dataSource={trades}
                rowKey="id"
                pagination={{
                  pageSize: 20,
                  showSizeChanger: true,
                  showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
                }}
                scroll={{ x: 1000 }}
                summary={(data) => {
                  const totalPnl = data.reduce((sum, trade) => sum + trade.pnl, 0)
                  const totalCommission = data.reduce((sum, trade) => sum + trade.commission, 0)
                  return (
                    <Table.Summary.Row>
                      <Table.Summary.Cell index={0} colSpan={7}>
                        <Text strong>本页汇总</Text>
                      </Table.Summary.Cell>
                      <Table.Summary.Cell index={7}>
                        <Text type={totalPnl > 0 ? 'success' : 'danger'} strong>
                          {totalPnl > 0 ? '+' : ''}${totalPnl.toFixed(2)}
                        </Text>
                      </Table.Summary.Cell>
                      <Table.Summary.Cell index={8}>
                        <Text type="secondary">
                          手续费: ${totalCommission.toFixed(2)}
                        </Text>
                      </Table.Summary.Cell>
                    </Table.Summary.Row>
                  )
                }}
              />
            </Card>
          </TabPane>

          <TabPane tab="风险分析" key="risk">
            <Row gutter={24}>
              <Col xs={24} lg={12}>
                <Card title="风险指标" style={{ marginBottom: 24 }}>
                  <Descriptions column={1}>
                    <Descriptions.Item label="最大回撤">
                      <Progress
                        percent={backtestResult.maxDrawdown * 100}
                        strokeColor="#f5222d"
                        format={(percent) => `-${percent?.toFixed(1)}%`}
                      />
                    </Descriptions.Item>
                    <Descriptions.Item label="回撤持续时间">
                      {backtestResult.maxDrawdownDuration} 天
                    </Descriptions.Item>
                    <Descriptions.Item label="VaR (95%)">
                      <Text type="danger">-2.8%</Text>
                    </Descriptions.Item>
                    <Descriptions.Item label="CVaR (95%)">
                      <Text type="danger">-4.2%</Text>
                    </Descriptions.Item>
                    <Descriptions.Item label="下行波动率">
                      12.5%
                    </Descriptions.Item>
                  </Descriptions>
                </Card>
              </Col>
              
              <Col xs={24} lg={12}>
                <Card title="风险调整收益">
                  <Descriptions column={1}>
                    <Descriptions.Item label="信息比率">
                      0.78
                    </Descriptions.Item>
                    <Descriptions.Item label="跟踪误差">
                      8.2%
                    </Descriptions.Item>
                    <Descriptions.Item label="上行捕获率">
                      85%
                    </Descriptions.Item>
                    <Descriptions.Item label="下行捕获率">
                      72%
                    </Descriptions.Item>
                    <Descriptions.Item label="Sterling比率">
                      2.15
                    </Descriptions.Item>
                  </Descriptions>
                </Card>
              </Col>
            </Row>

            <Alert
              message="风险提示"
              description="回测结果基于历史数据，不代表未来表现。实际交易中可能面临滑点、流动性等额外风险因素。"
              type="warning"
              showIcon
              style={{ marginTop: 16 }}
            />
          </TabPane>
        </Tabs>
      </Card>
    </div>
  )
}

export default BacktestResult