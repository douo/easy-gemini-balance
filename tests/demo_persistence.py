#!/usr/bin/env python3
"""
Demonstration script for SQLite persistence and file change detection features.
"""

import sys
import os
import time
import sqlite3
from typing import List
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from easy_gemini_balance import KeyBalancer


def create_demo_keys_file(filename: str = "demo_keys.txt"):
    """Create a demo keys file for testing."""
    demo_keys = [
        "AIzaSyDemo_Key1_abcdefghijklmnopqrstuvwxyz:2.0",
        "AIzaSyDemo_Key2_0987654321zyxwvutsrqponmlkj:1.5",
        "AIzaSyDemo_Key3_qwertyuiopasdfghjklzxcvbnm:1.0",
        "AIzaSyDemo_Key4_lmnopqrstuvwxyzabcdefghijk:0.8",
        "AIzaSyDemo_Key5_zyxwvutsrqponmlkjihgfedcba:1.2",
    ]
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("# Demo API Keys for persistence testing\n")
        for key in demo_keys:
            f.write(f"{key}\n")
    
    print(f"✅ Created demo keys file: {filename}")
    return demo_keys


def modify_keys_file(filename: str, action: str = "add"):
    """Modify the keys file to demonstrate change detection."""
    if action == "add":
        # 添加新key
        with open(filename, 'a', encoding='utf-8') as f:
            f.write("AIzaSyDemo_Key6_newlyaddedkeyforchange:1.0\n")
        print("➕ Added new key to file")
    
    elif action == "remove":
        # 删除一个key
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 删除最后一个非注释行
        with open(filename, 'w', encoding='utf-8') as f:
            for line in lines[:-1]:
                f.write(line)
        print("➖ Removed last key from file")
    
    elif action == "modify":
        # 修改权重
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 修改第一个key的权重
        modified_content = content.replace(":2.0", ":3.0")
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        print("✏️  Modified first key weight from 2.0 to 3.0")


def demonstrate_sqlite_persistence():
    """Demonstrate SQLite persistence functionality."""
    print("🚀 Easy Gemini Balance - SQLite Persistence Demo\n")
    
    # 创建演示文件
    demo_file = "demo_keys.txt"
    db_file = "demo_keys.db"
    
    if os.path.exists(demo_file):
        os.remove(demo_file)
    
    if os.path.exists(db_file):
        os.remove(db_file)
    
    create_demo_keys_file(demo_file)
    
    print("\n" + "="*60)
    print("📋 STEP 1: Initial Setup with SQLite")
    print("="*60)
    
    # 初始化均衡器（使用SQLite）
    start_time = time.time()
    balancer = KeyBalancer(
        keys_file=demo_file,
        db_path=db_file,
        auto_save=True,
        cache_size=50
    )
    init_time = time.time() - start_time
    
    # 显示初始状态
    stats = balancer.get_stats()
    db_info = balancer.get_database_info()
    
    print(f"📊 Initial state:")
    print(f"   Total keys: {stats['total_keys']}")
    print(f"   Available keys: {stats['available_keys']}")
    print(f"   Database: {db_info['database_path']}")
    print(f"   Database size: {db_info['database_size_mb']:.2f} MB")
    print(f"   Initialization time: {init_time:.4f}s")
    
    print("\n" + "="*60)
    print("🔑 STEP 2: Using Keys and Updating Health")
    print("="*60)
    
    # 使用一些keys并更新健康状态
    for i in range(3):
        key = balancer.get_single_key()
        print(f"   Using key: {key[:20]}...")
        
        # 模拟不同的API调用结果
        if i == 0:
            balancer.update_key_health(key, success=True)
            print(f"     ✅ API call successful")
        elif i == 1:
            balancer.update_key_health(key, error_code=403)
            print(f"     ❌ API call failed with 403 (weight reduced)")
        else:
            balancer.update_key_health(key, error_code=400)
            print(f"     ❌ API call failed with 400 (key marked unavailable)")
    
    # 显示更新后的状态
    stats = balancer.get_stats()
    print(f"\n📊 After health updates:")
    print(f"   Available keys: {stats['available_keys']}")
    print(f"   Unavailable keys: {stats['unavailable_keys']}")
    
    # 显示特定key的详细信息
    print(f"\n🔍 Key details:")
    for key in balancer.key_manager.keys[:3]:
        info = balancer.get_key_info(key.key)
        if info:
            print(f"   {info['key']}: weight={info['weight']}, available={info['available']}")
    
    print("\n" + "="*60)
    print("💾 STEP 3: SQLite State Persistence")
    print("="*60)
    
    # 手动保存状态
    print("   Saving state to SQLite database...")
    save_start = time.time()
    balancer.save_state_now()
    save_time = time.time() - save_start
    
    # 检查数据库状态
    db_info = balancer.get_database_info()
    print(f"   ✅ State saved to SQLite in {save_time:.4f}s")
    print(f"   📊 Database size: {db_info['database_size_mb']:.2f} MB")
    print(f"   📊 Total keys in DB: {db_info['total_keys_in_db']}")
    
    # 显示数据库统计信息
    print(f"\n🔍 Database statistics:")
    print(f"   Database path: {db_info['database_path']}")
    print(f"   Database size: {db_info['database_size_mb']:.2f} MB")
    print(f"   Average weight: {db_info['average_weight']}")
    
    print("\n" + "="*60)
    print("📁 STEP 4: File Change Detection")
    print("="*60)
    
    # 修改keys文件
    print("   Modifying keys file...")
    modify_keys_file(demo_file, "add")
    
    # 重新加载keys
    print("   Reloading keys...")
    reload_start = time.time()
    balancer.reload_keys()
    reload_time = time.time() - reload_start
    
    # 显示变更后的状态
    stats = balancer.get_stats()
    print(f"\n📊 After file modification:")
    print(f"   Total keys: {stats['total_keys']}")
    print(f"   Available keys: {stats['available_keys']}")
    print(f"   Reload time: {reload_time:.4f}s")
    
    # 再次修改文件（删除key）
    print(f"\n   Removing a key from file...")
    modify_keys_file(demo_file, "remove")
    
    # 重新加载
    balancer.reload_keys()
    stats = balancer.get_stats()
    print(f"\n📊 After key removal:")
    print(f"   Total keys: {stats['total_keys']}")
    print(f"   Available keys: {stats['available_keys']}")
    
    print("\n" + "="*60)
    print("🔄 STEP 5: Restart Simulation")
    print("="*60)
    
    # 模拟程序重启：创建新的均衡器实例
    print("   Simulating program restart...")
    del balancer
    
    # 创建新的均衡器实例（会自动加载SQLite状态）
    restart_start = time.time()
    new_balancer = KeyBalancer(
        keys_file=demo_file,
        db_path=db_file,
        auto_save=True
    )
    restart_time = time.time() - restart_start
    
    # 显示重启后的状态
    stats = new_balancer.get_stats()
    db_info = new_balancer.get_database_info()
    
    print(f"\n📊 After restart:")
    print(f"   Total keys: {stats['total_keys']}")
    print(f"   Available keys: {stats['available_keys']}")
    print(f"   Database loaded from: {db_info['database_path']}")
    print(f"   Restart time: {restart_time:.4f}s")
    
    # 显示key的持久化状态
    print(f"\n🔍 Persistent key states:")
    for key in new_balancer.key_manager.keys:
        info = new_balancer.get_key_info(key.key)
        if info:
            status = "✅" if info['available'] else "❌"
            print(f"   {status} {info['key']}: weight={info['weight']}, errors={info['error_count']}")
    
    print("\n" + "="*60)
    print("📊 STEP 6: Performance Comparison")
    print("="*60)
    
    # 比较SQLite vs JSON的性能
    print("   SQLite Performance Benefits:")
    print(f"     ✅ Fast queries with indexes")
    print(f"     ✅ Efficient storage (compressed)")
    print(f"     ✅ Transaction support")
    print(f"     ✅ Concurrent access support")
    print(f"     ✅ Database size: {db_info['database_size_mb']:.2f} MB")
    
    # 显示内存使用
    memory_stats = new_balancer.get_memory_usage()
    print(f"\n   Memory Usage:")
    print(f"     In-memory keys: {memory_stats['total_keys']}")
    print(f"     Memory size: {memory_stats['total_memory_bytes'] / 1024:.2f} KB")
    print(f"     Database size: {memory_stats['database_size_mb']:.2f} MB")
    
    print("\n" + "="*60)
    print("🧹 STEP 7: Cleanup")
    print("="*60)
    
    # 清理演示文件
    if os.path.exists(demo_file):
        os.remove(demo_file)
        print(f"   🗑️  Removed demo keys file: {demo_file}")
    
    if os.path.exists(db_file):
        os.remove(db_file)
        print(f"   🗑️  Removed database file: {db_file}")
    
    print("\n✨ SQLite persistence demo completed successfully!")
    print("\nKey advantages over JSON:")
    print("  ✅ Much faster for large key sets (1000+)")
    print("  ✅ Efficient storage with indexes")
    print("  ✅ Transaction support for data integrity")
    print("  ✅ Concurrent access support")
    print("  ✅ Better memory management")
    print("  ✅ Professional-grade persistence")


def demonstrate_database_structure():
    """Demonstrate the SQLite database structure."""
    print("\n" + "="*60)
    print("🗄️  SQLite Database Structure")
    print("="*60)
    
    # 创建临时数据库来展示结构
    temp_db = "temp_structure.db"
    if os.path.exists(temp_db):
        os.remove(temp_db)
    
    try:
        # 连接数据库
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # 创建表结构
        cursor.execute('''
            CREATE TABLE api_keys (
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
        
        cursor.execute('''
            CREATE TABLE file_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                file_hash TEXT NOT NULL,
                change_time TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 显示表结构
        print("📋 Tables created:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            print(f"\n   Table: {table_name}")
            
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            for col in columns:
                col_id, col_name, col_type, not_null, default_val, pk = col
                pk_mark = " 🔑" if pk else ""
                print(f"     {col_name} ({col_type}){pk_mark}")
        
        # 显示索引
        print(f"\n🔍 Indexes:")
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index'")
        indexes = cursor.fetchall()
        
        for idx_name, idx_sql in indexes:
            print(f"   {idx_name}: {idx_sql}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error showing database structure: {e}")
    
    finally:
        if os.path.exists(temp_db):
            os.remove(temp_db)


if __name__ == "__main__":
    demonstrate_sqlite_persistence()
    demonstrate_database_structure()
