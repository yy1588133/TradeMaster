import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'

import { authService } from '@/services'
import { User, LoginRequest, RegisterRequest } from '@/types'
import { token, storage } from '@/utils'
import { STORAGE_KEYS } from '@/constants'

// Async thunks
export const loginAsync = createAsyncThunk(
  'auth/login',
  async (credentials: LoginRequest, { rejectWithValue }) => {
    try {
      const response = await authService.login(credentials)
      
      // Store tokens
      token.set(response.tokens.access_token)
      token.setRefresh(response.tokens.refresh_token)
      
      // Store user info
      storage.set(STORAGE_KEYS.USER, response.user)
      
      return response
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || error.message || '登录失败')
    }
  }
)

export const logoutAsync = createAsyncThunk(
  'auth/logout',
  async (allDevices: boolean = false, { rejectWithValue }) => {
    try {
      await authService.logout(allDevices)
    } catch (error: any) {
      console.warn('Logout API failed:', error.message)
    } finally {
      // Always clear local storage
      token.clear()
      storage.remove(STORAGE_KEYS.USER)
    }
  }
)

export const registerAsync = createAsyncThunk(
  'auth/register',
  async (userData: RegisterRequest, { rejectWithValue }) => {
    try {
      const user = await authService.register(userData)
      return user
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || error.message || '注册失败')
    }
  }
)

export const refreshTokenAsync = createAsyncThunk(
  'auth/refreshToken',
  async (_, { rejectWithValue }) => {
    try {
      const refreshToken = token.getRefresh()
      if (!refreshToken) {
        throw new Error('No refresh token available')
      }
      
      const response = await authService.refreshToken(refreshToken)
      
      // Update tokens
      token.set(response.access_token)
      token.setRefresh(response.refresh_token)
      
      return response
    } catch (error: any) {
      // Clear tokens on refresh failure
      token.clear()
      storage.remove(STORAGE_KEYS.USER)
      return rejectWithValue(error.response?.data?.detail || error.message || 'Token refresh failed')
    }
  }
)

export const getProfileAsync = createAsyncThunk(
  'auth/getProfile',
  async (_, { rejectWithValue }) => {
    try {
      const user = await authService.getProfile()
      storage.set(STORAGE_KEYS.USER, user)
      return user
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || error.message || '获取用户信息失败')
    }
  }
)

export const updateProfileAsync = createAsyncThunk(
  'auth/updateProfile',
  async (userData: Partial<User>, { rejectWithValue }) => {
    try {
      const user = await authService.updateProfile(userData)
      storage.set(STORAGE_KEYS.USER, user)
      return user
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || error.message || '更新用户信息失败')
    }
  }
)

export const changePasswordAsync = createAsyncThunk(
  'auth/changePassword',
  async (passwordData: { current_password: string; new_password: string }, { rejectWithValue }) => {
    try {
      await authService.changePassword(passwordData)
      return { success: true }
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || error.message || '密码修改失败')
    }
  }
)

// Auth state interface
interface AuthState {
  user: User | null
  token: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  loading: boolean
  error: string | null
  passwordLoading: boolean
}

// Initial state
const initialState: AuthState = {
  user: storage.get(STORAGE_KEYS.USER, null),
  token: token.get(),
  refreshToken: token.getRefresh(),
  isAuthenticated: !!token.get(),
  loading: false,
  error: null,
  passwordLoading: false,
}

// Auth slice
const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    clearError: state => {
      state.error = null
    },
    
    clearAuth: state => {
      state.user = null
      state.token = null
      state.refreshToken = null
      state.isAuthenticated = false
      state.error = null
      
      // Clear storage
      token.clear()
      storage.remove(STORAGE_KEYS.USER)
    },
    
    setUser: (state, action: PayloadAction<User>) => {
      state.user = action.payload
      storage.set(STORAGE_KEYS.USER, action.payload)
    },
    
    setTokens: (state, action: PayloadAction<{ access_token: string; refresh_token: string }>) => {
      state.token = action.payload.access_token
      state.refreshToken = action.payload.refresh_token
      state.isAuthenticated = true
      
      // Store tokens
      token.set(action.payload.access_token)
      token.setRefresh(action.payload.refresh_token)
    },
  },
  extraReducers: builder => {
    // Login
    builder
      .addCase(loginAsync.pending, state => {
        state.loading = true
        state.error = null
      })
      .addCase(loginAsync.fulfilled, (state, action) => {
        state.loading = false
        state.user = action.payload.user
        state.token = action.payload.tokens.access_token
        state.refreshToken = action.payload.tokens.refresh_token
        state.isAuthenticated = true
        state.error = null
      })
      .addCase(loginAsync.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload as string
        state.isAuthenticated = false
      })

    // Logout
    builder
      .addCase(logoutAsync.pending, state => {
        state.loading = true
      })
      .addCase(logoutAsync.fulfilled, state => {
        state.loading = false
        state.user = null
        state.token = null
        state.refreshToken = null
        state.isAuthenticated = false
        state.error = null
      })

    // Register
    builder
      .addCase(registerAsync.pending, state => {
        state.loading = true
        state.error = null
      })
      .addCase(registerAsync.fulfilled, state => {
        state.loading = false
        state.error = null
      })
      .addCase(registerAsync.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload as string
      })

    // Refresh token
    builder
      .addCase(refreshTokenAsync.fulfilled, (state, action) => {
        state.token = action.payload.access_token
        state.refreshToken = action.payload.refresh_token
        state.isAuthenticated = true
      })
      .addCase(refreshTokenAsync.rejected, state => {
        state.user = null
        state.token = null
        state.refreshToken = null
        state.isAuthenticated = false
      })

    // Get profile
    builder
      .addCase(getProfileAsync.pending, state => {
        state.loading = true
      })
      .addCase(getProfileAsync.fulfilled, (state, action) => {
        state.loading = false
        state.user = action.payload
      })
      .addCase(getProfileAsync.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload as string
      })

    // Update profile
    builder
      .addCase(updateProfileAsync.pending, state => {
        state.loading = true
      })
      .addCase(updateProfileAsync.fulfilled, (state, action) => {
        state.loading = false
        state.user = action.payload
      })
      .addCase(updateProfileAsync.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload as string
      })

    // Change password
    builder
      .addCase(changePasswordAsync.pending, state => {
        state.passwordLoading = true
        state.error = null
      })
      .addCase(changePasswordAsync.fulfilled, state => {
        state.passwordLoading = false
        state.error = null
      })
      .addCase(changePasswordAsync.rejected, (state, action) => {
        state.passwordLoading = false
        state.error = action.payload as string
      })
  },
})

export const { clearError, clearAuth, setUser, setTokens } = authSlice.actions
export default authSlice.reducer