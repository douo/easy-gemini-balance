#!/usr/bin/env python3
"""
Easy Gemini Balance 测试运行器
支持运行不同的测试套件
"""

import sys
import subprocess
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def run_basic_tests():
    """运行基础功能测试"""
    print("🧪 Running Basic functionality tests...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/test_balancer.py", 
            "-v"
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        
        if result.returncode == 0:
            print("✅ Basic tests completed successfully")
            return True
        else:
            print(f"❌ Basic tests failed:\n{result.stdout}\n{result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error running basic tests: {e}")
        return False


def run_performance_tests():
    """运行性能测试"""
    print("🧪 Running Performance tests...")
    try:
        result = subprocess.run([
            sys.executable, "tests/performance_test.py"
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        
        if result.returncode == 0:
            print("✅ Performance tests completed successfully")
            return True
        else:
            print(f"❌ Performance tests failed:\n{result.stdout}\n{result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error running performance tests: {e}")
        return False


def run_persistence_tests():
    """运行持久化测试"""
    print("🧪 Running Persistence tests...")
    try:
        result = subprocess.run([
            sys.executable, "tests/demo_persistence.py"
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        
        if result.returncode == 0:
            print("✅ Persistence tests completed successfully")
            return True
        else:
            print(f"❌ Persistence tests failed:\n{result.stdout}\n{result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error running persistence tests: {e}")
        return False


def run_cli_tests():
    """运行 CLI 测试"""
    print("🧪 Running CLI tests...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/test_cli.py", 
            "-v"
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        
        if result.returncode == 0:
            print("✅ CLI tests completed successfully")
            return True
        else:
            print(f"❌ CLI tests failed:\n{result.stdout}\n{result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error running CLI tests: {e}")
        return False


def run_three_schemes_tests():
    """运行三个改进方案测试"""
    print("🧪 Running Three Improvement Schemes tests...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/test_three_schemes.py", 
            "-v"
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        
        if result.returncode == 0:
            print("✅ Three schemes tests completed successfully")
            return True
        else:
            print(f"❌ Three schemes tests failed:\n{result.stdout}\n{result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error running three schemes tests: {e}")
        return False


def run_gemini_client_tests():
    """运行 Gemini 客户端测试"""
    print("🧪 Running Gemini Client tests...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/test_gemini_client.py", 
            "-v"
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        
        if result.returncode == 0:
            print("✅ Gemini client tests completed successfully")
            return True
        else:
            print(f"❌ Gemini client tests failed:\n{result.stdout}\n{result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error running Gemini client tests: {e}")
        return False


def run_generate_data_tests():
    """运行数据生成测试"""
    print("🧪 Running Data generation tests...")
    try:
        result = subprocess.run([
            sys.executable, "tests/scripts/generate_keys.py"
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        
        if result.returncode == 0:
            print("✅ Data generation tests completed successfully")
            return True
        else:
            print(f"❌ Data generation tests failed:\n{result.stdout}\n{result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error running data generation tests: {e}")
        return False


def main():
    """主函数"""
    print("🚀 Easy Gemini Balance Test Runner")
    print("="*50)
    
    if len(sys.argv) < 2:
        print("用法: python run_tests.py [--basic|--performance|--persistence|--cli|--three-schemes|--gemini-client|--generate-data|--all]")
        print("\n可用的测试套件:")
        print("  --basic          基础功能测试")
        print("  --performance    性能测试")
        print("  --persistence    持久化测试")
        print("  --cli            CLI 功能测试")
        print("  --three-schemes  三个改进方案测试")
        print("  --gemini-client  Gemini 客户端测试")
        print("  --generate-data  数据生成测试")
        print("  --all            运行所有测试")
        return
    
    test_results = []
    
    if "--basic" in sys.argv or "--all" in sys.argv:
        test_results.append(("Basic", run_basic_tests()))
    
    if "--performance" in sys.argv or "--all" in sys.argv:
        test_results.append(("Performance", run_performance_tests()))
    
    if "--persistence" in sys.argv or "--all" in sys.argv:
        test_results.append(("Persistence", run_persistence_tests()))
    
    if "--cli" in sys.argv or "--all" in sys.argv:
        test_results.append(("CLI", run_cli_tests()))
    
    if "--three-schemes" in sys.argv or "--all" in sys.argv:
        test_results.append(("Three Schemes", run_three_schemes_tests()))
    
    if "--gemini-client" in sys.argv or "--all" in sys.argv:
        test_results.append(("Gemini Client", run_gemini_client_tests()))
    
    if "--generate-data" in sys.argv or "--all" in sys.argv:
        test_results.append(("Data Generation", run_generate_data_tests()))
    
    # 显示测试结果摘要
    print("\n" + "="*50)
    print("📊 Test Summary:")
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n📊 Overall: {passed}/{total} test suites passed")
    
    if passed == total:
        print("🎉 All test suites passed!")
        return 0
    else:
        print("❌ Some test suites failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
