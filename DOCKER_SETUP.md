# TradeMaster Docker 容器配置指南

## 概述

本文档记录了TradeMaster项目的Docker容器完整配置过程，包括容器创建、配置、管理和使用说明。

## 系统要求

- Windows 10/11
- Docker Desktop for Windows
- 至少8GB RAM
- 至少10GB可用磁盘空间

## 容器配置详情

### 镜像信息
- **镜像名称**: `trademaster:latest`
- **基础镜像**: Ubuntu 20.04
- **Python版本**: 3.8.10
- **镜像大小**: 5.47GB

### 容器配置
- **容器名称**: `trademaster-container`
- **重启策略**: `unless-stopped`
- **工作目录**: `/workspace` (映射到本地项目目录)

### 端口映射
| 本地端口 | 容器端口 | 用途 |
|---------|---------|------|
| 8080 | 8080 | Web服务 |
| 8888 | 8888 | Jupyter Notebook |
| 5001 | 5000 | API服务 |

### 数据卷挂载
| 本地路径 | 容器路径 | 用途 |
|---------|---------|------|
| `./data` | `/app/data` | 数据持久化 |
| `.` | `/workspace` | 项目文件访问 |

## 管理脚本

### 基础脚本

1. **start-container.bat** - 启动容器
   ```bash
   # 完整的容器启动命令
   docker run -d \
     --name trademaster-container \
     -p 8080:8080 \
     -p 8888:8888 \
     -p 5001:5000 \
     -v "%CD%\data:/app/data" \
     -v "%CD%:/workspace" \
     --restart unless-stopped \
     trademaster:latest tail -f /dev/null
   ```

2. **stop-container.bat** - 停止并删除容器

3. **enter-container.bat** - 进入容器交互式shell

4. **manage-container.bat** - 综合管理界面

### 使用方法

#### 快速启动
1. 双击 `start-container.bat`
2. 等待容器启动完成
3. 使用 `enter-container.bat` 进入容器

#### 综合管理
1. 双击 `manage-container.bat`
2. 根据菜单选择相应操作

## 测试验证

### 1. Python环境测试
```bash
docker exec trademaster-container python3 -c "import sys; print('Python version:', sys.version)"
```

**期望输出**:
```
Python version: 3.8.10 (default, Mar 18 2025, 20:04:55) 
[GCC 9.4.0]
```

### 2. TradeMaster模块测试
```bash
docker exec trademaster-container python3 -c "import trademaster; print('TradeMaster模块导入成功')"
```

**期望输出**:
```
TradeMaster模块导入成功
```

### 3. 数据访问测试
```bash
docker exec trademaster-container ls -la /app/data
docker exec trademaster-container ls -la /workspace/data
```

**期望结果**: 两个目录内容相同，包含以下子目录：
- algorithmic_trading
- high_frequency_trading
- market_dynamics_modeling
- order_execution
- portfolio_management

## 容器管理操作

### 查看容器状态
```bash
docker ps
docker ps -a  # 包含已停止的容器
```

### 查看容器日志
```bash
docker logs trademaster-container
docker logs -f trademaster-container  # 实时日志
```

### 重启容器
```bash
docker restart trademaster-container
```

### 进入容器
```bash
docker exec -it trademaster-container bash
```

### 停止容器
```bash
docker stop trademaster-container
```

### 删除容器
```bash
docker rm trademaster-container
docker rm -f trademaster-container  # 强制删除
```

## 网络访问

### Web服务
- URL: http://localhost:8080
- 用途: TradeMaster Web界面（如果可用）

### Jupyter Notebook
- URL: http://localhost:8888
- 用途: 交互式Python开发环境

### API服务
- URL: http://localhost:5001
- 用途: REST API接口

## 故障排除

### 常见问题

1. **端口被占用**
   ```
   Error: failed to bind host port for 0.0.0.0:5000:172.17.0.3:5000/tcp: address already in use
   ```
   **解决方案**: 修改端口映射，使用其他可用端口

2. **容器无法启动**
   - 检查Docker Desktop是否运行
   - 检查镜像是否存在: `docker images | grep trademaster`
   - 查看错误日志: `docker logs trademaster-container`

3. **数据卷挂载失败**
   - 确保本地路径存在
   - 检查Docker Desktop的文件共享设置
   - 使用绝对路径替代相对路径

### 调试命令

```bash
# 检查Docker状态
docker version
docker info

# 检查镜像
docker images

# 检查容器
docker ps -a

# 检查网络
docker network ls

# 检查数据卷
docker volume ls
```

## 配置过程记录

### 已解决的问题

1. **初始容器启动失败**
   - **问题**: 容器启动后立即重启
   - **原因**: 默认命令执行完毕后容器退出
   - **解决方案**: 使用 `tail -f /dev/null` 保持容器运行

2. **端口冲突**
   - **问题**: 5000端口已被占用
   - **解决方案**: 映射到5001端口

3. **数据卷权限**
   - **问题**: 数据卷挂载成功，权限正常
   - **状态**: 已验证

## 最佳实践

### 安全建议
1. 不要在生产环境中使用默认配置
2. 定期更新镜像和依赖
3. 使用专用网络隔离容器
4. 设置适当的资源限制

### 性能优化
1. 使用SSD存储挂载的数据卷
2. 根据需要调整内存限制
3. 定期清理未使用的镜像和容器

### 备份策略
1. 定期备份挂载的数据目录
2. 导出重要的容器配置
3. 保存自定义的环境变量设置

## 更新和维护

### 更新镜像
```bash
# 停止现有容器
docker stop trademaster-container
docker rm trademaster-container

# 拉取新镜像（如果有）
docker pull trademaster:latest

# 重新启动容器
start-container.bat
```

### 清理系统
```bash
# 清理未使用的镜像
docker image prune

# 清理停止的容器
docker container prune

# 清理未使用的网络
docker network prune
```

## 支持和联系

如遇到问题，请：
1. 查看本文档的故障排除部分
2. 检查Docker官方文档
3. 联系TradeMaster项目维护者

---

**配置完成时间**: 2025年8月15日  
**容器版本**: trademaster:latest  
**配置状态**: ✅ 已完成并测试通过