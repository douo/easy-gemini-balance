"""
API Key Manager for handling key storage and weight management using SSOT pattern.
All data is stored in and retrieved from SQLite database.
"""

import os
import sqlite3
import threading
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
import time
from pathlib import Path


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
    source: str = "database"  # 来源标识：database, imported, manual
    
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
            'source': self.source,
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
            source=data.get('source', 'database'),
        )
        
        if data.get('last_used'):
            key.last_used = datetime.fromisoformat(data['last_used'])
        if data.get('last_error'):
            key.last_error = datetime.fromisoformat(data['last_error'])
        if data.get('added_time'):
            key.added_time = datetime.fromisoformat(data['added_time'])
        
        return key


class SQLiteKeyStore:
    """SQLite-based key storage for efficient persistence using SSOT pattern."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.lock = threading.RLock()
        self._init_database()
    
    def _init_database(self):
        """Initialize the database with required tables."""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建keys表，key字段设置为UNIQUE约束
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
                    updated_time TEXT DEFAULT CURRENT_TIMESTAMP,
                    source TEXT DEFAULT 'database'
                )
            ''')
            
            # 创建索引以提高查询性能
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_available ON api_keys(is_available)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_weight ON api_keys(weight)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_last_used ON api_keys(last_used)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_error_count ON api_keys(error_count)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_source ON api_keys(source)')
            
            # 创建导入历史表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS import_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_file TEXT NOT NULL,
                    import_time TEXT DEFAULT CURRENT_TIMESTAMP,
                    keys_count INTEGER DEFAULT 0,
                    new_keys INTEGER DEFAULT 0,
                    updated_keys INTEGER DEFAULT 0,
                    skipped_keys INTEGER DEFAULT 0
                )
            ''')
            
            conn.commit()
            conn.close()
    
    def insert_key(self, key: APIKey) -> bool:
        """
        Insert a new key into database.
        
        Args:
            key: APIKey object to insert
            
        Returns:
            True if inserted successfully, False if key already exists
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    INSERT INTO api_keys 
                    (key, weight, is_available, error_count, consecutive_errors, 
                     last_used, last_error, added_time, updated_time, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    key.key,
                    key.weight,
                    1 if key.is_available else 0,
                    key.error_count,
                    key.consecutive_errors,
                    key.last_used.isoformat() if key.last_used else None,
                    key.last_error.isoformat() if key.last_error else None,
                    key.added_time.isoformat(),
                    datetime.now().isoformat(),
                    key.source
                ))
                
                conn.commit()
                return True
                
            except sqlite3.IntegrityError:
                # Key already exists
                return False
            finally:
                conn.close()
    
    def upsert_key(self, key: APIKey) -> bool:
        """
        Insert or update a key in database.
        
        Args:
            key: APIKey object to insert/update
            
        Returns:
            True if operation successful
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO api_keys 
                    (key, weight, is_available, error_count, consecutive_errors, 
                     last_used, last_error, added_time, updated_time, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    key.key,
                    key.weight,
                    1 if key.is_available else 0,
                    key.error_count,
                    key.consecutive_errors,
                    key.last_used.isoformat() if key.last_used else None,
                    key.last_error.isoformat() if key.last_error else None,
                    key.added_time.isoformat(),
                    datetime.now().isoformat(),
                    key.source
                ))
                
                conn.commit()
                return True
                
            finally:
                conn.close()
    
    def get_key(self, key_value: str) -> Optional[APIKey]:
        """
        Get a specific key from database.
        
        Args:
            key_value: The actual key string
            
        Returns:
            APIKey object or None if not found
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT key, weight, is_available, error_count, consecutive_errors,
                       last_used, last_error, added_time, source
                FROM api_keys
                WHERE key = ?
            ''', (key_value,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                key = APIKey(
                    key=row[0],
                    weight=row[1],
                    is_available=bool(row[2]),
                    error_count=row[3],
                    consecutive_errors=row[4],
                    source=row[7]
                )
                
                if row[5]:  # last_used
                    key.last_used = datetime.fromisoformat(row[5])
                if row[6]:  # last_error
                    key.last_error = datetime.fromisoformat(row[6])
                if row[7]:  # added_time
                    key.added_time = datetime.fromisoformat(row[7])
                
                return key
            
            return None
    
    def get_all_keys(self) -> List[APIKey]:
        """Get all keys from database."""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT key, weight, is_available, error_count, consecutive_errors,
                       last_used, last_error, added_time, source
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
                    consecutive_errors=row[4],
                    source=row[7]
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
    
    def get_available_keys(self) -> List[APIKey]:
        """Get all available keys from database."""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT key, weight, is_available, error_count, consecutive_errors,
                       last_used, last_error, added_time, source
                FROM api_keys
                WHERE is_available = 1
                ORDER BY weight DESC, last_used ASC
            ''')
            
            keys = []
            for row in cursor.fetchall():
                key = APIKey(
                    key=row[0],
                    weight=row[1],
                    is_available=bool(row[2]),
                    error_count=row[3],
                    consecutive_errors=row[4],
                    source=row[7]
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
    
    def delete_key(self, key_value: str) -> bool:
        """
        Delete a key from database.
        
        Args:
            key_value: The actual key string
            
        Returns:
            True if deleted successfully, False if not found
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM api_keys WHERE key = ?', (key_value,))
            deleted = cursor.rowcount > 0
            
            conn.commit()
            conn.close()
            
            return deleted
    
    def import_keys_from_file(self, file_path: str, source: str = "imported") -> Dict:
        """
        Import keys from a text file into database.
        
        Args:
            file_path: Path to the text file containing API keys
            source: Source identifier for imported keys
            
        Returns:
            Dictionary with import statistics
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Keys file not found: {file_path}")
        
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                # 开始事务
                cursor.execute('BEGIN TRANSACTION')
                
                # 读取文件
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                new_keys = 0
                updated_keys = 0
                skipped_keys = 0
                
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
                        
                        # 检查key是否已存在
                        existing_key = self.get_key(key_str)
                        if existing_key:
                            # 更新现有key的权重
                            if abs(existing_key.weight - weight) > 0.01:
                                existing_key.weight = weight
                                self.update_key(existing_key)
                                updated_keys += 1
                            else:
                                skipped_keys += 1
                        else:
                            # 插入新key
                            new_key = APIKey(
                                key=key_str,
                                weight=weight,
                                source=source
                            )
                            if self.insert_key(new_key):
                                new_keys += 1
                            else:
                                skipped_keys += 1
                
                # 记录导入历史
                cursor.execute('''
                    INSERT INTO import_history 
                    (source_file, keys_count, new_keys, updated_keys, skipped_keys)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    file_path,
                    len(lines),
                    new_keys,
                    updated_keys,
                    skipped_keys
                ))
                
                # 提交事务
                cursor.execute('COMMIT')
                
                return {
                    'total_lines': len(lines),
                    'new_keys': new_keys,
                    'updated_keys': updated_keys,
                    'skipped_keys': skipped_keys,
                    'source': source
                }
                
            except Exception as e:
                cursor.execute('ROLLBACK')
                raise e
            finally:
                conn.close()
    
    def get_import_history(self) -> List[Dict]:
        """Get import history from database."""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT source_file, import_time, keys_count, new_keys, updated_keys, skipped_keys
                FROM import_history
                ORDER BY import_time DESC
            ''')
            
            history = []
            for row in cursor.fetchall():
                history.append({
                    'source_file': row[0],
                    'import_time': row[1],
                    'keys_count': row[2],
                    'new_keys': row[3],
                    'updated_keys': row[4],
                    'skipped_keys': row[5]
                })
            
            conn.close()
            return history
    
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
            
            # 按来源统计
            cursor.execute('SELECT source, COUNT(*) FROM api_keys GROUP BY source')
            source_stats = dict(cursor.fetchall())
            
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
                'source_distribution': source_stats,
                'database_size_bytes': db_size_bytes,
                'database_size_mb': round(db_size_bytes / (1024 * 1024), 2)
            }


class KeyManager:
    """Manages API keys using SSOT pattern - all data from database."""
    
    def __init__(self, db_path: Optional[str] = None, auto_save: bool = True, 
                 save_interval: int = 300):
        """
        Initialize the key manager.
        
        Args:
            db_path: Path to the SQLite database (defaults to XDG_DATA_HOME)
            auto_save: Whether to automatically save state periodically
            save_interval: Auto-save interval in seconds
        """
        if db_path is None:
            # 使用 XDG_DATA_HOME 目录
            xdg_data_home = os.environ.get('XDG_DATA_HOME')
            if xdg_data_home:
                data_dir = Path(xdg_data_home)
            else:
                data_dir = Path.home() / '.local' / 'share'
            
            # 创建 easy-gemini-balance 子目录
            data_dir = data_dir / 'easy-gemini-balance'
            data_dir.mkdir(parents=True, exist_ok=True)
            
            db_path = str(data_dir / 'keys.db')
        
        self.db_path = db_path
        self.auto_save = auto_save
        self.save_interval = save_interval
        
        self.keys: List[APIKey] = []
        self.keys_set: Set[str] = set()
        self.last_save_time = datetime.now()
        self.lock = threading.RLock()
        
        # 初始化SQLite存储
        self.key_store = SQLiteKeyStore(db_path)
        
        # 从数据库加载所有keys
        self._load_from_database()
        
        # 启动自动保存线程
        if self.auto_save:
            self._start_auto_save()
    
    def _load_from_database(self):
        """Load all keys from database."""
        try:
            self.keys = self.key_store.get_all_keys()
            self.keys_set = {key.key for key in self.keys}
            
            if self.keys:
                print(f"✅ Loaded {len(self.keys)} keys from database: {self.db_path}")
            else:
                print("ℹ️  No keys found in database")
                
        except Exception as e:
            print(f"⚠️  Error loading from database: {e}, starting fresh")
            self.keys = []
            self.keys_set = set()
    
    def _save_state(self):
        """Save current key states to database."""
        try:
            if self.keys:
                for key in self.keys:
                    self.key_store.update_key(key)
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
    
    # 核心数据库操作方法
    def import_keys_from_file(self, file_path: str, source: str = "imported") -> Dict:
        """
        Import keys from a text file into database.
        
        Args:
            file_path: Path to the text file containing API keys
            source: Source identifier for imported keys
            
        Returns:
            Dictionary with import statistics
        """
        result = self.key_store.import_keys_from_file(file_path, source)
        
        # 重新加载数据库
        self._load_from_database()
        
        return result
    
    def add_key(self, key_value: str, weight: float = 1.0, source: str = "manual") -> bool:
        """
        Add a new key manually.
        
        Args:
            key_value: The API key string
            weight: Key weight
            source: Source identifier
            
        Returns:
            True if added successfully, False if key already exists
        """
        if key_value in self.keys_set:
            return False
        
        new_key = APIKey(key=key_value, weight=weight, source=source)
        
        if self.key_store.insert_key(new_key):
            self.keys.append(new_key)
            self.keys_set.add(key_value)
            return True
        
        return False
    
    def remove_key(self, key_value: str) -> bool:
        """
        Remove a key.
        
        Args:
            key_value: The API key string
            
        Returns:
            True if removed successfully, False if not found
        """
        if key_value not in self.keys_set:
            return False
        
        if self.key_store.delete_key(key_value):
            self.keys = [k for k in self.keys if k.key != key_value]
            self.keys_set.remove(key_value)
            return True
        
        return False
    
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
                
                # 立即更新数据库
                self.key_store.update_key(key)
    
    def get_key_stats(self) -> Dict:
        """Get statistics about all keys."""
        db_stats = self.key_store.get_stats()
        
        return {
            'total_keys': db_stats['total_keys'],
            'available_keys': db_stats['available_keys'],
            'unavailable_keys': db_stats['unavailable_keys'],
            'average_weight': db_stats['average_weight'],
            'source_distribution': db_stats['source_distribution'],
            'database_size_mb': db_stats['database_size_mb'],
            'last_save': self.last_save_time.isoformat(),
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
                    'source': key.source,
                }
                for key in self.keys
            ]
        }
    
    def get_import_history(self) -> List[Dict]:
        """Get import history."""
        return self.key_store.get_import_history()
    
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
                # 重新加载数据库
                self._load_from_database()
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
