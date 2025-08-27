#!/usr/bin/env python3
"""
演示 Easy Gemini Balance 的三个改进方案：
1. 自动成功模式 (Auto-success mode)
2. 上下文管理器 (Context manager)
3. 装饰器模式 (Decorator pattern)
"""

import sys
import time
import requests
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from easy_gemini_balance import KeyBalancer


def create_test_keys():
    """创建测试用的 keys 文件"""
    keys_file = "test_keys.txt"
    with open(keys_file, "w") as f:
        # 创建一些测试 keys
        for i in range(5):
            f.write(f"AIzaSyTest_Key{i+1}_abcdefghijklmnopqrstuvwxyz:{1.0 + i * 0.1}\n")
    return keys_file


def simulate_api_call(key, should_fail=False, error_code=500):
    """模拟 API 调用"""
    print(f"🔑 使用 key: {key[:20]}...")
    time.sleep(0.1)  # 模拟网络延迟
    
    if should_fail:
        # 模拟失败
        if error_code == 400:
            raise requests.exceptions.HTTPError(f"400 Bad Request for key {key[:8]}...")
        elif error_code == 403:
            raise requests.exceptions.HTTPError(f"403 Forbidden for key {key[:8]}...")
        elif error_code == 429:
            raise requests.exceptions.HTTPError(f"429 Too Many Requests for key {key[:8]}...")
        else:
            raise requests.exceptions.HTTPError(f"{error_code} Error for key {key[:8]}...")
    
    # 模拟成功
    return {"status": "success", "key_used": key[:8] + "..."}


def demo_auto_success_mode():
    """演示方案1：自动成功模式"""
    print("\n" + "="*60)
    print("🎯 方案1：自动成功模式 (Auto-success mode)")
    print("="*60)
    
    # 创建 balancer，启用自动成功模式
    balancer = KeyBalancer(
        keys_file="test_keys.txt",
        db_path="test_auto_success.db",
        auto_success=True  # 启用自动成功模式
    )
    
    print("✅ 自动成功模式已启用")
    print("📊 初始状态:")
    print(f"   - 可用 keys: {len(balancer.key_manager.get_available_keys())}")
    
    # 获取 key 并模拟成功调用
    print("\n🔄 获取 key 并模拟成功调用...")
    key = balancer.get_single_key()
    result = simulate_api_call(key, should_fail=False)
    print(f"   ✅ API 调用成功: {result}")
    
    # 注意：这里不需要手动调用 update_key_health(key, success=True)
    # 因为 auto_success=True，key 已经被自动标记为成功
    
    print("\n📊 调用后的状态:")
    key_info = balancer.get_key_info(key)
    print(f"   - Key: {key_info['key']}")
    print(f"   - 最后使用时间: {key_info['last_used']}")
    print(f"   - 在缓存中: {key_info['in_cache']}")
    
    # 清理
    import os
    if os.path.exists("test_auto_success.db"):
        os.unlink("test_auto_success.db")


def demo_context_manager():
    """演示方案2：上下文管理器"""
    print("\n" + "="*60)
    print("🎯 方案2：上下文管理器 (Context manager)")
    print("="*60)
    
    balancer = KeyBalancer(
        keys_file="test_keys.txt",
        db_path="test_context.db",
        auto_success=False  # 关闭自动成功模式，使用上下文管理器
    )
    
    print("✅ 上下文管理器模式")
    print("📊 初始状态:")
    print(f"   - 可用 keys: {len(balancer.key_manager.get_available_keys())}")
    
    # 使用上下文管理器
    print("\n🔄 使用上下文管理器获取 key...")
    with balancer.get_key_context(count=1) as keys:
        key = keys[0]
        print(f"   🔑 获取到 key: {key[:20]}...")
        
        # 模拟成功调用
        result = simulate_api_call(key, should_fail=False)
        print(f"   ✅ API 调用成功: {result}")
        
        # 上下文管理器会自动处理成功状态
    
    print("\n📊 上下文管理器退出后的状态:")
    key_info = balancer.get_key_info(key)
    print(f"   - Key: {key_info['key']}")
    print(f"   - 最后使用时间: {key_info['last_used']}")
    
    # 演示异常情况
    print("\n🔄 演示异常情况...")
    try:
        with balancer.get_key_context(count=1) as keys:
            key = keys[0]
            print(f"   🔑 获取到 key: {key[:20]}...")
            
            # 模拟失败调用
            simulate_api_call(key, should_fail=True, error_code=403)
    except Exception as e:
        print(f"   ❌ API 调用失败: {e}")
        # 手动处理失败情况
        balancer.update_key_health(key, error_code=403)
    
    print("\n📊 异常处理后的状态:")
    key_info = balancer.get_key_info(key)
    print(f"   - Key: {key_info['key']}")
    print(f"   - 错误次数: {key_info['error_count']}")
    print(f"   - 连续错误: {key_info['consecutive_errors']}")
    
    # 清理
    import os
    if os.path.exists("test_context.db"):
        os.unlink("test_context.db")


def demo_decorator_pattern():
    """演示方案3：装饰器模式"""
    print("\n" + "="*60)
    print("🎯 方案3：装饰器模式 (Decorator pattern)")
    print("="*60)
    
    balancer = KeyBalancer(
        keys_file="test_keys.txt",
        db_path="test_decorator.db",
        auto_success=False  # 关闭自动成功模式，使用装饰器
    )
    
    print("✅ 装饰器模式")
    print("📊 初始状态:")
    print(f"   - 可用 keys: {len(balancer.key_manager.get_available_keys())}")
    
    # 使用装饰器
    @balancer.with_key_balancing(key_count=1, auto_success=True)
    def api_call_with_decorator():
        """使用装饰器自动管理 key 的 API 调用"""
        # 装饰器会自动获取 key
        # 这里我们通过 balancer 的当前状态来获取最后使用的 key
        available_keys = balancer.key_manager.get_available_keys()
        if available_keys:
            key = available_keys[0].key
            print(f"   🔑 装饰器获取到 key: {key[:20]}...")
            return simulate_api_call(key, should_fail=False)
        return None
    
    # 调用带装饰器的函数
    print("\n🔄 调用带装饰器的函数...")
    try:
        result = api_call_with_decorator()
        print(f"   ✅ API 调用成功: {result}")
    except Exception as e:
        print(f"   ❌ API 调用失败: {e}")
    
    # 演示失败情况
    @balancer.with_key_balancing(key_count=1, auto_success=False)
    def failing_api_call():
        """模拟失败的 API 调用"""
        available_keys = balancer.key_manager.get_available_keys()
        if available_keys:
            key = available_keys[0].key
            print(f"   🔑 装饰器获取到 key: {key[:20]}...")
            return simulate_api_call(key, should_fail=True, error_code=429)
        return None
    
    print("\n🔄 演示失败的 API 调用...")
    try:
        result = failing_api_call()
        print(f"   ✅ API 调用成功: {result}")
    except Exception as e:
        print(f"   ❌ API 调用失败: {e}")
        # 装饰器会自动处理失败情况
    
    print("\n📊 装饰器处理后的状态:")
    stats = balancer.get_stats()
    print(f"   - 总 keys: {stats['total_keys']}")
    print(f"   - 可用 keys: {stats['available_keys']}")
    print(f"   - 不可用 keys: {stats['unavailable_keys']}")
    
    # 清理
    import os
    if os.path.exists("test_decorator.db"):
        os.unlink("test_decorator.db")


def demo_comparison():
    """对比三种方案的使用方式"""
    print("\n" + "="*60)
    print("📊 三种方案对比")
    print("="*60)
    
    print("""
🎯 方案1：自动成功模式 (Auto-success mode)
   优点：
   ✅ 最简单，无需额外代码
   ✅ 适合大多数使用场景
   ✅ 性能最好
   
   缺点：
   ❌ 无法处理复杂的成功/失败逻辑
   ❌ 灵活性较低
   
   适用场景：简单的 API 调用，不需要特殊错误处理

🎯 方案2：上下文管理器 (Context manager)
   优点：
   ✅ 自动处理成功状态
   ✅ 可以手动处理失败情况
   ✅ 代码清晰，易于理解
   ✅ 支持异常处理
   
   缺点：
   ❌ 需要额外的 with 语句
   ❌ 代码稍微冗长
   
   适用场景：需要精确控制成功/失败处理逻辑

🎯 方案3：装饰器模式 (Decorator pattern)
   优点：
   ✅ 最优雅的语法
   ✅ 完全自动化
   ✅ 可以装饰任何函数
   ✅ 支持批量处理
   
   缺点：
   ❌ 调试相对困难
   ❌ 错误处理相对粗糙
   
   适用场景：函数式编程，批量 API 调用
    """)
    
    print("\n💡 推荐使用策略：")
    print("   - 简单场景：使用方案1（自动成功模式）")
    print("   - 需要精确控制：使用方案2（上下文管理器）")
    print("   - 函数式编程：使用方案3（装饰器模式）")


def main():
    """主函数"""
    print("🚀 Easy Gemini Balance - 三种改进方案演示")
    print("="*60)
    
    # 创建测试 keys 文件
    keys_file = create_test_keys()
    print(f"📝 创建测试 keys 文件: {keys_file}")
    
    try:
        # 演示三种方案
        demo_auto_success_mode()
        demo_context_manager()
        demo_decorator_pattern()
        demo_comparison()
        
        print("\n" + "="*60)
        print("🎉 所有演示完成！")
        print("="*60)
        
    finally:
        # 清理测试文件
        import os
        if os.path.exists(keys_file):
            os.unlink(keys_file)
        print(f"🧹 清理测试文件: {keys_file}")


if __name__ == "__main__":
    main()
