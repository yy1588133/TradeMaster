# TradeMaster Web Interface Backend

基于FastAPI的现代化量化交易平台Web后端，为TradeMaster提供统一的Web界面API服务。

## 🚀 项目特性

### 🎯 核心功能
- **用户认证** - JWT令牌认证、权限管理、用户注册登录
- **策略管理** - 创建、编辑、执行交易策略，支持多种策略类型
- **数据管理** - 数据上传、预处理、可视化
- **模型训练** - 异步训练任务管理、状态监控
- **性能分析** - 回测分析、风险评估、性能指标计算
- **实时监控** - WebSocket实时数据推送、策略状态监控

### 🔧 技术栈
- **框架**: FastAPI 0.104+ (高性能异步Web框架)
- **数据库**: PostgreSQL + SQLAlchemy 2.0 (异步ORM)
- **缓存**: Redis (会话存储、缓存)
- **任务队列**: Celery + Redis (异步任务处理)
- **认证**: JWT + Passlib (安全认证)
- **数据验证**: Pydantic v2 (数据验证和序列化)
- **HTTP客户端**: HTTPX (异步HTTP请求)
- **日志**: Loguru + Structlog (结构化日志)

### 🌟 架构特点
- **现代化异步设计** - 全面使用async/await，高并发处理
- **微服务架构** - 模块化设计，易于扩展和维护
- **类型安全** - 完整的类型注解，IDE友好
- **依赖注入** - FastAPI原生依赖注入系统
- **统一异常处理** - 全局异常处理和错误响应
- **API文档自动生成** - OpenAPI/Swagger文档
- **TradeMaster集成** - 无缝对接现有TradeMaster系统

## 📋 目录结构

```
backend/
├── app/                          # 应用核心代码
│   ├── __init__.py              # 应用初始化
│   ├── main.py                  # FastAPI应用入口
│   ├── core/                    # 核心配置和工具
│   │   ├── config.py           # 应用配置管理
│   │   ├── security.py         # 安全认证系统
│   │   └── dependencies.py     # 依赖注入
│   ├── api/                     # API路由模块
│   │   └── api_v1/             # API版本1
│   │       ├── api.py          # 路由聚合
│   │       └── endpoints/      # 具体端点
│   │           ├── auth.py     # 认证接口
│   │           ├── strategies.py # 策略管理
│   │           ├── data.py     # 数据管理
│   │           ├── training.py # 训练任务
│   │           └── analysis.py # 分析评估
│   ├── models/                  # 数据库模型
│   │   └── database.py         # SQLAlchemy模型
│   ├── schemas/                 # Pydantic模式
│   │   └── base.py             # 数据验证模式
│   ├── services/                # 业务服务层
│   │   └── trademaster_integration.py # TradeMaster集成
│   └── utils/                   # 工具函数
│       └── helpers.py          # 辅助工具
├── requirements.txt             # Python依赖
├── .env.example                # 环境配置示例
└── README.md                   # 项目说明
```

## 🛠️ 安装和运行

### 环境要求
- Python 3.11+
- PostgreSQL 13+
- Redis 6+
- TradeMaster系统 (运行在端口8080)
- **推荐**: uv包管理器 (现代化Python依赖管理)

### 1. 克隆项目
```bash
cd web_interface/backend
```

### 2. 安装依赖

#### 方案一：使用uv (推荐)
uv是现代化的Python包管理器，具有更快的安装速度和更智能的依赖解析能力。

```bash
# 安装uv (如果尚未安装)
# Windows (PowerShell):
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
# macOS/Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh

# 使用uv创建虚拟环境
uv venv .venv

# 激活虚拟环境
# Linux/macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# 使用uv安装依赖 (比pip快10倍+)
uv pip install -r requirements.txt
```

#### 方案二：使用pip (传统方式)
```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Linux/macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

**注意**: requirements.txt包含完整的ML依赖栈(PyTorch, TensorFlow, mmcv等)，推荐使用uv避免依赖冲突问题。

### 3. 配置环境变量
```bash
# 复制环境配置示例
cp .env.example .env

# 编辑配置文件，设置数据库、Redis等配置
# 重要：生产环境必须修改SECRET_KEY和数据库密码
```

### 4. 数据库初始化
```bash
# 创建数据库迁移
alembic revision --autogenerate -m "Initial migration"

# 执行数据库迁移
alembic upgrade head
```

### 5. 启动服务

#### 开发环境
```bash
# 启动FastAPI开发服务器
python app/main.py

# 或使用uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 生产环境
```bash
# 使用Gunicorn启动
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 6. 启动异步任务服务 (可选)
```bash
# 启动Celery worker
celery -A app.core.celery_app worker --loglevel=info

# 启动Celery监控 (可选)
celery -A app.core.celery_app flower
```

## 📚 API文档

启动服务后，可以通过以下地址访问API文档：

- **Swagger UI**: http://localhost:8000/api/v1/docs
- **ReDoc**: http://localhost:8000/api/v1/redoc
- **OpenAPI JSON**: http://localhost:8000/api/v1/openapi.json

## 🔐 认证使用

### 注册用户
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "SecurePass123!",
    "agree_terms": true
  }'
```

### 用户登录
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "SecurePass123!"
  }'
```

### 使用JWT令牌
```bash
# 在请求头中包含访问令牌
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 🎯 核心API端点

### 认证相关
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/refresh` - 刷新令牌
- `GET /api/v1/auth/me` - 获取用户信息
- `POST /api/v1/auth/logout` - 用户登出

### 策略管理
- `GET /api/v1/strategies` - 获取策略列表
- `POST /api/v1/strategies` - 创建策略
- `GET /api/v1/strategies/{id}` - 获取策略详情
- `PUT /api/v1/strategies/{id}` - 更新策略
- `DELETE /api/v1/strategies/{id}` - 删除策略
- `POST /api/v1/strategies/{id}/execute` - 执行策略
- `POST /api/v1/strategies/{id}/stop` - 停止策略

### 数据管理
- `POST /api/v1/data/upload` - 上传数据
- `GET /api/v1/data/datasets` - 获取数据集列表
- `POST /api/v1/data/preprocess` - 数据预处理

### 训练任务
- `POST /api/v1/training/start` - 启动训练
- `GET /api/v1/training/{id}/status` - 获取训练状态
- `POST /api/v1/training/{id}/stop` - 停止训练

### 分析评估
- `GET /api/v1/analysis/performance` - 性能分析
- `GET /api/v1/analysis/risk` - 风险分析
- `POST /api/v1/analysis/backtest` - 回测分析

## 🔧 配置说明

### 核心配置项

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `DEBUG` | 调试模式 | `false` |
| `SECRET_KEY` | JWT签名密钥 | 必须设置 |
| `DATABASE_URL` | 数据库连接URL | 自动构建 |
| `REDIS_URL` | Redis连接URL | `redis://localhost:6379/0` |
| `TRADEMASTER_API_URL` | TradeMaster API地址 | `http://localhost:8080` |

### 安全配置
- 生产环境必须设置强随机的`SECRET_KEY`
- 建议启用HTTPS和设置安全的CORS策略
- 配置适当的API限流和防护机制

## 🚀 部署指南

### Docker部署 (推荐)
```bash
# 构建镜像
docker build -t trademaster-backend .

# 运行容器
docker run -d \
  --name trademaster-backend \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@db:5432/trademaster \
  -e REDIS_URL=redis://redis:6379/0 \
  trademaster-backend
```

### 系统服务部署
```bash
# 创建systemd服务文件
sudo nano /etc/systemd/system/trademaster-backend.service

# 启动并启用服务
sudo systemctl start trademaster-backend
sudo systemctl enable trademaster-backend
```

## 🧪 测试

### 运行测试
```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest app/tests/test_auth.py

# 生成测试覆盖率报告
pytest --cov=app --cov-report=html
```

### 测试分类
- **单元测试** - 测试单个函数和类
- **集成测试** - 测试API端点和数据库交互
- **端到端测试** - 测试完整的用户场景

## 📊 监控和日志

### 日志配置
- 使用结构化日志格式(JSON)
- 支持多级别日志 (DEBUG, INFO, WARNING, ERROR)
- 自动日志轮转和归档

### 监控指标
- **性能指标** - 请求延迟、吞吐量、错误率
- **业务指标** - 活跃用户、策略执行次数
- **系统指标** - CPU、内存、数据库连接数

### 健康检查
```bash
# 检查API健康状态
curl http://localhost:8000/health

# 检查TradeMaster集成状态
curl http://localhost:8000/api/v1/status
```

## 🤝 开发指南

### 代码规范
- 使用Black进行代码格式化
- 使用isort进行导入排序
- 使用Flake8进行代码检查
- 使用MyPy进行类型检查
- **推荐使用uv进行依赖管理** - 更快、更智能的包管理

### 提交规范
```bash
# 安装pre-commit钩子
pre-commit install

# 手动运行检查
pre-commit run --all-files
```

### 添加新功能
1. 在`app/api/api_v1/endpoints/`中添加新的API端点
2. 在`app/services/`中实现业务逻辑
3. 在`app/schemas/`中定义数据模式
4. 在`app/models/`中添加数据库模型 (如需要)
5. 编写测试并更新文档

### 依赖管理最佳实践

#### 添加新依赖
```bash
# 使用uv添加新包 (推荐)
uv pip install package_name

# 更新requirements.txt
uv pip freeze > requirements.txt

# 或使用pip
pip install package_name
pip freeze > requirements.txt
```

#### 依赖版本管理
- **生产环境**: 使用固定版本 (如 `fastapi==0.104.1`)
- **开发环境**: 可使用版本范围 (如 `fastapi>=0.104.0`)
- **关键ML库**: 谨慎升级，注意兼容性

#### uv的优势
- **速度**: 比pip快10-100倍的安装速度
- **智能解析**: 自动解决依赖冲突
- **并行下载**: 支持多线程下载
- **缓存优化**: 智能缓存机制

## 🔗 集成说明

### TradeMaster集成
本项目通过HTTP API与现有的TradeMaster Flask服务集成：
- 策略训练和测试
- 数据处理和分析
- 市场动态建模
- 结果获取和报告生成

### 扩展支持
- **FinAgent** - 智能代理集成
- **EarnMore** - 收益优化平台
- **外部数据源** - 支持多种数据提供商

## 🛡️ 安全最佳实践

1. **认证和授权**
   - 使用强随机密钥签名JWT
   - 实施适当的令牌过期策略
   - 基于角色的权限控制

2. **数据保护**
   - 敏感数据加密存储
   - HTTPS传输加密
   - 输入验证和清理

3. **API安全**
   - 实施速率限制
   - 请求大小限制
   - CORS策略配置

## 📈 性能优化

1. **数据库优化**
   - 适当的索引策略
   - 连接池配置
   - 查询优化

2. **缓存策略**
   - Redis缓存热点数据
   - API响应缓存
   - 数据库查询缓存

3. **异步处理**
   - 长时间任务异步化
   - 批量操作优化
   - 并发控制

## 🐛 故障排除

### 常见问题

1. **数据库连接失败**
   ```bash
   # 检查数据库服务状态
   sudo systemctl status postgresql
   
   # 检查连接配置
   echo $DATABASE_URL
   ```

2. **Redis连接失败**
   ```bash
   # 检查Redis服务
   redis-cli ping
   
   # 检查配置
   echo $REDIS_URL
   ```

3. **TradeMaster集成失败**
   ```bash
   # 检查TradeMaster服务
   curl http://localhost:8080/health
   
   # 检查日志
   tail -f logs/app.log
   ```

### 日志分析
```bash
# 查看实时日志
tail -f logs/app.log

# 查看错误日志
grep "ERROR" logs/app.log

# 查看特定用户的操作日志
grep "user_id:123" logs/app.log
```

## 📞 支持和贡献

### 问题反馈
- 通过GitHub Issues报告问题
- 提供详细的错误信息和复现步骤
- 包含相关的日志和配置信息

### 贡献指南
1. Fork项目
2. 创建功能分支
3. 提交更改
4. 创建Pull Request

### 联系信息
- **项目主页**: https://github.com/TradeMaster-NTU/TradeMaster
- **文档网站**: https://trademaster.ai/docs
- **邮件联系**: contact@trademaster.ai

---

## 📄 许可证

本项目采用MIT许可证，详见LICENSE文件。

---

**TradeMaster Web Interface Backend** - 现代化量化交易平台的Web后端服务 🚀