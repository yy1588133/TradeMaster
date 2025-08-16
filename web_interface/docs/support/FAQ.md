# 常见问题解答 (FAQ)

本文档收集了用户在使用TradeMaster Web Interface过程中最常遇到的问题和解决方案。我们根据问题类型进行分类，帮助您快速找到所需答案。

## 📋 目录

- [账户相关问题](#账户相关问题)
- [登录认证问题](#登录认证问题)  
- [策略管理问题](#策略管理问题)
- [数据相关问题](#数据相关问题)
- [模型训练问题](#模型训练问题)
- [分析报告问题](#分析报告问题)
- [系统性能问题](#系统性能问题)
- [API接口问题](#api接口问题)
- [部署安装问题](#部署安装问题)
- [浏览器兼容性问题](#浏览器兼容性问题)

---

## 账户相关问题

### Q1: 如何注册新账户？
**A:** 目前系统采用邀请制注册，您需要：
1. 联系管理员获取邀请码
2. 访问注册页面：`/register`
3. 填写必要信息和邀请码
4. 验证邮箱完成注册

**相关文档：** [新手入门指南](../user-guide/getting-started.md#用户注册)

### Q2: 忘记密码怎么办？
**A:** 密码重置步骤：
```
步骤1: 访问登录页面
步骤2: 点击"忘记密码"链接
步骤3: 输入注册邮箱地址
步骤4: 检查邮箱重置链接
步骤5: 设置新密码
```

**注意事项：**
- 重置链接有效期为24小时
- 新密码需包含大小写字母、数字和特殊字符
- 重置后建议立即登录测试

### Q3: 如何修改个人信息？
**A:** 个人信息修改路径：
1. 登录后点击右上角头像
2. 选择"个人设置"
3. 修改相应信息字段
4. 点击"保存修改"

**可修改项目：**
- 用户名（仅限一次）
- 邮箱地址（需邮箱验证）
- 手机号码
- 个人简介
- 头像图片

### Q4: 如何注销账户？
**A:** 账户注销流程：
```
警告：账户注销后数据无法恢复！

流程：
1. 备份重要数据
2. 联系客服申请注销
3. 填写注销申请表
4. 等待审核确认
5. 完成账户注销
```

**注销影响：**
- 所有个人数据将被永久删除
- 创建的策略和模型将被清理
- 历史交易记录将被移除
- API密钥将失效

---

## 登录认证问题

### Q5: 登录后显示"权限不足"？
**A:** 可能原因和解决方案：

**原因1：账户未激活**
```
解决方案：
- 检查注册邮箱激活链接
- 联系管理员手动激活
- 重新发送激活邮件
```

**原因2：权限角色问题**
```
解决方案：
- 确认当前用户角色
- 联系管理员分配权限
- 查看功能权限要求
```

**原因3：会话过期**
```
解决方案：
- 退出后重新登录
- 清除浏览器缓存
- 检查系统时间设置
```

### Q6: 为什么总是要求重新登录？
**A:** 自动登出原因分析：

**常见原因：**
- 会话超时（默认24小时）
- 多地点登录冲突
- 浏览器Cookie设置问题
- 系统安全策略触发

**解决方案：**
```yaml
会话设置优化:
1. 勾选"记住我"选项
2. 浏览器允许Cookie
3. 关闭无痕浏览模式
4. 定期清理浏览器缓存

安全设置调整:
1. 检查IP白名单设置
2. 确认设备信任状态
3. 关闭异地登录保护
4. 联系管理员调整策略
```

### Q7: 双因素认证如何设置？
**A:** 2FA设置步骤：

**启用2FA：**
```
步骤1: 进入安全设置页面
步骤2: 选择"启用双因素认证"
步骤3: 下载认证应用（推荐Google Authenticator）
步骤4: 扫描二维码
步骤5: 输入验证码确认
步骤6: 保存备用恢复码
```

**推荐认证应用：**
- Google Authenticator
- Microsoft Authenticator
- Authy
- 1Password

### Q8: API密钥如何管理？
**A:** API密钥管理指南：

**创建API密钥：**
```
步骤1: 访问开发者设置
步骤2: 点击"创建新密钥"
步骤3: 设置密钥名称和权限
步骤4: 复制并保存密钥
步骤5: 配置IP白名单（可选）
```

**安全建议：**
- 定期轮换API密钥（建议3个月）
- 为不同应用创建独立密钥
- 设置最小权限原则
- 及时删除不用的密钥
- 监控API调用日志

---

## 策略管理问题

### Q9: 策略上传失败怎么办？
**A:** 策略上传故障排查：

**检查文件格式：**
```python
# 支持的策略格式
支持格式: .py, .ipynb, .zip
文件大小: 最大50MB
编码格式: UTF-8

# 策略文件结构示例
strategy_example.py:
```
```python
class MyStrategy:
    def __init__(self):
        pass
    
    def trade_signal(self, data):
        # 策略逻辑
        return signal
```

**检查网络连接：**
```
测试方法：
1. 尝试上传小文件测试
2. 检查网络稳定性
3. 关闭VPN或代理
4. 使用有线网络连接
```

### Q10: 策略回测结果不准确？
**A:** 回测准确性检查：

**数据质量检查：**
```yaml
数据验证项:
- 数据完整性: 检查缺失值
- 数据准确性: 对比其他数据源
- 时间对齐: 确认时间戳正确
- 企业行动: 考虑分红送股影响
```

**参数设置检查：**
```yaml
回测参数:
- 起始资金: 确认初始资金设置
- 手续费率: 设置实际交易费用
- 滑点设置: 考虑市场冲击成本
- 基准对比: 选择合适基准指数
```

### Q11: 如何优化策略性能？
**A:** 策略性能优化建议：

**算法层面优化：**
```python
# 1. 向量化操作替代循环
# 慢速版本
for i in range(len(data)):
    result[i] = data[i] * factor

# 快速版本
result = data * factor

# 2. 使用缓存机制
from functools import lru_cache

@lru_cache(maxsize=1000)
def expensive_calculation(param):
    return complex_computation(param)

# 3. 批量数据处理
def batch_process(data_list, batch_size=1000):
    for i in range(0, len(data_list), batch_size):
        batch = data_list[i:i+batch_size]
        process_batch(batch)
```

**数据处理优化：**
- 使用高效的数据结构（如pandas DataFrame）
- 预处理数据减少重复计算
- 合理设置数据窗口大小
- 使用异步数据获取

---

## 数据相关问题

### Q12: 数据上传速度很慢？
**A:** 数据上传优化方法：

**网络优化：**
```yaml
网络设置:
1. 使用有线网络连接
2. 关闭其他下载任务
3. 选择网络较好的时间段
4. 考虑使用CDN加速
```

**文件优化：**
```yaml
文件处理:
1. 压缩数据文件（.zip, .gz）
2. 分批上传大文件
3. 删除不必要的列
4. 使用高效格式（如parquet）
```

**上传策略：**
```python
# 分块上传示例
def chunked_upload(file_path, chunk_size=1024*1024):
    with open(file_path, 'rb') as f:
        chunk_num = 0
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            upload_chunk(chunk, chunk_num)
            chunk_num += 1
```

### Q13: 数据格式不被支持？
**A:** 数据格式转换指南：

**支持的数据格式：**
```yaml
时序数据:
  - CSV (.csv)
  - Excel (.xlsx, .xls)
  - JSON (.json)
  - Parquet (.parquet)
  - HDF5 (.h5, .hdf5)

财务数据:
  - Yahoo Finance格式
  - Bloomberg格式
  - Wind数据格式
  - 通达信格式
```

**格式转换示例：**
```python
import pandas as pd

# Excel转CSV
df = pd.read_excel('data.xlsx')
df.to_csv('data.csv', index=False)

# JSON转CSV
df = pd.read_json('data.json')
df.to_csv('data.csv', index=False)

# 标准化日期格式
df['date'] = pd.to_datetime(df['date'])
df = df.set_index('date')
```

### Q14: 数据缺失值如何处理？
**A:** 缺失值处理策略：

**检测缺失值：**
```python
import pandas as pd
import numpy as np

# 检查缺失值
print(df.isnull().sum())
print(df.info())

# 可视化缺失值模式
import matplotlib.pyplot as plt
import seaborn as sns

plt.figure(figsize=(10, 6))
sns.heatmap(df.isnull(), cbar=True, cmap='viridis')
plt.title('Missing Values Heatmap')
plt.show()
```

**处理策略：**
```python
# 1. 删除缺失值
df_cleaned = df.dropna()

# 2. 前向填充
df_filled = df.fillna(method='ffill')

# 3. 插值填充
df_interpolated = df.interpolate(method='linear')

# 4. 均值填充
df_mean_filled = df.fillna(df.mean())

# 5. 自定义填充
df_custom = df.fillna({
    'price': df['price'].median(),
    'volume': 0,
    'returns': df['returns'].mean()
})
```

---

## 模型训练问题

### Q15: 模型训练时间过长？
**A:** 训练时间优化方案：

**硬件优化：**
```yaml
计算资源:
1. 使用GPU加速训练
2. 增加内存分配
3. 使用SSD存储数据
4. 启用多核心并行
```

**算法优化：**
```python
# 1. 早停机制
from sklearn.model_selection import EarlyStopping

early_stopping = EarlyStopping(
    patience=10,
    restore_best_weights=True
)

# 2. 学习率调度
from tensorflow.keras.callbacks import ReduceLROnPlateau

lr_scheduler = ReduceLROnPlateau(
    factor=0.5,
    patience=5,
    min_lr=1e-7
)

# 3. 批量大小优化
batch_sizes = [32, 64, 128, 256]
for batch_size in batch_sizes:
    model.fit(X_train, y_train, batch_size=batch_size)
```

### Q16: 模型过拟合怎么办？
**A:** 过拟合解决方案：

**正则化技术：**
```python
# 1. L1/L2正则化
from tensorflow.keras.regularizers import l1, l2, l1_l2

model.add(Dense(64, 
    kernel_regularizer=l2(0.001),
    activity_regularizer=l1(0.001)
))

# 2. Dropout
from tensorflow.keras.layers import Dropout

model.add(Dropout(0.5))

# 3. 早停
early_stopping = EarlyStopping(
    monitor='val_loss',
    patience=10,
    restore_best_weights=True
)
```

**数据增强：**
```python
# 时序数据增强
def augment_time_series(data, noise_level=0.01):
    # 添加噪声
    noise = np.random.normal(0, noise_level, data.shape)
    augmented = data + noise
    
    # 时间扭曲
    from scipy.interpolate import interp1d
    stretch_factor = np.random.uniform(0.9, 1.1)
    new_indices = np.linspace(0, len(data)-1, 
                            int(len(data) * stretch_factor))
    f = interp1d(range(len(data)), data, kind='linear')
    stretched = f(new_indices)
    
    return augmented, stretched
```

### Q17: 模型预测准确率低？
**A:** 准确率提升策略：

**特征工程：**
```python
# 1. 技术指标
def add_technical_indicators(df):
    # 移动平均
    df['MA_5'] = df['close'].rolling(5).mean()
    df['MA_20'] = df['close'].rolling(20).mean()
    
    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD
    ema_12 = df['close'].ewm(span=12).mean()
    ema_26 = df['close'].ewm(span=26).mean()
    df['MACD'] = ema_12 - ema_26
    
    return df

# 2. 滞后特征
def add_lag_features(df, lags=[1, 2, 3, 5]):
    for lag in lags:
        df[f'close_lag_{lag}'] = df['close'].shift(lag)
        df[f'volume_lag_{lag}'] = df['volume'].shift(lag)
    return df
```

**模型集成：**
```python
# 模型融合
from sklearn.ensemble import VotingClassifier

# 创建基础模型
rf_model = RandomForestClassifier(n_estimators=100)
svm_model = SVC(probability=True)
lr_model = LogisticRegression()

# 投票集成
voting_model = VotingClassifier(
    estimators=[
        ('rf', rf_model),
        ('svm', svm_model),
        ('lr', lr_model)
    ],
    voting='soft'
)

# 训练集成模型
voting_model.fit(X_train, y_train)
```

---

## 分析报告问题

### Q18: 报告生成失败？
**A:** 报告生成故障排查：

**权限检查：**
```yaml
权限要求:
- 报告生成权限: Analyst角色或以上
- 数据访问权限: 相关数据集读取权限
- 存储权限: 报告保存目录写入权限
```

**资源检查：**
```yaml
系统资源:
- 内存使用: 确保足够内存空间
- 磁盘空间: 检查临时文件空间
- CPU负载: 避免高峰期生成报告
- 网络连接: 确保稳定网络连接
```

**数据检查：**
```python
# 数据完整性检查
def validate_data_for_report(df):
    checks = {
        'empty_data': len(df) == 0,
        'missing_columns': set(['date', 'close', 'volume']) - set(df.columns),
        'null_values': df.isnull().sum().sum() > len(df) * 0.5,
        'date_range': df.index.max() - df.index.min() < pd.Timedelta(days=30)
    }
    
    failed_checks = [k for k, v in checks.items() if v]
    if failed_checks:
        raise ValueError(f"Data validation failed: {failed_checks}")
    
    return True
```

### Q19: 报告导出格式问题？
**A:** 报告格式和导出选项：

**支持格式：**
```yaml
导出格式:
  PDF:
    - 高质量打印版本
    - 包含图表和表格
    - 支持书签导航
    - 文件大小较大
    
  Excel:
    - 多工作表结构
    - 原始数据包含
    - 公式和计算保留
    - 便于二次分析
    
  HTML:
    - 交互式图表
    - 响应式布局
    - 在线分享友好
    - 加载速度快
    
  Word:
    - 便于编辑修改
    - 格式化文档
    - 插入注释方便
    - 协作友好
```

**导出设置：**
```python
# 报告导出配置
export_config = {
    'format': 'pdf',  # pdf, excel, html, word
    'quality': 'high',  # low, medium, high
    'include_raw_data': True,
    'compress': False,
    'password_protect': False,
    'watermark': False
}

# 批量导出
formats = ['pdf', 'excel']
for fmt in formats:
    export_report(report_id, format=fmt)
```

### Q20: 报告图表显示异常？
**A:** 图表问题解决方案：

**浏览器兼容性：**
```yaml
推荐浏览器:
- Chrome: 版本80+
- Firefox: 版本75+  
- Safari: 版本13+
- Edge: 版本80+

避免使用:
- IE浏览器（不支持）
- 过旧版本浏览器
- 移动端浏览器（部分功能受限）
```

**图表渲染问题：**
```javascript
// 图表重新渲染
function refreshChart(chartId) {
    const chart = echarts.getInstanceByDom(
        document.getElementById(chartId)
    );
    if (chart) {
        chart.resize();
        chart.refresh();
    }
}

// 响应式图表
window.addEventListener('resize', function() {
    setTimeout(refreshChart, 100);
});
```

---

## 系统性能问题

### Q21: 页面加载缓慢？
**A:** 页面性能优化：

**浏览器优化：**
```yaml
浏览器设置:
1. 清除浏览器缓存和Cookie
2. 禁用不必要的浏览器扩展
3. 启用硬件加速
4. 关闭其他占用资源的标签页
```

**网络优化：**
```yaml
网络检查:
1. 测试网络连接速度
2. 检查DNS解析时间
3. 尝试不同网络环境
4. 使用网络加速工具
```

**系统优化：**
```python
# 前端性能监控
function measurePagePerformance() {
    const perfData = performance.getEntriesByType('navigation')[0];
    
    console.log({
        'DNS查询时间': perfData.domainLookupEnd - perfData.domainLookupStart,
        'TCP连接时间': perfData.connectEnd - perfData.connectStart,
        '请求响应时间': perfData.responseEnd - perfData.requestStart,
        'DOM加载时间': perfData.domContentLoadedEventEnd - perfData.navigationStart,
        '页面完全加载时间': perfData.loadEventEnd - perfData.navigationStart
    });
}
```

### Q22: 内存使用过高？
**A:** 内存优化策略：

**前端内存管理：**
```javascript
// 1. 及时清理事件监听器
function cleanup() {
    window.removeEventListener('resize', handleResize);
    document.removeEventListener('click', handleClick);
}

// 2. 清理定时器
clearInterval(intervalId);
clearTimeout(timeoutId);

// 3. 释放大对象引用
largeDataObject = null;

// 4. 使用WeakMap存储临时数据
const cache = new WeakMap();
```

**数据处理优化：**
```python
# 分批处理大数据集
def process_large_dataset(data, batch_size=1000):
    for i in range(0, len(data), batch_size):
        batch = data[i:i+batch_size]
        result = process_batch(batch)
        yield result
        
        # 强制垃圾回收
        import gc
        gc.collect()
```

---

## API接口问题

### Q23: API调用失败？
**A:** API问题诊断：

**认证问题：**
```python
# 检查API密钥
headers = {
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json'
}

# 测试API连接
import requests

def test_api_connection():
    try:
        response = requests.get(
            'https://api.trademaster.ai/v1/health',
            headers=headers,
            timeout=10
        )
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"API连接失败: {e}")
        return False
```

**请求格式检查：**
```python
# 正确的API请求格式
def make_api_request(endpoint, data=None):
    url = f"https://api.trademaster.ai/v1/{endpoint}"
    
    payload = {
        'timestamp': int(time.time()),
        'data': data
    }
    
    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=30
    )
    
    if response.status_code != 200:
        raise APIError(f"API请求失败: {response.text}")
    
    return response.json()
```

### Q24: API限流怎么处理？
**A:** 限流处理策略：

**限流检测：**
```python
import time
from functools import wraps

def rate_limit_handler(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                # 获取重试时间
                retry_after = int(e.response.headers.get('Retry-After', 60))
                print(f"API限流，等待{retry_after}秒后重试")
                time.sleep(retry_after)
                return func(*args, **kwargs)
            raise
    return wrapper
```

**请求优化：**
```python
# 批量请求
def batch_api_requests(endpoints, batch_size=5):
    results = []
    for i in range(0, len(endpoints), batch_size):
        batch = endpoints[i:i+batch_size]
        batch_results = []
        
        for endpoint in batch:
            result = make_api_request(endpoint)
            batch_results.append(result)
            time.sleep(0.1)  # 避免过快请求
        
        results.extend(batch_results)
        time.sleep(1)  # 批次间延迟
    
    return results
```

---

## 部署安装问题

### Q25: Docker部署失败？
**A:** Docker部署故障排查：

**环境检查：**
```bash
# 检查Docker版本
docker --version
docker-compose --version

# 检查Docker服务状态
sudo systemctl status docker

# 检查磁盘空间
df -h
docker system df
```

**常见错误解决：**
```yaml
错误类型:

端口冲突:
  错误: "Port already in use"
  解决: 
    - 检查端口占用: netstat -tlnp | grep :8000
    - 修改配置文件端口
    - 停止冲突服务

权限问题:
  错误: "Permission denied"
  解决:
    - 添加用户到docker组: sudo usermod -aG docker $USER
    - 使用sudo运行: sudo docker-compose up
    - 检查文件权限: chmod +x scripts/*

镜像拉取失败:
  错误: "Pull access denied"
  解决:
    - 配置镜像加速器
    - 检查网络连接
    - 使用本地构建: docker-compose build
```

### Q26: 数据库连接失败？
**A:** 数据库连接问题：

**连接检查：**
```python
# PostgreSQL连接测试
import psycopg2

def test_db_connection():
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="trademaster",
            user="postgres",
            password="password",
            port="5432"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"数据库连接成功: {version}")
        return True
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return False
    finally:
        if conn:
            conn.close()
```

**配置文件检查：**
```yaml
# 数据库配置示例
database:
  host: localhost
  port: 5432
  name: trademaster
  user: postgres
  password: your_password
  
# 连接池设置
connection_pool:
  min_connections: 5
  max_connections: 20
  timeout: 30
```

---

## 浏览器兼容性问题

### Q27: 浏览器不兼容？
**A:** 兼容性解决方案：

**支持的浏览器版本：**
```yaml
推荐浏览器:
  Chrome: 版本80+ ✅
  Firefox: 版本75+ ✅
  Safari: 版本13+ ✅
  Edge: 版本80+ ✅

不支持:
  IE浏览器: 任何版本 ❌
  Chrome: 版本70以下 ❌
  Firefox: 版本70以下 ❌
```

**兼容性检测：**
```javascript
// 浏览器兼容性检测
function checkBrowserCompatibility() {
    const userAgent = navigator.userAgent;
    const checks = {
        es6Support: typeof Symbol !== 'undefined',
        fetchSupport: typeof fetch !== 'undefined',
        promiseSupport: typeof Promise !== 'undefined',
        webSocketSupport: typeof WebSocket !== 'undefined'
    };
    
    const unsupportedFeatures = Object.keys(checks)
        .filter(key => !checks[key]);
    
    if (unsupportedFeatures.length > 0) {
        alert(`您的浏览器不支持以下功能：${unsupportedFeatures.join(', ')}\n请升级到最新版本的Chrome、Firefox或Safari浏览器。`);
    }
}
```

### Q28: 移动端显示问题？
**A:** 移动端适配：

**响应式设计检查：**
```css
/* 移动端适配样式 */
@media (max-width: 768px) {
    .container {
        padding: 10px;
        font-size: 14px;
    }
    
    .table-responsive {
        overflow-x: auto;
    }
    
    .btn {
        width: 100%;
        margin-bottom: 10px;
    }
}

/* 触摸友好的按钮大小 */
.touch-friendly {
    min-height: 44px;
    min-width: 44px;
}
```

**移动端优化建议：**
```yaml
使用建议:
1. 使用桌面版浏览器获得最佳体验
2. 移动端建议使用Chrome或Safari
3. 开启桌面版网站模式
4. 横屏使用以获得更好的显示效果

功能限制:
- 复杂图表可能显示不完整
- 文件上传功能受限
- 某些交互功能简化
- 报告导出功能受限
```

---

## 🔍 问题提交指南

如果以上FAQ没有解决您的问题，请按以下格式提交问题：

```yaml
问题标题: [简洁描述问题]

问题描述:
- 具体问题现象
- 预期结果 vs 实际结果
- 问题出现频率

环境信息:
- 操作系统: Windows 10/macOS/Linux
- 浏览器: Chrome 91.0.4472.124
- 账户类型: Admin/User/Analyst/Viewer
- 系统版本: v1.0.0

重现步骤:
1. 打开页面...
2. 点击按钮...
3. 输入数据...
4. 出现错误...

错误信息:
[复制完整错误信息]

已尝试解决方案:
- 清除浏览器缓存 ✅
- 重新登录 ✅
- 尝试其他浏览器 ❌

附件:
- 错误截图
- 控制台日志
- 相关文件
```

## 📞 获取更多帮助

- 📧 **邮箱支持**: support@trademaster.ai
- 💬 **在线客服**: 点击右下角聊天图标  
- 📞 **技术热线**: 400-xxx-xxxx
- 🎫 **工单系统**: https://support.trademaster.ai
- 📖 **用户手册**: [完整用户指南](../user-guide/README.md)

---

📅 **最后更新**：2025年8月15日  
📝 **文档版本**：v1.0.0  
👥 **维护团队**：TradeMaster技术支持团队