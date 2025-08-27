#!/usr/bin/env python3
"""
Command Line Interface for Easy Gemini Balance module.
Provides easy access to statistics and key management functions.
"""

import argparse
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from .balancer import KeyBalancer
from .key_manager import KeyManager


class EasyGeminiCLI:
    """Command Line Interface for Easy Gemini Balance."""
    
    def __init__(self):
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the command line argument parser."""
        parser = argparse.ArgumentParser(
            description="Easy Gemini Balance - API Key Management CLI",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Show all statistics
  %(prog)s stats --keys-file keys.txt --db-path keys.db
  
  # Show only key health status
  %(prog)s health --keys-file keys.txt --db-path keys.db
  
  # Show database information
  %(prog)s db-info --db-path keys.db
  
  # Show memory usage
  %(prog)s memory --keys-file keys.txt --db-path keys.db
  
  # Export statistics to JSON
  %(prog)s export --keys-file keys.txt --db-path keys.db --output stats.json
  
  # Monitor real-time statistics
  %(prog)s monitor --keys-file keys.txt --db-path keys.db --interval 5
            """
        )
        
        # Subcommands
        subparsers = parser.add_subparsers(
            dest='command',
            help='Available commands'
        )
        
        # Stats command
        stats_parser = subparsers.add_parser(
            'stats',
            help='Show comprehensive statistics'
        )
        stats_parser.add_argument(
            '--keys-file', '-k',
            default='keys.txt',
            help='Path to the keys file (default: keys.txt)'
        )
        stats_parser.add_argument(
            '--db-path', '-d',
            default='keys.db',
            help='Path to the SQLite database (default: keys.db)'
        )
        stats_parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Enable verbose output'
        )
        stats_parser.add_argument(
            '--json', '-j',
            action='store_true',
            help='Output in JSON format'
        )
        stats_parser.add_argument(
            '--detailed', '-D',
            action='store_true',
            help='Show detailed key information'
        )
        
        # Health command
        health_parser = subparsers.add_parser(
            'health',
            help='Show key health status'
        )
        health_parser.add_argument(
            '--keys-file', '-k',
            default='keys.txt',
            help='Path to the keys file (default: keys.txt)'
        )
        health_parser.add_argument(
            '--db-path', '-d',
            default='keys.db',
            help='Path to the SQLite database (default: keys.db)'
        )
        health_parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Enable verbose output'
        )
        health_parser.add_argument(
            '--json', '-j',
            action='store_true',
            help='Output in JSON format'
        )
        health_parser.add_argument(
            '--filter',
            choices=['all', 'available', 'unavailable', 'error'],
            default='all',
            help='Filter keys by status (default: all)'
        )
        
        # Database command
        db_parser = subparsers.add_parser(
            'db-info',
            help='Show database information'
        )
        db_parser.add_argument(
            '--db-path', '-d',
            default='keys.db',
            help='Path to the SQLite database (default: keys.db)'
        )
        db_parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Enable verbose output'
        )
        db_parser.add_argument(
            '--json', '-j',
            action='store_true',
            help='Output in JSON format'
        )
        
        # Memory command
        memory_parser = subparsers.add_parser(
            'memory',
            help='Show memory usage statistics'
        )
        memory_parser.add_argument(
            '--keys-file', '-k',
            default='keys.txt',
            help='Path to the keys file (default: keys.txt)'
        )
        memory_parser.add_argument(
            '--db-path', '-d',
            default='keys.db',
            help='Path to the SQLite database (default: keys.db)'
        )
        memory_parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Enable verbose output'
        )
        memory_parser.add_argument(
            '--json', '-j',
            action='store_true',
            help='Output in JSON format'
        )
        
        # Export command
        export_parser = subparsers.add_parser(
            'export',
            help='Export statistics to file'
        )
        export_parser.add_argument(
            '--keys-file', '-k',
            default='keys.txt',
            help='Path to the keys file (default: keys.txt)'
        )
        export_parser.add_argument(
            '--db-path', '-d',
            default='keys.db',
            help='Path to the SQLite database (default: keys.db)'
        )
        export_parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Enable verbose output'
        )
        export_parser.add_argument(
            '--output', '-o',
            required=True,
            help='Output file path'
        )
        export_parser.add_argument(
            '--format',
            choices=['json', 'csv', 'txt'],
            default='json',
            help='Output format (default: json)'
        )
        
        # Monitor command
        monitor_parser = subparsers.add_parser(
            'monitor',
            help='Monitor real-time statistics'
        )
        monitor_parser.add_argument(
            '--keys-file', '-k',
            default='keys.txt',
            help='Path to the keys file (default: keys.txt)'
        )
        monitor_parser.add_argument(
            '--db-path', '-d',
            default='keys.db',
            help='Path to the SQLite database (default: keys.db)'
        )
        monitor_parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Enable verbose output'
        )
        monitor_parser.add_argument(
            '--interval', '-i',
            type=int,
            default=5,
            help='Update interval in seconds (default: 5)'
        )
        monitor_parser.add_argument(
            '--count', '-c',
            type=int,
            help='Number of updates (default: infinite)'
        )
        
        # List command
        list_parser = subparsers.add_parser(
            'list',
            help='List all keys'
        )
        list_parser.add_argument(
            '--keys-file', '-k',
            default='keys.txt',
            help='Path to the keys file (default: keys.txt)'
        )
        list_parser.add_argument(
            '--db-path', '-d',
            default='keys.db',
            help='Path to the SQLite database (default: keys.db)'
        )
        list_parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Enable verbose output'
        )
        list_parser.add_argument(
            '--json', '-j',
            action='store_true',
            help='Output in JSON format'
        )
        list_parser.add_argument(
            '--sort-by',
            choices=['key', 'weight', 'last_used', 'error_count', 'status'],
            default='key',
            help='Sort keys by field (default: key)'
        )
        list_parser.add_argument(
            '--limit', '-l',
            type=int,
            help='Limit number of keys to show'
        )
        
        # Reset command
        reset_parser = subparsers.add_parser(
            'reset',
            help='Reset key weights and status'
        )
        reset_parser.add_argument(
            '--keys-file', '-k',
            default='keys.txt',
            help='Path to the keys file (default: keys.txt)'
        )
        reset_parser.add_argument(
            '--db-path', '-d',
            default='keys.db',
            help='Path to the SQLite database (default: keys.db)'
        )
        reset_parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Enable verbose output'
        )
        reset_parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm reset operation'
        )
        
        return parser
    
    def run(self, args: Optional[list] = None) -> int:
        """Run the CLI with given arguments."""
        if args is None:
            args = sys.argv[1:]
        
        parsed_args = self.parser.parse_args(args)
        
        if not parsed_args.command:
            self.parser.print_help()
            return 1
        
        try:
            return self._execute_command(parsed_args)
        except KeyboardInterrupt:
            print("\n❌ Operation cancelled by user")
            return 130
        except Exception as e:
            if hasattr(parsed_args, 'verbose') and parsed_args.verbose:
                import traceback
                traceback.print_exc()
            else:
                print(f"❌ Error: {e}")
            return 1
    
    def _execute_command(self, args: argparse.Namespace) -> int:
        """Execute the specified command."""
        if hasattr(args, 'verbose') and args.verbose:
            if hasattr(args, 'keys_file'):
                print(f"🔧 Using keys file: {args.keys_file}")
            if hasattr(args, 'db_path'):
                print(f"🗄️  Using database: {args.db_path}")
            print()
        
        if args.command == 'stats':
            return self._show_stats(args)
        elif args.command == 'health':
            return self._show_health(args)
        elif args.command == 'db-info':
            return self._show_db_info(args)
        elif args.command == 'memory':
            return self._show_memory(args)
        elif args.command == 'export':
            return self._export_stats(args)
        elif args.command == 'monitor':
            return self._monitor_stats(args)
        elif args.command == 'list':
            return self._list_keys(args)
        elif args.command == 'reset':
            return self._reset_keys(args)
        else:
            print(f"❌ Unknown command: {args.command}")
            return 1
    
    def _show_stats(self, args: argparse.Namespace) -> int:
        """Show comprehensive statistics."""
        try:
            balancer = KeyBalancer(
                keys_file=args.keys_file,
                db_path=args.db_path,
                auto_save=False
            )
            
            stats = balancer.get_stats()
            db_info = balancer.get_database_info()
            
            if args.json:
                import json
                output = {
                    'timestamp': datetime.now().isoformat(),
                    'keys_file': args.keys_file,
                    'database': args.db_path,
                    'statistics': stats,
                    'database_info': db_info
                }
                print(json.dumps(output, indent=2))
            else:
                self._print_stats_table(stats, db_info, args.detailed)
            
            return 0
            
        except Exception as e:
            print(f"❌ Failed to get statistics: {e}")
            return 1
    
    def _show_health(self, args: argparse.Namespace) -> int:
        """Show key health status."""
        try:
            balancer = KeyBalancer(
                keys_file=args.keys_file,
                db_path=args.db_path,
                auto_save=False
            )
            
            stats = balancer.get_stats()
            
            if args.json:
                import json
                output = {
                    'timestamp': datetime.now().isoformat(),
                    'filter': args.filter,
                    'health_summary': {
                        'total_keys': stats['total_keys'],
                        'available_keys': stats['available_keys'],
                        'unavailable_keys': stats['unavailable_keys'],
                        'error_summary': stats.get('error_summary', {})
                    }
                }
                print(json.dumps(output, indent=2))
            else:
                self._print_health_table(stats, args.filter)
            
            return 0
            
        except Exception as e:
            print(f"❌ Failed to get health status: {e}")
            return 1
    
    def _show_db_info(self, args: argparse.Namespace) -> int:
        """Show database information."""
        try:
            balancer = KeyBalancer(
                keys_file='keys.txt',  # Use default for db-info
                db_path=args.db_path,
                auto_save=False
            )
            
            db_info = balancer.get_database_info()
            
            if args.json:
                import json
                output = {
                    'timestamp': datetime.now().isoformat(),
                    'database_info': db_info
                }
                print(json.dumps(output, indent=2))
            else:
                self._print_db_info_table(db_info)
            
            return 0
            
        except Exception as e:
            print(f"❌ Failed to get database info: {e}")
            return 1
    
    def _show_memory(self, args: argparse.Namespace) -> int:
        """Show memory usage statistics."""
        try:
            balancer = KeyBalancer(
                keys_file=args.keys_file,
                db_path=args.db_path,
                auto_save=False
            )
            
            memory_stats = balancer.get_memory_usage()
            
            if args.json:
                import json
                output = {
                    'timestamp': datetime.now().isoformat(),
                    'memory_usage': memory_stats
                }
                print(json.dumps(output, indent=2))
            else:
                self._print_memory_table(memory_stats)
            
            return 0
            
        except Exception as e:
            print(f"❌ Failed to get memory usage: {e}")
            return 1
    
    def _export_stats(self, args: argparse.Namespace) -> int:
        """Export statistics to file."""
        try:
            balancer = KeyBalancer(
                keys_file=args.keys_file,
                db_path=args.db_path,
                auto_save=False
            )
            
            stats = balancer.get_stats()
            db_info = balancer.get_database_info()
            memory_stats = balancer.get_memory_usage()
            
            data = {
                'timestamp': datetime.now().isoformat(),
                'keys_file': args.keys_file,
                'database': args.db_path,
                'statistics': stats,
                'database_info': db_info,
                'memory_usage': memory_stats
            }
            
            if args.format == 'json':
                import json
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            elif args.format == 'csv':
                self._export_to_csv(data, args.output)
            elif args.format == 'txt':
                self._export_to_txt(data, args.output)
            
            print(f"✅ Statistics exported to {args.output}")
            return 0
            
        except Exception as e:
            print(f"❌ Failed to export statistics: {e}")
            return 1
    
    def _monitor_stats(self, args: argparse.Namespace) -> int:
        """Monitor real-time statistics."""
        try:
            balancer = KeyBalancer(
                keys_file=args.keys_file,
                db_path=args.db_path,
                auto_save=False
            )
            
            import time
            
            count = 0
            while True:
                if args.count and count >= args.count:
                    break
                
                # Clear screen
                os.system('clear' if os.name == 'posix' else 'cls')
                
                print(f"🔄 Real-time Monitoring - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"📊 Keys file: {args.keys_file}")
                print(f"🗄️  Database: {args.db_path}")
                print("=" * 60)
                
                stats = balancer.get_stats()
                db_info = balancer.get_database_info()
                
                self._print_monitor_table(stats, db_info)
                
                count += 1
                if args.count and count >= args.count:
                    break
                
                print(f"\n⏰ Next update in {args.interval} seconds... (Press Ctrl+C to stop)")
                time.sleep(args.interval)
            
            return 0
            
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped")
            return 0
        except Exception as e:
            print(f"❌ Failed to monitor statistics: {e}")
            return 1
    
    def _list_keys(self, args: argparse.Namespace) -> int:
        """List all keys."""
        try:
            balancer = KeyBalancer(
                keys_file=args.keys_file,
                db_path=args.db_path,
                auto_save=False
            )
            
            keys = balancer.key_manager.keys
            
            # Sort keys
            if args.sort_by == 'weight':
                keys = sorted(keys, key=lambda k: k.weight, reverse=True)
            elif args.sort_by == 'last_used':
                keys = sorted(keys, key=lambda k: k.last_used or datetime.min)
            elif args.sort_by == 'error_count':
                keys = sorted(keys, key=lambda k: k.error_count, reverse=True)
            elif args.sort_by == 'status':
                keys = sorted(keys, key=lambda k: k.is_available, reverse=True)
            else:  # sort by key
                keys = sorted(keys, key=lambda k: k.key)
            
            # Apply limit
            if args.limit:
                keys = keys[:args.limit]
            
            if args.json:
                import json
                output = {
                    'timestamp': datetime.now().isoformat(),
                    'sort_by': args.sort_by,
                    'limit': args.limit,
                    'total_keys': len(keys),
                    'keys': [
                        {
                            'key': k.key[:20] + '...' if len(k.key) > 20 else k.key,
                            'weight': k.weight,
                            'available': k.is_available,
                            'error_count': k.error_count,
                            'last_used': k.last_used.isoformat() if k.last_used else None,
                            'added_time': k.added_time.isoformat()
                        }
                        for k in keys
                    ]
                }
                print(json.dumps(output, indent=2))
            else:
                self._print_keys_table(keys, args.sort_by)
            
            return 0
            
        except Exception as e:
            print(f"❌ Failed to list keys: {e}")
            return 1
    
    def _reset_keys(self, args: argparse.Namespace) -> int:
        """Reset key weights and status."""
        if not args.confirm:
            print("⚠️  This will reset all key weights and mark them as available.")
            print("⚠️  Use --confirm to proceed.")
            return 1
        
        try:
            balancer = KeyBalancer(
                keys_file=args.keys_file,
                db_path=args.db_path,
                auto_save=False
            )
            
            balancer.reset_all_weights()
            balancer.save_state_now()
            
            print("✅ All keys have been reset successfully!")
            return 0
            
        except Exception as e:
            print(f"❌ Failed to reset keys: {e}")
            return 1
    
    def _print_stats_table(self, stats: Dict[str, Any], db_info: Dict[str, Any], detailed: bool = False):
        """Print statistics in a formatted table."""
        print("📊 COMPREHENSIVE STATISTICS")
        print("=" * 60)
        
        # Basic stats
        print(f"🔑 Total Keys: {stats['total_keys']}")
        print(f"✅ Available Keys: {stats['available_keys']}")
        print(f"❌ Unavailable Keys: {stats['unavailable_keys']}")
        print(f"⚖️  Average Weight: {stats.get('average_weight', 'N/A')}")
        print(f"🗄️  Database Size: {db_info.get('database_size_mb', 'N/A')} MB")
        
        # Cache stats
        if 'cache_stats' in stats:
            cache = stats['cache_stats']
            print(f"💾 Cache Capacity: {cache.get('capacity', 'N/A')}")
            print(f"🎯 Cache Hit Rate: {cache.get('hit_rate', 'N/A'):.2%}")
        
        # Selection stats
        if 'selection_count' in stats:
            print(f"🔄 Total Selections: {stats['selection_count']}")
        
        if detailed and 'keys' in stats:
            print("\n🔍 DETAILED KEY INFORMATION")
            print("-" * 60)
            for key_info in stats['keys'][:10]:  # Show first 10
                status = "✅" if key_info['available'] else "❌"
                print(f"{status} {key_info['key']}: weight={key_info['weight']}, errors={key_info['error_count']}")
            if len(stats['keys']) > 10:
                print(f"... and {len(stats['keys']) - 10} more keys")
    
    def _print_health_table(self, stats: Dict[str, Any], filter_type: str):
        """Print health status table."""
        print("🏥 KEY HEALTH STATUS")
        print("=" * 60)
        
        total = stats['total_keys']
        available = stats['available_keys']
        unavailable = stats['unavailable_keys']
        
        print(f"🔑 Total Keys: {total}")
        print(f"✅ Available: {available} ({available/total*100:.1f}%)")
        print(f"❌ Unavailable: {unavailable} ({unavailable/total*100:.1f}%)")
        
        if filter_type == 'error' and 'keys' in stats:
            print("\n🚨 KEYS WITH ERRORS")
            print("-" * 60)
            error_keys = [k for k in stats['keys'] if k['error_count'] > 0]
            for key_info in sorted(error_keys, key=lambda k: k['error_count'], reverse=True):
                print(f"❌ {key_info['key']}: {key_info['error_count']} errors")
    
    def _print_db_info_table(self, db_info: Dict[str, Any]):
        """Print database information table."""
        print("🗄️  DATABASE INFORMATION")
        print("=" * 60)
        
        print(f"📁 Database Path: {db_info.get('database_path', 'N/A')}")
        print(f"💾 Database Size: {db_info.get('database_size_mb', 'N/A')} MB")
        print(f"🔑 Total Keys in DB: {db_info.get('total_keys_in_db', 'N/A')}")
        print(f"✅ Available Keys in DB: {db_info.get('available_keys_in_db', 'N/A')}")
        print(f"⚖️  Average Weight: {db_info.get('average_weight', 'N/A')}")
    
    def _print_memory_table(self, memory_stats: Dict[str, Any]):
        """Print memory usage table."""
        print("💾 MEMORY USAGE STATISTICS")
        print("=" * 60)
        
        print(f"🔑 Total Keys: {memory_stats.get('total_keys', 'N/A')}")
        print(f"💾 Total Memory: {memory_stats.get('total_memory_bytes', 0) / 1024:.2f} KB")
        print(f"📏 Average Key Size: {memory_stats.get('average_key_size_bytes', 0):.1f} bytes")
        print(f"🚀 Estimated 1000 Keys: {memory_stats.get('estimated_1000_keys_memory_mb', 0):.2f} MB")
        print(f"🗄️  Database Size: {memory_stats.get('database_size_mb', 0):.2f} MB")
    
    def _print_monitor_table(self, stats: Dict[str, Any], db_info: Dict[str, Any]):
        """Print monitoring table."""
        print(f"🔑 Keys: {stats['total_keys']} total, {stats['available_keys']} available")
        print(f"⚖️  Avg Weight: {stats.get('average_weight', 'N/A')}")
        print(f"🗄️  DB Size: {db_info.get('database_size_mb', 'N/A')} MB")
        
        if 'cache_stats' in stats:
            cache = stats['cache_stats']
            print(f"💾 Cache: {cache.get('hit_rate', 0):.2%} hit rate")
    
    def _print_keys_table(self, keys: list, sort_by: str):
        """Print keys table."""
        print(f"🔑 KEYS LIST (sorted by {sort_by})")
        print("=" * 80)
        print(f"{'Key':<30} {'Weight':<8} {'Status':<10} {'Errors':<8} {'Last Used':<20}")
        print("-" * 80)
        
        for key in keys:
            key_display = key.key[:27] + '...' if len(key.key) > 30 else key.key
            status = "✅ Available" if key.is_available else "❌ Unavailable"
            last_used = key.last_used.strftime('%Y-%m-%d %H:%M') if key.last_used else 'Never'
            
            print(f"{key_display:<30} {key.weight:<8.2f} {status:<10} {key.error_count:<8} {last_used:<20}")
    
    def _export_to_csv(self, data: Dict[str, Any], output_path: str):
        """Export data to CSV format."""
        import csv
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write basic info
            writer.writerow(['Timestamp', data['timestamp']])
            writer.writerow(['Keys File', data['keys_file']])
            writer.writerow(['Database', data['database']])
            writer.writerow([])
            
            # Write statistics
            writer.writerow(['STATISTICS'])
            for key, value in data['statistics'].items():
                if isinstance(value, (int, float, str)):
                    writer.writerow([key, value])
            
            writer.writerow([])
            
            # Write database info
            writer.writerow(['DATABASE INFO'])
            for key, value in data['database_info'].items():
                writer.writerow([key, value])
    
    def _export_to_txt(self, data: Dict[str, Any], output_path: str):
        """Export data to text format."""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("EASY GEMINI BALANCE - STATISTICS EXPORT\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Timestamp: {data['timestamp']}\n")
            f.write(f"Keys File: {data['keys_file']}\n")
            f.write(f"Database: {data['database']}\n\n")
            
            f.write("STATISTICS:\n")
            f.write("-" * 20 + "\n")
            for key, value in data['statistics'].items():
                if isinstance(value, (int, float, str)):
                    f.write(f"{key}: {value}\n")
            
            f.write("\nDATABASE INFO:\n")
            f.write("-" * 20 + "\n")
            for key, value in data['database_info'].items():
                f.write(f"{key}: {value}\n")


def main():
    """Main entry point for the CLI."""
    cli = EasyGeminiCLI()
    sys.exit(cli.run())


if __name__ == "__main__":
    main()
