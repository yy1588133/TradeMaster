# 前端技术规范与架构设计

## 🎯 技术栈选型

### 核心框架
- **React 18**: 最新版本，支持并发特性和自动批处理
- **TypeScript 4.9+**: 强类型支持，提升代码质量
- **Vite 4**: 现代化构建工具，极速热更新

### UI框架与设计
- **Ant Design Pro 5**: 企业级UI组件库，开箱即用
- **@ant-design/pro-components**: 高级业务组件
- **@ant-design/icons**: 图标库
- **Tailwind CSS**: 原子化CSS框架，快速样式开发

### 状态管理
- **Zustand**: 轻量级状态管理，替代Redux
- **React Query (TanStack Query)**: 服务端状态管理
- **React Hook Form**: 表单状态管理

### 数据可视化
- **ECharts 5**: 主要图表库，支持WebGL渲染
- **@ant-design/plots**: 基于G2的统计图表
- **D3.js**: 自定义可视化需求
- **React-ECharts**: ECharts的React封装

### 路由与导航
- **React Router v6**: 声明式路由
- **@ant-design/pro-layout**: 专业布局组件

### 开发工具
- **ESLint**: 代码检查
- **Prettier**: 代码格式化
- **Husky**: Git hooks
- **lint-staged**: 提交前检查

## 📋 Package.json 配置

```json
{
  "name": "trademaster-web-frontend",
  "version": "1.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite --host 0.0.0.0 --port 3000",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint src --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "lint:fix": "eslint src --ext ts,tsx --fix",
    "type-check": "tsc --noEmit",
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest --coverage",
    "prepare": "husky install"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.8.0",
    "@ant-design/pro-components": "^2.3.0",
    "@ant-design/pro-layout": "^7.8.0",
    "@ant-design/icons": "^5.0.0",
    "antd": "^5.2.0",
    "@ant-design/plots": "^1.2.0",
    "echarts": "^5.4.0",
    "echarts-for-react": "^3.0.2",
    "d3": "^7.8.0",
    "@types/d3": "^7.4.0",
    "zustand": "^4.3.0",
    "@tanstack/react-query": "^4.24.0",
    "react-hook-form": "^7.43.0",
    "@hookform/resolvers": "^2.9.0",
    "yup": "^1.0.0",
    "axios": "^1.3.0",
    "dayjs": "^1.11.0",
    "lodash-es": "^4.17.0",
    "@types/lodash-es": "^4.17.0",
    "react-draggable": "^4.4.0",
    "react-resizable": "^3.0.0",
    "react-grid-layout": "^1.3.0",
    "ahooks": "^3.7.0",
    "classnames": "^2.3.0",
    "react-helmet-async": "^1.3.0",
    "react-hotkeys-hook": "^4.3.0",
    "react-use": "^17.4.0"
  },
  "devDependencies": {
    "@types/react": "^18.0.0",
    "@types/react-dom": "^18.0.0",
    "@types/node": "^18.0.0",
    "@vitejs/plugin-react": "^3.1.0",
    "vite": "^4.1.0",
    "typescript": "^4.9.0",
    "tailwindcss": "^3.2.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "@typescript-eslint/eslint-plugin": "^5.54.0",
    "@typescript-eslint/parser": "^5.54.0",
    "eslint": "^8.35.0",
    "eslint-plugin-react": "^7.32.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.3.0",
    "prettier": "^2.8.0",
    "husky": "^8.0.0",
    "lint-staged": "^13.1.0",
    "vitest": "^0.28.0",
    "@testing-library/react": "^14.0.0",
    "@testing-library/jest-dom": "^5.16.0",
    "jsdom": "^21.1.0",
    "@vitejs/plugin-eslint": "^1.8.0",
    "rollup-plugin-visualizer": "^5.9.0"
  },
  "lint-staged": {
    "*.{js,jsx,ts,tsx}": [
      "eslint --fix",
      "prettier --write"
    ],
    "*.{json,css,md}": [
      "prettier --write"
    ]
  }
}
```

## ⚙️ Vite 配置

```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'
import eslint from '@vitejs/plugin-eslint'
import { visualizer } from 'rollup-plugin-visualizer'

export default defineConfig({
  plugins: [
    react(),
    eslint(),
    visualizer({
      filename: 'dist/stats.html',
      open: true,
      gzipSize: true,
      brotliSize: true,
    }),
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
      '@/components': resolve(__dirname, 'src/components'),
      '@/pages': resolve(__dirname, 'src/pages'),
      '@/stores': resolve(__dirname, 'src/stores'),
      '@/services': resolve(__dirname, 'src/services'),
      '@/utils': resolve(__dirname, 'src/utils'),
      '@/types': resolve(__dirname, 'src/types'),
      '@/hooks': resolve(__dirname, 'src/hooks'),
      '@/styles': resolve(__dirname, 'src/styles'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '/api/v1'),
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
        changeOrigin: true,
      },
    },
  },
  build: {
    target: 'es2015',
    outDir: 'dist',
    sourcemap: true,
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        chunkFileNames: 'assets/js/[name]-[hash].js',
        entryFileNames: 'assets/js/[name]-[hash].js',
        assetFileNames: 'assets/[ext]/[name]-[hash].[ext]',
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'antd-vendor': ['antd', '@ant-design/icons', '@ant-design/pro-components'],
          'chart-vendor': ['echarts', 'echarts-for-react', '@ant-design/plots'],
          'utils-vendor': ['lodash-es', 'dayjs', 'axios'],
        },
      },
    },
  },
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'antd',
      'echarts',
      '@ant-design/icons',
      'lodash-es',
      'dayjs',
    ],
  },
})
```

## 🎨 主题与样式配置

### Tailwind CSS 配置

```javascript
// tailwind.config.js
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f9ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        },
        success: {
          500: '#10b981',
          600: '#059669',
        },
        warning: {
          500: '#f59e0b',
          600: '#d97706',
        },
        error: {
          500: '#ef4444',
          600: '#dc2626',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
    require('@tailwindcss/aspect-ratio'),
  ],
  darkMode: 'class',
}
```

### 全局样式

```css
/* src/styles/globals.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --color-primary: #3b82f6;
  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-error: #ef4444;
  --color-text-primary: #1f2937;
  --color-text-secondary: #6b7280;
  --color-bg-primary: #ffffff;
  --color-bg-secondary: #f9fafb;
  --color-border: #e5e7eb;
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
  --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
}

[data-theme='dark'] {
  --color-text-primary: #f9fafb;
  --color-text-secondary: #d1d5db;
  --color-bg-primary: #1f2937;
  --color-bg-secondary: #111827;
  --color-border: #374151;
}

* {
  box-sizing: border-box;
  padding: 0;
  margin: 0;
}

html,
body {
  max-width: 100vw;
  overflow-x: hidden;
  font-family: 'Inter', system-ui, sans-serif;
  line-height: 1.6;
  color: var(--color-text-primary);
  background-color: var(--color-bg-primary);
}

a {
  color: inherit;
  text-decoration: none;
}

.scrollbar-thin {
  scrollbar-width: thin;
  scrollbar-color: rgb(156 163 175) transparent;
}

.scrollbar-thin::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.scrollbar-thin::-webkit-scrollbar-track {
  background: transparent;
}

.scrollbar-thin::-webkit-scrollbar-thumb {
  background: rgb(156 163 175);
  border-radius: 3px;
}

.scrollbar-thin::-webkit-scrollbar-thumb:hover {
  background: rgb(107 114 128);
}

/* 自定义组件样式 */
.chart-container {
  @apply relative w-full bg-white rounded-lg shadow-sm border border-gray-100 p-4;
}

.dark .chart-container {
  @apply bg-gray-800 border-gray-700;
}

.loading-spinner {
  @apply inline-block animate-spin rounded-full border-2 border-gray-300 border-t-blue-600;
}

.status-badge {
  @apply inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium;
}

.status-badge.success {
  @apply bg-green-100 text-green-800;
}

.status-badge.warning {
  @apply bg-yellow-100 text-yellow-800;
}

.status-badge.error {
  @apply bg-red-100 text-red-800;
}

.status-badge.info {
  @apply bg-blue-100 text-blue-800;
}

/* 响应式断点工具类 */
@layer utilities {
  .container-responsive {
    @apply container mx-auto px-4 sm:px-6 lg:px-8;
  }
  
  .grid-responsive {
    @apply grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 lg:gap-6;
  }
  
  .flex-center {
    @apply flex items-center justify-center;
  }
  
  .flex-between {
    @apply flex items-center justify-between;
  }
  
  .text-truncate {
    @apply truncate;
  }
  
  .text-ellipsis-2 {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
  
  .text-ellipsis-3 {
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
}

/* Ant Design 自定义样式 */
.ant-layout {
  min-height: 100vh;
}

.ant-layout-sider {
  box-shadow: var(--shadow-md);
}

.ant-menu {
  border-right: none !important;
}

.ant-table {
  @apply rounded-lg;
}

.ant-card {
  @apply shadow-sm;
}

.ant-form-item-label > label {
  @apply font-medium text-gray-700;
}

.dark .ant-form-item-label > label {
  @apply text-gray-300;
}
```

## 🏗️ 组件架构设计

### 组件分层结构

```
components/
├── Layout/          # 布局组件 - 应用级别
├── Charts/          # 图表组件 - 业务级别  
├── Forms/           # 表单组件 - 业务级别
├── Tables/          # 表格组件 - 业务级别
├── Modals/          # 弹窗组件 - 业务级别
└── Common/          # 通用组件 - 基础级别
```

### 组件设计原则

1. **单一职责**: 每个组件只负责一个功能
2. **可复用性**: 组件设计考虑复用场景
3. **可组合性**: 小组件组合成大组件
4. **可测试性**: 便于单元测试
5. **类型安全**: 完整的TypeScript类型定义

### 示例组件结构

```typescript
// src/components/Charts/LineChart.tsx
import React, { memo, useMemo } from 'react'
import ReactECharts from 'echarts-for-react'
import { EChartsOption } from 'echarts'
import { useTheme } from '@/hooks/useTheme'

export interface LineChartProps {
  data: Array<{
    name: string
    value: number
    time: string
  }>
  title?: string
  height?: number
  loading?: boolean
  className?: string
  onPointClick?: (params: any) => void
}

export const LineChart: React.FC<LineChartProps> = memo(({
  data,
  title,
  height = 400,
  loading = false,
  className,
  onPointClick,
}) => {
  const { isDark } = useTheme()
  
  const option: EChartsOption = useMemo(() => {
    return {
      title: {
        text: title,
        textStyle: {
          color: isDark ? '#f9fafb' : '#1f2937',
        },
      },
      tooltip: {
        trigger: 'axis',
        backgroundColor: isDark ? '#374151' : '#ffffff',
        textStyle: {
          color: isDark ? '#f9fafb' : '#1f2937',
        },
      },
      xAxis: {
        type: 'category',
        data: data.map(item => item.time),
        axisLine: {
          lineStyle: {
            color: isDark ? '#6b7280' : '#e5e7eb',
          },
        },
      },
      yAxis: {
        type: 'value',
        axisLine: {
          lineStyle: {
            color: isDark ? '#6b7280' : '#e5e7eb',
          },
        },
      },
      series: [
        {
          data: data.map(item => item.value),
          type: 'line',
          smooth: true,
          lineStyle: {
            color: '#3b82f6',
            width: 2,
          },
          itemStyle: {
            color: '#3b82f6',
          },
        },
      ],
    }
  }, [data, title, isDark])

  return (
    <div className={`chart-container ${className || ''}`}>
      <ReactECharts
        option={option}
        style={{ height }}
        showLoading={loading}
        onEvents={{
          click: onPointClick,
        }}
        opts={{
          renderer: 'canvas',
          devicePixelRatio: window.devicePixelRatio || 1,
        }}
      />
    </div>
  )
})

LineChart.displayName = 'LineChart'
```

## 🔄 状态管理架构

### Zustand Store 结构

```typescript
// src/stores/strategyStore.ts
import { create } from 'zustand'
import { subscribeWithSelector } from 'zustand/middleware'
import { immer } from 'zustand/middleware/immer'
import { Strategy, StrategyStatus } from '@/types/strategy'

interface StrategyState {
  strategies: Strategy[]
  currentStrategy: Strategy | null
  loading: boolean
  error: string | null
  
  // Actions
  setStrategies: (strategies: Strategy[]) => void
  addStrategy: (strategy: Strategy) => void
  updateStrategy: (id: string, updates: Partial<Strategy>) => void
  deleteStrategy: (id: string) => void
  setCurrentStrategy: (strategy: Strategy | null) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  
  // Computed
  getStrategyById: (id: string) => Strategy | undefined
  getStrategiesByStatus: (status: StrategyStatus) => Strategy[]
}

export const useStrategyStore = create<StrategyState>()(
  subscribeWithSelector(
    immer((set, get) => ({
      strategies: [],
      currentStrategy: null,
      loading: false,
      error: null,
      
      setStrategies: (strategies) => set((state) => {
        state.strategies = strategies
      }),
      
      addStrategy: (strategy) => set((state) => {
        state.strategies.push(strategy)
      }),
      
      updateStrategy: (id, updates) => set((state) => {
        const index = state.strategies.findIndex(s => s.id === id)
        if (index !== -1) {
          state.strategies[index] = { ...state.strategies[index], ...updates }
        }
      }),
      
      deleteStrategy: (id) => set((state) => {
        state.strategies = state.strategies.filter(s => s.id !== id)
      }),
      
      setCurrentStrategy: (strategy) => set((state) => {
        state.currentStrategy = strategy
      }),
      
      setLoading: (loading) => set((state) => {
        state.loading = loading
      }),
      
      setError: (error) => set((state) => {
        state.error = error
      }),
      
      getStrategyById: (id) => {
        return get().strategies.find(s => s.id === id)
      },
      
      getStrategiesByStatus: (status) => {
        return get().strategies.filter(s => s.status === status)
      },
    }))
  )
)
```

## 🚀 性能优化策略

### 1. 代码分割与懒加载

```typescript
// src/routes/index.tsx
import { lazy, Suspense } from 'react'
import { Routes, Route } from 'react-router-dom'
import Loading from '@/components/Common/Loading'

// 懒加载页面组件
const Dashboard = lazy(() => import('@/pages/Dashboard'))
const Strategy = lazy(() => import('@/pages/Strategy'))
const Training = lazy(() => import('@/pages/Training'))

export const AppRoutes = () => {
  return (
    <Suspense fallback={<Loading />}>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/strategy/*" element={<Strategy />} />
        <Route path="/training/*" element={<Training />} />
      </Routes>
    </Suspense>
  )
}
```

### 2. 虚拟化长列表

```typescript
// src/components/Tables/VirtualTable.tsx
import { FixedSizeList as List } from 'react-window'
import { memo } from 'react'

interface VirtualTableProps {
  data: any[]
  height: number
  itemHeight: number
  renderItem: (props: any) => JSX.Element
}

export const VirtualTable: React.FC<VirtualTableProps> = memo(({
  data,
  height,
  itemHeight,
  renderItem,
}) => {
  return (
    <List
      height={height}
      itemCount={data.length}
      itemSize={itemHeight}
      itemData={data}
    >
      {renderItem}
    </List>
  )
})
```

### 3. 图表渲染优化

```typescript
// src/hooks/useChartOptimization.ts
import { useMemo, useCallback } from 'react'
import { debounce } from 'lodash-es'

export const useChartOptimization = (data: any[], threshold = 1000) => {
  // 数据抽样，减少渲染点数
  const sampledData = useMemo(() => {
    if (data.length <= threshold) return data
    
    const step = Math.ceil(data.length / threshold)
    return data.filter((_, index) => index % step === 0)
  }, [data, threshold])
  
  // 防抖更新
  const debouncedUpdate = useCallback(
    debounce((callback: () => void) => callback(), 300),
    []
  )
  
  return { sampledData, debouncedUpdate }
}
```

## 🧪 测试策略

### 单元测试示例

```typescript
// src/components/Charts/__tests__/LineChart.test.tsx
import { render, screen } from '@testing-library/react'
import { LineChart } from '../LineChart'

const mockData = [
  { name: 'A', value: 100, time: '2023-01-01' },
  { name: 'B', value: 200, time: '2023-01-02' },
]

describe('LineChart', () => {
  it('renders chart with data', () => {
    render(<LineChart data={mockData} title="Test Chart" />)
    expect(screen.getByText('Test Chart')).toBeInTheDocument()
  })
  
  it('shows loading state', () => {
    render(<LineChart data={[]} loading={true} />)
    expect(screen.getByTestId('chart-loading')).toBeInTheDocument()
  })
})
```

这个前端规范确保了：

- **现代化技术栈**：使用最新的React生态工具
- **类型安全**：完整的TypeScript支持
- **性能优化**：代码分割、虚拟化、防抖等优化手段
- **可维护性**：清晰的项目结构和组件架构
- **可测试性**：完整的测试策略
- **开发体验**：热更新、代码检查、自动格式化