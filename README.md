# Easy Gemini Balance

智能 API Key 管理和负载均衡工具，支持 Google Gemini API 的自动重试和健康监控。

## 特性

- 🔑 **智能 Key 管理**: LRU 缓存 + 权重分配
- 🔄 **自动重试**: 失败时自动切换 Key 并重试
- 📊 **健康监控**: 实时监控 Key 状态和性能
- ⚡ **性能优化**: 支持 1000+ keys 的高效管理
- 🛠️ **CLI 工具**: 完整的命令行管理界面
- 🐍 **Python API**: 简单易用的 Python 接口

## 快速开始

### 安装

```bash
# 使用 uv (推荐)
uv add easy-gemini-balance

# 或使用 pip
pip install easy-gemini-balance
```

### 基本使用

```python
from easy_gemini_balance import create_gemini_wrapper

# 创建包装器
wrapper = create_gemini_wrapper(
    max_retries=3,
    retry_delay=1.0
)

# 添加 API keys
wrapper.add_key("your_api_key_1", weight=1.0)
wrapper.add_key("your_api_key_2", weight=1.5)

# 使用 API
def generate_text(client):
    return client.generate_content("Hello, Gemini!")

# 自动重试和 Key 管理
result = wrapper.execute_with_retry(generate_text)
```

## 核心功能

> **注意**: 为了确保重试机制的可靠性，我们移除了上下文管理器支持，现在提供两种更稳定的重试方式。

### 1. 自动重试和 Key 管理

```python
# 使用 execute_with_retry
def api_call(client):
    return client.models.list(config={"pageSize": 10})

result = wrapper.execute_with_retry(api_call)
```

### 2. 装饰器模式

```python
@wrapper.with_retry(max_retries=3)
def my_function(client, prompt):
    return client.generate_content(prompt)

result = my_function("Hello")
```

### 4. 批量导入 Keys

```python
# 从文件导入
wrapper.import_keys_from_file("keys.txt", source="imported")

# 手动添加
wrapper.add_key("key_value", weight=1.0, source="manual")
```

### 5. 性能监控和统计

```python
# 获取详细统计信息
stats = wrapper.get_stats()
print(f"总 Keys: {stats['total_keys']}")
print(f"可用 Keys: {stats['available_keys']}")
print(f"缓存命中率: {stats['cache_stats']['hit_rate']:.2f}")

# 监控内存使用
memory_info = wrapper.get_memory_usage()
print(f"内存使用: {memory_info['total_memory_bytes']} bytes")
print(f"预估 1000 个 keys 内存: {memory_info['estimated_1000_keys_memory_mb']:.2f} MB")
```

## CLI 命令

```bash
# 显示统计信息
easy-gemini-balance stats

# 测试所有 Keys
easy-gemini-balance test-keys --max-retries 2 --retry-delay 0.5

# 导入 Keys 文件
easy-gemini-balance import keys.txt

# 显示健康状态
easy-gemini-balance health

# 添加单个 Key
easy-gemini-balance add-key "your_api_key" --weight 1.5

# 实时监控
easy-gemini-balance monitor --interval 10
```

## 高级配置

### 自定义重试策略

```python
wrapper = create_gemini_wrapper(
    max_retries=5,           # 最大重试次数
    retry_delay=2.0,         # 重试延迟（秒）
    db_path="custom.db"      # 自定义数据库路径
)
```

### 权重分配

```python
# 高优先级 Key
wrapper.add_key("premium_key", weight=2.0)

# 普通 Key
wrapper.add_key("normal_key", weight=1.0)

# 备用 Key
wrapper.add_key("backup_key", weight=0.5)
```

### LRU 缓存配置

```python
# 创建针对大量 keys 优化的 balancer
balancer = KeyBalancer(
    cache_size=500,        # 预期 5000 个 keys
    auto_save=True,
    auto_success=True
)

# 性能优化配置
balancer.optimize_for_large_keysets(5000)

# 监控缓存性能
stats = balancer.get_stats()
print(f"缓存命中率: {stats['cache_stats']['hit_rate']:.2f}")
print(f"缓存大小: {stats['cache_stats']['size']}/{stats['cache_stats']['capacity']}")
```

### 批量操作优化

```python
# 批量获取 keys 以提高效率
batch_sizes = [10, 20, 30]  # 不同批次大小
key_batches = balancer.batch_get_keys(batch_sizes)

# 预计算权重分布
balancer._update_weight_distribution()
```

## 数据库结构

使用 SQLite 存储，支持以下表：

- `api_keys`: 存储 API keys 和健康状态
- `import_history`: 记录导入历史
- `key_usage`: 记录使用统计

## 错误处理

自动识别和处理常见错误：

- `400`: API key 无效/过期
- `403`: 权限不足/服务未启用
- `429`: 配额超限
- `500`: 服务器错误

**重试策略**：
- 失败时自动切换到下一个可用的 API key
- 使用固定延迟重试（默认 1 秒）
- 支持自定义最大重试次数和重试延迟
- 智能错误分类，根据错误类型调整 key 权重

## 性能优化

- **LRU 缓存**：减少数据库查询，提高响应速度
- **权重算法**：优化 Key 选择，支持智能负载均衡
- **智能错误分类**：根据错误码自动调整权重
- **重试机制**：固定延迟重试，避免指数退避的复杂性

### LRU 缓存机制

LRU (Least Recently Used) 缓存自动管理最近使用的 API keys：

```python
# 缓存大小自动优化
balancer = KeyBalancer(
    cache_size=100,        # 默认缓存大小
    auto_save=True
)

# 针对大量 keys 的优化
balancer.optimize_for_large_keysets(5000)  # 预期 5000 个 keys
```

**缓存策略**：
- **小规模**（< 100 keys）：缓存大小 = 100
- **中等规模**（100-1000 keys）：缓存大小 = key 数量的 10%
- **大规模**（> 1000 keys）：缓存大小 = 1000

### 权重分配系统

权重系统实现智能负载均衡和自动健康管理：

```python
# 生产环境 - 高权重
wrapper.add_key("prod_key_1", weight=2.0, source="production")
wrapper.add_key("prod_key_2", weight=2.0, source="production")

# 开发环境 - 标准权重
wrapper.add_key("dev_key_1", weight=1.0, source="development")

# 备用环境 - 低权重
wrapper.add_key("backup_key", weight=0.5, source="backup")
```

**权重管理**：
- **自动调整**：成功时权重增加 10%，失败时减少 20%
- **错误分类**：400 错误标记为不可用，其他错误降低权重
- **健康恢复**：连续成功时权重逐步恢复

**最佳实践**：
- 生产环境：权重 2.0-3.0，承担主要负载
- 开发环境：权重 1.0，正常负载
- 备用环境：权重 0.5，紧急备用

## 开发

```bash
# 克隆仓库
git clone https://github.com/your-repo/easy-gemini-balance.git
cd easy-gemini-balance

# 安装依赖
uv sync

# 运行测试
uv run pytest
```

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件。
