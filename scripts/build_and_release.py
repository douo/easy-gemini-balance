#!/usr/bin/env python3
"""
Build and release script for Easy Gemini Balance.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(cmd, check=True):
    """Run a command and return the result."""
    print(f"🔄 Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    
    if check and result.returncode != 0:
        print(f"❌ Command failed: {cmd}")
        sys.exit(1)
    
    return result

def clean_build():
    """Clean previous build artifacts."""
    print("🧹 Cleaning previous build artifacts...")
    
    dirs_to_clean = ['build', 'dist', '*.egg-info']
    for pattern in dirs_to_clean:
        if os.path.exists(pattern):
            if os.path.isdir(pattern):
                shutil.rmtree(pattern)
            else:
                os.remove(pattern)
    
    print("✅ Build artifacts cleaned")

def run_tests():
    """Run all tests to ensure quality."""
    print("🧪 Running tests...")
    
    try:
        result = run_command("uv run python tests/run_tests.py --all", check=False)
        if result.returncode == 0:
            print("✅ All tests passed")
        else:
            print("❌ Some tests failed")
            return False
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return False
    
    return True

def build_package():
    """Build the package."""
    print("🔨 Building package...")
    
    try:
        run_command("uv run python -m build")
        print("✅ Package built successfully")
        return True
    except Exception as e:
        print(f"❌ Build failed: {e}")
        return False

def check_package():
    """Check the built package."""
    print("🔍 Checking built package...")
    
    try:
        # Check wheel
        wheel_file = list(Path("dist").glob("*.whl"))[0]
        print(f"📦 Wheel file: {wheel_file}")
        
        # Check source distribution
        sdist_file = list(Path("dist").glob("*.tar.gz"))[0]
        print(f"📦 Source distribution: {sdist_file}")
        
        # Show file sizes
        print(f"📏 Wheel size: {wheel_file.stat().st_size / 1024:.1f} KB")
        print(f"📏 Source size: {sdist_file.stat().st_size / 1024:.1f} KB")
        
        return True
    except Exception as e:
        print(f"❌ Package check failed: {e}")
        return False

def test_installation():
    """Test installing the built package."""
    print("🧪 Testing package installation...")
    
    try:
        # Install the wheel
        wheel_file = list(Path("dist").glob("*.whl"))[0]
        run_command(f"uv pip install {wheel_file}")
        
        # Test CLI
        result = run_command("uv run easy-gemini-balance --help", check=False)
        if result.returncode == 0:
            print("✅ CLI command works")
        else:
            print("❌ CLI command failed")
            return False
        
        # Test Python import
        result = run_command("uv run python -c \"from easy_gemini_balance import KeyBalancer; print('Import OK')\"", check=False)
        if result.returncode == 0:
            print("✅ Python import works")
        else:
            print("❌ Python import failed")
            return False
        
        # Uninstall for cleanup
        run_command("uv pip uninstall easy-gemini-balance --yes")
        
        return True
    except Exception as e:
        print(f"❌ Installation test failed: {e}")
        return False

def main():
    """Main build and release process."""
    print("🚀 Easy Gemini Balance - Build and Release Script\n")
    
    # Check if we're in the right directory
    if not os.path.exists("pyproject.toml"):
        print("❌ Error: pyproject.toml not found. Please run this script from the project root.")
        sys.exit(1)
    
    # Clean previous builds
    clean_build()
    
    # Run tests
    if not run_tests():
        print("❌ Tests failed. Aborting build.")
        sys.exit(1)
    
    # Build package
    if not build_package():
        print("❌ Build failed. Aborting.")
        sys.exit(1)
    
    # Check package
    if not check_package():
        print("❌ Package check failed. Aborting.")
        sys.exit(1)
    
    # Test installation
    if not test_installation():
        print("❌ Installation test failed. Aborting.")
        sys.exit(1)
    
    print("\n🎉 Build and release process completed successfully!")
    print("\n📦 Generated packages:")
    
    for file in Path("dist").glob("*"):
        print(f"   - {file.name}")
    
    print("\n📋 Next steps:")
    print("   1. Review the generated packages in dist/")
    print("   2. Test the packages in a clean environment")
    print("   3. Upload to PyPI if ready for release")
    print("   4. Create a git tag for this version")

if __name__ == "__main__":
    main()
