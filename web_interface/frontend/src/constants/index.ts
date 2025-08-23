// API endpoints
export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/api/v1/auth/login',
    LOGOUT: '/api/v1/auth/logout',
    REGISTER: '/api/v1/auth/register',
    REFRESH: '/api/v1/auth/refresh',
    PROFILE: '/api/v1/auth/me',
    CHANGE_PASSWORD: '/api/v1/auth/change-password',
    FORGOT_PASSWORD: '/api/v1/auth/forgot-password',
    RESET_PASSWORD: '/api/v1/auth/reset-password',
    VERIFY_TOKEN: '/api/v1/auth/verify-token',
  },
  STRATEGIES: {
    LIST: '/api/v1/strategies',
    CREATE: '/api/v1/strategies',
    DETAIL: (id: string) => `/api/v1/strategies/${id}`,
    UPDATE: (id: string) => `/api/v1/strategies/${id}`,
    DELETE: (id: string) => `/api/v1/strategies/${id}`,
    BACKTEST: (id: string) => `/api/v1/strategies/${id}/backtest`,
    START: (id: string) => `/api/v1/strategies/${id}/start`,
    STOP: (id: string) => `/api/v1/strategies/${id}/stop`,
  },
  DATASETS: {
    LIST: '/api/v1/data',
    CREATE: '/api/v1/data',
    DETAIL: (id: string) => `/api/v1/data/${id}`,
    UPDATE: (id: string) => `/api/v1/data/${id}`,
    DELETE: (id: string) => `/api/v1/data/${id}`,
    UPLOAD: '/api/v1/data/upload',
  },
  TRAINING: {
    LIST: '/api/v1/training',
    CREATE: '/api/v1/training',
    DETAIL: (id: string) => `/api/v1/training/${id}`,
    START: (id: string) => `/api/v1/training/${id}/start`,
    STOP: (id: string) => `/api/v1/training/${id}/stop`,
    LOGS: (id: string) => `/api/v1/training/${id}/logs`,
  },
} as const

// App configuration
export const APP_CONFIG = {
  TITLE: 'TradeMaster',
  VERSION: '1.0.0',
  DESCRIPTION: '专业的量化交易平台',
  AUTHOR: 'TradeMaster Team',
  COPYRIGHT: `© ${new Date().getFullYear()} TradeMaster. All rights reserved.`,
} as const

// Theme configuration
export const THEME_CONFIG = {
  PRIMARY_COLOR: '#1890ff',
  SUCCESS_COLOR: '#52c41a',
  WARNING_COLOR: '#faad14',
  ERROR_COLOR: '#f5222d',
  INFO_COLOR: '#1890ff',
  BORDER_RADIUS: 6,
  LAYOUT_HEADER_HEIGHT: 64,
  LAYOUT_SIDER_WIDTH: 256,
  LAYOUT_SIDER_COLLAPSED_WIDTH: 80,
} as const

// Storage keys
export const STORAGE_KEYS = {
  TOKEN: 'trademaster_token',
  REFRESH_TOKEN: 'trademaster_refresh_token',
  USER: 'trademaster_user',
  THEME: 'trademaster_theme',
  LANGUAGE: 'trademaster_language',
  SIDEBAR_COLLAPSED: 'trademaster_sidebar_collapsed',
} as const

// Strategy types
export const STRATEGY_TYPES = [
  {
    key: 'algorithmic_trading',
    label: '算法交易',
    description: '基于算法的自动化交易策略',
    icon: 'robot',
  },
  {
    key: 'portfolio_management',
    label: '投资组合管理',
    description: '多资产投资组合优化与管理',
    icon: 'pie-chart',
  },
  {
    key: 'order_execution',
    label: '订单执行',
    description: '智能订单执行与分割策略',
    icon: 'transaction',
  },
  {
    key: 'high_frequency_trading',
    label: '高频交易',
    description: '高频量化交易策略',
    icon: 'dashboard',
  },
] as const

// Strategy status
export const STRATEGY_STATUS = {
  DRAFT: { key: 'draft', label: '草稿', color: 'default' },
  ACTIVE: { key: 'active', label: '运行中', color: 'processing' },
  PAUSED: { key: 'paused', label: '已暂停', color: 'warning' },
  STOPPED: { key: 'stopped', label: '已停止', color: 'error' },
} as const

// Training status
export const TRAINING_STATUS = {
  PENDING: { key: 'pending', label: '等待中', color: 'default' },
  RUNNING: { key: 'running', label: '训练中', color: 'processing' },
  COMPLETED: { key: 'completed', label: '已完成', color: 'success' },
  FAILED: { key: 'failed', label: '失败', color: 'error' },
  CANCELLED: { key: 'cancelled', label: '已取消', color: 'default' },
} as const

// Dataset types
export const DATASET_TYPES = [
  { key: 'market_data', label: '市场数据', icon: 'line-chart' },
  { key: 'financial_data', label: '财务数据', icon: 'bar-chart' },
  { key: 'custom', label: '自定义数据', icon: 'database' },
] as const

// Dataset formats
export const DATASET_FORMATS = [
  { key: 'csv', label: 'CSV', extension: '.csv' },
  { key: 'json', label: 'JSON', extension: '.json' },
  { key: 'parquet', label: 'Parquet', extension: '.parquet' },
] as const

// Page sizes
export const PAGE_SIZES = [10, 20, 50, 100] as const
export const DEFAULT_PAGE_SIZE = 20

// Chart colors
export const CHART_COLORS = [
  '#1890ff',
  '#52c41a',
  '#faad14',
  '#f5222d',
  '#722ed1',
  '#fa8c16',
  '#a0d911',
  '#13c2c2',
  '#eb2f96',
  '#fa541c',
] as const

// Date formats
export const DATE_FORMATS = {
  DATE: 'YYYY-MM-DD',
  DATETIME: 'YYYY-MM-DD HH:mm:ss',
  TIME: 'HH:mm:ss',
  MONTH: 'YYYY-MM',
  YEAR: 'YYYY',
} as const

// HTTP status codes
export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  NO_CONTENT: 204,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  INTERNAL_SERVER_ERROR: 500,
} as const

// Error messages
export const ERROR_MESSAGES = {
  NETWORK_ERROR: '网络错误，请检查您的网络连接',
  UNAUTHORIZED: '登录已过期，请重新登录',
  FORBIDDEN: '没有权限执行此操作',
  NOT_FOUND: '请求的资源不存在',
  SERVER_ERROR: '服务器错误，请稍后重试',
  VALIDATION_ERROR: '数据验证失败',
  UNKNOWN_ERROR: '未知错误',
} as const

// Success messages
export const SUCCESS_MESSAGES = {
  LOGIN_SUCCESS: '登录成功',
  LOGOUT_SUCCESS: '退出成功',
  CREATE_SUCCESS: '创建成功',
  UPDATE_SUCCESS: '更新成功',
  DELETE_SUCCESS: '删除成功',
  UPLOAD_SUCCESS: '上传成功',
  OPERATION_SUCCESS: '操作成功',
} as const

// Routes
export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  REGISTER: '/register',
  FORGOT_PASSWORD: '/forgot-password',
  RESET_PASSWORD: '/reset-password',
  DASHBOARD: '/dashboard',
  STRATEGIES: '/strategies',
  STRATEGY_CREATE: '/strategies/create',
  STRATEGY_DETAIL: '/strategies/:id',
  DATASETS: '/datasets',
  DATASET_CREATE: '/datasets/create',
  DATASET_DETAIL: '/datasets/:id',
  TRAINING: '/training',
  TRAINING_CREATE: '/training/create',
  TRAINING_DETAIL: '/training/:id',
  ANALYSIS: '/analysis',
  PROFILE: '/profile',
  SETTINGS: '/settings',
} as const