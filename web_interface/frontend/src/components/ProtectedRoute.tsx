import React, { useEffect } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { Spin } from 'antd'

import { useAppSelector, useAppDispatch } from '@/store'
import { getProfileAsync, refreshTokenAsync } from '@/store/auth/authSlice'
import { ROUTES } from '@/constants'
import { token } from '@/utils'

interface ProtectedRouteProps {
  children: React.ReactNode
  requiredRole?: string[]
  fallback?: React.ReactNode
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredRole = [],
  fallback = null
}) => {
  const dispatch = useAppDispatch()
  const location = useLocation()
  const { isAuthenticated, user, loading } = useAppSelector(state => state.auth)

  // Check if user has required permissions
  const hasRequiredRole = (userRole: string, requiredRoles: string[]): boolean => {
    if (requiredRoles.length === 0) return true
    
    // Role hierarchy: admin > user > analyst > viewer
    const roleHierarchy = {
      admin: 4,
      user: 3,
      analyst: 2,
      viewer: 1
    }
    
    const userLevel = roleHierarchy[userRole as keyof typeof roleHierarchy] || 0
    const requiredLevel = Math.max(...requiredRoles.map(role => 
      roleHierarchy[role as keyof typeof roleHierarchy] || 0
    ))
    
    return userLevel >= requiredLevel
  }

  useEffect(() => {
    const initializeAuth = async () => {
      const accessToken = token.get()
      const refreshToken = token.getRefresh()

      if (!accessToken && !refreshToken) {
        // No tokens available, user needs to login
        return
      }

      if (!accessToken && refreshToken) {
        // Try to refresh the token
        try {
          await dispatch(refreshTokenAsync()).unwrap()
        } catch (error) {
          console.error('Token refresh failed:', error)
          return
        }
      }

      // If we have a token but no user info, fetch user profile
      if (accessToken && !user) {
        try {
          await dispatch(getProfileAsync()).unwrap()
        } catch (error) {
          console.error('Failed to fetch user profile:', error)
        }
      }
    }

    initializeAuth()
  }, [dispatch, user])

  // Show loading spinner while checking authentication
  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh' 
      }}>
        <Spin size="large" tip="验证身份中..." />
      </div>
    )
  }

  // Check if user is authenticated
  if (!isAuthenticated || !user) {
    // Store the attempted location for redirect after login
    return (
      <Navigate 
        to={ROUTES.LOGIN} 
        state={{ from: location.pathname + location.search }} 
        replace 
      />
    )
  }

  // Check if user account is active
  if (!user.is_active) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        flexDirection: 'column',
        gap: 16
      }}>
        <h2>账户已被禁用</h2>
        <p>您的账户已被管理员禁用，请联系客服处理。</p>
      </div>
    )
  }

  // Check role-based access
  if (requiredRole.length > 0 && !hasRequiredRole(user.role, requiredRole)) {
    if (fallback) {
      return <>{fallback}</>
    }
    
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        flexDirection: 'column',
        gap: 16
      }}>
        <h2>权限不足</h2>
        <p>您没有访问此页面的权限。</p>
      </div>
    )
  }

  // All checks passed, render the protected content
  return <>{children}</>
}

export default ProtectedRoute