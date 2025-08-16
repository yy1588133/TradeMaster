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
    const response = await apiClient.post<LoginResponse>(API_ENDPOINTS.AUTH.LOGIN, credentials)
    return response.data
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