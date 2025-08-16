/// <reference types="vitest" />
import { defineConfig, mergeConfig } from 'vite'
import viteConfig from './vite.config'

// ==================== TradeMaster Frontend Vitest 配置 ====================
// Vitest 测试框架配置文件

export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      // ==================== 基础配置 ====================
      // 全局测试 API，无需在每个测试文件中导入
      globals: true,
      
      // 测试环境
      environment: 'jsdom', // 'node' | 'jsdom' | 'happy-dom'
      
      // 环境选项
      environmentOptions: {
        jsdom: {
          resources: 'usable',
          runScripts: 'dangerously',
        },
      },
      
      // 设置文件
      setupFiles: [
        './src/test/setup.ts',
        './src/test/mocks/setup.ts',
      ],
      
      // 全局设置文件（在所有测试之前运行一次）
      globalSetup: './src/test/global-setup.ts',
      
      // ==================== 文件匹配 ====================
      // 测试文件匹配模式
      include: [
        'src/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}',
        'tests/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}',
      ],
      
      // 排除的文件
      exclude: [
        'node_modules',
        'dist',
        'build',
        'coverage',
        '.nyc_output',
        'cypress',
        'src/test/setup.ts',
        'src/test/mocks/**',
        'src/test/fixtures/**',
        'src/test/utils/**',
        '**/*.d.ts',
      ],
      
      // ==================== 超时配置 ====================
      // 测试超时时间 (毫秒)
      testTimeout: 10000,
      
      // Hook 超时时间
      hookTimeout: 10000,
      
      // ==================== 并行配置 ====================
      // 并行测试
      pool: 'threads', // 'threads' | 'forks'
      
      // 最大并发数
      poolOptions: {
        threads: {
          singleThread: false,
          minThreads: 1,
          maxThreads: 4,
        },
      },
      
      // ==================== 输出配置 ====================
      // 报告器
      reporter: ['verbose', 'html', 'json', 'junit'],
      
      // 输出文件
      outputFile: {
        html: './coverage/test-report.html',
        json: './coverage/test-results.json',
        junit: './coverage/junit.xml',
      },
      
      // ==================== 覆盖率配置 ====================
      coverage: {
        // 覆盖率提供者
        provider: 'v8', // 'v8' | 'istanbul' | 'c8'
        
        // 报告格式
        reporter: [
          'text',
          'text-summary', 
          'html',
          'json',
          'json-summary',
          'lcov',
          'clover',
        ],
        
        // 输出目录
        reportsDirectory: './coverage',
        
        // 包含的文件
        include: [
          'src/**/*.{js,jsx,ts,tsx}',
        ],
        
        // 排除的文件
        exclude: [
          'src/**/*.d.ts',
          'src/**/*.test.{js,jsx,ts,tsx}',
          'src/**/*.spec.{js,jsx,ts,tsx}',
          'src/test/**',
          'src/mocks/**',
          'src/vite-env.d.ts',
          'src/main.tsx',
          'src/App.tsx',
          'src/**/*.stories.{js,jsx,ts,tsx}',
          'src/**/*.config.{js,jsx,ts,tsx}',
          'src/types/**',
          'src/constants/**',
          '**/*.d.ts',
          'node_modules/**',
        ],
        
        // 覆盖率阈值
        thresholds: {
          global: {
            branches: 80,
            functions: 80,
            lines: 80,
            statements: 80,
          },
          // 针对特定文件的阈值
          'src/utils/**': {
            branches: 90,
            functions: 90,
            lines: 90,
            statements: 90,
          },
          'src/services/**': {
            branches: 85,
            functions: 85,
            lines: 85,
            statements: 85,
          },
        },
        
        // 是否显示未覆盖的行
        skipFull: false,
        
        // 是否检查覆盖率
        checkCoverage: true,
      },
      
      // ==================== CSS 配置 ====================
      // 是否处理 CSS
      css: {
        include: [/.+/],
        modules: {
          classNameStrategy: 'stable',
        },
      },
      
      // ==================== Mock 配置 ====================
      // 依赖 Mock
      deps: {
        inline: [
          // 强制内联这些包
          'antd',
          '@ant-design/icons',
          '@ant-design/plots',
          'echarts',
          'echarts-for-react',
        ],
        external: [
          // 外部依赖
        ],
      },
      
      // ==================== 监听模式配置 ====================
      // 监听文件变化
      watch: {
        // 监听的文件夹
        include: ['src/**'],
        // 排除的文件夹
        exclude: ['node_modules/**', 'dist/**'],
      },
      
      // ==================== 快照配置 ====================
      // 快照序列化器
      snapshotSerializers: [
        // 可以添加自定义序列化器
      ],
      
      // ==================== 自定义匹配器 ====================
      // 可以扩展 expect
      // setupFiles 中配置
      
      // ==================== 环境变量 ====================
      // 定义全局变量
      define: {
        __TEST__: true,
        __DEV__: false,
        __PROD__: false,
      },
      
      // ==================== 别名配置 ====================
      // 继承 vite.config.ts 中的别名配置
      
      // ==================== 缓存配置 ====================
      cache: {
        dir: 'node_modules/.vitest',
      },
      
      // ==================== 并发控制 ====================
      // 最大并发文件数
      maxConcurrency: 5,
      
      // ==================== 日志配置 ====================
      // 日志级别
      logLevel: 'info', // 'silent' | 'error' | 'warn' | 'info'
      
      // ==================== 故障排除 ====================
      // 是否在测试失败时打开浏览器
      open: false,
      
      // UI 配置
      ui: {
        enabled: true,
        port: 51204,
        open: false,
      },
      
      // ==================== 自定义配置 ====================
      // 测试运行模式
      run: true,
      
      // 是否单线程运行
      singleThread: false,
      
      // 隔离配置
      isolate: true,
      
      // ==================== Vitest 特定功能 ====================
      // 基准测试
      benchmark: {
        include: ['src/**/*.bench.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'],
        exclude: ['node_modules', 'dist', '.idea', '.git', '.cache'],
      },
    },
    
    // ==================== Esbuild 配置 ====================
    esbuild: {
      target: 'es2022',
    },
    
    // ==================== 定义环境变量 ====================
    define: {
      // 测试环境变量
      'import.meta.env.VITE_APP_ENV': '"test"',
      'import.meta.env.VITE_ENABLE_MOCK': 'true',
      'import.meta.env.VITE_API_BASE_URL': '"http://localhost:3001"',
    },
  })
)