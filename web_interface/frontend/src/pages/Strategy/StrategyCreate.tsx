import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Card,
  Steps,
  Form,
  Input,
  Select,
  Button,
  Typography,
  Space,
  Row,
  Col,
  Divider,
  Alert,
  message,
  Switch,
  InputNumber,
  Tooltip,
  Upload,
  Modal,
  Tabs,
  Collapse,
  Tag,
} from 'antd'
import {
  ArrowLeftOutlined,
  SaveOutlined,
  PlayCircleOutlined,
  QuestionCircleOutlined,
  UploadOutlined,
  EyeOutlined,
  SettingOutlined,
  DatabaseOutlined,
  RobotOutlined,
  BarChartOutlined,
} from '@ant-design/icons'
import type { UploadProps } from 'antd'

import { useAppDispatch, useAppSelector } from '@/store'
import { createStrategyAsync } from '@/store/strategy/strategySlice'
import { ROUTES, STRATEGY_TYPES } from '@/constants'
import { CreateStrategyRequest, Dataset } from '@/types'

const { Title, Text, Paragraph } = Typography
const { Option } = Select
const { Step } = Steps
const { TextArea } = Input
const { TabPane } = Tabs
const { Panel } = Collapse

interface StrategyFormData extends CreateStrategyRequest {
  datasets?: string[]
  start_immediately?: boolean
}

const StrategyCreate: React.FC = () => {
  const navigate = useNavigate()
  const dispatch = useAppDispatch()
  const { loading } = useAppSelector(state => state.strategy)

  // Form and state management
  const [form] = Form.useForm()
  const [currentStep, setCurrentStep] = useState(0)
  const [selectedType, setSelectedType] = useState<string>('')
  const [previewVisible, setPreviewVisible] = useState(false)
  const [formData, setFormData] = useState<StrategyFormData>({} as StrategyFormData)

  // Mock data - in real app, fetch from API
  const [availableDatasets] = useState<Dataset[]>([
    {
      id: '1',
      name: 'BTC 日线数据',
      description: 'Bitcoin 历史价格数据',
      type: 'market_data',
      format: 'csv',
      size: 1024000,
      columns: ['date', 'open', 'high', 'low', 'close', 'volume'],
      rowCount: 1000,
      createdAt: '2024-01-01T00:00:00Z',
      updatedAt: '2024-01-01T00:00:00Z',
    },
    {
      id: '2',
      name: 'ETH-USDT 5分钟数据',
      description: 'Ethereum 5分钟K线数据',
      type: 'market_data',
      format: 'json',
      size: 2048000,
      columns: ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'],
      rowCount: 5000,
      createdAt: '2024-01-01T00:00:00Z',
      updatedAt: '2024-01-01T00:00:00Z',
    },
  ])

  const strategyTemplates = {
    algorithmic_trading: [
      {
        name: '双均线策略',
        description: '基于快慢均线交叉的经典策略',
        config: {
          fast_period: 5,
          slow_period: 20,
          trade_size: 1000,
        },
      },
      {
        name: 'RSI 反转策略',
        description: '基于相对强弱指数的反转策略',
        config: {
          rsi_period: 14,
          oversold_threshold: 30,
          overbought_threshold: 70,
          trade_size: 1000,
        },
      },
    ],
    portfolio_management: [
      {
        name: '均值回归组合',
        description: '基于均值回归理论的投资组合策略',
        config: {
          lookback_period: 252,
          rebalance_frequency: 'monthly',
          max_weight: 0.2,
        },
      },
      {
        name: '动量投资组合',
        description: '基于动量因子的投资组合策略',
        config: {
          momentum_period: 126,
          holding_period: 21,
          top_n: 10,
        },
      },
    ],
    order_execution: [
      {
        name: 'TWAP 执行策略',
        description: '时间加权平均价格执行策略',
        config: {
          execution_time: 3600,
          slice_size: 100,
          participation_rate: 0.1,
        },
      },
    ],
    high_frequency_trading: [
      {
        name: '做市策略',
        description: '高频做市策略',
        config: {
          spread: 0.001,
          inventory_limit: 1000,
          order_size: 10,
        },
      },
    ],
  }

  const steps = [
    {
      title: '基本信息',
      description: '设置策略基本信息',
      icon: <SettingOutlined />,
    },
    {
      title: '选择类型',
      description: '选择策略类型和模板',
      icon: <RobotOutlined />,
    },
    {
      title: '配置参数',
      description: '设置策略参数',
      icon: <BarChartOutlined />,
    },
    {
      title: '数据配置',
      description: '选择数据源',
      icon: <DatabaseOutlined />,
    },
  ]

  const handleNext = async () => {
    try {
      await form.validateFields()
      const values = form.getFieldsValue()
      setFormData({ ...formData, ...values })
      setCurrentStep(currentStep + 1)
    } catch (error) {
      console.error('Validation failed:', error)
    }
  }

  const handlePrev = () => {
    setCurrentStep(currentStep - 1)
  }

  const handleTypeSelect = (type: string) => {
    setSelectedType(type)
    form.setFieldsValue({ type })
  }

  const handleTemplateSelect = (template: any) => {
    const updatedConfig = { ...formData.config, ...template.config }
    form.setFieldsValue({ 
      config: updatedConfig,
      description: template.description 
    })
    setFormData({ ...formData, config: updatedConfig })
  }

  const handlePreview = () => {
    const values = form.getFieldsValue()
    setFormData({ ...formData, ...values })
    setPreviewVisible(true)
  }

  const handleSubmit = async (startImmediately: boolean = false) => {
    try {
      await form.validateFields()
      const values = form.getFieldsValue()
      const submitData = { ...formData, ...values }

      await dispatch(createStrategyAsync(submitData)).unwrap()
      
      message.success('策略创建成功！')
      
      if (startImmediately) {
        message.info('策略正在启动中...')
      }
      
      navigate(ROUTES.STRATEGIES)
    } catch (error: any) {
      message.error(`创建失败：${error.message || error}`)
    }
  }

  const uploadProps: UploadProps = {
    name: 'file',
    action: '/api/strategies/import',
    headers: {
      authorization: 'Bearer ' + localStorage.getItem('token'),
    },
    onChange(info) {
      if (info.file.status === 'done') {
        message.success(`${info.file.name} 导入成功`)
        // Fill form with imported data
        const importedData = info.file.response
        form.setFieldsValue(importedData)
      } else if (info.file.status === 'error') {
        message.error(`${info.file.name} 导入失败`)
      }
    },
  }

  const renderBasicInfoStep = () => (
    <Card title="基本信息" style={{ marginBottom: 24 }}>
      <Row gutter={24}>
        <Col span={12}>
          <Form.Item
            name="name"
            label="策略名称"
            rules={[
              { required: true, message: '请输入策略名称' },
              { max: 100, message: '策略名称最多100个字符' },
            ]}
          >
            <Input
              placeholder="请输入策略名称"
              size="large"
            />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item
            name="version"
            label="版本号"
            initialValue="1.0.0"
          >
            <Input
              placeholder="1.0.0"
              size="large"
            />
          </Form.Item>
        </Col>
      </Row>

      <Form.Item
        name="description"
        label="策略描述"
        rules={[{ max: 500, message: '策略描述最多500个字符' }]}
      >
        <TextArea
          rows={4}
          placeholder="请描述您的策略..."
          size="large"
        />
      </Form.Item>

      <Form.Item
        name="tags"
        label="标签"
      >
        <Select
          mode="tags"
          placeholder="添加标签..."
          size="large"
        >
          <Option value="量化">量化</Option>
          <Option value="高频">高频</Option>
          <Option value="套利">套利</Option>
          <Option value="趋势">趋势</Option>
          <Option value="均值回归">均值回归</Option>
        </Select>
      </Form.Item>

      <Alert
        message="提示"
        description="策略名称应该简洁明了，描述应该包含策略的核心逻辑和适用场景。"
        type="info"
        showIcon
        style={{ marginTop: 16 }}
      />
    </Card>
  )

  const renderTypeSelectionStep = () => (
    <div>
      <Card title="选择策略类型" style={{ marginBottom: 24 }}>
        <Row gutter={[16, 16]}>
          {STRATEGY_TYPES.map(type => (
            <Col xs={24} sm={12} key={type.key}>
              <Card
                hoverable
                className={selectedType === type.key ? 'selected-card' : ''}
                onClick={() => handleTypeSelect(type.key)}
                style={{
                  border: selectedType === type.key ? '2px solid #1890ff' : '1px solid #d9d9d9',
                }}
              >
                <Card.Meta
                  title={
                    <div style={{ display: 'flex', alignItems: 'center' }}>
                      <span>{type.label}</span>
                      {selectedType === type.key && (
                        <Tag color="blue" style={{ marginLeft: 8 }}>已选择</Tag>
                      )}
                    </div>
                  }
                  description={type.description}
                />
              </Card>
            </Col>
          ))}
        </Row>
      </Card>

      {selectedType && (
        <Card title="选择策略模板（可选）">
          <Row gutter={[16, 16]}>
            {strategyTemplates[selectedType as keyof typeof strategyTemplates]?.map((template, index) => (
              <Col xs={24} sm={12} lg={8} key={index}>
                <Card
                  size="small"
                  hoverable
                  actions={[
                    <Button
                      type="link"
                      size="small"
                      onClick={() => handleTemplateSelect(template)}
                    >
                      使用模板
                    </Button>
                  ]}
                >
                  <Card.Meta
                    title={template.name}
                    description={template.description}
                  />
                </Card>
              </Col>
            ))}
          </Row>
          <Alert
            message="模板说明"
            description="选择模板可以快速开始，您可以在下一步中自定义参数。也可以跳过模板，从零开始配置。"
            type="info"
            showIcon
            style={{ marginTop: 16 }}
          />
        </Card>
      )}
    </div>
  )

  const renderConfigurationStep = () => (
    <Card title="策略参数配置">
      <Tabs defaultActiveKey="basic">
        <TabPane tab="基础参数" key="basic">
          <Row gutter={24}>
            <Col span={12}>
              <Form.Item
                name={['config', 'initial_cash']}
                label="初始资金"
                rules={[{ required: true, message: '请输入初始资金' }]}
                initialValue={100000}
              >
                <InputNumber
                  style={{ width: '100%' }}
                  formatter={value => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                  parser={value => value!.replace(/\$\s?|(,*)/g, '')}
                  min={1000}
                  max={10000000}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name={['config', 'max_position_size']}
                label="最大持仓比例"
                initialValue={0.1}
              >
                <InputNumber
                  style={{ width: '100%' }}
                  min={0.01}
                  max={1}
                  step={0.01}
                  formatter={value => `${(Number(value) * 100)}%`}
                  parser={value => Number(value!.replace('%', '')) / 100}
                />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={24}>
            <Col span={12}>
              <Form.Item
                name={['config', 'commission']}
                label="手续费率"
                initialValue={0.001}
              >
                <InputNumber
                  style={{ width: '100%' }}
                  min={0}
                  max={0.01}
                  step={0.0001}
                  formatter={value => `${(Number(value) * 100)}%`}
                  parser={value => Number(value!.replace('%', '')) / 100}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name={['config', 'slippage']}
                label="滑点"
                initialValue={0.0005}
              >
                <InputNumber
                  style={{ width: '100%' }}
                  min={0}
                  max={0.01}
                  step={0.0001}
                  formatter={value => `${(Number(value) * 100)}%`}
                  parser={value => Number(value!.replace('%', '')) / 100}
                />
              </Form.Item>
            </Col>
          </Row>
        </TabPane>

        <TabPane tab="风险管理" key="risk">
          <Row gutter={24}>
            <Col span={12}>
              <Form.Item
                name={['config', 'stop_loss']}
                label="止损比例"
                initialValue={0.05}
              >
                <InputNumber
                  style={{ width: '100%' }}
                  min={0.01}
                  max={0.5}
                  step={0.01}
                  formatter={value => `${(Number(value) * 100)}%`}
                  parser={value => Number(value!.replace('%', '')) / 100}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name={['config', 'take_profit']}
                label="止盈比例"
                initialValue={0.15}
              >
                <InputNumber
                  style={{ width: '100%' }}
                  min={0.01}
                  max={1}
                  step={0.01}
                  formatter={value => `${(Number(value) * 100)}%`}
                  parser={value => Number(value!.replace('%', '')) / 100}
                />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={24}>
            <Col span={12}>
              <Form.Item
                name={['config', 'max_drawdown']}
                label="最大回撤限制"
                initialValue={0.2}
              >
                <InputNumber
                  style={{ width: '100%' }}
                  min={0.05}
                  max={0.5}
                  step={0.01}
                  formatter={value => `${(Number(value) * 100)}%`}
                  parser={value => Number(value!.replace('%', '')) / 100}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name={['config', 'risk_free_rate']}
                label="无风险利率"
                initialValue={0.03}
              >
                <InputNumber
                  style={{ width: '100%' }}
                  min={0}
                  max={0.1}
                  step={0.001}
                  formatter={value => `${(Number(value) * 100)}%`}
                  parser={value => Number(value!.replace('%', '')) / 100}
                />
              </Form.Item>
            </Col>
          </Row>
        </TabPane>

        <TabPane tab="高级设置" key="advanced">
          <Collapse>
            <Panel header="技术指标参数" key="indicators">
              <Row gutter={24}>
                <Col span={12}>
                  <Form.Item
                    name={['config', 'ma_short']}
                    label="短期均线周期"
                    initialValue={5}
                  >
                    <InputNumber
                      style={{ width: '100%' }}
                      min={1}
                      max={100}
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name={['config', 'ma_long']}
                    label="长期均线周期"
                    initialValue={20}
                  >
                    <InputNumber
                      style={{ width: '100%' }}
                      min={1}
                      max={200}
                    />
                  </Form.Item>
                </Col>
              </Row>
            </Panel>

            <Panel header="回测设置" key="backtest">
              <Row gutter={24}>
                <Col span={12}>
                  <Form.Item
                    name={['config', 'benchmark']}
                    label="基准指数"
                    initialValue="SPY"
                  >
                    <Select>
                      <Option value="SPY">标普500 (SPY)</Option>
                      <Option value="QQQ">纳斯达克100 (QQQ)</Option>
                      <Option value="BTC">比特币 (BTC)</Option>
                      <Option value="ETH">以太坊 (ETH)</Option>
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name={['config', 'rebalance_frequency']}
                    label="再平衡频率"
                    initialValue="daily"
                  >
                    <Select>
                      <Option value="daily">每日</Option>
                      <Option value="weekly">每周</Option>
                      <Option value="monthly">每月</Option>
                      <Option value="quarterly">每季度</Option>
                    </Select>
                  </Form.Item>
                </Col>
              </Row>
            </Panel>
          </Collapse>
        </TabPane>
      </Tabs>
    </Card>
  )

  const renderDataConfigStep = () => (
    <Card title="数据源配置">
      <Form.Item
        name="datasets"
        label="选择数据集"
        rules={[{ required: true, message: '请至少选择一个数据集' }]}
      >
        <Select
          mode="multiple"
          placeholder="选择数据集..."
          size="large"
          optionLabelProp="label"
        >
          {availableDatasets.map(dataset => (
            <Option key={dataset.id} value={dataset.id} label={dataset.name}>
              <div>
                <div style={{ fontWeight: 600 }}>{dataset.name}</div>
                <div style={{ fontSize: '12px', color: '#666' }}>
                  {dataset.description} • {dataset.rowCount} 行 • {(dataset.size / 1024 / 1024).toFixed(2)} MB
                </div>
              </div>
            </Option>
          ))}
        </Select>
      </Form.Item>

      <Divider>数据集详情</Divider>
      
      <Row gutter={16}>
        {availableDatasets.map(dataset => (
          <Col xs={24} sm={12} key={dataset.id}>
            <Card size="small" style={{ marginBottom: 16 }}>
              <Card.Meta
                title={dataset.name}
                description={
                  <div>
                    <p>{dataset.description}</p>
                    <Space size="small">
                      <Tag color="blue">{dataset.type}</Tag>
                      <Tag color="green">{dataset.format.toUpperCase()}</Tag>
                      <Tag>{dataset.rowCount} 行</Tag>
                    </Space>
                    <div style={{ marginTop: 8, fontSize: '12px', color: '#666' }}>
                      字段：{dataset.columns.join(', ')}
                    </div>
                  </div>
                }
              />
            </Card>
          </Col>
        ))}
      </Row>

      <Alert
        message="数据说明"
        description="请确保选择的数据集包含策略所需的所有字段。数据质量直接影响策略表现。"
        type="info"
        showIcon
        style={{ marginTop: 16 }}
      />
    </Card>
  )

  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        return renderBasicInfoStep()
      case 1:
        return renderTypeSelectionStep()
      case 2:
        return renderConfigurationStep()
      case 3:
        return renderDataConfigStep()
      default:
        return null
    }
  }

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: 16 }}>
          <Button
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate(ROUTES.STRATEGIES)}
            style={{ marginRight: 16 }}
          >
            返回
          </Button>
          <div>
            <Title level={2} style={{ margin: 0 }}>
              创建策略
            </Title>
            <Text type="secondary">
              按照步骤创建您的量化交易策略
            </Text>
          </div>
        </div>

        {/* Import Option */}
        <Card size="small" style={{ marginBottom: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <Text strong>已有策略配置文件？</Text>
              <Text type="secondary" style={{ marginLeft: 8 }}>
                您可以直接导入现有的策略配置文件
              </Text>
            </div>
            <Upload {...uploadProps}>
              <Button icon={<UploadOutlined />}>导入配置</Button>
            </Upload>
          </div>
        </Card>
      </div>

      {/* Steps */}
      <Card style={{ marginBottom: 24 }}>
        <Steps current={currentStep} type="navigation">
          {steps.map((step, index) => (
            <Step
              key={index}
              title={step.title}
              description={step.description}
              icon={step.icon}
            />
          ))}
        </Steps>
      </Card>

      {/* Form */}
      <Form
        form={form}
        layout="vertical"
        size="large"
        onFinish={() => handleSubmit(false)}
      >
        {renderStepContent()}

        {/* Actions */}
        <Card>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <div>
              {currentStep > 0 && (
                <Button onClick={handlePrev}>
                  上一步
                </Button>
              )}
            </div>
            <Space>
              <Button
                icon={<EyeOutlined />}
                onClick={handlePreview}
              >
                预览配置
              </Button>
              {currentStep < steps.length - 1 ? (
                <Button type="primary" onClick={handleNext}>
                  下一步
                </Button>
              ) : (
                <Space>
                  <Button
                    icon={<SaveOutlined />}
                    onClick={() => handleSubmit(false)}
                    loading={loading}
                  >
                    保存策略
                  </Button>
                  <Button
                    type="primary"
                    icon={<PlayCircleOutlined />}
                    onClick={() => handleSubmit(true)}
                    loading={loading}
                  >
                    保存并启动
                  </Button>
                </Space>
              )}
            </Space>
          </div>
        </Card>
      </Form>

      {/* Preview Modal */}
      <Modal
        title="策略配置预览"
        open={previewVisible}
        onCancel={() => setPreviewVisible(false)}
        footer={[
          <Button key="close" onClick={() => setPreviewVisible(false)}>
            关闭
          </Button>
        ]}
        width={800}
      >
        <div style={{ maxHeight: 600, overflow: 'auto' }}>
          <pre style={{ 
            background: '#f5f5f5', 
            padding: 16, 
            borderRadius: 4,
            fontSize: '12px'
          }}>
            {JSON.stringify(formData, null, 2)}
          </pre>
        </div>
      </Modal>
    </div>
  )
}

export default StrategyCreate