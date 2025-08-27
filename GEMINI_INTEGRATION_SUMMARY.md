# Easy Gemini Balance - Gemini API 集成架构总结

## 🎯 重新设计的核心思想

基于你提出的实际使用场景，我们重新设计了整个架构，专注于解决以下问题：

```python
from google import genai
from google.genai import types

# 创建客户端
self.client = genai.Client(api_key=api_key)
```

**用户需求**：
1. 通过 API key 获取 Gemini 客户端
2. 使用客户端进行 API 调用
3. 失败时自动重试，获取下一个 key 并重建客户端
4. 直到成功或达到重试次数为止

## 🚀 新的架构设计

### 核心组件：GeminiClientWrapper

我们创建了一个专门的包装器类，完全围绕你的使用场景设计：

```python
from easy_gemini_balance import create_gemini_wrapper

# 创建包装器
wrapper = create_gemini_wrapper(
    keys_file="api_keys.txt",
    db_path="keys_state.db",
    max_retries=3,
    retry_delay=1.0,
    backoff_factor=2.0
)
```

### 四种使用模式

#### 1. **execute_with_retry 方法** - 最直接的方式

```python
def gemini_operation(client, prompt, max_tokens):
    # 这里使用 client 进行实际的 API 调用
    return client.generate_content(prompt, max_tokens=max_tokens)

# 执行操作，自动重试和 key 管理
result = wrapper.execute_with_retry(
    gemini_operation,
    "请解释什么是人工智能？",
    max_tokens=150
)
```

**特点**：
- ✅ 最直接，适合单次调用
- ✅ 完全控制重试逻辑
- ✅ 适合复杂的操作函数
- ✅ 自动处理 key 获取、客户端重建、错误重试

#### 2. **上下文管理器** - 适合多次调用

```python
with wrapper.client_context() as client:
    # 可以重用同一个客户端进行多次调用
    result1 = client.generate_content("第一个问题")
    result2 = client.generate_content("第二个问题")
    result3 = client.generate_content("第三个问题")
    # 上下文管理器退出时自动标记为成功
```

**特点**：
- ✅ 可以重用同一个客户端
- ✅ 适合多次连续调用
- ✅ 代码清晰，易于理解
- ✅ 自动处理成功状态

#### 3. **装饰器模式** - 最优雅的语法

```python
@wrapper.with_retry(max_retries=3)
def chat_with_gemini(client, message, context=""):
    """与 Gemini 聊天"""
    full_prompt = f"{context}\n用户: {message}\n助手:"
    return client.generate_content(full_prompt, max_tokens=150)

# 调用函数，装饰器自动处理一切
response = chat_with_gemini("你好，请介绍一下你自己")
```

**特点**：
- ✅ 最优雅的语法
- ✅ 可以装饰任何函数
- ✅ 适合函数式编程
- ✅ 完全自动化

#### 4. **Lambda 函数** - 最灵活的方式

```python
# 简单的文本生成
result = wrapper.execute_with_retry(
    lambda client: client.generate_content("生成一个随机故事", max_tokens=100)
)

# 复杂的操作
result = wrapper.execute_with_retry(
    lambda client: {
        "story": client.generate_content("写一个科幻故事", max_tokens=150),
        "summary": client.generate_content("总结上面的故事", max_tokens=50),
        "timestamp": time.time()
    }
)
```

**特点**：
- ✅ 最灵活
- ✅ 可以内联定义操作
- ✅ 适合简单的一次性操作
- ✅ 支持复杂的多步操作

## 🔧 技术实现细节

### 自动重试机制

```python
def execute_with_retry(self, operation, *args, **kwargs):
    """执行操作，自动重试和 key 管理"""
    last_error = None
    
    for attempt in range(self.max_retries + 1):
        try:
            # 获取新的客户端
            api_key, client = self._get_new_client()
            self._current_key = api_key
            self._current_client = client
            
            # 执行操作
            result = operation(client, *args, **kwargs)
            
            # 成功时标记 key 为健康
            self.balancer._mark_key_success(api_key)
            return result
            
        except Exception as e:
            last_error = e
            
            if attempt < self.max_retries:
                # 处理错误并准备重试
                self._handle_error(api_key, e, attempt)
            else:
                # 最后一次尝试失败
                print(f"❌ 所有重试都失败了，最后错误: {e}")
                self._handle_error(api_key, e, attempt)
    
    # 所有重试都失败
    raise last_error
```

### 智能错误处理

```python
def _extract_error_code(self, error: Exception) -> int:
    """从异常中提取错误代码"""
    # 尝试从 Google API 错误中提取状态码
    if hasattr(error, 'status_code'):
        return error.status_code
    
    # 尝试从 HTTP 错误中提取状态码
    if hasattr(error, 'response') and hasattr(error.response, 'status_code'):
        return error.response.status_code
    
    # 根据错误类型推断错误代码
    error_str = str(error).lower()
    if 'quota' in error_str or 'rate limit' in error_str:
        return 429  # Too Many Requests
    elif 'unauthorized' in error_str or 'invalid' in error_str:
        return 401  # Unauthorized
    elif 'forbidden' in error_str:
        return 403  # Forbidden
    elif 'not found' in error_str:
        return 404  # Not Found
    elif 'server error' in error_str or 'internal' in error_str:
        return 500  # Internal Server Error
    else:
        return 500  # 默认错误代码
```

### 指数退避重试

```python
def _handle_error(self, api_key: str, error: Exception, attempt: int):
    """处理错误，更新 key 健康状态"""
    error_code = self._extract_error_code(error)
    self.balancer.update_key_health(api_key, error_code=error_code)
    
    if attempt < self.max_retries:
        delay = self.retry_delay * (self.backoff_factor ** attempt)
        print(f"⚠️  API 调用失败 (尝试 {attempt + 1}/{self.max_retries})，等待 {delay:.1f} 秒后重试...")
        time.sleep(delay)
```

## 📊 实际使用场景示例

### 聊天机器人场景

```python
# 创建包装器
wrapper = create_gemini_wrapper(
    keys_file="chatbot_keys.txt",
    db_path="chatbot_keys.db",
    max_retries=3,
    retry_delay=1.0,
    backoff_factor=2.0
)

# 定义聊天函数
@wrapper.with_retry(max_retries=2)
def chat_with_gemini(client, message, context=""):
    """与 Gemini 聊天"""
    full_prompt = f"{context}\n用户: {message}\n助手:" if context else f"用户: {message}\n助手:"
    return client.generate_content(full_prompt, max_tokens=150)

# 模拟对话
conversation = [
    "你好，请介绍一下你自己",
    "什么是人工智能？",
    "写一个 Python 函数来计算斐波那契数列"
]

for message in conversation:
    try:
        response = chat_with_gemini(message)
        print(f"🤖 助手: {response.text}")
    except Exception as e:
        print(f"❌ 对话失败: {e}")
        break
```

### 批量处理场景

```python
# 批量文本处理任务
tasks = [
    {"text": "人工智能正在改变世界", "task": "翻译为英文"},
    {"text": "Python is a great programming language", "task": "翻译为中文"},
    {"text": "机器学习算法", "task": "解释概念"}
]

for task in tasks:
    try:
        def process_task(client, task_data):
            prompt = f"请{task_data['task']}：{task_data['text']}"
            return client.generate_content(prompt, max_tokens=100)
        
        result = wrapper.execute_with_retry(process_task, task)
        print(f"✅ 成功: {result.text}")
        
    except Exception as e:
        print(f"❌ 失败: {e}")
```

### Web 服务场景

```python
# 模拟 Web 服务请求
requests = [
    {"user_id": "user001", "query": "天气怎么样？", "priority": "high"},
    {"user_id": "user002", "query": "推荐一些好书", "priority": "medium"}
]

for request in requests:
    try:
        with wrapper.client_context() as client:
            # 模拟 API 调用
            response = client.generate_content(
                request['query'], 
                max_tokens=200 if request['priority'] == 'high' else 100
            )
            print(f"✅ 响应: {response.text[:50]}...")
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
```

## 🔄 与原有架构的关系

### 向后兼容性

新的 `GeminiClientWrapper` 完全基于原有的 `KeyBalancer` 和 `KeyManager`：

```python
class GeminiClientWrapper:
    def __init__(self, balancer: KeyBalancer, ...):
        self.balancer = balancer  # 使用原有的均衡器
        # ... 其他配置
```

### 功能增强

1. **自动重试**：原有的 key 管理 + 新的重试逻辑
2. **客户端管理**：自动创建、重建 Gemini 客户端
3. **错误处理**：智能识别错误类型，自动更新 key 健康状态
4. **多种使用模式**：满足不同编程风格的需求

## 🎯 核心优势

### 1. **完全自动化**
- 无需手动管理 API key
- 无需手动处理重试逻辑
- 无需手动重建客户端

### 2. **智能错误处理**
- 自动识别错误类型
- 智能选择重试策略
- 自动更新 key 健康状态

### 3. **灵活的使用方式**
- 四种不同的使用模式
- 支持函数式编程
- 支持面向对象编程

### 4. **生产就绪**
- 完整的错误处理
- 可配置的重试参数
- 详细的统计信息
- 监控和告警支持

## 💡 使用建议

### 选择使用模式

1. **单次调用**：使用 `execute_with_retry`
2. **多次调用**：使用 `client_context`
3. **函数式编程**：使用 `with_retry` 装饰器
4. **简单操作**：使用 Lambda 函数

### 配置参数

```python
wrapper = create_gemini_wrapper(
    keys_file="api_keys.txt",
    db_path="keys_state.db",
    max_retries=3,        # 最大重试次数
    retry_delay=1.0,      # 初始重试延迟
    backoff_factor=2.0    # 指数退避因子
)
```

### 监控和告警

```python
# 获取统计信息
stats = wrapper.balancer.get_stats()

# 告警逻辑
if stats['available_keys'] < stats['total_keys'] * 0.5:
    print("🚨 警告: 可用 keys 数量不足！")
```

## 🎉 总结

通过重新设计，我们成功解决了你提出的实际使用场景：

1. **✅ 自动 key 管理**：无需手动获取和管理 API key
2. **✅ 自动重试**：失败时自动获取下一个 key 并重建客户端
3. **✅ 多种使用模式**：支持 lambda、函数、上下文管理器等
4. **✅ 生产就绪**：完整的错误处理、监控和告警功能

现在你可以专注于业务逻辑，而不用担心 API key 管理的复杂性！
