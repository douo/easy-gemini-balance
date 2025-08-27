#!/usr/bin/env python3
"""
Simple test script for the Easy Gemini Balance module.
"""

import sys
import os
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from easy_gemini_balance import KeyBalancer, KeyManager, APIKey


def test_basic_functionality():
    """Test basic functionality of the module."""
    print("🧪 Testing basic functionality...")
    
    try:
        # Test KeyManager
        keys_file = Path(__file__).parent / "data" / "keys.txt"
        key_manager = KeyManager(str(keys_file))
        print(f"✅ KeyManager initialized with {len(key_manager.keys)} keys")
        
        # Test KeyBalancer
        balancer = KeyBalancer(str(keys_file), cache_size=10)
        print(f"✅ KeyBalancer initialized with cache size {balancer.lru_cache.capacity}")
        
        # Test getting keys
        single_key = balancer.get_single_key()
        print(f"✅ Retrieved single key: {single_key[:20]}...")
        
        multiple_keys = balancer.get_keys(2)
        print(f"✅ Retrieved {len(multiple_keys)} keys")
        
        # Test stats
        stats = balancer.get_stats()
        print(f"✅ Stats retrieved: {stats['total_keys']} total keys, {stats['available_keys']} available")
        
        print("✅ All basic tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def test_error_handling():
    """Test error handling functionality."""
    print("\n🧪 Testing error handling...")
    
    try:
        keys_file = Path(__file__).parent / "data" / "keys.txt"
        balancer = KeyBalancer(str(keys_file))
        
        # Test with a valid key
        key = balancer.get_single_key()
        if not key:
            print("❌ No key available for testing")
            return False
        
        # Test success case
        balancer.update_key_health(key, success=True)
        key_info = balancer.get_key_info(key)
        print(f"✅ Success case: key weight = {key_info['weight']}")
        
        # Test 403 error (weight reduction)
        balancer.update_key_health(key, error_code=403)
        key_info = balancer.get_key_info(key)
        print(f"✅ 403 error case: key weight = {key_info['weight']}")
        
        # Test 400 error (key becomes unavailable)
        balancer.update_key_health(key, error_code=400)
        key_info = balancer.get_key_info(key)
        print(f"✅ 400 error case: key available = {key_info['available']}")
        
        # Reset weights
        balancer.reset_all_weights()
        key_info = balancer.get_key_info(key)
        print(f"✅ Reset case: key weight = {key_info['weight']}, available = {key_info['available']}")
        
        print("✅ All error handling tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False


def test_weight_distribution():
    """Test weight-based key selection."""
    print("\n🧪 Testing weight distribution...")
    
    try:
        keys_file = Path(__file__).parent / "data" / "keys.txt"
        balancer = KeyBalancer(str(keys_file))
        
        # Get all available keys
        available_keys = balancer.key_manager.get_available_keys()
        if len(available_keys) < 2:
            print("❌ Need at least 2 keys for weight distribution test")
            return False
        
        # Test multiple key selection
        selected_keys = balancer.get_keys(len(available_keys))
        print(f"✅ Selected {len(selected_keys)} keys using weight distribution")
        
        # Show key weights
        for key in selected_keys:
            key_info = balancer.get_key_info(key)
            if key_info:
                print(f"   Key: {key_info['key']}, Weight: {key_info['weight']}")
        
        print("✅ Weight distribution test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Weight distribution test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 Easy Gemini Balance - Test Suite\n")
    
    tests = [
        test_basic_functionality,
        test_error_handling,
        test_weight_distribution,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Module is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
