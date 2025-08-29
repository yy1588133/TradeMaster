import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'

import { strategyService } from '@/services'
import { Strategy, CreateStrategyRequest, PaginationParams, PaginationResponse } from '@/types'

// Async thunks
export const getStrategiesAsync = createAsyncThunk(
  'strategy/getStrategies',
  async (params?: PaginationParams & {
    type?: string
    strategy_status?: string
    search?: string
  }, { rejectWithValue }) => {
    try {
      const response = await strategyService.getStrategies(params)
      return response
    } catch (error: any) {
      return rejectWithValue(error.message || '获取策略列表失败')
    }
  }
)

export const fetchStrategiesAsync = createAsyncThunk(
  'strategy/fetchStrategies',
  async (params?: PaginationParams & {
    type?: string
    strategy_status?: string
    search?: string
  }, { rejectWithValue }) => {
    try {
      const response = await strategyService.getStrategies(params)
      return response
    } catch (error: any) {
      return rejectWithValue(error.message || '获取策略列表失败')
    }
  }
)

export const getStrategyAsync = createAsyncThunk(
  'strategy/getStrategy',
  async (id: string, { rejectWithValue }) => {
    try {
      const strategy = await strategyService.getStrategy(id)
      return strategy
    } catch (error: any) {
      return rejectWithValue(error.message || '获取策略详情失败')
    }
  }
)

export const fetchStrategyAsync = createAsyncThunk(
  'strategy/fetchStrategy',
  async (id: string, { rejectWithValue }) => {
    try {
      const strategy = await strategyService.getStrategy(id)
      return strategy
    } catch (error: any) {
      return rejectWithValue(error.message || '获取策略详情失败')
    }
  }
)

export const createStrategyAsync = createAsyncThunk(
  'strategy/createStrategy',
  async (data: CreateStrategyRequest, { rejectWithValue }) => {
    try {
      const strategy = await strategyService.createStrategy(data)
      return strategy
    } catch (error: any) {
      return rejectWithValue(error.message || '创建策略失败')
    }
  }
)

export const updateStrategyAsync = createAsyncThunk(
  'strategy/updateStrategy',
  async ({ id, data }: { id: string; data: Partial<CreateStrategyRequest> }, { rejectWithValue }) => {
    try {
      const strategy = await strategyService.updateStrategy(id, data)
      return strategy
    } catch (error: any) {
      return rejectWithValue(error.message || '更新策略失败')
    }
  }
)

export const deleteStrategyAsync = createAsyncThunk(
  'strategy/deleteStrategy',
  async (id: string, { rejectWithValue }) => {
    try {
      await strategyService.deleteStrategy(id)
      return id
    } catch (error: any) {
      return rejectWithValue(error.message || '删除策略失败')
    }
  }
)

export const startStrategyAsync = createAsyncThunk(
  'strategy/startStrategy',
  async (id: string, { rejectWithValue }) => {
    try {
      await strategyService.startStrategy(id)
      return id
    } catch (error: any) {
      return rejectWithValue(error.message || '启动策略失败')
    }
  }
)

export const stopStrategyAsync = createAsyncThunk(
  'strategy/stopStrategy',
  async (id: string, { rejectWithValue }) => {
    try {
      await strategyService.stopStrategy(id)
      return id
    } catch (error: any) {
      return rejectWithValue(error.message || '停止策略失败')
    }
  }
)

export const runBacktestAsync = createAsyncThunk(
  'strategy/runBacktest',
  async ({ id, config }: { 
    id: string 
    config?: {
      startDate?: string
      endDate?: string
      initialCash?: number
      [key: string]: any
    }
  }, { rejectWithValue }) => {
    try {
      const result = await strategyService.runBacktest(id, config)
      return { strategyId: id, ...result }
    } catch (error: any) {
      return rejectWithValue(error.message || '运行回测失败')
    }
  }
)

export const getBacktestResultsAsync = createAsyncThunk(
  'strategy/getBacktestResults',
  async ({ id, taskId }: { id: string; taskId: string }, { rejectWithValue }) => {
    try {
      const results = await strategyService.getBacktestResults(id, taskId)
      return { strategyId: id, taskId, ...results }
    } catch (error: any) {
      return rejectWithValue(error.message || '获取回测结果失败')
    }
  }
)

// Strategy state interface
interface StrategyState {
  strategies: Strategy[]
  currentStrategy: Strategy | null
  pagination: {
    total: number
    page: number
    pageSize: number
    totalPages: number
  }
  loading: boolean
  error: string | null
  backtestTasks: Record<string, {
    strategyId: string
    taskId: string
    status: string
    progress: number
    results?: any
  }>
}

// Initial state
const initialState: StrategyState = {
  strategies: [],
  currentStrategy: null,
  pagination: {
    total: 0,
    page: 1,
    pageSize: 20,
    totalPages: 0,
  },
  loading: false,
  error: null,
  backtestTasks: {},
}

// Strategy slice
const strategySlice = createSlice({
  name: 'strategy',
  initialState,
  reducers: {
    clearError: state => {
      state.error = null
    },
    
    setCurrentStrategy: (state, action: PayloadAction<Strategy | null>) => {
      state.currentStrategy = action.payload
    },
    
    updateStrategyStatus: (state, action: PayloadAction<{ id: string; status: Strategy['status'] }>) => {
      const strategy = state.strategies.find(s => s.id === action.payload.id)
      if (strategy) {
        strategy.status = action.payload.status
      }
      
      if (state.currentStrategy?.id === action.payload.id) {
        state.currentStrategy.status = action.payload.status
      }
    },
    
    removeBacktestTask: (state, action: PayloadAction<string>) => {
      delete state.backtestTasks[action.payload]
    },
  },
  extraReducers: builder => {
    // Get strategies (new)
    builder
      .addCase(getStrategiesAsync.pending, state => {
        state.loading = true
        state.error = null
      })
      .addCase(getStrategiesAsync.fulfilled, (state, action) => {
        state.loading = false
        state.strategies = action.payload.list
        state.pagination = {
          total: action.payload.total,
          page: action.payload.page,
          pageSize: action.payload.pageSize,
          totalPages: action.payload.totalPages,
        }
      })
      .addCase(getStrategiesAsync.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload as string
      })

    // Fetch strategies (legacy)
    builder
      .addCase(fetchStrategiesAsync.pending, state => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchStrategiesAsync.fulfilled, (state, action) => {
        state.loading = false
        state.strategies = action.payload.list
        state.pagination = {
          total: action.payload.total,
          page: action.payload.page,
          pageSize: action.payload.pageSize,
          totalPages: action.payload.totalPages,
        }
      })
      .addCase(fetchStrategiesAsync.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload as string
      })

    // Get strategy (new)
    builder
      .addCase(getStrategyAsync.pending, state => {
        state.loading = true
        state.error = null
      })
      .addCase(getStrategyAsync.fulfilled, (state, action) => {
        state.loading = false
        state.currentStrategy = action.payload
      })
      .addCase(getStrategyAsync.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload as string
      })

    // Fetch strategy (legacy)
    builder
      .addCase(fetchStrategyAsync.pending, state => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchStrategyAsync.fulfilled, (state, action) => {
        state.loading = false
        state.currentStrategy = action.payload
      })
      .addCase(fetchStrategyAsync.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload as string
      })

    // Create strategy
    builder
      .addCase(createStrategyAsync.pending, state => {
        state.loading = true
        state.error = null
      })
      .addCase(createStrategyAsync.fulfilled, (state, action) => {
        state.loading = false
        state.strategies.unshift(action.payload)
        state.pagination.total += 1
      })
      .addCase(createStrategyAsync.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload as string
      })

    // Update strategy
    builder
      .addCase(updateStrategyAsync.pending, state => {
        state.loading = true
        state.error = null
      })
      .addCase(updateStrategyAsync.fulfilled, (state, action) => {
        state.loading = false
        const index = state.strategies.findIndex(s => s.id === action.payload.id)
        if (index !== -1) {
          state.strategies[index] = action.payload
        }
        if (state.currentStrategy?.id === action.payload.id) {
          state.currentStrategy = action.payload
        }
      })
      .addCase(updateStrategyAsync.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload as string
      })

    // Delete strategy
    builder
      .addCase(deleteStrategyAsync.pending, state => {
        state.loading = true
        state.error = null
      })
      .addCase(deleteStrategyAsync.fulfilled, (state, action) => {
        state.loading = false
        state.strategies = state.strategies.filter(s => s.id !== action.payload)
        state.pagination.total -= 1
        if (state.currentStrategy?.id === action.payload) {
          state.currentStrategy = null
        }
      })
      .addCase(deleteStrategyAsync.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload as string
      })

    // Start strategy
    builder
      .addCase(startStrategyAsync.fulfilled, (state, action) => {
        const strategy = state.strategies.find(s => s.id === action.payload)
        if (strategy) {
          strategy.status = 'active'
        }
        if (state.currentStrategy?.id === action.payload) {
          state.currentStrategy.status = 'active'
        }
      })

    // Stop strategy
    builder
      .addCase(stopStrategyAsync.fulfilled, (state, action) => {
        const strategy = state.strategies.find(s => s.id === action.payload)
        if (strategy) {
          strategy.status = 'stopped'
        }
        if (state.currentStrategy?.id === action.payload) {
          state.currentStrategy.status = 'stopped'
        }
      })

    // Run backtest
    builder
      .addCase(runBacktestAsync.fulfilled, (state, action) => {
        state.backtestTasks[action.payload.taskId] = {
          strategyId: action.payload.strategyId,
          taskId: action.payload.taskId,
          status: action.payload.status,
          progress: 0,
        }
      })

    // Get backtest results
    builder
      .addCase(getBacktestResultsAsync.fulfilled, (state, action) => {
        const task = state.backtestTasks[action.payload.taskId]
        if (task) {
          task.status = action.payload.status
          task.progress = action.payload.progress
          task.results = action.payload.results
        }
      })
  },
})

export const {
  clearError,
  setCurrentStrategy,
  updateStrategyStatus,
  removeBacktestTask,
} = strategySlice.actions

export default strategySlice.reducer