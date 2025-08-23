# 整合requirements文件执行计划

## 上下文
- **任务**: 整合web_interface/backend目录中的多个requirements文件为单一完整文件
- **目标**: 消除依赖管理混淆，提供统一的依赖安装方案
- **方案**: 基于requirements.txt整合，添加开发工具依赖

## 执行计划

### 步骤1：分析并整合requirements文件
- 以requirements.txt为基础模板
- 从requirements-dev.txt提取开发工具依赖
- 解决版本冲突（TensorFlow、numpy等）
- 保持清晰注释结构

### 步骤2：删除多余文件
- 删除requirements-dev.txt、requirements-prod.txt、requirements-minimal.txt
- 保留requirements-installed.flag

### 步骤3：安装完整依赖
- pip install -r requirements.txt
- 验证安装状态

### 步骤4：验证结果
- 测试关键包导入
- 验证应用启动
- 确认功能正常

## 预期结果
- 单一requirements.txt文件（约80-90行）
- 虚拟环境包含所有必要依赖
- 后端服务正常启动