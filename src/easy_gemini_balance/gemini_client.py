#!/usr/bin/env python3
"""
Google Gemini API 客户端封装
提供自动重试、key 管理和错误处理功能
"""

import time
import functools
from typing import Callable, Any, Optional, Union, List
from contextlib import contextmanager

try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Warning: google-genai package not available. Install with: pip install google-genai")

from .balancer import KeyBalancer


class GeminiClientWrapper:
    """
    Google Gemini API 客户端包装器
    自动管理 API key 和重试逻辑
    """
    
    def __init__(
        self,
        balancer: KeyBalancer,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        backoff_factor: float = 2.0
    ):
        """
        初始化 Gemini 客户端包装器
        
        Args:
            balancer: KeyBalancer 实例，用于管理 API keys
            max_retries: 最大重试次数
            retry_delay: 初始重试延迟（秒）
            backoff_factor: 重试延迟的指数退避因子
        """
        if not GEMINI_AVAILABLE:
            raise ImportError("google-genai package is required. Install with: pip install google-genai")
        
        self.balancer = balancer
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.backoff_factor = backoff_factor
        self._current_client = None
        self._current_key = None
    
    def _create_client(self, api_key: str):
        """创建 Gemini 客户端"""
        return genai.Client(api_key=api_key)
    
    def _get_new_client(self) -> tuple:
        """获取新的 API key 和客户端"""
        api_key = self.balancer.get_single_key()
        client = self._create_client(api_key)
        return api_key, client
    
    def _handle_error(self, api_key: str, error: Exception, attempt: int):
        """处理错误，更新 key 健康状态"""
        error_code = self._extract_error_code(error)
        self.balancer.update_key_health(api_key, error_code=error_code)
        
        if attempt < self.max_retries:
            delay = self.retry_delay * (self.backoff_factor ** attempt)
            print(f"⚠️  API 调用失败 (尝试 {attempt + 1}/{self.max_retries})，等待 {delay:.1f} 秒后重试...")
            time.sleep(delay)
    
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
    
    def execute_with_retry(
        self,
        operation: Callable[[genai.Client], Any],
        *args,
        **kwargs
    ) -> Any:
        """
        执行操作，自动重试和 key 管理
        
        Args:
            operation: 接收 genai.Client 作为第一个参数的函数
            *args, **kwargs: 传递给 operation 的参数
        
        Returns:
            operation 的返回值
        
        Raises:
            Exception: 当所有重试都失败时抛出最后一个异常
        """
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
    
    @contextmanager
    def client_context(self):
        """
        上下文管理器，提供可重用的客户端
        
        使用方式:
        with wrapper.client_context() as client:
            result = client.generate_content("Hello")
        """
        try:
            api_key, client = self._get_new_client()
            self._current_key = api_key
            self._current_client = client
            
            yield client
            
            # 成功完成，标记 key 为健康
            self.balancer._mark_key_success(api_key)
            
        except Exception as e:
            # 发生异常，更新 key 健康状态
            if self._current_key:
                self._handle_error(self._current_key, e, 0)
            raise
    
    def with_retry(self, max_retries: Optional[int] = None):
        """
        装饰器，为函数添加自动重试和 key 管理功能
        
        Args:
            max_retries: 最大重试次数，如果为 None 则使用实例默认值
        
        Returns:
            装饰器函数
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # 从函数参数中提取 client 参数
                # 假设函数签名为 func(client, *args, **kwargs)
                if args and hasattr(args[0], 'generate_content'):
                    # 第一个参数是 client，直接调用
                    return func(*args, **kwargs)
                else:
                    # 需要创建新的 client
                    retry_count = max_retries if max_retries is not None else self.max_retries
                    
                    for attempt in range(retry_count + 1):
                        try:
                            api_key, client = self._get_new_client()
                            self._current_key = api_key
                            self._current_client = client
                            
                            # 将 client 作为第一个参数调用函数
                            result = func(client, *args, **kwargs)
                            
                            # 成功时标记 key 为健康
                            self.balancer._mark_key_success(api_key)
                            return result
                            
                        except Exception as e:
                            if attempt < retry_count:
                                self._handle_error(api_key, e, attempt)
                            else:
                                print(f"❌ 所有重试都失败了，最后错误: {e}")
                                self._handle_error(api_key, e, attempt)
                                raise
            return wrapper
        return decorator
    
    def get_current_client(self) -> Optional[genai.Client]:
        """获取当前客户端（如果存在）"""
        return self._current_client
    
    def get_current_key(self) -> Optional[str]:
        """获取当前 API key（如果存在）"""
        return self._current_key


# 便捷函数
def create_gemini_wrapper(
    keys_file: str,
    db_path: str,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    backoff_factor: float = 2.0,
    **balancer_kwargs
) -> GeminiClientWrapper:
    """
    创建 Gemini 客户端包装器的便捷函数
    
    Args:
        keys_file: API keys 文件路径
        db_path: 数据库文件路径
        max_retries: 最大重试次数
        retry_delay: 初始重试延迟
        backoff_factor: 重试延迟的指数退避因子
        **balancer_kwargs: 传递给 KeyBalancer 的其他参数
    
    Returns:
        GeminiClientWrapper 实例
    """
    balancer = KeyBalancer(keys_file=keys_file, db_path=db_path, **balancer_kwargs)
    return GeminiClientWrapper(
        balancer=balancer,
        max_retries=max_retries,
        retry_delay=retry_delay,
        backoff_factor=backoff_factor
    )
