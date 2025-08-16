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
  Upload,
  Modal,
  message,
  Tooltip,
  Popconfirm,
  Descriptions,
  Alert,
} from 'antd'
import {
  PlusOutlined,
  UploadOutlined,
  SearchOutlined,
  ReloadOutlined,
  EyeOutlined,
  EditOutlined,
  DeleteOutlined,
  DownloadOutlined,
  DatabaseOutlined,
  FileTextOutlined,
  CloudUploadOutlined,
  BarChartOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import type { UploadProps } from 'antd'

import { DATASET_TYPES, DATASET_FORMATS } from '@/constants'
import { Dataset } from '@/types'
import { format } from '@/utils'

const { Title, Text } = Typography
const { Search } = Input
const { Option } = Select

const DatasetList: React.FC = () => {
  const navigate = useNavigate()

  // Local state
  const [loading, setLoading] = useState(false)
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [searchText, setSearchText] = useState('')
  const [typeFilter, setTypeFilter] = useState<string>('')
  const [formatFilter, setFormatFilter] = useState<string>('')
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([])
  const [previewVisible, setPreviewVisible] = useState(false)
  const [previewDataset, setPreviewDataset] = useState<Dataset | null>(null)
  const [uploadVisible, setUploadVisible] = useState(false)

  // Mock data - in real app, fetch from API
  const mockDatasets: Dataset[] = [
    {
      id: '1',
      name: 'BTC-USDT 日线数据',
      description: 'Bitcoin 对 USDT 的历史日线数据，包含开高低收量',
      type: 'market_data',
      format: 'csv',
      size: 1024000,
      columns: ['date', 'open', 'high', 'low', 'close', 'volume'],
      rowCount: 1500,
      createdAt: '2024-01-01T00:00:00Z',
      updatedAt: '2024-01-15T10:30:00Z',
    },
    {
      id: '2',
      name: 'ETH-USDT 5分钟数据',
      description: 'Ethereum 对 USDT 的5分钟K线数据',
      type: 'market_data',
      format: 'json',
      size: 5120000,
      columns: ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'],
      rowCount: 10000,
      createdAt: '2024-01-01T00:00:00Z',
      updatedAt: '2024-01-15T14:20:00Z',
    },
    {
      id: '3',
      name: '标普500成分股财务数据',
      description: 'S&P 500成分股的季度财务报表数据',
      type: 'financial_data',
      format: 'parquet',
      size: 8192000,
      columns: ['symbol', 'quarter', 'revenue', 'net_income', 'total_assets', 'equity'],
      rowCount: 2500,
      createdAt: '2023-12-01T00:00:00Z',
      updatedAt: '2024-01-10T09:15:00Z',
    },
    {
      id: '4',
      name: '自定义因子数据',
      description: '基于技术指标计算的自定义因子数据集',
      type: 'custom',
      format: 'csv',
      size: 2048000,
      columns: ['date', 'symbol', 'factor1', 'factor2', 'factor3', 'returns'],
      rowCount: 5000,
      createdAt: '2024-01-05T00:00:00Z',
      updatedAt: '2024-01-14T16:45:00Z',
    },
  ]

  // Statistics
  const stats = {
    totalDatasets: mockDatasets.length,
    totalSize: mockDatasets.reduce((sum, d) => sum + d.size, 0),
    totalRows: mockDatasets.reduce((sum, d) => sum + d.rowCount, 0),
    marketData: mockDatasets.filter(d => d.type === 'market_data').length,
  }

  useEffect(() => {
    loadDatasets()
  }, [])

  const loadDatasets = async () => {
    setLoading(true)
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000))
      setDatasets(mockDatasets)
    } catch (error) {
      message.error('加载数据集失败')
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = (value: string) => {
    setSearchText(value)
    // In real app, trigger API call with search params
  }

  const handleTypeFilterChange = (value: string) => {
    setTypeFilter(value)
    // In real app, trigger API call with filter params
  }

  const handleFormatFilterChange = (value: string) => {
    setFormatFilter(value)
    // In real app, trigger API call with filter params
  }

  const handlePreview = (dataset: Dataset) => {
    setPreviewDataset(dataset)
    setPreviewVisible(true)
  }

  const handleDelete = async (dataset: Dataset) => {
    try {
      // In real app, call delete API
      message.success(`数据集 "${dataset.name}" 删除成功`)
      loadDatasets()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleDownload = async (dataset: Dataset) => {
    try {
      // In real app, call download API
      message.success(`数据集 "${dataset.name}" 下载开始`)
    } catch (error) {
      message.error('下载失败')
    }
  }

  const handleBatchDelete = () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请选择要删除的数据集')
      return
    }

    Modal.confirm({
      title: '确认批量删除？',
      content: `将删除 ${selectedRowKeys.length} 个数据集，此操作不可恢复`,
      okText: '删除',
      okType: 'danger',
      onOk: async () => {
        try {
          // In real app, call batch delete API
          message.success('批量删除成功')
          setSelectedRowKeys([])
          loadDatasets()
        } catch (error) {
          message.error('批量删除失败')
        }
      }
    })
  }

  const getTypeTag = (type: string) => {
    const typeConfig = DATASET_TYPES.find(t => t.key === type)
    return typeConfig ? (
      <Tag color="blue">{typeConfig.label}</Tag>
    ) : (
      <Tag>{type}</Tag>
    )
  }

  const getFormatTag = (format: string) => {
    const colors = {
      csv: 'green',
      json: 'orange',
      parquet: 'purple',
    }
    return (
      <Tag color={colors[format as keyof typeof colors] || 'default'}>
        {format.toUpperCase()}
      </Tag>
    )
  }

  const uploadProps: UploadProps = {
    name: 'file',
    action: '/api/datasets/upload',
    headers: {
      authorization: 'Bearer ' + localStorage.getItem('token'),
    },
    multiple: true,
    accept: '.csv,.json,.parquet',
    onChange(info) {
      if (info.file.status === 'done') {
        message.success(`${info.file.name} 上传成功`)
        loadDatasets()
      } else if (info.file.status === 'error') {
        message.error(`${info.file.name} 上传失败`)
      }
    },
    beforeUpload(file) {
      const isValidFormat = ['text/csv', 'application/json', 'application/octet-stream'].includes(file.type)
      if (!isValidFormat) {
        message.error('只支持 CSV、JSON、Parquet 格式的文件')
        return false
      }
      const isLt100M = file.size / 1024 / 1024 < 100
      if (!isLt100M) {
        message.error('文件大小不能超过 100MB')
        return false
      }
      return true
    },
  }

  const columns: ColumnsType<Dataset> = [
    {
      title: '数据集名称',
      dataIndex: 'name',
      key: 'name',
      width: 200,
      fixed: 'left',
      render: (text: string, record: Dataset) => (
        <div>
          <div>
            <Button
              type="link"
              onClick={() => handlePreview(record)}
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
      width: 120,
      render: (type: string) => getTypeTag(type),
      filters: DATASET_TYPES.map(type => ({ text: type.label, value: type.key })),
      onFilter: (value, record) => record.type === value,
    },
    {
      title: '格式',
      dataIndex: 'format',
      key: 'format',
      width: 100,
      render: (format: string) => getFormatTag(format),
      filters: DATASET_FORMATS.map(format => ({ text: format.label, value: format.key })),
      onFilter: (value, record) => record.format === value,
    },
    {
      title: '大小',
      dataIndex: 'size',
      key: 'size',
      width: 100,
      render: (size: number) => format.fileSize(size),
      sorter: (a, b) => a.size - b.size,
    },
    {
      title: '行数',
      dataIndex: 'rowCount',
      key: 'rowCount',
      width: 100,
      render: (count: number) => count.toLocaleString(),
      sorter: (a, b) => a.rowCount - b.rowCount,
    },
    {
      title: '字段数',
      dataIndex: 'columns',
      key: 'columns',
      width: 100,
      render: (columns: string[]) => (
        <Tooltip title={columns.join(', ')}>
          {columns.length} 个字段
        </Tooltip>
      ),
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
      render: (_, record: Dataset) => (
        <Space size="small">
          <Tooltip title="预览数据">
            <Button
              size="small"
              icon={<EyeOutlined />}
              onClick={() => handlePreview(record)}
            />
          </Tooltip>
          
          <Tooltip title="编辑数据集">
            <Button
              size="small"
              icon={<EditOutlined />}
              onClick={() => {
                // In real app, navigate to edit page
                message.info('编辑功能开发中')
              }}
            />
          </Tooltip>
          
          <Tooltip title="下载数据集">
            <Button
              size="small"
              icon={<DownloadOutlined />}
              onClick={() => handleDownload(record)}
            />
          </Tooltip>
          
          <Popconfirm
            title="确认删除数据集？"
            description={`将删除数据集"${record.name}"，此操作不可恢复`}
            onConfirm={() => handleDelete(record)}
            okText="删除"
            cancelText="取消"
            okType="danger"
          >
            <Tooltip title="删除数据集">
              <Button
                size="small"
                danger
                icon={<DeleteOutlined />}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  const rowSelection = {
    selectedRowKeys,
    onChange: (keys: React.Key[]) => setSelectedRowKeys(keys),
  }

  const mockPreviewData = [
    { date: '2024-01-15', open: 42500, high: 43200, low: 42100, close: 42800, volume: 1234567 },
    { date: '2024-01-14', open: 42200, high: 42750, low: 41800, close: 42500, volume: 2345678 },
    { date: '2024-01-13', open: 41900, high: 42400, low: 41600, close: 42200, volume: 3456789 },
  ]

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div>
            <Title level={2} style={{ margin: 0 }}>
              数据管理
            </Title>
            <Text type="secondary">
              管理您的数据集，支持多种格式的数据导入和处理
            </Text>
          </div>
          <Space>
            <Button
              icon={<UploadOutlined />}
              onClick={() => setUploadVisible(true)}
            >
              上传数据
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => {
                // In real app, navigate to create page
                message.info('创建数据集功能开发中')
              }}
            >
              创建数据集
            </Button>
          </Space>
        </div>

        {/* Statistics Cards */}
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col xs={24} sm={6}>
            <Card size="small">
              <Statistic
                title="数据集总数"
                value={stats.totalDatasets}
                prefix={<DatabaseOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card size="small">
              <Statistic
                title="总存储量"
                value={format.fileSize(stats.totalSize)}
                prefix={<CloudUploadOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card size="small">
              <Statistic
                title="总数据行数"
                value={stats.totalRows}
                prefix={<BarChartOutlined />}
                valueStyle={{ color: '#faad14' }}
                formatter={(value) => Number(value).toLocaleString()}
              />
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card size="small">
              <Statistic
                title="市场数据"
                value={stats.marketData}
                prefix={<FileTextOutlined />}
                valueStyle={{ color: '#722ed1' }}
                suffix={`/ ${stats.totalDatasets}`}
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
              placeholder="搜索数据集名称或描述"
              allowClear
              onSearch={handleSearch}
              style={{ width: '100%' }}
            />
          </Col>
          <Col xs={24} sm={8} md={4}>
            <Select
              placeholder="数据类型"
              allowClear
              value={typeFilter || undefined}
              onChange={handleTypeFilterChange}
              style={{ width: '100%' }}
            >
              {DATASET_TYPES.map(type => (
                <Option key={type.key} value={type.key}>
                  {type.label}
                </Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} sm={8} md={4}>
            <Select
              placeholder="文件格式"
              allowClear
              value={formatFilter || undefined}
              onChange={handleFormatFilterChange}
              style={{ width: '100%' }}
            >
              {DATASET_FORMATS.map(format => (
                <Option key={format.key} value={format.key}>
                  {format.label}
                </Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} sm={24} md={10}>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
              {selectedRowKeys.length > 0 && (
                <Button
                  size="small"
                  danger
                  onClick={handleBatchDelete}
                >
                  批量删除 ({selectedRowKeys.length})
                </Button>
              )}
              <Button
                icon={<ReloadOutlined />}
                onClick={loadDatasets}
                loading={loading}
              >
                刷新
              </Button>
            </div>
          </Col>
        </Row>
      </Card>

      {/* Dataset Table */}
      <Card>
        <Table
          columns={columns}
          dataSource={datasets}
          rowKey="id"
          loading={loading}
          rowSelection={rowSelection}
          scroll={{ x: 1200 }}
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

      {/* Upload Modal */}
      <Modal
        title="上传数据文件"
        open={uploadVisible}
        onCancel={() => setUploadVisible(false)}
        footer={null}
        width={600}
      >
        <Alert
          message="上传说明"
          description={
            <ul style={{ marginBottom: 0, paddingLeft: 20 }}>
              <li>支持 CSV、JSON、Parquet 格式文件</li>
              <li>单文件大小不超过 100MB</li>
              <li>支持批量上传多个文件</li>
              <li>上传后系统会自动解析文件结构</li>
            </ul>
          }
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />
        
        <Upload.Dragger {...uploadProps}>
          <p className="ant-upload-drag-icon">
            <UploadOutlined style={{ fontSize: 48, color: '#1890ff' }} />
          </p>
          <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
          <p className="ant-upload-hint">
            支持单文件或批量上传，严格禁止上传公司数据或其他敏感信息
          </p>
        </Upload.Dragger>
      </Modal>

      {/* Preview Modal */}
      <Modal
        title={`数据预览 - ${previewDataset?.name}`}
        open={previewVisible}
        onCancel={() => setPreviewVisible(false)}
        footer={[
          <Button key="close" onClick={() => setPreviewVisible(false)}>
            关闭
          </Button>
        ]}
        width={1000}
      >
        {previewDataset && (
          <div>
            <Descriptions column={2} size="small" style={{ marginBottom: 16 }}>
              <Descriptions.Item label="类型">
                {getTypeTag(previewDataset.type)}
              </Descriptions.Item>
              <Descriptions.Item label="格式">
                {getFormatTag(previewDataset.format)}
              </Descriptions.Item>
              <Descriptions.Item label="大小">
                {format.fileSize(previewDataset.size)}
              </Descriptions.Item>
              <Descriptions.Item label="行数">
                {previewDataset.rowCount.toLocaleString()}
              </Descriptions.Item>
              <Descriptions.Item label="字段" span={2}>
                <Space wrap>
                  {previewDataset.columns.map(col => (
                    <Tag key={col}>{col}</Tag>
                  ))}
                </Space>
              </Descriptions.Item>
            </Descriptions>
            
            <div style={{ marginBottom: 16 }}>
              <Text strong>数据预览（前3行）：</Text>
            </div>
            
            <div style={{ 
              background: '#f5f5f5', 
              padding: 16, 
              borderRadius: 4,
              overflow: 'auto',
              maxHeight: 400 
            }}>
              <pre style={{ margin: 0, fontSize: '12px' }}>
                {JSON.stringify(mockPreviewData, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}

export default DatasetList