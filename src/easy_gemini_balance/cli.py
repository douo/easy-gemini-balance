#!/usr/bin/env python3
"""
Command Line Interface for Easy Gemini Balance
提供统计信息、健康检查、数据库管理等功能
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from .balancer import KeyBalancer
from .gemini_client import GeminiClientWrapper


class EasyGeminiCLI:
    """Command Line Interface for Easy Gemini Balance"""
    
    def __init__(self):
        self.parser = self._create_parser()
    
    def _create_parser(self):
        """创建命令行参数解析器"""
        parser = argparse.ArgumentParser(
            description="Easy Gemini Balance - API Key Management Tool",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # 显示统计信息
  easy-gemini-balance stats
  
  # 导入 keys 文件
  easy-gemini-balance import keys.txt
  
  # 显示健康状态
  easy-gemini-balance health
  
  # 添加单个 key
  easy-gemini-balance add-key "AIzaSyYour_Key_Here" --weight 1.5
  
  # 显示导入历史
  easy-gemini-balance import-history
            """
        )
        
        # 全局选项
        parser.add_argument(
            '--db-path',
            help='Database file path (defaults to XDG_DATA_HOME)'
        )
        parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Verbose output'
        )
        parser.add_argument(
            '--json',
            action='store_true',
            help='Output in JSON format'
        )
        
        # 子命令
        subparsers = parser.add_subparsers(
            dest='command',
            help='Available commands'
        )
        
        # stats 命令
        stats_parser = subparsers.add_parser(
            'stats',
            help='Show key statistics'
        )
        
        # health 命令
        health_parser = subparsers.add_parser(
            'health',
            help='Show key health status'
        )
        
        # db-info 命令
        db_info_parser = subparsers.add_parser(
            'db-info',
            help='Show database information'
        )
        
        # memory 命令
        memory_parser = subparsers.add_parser(
            'memory',
            help='Show memory usage information'
        )
        
        # import 命令
        import_parser = subparsers.add_parser(
            'import',
            help='Import keys from a text file'
        )
        import_parser.add_argument(
            'file_path',
            help='Path to the text file containing API keys'
        )
        import_parser.add_argument(
            '--source',
            default='imported',
            help='Source identifier for imported keys (default: imported)'
        )
        
        # add-key 命令
        add_key_parser = subparsers.add_parser(
            'add-key',
            help='Add a single API key'
        )
        add_key_parser.add_argument(
            'key_value',
            help='The API key string'
        )
        add_key_parser.add_argument(
            '--weight',
            type=float,
            default=1.0,
            help='Key weight (default: 1.0)'
        )
        add_key_parser.add_argument(
            '--source',
            default='manual',
            help='Source identifier (default: manual)'
        )
        
        # remove-key 命令
        remove_key_parser = subparsers.add_parser(
            'remove-key',
            help='Remove an API key'
        )
        remove_key_parser.add_argument(
            'key_value',
            help='The API key string to remove'
        )
        
        # list 命令
        list_parser = subparsers.add_parser(
            'list',
            help='List all keys'
        )
        list_parser.add_argument(
            '--available-only',
            action='store_true',
            help='Show only available keys'
        )
        list_parser.add_argument(
            '--by-source',
            action='store_true',
            help='Group keys by source'
        )
        
        # import-history 命令
        import_history_parser = subparsers.add_parser(
            'import-history',
            help='Show import history'
        )
        
        # reset 命令
        reset_parser = subparsers.add_parser(
            'reset',
            help='Reset key weights and health status'
        )
        reset_parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm the reset operation'
        )
        
        # cleanup 命令
        cleanup_parser = subparsers.add_parser(
            'cleanup',
            help='Clean up old unused keys'
        )
        cleanup_parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Remove keys unused for N days (default: 30)'
        )
        cleanup_parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm the cleanup operation'
        )
        
        # monitor 命令
        monitor_parser = subparsers.add_parser(
            'monitor',
            help='Monitor key usage in real-time'
        )
        monitor_parser.add_argument(
            '--interval',
            type=int,
            default=5,
            help='Update interval in seconds (default: 5)'
        )
        
        # test-keys 命令
        test_keys_parser = subparsers.add_parser(
            'test-keys',
            help='Test all available keys using Gemini API'
        )
        test_keys_parser.add_argument(
            '--max-retries',
            type=int,
            default=1,
            help='Max retries per key (default: 1)'
        )
        test_keys_parser.add_argument(
            '--retry-delay',
            type=float,
            default=0.5,
            help='Retry delay in seconds (default: 0.5)'
        )
        test_keys_parser.add_argument(
            '--page-size',
            type=int,
            default=10,
            help='Page size for models.list API call (default: 10)'
        )
        
        return parser
    
    def run(self, args: Optional[list] = None):
        """运行 CLI"""
        parsed_args = self.parser.parse_args(args)
        
        if not parsed_args.command:
            self.parser.print_help()
            return 1
        
        try:
            return self._execute_command(parsed_args)
        except KeyboardInterrupt:
            print("\n❌ Operation cancelled by user")
            return 1
        except Exception as e:
            if parsed_args.verbose:
                raise
            print(f"❌ Error: {e}")
            return 1
    
    def _execute_command(self, args):
        """执行具体的命令"""
        # 创建 KeyBalancer 实例
        balancer = KeyBalancer(db_path=args.db_path)
        
        if args.command == 'stats':
            return self._show_stats(balancer, args)
        elif args.command == 'health':
            return self._show_health(balancer, args)
        elif args.command == 'db-info':
            return self._show_db_info(balancer, args)
        elif args.command == 'memory':
            return self._show_memory(balancer, args)
        elif args.command == 'import':
            return self._import_keys(balancer, args)
        elif args.command == 'add-key':
            return self._add_key(balancer, args)
        elif args.command == 'remove-key':
            return self._remove_key(balancer, args)
        elif args.command == 'list':
            return self._list_keys(balancer, args)
        elif args.command == 'import-history':
            return self._show_import_history(balancer, args)
        elif args.command == 'reset':
            return self._reset_keys(balancer, args)
        elif args.command == 'cleanup':
            return self._cleanup_keys(balancer, args)
        elif args.command == 'monitor':
            return self._monitor_keys(balancer, args)
        elif args.command == 'test-keys':
            return self._test_keys(balancer, args)
        else:
            print(f"❌ Unknown command: {args.command}")
            return 1
    
    def _show_stats(self, balancer: KeyBalancer, args):
        """显示统计信息"""
        stats = balancer.get_stats()
        
        if args.json:
            print(json.dumps(stats, indent=2, default=str))
            return 0
        
        print("📊 Key Statistics")
        print("=" * 50)
        print(f"Total Keys: {stats['total_keys']}")
        print(f"Available Keys: {stats['available_keys']}")
        print(f"Unavailable Keys: {stats['unavailable_keys']}")
        print(f"Average Weight: {stats['average_weight']}")
        print(f"Database Size: {stats['database_size_mb']:.2f} MB")
        print(f"Last Save: {stats['last_save']}")
        
        if 'source_distribution' in stats:
            print("\nSource Distribution:")
            for source, count in stats['source_distribution'].items():
                print(f"  {source}: {count}")
        
        cache_stats = stats.get('cache_stats', {})
        if cache_stats:
            print(f"\nCache Stats:")
            print(f"  Size: {cache_stats['size']}/{cache_stats['capacity']}")
            print(f"  Hit Rate: {cache_stats['hit_rate']:.2f}")
            print(f"  Access Count: {cache_stats['access_count']}")
        
        return 0
    
    def _show_health(self, balancer: KeyBalancer, args):
        """显示健康状态"""
        stats = balancer.get_stats()
        
        if args.json:
            print(json.dumps(stats, indent=2, default=str))
            return 0
        
        print("🏥 Key Health Status")
        print("=" * 50)
        
        total = stats['total_keys']
        available = stats['available_keys']
        unavailable = stats['unavailable_keys']
        
        if total == 0:
            print("❌ No keys found in database")
            return 1
        
        health_percentage = (available / total) * 100
        print(f"Overall Health: {health_percentage:.1f}%")
        print(f"Available: {available}/{total}")
        print(f"Unavailable: {unavailable}/{total}")
        
        if health_percentage < 50:
            print("🚨 Warning: Less than 50% of keys are available!")
        elif health_percentage < 80:
            print("⚠️  Notice: Some keys are unavailable")
        else:
            print("✅ Good: Most keys are available")
        
        return 0
    
    def _show_db_info(self, balancer: KeyBalancer, args):
        """显示数据库信息"""
        db_info = balancer.get_database_info()
        
        if args.json:
            print(json.dumps(db_info, indent=2, default=str))
            return 0
        
        print("🗄️  Database Information")
        print("=" * 50)
        print(f"Database Path: {db_info['database_path']}")
        print(f"Database Size: {db_info['database_size_mb']:.2f} MB")
        print(f"Total Keys: {db_info['total_keys_in_db']}")
        print(f"Available Keys: {db_info['available_keys_in_db']}")
        print(f"Average Weight: {db_info['average_weight']:.2f}")
        
        if 'source_distribution' in db_info:
            print("\nSource Distribution:")
            for source, count in db_info['source_distribution'].items():
                print(f"  {source}: {count}")
        
        return 0
    
    def _show_memory(self, balancer: KeyBalancer, args):
        """显示内存使用信息"""
        memory_info = balancer.get_memory_usage()
        
        if args.json:
            print(json.dumps(memory_info, indent=2, default=str))
            return 0
        
        print("💾 Memory Usage")
        print("=" * 50)
        print(f"Total Keys: {memory_info['total_keys']}")
        print(f"Total Memory: {memory_info['total_memory_bytes']} bytes")
        print(f"Average Key Size: {memory_info['average_key_size_bytes']:.1f} bytes")
        print(f"Estimated 1000 Keys: {memory_info['estimated_1000_keys_memory_mb']:.2f} MB")
        print(f"Database Size: {memory_info['database_size_mb']:.2f} MB")
        
        return 0
    
    def _import_keys(self, balancer: KeyBalancer, args):
        """导入 keys 文件"""
        file_path = Path(args.file_path)
        
        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            return 1
        
        print(f"📥 Importing keys from: {file_path}")
        print(f"Source: {args.source}")
        
        try:
            result = balancer.import_keys_from_file(str(file_path), args.source)
            
            if args.json:
                print(json.dumps(result, indent=2, default=str))
                return 0
            
            print("\n📊 Import Results:")
            print(f"Total Lines: {result['total_lines']}")
            print(f"New Keys: {result['new_keys']}")
            print(f"Updated Keys: {result['updated_keys']}")
            print(f"Skipped Keys: {result['skipped_keys']}")
            print(f"Source: {result['source']}")
            
            if result['new_keys'] > 0:
                print(f"✅ Successfully imported {result['new_keys']} new keys")
            else:
                print("ℹ️  No new keys imported")
            
            return 0
            
        except Exception as e:
            print(f"❌ Import failed: {e}")
            return 1
    
    def _add_key(self, balancer: KeyBalancer, args):
        """添加单个 key"""
        print(f"➕ Adding key: {args.key_value[:20]}...")
        print(f"Weight: {args.weight}")
        print(f"Source: {args.source}")
        
        try:
            success = balancer.add_key(args.key_value, args.weight, args.source)
            
            if success:
                print("✅ Key added successfully")
                return 0
            else:
                print("❌ Key already exists")
                return 1
                
        except Exception as e:
            print(f"❌ Failed to add key: {e}")
            return 1
    
    def _remove_key(self, balancer: KeyBalancer, args):
        """移除 key"""
        print(f"🗑️  Removing key: {args.key_value[:20]}...")
        
        try:
            success = balancer.remove_key(args.key_value)
            
            if success:
                print("✅ Key removed successfully")
                return 0
            else:
                print("❌ Key not found")
                return 1
                
        except Exception as e:
            print(f"❌ Failed to remove key: {e}")
            return 1
    
    def _list_keys(self, balancer: KeyBalancer, args):
        """列出所有 keys"""
        stats = balancer.get_stats()
        keys = stats['keys']
        
        if args.available_only:
            keys = [k for k in keys if k['available']]
            print(f"🔑 Available Keys ({len(keys)}):")
        else:
            print(f"🔑 All Keys ({len(keys)}):")
        
        print("=" * 80)
        
        if args.by_source:
            # 按来源分组
            source_groups = {}
            for key in keys:
                source = key.get('source', 'unknown')
                if source not in source_groups:
                    source_groups[source] = []
                source_groups[source].append(key)
            
            for source, source_keys in source_groups.items():
                print(f"\n📁 Source: {source} ({len(source_keys)} keys)")
                print("-" * 40)
                for key in source_keys:
                    self._print_key_info(key)
        else:
            # 按可用性排序
            keys.sort(key=lambda x: (not x['available'], x['weight']), reverse=True)
            for key in keys:
                self._print_key_info(key)
        
        return 0
    
    def _print_key_info(self, key: dict):
        """打印单个 key 信息"""
        status = "✅" if key['available'] else "❌"
        print(f"{status} {key['key']} | Weight: {key['weight']} | "
              f"Errors: {key['error_count']} | Source: {key.get('source', 'unknown')}")
    
    def _show_import_history(self, balancer: KeyBalancer, args):
        """显示导入历史"""
        history = balancer.get_import_history()
        
        if args.json:
            print(json.dumps(history, indent=2, default=str))
            return 0
        
        if not history:
            print("📚 No import history found")
            return 0
        
        print("📚 Import History")
        print("=" * 80)
        
        for record in history:
            print(f"📁 File: {record['source_file']}")
            print(f"⏰ Time: {record['import_time']}")
            print(f"📊 Stats: {record['keys_count']} total, "
                  f"{record['new_keys']} new, {record['updated_keys']} updated, "
                  f"{record['skipped_keys']} skipped")
            print("-" * 40)
        
        return 0
    
    def _reset_keys(self, balancer: KeyBalancer, args):
        """重置 key 权重和健康状态"""
        if not args.confirm:
            print("⚠️  This will reset all key weights and health status!")
            print("Use --confirm to proceed")
            return 1
        
        print("🔄 Resetting all key weights and health status...")
        
        try:
            balancer.reset_all_weights()
            print("✅ All keys have been reset")
            return 0
        except Exception as e:
            print(f"❌ Reset failed: {e}")
            return 1
    
    def _cleanup_keys(self, balancer: KeyBalancer, args):
        """清理旧的未使用的 keys"""
        if not args.confirm:
            print(f"⚠️  This will remove keys unused for {args.days} days!")
            print("Use --confirm to proceed")
            return 1
        
        print(f"🧹 Cleaning up keys unused for {args.days} days...")
        
        try:
            removed_count = balancer.cleanup_old_keys(args.days)
            print(f"✅ Cleanup completed: {removed_count} keys removed")
            return 0
        except Exception as e:
            print(f"❌ Cleanup failed: {e}")
            return 1
    
    def _monitor_keys(self, balancer: KeyBalancer, args):
        """实时监控 key 使用情况"""
        print(f"📊 Monitoring key usage (update every {args.interval}s)")
        print("Press Ctrl+C to stop")
        print("=" * 60)
        
        try:
            while True:
                stats = balancer.get_stats()
                available = stats['available_keys']
                total = stats['total_keys']
                health = (available / total * 100) if total > 0 else 0
                
                print(f"\r🔄 Health: {health:.1f}% | Available: {available}/{total} | "
                      f"Cache: {stats['cache_stats']['size']}/{stats['cache_stats']['capacity']}", end='')
                
                import time
                time.sleep(args.interval)
                
        except KeyboardInterrupt:
            print("\n\n✅ Monitoring stopped")
            return 0
    
    def _test_keys(self, balancer: KeyBalancer, args):
        """测试所有可用的 keys"""
        try:
            from .gemini_client import create_gemini_wrapper
        except ImportError:
            print("❌ Error: google-genai package not available. Install with: pip install google-genai")
            return 1
        
        print("🧪 Testing all available keys using Gemini API...")
        print(f"📊 Max retries per key: {args.max_retries}")
        print(f"⏱️  Retry delay: {args.retry_delay} seconds")
        print(f"📄 Page size: {args.page_size}")
        print("=" * 80)
        
        # 创建 Gemini 包装器，使用传入的 balancer
        wrapper = create_gemini_wrapper(
            balancer=balancer,
            max_retries=args.max_retries,
            retry_delay=args.retry_delay
        )
        
        # 获取所有可用的 keys
        available_keys = balancer.key_manager.get_available_keys()
        if not available_keys:
            print("❌ No available keys found")
            return 1
        
        print(f"🔑 Found {len(available_keys)} available keys")
        print()
        
        # 测试每个 key
        test_results = []
        total_keys = len(available_keys)
        
        for i, key in enumerate(available_keys, 1):
            key_value = key.key
            print(f"🔍 Testing key {i}/{total_keys}: {key_value[:20]}...")
            
            try:
                # 定义测试操作：调用 models.list API
                def test_operation(client):
                    return client.models.list(config={"pageSize": args.page_size})
                
                # 执行测试
                result = wrapper.execute_with_retry(test_operation)
                
                # 测试成功
                print(f"✅ Key {i}/{total_keys} - SUCCESS")
                if hasattr(result, 'models'):
                    print(f"   📊 Models found: {len(result.models)}")
                else:
                    print(f"   📊 Result type: {type(result)}")
                
                test_results.append({
                    'key': key_value[:20] + '...',
                    'status': 'SUCCESS',
                    'models_count': len(result.models) if hasattr(result, 'models') else 'N/A'
                })
                
            except Exception as e:
                # 测试失败
                print(f"❌ Key {i}/{total_keys} - FAILED: {e}")
                test_results.append({
                    'key': key_value[:20] + '...',
                    'status': 'FAILED',
                    'error': str(e)
                })
            
            print("-" * 60)
        
        # 显示测试结果摘要
        print("\n📊 Test Results Summary")
        print("=" * 80)
        
        successful_keys = [r for r in test_results if r['status'] == 'SUCCESS']
        failed_keys = [r for r in test_results if r['status'] == 'FAILED']
        
        print(f"✅ Successful: {len(successful_keys)}/{total_keys}")
        print(f"❌ Failed: {len(failed_keys)}/{total_keys}")
        print(f"📈 Success Rate: {(len(successful_keys)/total_keys)*100:.1f}%")
        
        if failed_keys:
            print("\n❌ Failed Keys:")
            for result in failed_keys:
                print(f"   {result['key']}: {result['error']}")
        
        if successful_keys:
            print("\n✅ Successful Keys:")
            for result in successful_keys:
                print(f"   {result['key']}: {result['models_count']} models")
        
        # 更新数据库中的 key 状态
        print("\n🔄 Updating key health status in database...")
        balancer.save_state_now()
        print("✅ Database updated")
        
        return 0


def main():
    """主函数"""
    cli = EasyGeminiCLI()
    return cli.run()


if __name__ == "__main__":
    sys.exit(main())
