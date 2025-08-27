"""
API Key Manager for handling key loading, storage, and weight management.
"""

import os
import sqlite3
import hashlib
import threading
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
import time


@dataclass
class APIKey:
    """Represents an API key with its metadata and health status."""
    
    key: str
    weight: float = 1.0
    max_weight: float = 10.0
    min_weight: float = 0.1
    is_available: bool = True
    last_used: Optional[datetime] = None
    last_error: Optional[datetime] = None
    error_count: int = 0
    consecutive_errors: int = 0
    added_time: datetime = field(default_factory=datetime.now)
    
    def mark_used(self):
        """Mark the key as recently used."""
        self.last_used = datetime.now()
    
    def mark_error(self, error_code: int):
        """Mark the key with an error and adjust weight accordingly."""
        self.last_error = datetime.now()
        self.error_count += 1
        self.consecutive_errors += 1
        
        if error_code == 400:
            # 400 错误表示 key 不可用
            self.is_available = False
        elif error_code in [403, 429, 500, 502, 503, 504]:
            # 其他错误码降低权重
            self.weight = max(self.min_weight, self.weight * 0.8)
        else:
            # 其他错误码轻微降低权重
            self.weight = max(self.min_weight, self.weight * 0.9)
    
    def mark_success(self):
        """Mark the key as successful and potentially increase weight."""
        self.consecutive_errors = 0
        if self.weight < self.max_weight:
            self.weight = min(self.max_weight, self.weight * 1.1)
    
    def reset_weight(self):
        """Reset the key weight to default."""
        self.weight = 1.0
        self.is_available = True
        self.consecutive_errors = 0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'key': self.key,
            'weight': self.weight,
            'is_available': self.is_available,
            'error_count': self.error_count,
            'consecutive_errors': self.consecutive_errors,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'last_error': self.last_error.isoformat() if self.last_error else None,
            'added_time': self.added_time.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'APIKey':
        """Create from dictionary for deserialization."""
        key = cls(
            key=data['key'],
            weight=data.get('weight', 1.0),
            is_available=data.get('is_available', True),
            error_count=data.get('error_count', 0),
            consecutive_errors=data.get('consecutive_errors', 0),
        )
        
        if data.get('last_used'):
            key.last_used = datetime.fromisoformat(data['last_used'])
        if data.get('last_error'):
            key.last_error = datetime.fromisoformat(data['last_error'])
        if data.get('added_time'):
            key.added_time = datetime.fromisoformat(data['added_time'])
        
        return key


class SQLiteKeyStore:
    """SQLite-based key storage for efficient persistence."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.lock = threading.RLock()
        self._init_database()
    
    def _init_database(self):
        """Initialize the database with required tables."""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建keys表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_keys (
                    key TEXT PRIMARY KEY,
                    weight REAL DEFAULT 1.0,
                    is_available INTEGER DEFAULT 1,
                    error_count INTEGER DEFAULT 0,
                    consecutive_errors INTEGER DEFAULT 0,
                    last_used TEXT,
                    last_error TEXT,
                    added_time TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_time TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建索引以提高查询性能
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_available ON api_keys(is_available)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_weight ON api_keys(weight)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_last_used ON api_keys(last_used)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_error_count ON api_keys(error_count)')
            
            # 创建文件变更记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS file_changes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    file_hash TEXT NOT NULL,
                    change_time TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
    
    def save_keys(self, keys: List[APIKey]):
        """Save keys to database efficiently using batch operations."""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                # 使用事务进行批量插入/更新
                cursor.execute('BEGIN TRANSACTION')
                
                for key in keys:
                    cursor.execute('''
                        INSERT OR REPLACE INTO api_keys 
                        (key, weight, is_available, error_count, consecutive_errors, 
                         last_used, last_error, added_time, updated_time)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        key.key,
                        key.weight,
                        1 if key.is_available else 0,
                        key.error_count,
                        key.consecutive_errors,
                        key.last_used.isoformat() if key.last_used else None,
                        key.last_error.isoformat() if key.last_error else None,
                        key.added_time.isoformat(),
                        datetime.now().isoformat()
                    ))
                
                cursor.execute('COMMIT')
                
            except Exception as e:
                cursor.execute('ROLLBACK')
                raise e
            finally:
                conn.close()
    
    def load_keys(self) -> List[APIKey]:
        """Load all keys from database."""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT key, weight, is_available, error_count, consecutive_errors,
                       last_used, last_error, added_time
                FROM api_keys
                ORDER BY key
            ''')
            
            keys = []
            for row in cursor.fetchall():
                key = APIKey(
                    key=row[0],
                    weight=row[1],
                    is_available=bool(row[2]),
                    error_count=row[3],
                    consecutive_errors=row[4]
                )
                
                if row[5]:  # last_used
                    key.last_used = datetime.fromisoformat(row[5])
                if row[6]:  # last_error
                    key.last_error = datetime.fromisoformat(row[6])
                if row[7]:  # added_time
                    key.added_time = datetime.fromisoformat(row[7])
                
                keys.append(key)
            
            conn.close()
            return keys
    
    def update_key(self, key: APIKey):
        """Update a single key in the database."""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE api_keys SET
                    weight = ?, is_available = ?, error_count = ?, consecutive_errors = ?,
                    last_used = ?, last_error = ?, updated_time = ?
                WHERE key = ?
            ''', (
                key.weight,
                1 if key.is_available else 0,
                key.error_count,
                key.consecutive_errors,
                key.last_used.isoformat() if key.last_used else None,
                key.last_error.isoformat() if key.last_error else None,
                datetime.now().isoformat(),
                key.key
            ))
            
            conn.commit()
            conn.close()
    
    def record_file_change(self, file_path: str, file_hash: str):
        """Record file change for change detection."""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO file_changes (file_path, file_hash, change_time)
                VALUES (?, ?, ?)
            ''', (file_path, file_hash, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
    
    def get_last_file_hash(self, file_path: str) -> Optional[str]:
        """Get the last recorded hash for a file."""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT file_hash FROM file_changes 
                WHERE file_path = ? 
                ORDER BY change_time DESC 
                LIMIT 1
            ''', (file_path,))
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else None
    
    def cleanup_old_keys(self, days_old: int) -> int:
        """Remove keys that haven't been used for specified days."""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_date = (datetime.now() - timedelta(days=days_old)).isoformat()
            
            cursor.execute('''
                DELETE FROM api_keys 
                WHERE last_used < ? AND last_used IS NOT NULL
            ''', (cutoff_date,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            return deleted_count
    
    def get_stats(self) -> Dict:
        """Get database statistics."""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 总key数量
            cursor.execute('SELECT COUNT(*) FROM api_keys')
            total_keys = cursor.fetchone()[0]
            
            # 可用key数量
            cursor.execute('SELECT COUNT(*) FROM api_keys WHERE is_available = 1')
            available_keys = cursor.fetchone()[0]
            
            # 平均权重
            cursor.execute('SELECT AVG(weight) FROM api_keys')
            avg_weight = cursor.fetchone()[0] or 0
            
            # 数据库大小
            cursor.execute('PRAGMA page_count')
            page_count = cursor.fetchone()[0]
            cursor.execute('PRAGMA page_size')
            page_size = cursor.fetchone()[0]
            db_size_bytes = page_count * page_size
            
            conn.close()
            
            return {
                'total_keys': total_keys,
                'available_keys': available_keys,
                'unavailable_keys': total_keys - available_keys,
                'average_weight': round(avg_weight, 2),
                'database_size_bytes': db_size_bytes,
                'database_size_mb': round(db_size_bytes / (1024 * 1024), 2)
            }


class KeyManager:
    """Manages API keys loaded from text files with weight and health tracking."""
    
    def __init__(self, keys_file: str = "keys.txt", db_path: str = "keys.db", 
                 auto_save: bool = True, save_interval: int = 300):
        """
        Initialize the key manager.
        
        Args:
            keys_file: Path to the text file containing API keys (one per line)
            db_path: Path to the SQLite database for persisting key states
            auto_save: Whether to automatically save state periodically
            save_interval: Auto-save interval in seconds
        """
        self.keys_file = keys_file
        self.db_path = db_path
        self.auto_save = auto_save
        self.save_interval = save_interval
        
        self.keys: List[APIKey] = []
        self.keys_set: Set[str] = set()  # 用于快速查找
        self.file_hash: Optional[str] = None
        self.last_save_time = datetime.now()
        self.lock = threading.RLock()  # 读写锁
        
        # 初始化SQLite存储
        self.key_store = SQLiteKeyStore(db_path)
        
        # 加载持久化状态和keys文件
        self._load_persisted_state()
        self._load_keys()
        
        # 启动自动保存线程
        if self.auto_save:
            self._start_auto_save()
    
    def _get_file_hash(self, file_path: str) -> str:
        """Calculate MD5 hash of file content."""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                return hashlib.md5(content).hexdigest()
        except (FileNotFoundError, IOError):
            return ""
    
    def _load_persisted_state(self):
        """Load persisted key states from SQLite database."""
        try:
            self.keys = self.key_store.load_keys()
            self.keys_set = {key.key for key in self.keys}
            
            if self.keys:
                print(f"✅ Loaded {len(self.keys)} keys from database: {self.db_path}")
            else:
                print("ℹ️  No persisted keys found in database")
                
        except Exception as e:
            print(f"⚠️  Error loading from database: {e}, starting fresh")
            self.keys = []
            self.keys_set = set()
    
    def _save_state(self):
        """Save current key states to SQLite database."""
        try:
            if self.keys:
                self.key_store.save_keys(self.keys)
                self.last_save_time = datetime.now()
                
        except Exception as e:
            print(f"❌ Error saving to database: {e}")
    
    def _start_auto_save(self):
        """Start background thread for auto-saving state."""
        def auto_save_worker():
            while True:
                try:
                    time.sleep(self.save_interval)
                    if self.auto_save:
                        self._save_state()
                except Exception as e:
                    print(f"⚠️  Auto-save error: {e}")
        
        save_thread = threading.Thread(target=auto_save_worker, daemon=True)
        save_thread.start()
    
    def _load_keys(self):
        """Load API keys from the text file and merge with existing state."""
        if not os.path.exists(self.keys_file):
            raise FileNotFoundError(f"Keys file not found: {self.keys_file}")
        
        # 计算文件hash
        current_hash = self._get_file_hash(self.keys_file)
        last_hash = self.key_store.get_last_file_hash(self.keys_file)
        
        if current_hash == last_hash:
            print("ℹ️  Keys file unchanged, skipping reload")
            return
        
        self.file_hash = current_hash
        self.key_store.record_file_change(self.keys_file, current_hash)
        
        with open(self.keys_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        new_keys = []
        new_keys_set = set()
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if line and not line.startswith('#'):
                # 支持权重格式: key:weight 或 key
                if ':' in line:
                    key_part, weight_part = line.split(':', 1)
                    try:
                        weight = float(weight_part.strip())
                    except ValueError:
                        weight = 1.0
                    key_str = key_part.strip()
                else:
                    key_str = line
                    weight = 1.0
                
                new_keys_set.add(key_str)
                
                # 检查是否已存在
                if key_str in self.keys_set:
                    # 更新现有key的权重（如果文件中的权重不同）
                    existing_key = next(k for k in self.keys if k.key == key_str)
                    if abs(existing_key.weight - weight) > 0.01:  # 允许小的浮点误差
                        existing_key.weight = weight
                        print(f"ℹ️  Updated weight for key {key_str[:8]}... to {weight}")
                else:
                    # 创建新key
                    new_key = APIKey(key=key_str, weight=weight)
                    new_keys.append(new_key)
                    print(f"➕ Added new key {key_str[:8]}... with weight {weight}")
        
        # 标记在文件中找不到的key为不可用
        removed_count = 0
        for key in self.keys:
            if key.key not in new_keys_set:
                if key.is_available:
                    key.is_available = False
                    removed_count += 1
                    print(f"❌ Marked key {key.key[:8]}... as unavailable (not in file)")
        
        # 添加新keys
        self.keys.extend(new_keys)
        self.keys_set.update(new_keys_set)
        
        print(f"✅ Keys file reloaded: {len(new_keys)} new keys, {removed_count} marked unavailable")
        print(f"📊 Total keys: {len(self.keys)}, Available: {len(self.get_available_keys())}")
        
        # 保存更新后的状态
        self._save_state()
    
    def reload_keys(self):
        """Reload keys from the file."""
        with self.lock:
            self._load_keys()
    
    def get_available_keys(self) -> List[APIKey]:
        """Get all available keys."""
        with self.lock:
            return [key for key in self.keys if key.is_available]
    
    def get_key_by_value(self, key_value: str) -> Optional[APIKey]:
        """Get an APIKey object by its key value."""
        with self.lock:
            if key_value in self.keys_set:
                return next((key for key in self.keys if key.key == key_value), None)
            return None
    
    def update_key_health(self, key_value: str, error_code: Optional[int] = None, success: bool = False):
        """
        Update the health status of a key.
        
        Args:
            key_value: The actual key string
            error_code: HTTP error code if an error occurred
            success: Whether the request was successful
        """
        with self.lock:
            key = self.get_key_by_value(key_value)
            if key:
                if success:
                    key.mark_success()
                elif error_code is not None:
                    key.mark_error(error_code)
                
                # 如果状态发生重要变化，立即保存
                if not key.is_available or key.consecutive_errors > 5:
                    self.key_store.update_key(key)
    
    def get_key_stats(self) -> Dict:
        """Get statistics about all keys."""
        with self.lock:
            db_stats = self.key_store.get_stats()
            
            return {
                'total_keys': db_stats['total_keys'],
                'available_keys': db_stats['available_keys'],
                'unavailable_keys': db_stats['unavailable_keys'],
                'average_weight': db_stats['average_weight'],
                'database_size_mb': db_stats['database_size_mb'],
                'last_save': self.last_save_time.isoformat(),
                'file_hash': self.file_hash,
                'keys': [
                    {
                        'key': key.key[:8] + '...' if len(key.key) > 8 else key.key,
                        'weight': round(key.weight, 2),
                        'available': key.is_available,
                        'error_count': key.error_count,
                        'consecutive_errors': key.consecutive_errors,
                        'last_used': key.last_used.isoformat() if key.last_used else None,
                        'last_error': key.last_error.isoformat() if key.last_error else None,
                        'added_time': key.added_time.isoformat(),
                    }
                    for key in self.keys
                ]
            }
    
    def save_state_now(self):
        """Manually save state immediately."""
        self._save_state()
    
    def reset_all_weights(self):
        """Reset weights for all keys."""
        with self.lock:
            for key in self.keys:
                key.reset_weight()
            self._save_state()
    
    def cleanup_old_keys(self, days_old: int = 30):
        """Remove keys that haven't been used for specified days."""
        with self.lock:
            removed_count = self.key_store.cleanup_old_keys(days_old)
            
            if removed_count > 0:
                # 从内存中移除
                self.keys = [key for key in self.keys if key.last_used is None or 
                           (datetime.now() - key.last_used).days < days_old]
                self.keys_set = {key.key for key in self.keys}
                print(f"🧹 Cleaned up {removed_count} old unused keys")
            
            return removed_count
    
    def get_memory_usage(self) -> Dict:
        """Get memory usage statistics."""
        import sys
        
        with self.lock:
            total_size = sum(sys.getsizeof(key) for key in self.keys)
            key_sizes = [sys.getsizeof(key.key) for key in self.keys]
            
            return {
                'total_keys': len(self.keys),
                'total_memory_bytes': total_size,
                'average_key_size_bytes': sum(key_sizes) / len(key_sizes) if key_sizes else 0,
                'estimated_1000_keys_memory_mb': (total_size / len(self.keys) * 1000) / (1024 * 1024) if self.keys else 0,
                'database_size_mb': self.key_store.get_stats()['database_size_mb']
            }
