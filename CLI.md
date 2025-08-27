# 🖥️ CLI 使用指南

Easy Gemini Balance 提供了一个功能强大的命令行界面，让你可以方便地查看和管理 API key 的统计信息。

## 📦 安装后使用

安装模块后，你可以直接使用以下命令：

```bash
# 查看所有统计信息
easy-gemini-balance stats --keys-file keys.txt --db-path keys.db

# 查看 key 健康状态
easy-gemini-balance health --keys-file keys.txt --db-path keys.db

# 查看数据库信息
easy-gemini-balance db-info --db-path keys.db

# 查看内存使用情况
easy-gemini-balance memory --keys-file keys.txt --db-path keys.db

# 导出统计信息到 JSON 文件
easy-gemini-balance export --keys-file keys.txt --db-path keys.db --output stats.json

# 实时监控统计信息
easy-gemini-balance monitor --keys-file keys.txt --db-path keys.db --interval 5

# 列出所有 keys
easy-gemini-balance list --keys-file keys.txt --db-path keys.db --limit 10

# 重置所有 key 权重和状态
easy-gemini-balance reset --keys-file keys.txt --db-path keys.db --confirm
```

## 🔧 开发环境使用

在开发环境中，你可以使用 Python 模块方式：

```bash
# 查看帮助信息
python -m easy_gemini_balance.cli --help

# 查看特定命令的帮助
python -m easy_gemini_balance.cli stats --help

# 运行命令
python -m easy_gemini_balance.cli stats --keys-file keys.txt --db-path keys.db
```

## 📊 主要命令

### `stats` - 综合统计信息

显示所有 key 的统计信息，包括总数、可用数量、平均权重等。

```bash
easy-gemini-balance stats --keys-file keys.txt --db-path keys.db --detailed
```

**选项：**
- `--detailed, -D`: 显示详细的 key 信息
- `--json, -j`: 以 JSON 格式输出
- `--verbose, -v`: 启用详细输出

### `health` - Key 健康状态

显示 key 的健康状态，包括可用性、错误统计等。

```bash
easy-gemini-balance health --keys-file keys.txt --db-path keys.db --filter error
```

**选项：**
- `--filter`: 过滤显示（all, available, unavailable, error）
- `--json, -j`: 以 JSON 格式输出

### `db-info` - 数据库信息

显示 SQLite 数据库的详细信息。

```bash
easy-gemini-balance db-info --db-path keys.db
```

### `memory` - 内存使用统计

显示内存使用情况，包括预估的 1000 个 key 的内存需求。

```bash
easy-gemini-balance memory --keys-file keys.txt --db-path keys.db
```

### `export` - 导出统计信息

将统计信息导出到文件，支持多种格式。

```bash
# 导出为 JSON
easy-gemini-balance export --keys-file keys.txt --db-path keys.db --output stats.json --format json

# 导出为 CSV
easy-gemini-balance export --keys-file keys.txt --db-path keys.db --output stats.csv --format csv

# 导出为文本
easy-gemini-balance export --keys-file keys.txt --db-path keys.db --output stats.txt --format txt
```

### `monitor` - 实时监控

实时监控统计信息的变化。

```bash
# 每 5 秒更新一次
easy-gemini-balance monitor --keys-file keys.txt --db-path keys.db --interval 5

# 只更新 10 次
easy-gemini-balance monitor --keys-file keys.txt --db-path keys.db --interval 2 --count 10
```

### `list` - 列出所有 Keys

列出所有 keys，支持排序和限制数量。

```bash
# 按权重排序，限制显示 5 个
easy-gemini-balance list --keys-file keys.txt --db-path keys.db --sort-by weight --limit 5

# 按错误数量排序
easy-gemini-balance list --keys-file keys.txt --db-path keys.db --sort-by error_count
```

**排序选项：**
- `key`: 按 key 值排序
- `weight`: 按权重排序（降序）
- `last_used`: 按最后使用时间排序
- `error_count`: 按错误数量排序（降序）
- `status`: 按可用状态排序

### `reset` - 重置 Keys

重置所有 key 的权重和状态。

```bash
easy-gemini-balance reset --keys-file keys.txt --db-path keys.db --confirm
```

**注意：** 此操作需要 `--confirm` 参数确认。

## 🌐 全局选项

所有命令都支持以下全局选项：

- `--keys-file, -k`: 指定 keys 文件路径（默认：keys.txt）
- `--db-path, -d`: 指定数据库路径（默认：keys.db）
- `--verbose, -v`: 启用详细输出
- `--json, -j`: 以 JSON 格式输出

## 📤 输出格式

CLI 支持两种输出格式：

1. **表格格式（默认）**: 人类可读的表格形式
2. **JSON 格式**: 机器可读的 JSON 格式，便于脚本处理

## 💡 使用示例

### 基本使用

```bash
# 查看当前 keys 的统计信息
easy-gemini-balance stats --keys-file my_keys.txt --db-path my_keys.db

# 检查 key 健康状态
easy-gemini-balance health --keys-file my_keys.txt --db-path my_keys.db --filter error

# 导出统计信息用于分析
easy-gemini-balance export --keys-file my_keys.txt --db-path my_keys.db --output analysis.json
```

### 高级使用

```bash
# 实时监控 key 状态变化
easy-gemini-balance monitor --keys-file my_keys.txt --db-path my_keys.db --interval 10

# 按权重排序查看 top 10 keys
easy-gemini-balance list --keys-file my_keys.txt --db-path my_keys.db --sort-by weight --limit 10

# 重置所有 key 状态（谨慎使用）
easy-gemini-balance reset --keys-file my_keys.txt --db-path my_keys.db --confirm
```

### 脚本集成

```bash
# 获取 JSON 格式的统计信息
easy-gemini-balance stats --keys-file keys.txt --db-path keys.db --json > stats.json

# 在脚本中使用
TOTAL_KEYS=$(easy-gemini-balance stats --keys-file keys.txt --db-path keys.db --json | jq '.statistics.total_keys')
echo "Total keys: $TOTAL_KEYS"
```

## 🚨 错误处理

CLI 模块包含完善的错误处理：

- 文件不存在时会显示清晰的错误信息
- 数据库连接失败时会提供诊断信息
- 使用 `--verbose` 选项可以查看详细的错误堆栈
- 支持 Ctrl+C 中断操作

## ⚡ 性能特点

- **快速响应**: 所有命令都在毫秒级响应
- **内存高效**: 支持处理大量 keys（1000+）而不会显著增加内存使用
- **并发安全**: 支持多个 CLI 实例同时访问同一个数据库
- **缓存优化**: 利用 LRU 缓存提高重复查询的性能

## 🔍 调试技巧

### 启用详细输出

```bash
# 查看详细的执行信息
easy-gemini-balance stats --keys-file keys.txt --db-path keys.db --verbose
```

### JSON 输出调试

```bash
# 获取机器可读的输出，便于脚本处理
easy-gemini-balance stats --keys-file keys.txt --db-path keys.db --json | jq '.'

# 提取特定信息
easy-gemini-balance stats --keys-file keys.txt --db-path keys.db --json | jq '.statistics.available_keys'
```

### 实时监控调试

```bash
# 快速监控（1秒间隔）
easy-gemini-balance monitor --keys-file keys.txt --db-path keys.db --interval 1 --count 5
```

---

🎯 现在你可以使用 CLI 工具来方便地管理和监控你的 API keys 了！
