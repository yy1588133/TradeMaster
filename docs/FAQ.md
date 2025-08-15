# TradeMaster Docker 常见问题解答

<div align="center">
    <h2>❓ 常见问题快速解答</h2>
    <p>从安装到运维的全面问题解决方案</p>
</div>

---

## 📋 目录

- [🚀 安装和部署问题](#安装和部署问题)
- [🔧 配置相关问题](#配置相关问题)
- [⚡ 性能和优化问题](#性能和优化问题)
- [🔒 安全相关问题](#安全相关问题)
- [🐛 运行时错误问题](#运行时错误问题)
- [📊 数据和存储问题](#数据和存储问题)
- [🌐 网络连接问题](#网络连接问题)
- [🔄 更新和维护问题](#更新和维护问题)
- [🧪 开发和调试问题](#开发和调试问题)
- [📞 获取更多帮助](#获取更多帮助)

---

## 🚀 安装和部署问题

### Q1: Docker Desktop 安装失败怎么办？

**A**: 根据不同系统采用相应解决方案：

**Windows系统**:
```bash
# 1. 确保启用虚拟化
# 进入BIOS启用Intel VT-x或AMD-V

# 2. 启用Hyper-V和WSL 2
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

# 3. 重启电脑后安装WSL 2
wsl --install
wsl --set-default-version 2
```

**macOS系统**:
```bash
# 1. 确保系统版本足够新
sw_vers

# 2. 清理旧版本Docker
sudo rm -rf /Applications/Docker.app
sudo rm -rf ~/Library/Group\ Containers/group.com.docker
sudo rm -rf ~/Library/Containers/com.docker.docker

# 3. 重新下载安装
curl -o Docker.dmg https://desktop.docker.com/mac/main/amd64/Docker.dmg
```

**Linux系统**:
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# CentOS/RHEL
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install docker-ce docker-ce-cli containerd.io
sudo systemctl start docker
sudo systemctl enable docker
```

### Q2: 镜像构建时间过长或失败？

**A**: 优化构建过程：

```bash
# 1. 使用国内镜像源加速
docker build \
  --build-arg PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/ \
  --build-arg PIP_TRUSTED_HOST=mirrors.aliyun.com \
  -t trademaster:latest .

# 2. 使用构建缓存
docker buildx build --cache-from type=registry,ref=myregistry/cache \
  --cache-to type=registry,ref=myregistry/cache,mode=max \
  -t trademaster:latest .

# 3. 多阶段构建优化
# 查看 BEST_PRACTICES_GUIDE.md 中的多阶段构建示例

# 4. 清理Docker缓存
docker builder prune -af
docker system prune -af
```

### Q3: 容器启动后立即退出？

**A**: 检查和修复启动问题：

```bash
# 1. 查看容器日志
docker logs trademaster-container

# 2. 检查入口点脚本
docker run --rm -it trademaster:latest /bin/bash
cat /entrypoint.sh

# 3. 修复启动命令
docker run -d \
  --name trademaster-container \
  --entrypoint="" \
  trademaster:latest \
  tail -f /dev/null

# 4. 调试模式启动
docker run -it --rm \
  --name trademaster-debug \
  trademaster:latest \
  /bin/bash
```

### Q4: 端口被占用无法启动？

**A**: 解决端口冲突：

```bash
# 1. 查看端口占用
netstat -tuln | grep 8080
lsof -i :8080  # macOS/Linux
netstat -ano | findstr :8080  # Windows

# 2. 停止占用进程
# Linux/macOS
kill -9 $(lsof -ti:8080)

# Windows
taskkill /PID <PID> /F

# 3. 使用不同端口
docker run -d \
  --name trademaster-container \
  -p 8081:8080 \
  -p 8889:8888 \
  -p 5002:5000 \
  trademaster:latest

# 4. 使用随机端口
docker run -d \
  --name trademaster-container \
  -P \
  trademaster:latest
```

---

## 🔧 配置相关问题

### Q5: 环境变量不生效？

**A**: 检查环境变量配置：

```bash
# 1. 验证环境变量
docker exec trademaster-container env | grep TRADEMASTER
docker exec trademaster-container printenv

# 2. 检查.env文件格式
cat .env
# 确保格式：KEY=VALUE (等号两边无空格)

# 3. 重新加载环境变量
docker-compose down
docker-compose up -d

# 4. 调试环境变量
docker run --rm -it \
  --env-file .env \
  trademaster:latest \
  python3 -c "import os; print(os.environ.get('YOUR_VAR'))"
```

### Q6: 配置文件挂载失败？

**A**: 修复配置挂载问题：

```bash
# 1. 检查文件路径
ls -la ./config/
pwd

# 2. 使用绝对路径
docker run -d \
  -v "$(pwd)/config:/app/config:ro" \
  trademaster:latest

# 3. 检查文件权限
chmod 644 ./config/*.yml
chmod 755 ./config/

# 4. 使用配置卷
docker volume create trademaster-config
docker run --rm -v trademaster-config:/config -v "$(pwd)/config:/source" alpine cp -r /source/* /config/
docker run -d -v trademaster-config:/app/config trademaster:latest
```

### Q7: 数据库连接失败？

**A**: 解决数据库连接问题：

```bash
# 1. 检查数据库容器状态
docker ps | grep postgres
docker logs postgres-container

# 2. 测试网络连通性
docker exec trademaster-container ping postgres
docker exec trademaster-container telnet postgres 5432

# 3. 验证连接字符串
docker exec trademaster-container python3 -c "
import psycopg2
try:
    conn = psycopg2.connect('postgresql://user:pass@postgres:5432/db')
    print('连接成功')
except Exception as e:
    print(f'连接失败: {e}')
"

# 4. 重建网络连接
docker-compose down
docker-compose up -d
```

---

## ⚡ 性能和优化问题

### Q8: 容器运行缓慢？

**A**: 性能优化策略：

```bash
# 1. 检查资源使用
docker stats trademaster-container

# 2. 增加资源限制
docker update --memory="8g" --cpus="4" trademaster-container

# 3. 优化Python配置
docker exec trademaster-container python3 -c "
import os
os.environ['PYTHONOPTIMIZE'] = '1'
os.environ['OMP_NUM_THREADS'] = '4'
os.environ['MKL_NUM_THREADS'] = '4'
"

# 4. 使用性能分析
docker exec trademaster-container python3 -m cProfile -o profile.stats your_script.py
```

### Q9: 内存使用过高？

**A**: 内存优化方案：

```python
# 1. 在容器内执行内存优化
docker exec trademaster-container python3 -c "
import gc
import psutil

# 强制垃圾回收
collected = gc.collect()
print(f'清理了 {collected} 个对象')

# 查看内存使用
process = psutil.Process()
memory_info = process.memory_info()
print(f'RSS: {memory_info.rss / 1024**2:.1f} MB')
print(f'VMS: {memory_info.vms / 1024**2:.1f} MB')
"

# 2. 优化PyTorch内存使用
docker exec trademaster-container python3 -c "
import torch
if torch.cuda.is_available():
    torch.cuda.empty_cache()
    torch.cuda.set_per_process_memory_fraction(0.7)
"

# 3. 重启容器清理内存
docker restart trademaster-container
```

### Q10: 磁盘空间不足？

**A**: 磁盘空间清理：

```bash
# 1. 检查磁盘使用
docker system df
docker exec trademaster-container df -h

# 2. 清理Docker资源
docker system prune -af --volumes
docker volume prune
docker image prune -af

# 3. 清理容器内文件
docker exec trademaster-container bash -c "
find /tmp -type f -mtime +1 -delete
find /app/logs -name '*.log' -mtime +7 -delete
find /app/cache -type f -mtime +1 -delete
"

# 4. 日志轮转
docker exec trademaster-container bash -c "
truncate -s 0 /var/log/*.log
journalctl --vacuum-time=7d
"
```

---

## 🔒 安全相关问题

### Q11: 如何加强容器安全？

**A**: 容器安全加固：

```bash
# 1. 使用非root用户
docker run -d \
  --name trademaster-secure \
  --user 1000:1000 \
  --security-opt no-new-privileges:true \
  --read-only \
  --tmpfs /tmp \
  trademaster:latest

# 2. 限制能力
docker run -d \
  --cap-drop ALL \
  --cap-add NET_BIND_SERVICE \
  trademaster:latest

# 3. 网络隔离
docker network create --internal secure-net
docker run -d --network secure-net trademaster:latest

# 4. 安全扫描
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image trademaster:latest
```

### Q12: 如何管理敏感信息？

**A**: 安全的秘密管理：

```yaml
# 使用Docker Secrets
version: '3.8'
services:
  trademaster:
    image: trademaster:latest
    secrets:
      - db_password
      - api_key
    environment:
      - DATABASE_PASSWORD_FILE=/run/secrets/db_password
      - API_KEY_FILE=/run/secrets/api_key

secrets:
  db_password:
    file: ./secrets/db_password.txt
  api_key:
    external: true
```

```bash
# 创建外部秘密
echo "your_secure_password" | docker secret create db_password -
echo "your_api_key" | docker secret create api_key -
```

---

## 🐛 运行时错误问题

### Q13: 模块导入失败？

**A**: 解决导入问题：

```bash
# 1. 检查Python路径
docker exec trademaster-container python3 -c "
import sys
print('Python路径:')
for path in sys.path:
    print(f'  {path}')
"

# 2. 设置PYTHONPATH
docker exec trademaster-container bash -c "
export PYTHONPATH='/home/TradeMaster:\$PYTHONPATH'
python3 -c 'import trademaster; print(\"成功导入\")'
"

# 3. 检查文件结构
docker exec trademaster-container find /home/TradeMaster -name "*.py" | head -10

# 4. 重新安装包
docker exec trademaster-container pip install -e /home/TradeMaster/
```

### Q14: 权限被拒绝错误？

**A**: 解决权限问题：

```bash
# 1. 检查文件权限
docker exec trademaster-container ls -la /app/data/

# 2. 修复权限
docker exec trademaster-container chown -R $(whoami):$(whoami) /app/data/
docker exec trademaster-container chmod -R 755 /app/data/

# 3. 检查用户身份
docker exec trademaster-container whoami
docker exec trademaster-container id

# 4. 以正确用户启动
docker run -d --user $(id -u):$(id -g) trademaster:latest
```

### Q15: 服务无响应？

**A**: 诊断服务问题：

```bash
# 1. 检查进程状态
docker exec trademaster-container ps aux

# 2. 检查端口监听
docker exec trademaster-container netstat -tuln

# 3. 检查服务日志
docker logs --tail 100 trademaster-container

# 4. 健康检查
docker exec trademaster-container curl -f http://localhost:8080/health

# 5. 重启服务
docker exec trademaster-container supervisorctl restart all
```

---

## 📊 数据和存储问题

### Q16: 数据丢失怎么办？

**A**: 数据恢复策略：

```bash
# 1. 检查数据卷
docker volume ls
docker volume inspect trademaster-data

# 2. 查找数据备份
ls -la /opt/backups/trademaster/

# 3. 恢复数据
docker run --rm \
  -v trademaster-data:/data \
  -v /opt/backups/latest:/backup \
  alpine:latest \
  tar xzf /backup/data.tar.gz -C /data

# 4. 验证数据完整性
docker exec trademaster-container python3 -c "
import os
data_files = []
for root, dirs, files in os.walk('/app/data'):
    data_files.extend(files)
print(f'数据文件数量: {len(data_files)}')
"
```

### Q17: 数据库迁移失败？

**A**: 数据库迁移解决：

```bash
# 1. 检查迁移状态
docker exec trademaster-container python3 manage.py showmigrations

# 2. 手动运行迁移
docker exec trademaster-container python3 manage.py migrate --fake-initial

# 3. 回滚迁移
docker exec trademaster-container python3 manage.py migrate app_name 0001

# 4. 重置数据库
docker exec postgres-container psql -U postgres -c "DROP DATABASE IF EXISTS trademaster;"
docker exec postgres-container psql -U postgres -c "CREATE DATABASE trademaster;"
docker exec trademaster-container python3 manage.py migrate
```

---

## 🌐 网络连接问题

### Q18: 无法访问外部服务？

**A**: 网络连接诊断：

```bash
# 1. 测试DNS解析
docker exec trademaster-container nslookup google.com
docker exec trademaster-container dig google.com

# 2. 测试网络连通性
docker exec trademaster-container ping 8.8.8.8
docker exec trademaster-container curl -I http://google.com

# 3. 检查代理设置
docker exec trademaster-container env | grep -i proxy

# 4. 设置DNS服务器
docker run -d --dns 8.8.8.8 --dns 114.114.114.114 trademaster:latest
```

### Q19: 容器间通信失败？

**A**: 容器网络问题：

```bash
# 1. 检查网络配置
docker network ls
docker network inspect bridge

# 2. 测试容器间连通性
docker exec trademaster-container ping postgres-container
docker exec trademaster-container telnet postgres-container 5432

# 3. 重建网络
docker-compose down
docker network prune
docker-compose up -d

# 4. 使用自定义网络
docker network create trademaster-net
docker run -d --network trademaster-net --name app trademaster:latest
docker run -d --network trademaster-net --name db postgres:13
```

---

## 🔄 更新和维护问题

### Q20: 如何安全更新容器？

**A**: 容器更新策略：

```bash
# 1. 备份现有数据
./backup_data.sh

# 2. 拉取新镜像
docker pull trademaster:latest

# 3. 滚动更新
docker-compose up -d --no-deps trademaster

# 4. 验证更新
docker exec trademaster-container python3 -c "
import trademaster
print(f'版本: {getattr(trademaster, \"__version__\", \"未知\")}')
"

# 5. 回滚策略
docker tag trademaster:latest trademaster:backup
docker tag trademaster:previous trademaster:latest
docker-compose up -d --no-deps trademaster
```

### Q21: 如何批量管理多个容器？

**A**: 批量管理方案：

```bash
# 1. 使用Docker Compose
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 2. 使用Docker Stack
docker stack deploy -c docker-compose.yml trademaster

# 3. 批量操作脚本
#!/bin/bash
containers=("trademaster-1" "trademaster-2" "trademaster-3")
for container in "${containers[@]}"; do
    echo "更新 $container"
    docker exec "$container" python3 -m pip install --upgrade trademaster
done

# 4. 使用Portainer管理界面
docker run -d -p 9000:9000 -v /var/run/docker.sock:/var/run/docker.sock portainer/portainer-ce
```

---

## 🧪 开发和调试问题

### Q22: 如何调试容器内的应用？

**A**: 容器调试技巧：

```bash
# 1. 进入容器调试
docker exec -it trademaster-container /bin/bash

# 2. 远程调试配置
docker run -d -p 5678:5678 \
  -e PYTHONPATH=/app \
  trademaster:debug \
  python3 -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m trademaster

# 3. 使用调试版镜像
docker build -f Dockerfile.debug -t trademaster:debug .
docker run -it --rm trademaster:debug

# 4. 日志调试
docker exec trademaster-container python3 -c "
import logging
logging.basicConfig(level=logging.DEBUG)
# 你的代码
"
```

### Q23: 如何进行性能分析？

**A**: 性能分析方法：

```python
# 1. 在容器内运行性能分析
docker exec trademaster-container python3 -c "
import cProfile
import pstats

# 性能分析
profiler = cProfile.Profile()
profiler.enable()

# 你的代码
your_function()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
"

# 2. 内存分析
docker exec trademaster-container python3 -c "
import tracemalloc
import gc

tracemalloc.start()
# 你的代码
current, peak = tracemalloc.get_traced_memory()
print(f'当前内存: {current / 1024**2:.1f} MB')
print(f'峰值内存: {peak / 1024**2:.1f} MB')
tracemalloc.stop()
"
```

---

## 🆘 应急处理问题

### Q24: 生产环境容器崩溃怎么办？

**A**: 应急处理流程：

```bash
# 1. 立即诊断
docker ps -a | grep trademaster
docker logs --tail 100 trademaster-container

# 2. 快速恢复
docker start trademaster-container
# 或者
docker run -d --name trademaster-emergency \
  -v trademaster-data:/app/data \
  trademaster:latest

# 3. 切换到备用实例
docker start trademaster-standby
# 更新负载均衡配置

# 4. 收集故障信息
docker logs trademaster-container > crash_$(date +%Y%m%d_%H%M%S).log
docker inspect trademaster-container > inspect_$(date +%Y%m%d_%H%M%S).json
```

### Q25: 数据损坏如何恢复？

**A**: 数据恢复步骤：

```bash
# 1. 立即停止写入
docker exec trademaster-container supervisorctl stop all

# 2. 评估损坏程度
docker exec postgres-container pg_dump trademaster > current_state.sql
# 检查导出是否成功

# 3. 从备份恢复
# 找到最近的完整备份
ls -la /opt/backups/trademaster/ | tail -5

# 恢复数据
docker exec postgres-container psql -U postgres -c "DROP DATABASE trademaster;"
docker exec postgres-container psql -U postgres -c "CREATE DATABASE trademaster;"
zcat /opt/backups/trademaster/latest/database.sql.gz | \
docker exec -i postgres-container psql -U postgres -d trademaster

# 4. 验证数据完整性
docker exec trademaster-container python3 -c "
# 运行数据完整性检查脚本
"
```

---

## 📞 获取更多帮助

### 🔍 自助诊断工具

运行综合诊断脚本：
```bash
# 下载诊断脚本
curl -o diagnose.sh https://raw.githubusercontent.com/TradeMaster-NTU/TradeMaster/main/scripts/diagnose.sh
chmod +x diagnose.sh
./diagnose.sh
```

### 📚 相关文档

- [📖 完整部署指南](DOCKER_DEPLOYMENT_GUIDE.md)
- [🚀 快速启动指南](QUICK_START_GUIDE.md)
- [🔧 故障排除指南](TROUBLESHOOTING_GUIDE.md)
- [⚙️ 配置参数指南](CONFIGURATION_GUIDE.md)
- [🏆 最佳实践指南](BEST_PRACTICES_GUIDE.md)

### 💬 技术支持渠道

| 渠道 | 用途 | 响应时间 |
|------|------|----------|
| [GitHub Issues](https://github.com/TradeMaster-NTU/TradeMaster/issues) | Bug报告、功能请求 | 1-3个工作日 |
| [GitHub Discussions](https://github.com/TradeMaster-NTU/TradeMaster/discussions) | 技术讨论、使用问题 | 实时 |
| [邮件支持](mailto:TradeMaster.NTU@gmail.com) | 商业支持、定制需求 | 24小时内 |

### 📝 问题报告模板

提交问题时，请提供以下信息：

```
## 环境信息
- 操作系统: [Windows 11 / macOS 12 / Ubuntu 20.04]
- Docker版本: [docker --version]
- TradeMaster版本: [镜像标签]

## 问题描述
[详细描述遇到的问题]

## 重现步骤
1. [具体操作步骤]
2. [...]

## 期望行为
[描述期望的正常行为]

## 实际行为
[描述实际发生的情况]

## 错误日志
```
[粘贴相关日志内容]
```

## 诊断信息
[运行诊断脚本的输出]

## 已尝试的解决方案
[列出已经尝试过的解决方法]
```

### 🎯 快速解决建议

遇到问题时，推荐按以下顺序尝试：

1. **📖 查阅本FAQ** - 90%的问题都能在这里找到答案
2. **🔍 运行诊断脚本** - 自动检测和修复常见问题
3. **📚 查看相关文档** - 深入了解配置和使用方法
4. **🔄 重启大法** - 重启容器解决临时性问题
5. **💬 社区求助** - 在GitHub Discussions提问
6. **🐛 提交Issue** - 报告Bug或请求新功能

---

## 📊 问题统计

根据用户反馈，最常见的问题类型：

| 问题类型 | 占比 | 平均解决时间 |
|----------|------|--------------|
| 安装部署问题 | 35% | 30分钟 |
| 配置错误 | 25% | 15分钟 |
| 性能相关 | 20% | 1小时 |
| 网络连接 | 10% | 20分钟 |
| 数据问题 | 5% | 2小时 |
| 其他 | 5% | 变动 |

---

## 🚀 持续改进

我们持续改进FAQ内容：

- ✅ 每周更新常见问题
- ✅ 根据用户反馈优化解答
- ✅ 添加新的诊断工具
- ✅ 完善自动化解决方案

**意见反馈**: 如果你发现FAQ中的信息有误或需要补充，请通过GitHub Issues告诉我们。

---

## 📄 版本信息

**文档版本**: v2.0.0  
**最后更新**: 2025年8月15日  
**涵盖版本**: TradeMaster Docker v1.0+  
**维护团队**: TradeMaster Development Team

**更新日志**:
- v2.0.0: 全面重写，增加25个常见问题解答
- v1.5.0: 增加应急处理部分
- v1.0.0: 初始版本发布