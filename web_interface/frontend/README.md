# TradeMaster Frontend

TradeMaster 前端应用，基于 React + TypeScript + Vite 构建的现代化量化交易平台界面。

## 🚀 技术栈

- **框架**: React 18 + TypeScript 5.0+
- **构建工具**: Vite 5.0+
- **UI 框架**: Ant Design 5.0+
- **状态管理**: Redux Toolkit + RTK Query
- **路由**: React Router 6.0+
- **图表库**: ECharts + @ant-design/plots
- **HTTP 客户端**: Axios
- **样式**: CSS Modules + Less
- **代码规范**: ESLint + Prettier

## 📦 项目结构

```
frontend/
├── public/                 # 静态资源
├── src/
│   ├── components/         # 通用组件
│   │   ├── Layout/        # 布局组件
│   │   ├── Charts/        # 图表组件
│   │   ├── Forms/         # 表单组件
│   │   └── Common/        # 其他通用组件
│   ├── pages/             # 页面组件
│   │   ├── Auth/          # 认证页面
│   │   ├── Dashboard/     # 仪表板
│   │   ├── Strategy/      # 策略管理
│   │   ├── Data/          # 数据管理
│   │   ├── Training/      # 训练管理
│   │   └── Analysis/      # 分析评估
│   ├── services/          # API服务
│   ├── store/             # 状态管理
│   ├── hooks/             # 自定义hooks
│   ├── utils/             # 工具函数
│   ├── styles/            # 样式文件
│   ├── constants/         # 常量定义
│   ├── types/             # 类型定义
│   ├── App.tsx            # 应用主组件
│   └── main.tsx           # 应用入口
├── package.json           # 项目配置
├── vite.config.ts         # Vite配置
├── tsconfig.json          # TypeScript配置
└── README.md              # 项目说明
```

## 🛠️ 开发环境

### 环境要求

- Node.js >= 18.0.0
- pnpm >= 8.0.0 (推荐)
- 或 npm >= 9.0.0
- 或 yarn >= 1.22.0

### 安装依赖

```bash
# 使用 pnpm (推荐)
pnpm install

# 或使用 npm
npm install

# 或使用 yarn
yarn install
```

### 环境变量

创建 `.env.local` 文件并配置以下环境变量：

```bash
# API 基础地址
VITE_API_BASE_URL=http://localhost:8000

# 应用标题
VITE_APP_TITLE=TradeMaster

# 应用版本
VITE_APP_VERSION=1.0.0
```

### 开发命令

```bash
# 启动开发服务器
pnpm dev

# 构建生产版本
pnpm build

# 预览生产构建
pnpm preview

# 类型检查
pnpm type-check

# 代码检查
pnpm lint

# 代码检查并修复
pnpm lint:fix

# 代码格式化
pnpm format

# 代码格式化检查
pnpm format:check
```

## 🏗️ 构建部署

### 生产构建

```bash
pnpm build
```

构建产物将生成在 `dist/` 目录中。

### 部署说明

1. **静态文件服务器**: 将 `dist/` 目录部署到任何静态文件服务器
2. **Nginx**: 配置 Nginx 代理和路由重写
3. **Docker**: 使用提供的 Dockerfile 构建镜像

### Nginx 配置示例

```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /var/www/trademaster-frontend;
    index index.html;

    # 处理 React Router 路由
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API 代理
    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## 🔧 配置说明

### Vite 配置

- **路径别名**: 配置了 `@/` 指向 `src/` 目录
- **代理配置**: 开发环境下代理 `/api` 请求到后端服务
- **构建优化**: 代码分割、压缩、Tree Shaking
- **Less 支持**: 配置 Less 预处理器和 Ant Design 主题变量

### TypeScript 配置

- **严格模式**: 启用所有严格类型检查
- **路径映射**: 支持绝对路径导入
- **现代 ES 特性**: 支持最新的 ECMAScript 特性

### ESLint + Prettier

- **代码规范**: 基于 Airbnb 规范和 React 最佳实践
- **自动格式化**: 保存时自动格式化代码
- **Git Hooks**: 提交前自动检查代码质量

## 📚 开发指南

### 组件开发

```tsx
import React from 'react'
import { Card, Typography } from 'antd'
import styles from './MyComponent.module.less'

interface MyComponentProps {
  title: string
  children?: React.ReactNode
}

const MyComponent: React.FC<MyComponentProps> = ({ title, children }) => {
  return (
    <Card className={styles.container}>
      <Typography.Title level={3}>{title}</Typography.Title>
      {children}
    </Card>
  )
}

export default MyComponent
```

### 状态管理

```tsx
import { useAppDispatch, useAppSelector } from '@/store'
import { fetchDataAsync } from '@/store/slices/dataSlice'

const MyComponent: React.FC = () => {
  const dispatch = useAppDispatch()
  const { data, loading } = useAppSelector(state => state.data)

  const handleFetch = () => {
    dispatch(fetchDataAsync())
  }

  return (
    // Component JSX
  )
}
```

### API 调用

```tsx
import { apiClient } from '@/services'

// GET 请求
const data = await apiClient.get('/api/data')

// POST 请求
const result = await apiClient.post('/api/data', { name: 'example' })

// 文件上传
const uploadResult = await apiClient.upload('/api/upload', file)
```

### 样式开发

```less
// styles/MyComponent.module.less
@import '@/styles/variables.less';

.container {
  padding: @padding-lg;
  background: @component-background;
  border-radius: @border-radius-base;
  box-shadow: @box-shadow-base;

  .title {
    color: @heading-color;
    margin-bottom: @margin-md;
  }

  &:hover {
    box-shadow: @box-shadow-2;
  }
}
```

## 🧪 测试

```bash
# 运行单元测试
pnpm test

# 运行测试并生成覆盖率报告
pnpm test:coverage

# 监听模式运行测试
pnpm test:watch
```

## 📈 性能优化

### 代码分割

- 路由级别的懒加载
- 组件级别的动态导入
- 第三方库的 Bundle 分离

### 构建优化

- Tree Shaking 移除未使用代码
- 资源压缩和优化
- 现代浏览器构建目标

### 运行时优化

- React.memo 防止不必要的重渲染
- useMemo 和 useCallback 缓存计算结果
- 虚拟滚动处理大数据列表

## 🐛 调试

### 开发工具

- **React Developer Tools**: React 组件调试
- **Redux DevTools**: 状态管理调试
- **Network Tab**: API 请求调试
- **Console**: 日志输出和错误跟踪

### 日志配置

```tsx
// 开发环境日志
if (import.meta.env.DEV) {
  console.log('Debug info:', data)
}

// 生产环境错误追踪
if (import.meta.env.PROD) {
  // 集成错误监控服务
}
```

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

### 代码规范

- 遵循 ESLint 和 Prettier 配置
- 使用 TypeScript 严格模式
- 编写清晰的注释和文档
- 保持组件的单一职责原则

## 📄 许可证

本项目基于 MIT 许可证开源 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🔗 相关链接

- [TradeMaster 后端项目](../backend/)
- [项目文档](../docs/)
- [API 文档](../docs/api/)
- [部署指南](../docs/deployment/)

## 📞 联系方式

如有问题或建议，请联系项目维护者或创建 Issue。