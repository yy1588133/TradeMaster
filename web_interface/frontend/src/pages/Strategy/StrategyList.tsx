import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Typography,
  Input,
  Select,
  Popconfirm,
  message,
  Tooltip,
  Progress,
  Row,
  Col,
  Statistic,
  Dropdown,
  Modal,
  Form,
} from 'antd'
import {
  PlusOutlined,
  SearchOutlined,
  ReloadOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  StopOutlined,
  EditOutlined,
  DeleteOutlined,
  CopyOutlined,
  BarChartOutlined,
  SettingOutlined,
  ExportOutlined,
  ImportOutlined,
  MoreOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import type { MenuProps } from 'antd'

import { useAppDispatch, useAppSelector } from '@/store'
import { getStrategiesAsync, deleteStrategyAsync, startStrategyAsync, stopStrategyAsync } from '@/store/strategy/strategySlice'
import { ROUTES, STRATEGY_TYPES, STRATEGY_STATUS } from '@/constants'
import { Strategy } from '@/types'
import { format } from '@/utils'

const { Title, Text } = Typography
const { Search } = Input
const { Option } = Select

const StrategyList: React.FC = () => {
  const navigate = useNavigate()
  const dispatch = useAppDispatch()
  const { strategies, loading, pagination } = useAppSelector(state => state.strategy)

  // Local state
  const [searchText, setSearchText] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [typeFilter, setTypeFilter] = useState<string>('')
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([])
  const [cloneModalVisible, setCloneModalVisible] = useState(false)
  const [cloneForm] = Form.useForm()
  const [cloningStrategy, setCloningStrategy] = useState<Strategy | null>(null)

  // Statistics data
  const stats = {
    total: strategies.length,
    active: strategies.filter(s => s.status === 'active').length,
    paused: strategies.filter(s => s.status === 'paused').length,
    stopped: strategies.filter(s => s.status === 'stopped').length,
  }

  // Load strategies on mount
  useEffect(() => {
    handleRefresh()
  }, [])

  const handleRefresh = () => {
    dispatch(getStrategiesAsync({
      page: pagination.current,
      pageSize: pagination.pageSize,
      search: searchText,
      status: statusFilter,
      type: typeFilter,
    }))
  }

  const handleSearch = (value: string) => {
    setSearchText(value)
    dispatch(getStrategiesAsync({
      page: 1,
      pageSize: pagination.pageSize,
      search: value,
      status: statusFilter,
      type: typeFilter,
    }))
  }

  const handleStatusFilterChange = (value: string) => {
    setStatusFilter(value)
    dispatch(getStrategiesAsync({
      page: 1,
      pageSize: pagination.pageSize,
      search: searchText,
      status: value,
      type: typeFilter,
    }))
  }

  const handleTypeFilterChange = (value: string) => {
    setTypeFilter(value)
    dispatch(getStrategiesAsync({
      page: 1,
      pageSize: pagination.pageSize,
      search: searchText,
      status: statusFilter,
      type: value,
    }))
  }

  const handleTableChange = (pagination: any) => {
    dispatch(getStrategiesAsync({
      page: pagination.current,
      pageSize: pagination.pageSize,
      search: searchText,
      status: statusFilter,
      type: typeFilter,
    }))
  }

  const handleStart = async (strategy: Strategy) => {
    try {
      await dispatch(startStrategyAsync(strategy.id)).unwrap()
      message.success(`策略 "${strategy.name}" 已启动`)
      handleRefresh()
    } catch (error: any) {
      message.error(`启动失败：${error.message || error}`)
    }
  }

  const handleStop = async (strategy: Strategy) => {
    try {
      await dispatch(stopStrategyAsync(strategy.id)).unwrap()
      message.success(`策略 "${strategy.name}" 已停止`)
      handleRefresh()
    } catch (error: any) {
      message.error(`停止失败：${error.message || error}`)
    }
  }

  const handleDelete = async (strategy: Strategy) => {
    try {
      await dispatch(deleteStrategyAsync(strategy.id)).unwrap()
      message.success(`策略 "${strategy.name}" 已删除`)
      handleRefresh()
    } catch (error: any) {
      message.error(`删除失败：${error.message || error}`)
    }
  }

  const handleClone = (strategy: Strategy) => {
    setCloningStrategy(strategy)
    cloneForm.setFieldsValue({
      name: `${strategy.name} - 副本`,
      description: strategy.description,
    })
    setCloneModalVisible(true)
  }

  const handleCloneSubmit = async () => {
    try {
      const values = await cloneForm.validateFields()
      // TODO: Implement clone strategy API call
      message.success('策略克隆成功')
      setCloneModalVisible(false)
      setCloningStrategy(null)
      handleRefresh()
    } catch (error: any) {
      message.error(`克隆失败：${error.message || error}`)
    }
  }

  const handleBatchAction = (action: string) => {
    if (selectedRowKeys.length === 0) {
      message.warning('请选择要操作的策略')
      return
    }

    Modal.confirm({
      title: `确认${action}选中的策略吗？`,
      content: `将${action} ${selectedRowKeys.length} 个策略`,
      onOk: async () => {
        try {
          // TODO: Implement batch operations
          message.success(`批量${action}成功`)
          setSelectedRowKeys([])
          handleRefresh()
        } catch (error: any) {
          message.error(`批量${action}失败：${error.message || error}`)
        }
      }
    })
  }

  const getStatusTag = (status: string) => {
    const statusConfig = STRATEGY_STATUS[status.toUpperCase() as keyof typeof STRATEGY_STATUS]
    if (!statusConfig) return <Tag>{status}</Tag>

    const icons = {
      active: <PlayCircleOutlined />,
      paused: <PauseCircleOutlined />,
      stopped: <StopOutlined />,
      draft: <EditOutlined />,
    }

    return (
      <Tag color={statusConfig.color} icon={icons[status as keyof typeof icons]}>
        {statusConfig.label}
      </Tag>
    )
  }

  const getTypeTag = (type: string) => {
    const typeConfig = STRATEGY_TYPES.find(t => t.key === type)
    return typeConfig ? (
      <Tag color="blue">{typeConfig.label}</Tag>
    ) : (
      <Tag>{type}</Tag>
    )
  }

  const getActionMenuItems = (strategy: Strategy): MenuProps['items'] => [
    {
      key: 'edit',
      label: '编辑策略',
      icon: <EditOutlined />,
      onClick: () => navigate(`${ROUTES.STRATEGIES}/${strategy.id}/edit`),
    },
    {
      key: 'clone',
      label: '克隆策略',
      icon: <CopyOutlined />,
      onClick: () => handleClone(strategy),
    },
    {
      key: 'analysis',
      label: '性能分析',
      icon: <BarChartOutlined />,
      onClick: () => navigate(`${ROUTES.ANALYSIS}?strategy=${strategy.id}`),
    },
    {
      type: 'divider',
    },
    {
      key: 'export',
      label: '导出配置',
      icon: <ExportOutlined />,
      onClick: () => {
        // TODO: Implement export strategy
        message.info('导出功能开发中')
      },
    },
    {
      type: 'divider',
    },
    {
      key: 'delete',
      label: '删除策略',
      icon: <DeleteOutlined />,
      danger: true,
      onClick: () => {
        Modal.confirm({
          title: '确认删除策略？',
          content: `将删除策略"${strategy.name}"，此操作不可恢复`,
          okText: '删除',
          okType: 'danger',
          onOk: () => handleDelete(strategy),
        })
      },
    },
  ]

  const columns: ColumnsType<Strategy> = [
    {
      title: '策略名称',
      dataIndex: 'name',
      key: 'name',
      width: 200,
      fixed: 'left',
      render: (text: string, record: Strategy) => (
        <div>
          <div>
            <Button
              type="link"
              onClick={() => navigate(ROUTES.STRATEGY_DETAIL.replace(':id', record.id))}
              style={{ padding: 0, fontWeight: 600, fontSize: '14px' }}
            >
              {text}
            </Button>
          </div>
          <div style={{ fontSize: '12px', color: '#666', marginTop: 4 }}>
            {record.description && record.description.length > 50
              ? `${record.description.substring(0, 50)}...`
              : record.description}
          </div>
        </div>
      ),
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      width: 140,
      render: (type: string) => getTypeTag(type),
      filters: STRATEGY_TYPES.map(type => ({ text: type.label, value: type.key })),
      onFilter: (value, record) => record.type === value,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: string) => getStatusTag(status),
      filters: Object.values(STRATEGY_STATUS).map(status => ({
        text: status.label,
        value: status.key,
      })),
      onFilter: (value, record) => record.status === value,
    },
    {
      title: '性能指标',
      key: 'performance',
      width: 200,
      render: (_, record: Strategy) => {
        if (!record.performance) {
          return <Text type="secondary">暂无数据</Text>
        }

        const { totalReturn, sharpeRatio, maxDrawdown, winRate } = record.performance

        return (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
              <span style={{ fontSize: '12px', color: '#666' }}>总收益率:</span>
              <span style={{ 
                fontSize: '12px', 
                color: totalReturn >= 0 ? '#52c41a' : '#f5222d',
                fontWeight: 600 
              }}>
                {totalReturn >= 0 ? '+' : ''}{(totalReturn * 100).toFixed(2)}%
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
              <span style={{ fontSize: '12px', color: '#666' }}>夏普比率:</span>
              <span style={{ fontSize: '12px', fontWeight: 600 }}>
                {sharpeRatio.toFixed(2)}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
              <span style={{ fontSize: '12px', color: '#666' }}>最大回撤:</span>
              <span style={{ fontSize: '12px', color: '#f5222d', fontWeight: 600 }}>
                -{(maxDrawdown * 100).toFixed(2)}%
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '12px', color: '#666' }}>胜率:</span>
              <span style={{ fontSize: '12px', fontWeight: 600 }}>
                {(winRate * 100).toFixed(1)}%
              </span>
            </div>
          </div>
        )
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
      width: 200,
      fixed: 'right',
      render: (_, record: Strategy) => (
        <Space size="small">
          {record.status === 'stopped' || record.status === 'paused' ? (
            <Tooltip title="启动策略">
              <Button
                type="primary"
                size="small"
                icon={<PlayCircleOutlined />}
                onClick={() => handleStart(record)}
              />
            </Tooltip>
          ) : (
            <Tooltip title="停止策略">
              <Button
                danger
                size="small"
                icon={<StopOutlined />}
                onClick={() => handleStop(record)}
              />
            </Tooltip>
          )}
          
          <Tooltip title="编辑策略">
            <Button
              size="small"
              icon={<EditOutlined />}
              onClick={() => navigate(`${ROUTES.STRATEGIES}/${record.id}/edit`)}
            />
          </Tooltip>

          <Dropdown
            menu={{ items: getActionMenuItems(record) }}
            trigger={['click']}
          >
            <Button size="small" icon={<MoreOutlined />} />
          </Dropdown>
        </Space>
      ),
    },
  ]

  const rowSelection = {
    selectedRowKeys,
    onChange: (keys: React.Key[]) => setSelectedRowKeys(keys),
  }

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div>
            <Title level={2} style={{ margin: 0 }}>
              策略管理
            </Title>
            <Text type="secondary">
              管理和监控您的量化交易策略
            </Text>
          </div>
          <Space>
            <Button icon={<ImportOutlined />}>导入策略</Button>
            <Button 
              type="primary" 
              icon={<PlusOutlined />}
              onClick={() => navigate(ROUTES.STRATEGY_CREATE)}
            >
              创建策略
            </Button>
          </Space>
        </div>

        {/* Statistics Cards */}
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col xs={24} sm={6}>
            <Card size="small">
              <Statistic
                title="总数"
                value={stats.total}
                prefix={<SettingOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card size="small">
              <Statistic
                title="运行中"
                value={stats.active}
                prefix={<PlayCircleOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card size="small">
              <Statistic
                title="已暂停"
                value={stats.paused}
                prefix={<PauseCircleOutlined />}
                valueStyle={{ color: '#faad14' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card size="small">
              <Statistic
                title="已停止"
                value={stats.stopped}
                prefix={<StopOutlined />}
                valueStyle={{ color: '#666' }}
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
              placeholder="搜索策略名称或描述"
              allowClear
              onSearch={handleSearch}
              style={{ width: '100%' }}
            />
          </Col>
          <Col xs={24} sm={8} md={4}>
            <Select
              placeholder="状态筛选"
              allowClear
              value={statusFilter || undefined}
              onChange={handleStatusFilterChange}
              style={{ width: '100%' }}
            >
              {Object.values(STRATEGY_STATUS).map(status => (
                <Option key={status.key} value={status.key}>
                  {status.label}
                </Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} sm={8} md={4}>
            <Select
              placeholder="类型筛选"
              allowClear
              value={typeFilter || undefined}
              onChange={handleTypeFilterChange}
              style={{ width: '100%' }}
            >
              {STRATEGY_TYPES.map(type => (
                <Option key={type.key} value={type.key}>
                  {type.label}
                </Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} sm={24} md={10}>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
              {selectedRowKeys.length > 0 && (
                <Space>
                  <Button
                    size="small"
                    onClick={() => handleBatchAction('启动')}
                  >
                    批量启动
                  </Button>
                  <Button
                    size="small"
                    onClick={() => handleBatchAction('停止')}
                  >
                    批量停止
                  </Button>
                  <Button
                    size="small"
                    danger
                    onClick={() => handleBatchAction('删除')}
                  >
                    批量删除
                  </Button>
                </Space>
              )}
              <Button
                icon={<ReloadOutlined />}
                onClick={handleRefresh}
                loading={loading}
              >
                刷新
              </Button>
            </div>
          </Col>
        </Row>
      </Card>

      {/* Strategy Table */}
      <Card>
        <Table
          columns={columns}
          dataSource={strategies}
          rowKey="id"
          loading={loading}
          rowSelection={rowSelection}
          scroll={{ x: 1200 }}
          pagination={{
            current: pagination.current,
            pageSize: pagination.pageSize,
            total: pagination.total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) =>
              `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
          }}
          onChange={handleTableChange}
          size="middle"
        />
      </Card>

      {/* Clone Strategy Modal */}
      <Modal
        title="克隆策略"
        open={cloneModalVisible}
        onOk={handleCloneSubmit}
        onCancel={() => {
          setCloneModalVisible(false)
          setCloningStrategy(null)
        }}
        destroyOnClose
      >
        <Form form={cloneForm} layout="vertical">
          <Form.Item
            name="name"
            label="策略名称"
            rules={[
              { required: true, message: '请输入策略名称' },
              { max: 100, message: '策略名称最多100个字符' },
            ]}
          >
            <Input placeholder="请输入策略名称" />
          </Form.Item>
          <Form.Item
            name="description"
            label="策略描述"
            rules={[{ max: 500, message: '策略描述最多500个字符' }]}
          >
            <Input.TextArea 
              rows={3} 
              placeholder="请输入策略描述（可选）" 
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default StrategyList