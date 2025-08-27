import sys
import os
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# ... existing code ...

def run_three_schemes_tests():
    """Run three improvement schemes tests."""
    print("🎯 Running Three Improvement Schemes tests...")
    try:
        from test_three_schemes import main as three_schemes_test_main
        result = three_schemes_test_main()
        return result == 0
    except Exception as e:
        print(f"❌ Three schemes tests failed: {e}")
        return False

def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description="Easy Gemini Balance Test Runner")
    parser.add_argument("--basic", action="store_true", help="Run basic functionality tests")
    parser.add_argument("--performance", action="store_true", help="Run performance tests")
    parser.add_argument("--persistence", action="store_true", help="Run persistence demo")
    parser.add_argument("--cli", action="store_true", help="Run CLI tests")
    parser.add_argument("--three-schemes", action="store_true", help="Run three improvement schemes tests")
    parser.add_argument("--generate-data", action="store_true", help="Generate test data")
    parser.add_argument("--all", action="store_true", help="Run all tests")

    args = parser.parse_args()

    # If no specific tests are requested, show help
    if not any([args.basic, args.performance, args.persistence, args.cli, args.three_schemes, args.generate_data, args.all]):
        parser.print_help()
        return 0

    print("🚀 Easy Gemini Balance Test Runner")
    print("="*50)

    total_count = 0
    success_count = 0

    # Run basic tests
    if args.basic or args.all:
        total_count += 1
        if run_basic_tests():
            success_count += 1
            print("✅ Basic tests completed")
        else:
            print("❌ Basic tests failed")

    # Run performance tests
    if args.performance or args.all:
        total_count += 1
        if run_performance_tests():
            success_count += 1
            print("✅ Performance tests completed")
        else:
            print("❌ Performance tests failed")

    # Run persistence demo
    if args.persistence or args.all:
        total_count += 1
        if run_persistence_demo():
            success_count += 1
            print("✅ Persistence demo completed")
        else:
            print("❌ Persistence demo failed")

    # Run CLI tests
    if args.cli or args.all:
        total_count += 1
        if run_cli_tests():
            success_count += 1
            print("✅ CLI tests completed")
        else:
            print("❌ CLI tests failed")

    # Run three schemes tests
    if args.three_schemes or args.all:
        total_count += 1
        if run_three_schemes_tests():
            success_count += 1
            print("✅ Three schemes tests completed")
        else:
            print("❌ Three schemes tests failed")

    # Generate test data
    if args.generate_data or args.all:
        total_count += 1
        if generate_test_data():
            success_count += 1
            print("✅ Test data generation completed")
        else:
            print("❌ Test data generation failed")

    # Summary
    print("\n" + "="*50)
    print(f"📊 Test Summary: {success_count}/{total_count} test suites passed")
    
    if success_count == total_count:
        print("🎉 All test suites passed!")
        return 0
    else:
        print("❌ Some test suites failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
