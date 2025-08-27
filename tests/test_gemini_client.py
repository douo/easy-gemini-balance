#!/usr/bin/env python3
"""
测试 Gemini 客户端功能
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# 添加项目根目录到 Python 路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from easy_gemini_balance import GeminiClientWrapper, create_gemini_wrapper, KeyBalancer


class TestGeminiClientWrapper:
    """测试 GeminiClientWrapper 类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        # 创建临时文件
        self.temp_dir = tempfile.mkdtemp()
        self.keys_file = os.path.join(self.temp_dir, "test_keys.txt")
        self.db_path = os.path.join(self.temp_dir, "test.db")
        
        # 创建测试 keys 文件
        with open(self.keys_file, "w") as f:
            f.write("AIzaSyTest_Key1_abcdefghijklmnopqrstuvwxyz:1.0\n")
            f.write("AIzaSyTest_Key2_0987654321zyxwvutsrqponmlkj:1.1\n")
            f.write("AIzaSyTest_Key3_xyzabc123def456ghi789jkl:1.2\n")
        
        # Mock google.genai 模块
        self.genai_patcher = patch('easy_gemini_balance.gemini_client.GEMINI_AVAILABLE', True)
        self.genai_patcher.start()
        
        # 创建 KeyBalancer 实例
        self.balancer = KeyBalancer(keys_file=self.keys_file, db_path=self.db_path)
        
        # 创建 GeminiClientWrapper 实例
        self.wrapper = GeminiClientWrapper(
            balancer=self.balancer,
            max_retries=2,
            retry_delay=0.1,
            backoff_factor=2.0
        )
    
    def teardown_method(self):
        """每个测试方法后的清理"""
        # 停止 mock
        self.genai_patcher.stop()
        
        # 清理临时文件
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_init(self):
        """测试初始化"""
        assert self.wrapper.balancer == self.balancer
        assert self.wrapper.max_retries == 2
        assert self.wrapper.retry_delay == 0.1
        assert self.wrapper.backoff_factor == 2.0
        assert self.wrapper._current_client is None
        assert self.wrapper._current_key is None
    
    def test_create_client(self):
        """测试创建客户端"""
        api_key = "test_key"
        client = self.wrapper._create_client(api_key)
        assert client is not None
    
    def test_get_new_client(self):
        """测试获取新的客户端"""
        api_key, client = self.wrapper._get_new_client()
        assert api_key is not None
        assert client is not None
        assert api_key in self.balancer.key_manager.keys
    
    def test_extract_error_code(self):
        """测试错误代码提取"""
        # 测试不同类型的错误
        mock_error = Mock()
        mock_error.status_code = 429
        assert self.wrapper._extract_error_code(mock_error) == 429
        
        # 测试字符串匹配
        quota_error = Exception("Quota exceeded for this API key")
        assert self.wrapper._extract_error_code(quota_error) == 429
        
        unauthorized_error = Exception("Unauthorized access")
        assert self.wrapper._extract_error_code(unauthorized_error) == 401
        
        # 测试默认错误代码
        unknown_error = Exception("Unknown error")
        assert self.wrapper._extract_error_code(unknown_error) == 500
    
    def test_handle_error(self):
        """测试错误处理"""
        api_key = "test_key"
        error = Exception("Test error")
        
        # Mock update_key_health 方法
        with patch.object(self.balancer, 'update_key_health') as mock_update:
            self.wrapper._handle_error(api_key, error, 0)
            mock_update.assert_called_once_with(api_key, error_code=500)
    
    def test_execute_with_retry_success(self):
        """测试重试执行成功"""
        def successful_operation(client, *args, **kwargs):
            return "success"
        
        result = self.wrapper.execute_with_retry(successful_operation, "arg1", kwarg1="value1")
        assert result == "success"
        
        # 验证 key 被标记为成功
        current_key = self.wrapper.get_current_key()
        assert current_key is not None
    
    def test_execute_with_retry_failure(self):
        """测试重试执行失败"""
        def failing_operation(client, *args, **kwargs):
            raise Exception("Operation failed")
        
        with pytest.raises(Exception, match="Operation failed"):
            self.wrapper.execute_with_retry(failing_operation, "arg1")
    
    def test_client_context_success(self):
        """测试上下文管理器成功"""
        with self.wrapper.client_context() as client:
            assert client is not None
            assert self.wrapper.get_current_key() is not None
        
        # 验证 key 被标记为成功
        current_key = self.wrapper.get_current_key()
        assert current_key is not None
    
    def test_client_context_failure(self):
        """测试上下文管理器失败"""
        with pytest.raises(Exception):
            with self.wrapper.client_context() as client:
                raise Exception("Context error")
    
    def test_with_retry_decorator(self):
        """测试重试装饰器"""
        @self.wrapper.with_retry(max_retries=1)
        def test_function(client, message):
            return f"Processed: {message}"
        
        result = test_function("Hello")
        assert result == "Processed: Hello"
    
    def test_get_current_client_and_key(self):
        """测试获取当前客户端和 key"""
        # 初始状态
        assert self.wrapper.get_current_client() is None
        assert self.wrapper.get_current_key() is None
        
        # 执行操作后
        def test_operation(client, *args):
            return "test"
        
        self.wrapper.execute_with_retry(test_operation)
        
        assert self.wrapper.get_current_client() is not None
        assert self.wrapper.get_current_key() is not None


class TestCreateGeminiWrapper:
    """测试便捷函数"""
    
    def test_create_gemini_wrapper(self):
        """测试创建包装器"""
        with tempfile.TemporaryDirectory() as temp_dir:
            keys_file = os.path.join(temp_dir, "keys.txt")
            db_path = os.path.join(temp_dir, "test.db")
            
            # 创建测试 keys 文件
            with open(keys_file, "w") as f:
                f.write("AIzaSyTest_Key1_abcdefghijklmnopqrstuvwxyz:1.0\n")
            
            # Mock google.genai 模块
            with patch('easy_gemini_balance.gemini_client.GEMINI_AVAILABLE', True):
                wrapper = create_gemini_wrapper(
                    keys_file=keys_file,
                    db_path=db_path,
                    max_retries=5,
                    retry_delay=2.0,
                    backoff_factor=3.0
                )
                
                assert isinstance(wrapper, GeminiClientWrapper)
                assert wrapper.max_retries == 5
                assert wrapper.retry_delay == 2.0
                assert wrapper.backoff_factor == 3.0
                assert wrapper.balancer is not None


class TestGeminiClientIntegration:
    """测试集成功能"""
    
    def test_full_workflow(self):
        """测试完整工作流程"""
        with tempfile.TemporaryDirectory() as temp_dir:
            keys_file = os.path.join(temp_dir, "keys.txt")
            db_path = os.path.join(temp_dir, "test.db")
            
            # 创建测试 keys 文件
            with open(keys_file, "w") as f:
                f.write("AIzaSyTest_Key1_abcdefghijklmnopqrstuvwxyz:1.0\n")
                f.write("AIzaSyTest_Key2_0987654321zyxwvutsrqponmlkj:1.1\n")
            
            # Mock google.genai 模块
            with patch('easy_gemini_balance.gemini_client.GEMINI_AVAILABLE', True):
                wrapper = create_gemini_wrapper(
                    keys_file=keys_file,
                    db_path=db_path,
                    max_retries=1
                )
                
                # 测试成功操作
                def success_op(client, message):
                    return f"Success: {message}"
                
                result = wrapper.execute_with_retry(success_op, "Hello")
                assert result == "Success: Hello"
                
                # 测试失败操作
                def fail_op(client, message):
                    raise Exception("Simulated failure")
                
                with pytest.raises(Exception):
                    wrapper.execute_with_retry(fail_op, "Hello")
                
                # 查看统计信息
                stats = wrapper.balancer.get_stats()
                assert stats['total_keys'] == 2
                assert stats['available_keys'] >= 1


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
