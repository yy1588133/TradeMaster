// ==================== TradeMaster Frontend 测试设置 ====================
// Vitest 测试环境设置文件

import '@testing-library/jest-dom'
import { configure } from '@testing-library/react'
import { vi } from 'vitest'

// ==================== Testing Library 配置 ====================
configure({
  // 测试ID属性
  testIdAttribute: 'data-testid',
  
  // 异步工具超时时间
  asyncUtilTimeout: 5000,
  
  // 计算可访问名称时的选项
  computedStyleSupportsPseudoElements: true,
  
  // 默认隐藏元素
  defaultHidden: false,
  
  // 显示建议的查询
  showOriginalStackTrace: true,
  
  // 抛出建议
  throwSuggestions: true,
})

// ==================== 全局 Mock 配置 ====================

// Mock window.matchMedia (对于响应式组件)
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// Mock window.ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

// Mock IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
  root: null,
  rootMargin: '',
  thresholds: [],
}))

// Mock getComputedStyle
Object.defineProperty(window, 'getComputedStyle', {
  value: () => ({
    getPropertyValue: () => '',
  }),
})

// Mock HTMLCanvasElement.getContext
HTMLCanvasElement.prototype.getContext = vi.fn().mockReturnValue({
  fillRect: vi.fn(),
  clearRect: vi.fn(),
  getImageData: vi.fn(() => ({
    data: new Array(4),
  })),
  putImageData: vi.fn(),
  createImageData: vi.fn(() => []),
  setTransform: vi.fn(),
  drawImage: vi.fn(),
  save: vi.fn(),
  fillText: vi.fn(),
  restore: vi.fn(),
  beginPath: vi.fn(),
  moveTo: vi.fn(),
  lineTo: vi.fn(),
  closePath: vi.fn(),
  stroke: vi.fn(),
  translate: vi.fn(),
  scale: vi.fn(),
  rotate: vi.fn(),
  arc: vi.fn(),
  fill: vi.fn(),
  measureText: vi.fn(() => ({ width: 0 })),
  transform: vi.fn(),
  rect: vi.fn(),
  clip: vi.fn(),
})

// Mock URL.createObjectURL
Object.defineProperty(URL, 'createObjectURL', {
  writable: true,
  value: vi.fn().mockReturnValue('mock-url'),
})

// Mock URL.revokeObjectURL
Object.defineProperty(URL, 'revokeObjectURL', {
  writable: true,
  value: vi.fn(),
})

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  key: vi.fn(),
  length: 0,
}
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
})

// Mock sessionStorage
const sessionStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  key: vi.fn(),
  length: 0,
}
Object.defineProperty(window, 'sessionStorage', {
  value: sessionStorageMock,
})

// Mock window.location
Object.defineProperty(window, 'location', {
  value: {
    href: 'http://localhost:3000',
    origin: 'http://localhost:3000',
    protocol: 'http:',
    host: 'localhost:3000',
    hostname: 'localhost',
    port: '3000',
    pathname: '/',
    search: '',
    hash: '',
    assign: vi.fn(),
    replace: vi.fn(),
    reload: vi.fn(),
  },
  writable: true,
})

// Mock console 方法 (可选择性启用)
if (process.env.VITEST_MOCK_CONSOLE !== 'false') {
  global.console = {
    ...console,
    log: vi.fn(),
    debug: vi.fn(),
    info: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
  }
}

// Mock fetch (如果没有使用 MSW)
if (!global.fetch) {
  global.fetch = vi.fn()
}

// ==================== Ant Design 相关 Mock ====================

// Mock Ant Design 的 message 组件
vi.mock('antd', async () => {
  const actual = await vi.importActual('antd')
  return {
    ...actual,
    message: {
      success: vi.fn(),
      error: vi.fn(),
      info: vi.fn(),
      warning: vi.fn(),
      warn: vi.fn(),
      loading: vi.fn(),
      destroy: vi.fn(),
    },
    notification: {
      success: vi.fn(),
      error: vi.fn(),
      info: vi.fn(),
      warning: vi.fn(),
      warn: vi.fn(),
      open: vi.fn(),
      close: vi.fn(),
      destroy: vi.fn(),
    },
    Modal: {
      ...actual.Modal,
      confirm: vi.fn(),
      info: vi.fn(),
      success: vi.fn(),
      error: vi.fn(),
      warning: vi.fn(),
      warn: vi.fn(),
    },
  }
})

// ==================== 图表库 Mock ====================

// Mock ECharts
vi.mock('echarts', () => ({
  init: vi.fn().mockReturnValue({
    setOption: vi.fn(),
    resize: vi.fn(),
    dispose: vi.fn(),
    on: vi.fn(),
    off: vi.fn(),
    getWidth: vi.fn().mockReturnValue(400),
    getHeight: vi.fn().mockReturnValue(300),
  }),
  connect: vi.fn(),
  disconnect: vi.fn(),
  dispose: vi.fn(),
  registerTheme: vi.fn(),
  registerMap: vi.fn(),
}))

// Mock echarts-for-react
vi.mock('echarts-for-react', () => ({
  default: vi.fn().mockImplementation(() => null),
}))

// ==================== 路由 Mock ====================

// Mock react-router-dom
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => vi.fn(),
    useLocation: () => ({
      pathname: '/',
      search: '',
      hash: '',
      state: null,
    }),
    useParams: () => ({}),
    useSearchParams: () => [new URLSearchParams(), vi.fn()],
  }
})

// ==================== Redux Mock ====================

// 如果需要 Mock Redux store，可以在这里配置
// import { configureStore } from '@reduxjs/toolkit'
// export const mockStore = configureStore({
//   reducer: {
//     // your reducers
//   },
// })

// ==================== 工具函数 ====================

// 清理所有 Mock
export const clearAllMocks = () => {
  vi.clearAllMocks()
  localStorageMock.clear()
  sessionStorageMock.clear()
}

// 重置所有 Mock
export const resetAllMocks = () => {
  vi.resetAllMocks()
}

// 恢复所有 Mock
export const restoreAllMocks = () => {
  vi.restoreAllMocks()
}

// ==================== 自定义匹配器 ====================

// 扩展 expect 匹配器
declare global {
  namespace Vi {
    interface JestAssertion<T = any> {
      toBeInTheDocument(): T
      toHaveClass(className: string): T
      toHaveStyle(style: Record<string, any>): T
    }
  }
}

// ==================== 测试环境变量 ====================

// 设置测试环境变量
process.env.NODE_ENV = 'test'
process.env.VITE_APP_ENV = 'test'
process.env.VITE_ENABLE_MOCK = 'true'
process.env.VITE_API_BASE_URL = 'http://localhost:3001'

// ==================== 异步测试工具 ====================

// 等待异步操作完成的工具函数
export const waitForAsync = (timeout = 1000) =>
  new Promise(resolve => setTimeout(resolve, timeout))

// ==================== 错误处理 ====================

// 捕获未处理的 Promise 拒绝
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason)
})

// 捕获未处理的异常
process.on('uncaughtException', error => {
  console.error('Uncaught Exception:', error)
})

// ==================== 清理工作 ====================

// 在每个测试之前运行
beforeEach(() => {
  // 清理 DOM
  document.body.innerHTML = ''
  document.head.innerHTML = ''
  
  // 重置 Mock
  vi.clearAllMocks()
})

// 在每个测试文件之后运行
afterEach(() => {
  // 清理
  clearAllMocks()
})

// 在所有测试之后运行
afterAll(() => {
  // 最终清理
  restoreAllMocks()
})

// ==================== 使用说明 ====================
/*
这个设置文件会在所有测试运行之前执行，用于:

1. 配置测试环境
2. Mock 全局对象和函数
3. 设置测试工具
4. 提供测试辅助函数

使用方式:
- 在 vitest.config.ts 中通过 setupFiles 引入
- 测试文件中直接使用配置好的环境
- 使用提供的工具函数进行测试

常用测试模式:
```typescript
import { render, screen } from '@testing-library/react'
import { vi } from 'vitest'
import MyComponent from './MyComponent'

describe('MyComponent', () => {
  it('should render correctly', () => {
    render(<MyComponent />)
    expect(screen.getByRole('button')).toBeInTheDocument()
  })
})
```
*/