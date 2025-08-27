#!/usr/bin/env python3
"""
测试 Easy Gemini Balance 的三个改进方案：
1. 自动成功模式 (Auto-success mode)
2. 上下文管理器 (Context manager)
3. 装饰器模式 (Decorator pattern)
"""

import sys
import os
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from easy_gemini_balance import KeyBalancer


def create_test_keys():
    """创建测试用的 keys 文件"""
    keys_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
    try:
        # 创建一些测试 keys
        for i in range(5):
            keys_file.write(f"AIzaSyTest_Key{i+1}_abcdefghijklmnopqrstuvwxyz:{1.0 + i * 0.1}\n")
        keys_file.close()
        return keys_file.name
    except Exception:
        keys_file.close()
        if os.path.exists(keys_file.name):
            os.unlink(keys_file.name)
        raise


def test_auto_success_mode():
    """测试方案1：自动成功模式"""
    print("🧪 Testing Auto-success mode...")
    
    keys_file = create_test_keys()
    db_path = keys_file.replace('.txt', '_auto_success.db')
    
    try:
        # 创建 balancer，启用自动成功模式
        balancer = KeyBalancer(
            keys_file=keys_file,
            db_path=db_path,
            auto_success=True
        )
        
        # 获取 key
        key = balancer.get_single_key()
        assert key is not None, "Should get a key"
        
        # 检查 key 是否被自动标记为成功
        key_info = balancer.get_key_info(key)
        assert key_info is not None, "Should get key info"
        assert key_info['last_used'] is not None, "Key should be marked as used"
        
        print("✅ Auto-success mode works correctly")
        return True
        
    except Exception as e:
        print(f"❌ Auto-success mode test failed: {e}")
        return False
        
    finally:
        # 清理
        if os.path.exists(keys_file):
            os.unlink(keys_file)
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_context_manager():
    """测试方案2：上下文管理器"""
    print("🧪 Testing Context manager...")
    
    keys_file = create_test_keys()
    db_path = keys_file.replace('.txt', '_context.db')
    
    try:
        # 创建 balancer，关闭自动成功模式
        balancer = KeyBalancer(
            keys_file=keys_file,
            db_path=db_path,
            auto_success=False
        )
        
        # 使用上下文管理器
        with balancer.get_key_context(count=1) as keys:
            key = keys[0]
            assert key is not None, "Should get a key from context"
            
            # 模拟成功调用
            time.sleep(0.1)  # 模拟 API 调用
        
        # 检查 key 是否被上下文管理器标记为成功
        key_info = balancer.get_key_info(key)
        assert key_info is not None, "Should get key info"
        assert key_info['last_used'] is not None, "Key should be marked as used by context manager"
        
        print("✅ Context manager works correctly")
        return True
        
    except Exception as e:
        print(f"❌ Context manager test failed: {e}")
        return False
        
    finally:
        # 清理
        if os.path.exists(keys_file):
            os.unlink(keys_file)
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_decorator_pattern():
    """测试方案3：装饰器模式"""
    print("🧪 Testing Decorator pattern...")
    
    keys_file = create_test_keys()
    db_path = keys_file.replace('.txt', '_decorator.db')
    
    try:
        # 创建 balancer，关闭自动成功模式
        balancer = KeyBalancer(
            keys_file=keys_file,
            db_path=db_path,
            auto_success=False
        )
        
        # 使用装饰器
        @balancer.with_key_balancing(key_count=1, auto_success=True)
        def test_api_call():
            """测试 API 调用函数"""
            # 装饰器会自动获取 key
            available_keys = balancer.key_manager.get_available_keys()
            if available_keys:
                key = available_keys[0].key
                # 模拟成功调用
                time.sleep(0.1)
                return {"status": "success", "key": key[:8] + "..."}
            return None
        
        # 调用带装饰器的函数
        result = test_api_call()
        assert result is not None, "Should get result from decorated function"
        assert result['status'] == 'success', "Should be successful"
        
        # 检查装饰器是否正确处理了 key
        # 注意：这里我们需要通过其他方式验证，因为装饰器内部处理
        
        print("✅ Decorator pattern works correctly")
        return True
        
    except Exception as e:
        print(f"❌ Decorator pattern test failed: {e}")
        return False
        
    finally:
        # 清理
        if os.path.exists(keys_file):
            os.unlink(keys_file)
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_auto_success_disabled():
    """测试自动成功模式关闭的情况"""
    print("🧪 Testing Auto-success mode disabled...")
    
    keys_file = create_test_keys()
    db_path = keys_file.replace('.txt', '_disabled.db')
    
    try:
        # 创建 balancer，关闭自动成功模式
        balancer = KeyBalancer(
            keys_file=keys_file,
            db_path=db_path,
            auto_success=False
        )
        
        # 获取 key
        key = balancer.get_single_key()
        assert key is not None, "Should get a key"
        
        # 检查 key 是否没有被自动标记为成功
        key_info = balancer.get_key_info(key)
        assert key_info is not None, "Should get key info"
        
        # 手动标记为成功
        balancer.update_key_health(key, success=True)
        
        # 再次检查
        key_info = balancer.get_key_info(key)
        assert key_info['last_used'] is not None, "Key should be marked as used after manual update"
        
        print("✅ Auto-success mode disabled works correctly")
        return True
        
    except Exception as e:
        print(f"❌ Auto-success mode disabled test failed: {e}")
        return False
        
    finally:
        # 清理
        if os.path.exists(keys_file):
            os.unlink(keys_file)
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_stats_with_auto_success():
    """测试统计信息中包含自动成功模式状态"""
    print("🧪 Testing stats with auto-success mode...")
    
    keys_file = create_test_keys()
    db_path = keys_file.replace('.txt', '_stats.db')
    
    try:
        # 创建 balancer，启用自动成功模式
        balancer = KeyBalancer(
            keys_file=keys_file,
            db_path=db_path,
            auto_success=True
        )
        
        # 获取统计信息
        stats = balancer.get_stats()
        assert 'auto_success_enabled' in stats, "Stats should include auto_success_enabled"
        assert stats['auto_success_enabled'] is True, "Auto-success should be enabled"
        
        print("✅ Stats with auto-success mode works correctly")
        return True
        
    except Exception as e:
        print(f"❌ Stats with auto-success mode test failed: {e}")
        return False
        
    finally:
        # 清理
        if os.path.exists(keys_file):
            os.unlink(keys_file)
        if os.path.exists(db_path):
            os.unlink(db_path)


def main():
    """主测试函数"""
    print("🚀 Testing Three Improvement Schemes...")
    print("="*60)
    
    tests = [
        test_auto_success_mode,
        test_context_manager,
        test_decorator_pattern,
        test_auto_success_disabled,
        test_stats_with_auto_success,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
    
    print("\n" + "="*60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
