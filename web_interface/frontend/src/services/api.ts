import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios'
import { message } from 'antd'

import { token, storage } from '@/utils'
import { HTTP_STATUS, ERROR_MESSAGES, STORAGE_KEYS, API_ENDPOINTS } from '@/constants'

// API configuration
const API_CONFIG = {
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 30000,
  withCredentials: false,
}

// Create axios instance
const api: AxiosInstance = axios.create(API_CONFIG)

// Flag to prevent multiple token refresh requests
let isRefreshing = false
let failedQueue: Array<{
  resolve: (value?: any) => void
  reject: (reason?: any) => void
}> = []

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error)
    } else {
      resolve(token)
    }
  })
  
  failedQueue = []
}

// Request interceptor
api.interceptors.request.use(
  (config: AxiosRequestConfig) => {
    // Add authorization header
    const authToken = token.get()
    if (authToken && config.headers) {
      config.headers.Authorization = `Bearer ${authToken}`
    }

    // Add timestamp to prevent caching for GET requests
    if (config.method === 'get') {
      config.params = {
        ...config.params,
        _t: Date.now(),
      }
    }

    // Log request in development
    if (import.meta.env.DEV) {
      console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`, {
        params: config.params,
        data: config.data,
      })
    }

    return config
  },
  (error: AxiosError) => {
    console.error('[API Request Error]', error)
    return Promise.reject(error)
  },
)

// Response interceptor with token refresh logic
api.interceptors.response.use(
  (response: AxiosResponse) => {
    // Log response in development
    if (import.meta.env.DEV) {
      console.log(`[API Response] ${response.config.method?.toUpperCase()} ${response.config.url}`, response.data)
    }

    return response
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean }

    // Log error in development
    if (import.meta.env.DEV) {
      console.error('[API Response Error]', error)
    }

    // Handle token refresh for 401 errors
    if (error.response?.status === HTTP_STATUS.UNAUTHORIZED && !originalRequest._retry) {
      if (isRefreshing) {
        // If already refreshing, queue this request
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then(token => {
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${token}`
          }
          return api(originalRequest)
        }).catch(err => {
          return Promise.reject(err)
        })
      }

      originalRequest._retry = true
      isRefreshing = true

      const refreshToken = token.getRefresh()
      
      if (refreshToken && !originalRequest.url?.includes('/auth/refresh')) {
        try {
          const response = await api.post(API_ENDPOINTS.AUTH.REFRESH, {
            refresh_token: refreshToken
          })
          
          const { access_token, refresh_token: newRefreshToken } = response.data
          
          // Update tokens
          token.set(access_token)
          token.setRefresh(newRefreshToken)
          
          // Process queued requests
          processQueue(null, access_token)
          
          // Retry original request
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${access_token}`
          }
          
          return api(originalRequest)
        } catch (refreshError) {
          processQueue(refreshError, null)
          
          // Clear tokens and redirect to login
          token.clear()
          storage.remove(STORAGE_KEYS.USER)
          
          if (window.location.pathname !== '/login') {
            window.location.href = '/login'
          }
          
          return Promise.reject(refreshError)
        } finally {
          isRefreshing = false
        }
      } else {
        // No refresh token or refresh request failed
        token.clear()
        storage.remove(STORAGE_KEYS.USER)
        
        if (window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
      }
    }

    // Handle other error cases
    if (error.response) {
      const { status, data } = error.response
      let errorMessage: string

      // Extract error message from FastAPI response format
      if (typeof data === 'object' && data.detail) {
        if (typeof data.detail === 'string') {
          errorMessage = data.detail
        } else if (typeof data.detail === 'object' && data.detail.message) {
          errorMessage = data.detail.message
        } else {
          errorMessage = JSON.stringify(data.detail)
        }
      } else if (data && data.message) {
        errorMessage = data.message
      } else {
        // Default error messages based on status codes
        switch (status) {
          case HTTP_STATUS.BAD_REQUEST:
            errorMessage = ERROR_MESSAGES.VALIDATION_ERROR
            break
          case HTTP_STATUS.UNAUTHORIZED:
            errorMessage = ERROR_MESSAGES.UNAUTHORIZED
            break
          case HTTP_STATUS.FORBIDDEN:
            errorMessage = ERROR_MESSAGES.FORBIDDEN
            break
          case HTTP_STATUS.NOT_FOUND:
            errorMessage = ERROR_MESSAGES.NOT_FOUND
            break
          case HTTP_STATUS.INTERNAL_SERVER_ERROR:
            errorMessage = ERROR_MESSAGES.SERVER_ERROR
            break
          default:
            errorMessage = ERROR_MESSAGES.UNKNOWN_ERROR
        }
      }

      // Don't show error message for auth endpoints to avoid double messages
      if (!originalRequest.url?.includes('/auth/')) {
        message.error(errorMessage)
      }

      return Promise.reject(error)
    }

    // Network error
    if (error.code === 'NETWORK_ERROR' || !error.response) {
      message.error(ERROR_MESSAGES.NETWORK_ERROR)
      return Promise.reject(error)
    }

    return Promise.reject(error)
  },
)

// API methods
export const apiClient = {
  // GET request
  get: <T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> => {
    return api.get(url, config)
  },

  // POST request
  post: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> => {
    return api.post(url, data, config)
  },

  // PUT request
  put: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> => {
    return api.put(url, data, config)
  },

  // PATCH request
  patch: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> => {
    return api.patch(url, data, config)
  },

  // DELETE request
  delete: <T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> => {
    return api.delete(url, config)
  },

  // Upload file
  upload: <T = any>(
    url: string,
    file: File,
    config?: AxiosRequestConfig & {
      onProgress?: (progressEvent: ProgressEvent) => void
    },
  ): Promise<AxiosResponse<T>> => {
    const formData = new FormData()
    formData.append('file', file)

    return api.post(url, formData, {
      ...config,
      headers: {
        'Content-Type': 'multipart/form-data',
        ...config?.headers,
      },
      onUploadProgress: config?.onProgress,
    })
  },

  // Download file
  download: (url: string, filename?: string, config?: AxiosRequestConfig): Promise<void> => {
    return api
      .get(url, {
        ...config,
        responseType: 'blob',
      })
      .then(response => {
        const blob = new Blob([response.data])
        const downloadUrl = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = downloadUrl
        link.download = filename || 'download'
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(downloadUrl)
      })
  },
}

// Export axios instance for advanced usage
export { api }
export default apiClient