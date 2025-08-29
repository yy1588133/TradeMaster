import dayjs, { Dayjs } from 'dayjs'
import { message } from 'antd'

import { DATE_FORMATS, STORAGE_KEYS } from '@/constants'

// Storage utilities
export const storage = {
  get: <T = any>(key: string, defaultValue?: T): T => {
    try {
      const item = localStorage.getItem(key)
      return item ? JSON.parse(item) : defaultValue
    } catch {
      return defaultValue as T
    }
  },
  
  set: (key: string, value: any): void => {
    try {
      localStorage.setItem(key, JSON.stringify(value))
    } catch (error) {
      console.error('Storage set error:', error)
    }
  },
  
  remove: (key: string): void => {
    try {
      localStorage.removeItem(key)
    } catch (error) {
      console.error('Storage remove error:', error)
    }
  },
  
  clear: (): void => {
    try {
      localStorage.clear()
    } catch (error) {
      console.error('Storage clear error:', error)
    }
  },
}

// Token utilities
export const token = {
  get: (): string | null => storage.get(STORAGE_KEYS.TOKEN),
  set: (value: string): void => storage.set(STORAGE_KEYS.TOKEN, value),
  remove: (): void => storage.remove(STORAGE_KEYS.TOKEN),
  
  getRefresh: (): string | null => storage.get(STORAGE_KEYS.REFRESH_TOKEN),
  setRefresh: (value: string): void => storage.set(STORAGE_KEYS.REFRESH_TOKEN, value),
  removeRefresh: (): void => storage.remove(STORAGE_KEYS.REFRESH_TOKEN),
  
  clear: (): void => {
    token.remove()
    token.removeRefresh()
  },
}

// Format utilities
export const format = {
  date: (date: string | Date | Dayjs, formatStr: string = DATE_FORMATS.DATE): string => {
    return dayjs(date).format(formatStr)
  },
  
  datetime: (date: string | Date | Dayjs): string => {
    return dayjs(date).format(DATE_FORMATS.DATETIME)
  },
  
  time: (date: string | Date | Dayjs): string => {
    return dayjs(date).format(DATE_FORMATS.TIME)
  },
  
  number: (num: number, precision: number = 2): string => {
    return num.toFixed(precision)
  },
  
  percentage: (num: number, precision: number = 2): string => {
    return `${(num * 100).toFixed(precision)}%`
  },
  
  currency: (num: number, currency: string = 'USD', precision: number = 2): string => {
    return `${currency} ${num.toFixed(precision)}`
  },
  
  fileSize: (bytes: number): string => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`
  },
}

// Validation utilities
export const validate = {
  email: (email: string): boolean => {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return regex.test(email)
  },
  
  phone: (phone: string): boolean => {
    const regex = /^1[3-9]\d{9}$/
    return regex.test(phone)
  },
  
  password: (password: string): boolean => {
    // At least 8 characters, including uppercase, lowercase, and number
    if (password.length < 8) return false
    
    // Check for at least one lowercase letter
    if (!/[a-z]/.test(password)) return false
    
    // Check for at least one uppercase letter
    if (!/[A-Z]/.test(password)) return false
    
    // Check for at least one number
    if (!/\d/.test(password)) return false
    
    return true
  },
  
  url: (url: string): boolean => {
    try {
      new URL(url)
      return true
    } catch {
      return false
    }
  },
  
  required: (value: any): boolean => {
    if (typeof value === 'string') return value.trim().length > 0
    if (Array.isArray(value)) return value.length > 0
    return value !== null && value !== undefined
  },
}

// Utility functions
export const utils = {
  sleep: (ms: number): Promise<void> => {
    return new Promise(resolve => setTimeout(resolve, ms))
  },
  
  debounce: <T extends (...args: any[]) => any>(
    func: T,
    wait: number,
  ): T => {
    let timeout: NodeJS.Timeout
    return ((...args: any[]) => {
      clearTimeout(timeout)
      timeout = setTimeout(() => func.apply(this, args), wait)
    }) as T
  },
  
  throttle: <T extends (...args: any[]) => any>(
    func: T,
    limit: number,
  ): T => {
    let inThrottle: boolean
    return ((...args: any[]) => {
      if (!inThrottle) {
        func.apply(this, args)
        inThrottle = true
        setTimeout(() => (inThrottle = false), limit)
      }
    }) as T
  },
  
  generateId: (): string => {
    return Math.random().toString(36).substr(2, 9)
  },
  
  copyToClipboard: async (text: string): Promise<boolean> => {
    try {
      await navigator.clipboard.writeText(text)
      message.success('复制成功')
      return true
    } catch {
      // Fallback for older browsers
      const textArea = document.createElement('textarea')
      textArea.value = text
      document.body.appendChild(textArea)
      textArea.select()
      try {
        document.execCommand('copy')
        message.success('复制成功')
        return true
      } catch {
        message.error('复制失败')
        return false
      } finally {
        document.body.removeChild(textArea)
      }
    }
  },
  
  downloadFile: (url: string, filename?: string): void => {
    const link = document.createElement('a')
    link.href = url
    if (filename) link.download = filename
    link.target = '_blank'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  },
  
  getQueryParams: (search: string = window.location.search): Record<string, string> => {
    const params = new URLSearchParams(search)
    const result: Record<string, string> = {}
    params.forEach((value, key) => {
      result[key] = value
    })
    return result
  },
  
  setQueryParams: (params: Record<string, any>): string => {
    const searchParams = new URLSearchParams()
    Object.keys(params).forEach(key => {
      if (params[key] !== undefined && params[key] !== null && params[key] !== '') {
        searchParams.set(key, String(params[key]))
      }
    })
    return searchParams.toString()
  },
}

// Array utilities
export const array = {
  chunk: <T>(arr: T[], size: number): T[][] => {
    const chunks: T[][] = []
    for (let i = 0; i < arr.length; i += size) {
      chunks.push(arr.slice(i, i + size))
    }
    return chunks
  },
  
  unique: <T>(arr: T[], key?: keyof T): T[] => {
    if (!key) return [...new Set(arr)]
    const seen = new Set()
    return arr.filter(item => {
      const value = item[key]
      if (seen.has(value)) return false
      seen.add(value)
      return true
    })
  },
  
  groupBy: <T>(arr: T[], key: keyof T): Record<string, T[]> => {
    return arr.reduce((groups, item) => {
      const group = String(item[key])
      groups[group] = groups[group] || []
      groups[group].push(item)
      return groups
    }, {} as Record<string, T[]>)
  },
  
  sortBy: <T>(arr: T[], key: keyof T, order: 'asc' | 'desc' = 'asc'): T[] => {
    return [...arr].sort((a, b) => {
      if (a[key] < b[key]) return order === 'asc' ? -1 : 1
      if (a[key] > b[key]) return order === 'asc' ? 1 : -1
      return 0
    })
  },
}

// Color utilities
export const color = {
  hexToRgb: (hex: string): { r: number; g: number; b: number } | null => {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
    return result
      ? {
          r: parseInt(result[1], 16),
          g: parseInt(result[2], 16),
          b: parseInt(result[3], 16),
        }
      : null
  },
  
  rgbToHex: (r: number, g: number, b: number): string => {
    return `#${[r, g, b].map(x => x.toString(16).padStart(2, '0')).join('')}`
  },
  
  lighten: (hex: string, percent: number): string => {
    const rgb = color.hexToRgb(hex)
    if (!rgb) return hex
    
    const { r, g, b } = rgb
    const amount = Math.round(2.55 * percent)
    
    return color.rgbToHex(
      Math.min(255, r + amount),
      Math.min(255, g + amount),
      Math.min(255, b + amount)
    )
  },
  
  darken: (hex: string, percent: number): string => {
    const rgb = color.hexToRgb(hex)
    if (!rgb) return hex
    
    const { r, g, b } = rgb
    const amount = Math.round(2.55 * percent)
    
    return color.rgbToHex(
      Math.max(0, r - amount),
      Math.max(0, g - amount),
      Math.max(0, b - amount)
    )
  },
}