import { apiClient } from './api'
import { API_ENDPOINTS } from '@/constants'
import {
  User,
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  TokenResponse,
  ChangePasswordRequest,
  PasswordResetRequest,
  PasswordResetConfirm
} from '@/types'

export const authService = {
  // User login
  login: async (credentials: LoginRequest): Promise<LoginResponse> => {
    try {
      const response = await apiClient.post<LoginResponse>(API_ENDPOINTS.AUTH.LOGIN, credentials)
      
      // Validate response data structure
      if (!response.data) {
        throw new Error('无效的响应数据')
      }
      
      const { user, tokens } = response.data
      if (!user || !tokens) {
        throw new Error('响应数据格式错误：缺少用户信息或令牌')
      }
      
      if (!tokens.access_token || !tokens.refresh_token) {
        throw new Error('响应数据格式错误：缺少访问令牌或刷新令牌')
      }
      
      return response.data
    } catch (error: any) {
      // Enhanced error handling
      if (error.response) {
        // Server responded with error status
        const status = error.response.status
        const data = error.response.data
        
        if (status === 404) {
          throw new Error('登录接口不存在，请检查服务器配置')
        } else if (status === 401) {
          throw new Error(data?.detail || '用户名或密码错误')
        } else if (status >= 500) {
          throw new Error('服务器错误，请稍后重试')
        }
      } else if (error.request) {
        // Network error
        throw new Error('网络连接失败，请检查网络连接')
      }
      
      // Re-throw the error with original message if it's a validation error
      throw error
    }
  },

  // User logout
  logout: async (allDevices: boolean = false): Promise<void> => {
    await apiClient.post(API_ENDPOINTS.AUTH.LOGOUT, { all_devices: allDevices })
  },

  // User registration
  register: async (userData: RegisterRequest): Promise<User> => {
    const response = await apiClient.post<User>(API_ENDPOINTS.AUTH.REGISTER, userData)
    return response.data
  },

  // Refresh token
  refreshToken: async (refreshToken: string): Promise<TokenResponse> => {
    const response = await apiClient.post<TokenResponse>(API_ENDPOINTS.AUTH.REFRESH, {
      refresh_token: refreshToken,
    })
    return response.data
  },

  // Get user profile
  getProfile: async (): Promise<User> => {
    const response = await apiClient.get<User>(API_ENDPOINTS.AUTH.PROFILE)
    return response.data
  },

  // Update user profile
  updateProfile: async (userData: Partial<User>): Promise<User> => {
    const response = await apiClient.put<User>(API_ENDPOINTS.AUTH.PROFILE, userData)
    return response.data
  },

  // Change password
  changePassword: async (data: ChangePasswordRequest): Promise<void> => {
    await apiClient.post(API_ENDPOINTS.AUTH.CHANGE_PASSWORD, {
      current_password: data.current_password,
      new_password: data.new_password,
    })
  },

  // Forgot password
  forgotPassword: async (data: PasswordResetRequest): Promise<void> => {
    await apiClient.post(API_ENDPOINTS.AUTH.FORGOT_PASSWORD, data)
  },

  // Reset password
  resetPassword: async (data: PasswordResetConfirm): Promise<void> => {
    await apiClient.post(API_ENDPOINTS.AUTH.RESET_PASSWORD, {
      token: data.token,
      new_password: data.new_password,
    })
  },

  // Verify token
  verifyToken: async (token: string): Promise<{
    valid: boolean
    user_id?: string
    username?: string
    role?: string
    expires_at?: number
    error?: string
  }> => {
    const response = await apiClient.post(API_ENDPOINTS.AUTH.VERIFY_TOKEN, { token })
    return response.data
  },

  // Upload avatar
  uploadAvatar: async (file: File): Promise<{ avatar_url: string }> => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await apiClient.post<{ avatar_url: string }>('/api/v1/auth/avatar', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },
}

export default authService