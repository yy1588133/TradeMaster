import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Card,
  Table,
  Button,
  Space,
  Typography,
  Input,
  Select,
  Tag,
  Progress,
  Row,
  Col,
  Statistic,
  Modal,
  message,
  Tooltip,
  Timeline,
  Alert,
  Descriptions,
} from 'antd'
import {
  PlusOutlined,
  SearchOutlined,
  ReloadOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  StopOutlined,
  EyeOutlined,
  DeleteOutlined,
  HistoryOutlined,
  RobotOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  LineChartOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { Line } from '@ant-design/plots'

import { TRAINING_STATUS } from '@/constants'
import { TrainingJob } from '@/types'
import { format } from '@/utils'

const { Title, Text } = Typography
const { Search } = Input
const { Option } = Select

interface TrainingMetrics {
  epoch: number
  trainLoss: number
  validationLoss: number
  accuracy?: number
  timestamp: string
}

const TrainingList: React.FC = () => {
  const navigate = useNavigate()

  // Local state
  const [loading, setLoading] = useState(false)
  const [trainingJobs, setTrainingJobs] = useState<TrainingJob[]>([])
  const [searchText, setSearchText] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([])
  const [detailVisible, setDetailVisible] = useState(false)
  const [currentJob, setCurrentJob] = useState<TrainingJob | null>(null)

  // Mock data - in real app, fetch from API
  const mockTrainingJobs: TrainingJob[] = [
    {
      id: '1',
      name: 'MA交叉策略训练',
      strategyId: 'strategy-1',
      status: 'running',
      progress: 65,
      config: {
        datasetId: 'dataset-1',
        trainRatio: 0.7,
        validationRatio: 0.2,
        testRatio: 0.1,
        epochs: 100,
        batchSize: 32,
        learningRate: 0.001,
        optimizer: 'adam',
      },
      results: {
        trainLoss: [0.8, 0.6, 0.45, 0.35, 0.28],
        validationLoss: [0.9, 0.7, 0.55, 0.42, 0.35],
        metrics: {
          accuracy: 0.82,
          precision: 0.79,
          recall: 0.85,
          f1Score: 0.82,
        },
        bestEpoch: 45,
        modelPath: '/models/ma_cross_strategy_v1.pkl',
      },
      createdAt: '2024-01-15T10:00:00Z',
      updatedAt: '2024-01-15T14:30:00Z',
      startedAt: '2024-01-15T10:05:00Z',
    },
    {
      id: '2',
      name: 'RSI反转策略训练',
      strategyId: 'strategy-2',
      status: 'completed',
      progress: 100,
      config: {
        datasetId: 'dataset-2',
        trainRatio: 0.8,
        validationRatio: 0.15,
        testRatio: 0.05,
        epochs: 50,
        batchSize: 64,
        learningRate: 0.01,
        optimizer: 'sgd',
      },
      results: {
        trainLoss: [1.2, 0.9, 0.7, 0.55, 0.42, 0.35, 0.31],
        validationLoss: [1.3, 1.0, 0.8, 0.65, 0.52, 0.45, 0.41],
        metrics: {
          accuracy: 0.78,
          precision: 0.75,
          recall: 0.82,
          f1Score: 0.78,
        },
        bestEpoch: 35,
        modelPath: '/models/rsi_reversal_strategy_v2.pkl',
      },
      createdAt: '2024-01-14T09:00:00Z',
      updatedAt: '2024-01-14T16:45:00Z',
      startedAt: '2024-01-14T09:10:00Z',
      completedAt: '2024-01-14T16:45:00Z',
    },
    {
      id: '3',
      name: '动量策略训练',
      strategyId: 'strategy-3',
      status: 'failed',
      progress: 25,
      config: {
        datasetId: 'dataset-3',
        trainRatio: 0.75,
        validationRatio: 0.15,
        testRatio: 0.1,
        epochs: 80,
        batchSize: 16,
        learningRate: 0.005,
        optimizer: 'rmsprop',
      },
      createdAt: '2024-01-13T14:00:00Z',
      updatedAt: '2024-01-13T15:30:00Z',
      startedAt: '2024-01-13T14:15:00Z',
    },
    {
      id: '4',
      name: '套利策略训练',
      strategyId: 'strategy-4',
      status: 'pending',
      progress: 0,
      config: {
        datasetId: 'dataset-4',
        trainRatio: 0.7,
        validationRatio: 0.2,
        testRatio: 0.1,
        epochs: 60,
        batchSize: 32,
        learningRate: 0.002,
        optimizer: 'adam',
      },
      createdAt: '2024-01-15T16:00:00Z',
      updatedAt: '2024-01-15T16:00:00Z',
    },
  ]

  // Statistics
  const stats = {
    total: mockTrainingJobs.length,
    running: mockTrainingJobs.filter(job => job.status === 'running').length,
    completed: mockTrainingJobs.filter(job => job.status === 'completed').length,
    failed: mockTrainingJobs.filter(job => job.status === 'failed').length,
    pending: mockTrainingJobs.filter(job => job.status === 'pending').length,
  }

  useEffect(() => {
    loadTrainingJobs()
    // Set up polling for running jobs
    const interval = setInterval(() => {
      if (mockTrainingJobs.some(job => job.status === 'running')) {
        loadTrainingJobs()
      }
    }, 5000)

    return () => clearInterval(interval)
  }, [])

  const loadTrainingJobs = async () => {
    setLoading(true)
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 500))
      setTrainingJobs(mockTrainingJobs)
    } catch (error) {
      message.error('加载训练任务失败')
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = (value: string) => {
    setSearchText(value)
    // In real app, trigger API call with search params
  }

  const handleStatusFilterChange = (value: string) => {
    setStatusFilter(value)
    // In real app, trigger API call with filter params
  }

  const handleStart = async (job: TrainingJob) => {
    try {
      // In real app, call start API
      message.success(`训练任务 "${job.name}" 已启动`)
      loadTrainingJobs()
    } catch (error) {
      message.error('启动失败')
    }
  }

  const handleStop = async (job: TrainingJob) => {
    try {
      // In real app, call stop API
      message.success(`训练任务 "${job.name}" 已停止`)
      loadTrainingJobs()
    } catch (error) {
      message.error('停止失败')
    }
  }

  const handleDelete = async (job: TrainingJob) => {
    Modal.confirm({
      title: '确认删除训练任务？',
      content: `将删除训练任务"${job.name}"，此操作不可恢复`,
      okText: '删除',
      okType: 'danger',
      onOk: async () => {
        try {
          // In real app, call delete API
          message.success(`训练任务 "${job.name}" 删除成功`)
          loadTrainingJobs()
        } catch (error) {
          message.error('删除失败')
        }
      }
    })
  }

  const handleViewDetail = (job: TrainingJob) => {
    setCurrentJob(job)
    setDetailVisible(true)
  }

  const getStatusTag = (status: string) => {
    const statusConfig = TRAINING_STATUS[status.toUpperCase() as keyof typeof TRAINING_STATUS]
    if (!statusConfig) return <Tag>{status}</Tag>

    const icons = {
      pending: <ClockCircleOutlined />,
      running: <PlayCircleOutlined />,
      completed: <CheckCircleOutlined />,
      failed: <ExclamationCircleOutlined />,
      cancelled: <StopOutlined />,
    }

    return (
      <Tag color={statusConfig.color} icon={icons[status as keyof typeof icons]}>
        {statusConfig.label}
      </Tag>
    )
  }

  const getProgressColor = (status: string) => {
    switch (status) {
      case 'running':
        return '#1890ff'
      case 'completed':
        return '#52c41a'
      case 'failed':
        return '#f5222d'
      default:
        return '#d9d9d9'
    }
  }

  const columns: ColumnsType<TrainingJob> = [
    {
      title: '任务名称',
      dataIndex: 'name',
      key: 'name',
      width: 200,
      fixed: 'left',
      render: (text: string, record: TrainingJob) => (
        <div>
          <div>
            <Button
              type="link"
              onClick={() => handleViewDetail(record)}
              style={{ padding: 0, fontWeight: 600, fontSize: '14px' }}
            >
              {text}
            </Button>
          </div>
          <div style={{ fontSize: '12px', color: '#666', marginTop: 4 }}>
            策略ID: {record.strategyId}
          </div>
        </div>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: string) => getStatusTag(status),
      filters: Object.values(TRAINING_STATUS).map(status => ({
        text: status.label,
        value: status.key,
      })),
      onFilter: (value, record) => record.status === value,
    },
    {
      title: '进度',
      dataIndex: 'progress',
      key: 'progress',
      width: 150,
      render: (progress: number, record: TrainingJob) => (
        <div>
          <Progress
            percent={progress}
            size="small"
            strokeColor={getProgressColor(record.status)}
            showInfo={false}
          />
          <Text style={{ fontSize: '12px', color: '#666' }}>
            {progress}%
          </Text>
        </div>
      ),
    },
    {
      title: '配置信息',
      key: 'config',
      width: 200,
      render: (_, record: TrainingJob) => (
        <div style={{ fontSize: '12px' }}>
          <div>Epochs: {record.config.epochs}</div>
          <div>Batch Size: {record.config.batchSize}</div>
          <div>Learning Rate: {record.config.learningRate}</div>
          <div>Optimizer: {record.config.optimizer.toUpperCase()}</div>
        </div>
      ),
    },
    {
      title: '结果指标',
      key: 'results',
      width: 150,
      render: (_, record: TrainingJob) => {
        if (!record.results) {
          return <Text type="secondary">训练中...</Text>
        }

        return (
          <div style={{ fontSize: '12px' }}>
            <div>准确率: {(record.results.metrics.accuracy! * 100).toFixed(1)}%</div>
            <div>F1分数: {(record.results.metrics.f1Score! * 100).toFixed(1)}%</div>
            <div>最佳轮次: {record.results.bestEpoch}</div>
          </div>
        )
      },
    },
    {
      title: '运行时长',
      key: 'duration',
      width: 120,
      render: (_, record: TrainingJob) => {
        if (!record.startedAt) return '-'
        
        const endTime = record.completedAt || new Date().toISOString()
        const duration = new Date(endTime).getTime() - new Date(record.startedAt).getTime()
        const hours = Math.floor(duration / (1000 * 60 * 60))
        const minutes = Math.floor((duration % (1000 * 60 * 60)) / (1000 * 60))
        
        return `${hours}h ${minutes}m`
      },
    },
    {
      title: '创建时间',
      dataIndex: 'createdAt',
      key: 'createdAt',
      width: 140,
      render: (date: string) => (
        <Tooltip title={format.datetime(date)}>
          {format.date(date)}
        </Tooltip>
      ),
      sorter: (a, b) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime(),
    },
    {
      title: '操作',
      key: 'actions',
      width: 180,
      fixed: 'right',
      render: (_, record: TrainingJob) => (
        <Space size="small">
          {record.status === 'pending' && (
            <Tooltip title="启动训练">
              <Button
                type="primary"
                size="small"
                icon={<PlayCircleOutlined />}
                onClick={() => handleStart(record)}
              />
            </Tooltip>
          )}
          
          {record.status === 'running' && (
            <Tooltip title="停止训练">
              <Button
                danger
                size="small"
                icon={<StopOutlined />}
                onClick={() => handleStop(record)}
              />
            </Tooltip>
          )}
          
          <Tooltip title="查看详情">
            <Button
              size="small"
              icon={<EyeOutlined />}
              onClick={() => handleViewDetail(record)}
            />
          </Tooltip>
          
          <Tooltip title="删除任务">
            <Button
              size="small"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleDelete(record)}
              disabled={record.status === 'running'}
            />
          </Tooltip>
        </Space>
      ),
    },
  ]

  const rowSelection = {
    selectedRowKeys,
    onChange: (keys: React.Key[]) => setSelectedRowKeys(keys),
    getCheckboxProps: (record: TrainingJob) => ({
      disabled: record.status === 'running',
    }),
  }

  // Mock training metrics for chart
  const mockMetrics: TrainingMetrics[] = currentJob?.results ? 
    currentJob.results.trainLoss.map((loss, index) => ({
      epoch: index + 1,
      trainLoss: loss,
      validationLoss: currentJob.results!.validationLoss[index],
      timestamp: new Date(Date.now() - (currentJob.results!.trainLoss.length - index) * 60000).toISOString(),
    })) : []

  const lossChartData = mockMetrics.reduce((acc, item) => {
    acc.push(
      { epoch: item.epoch, loss: item.trainLoss, type: '训练损失' },
      { epoch: item.epoch, loss: item.validationLoss, type: '验证损失' }
    )
    return acc
  }, [] as any[])

  const lossChartConfig = {
    data: lossChartData,
    xField: 'epoch',
    yField: 'loss',
    seriesField: 'type',
    smooth: true,
    color: ['#1890ff', '#52c41a'],
  }

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div>
            <Title level={2} style={{ margin: 0 }}>
              训练管理
            </Title>
            <Text type="secondary">
              管理和监控策略模型训练任务
            </Text>
          </div>
          <Space>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => {
                // In real app, navigate to create training page
                message.info('创建训练任务功能开发中')
              }}
            >
              创建训练任务
            </Button>
          </Space>
        </div>

        {/* Statistics Cards */}
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col xs={24} sm={6}>
            <Card size="small">
              <Statistic
                title="总任务数"
                value={stats.total}
                prefix={<RobotOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card size="small">
              <Statistic
                title="运行中"
                value={stats.running}
                prefix={<PlayCircleOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card size="small">
              <Statistic
                title="已完成"
                value={stats.completed}
                prefix={<CheckCircleOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card size="small">
              <Statistic
                title="待处理"
                value={stats.pending}
                prefix={<ClockCircleOutlined />}
                valueStyle={{ color: '#faad14' }}
              />
            </Card>
          </Col>
        </Row>
      </div>

      {/* Filters and Actions */}
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={16} align="middle">
          <Col xs={24} sm={8} md={6}>
            <Search
              placeholder="搜索训练任务名称"
              allowClear
              onSearch={handleSearch}
              style={{ width: '100%' }}
            />
          </Col>
          <Col xs={24} sm={8} md={4}>
            <Select
              placeholder="任务状态"
              allowClear
              value={statusFilter || undefined}
              onChange={handleStatusFilterChange}
              style={{ width: '100%' }}
            >
              {Object.values(TRAINING_STATUS).map(status => (
                <Option key={status.key} value={status.key}>
                  {status.label}
                </Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} sm={24} md={14}>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
              {selectedRowKeys.length > 0 && (
                <Button
                  size="small"
                  danger
                  onClick={() => {
                    Modal.confirm({
                      title: '确认批量删除？',
                      content: `将删除 ${selectedRowKeys.length} 个训练任务`,
                      okText: '删除',
                      okType: 'danger',
                      onOk: () => {
                        message.success('批量删除成功')
                        setSelectedRowKeys([])
                        loadTrainingJobs()
                      }
                    })
                  }}
                >
                  批量删除 ({selectedRowKeys.length})
                </Button>
              )}
              <Button
                icon={<ReloadOutlined />}
                onClick={loadTrainingJobs}
                loading={loading}
              >
                刷新
              </Button>
            </div>
          </Col>
        </Row>
      </Card>

      {/* Training Table */}
      <Card>
        <Table
          columns={columns}
          dataSource={trainingJobs}
          rowKey="id"
          loading={loading}
          rowSelection={rowSelection}
          scroll={{ x: 1400 }}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) =>
              `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
          }}
          size="middle"
        />
      </Card>

      {/* Training Detail Modal */}
      <Modal
        title={`训练详情 - ${currentJob?.name}`}
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailVisible(false)}>
            关闭
          </Button>
        ]}
        width={1000}
      >
        {currentJob && (
          <div>
            <Row gutter={24}>
              <Col span={12}>
                <Card title="基本信息" size="small" style={{ marginBottom: 16 }}>
                  <Descriptions column={1} size="small">
                    <Descriptions.Item label="任务状态">
                      {getStatusTag(currentJob.status)}
                    </Descriptions.Item>
                    <Descriptions.Item label="进度">
                      <Progress percent={currentJob.progress} />
                    </Descriptions.Item>
                    <Descriptions.Item label="策略ID">
                      {currentJob.strategyId}
                    </Descriptions.Item>
                    <Descriptions.Item label="创建时间">
                      {format.datetime(currentJob.createdAt)}
                    </Descriptions.Item>
                    {currentJob.startedAt && (
                      <Descriptions.Item label="开始时间">
                        {format.datetime(currentJob.startedAt)}
                      </Descriptions.Item>
                    )}
                    {currentJob.completedAt && (
                      <Descriptions.Item label="完成时间">
                        {format.datetime(currentJob.completedAt)}
                      </Descriptions.Item>
                    )}
                  </Descriptions>
                </Card>
              </Col>
              
              <Col span={12}>
                <Card title="训练配置" size="small" style={{ marginBottom: 16 }}>
                  <Descriptions column={1} size="small">
                    <Descriptions.Item label="数据集">
                      {currentJob.config.datasetId}
                    </Descriptions.Item>
                    <Descriptions.Item label="训练比例">
                      {(currentJob.config.trainRatio * 100)}%
                    </Descriptions.Item>
                    <Descriptions.Item label="验证比例">
                      {(currentJob.config.validationRatio * 100)}%
                    </Descriptions.Item>
                    <Descriptions.Item label="测试比例">
                      {(currentJob.config.testRatio * 100)}%
                    </Descriptions.Item>
                    <Descriptions.Item label="训练轮次">
                      {currentJob.config.epochs}
                    </Descriptions.Item>
                    <Descriptions.Item label="批次大小">
                      {currentJob.config.batchSize}
                    </Descriptions.Item>
                    <Descriptions.Item label="学习率">
                      {currentJob.config.learningRate}
                    </Descriptions.Item>
                    <Descriptions.Item label="优化器">
                      {currentJob.config.optimizer.toUpperCase()}
                    </Descriptions.Item>
                  </Descriptions>
                </Card>
              </Col>
            </Row>

            {currentJob.results && (
              <Row gutter={24}>
                <Col span={12}>
                  <Card title="训练指标" size="small" style={{ marginBottom: 16 }}>
                    <Descriptions column={1} size="small">
                      <Descriptions.Item label="准确率">
                        {(currentJob.results.metrics.accuracy! * 100).toFixed(2)}%
                      </Descriptions.Item>
                      <Descriptions.Item label="精确率">
                        {(currentJob.results.metrics.precision! * 100).toFixed(2)}%
                      </Descriptions.Item>
                      <Descriptions.Item label="召回率">
                        {(currentJob.results.metrics.recall! * 100).toFixed(2)}%
                      </Descriptions.Item>
                      <Descriptions.Item label="F1分数">
                        {(currentJob.results.metrics.f1Score! * 100).toFixed(2)}%
                      </Descriptions.Item>
                      <Descriptions.Item label="最佳轮次">
                        {currentJob.results.bestEpoch}
                      </Descriptions.Item>
                      <Descriptions.Item label="模型路径">
                        <Text code style={{ fontSize: '11px' }}>
                          {currentJob.results.modelPath}
                        </Text>
                      </Descriptions.Item>
                    </Descriptions>
                  </Card>
                </Col>
                
                <Col span={12}>
                  <Card title="损失曲线" size="small" style={{ marginBottom: 16 }}>
                    <Line {...lossChartConfig} height={200} />
                  </Card>
                </Col>
              </Row>
            )}

            {currentJob.status === 'failed' && (
              <Alert
                message="训练失败"
                description="训练过程中出现错误，请检查配置参数和数据集。"
                type="error"
                showIcon
                style={{ marginTop: 16 }}
              />
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}

export default TrainingList