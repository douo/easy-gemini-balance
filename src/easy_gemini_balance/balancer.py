"""
Key Balancer with LRU caching and weight-based selection using SSOT pattern.
All data is stored in and retrieved from SQLite database.
"""

import random
import time
import functools
from typing import List, Optional, Tuple, Callable, Any, Dict
from collections import OrderedDict
from datetime import datetime

from .key_manager import KeyManager, APIKey


class LRUCache:
    """Simple LRU cache implementation optimized for large key sets."""
    
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = OrderedDict()
        self.access_count = 0
    
    def get(self, key: str) -> Optional[APIKey]:
        """Get an item from cache and mark it as recently used."""
        if key in self.cache:
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            self.access_count += 1
            return self.cache[key]
        return None
    
    def put(self, key: str, value: APIKey):
        """Put an item in cache."""
        if key in self.cache:
            # Move to end (most recently used)
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.capacity:
                # Remove least recently used item
                self.cache.popitem(last=False)
        self.cache[key] = value
    
    def clear(self):
        """Clear the cache."""
        self.cache.clear()
        self.access_count = 0
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        return {
            'size': len(self.cache),
            'capacity': self.capacity,
            'hit_rate': self.access_count / max(len(self.cache), 1),
            'access_count': self.access_count
        }


class KeyContext:
    """Context manager for automatic key health management."""
    
    def __init__(self, balancer, keys: List[str]):
        self.balancer = balancer
        self.keys = keys
        self.success = False
    
    def __enter__(self):
        return self.keys
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            # 没有异常，自动标记为成功
            self.success = True
            for key in self.keys:
                self.balancer._mark_key_success(key)
        else:
            # 有异常，可以在这里处理失败情况
            # 注意：这里不自动标记失败，因为用户可能需要根据具体错误码处理
            pass


class KeyBalancer:
    """
    Main key balancer that provides LRU caching and weight-based key selection.
    Optimized for large key sets (1000+ keys) with SQLite persistence using SSOT pattern.
    
    Now supports three improvement schemes:
    1. Auto-success mode: automatically mark keys as successful when retrieved
    2. Context manager: automatic key health management with context
    3. Decorator pattern: automatic key health management with decorators
    """
    
    def __init__(self, cache_size: int = 100, db_path: Optional[str] = None, 
                 auto_save: bool = True, auto_success: bool = True):
        """
        Initialize the key balancer.
        
        Args:
            cache_size: Size of the LRU cache for recently used keys
            db_path: Path to the SQLite database (defaults to XDG_DATA_HOME)
            auto_save: Whether to automatically save state periodically
            auto_success: Whether to automatically mark keys as successful when retrieved
        """
        # 根据预期key数量自动调整缓存大小
        if cache_size < 100:
            cache_size = max(100, cache_size)
        
        self.key_manager = KeyManager(
            db_path=db_path,
            auto_save=auto_save
        )
        self.lru_cache = LRUCache(cache_size)
        self.last_selection_time = 0
        self.min_selection_interval = 0.05  # 降低最小选择间隔以支持大量key
        self.selection_count = 0
        self.auto_success = auto_success
        
        # 初始化权重分布相关属性
        self._cumulative_weights = []
        self._available_keys_list = []
        
        # 性能优化：预计算权重分布
        self._update_weight_distribution()
    
    def _mark_key_success(self, key_value: str):
        """Internal method: mark key as successful."""
        key_obj = self.key_manager.get_key_by_value(key_value)
        if key_obj:
            key_obj.last_used = datetime.now()
            # 可以在这里添加其他成功逻辑，比如增加权重等
    
    def _update_weight_distribution(self):
        """Update the weight distribution with proper LRU selection."""
        available_keys = self.key_manager.get_available_keys()
        if not available_keys:
            self._available_keys_list = []
            self._cumulative_weights = []
            return
        
        # 按 LRU 原则排序：last_used 为 None 的排在前面（从未使用过），然后按 last_used 升序
        lru_sorted_keys = sorted(available_keys, key=lambda k: (k.last_used is None, k.last_used or datetime.min))
        
        # 过滤掉最近有 429 错误的 keys（冷却期）
        current_time = datetime.now()
        filtered_keys = []
        
        for key in lru_sorted_keys:
            # 如果最近有 429 错误，检查是否在冷却期内
            if key.last_error and key.weight <= 0.2:  # 权重很低说明可能有 429 错误
                time_since_error = current_time - key.last_error
                if time_since_error.total_seconds() < 300:  # 5分钟冷却期
                    continue  # 跳过这个 key
            filtered_keys.append(key)
        
        # 如果没有过滤后的 keys，使用原始列表
        if not filtered_keys:
            filtered_keys = lru_sorted_keys
        
        # 只选择前 5 个最少使用的 keys，避免总是选择相同的 key
        max_keys_to_consider = min(5, len(filtered_keys))
        selected_keys = filtered_keys[:max_keys_to_consider]
        
        # 更新权重分布
        self._available_keys_list = selected_keys
        self._cumulative_weights = []
        
        if selected_keys:
            # 计算总权重
            total_weight = sum(key.weight for key in selected_keys)
            if total_weight > 0:
                cumulative = 0
                for key in selected_keys:
                    cumulative += key.weight
                    self._cumulative_weights.append((cumulative, key))
    
    def _calculate_time_decay_weight(self, last_used: Optional[datetime], current_time: float) -> float:
        """
        计算基于时间的权重衰减。
        
        时间衰减规则：
        - 10秒内：降权 0.5
        - 1分钟内：降权 0.1
        - 使用指数下降：weight = base_weight * (0.5 ^ (time_diff / 10))
        
        Args:
            last_used: 上次使用时间（datetime对象）
            current_time: 当前时间戳（float）
            
        Returns:
            时间衰减权重（0.0 到 1.0 之间）
        """
        if last_used is None:
            return 1.0  # 从未使用过的key保持原权重
        
        # 将datetime转换为timestamp
        last_used_timestamp = last_used.timestamp()
        time_diff = current_time - last_used_timestamp
        
        if time_diff <= 0:
            return 1.0  # 刚刚使用过，保持原权重
        
        # 指数下降：以10秒为基准周期，0.5为衰减因子
        # weight = 0.5 ^ (time_diff / 10)
        decay_factor = 0.5
        time_period = 10.0  # 10秒
        
        time_decay_weight = decay_factor ** (time_diff / time_period)
        
        # 确保权重在合理范围内
        return max(0.01, min(1.0, time_decay_weight))
    
    def get_keys(self, count: int = 1) -> List[str]:
        """
        Get a specified number of available API keys using LRU and weight-based selection.
        Optimized for large key sets.
        
        Args:
            count: Number of keys to return
            
        Returns:
            List of API key strings
        """
        if count <= 0:
            return []
        
        # 每次获取keys时都更新权重分布（包含时间衰减）
        self._update_weight_distribution()
        
        if not self._available_keys_list:
            raise RuntimeError("No available API keys")
        
        if count > len(self._available_keys_list):
            # If requesting more keys than available, return all available
            count = len(self._available_keys_list)
        
        # Apply rate limiting to prevent too frequent selections
        current_time = time.time()
        if current_time - self.last_selection_time < self.min_selection_interval:
            time.sleep(self.min_selection_interval - (current_time - self.last_selection_time))
        
        selected_keys = []
        
        # 使用真正的 LRU 选择：选择最少使用的 keys
        if count >= len(self._available_keys_list):
            selected_keys = self._available_keys_list.copy()
        else:
            # 选择前 count 个最少使用的 keys
            selected_keys = self._available_keys_list[:count]
        
        # Update LRU cache and mark keys as used
        for key in selected_keys:
            self.lru_cache.put(key.key, key)
            # 从key_manager的keys列表中查找对应的key对象
            for original_key_obj in self.key_manager.keys:
                if original_key_obj.key == key.key:
                    original_key_obj.mark_used()
                    # 打印 key 使用信息
                    print(f"🔑 使用 Key: {key.key[:20]}... | 权重: {key.weight:.2f} | 总使用次数: {self.selection_count + 1}")
                    break
        
        self.last_selection_time = time.time()
        self.selection_count += 1
        
        # 方案1：自动成功模式
        key_strings = [key.key for key in selected_keys]
        if self.auto_success:
            for key_str in key_strings:
                self._mark_key_success(key_str)
        
        return key_strings
    
    def _fast_weighted_selection(self, keys: List[APIKey], count: int) -> List[APIKey]:
        """
        Fast weighted selection for large key sets using pre-computed cumulative weights.
        """
        if count >= len(keys):
            return keys.copy()
        
        # 使用预计算的权重分布
        self._update_weight_distribution()
        
        selected_keys = []
        available_keys = keys.copy()
        total_weight = sum(key.weight for key in available_keys)
        
        for _ in range(count):
            if not available_keys:
                break
            
            # 使用二分查找优化权重选择
            rand_val = random.uniform(0, total_weight)
            selected_key = self._binary_search_key(available_keys, rand_val)
            
            if selected_key:
                selected_keys.append(selected_key)
                available_keys.remove(selected_key)
                total_weight -= selected_key.weight
        
        return selected_keys
    
    def _binary_search_key(self, keys: List[APIKey], target_weight: float) -> Optional[APIKey]:
        """Binary search for key selection based on weight."""
        if not keys:
            return None
        
        left, right = 0, len(keys) - 1
        cumulative_weight = 0
        
        for i, key in enumerate(keys):
            cumulative_weight += key.weight
            if cumulative_weight >= target_weight:
                return key
        
        # Fallback to last key if not found
        return keys[-1] if keys else None
    
    def _standard_weighted_selection(self, keys: List[APIKey], count: int) -> List[APIKey]:
        """
        Standard weighted random selection for smaller key sets.
        """
        if count >= len(keys):
            return keys.copy()
        
        # Calculate total weight
        total_weight = sum(key.weight for key in keys)
        if total_weight <= 0:
            # Fallback to random selection if all weights are 0
            return random.sample(keys, count)
        
        selected_keys = []
        available_keys = keys.copy()
        
        for _ in range(count):
            if not available_keys:
                break
            
            # Weighted random selection
            rand_val = random.uniform(0, total_weight)
            cumulative_weight = 0
            
            for i, key in enumerate(available_keys):
                cumulative_weight += key.weight
                if cumulative_weight >= rand_val:
                    selected_keys.append(key)
                    available_keys.pop(i)
                    total_weight -= key.weight
                    break
        
        return selected_keys
    
    def get_single_key(self) -> str:
        """
        Get a single available API key.
        
        Returns:
            A single API key string
        """
        keys = self.get_keys(1)
        return keys[0] if keys else None
    
    def get_key_context(self, count: int = 1) -> KeyContext:
        """
        Get a context manager for automatic key health management.
        
        Args:
            count: Number of keys to return
            
        Returns:
            KeyContext object that can be used as a context manager
        """
        keys = self.get_keys(count)
        return KeyContext(self, keys)
    
    # 方案3：装饰器模式
    def with_key_balancing(self, key_count: int = 1, auto_success: bool = None):
        """
        Decorator for automatic key health management.
        
        Args:
            key_count: Number of keys to use
            auto_success: Whether to auto-mark as successful (defaults to instance setting)
            
        Returns:
            Decorator function
        """
        if auto_success is None:
            auto_success = self.auto_success
            
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # 获取 key
                keys = self.get_keys(key_count)
                
                try:
                    # 执行 API 调用
                    result = func(*args, **kwargs)
                    # 自动标记为成功
                    if auto_success:
                        for key in keys:
                            self._mark_key_success(key)
                    return result
                except Exception as e:
                    # 自动标记为失败（使用通用错误码500）
                    for key in keys:
                        self.update_key_health(key, error_code=500)
                    raise
            return wrapper
        return decorator
    
    def update_key_health(self, key_value: str, error_code: Optional[int] = None, success: bool = False):
        """
        Update the health status of a key.
        
        Args:
            key_value: The actual key string
            error_code: HTTP error code if an error occurred
            success: Whether the request was successful
        """
        self.key_manager.update_key_health(key_value, error_code, success)
        
        # 如果key状态发生重要变化，更新权重分布
        if error_code == 400 or (success and error_code is None):
            self._update_weight_distribution()
    
    def get_stats(self) -> dict:
        """
        Get statistics about the key balancer and all keys.
        
        Returns:
            Dictionary containing statistics
        """
        stats = self.key_manager.get_key_stats()
        cache_stats = self.lru_cache.get_stats()
        
        # 更新权重分布以获取当前状态
        self._update_weight_distribution()
        
        stats.update({
            'cache_stats': cache_stats,
            'last_selection_time': self.last_selection_time,
            'selection_count': self.selection_count,
            'min_selection_interval': self.min_selection_interval,
            'auto_success_enabled': self.auto_success,
            'current_top_weight_keys': len(self._available_keys_list) if hasattr(self, '_available_keys_list') else 0,
            'weight_distribution_updated': hasattr(self, '_cumulative_weights') and len(self._cumulative_weights) > 0,
        })
        
        return stats
    
    def reload_keys(self):
        """Reload keys from database."""
        self.key_manager._load_from_database()
        self.lru_cache.clear()
        self._update_weight_distribution()
    
    def reset_all_weights(self):
        """Reset weights for all keys."""
        self.key_manager.reset_all_weights()
        self.lru_cache.clear()
        self._update_weight_distribution()
    
    def get_key_info(self, key_value: str) -> Optional[dict]:
        """
        Get detailed information about a specific key.
        
        Args:
            key_value: The actual key string
            
        Returns:
            Dictionary containing key information or None if not found
        """
        key = self.key_manager.get_key_by_value(key_value)
        if not key:
            return None
        
        return {
            'key': key.key[:8] + '...' if len(key.key) > 8 else key.key,
            'weight': round(key.weight, 2),
            'available': key.is_available,
            'error_count': key.error_count,
            'consecutive_errors': key.consecutive_errors,
            'last_used': key.last_used.isoformat() if key.last_used else None,
            'last_error': key.last_error.isoformat() if key.last_error else None,
            'in_cache': key.key in self.lru_cache.cache,
            'added_time': key.added_time.isoformat(),
            'source': key.source,
        }
    
    def save_state_now(self):
        """Manually save state immediately."""
        self.key_manager.save_state_now()
    
    def cleanup_old_keys(self, days_old: int = 30):
        """Remove keys that haven't been used for specified days."""
        removed_count = self.key_manager.cleanup_old_keys(days_old)
        if removed_count > 0:
            self._update_weight_distribution()
        return removed_count
    
    def get_memory_usage(self) -> dict:
        """Get memory usage statistics."""
        return self.key_manager.get_memory_usage()
    
    def optimize_for_large_keysets(self, expected_keys: int = 1000):
        """
        Optimize the balancer for large key sets.
        
        Args:
            expected_keys: Expected number of keys for optimization
        """
        if expected_keys > 1000:
            # 对于大量key，调整缓存策略
            optimal_cache_size = min(expected_keys // 10, 1000)
            if optimal_cache_size != self.lru_cache.capacity:
                self.lru_cache = LRUCache(optimal_cache_size)
                print(f"🔄 Optimized cache size to {optimal_cache_size} for {expected_keys} keys")
            
            # 调整选择间隔
            self.min_selection_interval = max(0.01, 0.1 / (expected_keys / 100))
            print(f"🔄 Adjusted selection interval to {self.min_selection_interval:.3f}s")
    
    def batch_get_keys(self, batch_sizes: List[int]) -> List[List[str]]:
        """
        Get multiple batches of keys efficiently.
        
        Args:
            batch_sizes: List of batch sizes to retrieve
            
        Returns:
            List of key batches
        """
        total_requested = sum(batch_sizes)
        
        # 更新权重分布
        self._update_weight_distribution()
        
        if total_requested > len(self._available_keys_list):
            raise RuntimeError(f"Requested {total_requested} keys but only {len(self._available_keys_list)} available")
        
        # 一次性获取所有需要的keys
        all_keys = self.get_keys(total_requested)
        
        # 分割成批次
        batches = []
        start_idx = 0
        for batch_size in batch_sizes:
            end_idx = start_idx + batch_size
            batches.append(all_keys[start_idx:end_idx])
            start_idx = end_idx
        
        return batches
    
    def get_database_info(self) -> dict:
        """
        Get database-specific information.
        
        Returns:
            Dictionary containing database information
        """
        stats = self.key_manager.get_key_stats()
        return {
            'database_path': self.key_manager.db_path,
            'database_size_mb': stats.get('database_size_mb', 0),
            'total_keys_in_db': stats.get('total_keys', 0),
            'available_keys_in_db': stats.get('available_keys', 0),
            'average_weight': stats.get('average_weight', 0),
            'source_distribution': stats.get('source_distribution', {}),
        }
    

    


