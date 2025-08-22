import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react-swc'
import { resolve } from 'path'
import { visualizer } from 'rollup-plugin-visualizer'
import legacy from '@vitejs/plugin-legacy'
import checker from 'vite-plugin-checker'
import eslint from 'vite-plugin-eslint'

// https://vitejs.dev/config/
export default defineConfig(({ mode, command }) => {
  // 加载环境变量
  const env = loadEnv(mode, process.cwd(), '')
  const isProduction = mode === 'production'
  const isDevelopment = mode === 'development'

  return {
    plugins: [
      react(),
      
      // 开发环境ESLint检查 - 暂时禁用
      // isDevelopment &&
      //   eslint({
      //     cache: false,
      //     include: ['src/**/*.{ts,tsx}'],
      //     exclude: ['node_modules'],
      //   }),
      
      // TypeScript检查（生产环境禁用检查） - 暂时禁用
      // isDevelopment && checker({
      //   typescript: true,
      //   eslint: {
      //     lintCommand: 'eslint "./src/**/*.{ts,tsx}"',
      //   },
      //   overlay: {
      //     initialIsOpen: false,
      //   },
      // }),
      
      // HTML模板处理 - 使用内置的HTML处理
      
      // 生产环境插件
      isProduction &&
        legacy({
          targets: ['defaults', 'not IE 11'],
        }),
      
      // Bundle分析器
      isProduction &&
        visualizer({
          filename: 'dist/stats.html',
          open: false,
          gzipSize: true,
          brotliSize: true,
          template: 'treemap', // sunburst, treemap, network
        }),
    ].filter(Boolean),

    resolve: {
      alias: {
        '@': resolve(__dirname, 'src'),
        '@/components': resolve(__dirname, 'src/components'),
        '@/pages': resolve(__dirname, 'src/pages'),
        '@/services': resolve(__dirname, 'src/services'),
        '@/store': resolve(__dirname, 'src/store'),
        '@/hooks': resolve(__dirname, 'src/hooks'),
        '@/utils': resolve(__dirname, 'src/utils'),
        '@/styles': resolve(__dirname, 'src/styles'),
        '@/constants': resolve(__dirname, 'src/constants'),
        '@/types': resolve(__dirname, 'src/types'),
      },
    },

    // 环境变量前缀
    envPrefix: ['VITE_', 'REACT_APP_'],

    css: {
      preprocessorOptions: {
        less: {
          javascriptEnabled: true,
          modifyVars: {
            // Ant Design theme variables
            '@primary-color': '#1890ff',
            '@link-color': '#1890ff',
            '@success-color': '#52c41a',
            '@warning-color': '#faad14',
            '@error-color': '#f5222d',
            '@font-size-base': '14px',
            '@heading-color': 'rgba(0, 0, 0, 0.85)',
            '@text-color': 'rgba(0, 0, 0, 0.65)',
            '@text-color-secondary': 'rgba(0, 0, 0, 0.45)',
            '@disabled-color': 'rgba(0, 0, 0, 0.25)',
            '@border-radius-base': '6px',
            '@box-shadow-base': '0 3px 6px -4px rgba(0, 0, 0, 0.12), 0 6px 16px 0 rgba(0, 0, 0, 0.08), 0 9px 28px 8px rgba(0, 0, 0, 0.05)',
          },
        },
      },
    },

    server: {
      port: parseInt(env.VITE_PORT) || 3000,
      host: env.VITE_HOST || '0.0.0.0',
      open: isDevelopment && env.VITE_OPEN_BROWSER !== 'false',
      cors: true,
      strictPort: false,
      proxy: {
        '/api': {
          target: env.VITE_API_PROXY_TARGET || 'http://localhost:8000',
          changeOrigin: true,
          secure: false,
          rewrite: (path) => path,
          configure: (proxy, _options) => {
            proxy.on('error', (err, _req, _res) => {
              console.log('🔥 Proxy error:', err);
            });
            proxy.on('proxyReq', (proxyReq, req, _res) => {
              console.log('📤 Proxy request:', req.method, req.url);
            });
            proxy.on('proxyRes', (proxyRes, req, _res) => {
              console.log('📥 Proxy response:', proxyRes.statusCode, req.url);
            });
          },
        },
        '/ws': {
          target: env.VITE_WS_PROXY_TARGET || 'ws://localhost:8000',
          ws: true,
          changeOrigin: true,
        },
      },
      // 热更新配置
      hmr: {
        overlay: true,
        port: parseInt(env.VITE_HMR_PORT) || 24678,
      },
      watch: {
        usePolling: env.VITE_USE_POLLING === 'true',
        interval: 1000,
        ignored: ['**/node_modules/**', '**/.git/**'],
      },
    },

  build: {
    target: ['es2015', 'edge88', 'firefox78', 'chrome87', 'safari12'],
    outDir: env.VITE_BUILD_OUTPUT_DIR || 'dist',
    assetsDir: 'assets',
    sourcemap: isDevelopment || env.VITE_SOURCEMAP === 'true',
    minify: isProduction ? 'terser' : false,
    cssCodeSplit: true,
    chunkSizeWarningLimit: 1500,
    emptyOutDir: true,
    reportCompressedSize: isProduction,
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
      },
      output: {
        // 静态资源命名
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name.split('.')
          let extType = info[info.length - 1]
          if (/\.(mp4|webm|ogg|mp3|wav|flac|aac)(\?.*)?$/i.test(assetInfo.name)) {
            extType = 'media'
          } else if (/\.(png|jpe?g|gif|svg)(\?.*)?$/i.test(assetInfo.name)) {
            extType = 'images'
          } else if (/\.(woff2?|eot|ttf|otf)(\?.*)?$/i.test(assetInfo.name)) {
            extType = 'fonts'
          }
          return `${extType}/[name]-[hash][extname]`
        },
        // JS分包策略
        manualChunks: {
          // React相关
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          // UI组件库
          'antd-vendor': ['antd', '@ant-design/icons', '@ant-design/plots', '@ant-design/pro-components'],
          // 状态管理
          'redux-vendor': ['@reduxjs/toolkit', 'react-redux', 'immer'],
          // 工具库
          'utils-vendor': ['axios', 'dayjs', 'lodash-es', 'classnames', 'query-string'],
          // 图表库
          'charts-vendor': ['echarts', 'echarts-for-react'],
          // 开发工具
          ...(isDevelopment && {
            'dev-vendor': ['ahooks'],
          }),
        },
        // 文件命名
        chunkFileNames: (chunkInfo) => {
          const facadeModuleId = chunkInfo.facadeModuleId ? chunkInfo.facadeModuleId.split('/').pop().replace(/\.\w+$/, '') : 'chunk'
          return `js/[name]-[hash].js`
        },
        entryFileNames: 'js/[name]-[hash].js',
      },
      // 外部依赖（CDN）
      external: isProduction && env.VITE_USE_CDN === 'true' ? [
        // 可以选择性地将大型库外部化
      ] : [],
    },
    terserOptions: {
      compress: {
        drop_console: isProduction && env.VITE_DROP_CONSOLE !== 'false',
        drop_debugger: isProduction,
        pure_funcs: isProduction ? ['console.log', 'console.info'] : [],
      },
      mangle: {
        safari10: true,
      },
      format: {
        comments: false,
      },
    },
  },

  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      'antd',
      '@ant-design/icons',
      '@ant-design/plots',
      '@reduxjs/toolkit',
      'react-redux',
      'axios',
      'dayjs',
      'lodash-es',
      'classnames',
      'echarts',
      'echarts-for-react',
      'ahooks',
      'immer',
      'query-string',
    ],
    exclude: [
      // 排除某些不需要预构建的包
    ],
    force: env.VITE_FORCE_OPTIMIZE === 'true',
  },

  // 预览配置
  preview: {
    port: parseInt(env.VITE_PREVIEW_PORT) || 4173,
    host: env.VITE_PREVIEW_HOST || '0.0.0.0',
    strictPort: false,
    open: env.VITE_PREVIEW_OPEN === 'true',
  },

  // 测试配置
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    css: true,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        'src/vite-env.d.ts',
      ],
      thresholds: {
        global: {
          branches: 70,
          functions: 70,
          lines: 70,
          statements: 70,
        },
      },
    },
  },
// 定义全局常量
define: {
  __APP_VERSION__: JSON.stringify(process.env.npm_package_version || '1.0.0'),
  __BUILD_TIME__: JSON.stringify(new Date().toISOString()),
  __DEV__: isDevelopment,
  __PROD__: isProduction,
    },
  }
})