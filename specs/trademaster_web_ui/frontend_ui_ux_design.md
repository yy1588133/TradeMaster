# TradeMaster Web界面前端UI/UX设计方案

**文档版本**: v1.0  
**创建日期**: 2025年8月15日  
**设计师**: TradeMaster前端设计团队  
**项目代码**: TMW-2025-001

---

## 1. UI/UX设计理念

### 1.1 设计原则

#### 1.1.1 用户体验原则
- **简洁性 (Simplicity)**: 界面简洁明了，避免不必要的复杂性
- **一致性 (Consistency)**: 整个应用保持视觉和交互的一致性
- **可用性 (Usability)**: 符合用户直觉，降低学习成本
- **可访问性 (Accessibility)**: 支持不同用户群体的访问需求
- **响应性 (Responsiveness)**: 适配不同设备和屏幕尺寸

#### 1.1.2 视觉设计原则
- **层次化信息**: 重要信息突出显示，次要信息适当弱化
- **视觉对比**: 使用颜色、大小、空间营造视觉对比
- **信息密度**: 平衡信息密度与界面清晰度
- **品牌一致**: 体现TradeMaster专业、可靠的品牌形象

### 1.2 设计目标

#### 1.2.1 用户目标
- **新手用户**: 快速上手，轻松完成基础操作
- **专业用户**: 高效操作，深度功能易于访问
- **开发者**: 代码编辑舒适，调试信息清晰
- **管理者**: 系统状态一目了然，决策支持充分

#### 1.2.2 业务目标
- **降低使用门槛**: 吸引更多用户使用TradeMaster
- **提升工作效率**: 简化复杂操作流程
- **增强用户粘性**: 优秀的用户体验促进长期使用
- **展示专业性**: 体现量化交易平台的专业水准

## 2. 整体布局设计

### 2.1 布局架构

```
┌─────────────────────────────────────────────────────────────┐
│                        Header (60px)                        │
├─────────────────────────────────────────────────────────────┤
│          │                                                  │
│  Sidebar │                Main Content                      │
│  (240px) │               (Flexible)                         │
│          │                                                  │
│          │                                                  │
│          │                                                  │
│          │                                                  │
├─────────────────────────────────────────────────────────────┤
│                       Footer (40px)                         │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 响应式布局策略

#### 2.2.1 断点设计
```scss
// 响应式断点
$breakpoints: (
  xs: 0,      // 手机
  sm: 576px,  // 大手机
  md: 768px,  // 平板
  lg: 992px,  // 桌面
  xl: 1200px, // 大桌面
  xxl: 1600px // 超大桌面
);

// 布局变化
@media (max-width: 768px) {
  .sidebar {
    transform: translateX(-100%);
    position: fixed;
    z-index: 1000;
    
    &.open {
      transform: translateX(0);
    }
  }
  
  .main-content {
    margin-left: 0;
    padding: 16px;
  }
}

@media (min-width: 769px) {
  .sidebar {
    position: fixed;
    left: 0;
    transform: translateX(0);
  }
  
  .main-content {
    margin-left: 240px;
    padding: 24px;
  }
}
```

### 2.3 组件层次结构

```typescript
// 布局组件层次
interface LayoutStructure {
  App: {
    AppLayout: {
      Header: HeaderComponent;
      Sidebar: SidebarComponent;
      MainContent: {
        Breadcrumb: BreadcrumbComponent;
        PageHeader: PageHeaderComponent;
        PageContent: PageContentComponent;
      };
      Footer: FooterComponent;
    };
    GlobalComponents: {
      LoadingOverlay: LoadingComponent;
      NotificationCenter: NotificationComponent;
      ConfirmDialog: DialogComponent;
      HelpPanel: HelpComponent;
    };
  };
}
```

## 3. 视觉设计系统

### 3.1 颜色系统

#### 3.1.1 主色调方案
```scss
// 主要颜色
$primary-colors: (
  primary-50: #e8f4fd,
  primary-100: #bee6fb,
  primary-200: #7dd3f7,
  primary-300: #35bef3,
  primary-400: #00a9ee,
  primary-500: #0091d5,    // 主色
  primary-600: #0081c2,
  primary-700: #006ba6,
  primary-800: #005a94,
  primary-900: #003c73
);

// 功能颜色
$semantic-colors: (
  success: #52c41a,
  warning: #faad14,
  error: #f5222d,
  info: #1890ff,
  
  success-light: #f6ffed,
  warning-light: #fffbe6,
  error-light: #fff2f0,
  info-light: #e6f7ff
);

// 中性色
$neutral-colors: (
  white: #ffffff,
  gray-50: #fafafa,
  gray-100: #f5f5f5,
  gray-200: #f0f0f0,
  gray-300: #d9d9d9,
  gray-400: #bfbfbf,
  gray-500: #8c8c8c,
  gray-600: #595959,
  gray-700: #434343,
  gray-800: #262626,
  gray-900: #1f1f1f,
  black: #000000
);
```

#### 3.1.2 深色模式适配
```scss
// 深色模式颜色变量
:root {
  --bg-primary: #{$neutral-colors.white};
  --bg-secondary: #{$neutral-colors.gray-50};
  --bg-tertiary: #{$neutral-colors.gray-100};
  --text-primary: #{$neutral-colors.gray-900};
  --text-secondary: #{$neutral-colors.gray-600};
  --border-color: #{$neutral-colors.gray-300};
}

[data-theme="dark"] {
  --bg-primary: #{$neutral-colors.gray-900};
  --bg-secondary: #{$neutral-colors.gray-800};
  --bg-tertiary: #{$neutral-colors.gray-700};
  --text-primary: #{$neutral-colors.white};
  --text-secondary: #{$neutral-colors.gray-300};
  --border-color: #{$neutral-colors.gray-600};
}
```

### 3.2 字体系统

#### 3.2.1 字体家族
```scss
// 字体栈
$font-families: (
  sans: ('Inter', 'Helvetica Neue', 'Helvetica', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', 'Arial', sans-serif),
  mono: ('JetBrains Mono', 'Fira Code', 'Menlo', 'Monaco', 'Consolas', 'Courier New', monospace),
  display: ('Inter Display', 'Inter', sans-serif)
);

// 字体大小
$font-sizes: (
  xs: 0.75rem,    // 12px
  sm: 0.875rem,   // 14px
  base: 1rem,     // 16px
  lg: 1.125rem,   // 18px
  xl: 1.25rem,    // 20px
  2xl: 1.5rem,    // 24px
  3xl: 1.875rem,  // 30px
  4xl: 2.25rem,   // 36px
  5xl: 3rem       // 48px
);

// 字体权重
$font-weights: (
  light: 300,
  normal: 400,
  medium: 500,
  semibold: 600,
  bold: 700
);

// 行高
$line-heights: (
  tight: 1.25,
  normal: 1.5,
  relaxed: 1.75
);
```

#### 3.2.2 排版规范
```scss
// 标题样式
.typography {
  h1 {
    font-size: map-get($font-sizes, 4xl);
    font-weight: map-get($font-weights, bold);
    line-height: map-get($line-heights, tight);
    margin-bottom: 1.5rem;
  }
  
  h2 {
    font-size: map-get($font-sizes, 3xl);
    font-weight: map-get($font-weights, semibold);
    line-height: map-get($line-heights, tight);
    margin-bottom: 1rem;
  }
  
  h3 {
    font-size: map-get($font-sizes, 2xl);
    font-weight: map-get($font-weights, semibold);
    line-height: map-get($line-heights, normal);
    margin-bottom: 0.75rem;
  }
  
  // 正文
  p {
    font-size: map-get($font-sizes, base);
    line-height: map-get($line-heights, relaxed);
    margin-bottom: 1rem;
  }
  
  // 代码
  code {
    font-family: map-get($font-families, mono);
    font-size: map-get($font-sizes, sm);
    background-color: var(--bg-tertiary);
    padding: 0.125rem 0.25rem;
    border-radius: 0.25rem;
  }
}
```

### 3.3 间距和布局

#### 3.3.1 间距系统
```scss
// 间距标准
$spacing: (
  0: 0,
  1: 0.25rem,  // 4px
  2: 0.5rem,   // 8px
  3: 0.75rem,  // 12px
  4: 1rem,     // 16px
  5: 1.25rem,  // 20px
  6: 1.5rem,   // 24px
  8: 2rem,     // 32px
  10: 2.5rem,  // 40px
  12: 3rem,    // 48px
  16: 4rem,    // 64px
  20: 5rem,    // 80px
  24: 6rem     // 96px
);

// 组件间距
.component-spacing {
  // 卡片间距
  .card + .card {
    margin-top: map-get($spacing, 6);
  }
  
  // 表单项间距
  .form-item + .form-item {
    margin-top: map-get($spacing, 4);
  }
  
  // 按钮组间距
  .button-group .btn + .btn {
    margin-left: map-get($spacing, 2);
  }
}
```

#### 3.3.2 网格系统
```scss
// 12列网格系统
.grid {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: map-get($spacing, 6);
  
  .col-1 { grid-column: span 1; }
  .col-2 { grid-column: span 2; }
  .col-3 { grid-column: span 3; }
  .col-4 { grid-column: span 4; }
  .col-6 { grid-column: span 6; }
  .col-8 { grid-column: span 8; }
  .col-9 { grid-column: span 9; }
  .col-12 { grid-column: span 12; }
}

// Flexbox布局工具
.flex {
  display: flex;
  
  &.justify-between { justify-content: space-between; }
  &.justify-center { justify-content: center; }
  &.justify-end { justify-content: flex-end; }
  
  &.items-center { align-items: center; }
  &.items-start { align-items: flex-start; }
  &.items-end { align-items: flex-end; }
  
  &.flex-col { flex-direction: column; }
  &.flex-wrap { flex-wrap: wrap; }
}
```

## 4. 核心页面设计

### 4.1 仪表板页面

#### 4.1.1 页面布局
```typescript
// 仪表板布局结构
const DashboardLayout: React.FC = () => {
  return (
    <div className="dashboard">
      {/* 顶部统计卡片 */}
      <div className="grid grid-cols-4 gap-6 mb-8">
        <StatCard
          title="活跃策略"
          value={12}
          change={+2}
          icon={<StrategyIcon />}
        />
        <StatCard
          title="运行任务"
          value={3}
          change={0}
          icon={<TaskIcon />}
        />
        <StatCard
          title="本月收益"
          value="15.8%"
          change={+3.2}
          icon={<ProfitIcon />}
        />
        <StatCard
          title="风险指标"
          value="0.8"
          change={-0.1}
          icon={<RiskIcon />}
        />
      </div>

      {/* 主要内容区域 */}
      <div className="grid grid-cols-3 gap-6">
        {/* 左侧 - 最近活动 */}
        <div className="col-span-2">
          <Card title="最近活动" extra={<ViewAllLink />}>
            <RecentActivityList />
          </Card>
        </div>

        {/* 右侧 - 快速操作 */}
        <div className="col-span-1">
          <Card title="快速操作">
            <QuickActionButtons />
          </Card>
        </div>
      </div>

      {/* 底部图表区域 */}
      <div className="grid grid-cols-2 gap-6 mt-8">
        <Card title="收益趋势">
          <ProfitTrendChart />
        </Card>
        <Card title="策略表现">
          <StrategyPerformanceChart />
        </Card>
      </div>
    </div>
  );
};
```

#### 4.1.2 统计卡片设计
```typescript
// 统计卡片组件
interface StatCardProps {
  title: string;
  value: string | number;
  change: number;
  icon: React.ReactNode;
  loading?: boolean;
}

const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  change,
  icon,
  loading = false
}) => {
  const changeColor = change > 0 ? 'text-success' : change < 0 ? 'text-error' : 'text-gray-500';
  const changeIcon = change > 0 ? '↑' : change < 0 ? '↓' : '→';

  return (
    <Card className="stat-card">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-gray-600 text-sm mb-1">{title}</p>
          <Skeleton loading={loading} paragraph={false}>
            <h3 className="text-2xl font-bold text-gray-900">{value}</h3>
          </Skeleton>
          <div className={`flex items-center mt-2 text-sm ${changeColor}`}>
            <span className="mr-1">{changeIcon}</span>
            <span>{Math.abs(change)}</span>
          </div>
        </div>
        <div className="text-3xl text-primary-500 opacity-80">
          {icon}
        </div>
      </div>
    </Card>
  );
};
```

### 4.2 策略管理页面

#### 4.2.1 策略列表设计
```typescript
// 策略列表页面
const StrategyListPage: React.FC = () => {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [filters, setFilters] = useState<StrategyFilters>({});
  const [selectedRows, setSelectedRows] = useState<string[]>([]);

  return (
    <div className="strategy-list-page">
      {/* 页面头部 */}
      <PageHeader
        title="策略管理"
        subTitle="管理和监控您的交易策略"
        extra={[
          <Button key="import" icon={<ImportIcon />}>
            导入策略
          </Button>,
          <Button key="create" type="primary" icon={<PlusIcon />}>
            创建策略
          </Button>
        ]}
      />

      {/* 筛选和搜索 */}
      <Card className="mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Input.Search
              placeholder="搜索策略名称"
              style={{ width: 300 }}
              onSearch={handleSearch}
            />
            <Select
              placeholder="任务类型"
              style={{ width: 150 }}
              onChange={handleTaskTypeFilter}
            >
              <Option value="all">全部</Option>
              <Option value="portfolio_management">投资组合</Option>
              <Option value="algorithmic_trading">算法交易</Option>
              <Option value="order_execution">订单执行</Option>
            </Select>
            <Select
              placeholder="算法"
              style={{ width: 120 }}
              onChange={handleAlgorithmFilter}
            >
              <Option value="all">全部</Option>
              <Option value="ppo">PPO</Option>
              <Option value="sac">SAC</Option>
              <Option value="dqn">DQN</Option>
            </Select>
          </div>
          <div className="flex items-center space-x-2">
            <Button icon={<FilterIcon />}>高级筛选</Button>
            <Button icon={<RefreshIcon />} onClick={handleRefresh}>
              刷新
            </Button>
          </div>
        </div>
      </Card>

      {/* 策略表格 */}
      <Card>
        <Table
          columns={strategyColumns}
          dataSource={strategies}
          rowSelection={{
            selectedRowKeys: selectedRows,
            onChange: setSelectedRows
          }}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) =>
              `显示 ${range[0]}-${range[1]} 条，共 ${total} 条`
          }}
        />
      </Card>
    </div>
  );
};
```

#### 4.2.2 策略编辑器设计
```typescript
// 策略编辑器页面
const StrategyEditorPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('form');
  const [config, setConfig] = useState<StrategyConfig>({});

  return (
    <div className="strategy-editor">
      {/* 顶部操作栏 */}
      <div className="flex items-center justify-between mb-6 p-4 bg-white border rounded-lg">
        <div className="flex items-center space-x-4">
          <Button icon={<ArrowLeftIcon />} onClick={handleBack}>
            返回
          </Button>
          <div>
            <h1 className="text-xl font-semibold">策略编辑器</h1>
            <p className="text-gray-500 text-sm">创建和配置您的交易策略</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Button icon={<SaveIcon />}>保存草稿</Button>
          <Button icon={<PlayIcon />}>测试配置</Button>
          <Button type="primary" icon={<CheckIcon />}>
            保存策略
          </Button>
        </div>
      </div>

      {/* 编辑器主体 */}
      <div className="grid grid-cols-4 gap-6">
        {/* 左侧配置面板 */}
        <div className="col-span-3">
          <Card>
            <Tabs activeKey={activeTab} onChange={setActiveTab}>
              <TabPane key="form" tab="表单配置">
                <StrategyConfigForm
                  config={config}
                  onChange={setConfig}
                />
              </TabPane>
              <TabPane key="code" tab="代码编辑">
                <CodeEditor
                  language="python"
                  value={config.customCode}
                  onChange={handleCodeChange}
                  theme="vs-dark"
                  height="600px"
                />
              </TabPane>
              <TabPane key="visual" tab="可视化设计">
                <VisualStrategyBuilder
                  config={config}
                  onChange={setConfig}
                />
              </TabPane>
            </Tabs>
          </Card>
        </div>

        {/* 右侧信息面板 */}
        <div className="col-span-1">
          <div className="space-y-6">
            {/* 配置验证 */}
            <Card title="配置验证" size="small">
              <ConfigValidationStatus config={config} />
            </Card>

            {/* 参数预览 */}
            <Card title="参数预览" size="small">
              <ParameterPreview config={config} />
            </Card>

            {/* 帮助文档 */}
            <Card title="帮助文档" size="small">
              <HelpDocLinks taskType={config.taskType} />
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};
```

### 4.3 训练监控页面

#### 4.3.1 训练仪表板
```typescript
// 训练监控仪表板
const TrainingDashboard: React.FC = () => {
  const [jobs, setJobs] = useState<TrainingJob[]>([]);
  const [selectedJob, setSelectedJob] = useState<string | null>(null);

  return (
    <div className="training-dashboard">
      {/* 页面头部 */}
      <PageHeader
        title="训练监控"
        subTitle="实时监控训练任务的进展和性能"
        extra={[
          <Button key="refresh" icon={<RefreshIcon />}>
            刷新
          </Button>,
          <Button key="start" type="primary" icon={<PlayIcon />}>
            开始训练
          </Button>
        ]}
      />

      <div className="grid grid-cols-4 gap-6">
        {/* 左侧任务列表 */}
        <div className="col-span-1">
          <Card title="训练任务" size="small">
            <div className="space-y-2">
              {jobs.map(job => (
                <JobCard
                  key={job.id}
                  job={job}
                  selected={selectedJob === job.id}
                  onClick={() => setSelectedJob(job.id)}
                />
              ))}
            </div>
          </Card>
        </div>

        {/* 右侧详情区域 */}
        <div className="col-span-3">
          {selectedJob ? (
            <TrainingJobDetail jobId={selectedJob} />
          ) : (
            <Empty
              description="请选择一个训练任务查看详情"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          )}
        </div>
      </div>
    </div>
  );
};

// 训练任务卡片
const JobCard: React.FC<JobCardProps> = ({ job, selected, onClick }) => {
  const statusColor = {
    pending: 'orange',
    running: 'blue',
    completed: 'green',
    failed: 'red',
    cancelled: 'default'
  }[job.status] || 'default';

  return (
    <div
      className={`job-card p-3 border rounded cursor-pointer transition-colors ${
        selected ? 'border-primary-500 bg-primary-50' : 'border-gray-200 hover:border-gray-300'
      }`}
      onClick={onClick}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="font-medium text-sm truncate">{job.name}</span>
        <Tag color={statusColor} size="small">
          {job.status}
        </Tag>
      </div>
      <div className="text-xs text-gray-500 mb-2">
        {job.strategy?.name}
      </div>
      {job.status === 'running' && (
        <Progress
          percent={job.progress}
          size="small"
          showInfo={false}
          strokeColor="#1890ff"
        />
      )}
      <div className="text-xs text-gray-400 mt-1">
        {formatRelativeTime(job.createdAt)}
      </div>
    </div>
  );
};
```

#### 4.3.2 实时指标展示
```typescript
// 实时训练指标组件
const RealTimeMetrics: React.FC<{ jobId: string }> = ({ jobId }) => {
  const [metrics, setMetrics] = useState<TrainingMetrics[]>([]);
  const websocket = useWebSocket(`/ws/training/${jobId}`);

  useEffect(() => {
    websocket.onMessage = (data) => {
      if (data.type === 'training_update') {
        setMetrics(prev => [...prev.slice(-99), data.data]);
      }
    };
  }, [websocket]);

  return (
    <div className="real-time-metrics">
      <div className="grid grid-cols-2 gap-4 mb-6">
        {/* 损失函数 */}
        <Card title="训练损失" size="small">
          <LineChart
            data={metrics}
            xKey="epoch"
            yKey="loss"
            height={200}
            color="#f5222d"
          />
        </Card>

        {/* 准确率 */}
        <Card title="验证准确率" size="small">
          <LineChart
            data={metrics}
            xKey="epoch"
            yKey="accuracy"
            height={200}
            color="#52c41a"
          />
        </Card>
      </div>

      {/* 详细指标表格 */}
      <Card title="详细指标" size="small">
        <Table
          size="small"
          dataSource={metrics.slice(-10)}
          columns={[
            { title: 'Epoch', dataIndex: 'epoch', width: 80 },
            { title: 'Loss', dataIndex: 'loss', render: val => val.toFixed(6) },
            { title: 'Accuracy', dataIndex: 'accuracy', render: val => `${(val * 100).toFixed(2)}%` },
            { title: 'Time', dataIndex: 'timestamp', render: formatTime }
          ]}
          pagination={false}
          scroll={{ y: 300 }}
        />
      </Card>
    </div>
  );
};
```

### 4.4 数据管理页面

#### 4.4.1 数据集管理
```typescript
// 数据集管理页面
const DatasetManagePage: React.FC = () => {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [uploading, setUploading] = useState(false);

  return (
    <div className="dataset-manage-page">
      <PageHeader
        title="数据管理"
        subTitle="管理训练和回测所需的数据集"
        extra={[
          <Button key="import" icon={<ImportIcon />}>
            导入数据
          </Button>,
          <Upload
            key="upload"
            multiple
            showUploadList={false}
            beforeUpload={handleUpload}
          >
            <Button type="primary" icon={<UploadIcon />} loading={uploading}>
              上传数据集
            </Button>
          </Upload>
        ]}
      />

      {/* 数据集网格视图 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {datasets.map(dataset => (
          <DatasetCard
            key={dataset.id}
            dataset={dataset}
            onPreview={handlePreview}
            onEdit={handleEdit}
            onDelete={handleDelete}
          />
        ))}
      </div>
    </div>
  );
};

// 数据集卡片
const DatasetCard: React.FC<DatasetCardProps> = ({
  dataset,
  onPreview,
  onEdit,
  onDelete
}) => {
  const typeIcon = {
    market_data: <MarketIcon />,
    custom: <FileIcon />,
    synthetic: <GenerateIcon />
  }[dataset.dataType];

  return (
    <Card
      hoverable
      className="dataset-card"
      cover={
        <div className="h-32 bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
          <div className="text-white text-4xl">{typeIcon}</div>
        </div>
      }
      actions={[
        <EyeIcon key="preview" onClick={() => onPreview(dataset)} />,
        <EditIcon key="edit" onClick={() => onEdit(dataset)} />,
        <DeleteIcon key="delete" onClick={() => onDelete(dataset)} />
      ]}
    >
      <Card.Meta
        title={dataset.name}
        description={
          <div className="space-y-2">
            <p className="text-gray-500 text-sm line-clamp-2">
              {dataset.description}
            </p>
            <div className="flex items-center justify-between text-xs text-gray-400">
              <span>{formatFileSize(dataset.fileSize)}</span>
              <span>{formatRelativeTime(dataset.createdAt)}</span>
            </div>
            <div className="flex items-center space-x-2">
              <Tag size="small" color="blue">
                {dataset.dataType}
              </Tag>
              {dataset.isProcessed && (
                <Tag size="small" color="green">
                  已处理
                </Tag>
              )}
            </div>
          </div>
        }
      />
    </Card>
  );
};
```

#### 4.4.2 数据预览组件
```typescript
// 数据预览组件
const DataPreviewModal: React.FC<DataPreviewModalProps> = ({
  dataset,
  visible,
  onClose
}) => {
  const [previewData, setPreviewData] = useState<any[]>([]);
  const [statistics, setStatistics] = useState<DataStatistics | null>(null);
  const [loading, setLoading] = useState(false);

  return (
    <Modal
      title={`数据预览 - ${dataset?.name}`}
      open={visible}
      onCancel={onClose}
      width={1200}
      footer={null}
    >
      <Tabs defaultActiveKey="preview">
        <TabPane key="preview" tab="数据预览">
          <div className="space-y-4">
            {/* 基本信息 */}
            <div className="grid grid-cols-4 gap-4">
              <Statistic title="总行数" value={dataset?.rowCount} />
              <Statistic title="列数" value={previewData[0]?.length || 0} />
              <Statistic title="文件大小" value={formatFileSize(dataset?.fileSize)} />
              <Statistic title="数据类型" value={dataset?.dataType} />
            </div>

            {/* 数据表格 */}
            <Table
              dataSource={previewData}
              scroll={{ x: 'max-content', y: 400 }}
              pagination={{ pageSize: 20 }}
              size="small"
              loading={loading}
            />
          </div>
        </TabPane>

        <TabPane key="statistics" tab="统计信息">
          {statistics && (
            <div className="space-y-6">
              {/* 数值列统计 */}
              <Card title="数值列统计" size="small">
                <Table
                  dataSource={statistics.numericalColumns}
                  columns={[
                    { title: '列名', dataIndex: 'column' },
                    { title: '均值', dataIndex: 'mean', render: val => val.toFixed(4) },
                    { title: '标准差', dataIndex: 'std', render: val => val.toFixed(4) },
                    { title: '最小值', dataIndex: 'min' },
                    { title: '最大值', dataIndex: 'max' },
                    { title: '缺失值', dataIndex: 'nullCount' }
                  ]}
                  pagination={false}
                  size="small"
                />
              </Card>

              {/* 分布图表 */}
              <Card title="数据分布" size="small">
                <div className="grid grid-cols-2 gap-4">
                  {statistics.distributions.map(dist => (
                    <div key={dist.column}>
                      <h4 className="text-sm font-medium mb-2">{dist.column}</h4>
                      <Histogram data={dist.data} />
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          )}
        </TabPane>

        <TabPane key="quality" tab="数据质量">
          <DataQualityReport dataset={dataset} />
        </TabPane>
      </Tabs>
    </Modal>
  );
};
```

## 5. 交互设计

### 5.1 导航设计

#### 5.1.1 侧边栏导航
```typescript
// 导航菜单结构
const navigationItems = [
  {
    key: 'dashboard',
    icon: <DashboardIcon />,
    title: '仪表板',
    path: '/dashboard'
  },
  {
    key: 'strategies',
    icon: <StrategyIcon />,
    title: '策略管理',
    path: '/strategies',
    children: [
      { key: 'strategy-list', title: '策略列表', path: '/strategies' },
      { key: 'strategy-create', title: '创建策略', path: '/strategies/create' },
      { key: 'strategy-templates', title: '策略模板', path: '/strategies/templates' }
    ]
  },
  {
    key: 'training',
    icon: <TrainingIcon />,
    title: '训练管理',
    path: '/training',
    children: [
      { key: 'training-jobs', title: '训练任务', path: '/training/jobs' },
      { key: 'training-monitor', title: '实时监控', path: '/training/monitor' },
      { key: 'training-history', title: '历史记录', path: '/training/history' }
    ]
  },
  {
    key: 'data',
    icon: <DataIcon />,
    title: '数据管理',
    path: '/data',
    children: [
      { key: 'datasets', title: '数据集', path: '/data/datasets' },
      { key: 'upload', title: '数据上传', path: '/data/upload' },
      { key: 'processing', title: '数据处理', path: '/data/processing' }
    ]
  },
  {
    key: 'analysis',
    icon: <AnalysisIcon />,
    title: '结果分析',
    path: '/analysis',
    children: [
      { key: 'performance', title: '性能分析', path: '/analysis/performance' },
      { key: 'comparison', title: '策略对比', path: '/analysis/comparison' },
      { key: 'reports', title: '分析报告', path: '/analysis/reports' }
    ]
  },
  {
    key: 'tools',
    icon: <ToolsIcon />,
    title: '工具集成',
    path: '/tools',
    children: [
      { key: 'finagent', title: 'FinAgent', path: '/tools/finagent' },
      { key: 'earnmore', title: 'EarnMore', path: '/tools/earnmore' },
      { key: 'market-dynamics', title: '市场动态', path: '/tools/market-dynamics' }
    ]
  },
  {
    key: 'settings',
    icon: <SettingsIcon />,
    title: '系统设置',
    path: '/settings',
    children: [
      { key: 'profile', title: '个人设置', path: '/settings/profile' },
      { key: 'system', title: '系统配置', path: '/settings/system' },
      { key: 'help', title: '帮助文档', path: '/settings/help' }
    ]
  }
];

// 侧边栏组件
const Sidebar: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();

  return (
    <div className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-header">
        <div className="logo">
          <img src="/logo.svg" alt="TradeMaster" />
          {!collapsed && <span className="logo-text">TradeMaster</span>}
        </div>
        <Button
          type="text"
          icon={collapsed ? <MenuUnfoldIcon /> : <MenuFoldIcon />}
          onClick={() => setCollapsed(!collapsed)}
          className="collapse-btn"
        />
      </div>

      <Menu
        mode="inline"
        selectedKeys={[getActiveKey(location.pathname)]}
        openKeys={getOpenKeys(location.pathname)}
        items={navigationItems}
        inlineCollapsed={collapsed}
      />
    </div>
  );
};
```

#### 5.1.2 面包屑导航
```typescript
// 面包屑组件
const BreadcrumbNav: React.FC = () => {
  const location = useLocation();
  const breadcrumbItems = generateBreadcrumbs(location.pathname);

  return (
    <Breadcrumb className="mb-4">
      <Breadcrumb.Item>
        <Link to="/dashboard">
          <HomeIcon className="mr-1" />
          首页
        </Link>
      </Breadcrumb.Item>
      {breadcrumbItems.map((item, index) => (
        <Breadcrumb.Item key={index}>
          {item.path ? (
            <Link to={item.path}>{item.title}</Link>
          ) : (
            item.title
          )}
        </Breadcrumb.Item>
      ))}
    </Breadcrumb>
  );
};
```

### 5.2 表单设计

#### 5.2.1 策略配置表单
```typescript
// 策略配置表单
const StrategyConfigForm: React.FC<StrategyConfigFormProps> = ({
  config,
  onChange
}) => {
  const [form] = Form.useForm();

  const handleFieldChange = (changedFields: any, allFields: any) => {
    const newConfig = form.getFieldsValue();
    onChange(newConfig);
  };

  return (
    <Form
      form={form}
      layout="vertical"
      initialValues={config}
      onFieldsChange={handleFieldChange}
      className="strategy-config-form"
    >
      {/* 基本信息 */}
      <Card title="基本信息" className="mb-6">
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              label="策略名称"
              name="name"
              rules={[{ required: true, message: '请输入策略名称' }]}
            >
              <Input placeholder="输入策略名称" maxLength={50} />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              label="任务类型"
              name="taskType"
              rules={[{ required: true, message: '请选择任务类型' }]}
            >
              <Select placeholder="选择任务类型">
                <Option value="portfolio_management">投资组合管理</Option>
                <Option value="algorithmic_trading">算法交易</Option>
                <Option value="order_execution">订单执行</Option>
              </Select>
            </Form.Item>
          </Col>
        </Row>

        <Form.Item label="策略描述" name="description">
          <Input.TextArea
            placeholder="描述策略的目标和特点"
            rows={3}
            maxLength={500}
          />
        </Form.Item>
      </Card>

      {/* 算法配置 */}
      <Card title="算法配置" className="mb-6">
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              label="算法类型"
              name="algorithm"
              rules={[{ required: true, message: '请选择算法类型' }]}
            >
              <Select placeholder="选择算法类型">
                {getAlgorithmOptions(config.taskType).map(option => (
                  <Option key={option.value} value={option.value}>
                    {option.label}
                  </Option>
                ))}
              </Select>
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              label="数据集"
              name="dataset"
              rules={[{ required: true, message: '请选择数据集' }]}
            >
              <Select placeholder="选择数据集">
                {getDatasetOptions(config.taskType).map(option => (
                  <Option key={option.value} value={option.value}>
                    {option.label}
                  </Option>
                ))}
              </Select>
            </Form.Item>
          </Col>
        </Row>
      </Card>

      {/* 训练参数 */}
      <Card title="训练参数" className="mb-6">
        <Row gutter={16}>
          <Col span={8}>
            <Form.Item
              label="训练轮数"
              name="epochs"
              rules={[{ required: true, message: '请输入训练轮数' }]}
            >
              <InputNumber
                min={1}
                max={1000}
                placeholder="默认: 10"
                style={{ width: '100%' }}
              />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item
              label="学习率"
              name="learningRate"
              rules={[{ required: true, message: '请输入学习率' }]}
            >
              <InputNumber
                min={0.0001}
                max={1}
                step={0.0001}
                placeholder="默认: 0.001"
                style={{ width: '100%' }}
              />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item
              label="批次大小"
              name="batchSize"
              rules={[{ required: true, message: '请输入批次大小' }]}
            >
              <InputNumber
                min={1}
                max={1000}
                placeholder="默认: 32"
                style={{ width: '100%' }}
              />
            </Form.Item>
          </Col>
        </Row>

        {/* 高级参数 */}
        <Collapse ghost>
          <Collapse.Panel header="高级参数" key="advanced">
            <AdvancedParameterForm
              algorithm={config.algorithm}
              values={config.advancedParams}
              onChange={handleAdvancedParamsChange}
            />
          </Collapse.Panel>
        </Collapse>
      </Card>

      {/* 验证和预览 */}
      <Card title="配置验证">
        <ConfigValidation config={config} />
      </Card>
    </Form>
  );
};
```

#### 5.2.2 动态表单生成
```typescript
// 动态表单生成器
interface FormFieldConfig {
  name: string;
  label: string;
  type: 'input' | 'number' | 'select' | 'switch' | 'slider' | 'textarea';
  rules?: any[];
  options?: { label: string; value: any }[];
  props?: any;
  dependencies?: string[];
  condition?: (values: any) => boolean;
}

const DynamicFormBuilder: React.FC<{
  fields: FormFieldConfig[];
  values: any;
  onChange: (values: any) => void;
}> = ({ fields, values, onChange }) => {
  const [form] = Form.useForm();

  const renderField = (field: FormFieldConfig) => {
    // 检查条件渲染
    if (field.condition && !field.condition(values)) {
      return null;
    }

    const commonProps = {
      ...field.props,
      style: { width: '100%', ...field.props?.style }
    };

    switch (field.type) {
      case 'input':
        return <Input {...commonProps} />;
      
      case 'number':
        return <InputNumber {...commonProps} />;
      
      case 'select':
        return (
          <Select {...commonProps}>
            {field.options?.map(option => (
              <Option key={option.value} value={option.value}>
                {option.label}
              </Option>
            ))}
          </Select>
        );
      
      case 'switch':
        return <Switch {...commonProps} />;
      
      case 'slider':
        return <Slider {...commonProps} />;
      
      case 'textarea':
        return <Input.TextArea {...commonProps} />;
      
      default:
        return <Input {...commonProps} />;
    }
  };

  return (
    <Form
      form={form}
      layout="vertical"
      initialValues={values}
      onValuesChange={(_, allValues) => onChange(allValues)}
    >
      {fields.map(field => (
        <Form.Item
          key={field.name}
          name={field.name}
          label={field.label}
          rules={field.rules}
          dependencies={field.dependencies}
        >
          {renderField(field)}
        </Form.Item>
      ))}
    </Form>
  );
};
```

### 5.3 数据可视化设计

#### 5.3.1 图表组件库
```typescript
// 通用图表组件
const LineChart: React.FC<LineChartProps> = ({
  data,
  xKey,
  yKey,
  color = '#1890ff',
  height = 300,
  showGrid = true,
  showTooltip = true,
  smooth = true
}) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (chartRef.current) {
      chartInstance.current = echarts.init(chartRef.current);
      
      const option: echarts.EChartsOption = {
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: data.map(d => d[xKey]),
          axisLine: { show: showGrid },
          axisTick: { show: showGrid }
        },
        yAxis: {
          type: 'value',
          axisLine: { show: showGrid },
          axisTick: { show: showGrid },
          splitLine: { show: showGrid }
        },
        series: [{
          data: data.map(d => d[yKey]),
          type: 'line',
          smooth,
          itemStyle: { color },
          lineStyle: { color },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{
              offset: 0,
              color: color + '40'
            }, {
              offset: 1,
              color: color + '00'
            }])
          }
        }],
        tooltip: showTooltip ? {
          trigger: 'axis',
          formatter: (params: any) => {
            const point = params[0];
            return `${point.name}: ${point.value}`;
          }
        } : undefined
      };

      chartInstance.current.setOption(option);
    }

    return () => {
      chartInstance.current?.dispose();
    };
  }, [data, xKey, yKey, color, height, showGrid, showTooltip, smooth]);

  return <div ref={chartRef} style={{ width: '100%', height }} />;
};

// 雷达图组件
const RadarChart: React.FC<RadarChartProps> = ({
  data,
  indicators,
  colors = ['#1890ff', '#52c41a', '#faad14']
}) => {
  const chartRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (chartRef.current) {
      const chart = echarts.init(chartRef.current);
      
      const option: echarts.EChartsOption = {
        radar: {
          indicator: indicators.map(ind => ({
            name: ind.name,
            max: ind.max || 100
          })),
          radius: '70%'
        },
        series: [{
          type: 'radar',
          data: data.map((item, index) => ({
            value: item.values,
            name: item.name,
            itemStyle: { color: colors[index % colors.length] },
            areaStyle: { opacity: 0.1 }
          }))
        }],
        legend: {
          data: data.map(item => item.name),
          bottom: 0
        }
      };

      chart.setOption(option);
      
      return () => chart.dispose();
    }
  }, [data, indicators, colors]);

  return <div ref={chartRef} style={{ width: '100%', height: '400px' }} />;
};

// 热力图组件
const HeatmapChart: React.FC<HeatmapProps> = ({
  data,
  xAxisData,
  yAxisData,
  colorRange = ['#313695', '#4575b4', '#74add1', '#abd9e9', '#fee090', '#fdae61', '#f46d43', '#d73027']
}) => {
  const chartRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (chartRef.current) {
      const chart = echarts.init(chartRef.current);
      
      const option: echarts.EChartsOption = {
        grid: {
          height: '50%',
          top: '10%'
        },
        xAxis: {
          type: 'category',
          data: xAxisData,
          splitArea: { show: true }
        },
        yAxis: {
          type: 'category',
          data: yAxisData,
          splitArea: { show: true }
        },
        visualMap: {
          min: Math.min(...data.map(d => d[2])),
          max: Math.max(...data.map(d => d[2])),
          calculable: true,
          orient: 'horizontal',
          left: 'center',
          bottom: '15%',
          inRange: {
            color: colorRange
          }
        },
        series: [{
          type: 'heatmap',
          data,
          label: { show: true },
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          }
        }]
      };

      chart.setOption(option);
      
      return () => chart.dispose();
    }
  }, [data, xAxisData, yAxisData, colorRange]);

  return <div ref={chartRef} style={{ width: '100%', height: '400px' }} />;
};
```

#### 5.3.2 仪表板图表布局
```typescript
// 仪表板图表布局
const ChartDashboard: React.FC<{
  metrics: TrainingMetrics[];
  performance: PerformanceData;
}> = ({ metrics, performance }) => {
  return (
    <div className="chart-dashboard">
      {/* 主要指标 */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <MetricCard
          title="当前收益率"
          value={`${performance.currentReturn.toFixed(2)}%`}
          trend={performance.returnTrend}
          color="blue"
        />
        <MetricCard
          title="最大回撤"
          value={`${performance.maxDrawdown.toFixed(2)}%`}
          trend={performance.drawdownTrend}
          color="red"
        />
        <MetricCard
          title="夏普比率"
          value={performance.sharpeRatio.toFixed(3)}
          trend={performance.sharpeTrend}
          color="green"
        />
        <MetricCard
          title="胜率"
          value={`${performance.winRate.toFixed(1)}%`}
          trend={performance.winRateTrend}
          color="purple"
        />
      </div>

      {/* 主要图表 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 收益曲线 */}
        <Card title="收益曲线" extra={<ChartToolbar />}>
          <LineChart
            data={performance.returnsHistory}
            xKey="date"
            yKey="cumulativeReturn"
            height={300}
            color="#1890ff"
          />
        </Card>

        {/* 回撤分析 */}
        <Card title="回撤分析" extra={<ChartToolbar />}>
          <LineChart
            data={performance.drawdownHistory}
            xKey="date"
            yKey="drawdown"
            height={300}
            color="#f5222d"
          />
        </Card>

        {/* 风险收益散点图 */}
        <Card title="风险收益分析" extra={<ChartToolbar />}>
          <ScatterPlot
            data={performance.riskReturnData}
            xKey="risk"
            yKey="return"
            height={300}
          />
        </Card>

        {/* 策略表现雷达图 */}
        <Card title="综合表现" extra={<ChartToolbar />}>
          <RadarChart
            data={[{
              name: '当前策略',
              values: performance.radarData
            }]}
            indicators={[
              { name: '收益率', max: 100 },
              { name: '稳定性', max: 100 },
              { name: '风险控制', max: 100 },
              { name: '交易频率', max: 100 },
              { name: '市场适应性', max: 100 }
            ]}
          />
        </Card>
      </div>
    </div>
  );
};
```

## 6. 响应式和适配性设计

### 6.1 移动端适配

#### 6.1.1 移动端布局
```scss
// 移动端布局样式
.mobile-layout {
  @media (max-width: 768px) {
    .page-header {
      padding: 12px 16px;
      
      .page-title {
        font-size: 18px;
        margin-bottom: 4px;
      }
      
      .page-subtitle {
        font-size: 14px;
        display: none; // 在小屏幕上隐藏副标题
      }
      
      .page-extra {
        .btn {
          padding: 6px 12px;
          font-size: 14px;
          
          .btn-text {
            display: none; // 只显示图标
          }
        }
      }
    }
    
    .card {
      margin-bottom: 16px;
      border-radius: 8px;
      
      .card-header {
        padding: 12px 16px;
        font-size: 16px;
      }
      
      .card-body {
        padding: 16px;
      }
    }
    
    .table-responsive {
      .table {
        font-size: 14px;
        
        th, td {
          padding: 8px 12px;
        }
        
        // 隐藏次要列
        .hidden-mobile {
          display: none;
        }
      }
    }
  }
}
```

#### 6.1.2 触摸友好的交互 
```scss
// 触摸友好的交互设计
.touch-friendly {
  // 增大点击区域
  .btn, .link, .tab {
    min-height: 44px;
    min-width: 44px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  // 滑动手势支持
  .swipeable {
    touch-action: pan-x;
    -webkit-overflow-scrolling: touch;
  }
  
  // 长按菜单
  .long-press {
    -webkit-user-select: none;
    user-select: none;
    -webkit-touch-callout: none;
  }
  
  // 滚动优化
  .scroll-container {
    -webkit-overflow-scrolling: touch;
    overflow-scrolling: touch;
  }
}
```

### 6.2 主题切换

#### 6.2.1 主题系统实现
```typescript
// 主题系统
interface Theme {
  name: string;
  colors: {
    primary: string;
    secondary: string;
    background: string;
    surface: string;
    text: string;
    textSecondary: string;
    border: string;
    success: string;
    warning: string;
    error: string;
  };
  shadows: {
    sm: string;
    md: string;
    lg: string;
  };
  borderRadius: {
    sm: string;
    md: string;
    lg: string;
  };
}

const lightTheme: Theme = {
  name: 'light',
  colors: {
    primary: '#1890ff',
    secondary: '#722ed1',
    background: '#ffffff',
    surface: '#fafafa',
    text: '#000000d9',
    textSecondary: '#00000073',
    border: '#d9d9d9',
    success: '#52c41a',
    warning: '#faad14',
    error: '#f5222d'
  },
  shadows: {
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1)'
  },
  borderRadius: {
    sm: '4px',
    md: '6px',
    lg: '8px'
  }
};

const darkTheme: Theme = {
  name: 'dark',
  colors: {
    primary: '#1890ff',
    secondary: '#722ed1',
    background: '#141414',
    surface: '#1f1f1f',
    text: '#ffffffd9',
    textSecondary: '#ffffff73',
    border: '#434343',
    success: '#52c41a',
    warning: '#faad14',
    error: '#f5222d'
  },
  shadows: {
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.2)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.3)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.4)'
  },
  borderRadius: {
    sm: '4px',
    md: '6px',
    lg: '8px'
  }
};

// 主题提供者
const ThemeProvider: React.FC<{
  theme: Theme;
  children: React.ReactNode;
}> = ({ theme, children }) => {
  useEffect(() => {
    // 应用CSS变量
    const root = document.documentElement;
    Object.entries(theme.colors).forEach(([key, value]) => {
      root.style.setProperty(`--color-${key}`, value);
    });
    Object.entries(theme.shadows).forEach(([key, value]) => {
      root.style.setProperty(`--shadow-${key}`, value);
    });
    Object.entries(theme.borderRadius).forEach(([key, value]) => {
      root.style.setProperty(`--radius-${key}`, value);
    });
    
    // 设置主题类名
    root.setAttribute('data-theme', theme.name);
  }, [theme]);

  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: theme.colors.primary,
          colorBgBase: theme.colors.background,
          colorTextBase: theme.colors.text
        }
      }}
    >
      {children}
    </ConfigProvider>
  );
};
```

#### 6.2.2 主题切换组件
```typescript
// 主题切换器
const ThemeToggle: React.FC = () => {
  const [currentTheme, setCurrentTheme] = useState<'light' | 'dark'>('light');

  const toggleTheme = () => {
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    setCurrentTheme(newTheme);
    localStorage.setItem('theme', newTheme);
  };

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | null;
    if (savedTheme) {
      setCurrentTheme(savedTheme);
    } else {
      // 检测系统主题偏好
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      setCurrentTheme(prefersDark ? 'dark' : 'light');
    }
  }, []);

  return (
    <Button
      type="text"
      icon={currentTheme === 'light' ? <MoonIcon /> : <SunIcon />}
      onClick={toggleTheme}
      title={`切换到${currentTheme === 'light' ? '深色' : '浅色'}模式`}
    />
  );
};
```

## 7. 用户体验优化

### 7.1 加载状态设计

#### 7.1.1 全局加载状态
```typescript
// 全局加载组件
const GlobalLoading: React.FC<{
  loading: boolean;
  tip?: string;
}> = ({ loading, tip = '正在加载...' }) => {
  if (!loading) return null;

  return (
    <div className="global-loading">
      <div className="loading-backdrop" />
      <div className="loading-content">
        <Spin size="large" />
        <p className="loading-tip">{tip}</p>
      </div>
    </div>
  );
};

// 页面级加载
const PageLoading: React.FC<{ loading: boolean }> = ({ loading }) => {
  if (!loading) return null;

  return (
    <div className="page-loading">
      <div className="loading-skeleton">
        <Skeleton active paragraph={{ rows: 6 }} />
      </div>
    </div>
  );
};

// 组件级加载
const ComponentLoading: React.FC<{
  loading: boolean;
  children: React.ReactNode;
}> = ({ loading, children }) => {
  return (
    <Spin spinning={loading} tip="加载中...">
      {children}
    </Spin>
  );
};
```

#### 7.1.2 骨架屏设计
```typescript
// 自定义骨架屏组件
const StrategyCardSkeleton: React.FC = () => {
  return (
    <Card className="strategy-card-skeleton">
      <div className="flex items-start space-x-4">
        <Skeleton.Avatar size={64} />
        <div className="flex-1">
          <Skeleton.Input style={{ width: 200, height: 24 }} active />
          <div className="mt-2">
            <Skeleton.Input style={{ width: 150, height: 16 }} active />
          </div>
          <div className="mt-4">
            <Skeleton.Input style={{ width: 100, height: 20 }} active />
          </div>
        </div>
      </div>
    </Card>
  );
};

const TableSkeleton: React.FC<{ rows?: number; columns?: number }> = ({
  rows = 5,
  columns = 4
}) => {
  return (
    <div className="table-skeleton">
      {/* 表头 */}
      <div className="flex space-x-4 mb-4">
        {Array.from({ length: columns }).map((_, index) => (
          <Skeleton.Input key={index} style={{ width: 120, height: 32 }} active />
        ))}
      </div>
      
      {/* 表格行 */}
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div key={rowIndex} className="flex space-x-4 mb-2">
          {Array.from({ length: columns }).map((_, colIndex) => (
            <Skeleton.Input key={colIndex} style={{ width: 120, height: 24 }} active />
          ))}
        </div>
      ))}
    </div>
  );
};
```

### 7.2 错误处理和反馈

#### 7.2.1 错误边界组件
```typescript
// 错误边界
class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error?: Error }
> {
  constructor(props: any) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
    // 发送错误到监控服务
    reportError(error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary">
          <Result
            status="500"
            title="页面出现错误"
            subTitle="抱歉，页面遇到了一些问题。"
            extra={[
              <Button key="refresh" onClick={() => window.location.reload()}>
                刷新页面
              </Button>,
              <Button key="back" onClick={() => window.history.back()}>
                返回上页
              </Button>
            ]}
          />
        </div>
      );
    }

    return this.props.children;
  }
}

// 网络错误处理
const NetworkErrorHandler: React.FC<{
  error: AxiosError | null;
  onRetry: () => void;
}> = ({ error, onRetry }) => {
  if (!error) return null;

  const getErrorMessage = (error: AxiosError) => {
    if (error.code === 'NETWORK_ERROR') {
      return '网络连接异常，请检查网络设置';
    }
    if (error.response?.status === 401) {
      return '登录已过期，请重新登录';
    }
    if (error.response?.status === 403) {
      return '没有权限执行此操作';
    }
    if (error.response?.status >= 500) {
      return '服务器内部错误，请稍后重试';
    }
    return error.message || '请求失败';
  };

  return (
    <Alert
      type="error"
      message="请求失败"
      description={getErrorMessage(error)}
      showIcon
      action={
        <Button size="small" danger onClick={onRetry}>
          重试
        </Button>
      }
      closable
    />
  );
};
```

#### 7.2.2 消息通知系统
```typescript
// 全局消息管理
class NotificationManager {
  private static instance: NotificationManager;
  
  static getInstance() {
    if (!NotificationManager.instance) {
      NotificationManager.instance = new NotificationManager();
    }
    return NotificationManager.instance;
  }

  success(message: string, description?: string) {
    notification.success({
      message,
      description,
      placement: 'topRight',
      duration: 4
    });
  }

  error(message: string, description?: string) {
    notification.error({
      message,
      description,
      placement: 'topRight',
      duration: 6
    });
  }

  warning(message: string, description?: string) {
    notification.warning({
      message,
      description,
      placement: 'topRight',
      duration: 5
    });
  }

  info(message: string, description?: string) {
    notification.info({
      message,
      description,
      placement: 'topRight',
      duration: 4
    });
  }

  // 操作反馈
  loading(message: string) {
    return message.loading({
      content: message,
      duration: 0 // 不自动关闭
    });
  }

  // 确认对话框
  confirm(title: string, content: string, onOk: () => void) {
    Modal.confirm({
      title,
      content,
      okText: '确认',
      cancelText: '取消',
      onOk
    });
  }
}

export const notify = NotificationManager.getInstance();
```

### 7.3 性能优化

#### 7.3.1 虚拟滚动实现
```typescript
// 虚拟滚动列表
const VirtualList: React.FC<{
  items: any[];
  itemHeight: number;
  containerHeight: number;
  renderItem: (item: any, index: number) => React.ReactNode;
}> = ({ items, itemHeight, containerHeight, renderItem }) => {
  const [scrollTop, setScrollTop] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

  // 计算可见范围
  const startIndex = Math.floor(scrollTop / itemHeight);
  const endIndex = Math.min(
    startIndex + Math.ceil(containerHeight / itemHeight) + 1,
    items.length
  );

  const visibleItems = items.slice(startIndex, endIndex);
  const totalHeight = items.length * itemHeight;
  const offsetY = startIndex * itemHeight;

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(e.currentTarget.scrollTop);
  };

  return (
    <div
      ref={containerRef}
      style={{ height: containerHeight, overflow: 'auto' }}
      onScroll={handleScroll}
    >
      <div style={{ height: totalHeight, position: 'relative' }}>
        <div style={{ transform: `translateY(${offsetY}px)` }}>
          {visibleItems.map((item, index) => (
            <div
              key={startIndex + index}
              style={{ height: itemHeight }}
            >
              {renderItem(item, startIndex + index)}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
```

#### 7.3.2 图片懒加载
```typescript
// 图片懒加载组件
const LazyImage: React.FC<{
  src: string;
  alt: string;
  placeholder?: string;
  className?: string;
}> = ({ src, alt, placeholder, className }) => {
  const [loaded, setLoaded] = useState(false);
  const [inView, setInView] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setInView(true);
          observer.disconnect();
        }
      },
      { threshold: 0.1 }
    );

    if (imgRef.current) {
      observer.observe(imgRef.current);
    }

    return () => observer.disconnect();
  }, []);

  return (
    <div className={`lazy-image ${className}`} ref={imgRef}>
      {inView && (
        <>
          {!loaded && placeholder && (
            <img
              src={placeholder}
              alt=""
              className="placeholder"
            />
          )}
          <img
            src={src}
            alt={alt}
            onLoad={() => setLoaded(true)}
            style={{ display: loaded ? 'block' : 'none' }}
          />
        </>
      )}
    </div>
  );
};
```

## 8. 总结

### 8.1 设计特点

1. **用户导向**: 基于用户需求和使用场景设计界面
2. **一致性**: 统一的设计语言和交互模式
3. **响应式**: 适配各种设备和屏幕尺寸
4. **高效性**: 优化加载速度和交互响应
5. **可访问性**: 支持各种用户群体的访问需求

### 8.2 技术亮点

1. **组件化设计**: 高度模块化的组件架构
2. **主题系统**: 完整的深浅色主题支持
3. **性能优化**: 虚拟滚动、懒加载等优化技术
4. **错误处理**: 完善的错误边界和反馈机制
5. **交互优化**: 流畅的动画和过渡效果

### 8.3 实施建议

1. **渐进式开发**: 先实现核心界面，再完善细节
2. **用户测试**: 定期进行可用性测试和用户反馈收集
3. **性能监控**: 持续监控页面性能和用户体验指标
4. **迭代优化**: 基于用户反馈持续改进界面设计
5. **文档维护**: 保持设计规范和组件文档的更新

---

**文档状态**: ✅ 已完成  
**审核状态**: 🔄 待审核  
**下一步**: 进入开发实施阶段

**设计交付物**:
- ✅ 完整的UI/UX设计方案
- ✅ 视觉设计系统规范  
- ✅ 组件设计规范
- ✅ 响应式设计方案
- ✅ 用户体验优化方案