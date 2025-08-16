// Common types
export interface BaseResponse<T = any> {
  code: number
  message: string
  data: T
  success: boolean
  timestamp: number
}

export interface PaginationParams {
  page: number
  pageSize: number
}

export interface PaginationResponse<T> {
  list: T[]
  total: number
  page: number
  pageSize: number
  totalPages: number
}

// User types
export interface User {
  id: number
  uuid: string
  username: string
  email: string
  full_name?: string
  avatar_url?: string
  role: 'admin' | 'user' | 'viewer' | 'analyst'
  is_active: boolean
  is_verified: boolean
  created_at: string
  updated_at: string
  last_login_at?: string
  login_count: number
}

export interface LoginRequest {
  username: string
  password: string
  remember_me?: boolean
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
  full_name?: string
  agree_terms: boolean
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface LoginResponse {
  user: User
  tokens: TokenResponse
  message: string
}

export interface ChangePasswordRequest {
  current_password: string
  new_password: string
}

export interface PasswordResetRequest {
  email: string
}

export interface PasswordResetConfirm {
  token: string
  new_password: string
}

// Strategy types
export interface Strategy {
  id: string
  name: string
  description: string
  type: 'algorithmic_trading' | 'portfolio_management' | 'order_execution' | 'high_frequency_trading'
  status: 'draft' | 'active' | 'paused' | 'stopped'
  config: Record<string, any>
  performance?: StrategyPerformance
  createdAt: string
  updatedAt: string
  userId: string
}

export interface StrategyPerformance {
  totalReturn: number
  annualizedReturn: number
  sharpeRatio: number
  maxDrawdown: number
  winRate: number
  profitFactor: number
}

export interface CreateStrategyRequest {
  name: string
  description: string
  type: Strategy['type']
  config: Record<string, any>
}

// Dataset types
export interface Dataset {
  id: string
  name: string
  description: string
  type: 'market_data' | 'financial_data' | 'custom'
  format: 'csv' | 'json' | 'parquet'
  size: number
  columns: string[]
  rowCount: number
  createdAt: string
  updatedAt: string
}

// Training types
export interface TrainingJob {
  id: string
  name: string
  strategyId: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  progress: number
  config: TrainingConfig
  results?: TrainingResults
  createdAt: string
  updatedAt: string
  startedAt?: string
  completedAt?: string
}

export interface TrainingConfig {
  datasetId: string
  trainRatio: number
  validationRatio: number
  testRatio: number
  epochs: number
  batchSize: number
  learningRate: number
  optimizer: 'adam' | 'sgd' | 'rmsprop'
  [key: string]: any
}

export interface TrainingResults {
  trainLoss: number[]
  validationLoss: number[]
  metrics: Record<string, number>
  bestEpoch: number
  modelPath: string
}

// Chart types
export interface ChartData {
  timestamp: string
  value: number
  [key: string]: any
}

export interface TimeSeriesData {
  timestamps: string[]
  values: number[]
  label: string
}

// Theme types
export type ThemeMode = 'light' | 'dark'

// Route types
export interface RouteConfig {
  path: string
  component: React.ComponentType
  exact?: boolean
  title?: string
  icon?: string
  children?: RouteConfig[]
}