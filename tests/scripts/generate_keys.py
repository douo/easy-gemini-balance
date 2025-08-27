#!/usr/bin/env python3
"""
Generate test API keys for performance testing.
"""

import random
import string
from pathlib import Path


def generate_api_key():
    """Generate a fake API key that looks like a real one."""
    # Generate a key that looks like AIzaSy...
    prefix = "AIzaSy"
    chars = string.ascii_letters + string.digits
    suffix = ''.join(random.choice(chars) for _ in range(35))
    return f"{prefix}{suffix}"


def generate_keys_file(filename: str, count: int = 1000, include_weights: bool = True):
    """Generate a keys file with the specified number of keys."""
    
    print(f"🔑 Generating {count} API keys...")
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("# Generated test API keys\n")
        f.write(f"# Total keys: {count}\n")
        f.write("# Format: key:weight (weight is optional, default 1.0)\n\n")
        
        for i in range(count):
            key = generate_api_key()
            
            if include_weights:
                # 随机权重分布：大部分key权重为1.0，少数为0.5-2.0
                if random.random() < 0.8:
                    weight = 1.0
                else:
                    weight = round(random.uniform(0.5, 2.0), 1)
                
                f.write(f"{key}:{weight}\n")
            else:
                f.write(f"{key}\n")
            
            if (i + 1) % 100 == 0:
                print(f"   Generated {i + 1} keys...")
    
    print(f"✅ Generated {count} keys in {filename}")


def generate_small_keys_file(filename: str = None, count: int = 10):
    """Generate a small keys file for basic testing."""
    if filename is None:
        filename = Path(__file__).parent.parent / "data" / "keys_small.txt"
    generate_keys_file(filename, count, include_weights=True)


def generate_large_keys_file(filename: str = None, count: int = 1000):
    """Generate a large keys file for performance testing."""
    if filename is None:
        filename = Path(__file__).parent.parent / "data" / "keys_1000.txt"
    generate_keys_file(filename, count, include_weights=True)


def generate_huge_keys_file(filename: str = None, count: int = 10000):
    """Generate a huge keys file for extreme performance testing."""
    if filename is None:
        filename = Path(__file__).parent.parent / "data" / "keys_10000.txt"
    generate_keys_file(filename, count, include_weights=True)


def main():
    """Main function to generate all test key files."""
    print("🚀 API Key Generator\n")
    
    # 确保数据目录存在
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    # 生成不同大小的测试文件
    generate_small_keys_file(count=10)
    generate_large_keys_file(count=1000)
    generate_huge_keys_file(count=10000)
    
    print("\n✨ All key files generated successfully!")
    print("\nFiles created:")
    print("  - tests/data/keys_small.txt (10 keys)")
    print("  - tests/data/keys_1000.txt (1000 keys)")
    print("  - tests/data/keys_10000.txt (10000 keys)")
    print("\nYou can now test the balancer with different key set sizes.")


if __name__ == "__main__":
    main()
