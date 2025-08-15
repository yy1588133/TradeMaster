# TradeMaster Docker 快速参考

## 🚀 快速启动

```bash
# 启动容器
start-container.bat

# 进入容器
enter-container.bat

# 停止容器
stop-container.bat
```

## 📋 容器信息

| 项目 | 值 |
|------|-----|
| 容器名称 | `trademaster-container` |
| 镜像 | `trademaster:latest` |
| 状态 | ✅ 运行中 |

## 🌐 访问端口

| 服务 | 本地端口 | 容器端口 | URL |
|------|---------|---------|-----|
| Web服务 | 8080 | 8080 | http://localhost:8080 |
| Jupyter | 8888 | 8888 | http://localhost:8888 |
| API服务 | 5001 | 5000 | http://localhost:5001 |

## 📁 路径映射

| 本地路径 | 容器路径 | 用途 |
|---------|---------|------|
| `./data` | `/app/data` | 数据存储 |
| `.` | `/workspace` | 项目文件 |

## 🔧 常用命令

### 容器管理
```bash
# 查看运行状态
docker ps

# 查看所有容器
docker ps -a

# 查看日志
docker logs trademaster-container

# 重启容器
docker restart trademaster-container
```

### Python测试
```bash
# 进入容器后执行
python3 -c "import trademaster; print('✅ TradeMaster可用')"
python3 -c "import torch; print('✅ PyTorch版本:', torch.__version__)"
```

## 🛠️ 管理脚本

- **`manage-container.bat`** - 综合管理界面（推荐）
- **`start-container.bat`** - 启动容器
- **`stop-container.bat`** - 停止容器  
- **`enter-container.bat`** - 进入容器

## ⚡ 测试结果

### ✅ 已验证功能
- [x] Python 3.8.10 环境
- [x] TradeMaster模块导入
- [x] PyTorch 1.12.1+cpu
- [x] NumPy 1.21.6
- [x] Pandas 2.0.3
- [x] 数据卷挂载
- [x] 端口映射
- [x] 自动重启

### 🔧 环境详情
- **操作系统**: Ubuntu 20.04 (容器内)
- **Python**: 3.8.10
- **虚拟环境**: `/opt/trademaster-env`
- **工作目录**: `/workspace`
- **PYTHONPATH**: `/home/TradeMaster`

## 🆘 故障排除

### 常见问题
1. **端口被占用**: 修改端口映射
2. **容器无法启动**: 检查Docker Desktop
3. **模块导入失败**: 重新构建镜像

### 获取帮助
1. 查看 `DOCKER_SETUP.md` 详细文档
2. 运行 `manage-container.bat` 获取管理界面
3. 使用 `docker logs trademaster-container` 查看错误

---
**状态**: ✅ 配置完成 | **更新时间**: 2025-08-15