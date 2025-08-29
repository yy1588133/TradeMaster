import { apiClient } from './api'
import { API_ENDPOINTS } from '@/constants'
import { Strategy, CreateStrategyRequest, PaginationParams, PaginationResponse } from '@/types'

export const strategyService = {
  // Get strategy list
  getStrategies: async (params?: PaginationParams & {
    type?: string
    strategy_status?: string
    search?: string
  }): Promise<PaginationResponse<Strategy>> => {
    // 过滤空字符串参数
    const cleanParams = params ? Object.fromEntries(
      Object.entries(params).filter(([_, value]) => value !== '' && value !== null && value !== undefined)
    ) : {}
    
    const response = await apiClient.get<PaginationResponse<Strategy>>(
      API_ENDPOINTS.STRATEGIES.LIST,
      { params: cleanParams }
    )
    return response.data
  },

  // Get strategy by ID
  getStrategy: async (id: string): Promise<Strategy> => {
    const response = await apiClient.get<Strategy>(API_ENDPOINTS.STRATEGIES.DETAIL(id))
    return response.data
  },

  // Create strategy
  createStrategy: async (data: CreateStrategyRequest): Promise<Strategy> => {
    const response = await apiClient.post<Strategy>(API_ENDPOINTS.STRATEGIES.CREATE, data)
    return response.data
  },

  // Update strategy
  updateStrategy: async (id: string, data: Partial<CreateStrategyRequest>): Promise<Strategy> => {
    const response = await apiClient.put<Strategy>(API_ENDPOINTS.STRATEGIES.UPDATE(id), data)
    return response.data
  },

  // Delete strategy
  deleteStrategy: async (id: string): Promise<void> => {
    await apiClient.delete(API_ENDPOINTS.STRATEGIES.DELETE(id))
  },

  // Start strategy
  startStrategy: async (id: string): Promise<void> => {
    await apiClient.post(API_ENDPOINTS.STRATEGIES.START(id))
  },

  // Stop strategy
  stopStrategy: async (id: string): Promise<void> => {
    await apiClient.post(API_ENDPOINTS.STRATEGIES.STOP(id))
  },

  // Run backtest
  runBacktest: async (id: string, config?: {
    startDate?: string
    endDate?: string
    initialCash?: number
    [key: string]: any
  }): Promise<{
    taskId: string
    status: string
  }> => {
    const response = await apiClient.post<{
      taskId: string
      status: string
    }>(API_ENDPOINTS.STRATEGIES.BACKTEST(id), config)
    return response.data
  },

  // Get backtest results
  getBacktestResults: async (id: string, taskId: string): Promise<{
    status: string
    progress: number
    results?: {
      totalReturn: number
      annualizedReturn: number
      sharpeRatio: number
      maxDrawdown: number
      winRate: number
      profitFactor: number
      trades: Array<{
        timestamp: string
        action: 'buy' | 'sell'
        price: number
        quantity: number
        profit?: number
      }>
      equity: Array<{
        timestamp: string
        value: number
      }>
    }
  }> => {
    const response = await apiClient.get(`${API_ENDPOINTS.STRATEGIES.BACKTEST(id)}/${taskId}`)
    return response.data
  },

  // Get strategy performance
  getPerformance: async (id: string, timeRange?: '1d' | '7d' | '30d' | '90d' | '1y'): Promise<{
    totalReturn: number
    annualizedReturn: number
    sharpeRatio: number
    maxDrawdown: number
    winRate: number
    profitFactor: number
    equity: Array<{
      timestamp: string
      value: number
    }>
    trades: Array<{
      timestamp: string
      action: 'buy' | 'sell'
      symbol: string
      price: number
      quantity: number
      profit?: number
    }>
  }> => {
    const response = await apiClient.get(`${API_ENDPOINTS.STRATEGIES.DETAIL(id)}/performance`, {
      params: { timeRange }
    })
    return response.data
  },

  // Clone strategy
  cloneStrategy: async (id: string, name: string): Promise<Strategy> => {
    const response = await apiClient.post<Strategy>(`${API_ENDPOINTS.STRATEGIES.DETAIL(id)}/clone`, {
      name
    })
    return response.data
  },

  // Export strategy configuration
  exportStrategy: async (id: string): Promise<void> => {
    await apiClient.download(`${API_ENDPOINTS.STRATEGIES.DETAIL(id)}/export`, `strategy_${id}.json`)
  },

  // Import strategy configuration
  importStrategy: async (file: File): Promise<Strategy> => {
    const response = await apiClient.upload<Strategy>(`${API_ENDPOINTS.STRATEGIES.LIST}/import`, file)
    return response.data
  },
}

export default strategyService