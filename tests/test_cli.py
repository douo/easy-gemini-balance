#!/usr/bin/env python3
"""
Test script for the CLI module.
"""

import sys
import os
import tempfile
import json
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from easy_gemini_balance import EasyGeminiCLI


def test_cli_help():
    """Test CLI help command."""
    print("🧪 Testing CLI help command...")
    
    try:
        cli = EasyGeminiCLI()
        result = cli.run(['--help'])
        
        if result == 0:
            print("✅ CLI help command works")
            return True
        else:
            print("❌ CLI help command failed")
            return False
            
    except Exception as e:
        print(f"❌ CLI help test failed: {e}")
        return False


def test_cli_stats():
    """Test CLI stats command."""
    print("🧪 Testing CLI stats command...")
    
    try:
        # Create a temporary keys file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("AIzaSyTest_Key1_abcdefghijklmnopqrstuvwxyz:1.0\n")
            f.write("AIzaSyTest_Key2_0987654321zyxwvutsrqponmlkj:1.5\n")
            temp_keys_file = f.name
        
        # Create a temporary database path
        temp_db = temp_keys_file.replace('.txt', '.db')
        
        try:
            cli = EasyGeminiCLI()
            result = cli.run(['stats', '--keys-file', temp_keys_file, '--db-path', temp_db])
            
            if result == 0:
                print("✅ CLI stats command works")
                return True
            else:
                print("❌ CLI stats command failed")
                return False
                
        finally:
            # Cleanup
            if os.path.exists(temp_keys_file):
                os.unlink(temp_keys_file)
            if os.path.exists(temp_db):
                os.unlink(temp_db)
            
    except Exception as e:
        print(f"❌ CLI stats test failed: {e}")
        return False


def test_cli_health():
    """Test CLI health command."""
    print("🧪 Testing CLI health command...")
    
    try:
        # Create a temporary keys file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("AIzaSyTest_Key1_abcdefghijklmnopqrstuvwxyz:1.0\n")
            f.write("AIzaSyTest_Key2_0987654321zyxwvutsrqponmlkj:1.5\n")
            temp_keys_file = f.name
        
        # Create a temporary database path
        temp_db = temp_keys_file.replace('.txt', '.db')
        
        try:
            cli = EasyGeminiCLI()
            result = cli.run(['health', '--keys-file', temp_keys_file, '--db-path', temp_db])
            
            if result == 0:
                print("✅ CLI health command works")
                return True
            else:
                print("❌ CLI health command failed")
                return False
                
        finally:
            # Cleanup
            if os.path.exists(temp_keys_file):
                os.unlink(temp_keys_file)
            if os.path.exists(temp_db):
                os.unlink(temp_db)
            
    except Exception as e:
        print(f"❌ CLI health test failed: {e}")
        return False


def test_cli_db_info():
    """Test CLI db-info command."""
    print("🧪 Testing CLI db-info command...")
    
    try:
        # Create a temporary keys file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("AIzaSyTest_Key1_abcdefghijklmnopqrstuvwxyz:1.0\n")
            temp_keys_file = f.name
        
        # Create a temporary database path
        temp_db = temp_keys_file.replace('.txt', '.db')
        
        try:
            cli = EasyGeminiCLI()
            result = cli.run(['db-info', '--db-path', temp_db])
            
            if result == 0:
                print("✅ CLI db-info command works")
                return True
            else:
                print("❌ CLI db-info command failed")
                return False
                
        finally:
            # Cleanup
            if os.path.exists(temp_keys_file):
                os.unlink(temp_keys_file)
            if os.path.exists(temp_db):
                os.unlink(temp_db)
            
    except Exception as e:
        print(f"❌ CLI db-info test failed: {e}")
        return False


def test_cli_memory():
    """Test CLI memory command."""
    print("🧪 Testing CLI memory command...")
    
    try:
        # Create a temporary keys file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("AIzaSyTest_Key1_abcdefghijklmnopqrstuvwxyz:1.0\n")
            temp_keys_file = f.name
        
        # Create a temporary database path
        temp_db = temp_keys_file.replace('.txt', '.db')
        
        try:
            cli = EasyGeminiCLI()
            result = cli.run(['memory', '--keys-file', temp_keys_file, '--db-path', temp_db])
            
            if result == 0:
                print("✅ CLI memory command works")
                return True
            else:
                print("❌ CLI memory command failed")
                return False
                
        finally:
            # Cleanup
            if os.path.exists(temp_keys_file):
                os.unlink(temp_keys_file)
            if os.path.exists(temp_db):
                os.unlink(temp_db)
            
    except Exception as e:
        print(f"❌ CLI memory test failed: {e}")
        return False


def test_cli_list():
    """Test CLI list command."""
    print("🧪 Testing CLI list command...")
    
    try:
        # Create a temporary keys file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("AIzaSyTest_Key1_abcdefghijklmnopqrstuvwxyz:1.0\n")
            f.write("AIzaSyTest_Key2_0987654321zyxwvutsrqponmlkj:1.5\n")
            temp_keys_file = f.name
        
        # Create a temporary database path
        temp_db = temp_keys_file.replace('.txt', '.db')
        
        try:
            cli = EasyGeminiCLI()
            result = cli.run(['list', '--keys-file', temp_keys_file, '--db-path', temp_db, '--limit', '5'])
            
            if result == 0:
                print("✅ CLI list command works")
                return True
            else:
                print("❌ CLI list command failed")
                return False
                
        finally:
            # Cleanup
            if os.path.exists(temp_keys_file):
                os.unlink(temp_keys_file)
            if os.path.exists(temp_db):
                os.unlink(temp_db)
            
    except Exception as e:
        print(f"❌ CLI list test failed: {e}")
        return False


def test_cli_json_output():
    """Test CLI JSON output format."""
    print("🧪 Testing CLI JSON output format...")
    
    try:
        # Create a temporary keys file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("AIzaSyTest_Key1_abcdefghijklmnopqrstuvwxyz:1.0\n")
            temp_keys_file = f.name
        
        # Create a temporary database path
        temp_db = temp_keys_file.replace('.txt', '.db')
        
        try:
            cli = EasyGeminiCLI()
            result = cli.run(['stats', '--keys-file', temp_keys_file, '--db-path', temp_db, '--json'])
            
            if result == 0:
                print("✅ CLI JSON output works")
                return True
            else:
                print("❌ CLI JSON output failed")
                return False
                
        finally:
            # Cleanup
            if os.path.exists(temp_keys_file):
                os.unlink(temp_keys_file)
            if os.path.exists(temp_db):
                os.unlink(temp_db)
            
    except Exception as e:
        print(f"❌ CLI JSON output test failed: {e}")
        return False


def main():
    """Run all CLI tests."""
    print("🚀 Easy Gemini Balance - CLI Test Suite\n")
    
    tests = [
        test_cli_help,
        test_cli_stats,
        test_cli_health,
        test_cli_db_info,
        test_cli_memory,
        test_cli_list,
        test_cli_json_output,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 CLI Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All CLI tests passed! CLI module is working correctly.")
        return 0
    else:
        print("❌ Some CLI tests failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
