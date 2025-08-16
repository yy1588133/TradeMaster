import React, { useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { App as AntdApp } from 'antd'

import { useAppDispatch, useAppSelector } from './store'
import { getProfileAsync } from './store/auth/authSlice'
import { token } from './utils'
import { ROUTES } from './constants'

// Layout components
import MainLayout from './components/Layout/MainLayout'
import AuthLayout from './components/Layout/AuthLayout'

// Pages
import Login from './pages/Auth/Login'
import Register from './pages/Auth/Register'
import Dashboard from './pages/Dashboard/Overview'
import StrategyList from './pages/Strategy/StrategyList'
import StrategyCreate from './pages/Strategy/StrategyCreate'
import StrategyDetail from './pages/Strategy/StrategyDetail'
import DatasetList from './pages/Data/DatasetList'
import TrainingList from './pages/Training/TrainingList'
import Analysis from './pages/Analysis/Analysis'
import Profile from './pages/Profile/Profile'
import NotFound from './pages/Common/NotFound'

// Protected route wrapper
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAppSelector(state => state.auth)
  
  if (!isAuthenticated) {
    return <Navigate to={ROUTES.LOGIN} replace />
  }
  
  return <>{children}</>
}

// Public route wrapper (redirect to dashboard if authenticated)
const PublicRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAppSelector(state => state.auth)
  
  if (isAuthenticated) {
    return <Navigate to={ROUTES.DASHBOARD} replace />
  }
  
  return <>{children}</>
}

const App: React.FC = () => {
  const dispatch = useAppDispatch()
  const { isAuthenticated, loading } = useAppSelector(state => state.auth)

  // Initialize app
  useEffect(() => {
    const initApp = async () => {
      // Check if user has valid token
      const authToken = token.get()
      if (authToken && !isAuthenticated) {
        try {
          // Try to get user profile to validate token
          await dispatch(getProfileAsync()).unwrap()
        } catch (error) {
          // Token is invalid, clear it
          token.clear()
          console.warn('Invalid token, cleared from storage')
        }
      }
    }

    initApp()
  }, [dispatch, isAuthenticated])

  // Show loading screen while initializing
  if (loading) {
    return (
      <div 
        style={{
          height: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: '#f0f2f5'
        }}
      >
        <div className="loading-spinner" />
        <span style={{ marginLeft: 16, color: '#666' }}>正在加载...</span>
      </div>
    )
  }

  return (
    <AntdApp>
      <Routes>
        {/* Public routes */}
        <Route
          path={ROUTES.LOGIN}
          element={
            <PublicRoute>
              <AuthLayout>
                <Login />
              </AuthLayout>
            </PublicRoute>
          }
        />
        <Route
          path={ROUTES.REGISTER}
          element={
            <PublicRoute>
              <AuthLayout>
                <Register />
              </AuthLayout>
            </PublicRoute>
          }
        />

        {/* Protected routes */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <MainLayout />
            </ProtectedRoute>
          }
        >
          {/* Dashboard */}
          <Route index element={<Navigate to={ROUTES.DASHBOARD} replace />} />
          <Route path={ROUTES.DASHBOARD.slice(1)} element={<Dashboard />} />

          {/* Strategy routes */}
          <Route path={ROUTES.STRATEGIES.slice(1)} element={<StrategyList />} />
          <Route path={ROUTES.STRATEGY_CREATE.slice(1)} element={<StrategyCreate />} />
          <Route path={ROUTES.STRATEGY_DETAIL.slice(1)} element={<StrategyDetail />} />

          {/* Data routes */}
          <Route path={ROUTES.DATASETS.slice(1)} element={<DatasetList />} />

          {/* Training routes */}
          <Route path={ROUTES.TRAINING.slice(1)} element={<TrainingList />} />

          {/* Analysis routes */}
          <Route path={ROUTES.ANALYSIS.slice(1)} element={<Analysis />} />

          {/* Profile routes */}
          <Route path={ROUTES.PROFILE.slice(1)} element={<Profile />} />
        </Route>

        {/* 404 route */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </AntdApp>
  )
}

export default App