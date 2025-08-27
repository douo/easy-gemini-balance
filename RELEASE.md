# 📦 发布指南

本指南将帮助你打包和发布 Easy Gemini Balance 模块，供其他项目使用。

## 🚀 快速开始

### 1. 环境准备

确保你的开发环境已经设置好：

```bash
# 安装开发依赖
uv sync --group dev

# 验证环境
uv run python -c "import easy_gemini_balance; print('✅ 环境就绪')"
```

### 2. 一键构建和测试

使用我们提供的构建脚本：

```bash
# 运行完整的构建流程
uv run python scripts/build_and_release.py
```

这个脚本会自动：
- 🧹 清理之前的构建文件
- 🧪 运行所有测试
- 🔨 构建包
- 🔍 检查包质量
- 🧪 测试安装
- 📋 提供后续步骤指导

## 📦 手动构建

如果你想手动控制构建过程：

### 1. 清理环境

```bash
# 清理之前的构建文件
rm -rf build/ dist/ *.egg-info/
```

### 2. 运行测试

```bash
# 运行所有测试
uv run python tests/run_tests.py --all
```

### 3. 构建包

```bash
# 构建 wheel 和源码包
uv run python -m build
```

### 4. 检查构建结果

```bash
# 查看生成的文件
ls -la dist/

# 应该看到：
# - easy_gemini_balance-0.3.0-py3-none-any.whl (wheel 包)
# - easy_gemini_balance-0.3.0.tar.gz (源码包)
```

### 5. 测试安装

```bash
# 安装 wheel 包
uv pip install dist/easy_gemini_balance-0.3.0-py3-none-any.whl

# 测试 CLI
uv run easy-gemini-balance --help

# 测试 Python 导入
uv run python -c "from easy_gemini_balance import KeyBalancer; print('✅ 导入成功')"

# 清理安装
uv pip uninstall easy-gemini-balance --yes
```

## 🌐 发布到 PyPI

### 1. 准备 PyPI 账户

如果你还没有 PyPI 账户：
1. 访问 [PyPI](https://pypi.org/account/register/)
2. 创建账户并验证邮箱
3. 启用双因素认证（推荐）

### 2. 安装发布工具

```bash
uv add --dev twine
```

### 3. 构建发布版本

```bash
# 确保版本号正确
# 编辑 pyproject.toml 中的 version 字段

# 构建包
uv run python -m build

# 检查包
uv run twine check dist/*
```

### 4. 上传到 PyPI

```bash
# 上传到测试 PyPI（推荐先测试）
uv run twine upload --repository testpypi dist/*

# 上传到正式 PyPI
uv run twine upload dist/*
```

### 5. 验证发布

```bash
# 测试从 PyPI 安装
uv pip install --index-url https://test.pypi.org/simple/ easy-gemini-balance

# 或者正式版本
uv pip install easy-gemini-balance
```

## 📋 发布检查清单

在发布之前，请确保：

### ✅ 代码质量
- [ ] 所有测试通过
- [ ] 代码格式化完成 (`uv run black src/ tests/`)
- [ ] 没有明显的 bug 或问题

### ✅ 文档完整性
- [ ] README.md 更新完整
- [ ] CHANGELOG.md 记录所有变更
- [ ] 示例代码可以正常运行
- [ ] CLI 帮助信息完整

### ✅ 包配置
- [ ] `pyproject.toml` 配置正确
- [ ] 版本号已更新
- [ ] 依赖列表完整
- [ ] 包描述准确

### ✅ 构建验证
- [ ] 包可以正常构建
- [ ] 安装测试通过
- [ ] CLI 命令工作正常
- [ ] Python 导入无错误

## 🔧 常见问题

### Q: 构建失败怎么办？

**A:** 检查以下几点：
1. 确保所有依赖已安装：`uv sync --group dev`
2. 检查 `pyproject.toml` 语法是否正确
3. 确保在项目根目录运行构建命令
4. 查看错误信息，通常会有具体的错误提示

### Q: 测试失败怎么办？

**A:** 按以下步骤排查：
1. 单独运行失败的测试：`uv run python tests/test_balancer.py`
2. 检查测试环境是否正确设置
3. 确保测试数据文件存在
4. 查看具体的错误信息

### Q: 包安装后无法使用怎么办？

**A:** 检查以下几点：
1. 确认包已正确安装：`uv pip list | grep easy-gemini-balance`
2. 检查 `__init__.py` 文件是否正确导出类
3. 验证 CLI 入口点配置
4. 测试基本的 Python 导入

### Q: 如何更新版本号？

**A:** 编辑 `pyproject.toml` 文件：
```toml
[project]
version = "0.3.1"  # 更新版本号
```

同时更新 `CHANGELOG.md` 文件，记录新版本的变更。

## 📚 更多资源

### 有用的命令

```bash
# 查看包信息
uv pip show easy-gemini-balance

# 查看包的依赖
uv pip show --files easy-gemini-balance

# 检查包的完整性
uv run python -m build --sdist --wheel

# 运行特定测试
uv run python tests/run_tests.py --basic
uv run python tests/run_tests.py --performance
uv run python tests/run_tests.py --cli
```

### 相关文档

- [Python 打包用户指南](https://packaging.python.org/tutorials/packaging-projects/)
- [Hatchling 构建系统](https://hatch.pypa.io/latest/build/)
- [PyPI 发布指南](https://packaging.python.org/guides/distributing-packages-using-setuptools/#uploading-your-project-to-pypi)

## 🎯 下一步

成功发布后，你可以：

1. **创建 Git 标签**：
   ```bash
   git tag v0.3.0
   git push origin v0.3.0
   ```

2. **更新项目文档**：
   - 更新安装说明
   - 添加使用示例
   - 更新变更日志

3. **推广你的包**：
   - 在 README 中添加 PyPI 徽章
   - 分享到相关社区
   - 收集用户反馈

4. **维护和更新**：
   - 监控 issue 和 PR
   - 定期更新依赖
   - 发布补丁版本

---

🎉 恭喜！你的 Easy Gemini Balance 模块现在已经可以供其他项目使用了！
