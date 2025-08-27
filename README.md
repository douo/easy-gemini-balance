# Easy Gemini Balance

一个用于动态 API key 均衡的 Python 模块，支持 LRU 缓存、权重管理和 SQLite 持久化。

## ✨ 核心特性

- **动态均衡**: 基于 LRU 缓存和权重的智能 key 选择
- **健康监控**: 自动根据 HTTP 错误码调整 key 权重和可用性
- **高性能**: 针对大量 key（1000+）优化的选择算法
- **持久化**: 使用 SQLite 高效存储 key 状态
- **多种使用模式**: 支持自动成功、上下文管理器和装饰器三种模式

## 🚀 快速开始

### 安装

```bash
# 从源码安装
git clone https://github.com/yourusername/easy-gemini-balance.git
cd easy-gemini-balance
uv sync
uv run python -m pip install -e .
```

### 基本使用

```python
from easy_gemini_balance import KeyBalancer

# 创建 balancer 实例
balancer = KeyBalancer(
    keys_file="keys.txt",      # API keys 文件路径
    db_path="keys.db",         # SQLite 数据库路径
    auto_success=True          # 启用自动成功模式
)

# 获取单个 key
key = balancer.get_single_key()

# 获取多个 keys
keys = balancer.get_keys(count=3)

# 更新 key 健康状态
balancer.update_key_health(key, error_code=403)  # 失败
balancer.update_key_health(key, success=True)    # 成功
```

## 🎯 三种使用模式

### 方案1：自动成功模式（推荐）

最简单的使用方式，适合大多数场景：

```python
# 启用自动成功模式
balancer = KeyBalancer(auto_success=True)

# 获取 key 后自动标记为成功
key = balancer.get_single_key()
# 无需手动调用 update_key_health(key, success=True)

# 失败时仍需要手动处理
try:
    result = make_api_call(key)
except Exception as e:
    balancer.update_key_health(key, error_code=500)
```

### 方案2：上下文管理器

提供精确的成功/失败控制：

```python
# 关闭自动成功模式，使用上下文管理器
balancer = KeyBalancer(auto_success=False)

# 使用上下文管理器自动处理成功状态
with balancer.get_key_context(count=1) as keys:
    key = keys[0]
    result = make_api_call(key)
    # 上下文管理器退出时自动标记为成功

# 异常情况需要手动处理
try:
    with balancer.get_key_context(count=1) as keys:
        key = keys[0]
        make_api_call(key)
except Exception as e:
    balancer.update_key_health(key, error_code=403)
```

### 方案3：装饰器模式

最优雅的函数式编程方式：

```python
# 使用装饰器自动管理 key
@balancer.with_key_balancing(key_count=1, auto_success=True)
def api_call_function():
    # 装饰器会自动获取 key 并处理成功状态
    return make_api_call()

# 调用函数
result = api_call_function()
```

## 📁 项目结构

```
easy-gemini-balance/
├── src/easy_gemini_balance/
│   ├── __init__.py          # 模块入口
│   ├── balancer.py          # 核心均衡器（包含三种模式）
│   ├── key_manager.py       # Key 管理器
│   ├── store.py             # SQLite 存储后端
│   └── cli.py               # 命令行工具
├── tests/                   # 测试目录
├── examples/                # 示例代码
│   └── three_schemes_demo.py # 三种方案演示
├── pyproject.toml           # 项目配置
└── README.md               # 项目文档
```

## 🔧 开发环境使用

### 作为模块导入

```python
# 直接导入
from easy_gemini_balance import KeyBalancer, KeyManager, APIKey

# 创建实例
balancer = KeyBalancer("keys.txt", db_path="keys.db")

# 使用各种功能
key = balancer.get_single_key()
stats = balancer.get_stats()
```

### 运行测试

```bash
# 运行所有测试
uv run python tests/run_tests.py --all

# 运行特定测试
uv run python tests/run_tests.py --basic
uv run python tests/run_tests.py --performance
uv run python tests/run_tests.py --cli
```

### 运行示例

```bash
# 运行三种方案演示
uv run python examples/three_schemes_demo.py
```

## 📊 API 参考

### KeyBalancer 类

#### 初始化参数

- `keys_file`: API keys 文件路径
- `cache_size`: LRU 缓存大小（默认 100）
- `db_path`: SQLite 数据库路径
- `auto_save`: 是否自动保存状态（默认 True）
- `auto_success`: 是否启用自动成功模式（默认 True）

#### 主要方法

- `get_single_key()`: 获取单个 key
- `get_keys(count)`: 获取指定数量的 keys
- `get_key_context(count)`: 获取上下文管理器
- `with_key_balancing(key_count, auto_success)`: 装饰器工厂
- `update_key_health(key, error_code, success)`: 更新 key 健康状态
- `get_stats()`: 获取统计信息

## ⚡ 性能优势

- **预计算权重**: 使用累积权重和二分查找优化选择
- **智能缓存**: 根据 key 数量自动调整 LRU 缓存大小
- **批量操作**: 支持批量获取 keys 减少数据库查询
- **异步保存**: 后台线程自动保存状态，不阻塞主操作

## 📝 完整示例

```python
from easy_gemini_balance import KeyBalancer
import requests

# 创建 balancer
balancer = KeyBalancer(
    keys_file="api_keys.txt",
    db_path="keys_state.db",
    auto_success=True,  # 启用自动成功模式
    cache_size=200
)

# 方案1：自动成功模式
def simple_api_call():
    key = balancer.get_single_key()
    try:
        response = requests.get(
            "https://api.example.com/data",
            headers={"Authorization": f"Bearer {key}"}
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        # 根据错误码更新 key 健康状态
        balancer.update_key_health(key, error_code=e.response.status_code)
        raise

# 方案2：上下文管理器
def controlled_api_call():
    with balancer.get_key_context(count=1) as keys:
        key = keys[0]
        response = requests.get(
            "https://api.example.com/data",
            headers={"Authorization": f"Bearer {key}"}
        )
        response.raise_for_status()
        return response.json()
        # 上下文管理器自动处理成功状态

# 方案3：装饰器模式
@balancer.with_key_balancing(key_count=1)
def decorated_api_call():
    # 装饰器自动获取 key 并处理状态
    response = requests.get(
        "https://api.example.com/data",
        headers={"Authorization": f"Bearer {key}"}
    )
    response.raise_for_status()
    return response.json()

# 使用示例
try:
    # 选择你喜欢的方案
    result1 = simple_api_call()      # 方案1
    result2 = controlled_api_call()  # 方案2
    result3 = decorated_api_call()   # 方案3
    
    print("所有 API 调用成功！")
    
except Exception as e:
    print(f"API 调用失败: {e}")

# 查看统计信息
stats = balancer.get_stats()
print(f"可用 keys: {stats['available_keys']}")
print(f"错误 keys: {stats['error_keys']}")
```

## 🛠️ 开发

### 代码格式化

```bash
uv run black src/ tests/ examples/
uv run flake8 src/ tests/ examples/
```

### 运行测试

```bash
uv run python tests/run_tests.py --all
```

## 📦 打包和发布

详细的打包和发布说明请参考 [RELEASE.md](RELEASE.md)。

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

🎯 **推荐使用策略**：
- **简单场景**: 使用方案1（自动成功模式）
- **需要精确控制**: 使用方案2（上下文管理器）  
- **函数式编程**: 使用方案3（装饰器模式）

详细的 CLI 使用说明请参考 [CLI.md](CLI.md)。
