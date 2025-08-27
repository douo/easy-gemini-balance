# 安装和使用说明

## 快速开始

### 1. 环境要求

- Python 3.8 或更高版本
- uv 包管理器（推荐）或 pip

### 2. 安装 uv（推荐）

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或者使用 pip 安装
pip install uv
```

### 3. 安装项目依赖

```bash
# 使用 uv 安装
uv sync

# 或者使用 pip 安装
pip install requests
```

### 4. 配置 API Keys

编辑 `keys.txt` 文件，添加你的 API keys：

```txt
# 每行一个 key，支持权重格式
your-api-key-1:2.0
your-api-key-2:1.5
your-api-key-3:1.0
```

### 5. 运行示例

```bash
# 使用 uv 运行
uv run example.py

# 或者直接运行
python3 example.py
```

## 详细使用说明

### 基本用法

```python
from src.easy_gemini_balance import KeyBalancer

# 创建均衡器实例
balancer = KeyBalancer(keys_file="keys.txt", cache_size=100)

# 获取单个 key
key = balancer.get_single_key()

# 获取多个 key
keys = balancer.get_keys(3)

# 使用 key 后更新状态
balancer.update_key_health(key, success=True)  # 成功
balancer.update_key_health(key, error_code=403)  # 错误
```

### 高级功能

```python
# 获取统计信息
stats = balancer.get_stats()
print(f"可用 key 数量: {stats['available_keys']}")

# 获取特定 key 信息
key_info = balancer.get_key_info("your-api-key")

# 重新加载 keys 文件
balancer.reload_keys()

# 重置所有权重
balancer.reset_all_weights()
```

## 故障排除

### 常见问题

1. **ModuleNotFoundError**: 确保在正确的目录下运行，或者将 `src` 目录添加到 Python 路径
2. **FileNotFoundError**: 检查 `keys.txt` 文件是否存在
3. **ImportError**: 确保已安装 `requests` 依赖

### 调试模式

运行测试脚本来验证安装：

```bash
python3 test_balancer.py
```

## 生产环境部署

### 1. 虚拟环境

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置文件

创建配置文件来管理不同环境的设置：

```python
# config.py
KEYS_FILE = "keys.txt"
CACHE_SIZE = 100
MIN_SELECTION_INTERVAL = 0.1
```

### 3. 日志记录

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 在代码中使用
logger.info("Key selected: %s", key)
```

## 性能优化

### 1. 缓存调优

- 根据 key 数量调整 `cache_size`
- 监控缓存命中率

### 2. 权重调整

- 根据 API 响应时间调整权重
- 定期重置权重以恢复性能

### 3. 并发控制

- 使用线程锁保护共享状态
- 实现异步 key 选择

## 监控和维护

### 1. 健康检查

```python
# 定期检查 key 健康状态
stats = balancer.get_stats()
if stats['available_keys'] < stats['total_keys'] * 0.5:
    logger.warning("Too many keys are unavailable")
```

### 2. 自动恢复

```python
# 定期重置权重
import schedule
import time

def reset_weights():
    balancer.reset_all_weights()

schedule.every().hour.do(reset_weights)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### 3. 指标收集

```python
# 收集性能指标
import time

start_time = time.time()
key = balancer.get_single_key()
selection_time = time.time() - start_time

# 记录选择时间
logger.info("Key selection took %.3f seconds", selection_time)
```
