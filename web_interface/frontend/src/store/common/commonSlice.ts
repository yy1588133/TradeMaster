import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { ThemeMode } from '@/types'
import { storage } from '@/utils'
import { STORAGE_KEYS } from '@/constants'

// Common state interface
interface CommonState {
  theme: ThemeMode
  sidebarCollapsed: boolean
  loading: boolean
  breadcrumbs: Array<{
    title: string
    path?: string
  }>
  notifications: Array<{
    id: string
    type: 'success' | 'error' | 'warning' | 'info'
    title: string
    message?: string
    timestamp: number
    read: boolean
  }>
}

// Initial state
const initialState: CommonState = {
  theme: storage.get(STORAGE_KEYS.THEME, 'light'),
  sidebarCollapsed: storage.get(STORAGE_KEYS.SIDEBAR_COLLAPSED, false),
  loading: false,
  breadcrumbs: [],
  notifications: [],
}

// Common slice
const commonSlice = createSlice({
  name: 'common',
  initialState,
  reducers: {
    setTheme: (state, action: PayloadAction<ThemeMode>) => {
      state.theme = action.payload
      storage.set(STORAGE_KEYS.THEME, action.payload)
    },
    
    toggleTheme: state => {
      const newTheme = state.theme === 'light' ? 'dark' : 'light'
      state.theme = newTheme
      storage.set(STORAGE_KEYS.THEME, newTheme)
    },
    
    setSidebarCollapsed: (state, action: PayloadAction<boolean>) => {
      state.sidebarCollapsed = action.payload
      storage.set(STORAGE_KEYS.SIDEBAR_COLLAPSED, action.payload)
    },
    
    toggleSidebar: state => {
      state.sidebarCollapsed = !state.sidebarCollapsed
      storage.set(STORAGE_KEYS.SIDEBAR_COLLAPSED, state.sidebarCollapsed)
    },
    
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload
    },
    
    setBreadcrumbs: (state, action: PayloadAction<Array<{
      title: string
      path?: string
    }>>) => {
      state.breadcrumbs = action.payload
    },
    
    addNotification: (state, action: PayloadAction<{
      type: 'success' | 'error' | 'warning' | 'info'
      title: string
      message?: string
    }>) => {
      const notification = {
        id: Date.now().toString(),
        ...action.payload,
        timestamp: Date.now(),
        read: false,
      }
      state.notifications.unshift(notification)
      
      // Keep only the latest 50 notifications
      if (state.notifications.length > 50) {
        state.notifications = state.notifications.slice(0, 50)
      }
    },
    
    markNotificationAsRead: (state, action: PayloadAction<string>) => {
      const notification = state.notifications.find(n => n.id === action.payload)
      if (notification) {
        notification.read = true
      }
    },
    
    markAllNotificationsAsRead: state => {
      state.notifications.forEach(notification => {
        notification.read = true
      })
    },
    
    removeNotification: (state, action: PayloadAction<string>) => {
      state.notifications = state.notifications.filter(n => n.id !== action.payload)
    },
    
    clearNotifications: state => {
      state.notifications = []
    },
  },
})

export const {
  setTheme,
  toggleTheme,
  setSidebarCollapsed,
  toggleSidebar,
  setLoading,
  setBreadcrumbs,
  addNotification,
  markNotificationAsRead,
  markAllNotificationsAsRead,
  removeNotification,
  clearNotifications,
} = commonSlice.actions

export default commonSlice.reducer