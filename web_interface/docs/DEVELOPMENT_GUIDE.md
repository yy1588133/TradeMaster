# 开发指南

## 🚀 快速开始

### 系统要求

**最低要求：**
- Node.js 18+ 
- Python 3.8+
- Docker 20.10+
- Docker Compose 2.0+
- Git 2.30+

**推荐配置：**
- 16GB+ RAM
- 50GB+ 可用磁盘空间
- SSD硬盘
- 多核CPU

### 环境搭建

#### 1. 克隆项目
```bash
git clone <repository-url>
cd web_interface
```

#### 2. 环境变量配置
```bash
# 复制环境变量模板
cp .env.example .env.dev

# 编辑环境变量
vim .env.dev
```

#### 3. Docker开发环境启动
```bash
# 启动开发环境
docker-compose -f docker/docker-compose.dev.yml up -d

# 查看服务状态
docker-compose -f docker/docker-compose.dev.yml ps

# 查看日志
docker-compose -f docker/docker-compose.dev.yml logs -f
```

#### 4. 本地开发环境设置

**后端开发：**
```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements/dev.txt

# 运行数据库迁移
alembic upgrade head

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**前端开发：**
```bash
cd frontend

# 安装依赖
npm install
# 或使用 pnpm (推荐)
pnpm install

# 启动开发服务器
npm run dev
# 或
pnpm dev
```

### 服务访问地址

| 服务 | 地址 | 描述 |
|------|------|------|
| 前端应用 | http://localhost:3000 | React开发服务器 |
| 后端API | http://localhost:8000 | FastAPI应用 |
| API文档 | http://localhost:8000/api/v1/docs | Swagger UI |
| 数据库 | localhost:5433 | PostgreSQL |
| Redis | localhost:6380 | Redis缓存 |
| Flower | http://localhost:5555 | Celery监控 |
| TradeMaster API | http://localhost:8080 | 现有Flask API |

## 🏗️ 项目结构详解

### 前端项目结构 (frontend/)

```
frontend/
├── public/                          # 静态资源
│   ├── index.html                   # HTML模板
│   └── favicon.ico                  # 网站图标
├── src/
│   ├── components/                  # 组件库
│   │   ├── Layout/                  # 布局组件
│   │   │   ├── MainLayout.tsx       # 主布局
│   │   │   ├── Sidebar.tsx          # 侧边栏
│   │   │   └── Header.tsx           # 顶部导航
│   │   ├── Charts/                  # 图表组件
│   │   │   ├── LineChart.tsx        # 折线图
│   │   │   ├── CandlestickChart.tsx # K线图
│   │   │   └── RadarChart.tsx       # 雷达图
│   │   ├── Forms/                   # 表单组件
│   │   ├── Tables/                  # 表格组件
│   │   └── Common/                  # 通用组件
│   ├── pages/                       # 页面组件
│   │   ├── Dashboard/               # 仪表板
│   │   ├── Strategy/                # 策略管理
│   │   ├── Training/                # 模型训练
│   │   ├── Data/                    # 数据管理
│   │   └── Evaluation/              # 评估分析
│   ├── stores/                      # 状态管理 (Zustand)
│   ├── services/                    # API服务
│   ├── hooks/                       # 自定义Hook
│   ├── utils/                       # 工具函数
│   ├── types/                       # TypeScript类型
│   └── styles/                      # 样式文件
├── package.json                     # 依赖管理
├── vite.config.ts                   # Vite配置
├── tsconfig.json                    # TypeScript配置
└── tailwind.config.js               # Tailwind配置
```

### 后端项目结构 (backend/)

```
backend/
├── app/
│   ├── api/                         # API路由
│   │   ├── v1/                      # API版本1
│   │   │   ├── auth.py              # 认证路由
│   │   │   ├── strategy.py          # 策略路由
│   │   │   ├── training.py          # 训练路由
│   │   │   └── data.py              # 数据路由
│   │   └── dependencies.py          # 依赖注入
│   ├── core/                        # 核心配置
│   │   ├── config.py                # 应用配置
│   │   ├── security.py              # 安全配置
│   │   ├── database.py              # 数据库配置
│   │   └── celery_app.py            # Celery配置
│   ├── models/                      # 数据模型
│   ├── schemas/                     # Pydantic模式
│   ├── services/                    # 业务逻辑服务
│   ├── crud/                        # CRUD操作
│   ├── tasks/                       # Celery任务
│   └── utils/                       # 工具函数
├── alembic/                         # 数据库迁移
├── requirements/                    # 依赖文件
├── tests/                           # 测试文件
└── main.py                          # 应用入口
```

## ⚙️ 开发工作流

### Git工作流

我们采用 **Git Flow** 分支策略：

```
main                    # 生产分支
├── develop             # 开发分支
│   ├── feature/xxx     # 功能分支
│   ├── bugfix/xxx      # Bug修复分支
│   └── hotfix/xxx      # 热修复分支
└── release/vx.x.x      # 发布分支
```

**分支命名规范：**
- `feature/strategy-management` - 功能开发
- `bugfix/fix-login-error` - Bug修复
- `hotfix/critical-security-fix` - 紧急修复
- `release/v1.2.0` - 版本发布

**提交信息规范 (Conventional Commits)：**
```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**类型说明：**
- `feat`: 新功能
- `fix`: Bug修复
- `docs`: 文档更新
- `style`: 代码格式化
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建/工具链相关

**示例：**
```
feat(strategy): add strategy creation form

- Add form validation for strategy parameters
- Implement real-time preview
- Add support for multiple strategy types

Closes #123
```

### 代码质量控制

#### 前端代码规范

**ESLint配置 (.eslintrc.js)：**
```javascript
module.exports = {
  extends: [
    'eslint:recommended',
    '@typescript-eslint/recommended',
    'plugin:react/recommended',
    'plugin:react-hooks/recommended',
  ],
  rules: {
    'react/react-in-jsx-scope': 'off',
    '@typescript-eslint/no-unused-vars': 'error',
    'prefer-const': 'error',
    'no-var': 'error',
  },
  settings: {
    react: {
      version: 'detect',
    },
  },
}
```

**Prettier配置 (.prettierrc)：**
```json
{
  "semi": false,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100,
  "endOfLine": "lf"
}
```

#### 后端代码规范

**Black配置 (pyproject.toml)：**
```toml
[tool.black]
line-length = 100
target-version = ['py38']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''
```

**isort配置：**
```toml
[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 100
known_first_party = ["app"]
```

**Flake8配置 (.flake8)：**
```ini
[flake8]
max-line-length = 100
exclude = .git,__pycache__,docs/source/conf.py,old,build,dist
ignore = E203,W503
```

### Pre-commit钩子

**配置文件 (.pre-commit-config.yaml)：**
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.36.0
    hooks:
      - id: eslint
        files: \.(js|jsx|ts|tsx)$
        additional_dependencies:
          - eslint@8.36.0
          - '@typescript-eslint/parser@5.54.0'
          - '@typescript-eslint/eslint-plugin@5.54.0'
```

**安装和使用：**
```bash
# 安装pre-commit
pip install pre-commit

# 安装钩子
pre-commit install

# 手动运行所有文件检查
pre-commit run --all-files
```

## 🧪 测试策略

### 前端测试

**测试技术栈：**
- **Vitest**: 测试运行器
- **React Testing Library**: 组件测试
- **MSW**: API模拟
- **Playwright**: E2E测试

**测试配置 (vitest.config.ts)：**
```typescript
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    globals: true,
  },
})
```

**组件测试示例：**
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

**API模拟 (src/test/mocks/handlers.ts)：**
```typescript
import { rest } from 'msw'

export const handlers = [
  rest.get('/api/v1/strategies', (req, res, ctx) => {
    return res(
      ctx.json({
        success: true,
        data: {
          items: [
            {
              id: 1,
              name: 'Test Strategy',
              status: 'active',
            },
          ],
          total: 1,
        },
      })
    )
  }),
]
```

### 后端测试

**测试技术栈：**
- **Pytest**: 测试框架
- **pytest-asyncio**: 异步测试支持
- **Testcontainers**: 数据库测试
- **Factory Boy**: 测试数据生成
- **httpx**: HTTP客户端测试

**测试配置 (pytest.ini)：**
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
python_classes = Test*
addopts = 
    --strict-markers
    --strict-config
    --cov=app
    --cov-report=term-missing
    --cov-report=html
    --cov-report=xml
    --cov-fail-under=80
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    unit: marks tests as unit tests
```

**API测试示例：**
```python
# tests/api/test_strategies.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_strategy(client: AsyncClient, auth_headers: dict):
    strategy_data = {
        "name": "Test Strategy",
        "description": "Test description",
        "strategy_type": "algorithmic_trading",
        "config": {},
        "parameters": {}
    }
    
    response = await client.post(
        "/api/v1/strategies/",
        json=strategy_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["name"] == "Test Strategy"

@pytest.mark.asyncio
async def test_get_strategies(client: AsyncClient, auth_headers: dict):
    response = await client.get(
        "/api/v1/strategies/",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "items" in data["data"]
```

**数据工厂 (tests/factories.py)：**
```python
import factory
from app.models.user import User
from app.models.strategy import Strategy

class UserFactory(factory.Factory):
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    full_name = factory.Faker("name")
    is_active = True

class StrategyFactory(factory.Factory):
    class Meta:
        model = Strategy
    
    name = factory.Faker("sentence", nb_words=3)
    description = factory.Faker("text")
    strategy_type = "algorithmic_trading"
    status = "draft"
    owner = factory.SubFactory(UserFactory)
```

### E2E测试

**Playwright配置 (playwright.config.ts)：**
```typescript
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
})
```

**E2E测试示例：**
```typescript
// e2e/strategy-management.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Strategy Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.fill('[data-testid=username]', 'testuser')
    await page.fill('[data-testid=password]', 'password')
    await page.click('[data-testid=login-button]')
    await expect(page).toHaveURL('/dashboard')
  })

  test('should create new strategy', async ({ page }) => {
    await page.goto('/strategies')
    await page.click('[data-testid=create-strategy-button]')
    
    await page.fill('[data-testid=strategy-name]', 'Test Strategy')
    await page.selectOption('[data-testid=strategy-type]', 'algorithmic_trading')
    await page.fill('[data-testid=strategy-description]', 'Test description')
    
    await page.click('[data-testid=save-strategy-button]')
    
    await expect(page.locator('[data-testid=success-message]')).toBeVisible()
    await expect(page.locator('text=Test Strategy')).toBeVisible()
  })
})
```

## 📚 API文档

### 自动生成API文档

FastAPI自动生成交互式API文档：

- **Swagger UI**: http://localhost:8000/api/v1/docs
- **ReDoc**: http://localhost:8000/api/v1/redoc
- **OpenAPI JSON**: http://localhost:8000/api/v1/openapi.json

### API文档注释规范

```python
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.strategy import StrategyCreate, StrategyResponse

router = APIRouter()

@router.post("/", response_model=StrategyResponse, status_code=201)
async def create_strategy(
    strategy_in: StrategyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建新策略
    
    ## 参数说明
    - **name**: 策略名称 (必填)
    - **description**: 策略描述 (可选)
    - **strategy_type**: 策略类型 (必填)
    - **config**: 策略配置 (JSON格式)
    - **parameters**: 策略参数 (JSON格式)
    
    ## 返回值
    返回创建的策略详细信息
    
    ## 错误码
    - **400**: 参数验证失败
    - **401**: 未授权访问
    - **409**: 策略名称已存在
    """
    strategy = await strategy_service.create(db, strategy_in, current_user.id)
    return ApiResponse(data=strategy)
```

## 🔧 调试和故障排除

### 前端调试

**浏览器开发者工具：**
1. 打开浏览器开发者工具 (F12)
2. 使用Console查看日志
3. 使用Network查看API请求
4. 使用Sources设置断点

**VS Code调试配置 (.vscode/launch.json)：**
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Launch Chrome",
      "request": "launch",
      "type": "chrome",
      "url": "http://localhost:3000",
      "webRoot": "${workspaceFolder}/frontend/src"
    }
  ]
}
```

**React Developer Tools：**
安装浏览器扩展，用于调试React组件和状态。

### 后端调试

**VS Code调试配置：**
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/backend/main.py",
      "console": "integratedTerminal",
      "justMyCode": true,
      "env": {
        "DEBUG": "true"
      }
    }
  ]
}
```

**日志配置：**
```python
# app/core/logging.py
import logging
import sys
from loguru import logger

def setup_logging():
    # 移除默认处理器
    logger.remove()
    
    # 添加控制台处理器
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
               "<level>{message}</level>",
        level="DEBUG"
    )
    
    # 添加文件处理器
    logger.add(
        "logs/app.log",
        rotation="1 day",
        retention="30 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="INFO"
    )
```

### 常见问题排除

#### 1. 容器启动失败
```bash
# 检查容器状态
docker-compose ps

# 查看容器日志
docker-compose logs service_name

# 重新构建容器
docker-compose build --no-cache service_name

# 清理Docker资源
docker system prune -a
```

#### 2. 数据库连接问题
```bash
# 检查数据库连接
docker-compose exec postgres pg_isready -U postgres

# 连接数据库
docker-compose exec postgres psql -U postgres -d trademaster

# 查看数据库日志
docker-compose logs postgres
```

#### 3. 前端编译错误
```bash
# 清理缓存
rm -rf node_modules package-lock.json
npm install

# 检查类型错误
npm run type-check

# 修复ESLint错误
npm run lint:fix
```

#### 4. API请求失败
```bash
# 检查后端服务状态
curl http://localhost:8000/health

# 查看API文档
open http://localhost:8000/api/v1/docs

# 检查认证token
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/strategies/
```

## 📝 开发最佳实践

### 1. 代码组织
- **单一职责原则**: 每个函数/组件只做一件事
- **DRY原则**: 避免重复代码，提取公共逻辑
- **KISS原则**: 保持简单，避免过度设计
- **命名规范**: 使用有意义的变量和函数名

### 2. 性能优化
- **前端**: 使用React.memo、useCallback、useMemo
- **后端**: 数据库查询优化、缓存策略
- **网络**: 启用Gzip、CDN、图片压缩

### 3. 安全考虑
- **输入验证**: 所有用户输入都要验证
- **SQL注入防护**: 使用参数化查询
- **XSS防护**: 输出内容转义
- **CSRF防护**: 使用CSRF token

### 4. 监控和日志
- **错误监控**: 集成Sentry错误追踪
- **性能监控**: 添加性能指标收集
- **业务日志**: 记录关键业务操作
- **访问日志**: 记录API访问情况

这个开发指南为团队提供了：

- **标准化的开发流程**：Git工作流和代码规范
- **完整的测试策略**：单元测试、集成测试、E2E测试
- **调试和故障排除指南**：常见问题的解决方案
- **最佳实践建议**：代码质量和性能优化
- **详细的配置示例**：开发工具和环境配置