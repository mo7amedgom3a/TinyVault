#!/usr/bin/env python3
"""
Simple test script to verify TinyVault project structure and run basic tests.
"""
import sys
import subprocess
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n🔧 {description}...")
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        if e.stderr:
            print("STDERR:", e.stderr)
        return False


def check_project_structure():
    """Check if project structure is correct."""
    print("🔍 Checking project structure...")
    
    required_dirs = [
        "app",
        "app/api",
        "app/services", 
        "app/repositories",
        "app/data",
        "app/utilities",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/fixtures"
    ]
    
    required_files = [
        "app/main.py",
        "app/models.py",
        "app/schemas.py",
        "app/utilities/config.py",
        "app/utilities/database.py",
        "app/utilities/dependencies.py",
        "tests/conftest.py",
        "tests/run_tests.py",
        "pytest.ini",
        "requirements.txt"
    ]
    
    missing_dirs = []
    missing_files = []
    
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            missing_dirs.append(dir_path)
    
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_dirs or missing_files:
        print("❌ Project structure issues found:")
        if missing_dirs:
            print(f"  Missing directories: {', '.join(missing_dirs)}")
        if missing_files:
            print(f"  Missing files: {', '.join(missing_files)}")
        return False
    
    print("✅ Project structure is correct")
    return True


def run_basic_tests():
    """Run basic tests to verify functionality."""
    print("\n🧪 Running basic tests...")
    
    # Test 1: Check if we can import the main app
    try:
        sys.path.insert(0, str(Path.cwd()))
        from app.main import app
        print("✅ Main app imports successfully")
    except ImportError as e:
        print(f"❌ Failed to import main app: {e}")
        return False
    
    # Test 2: Check if we can import models
    try:
        from app.models import User, Item
        print("✅ Models import successfully")
    except ImportError as e:
        print(f"❌ Failed to import models: {e}")
        return False
    
    # Test 3: Check if we can import services
    try:
        from app.services.telegram_service import TelegramService
        print("✅ Services import successfully")
    except ImportError as e:
        print(f"❌ Failed to import services: {e}")
        return False
    
    return True


def main():
    """Main function."""
    print("🚀 TinyVault Project Test")
    print("=" * 50)
    
    # Check project structure
    if not check_project_structure():
        print("\n❌ Project structure check failed")
        sys.exit(1)
    
    # Run basic tests
    if not run_basic_tests():
        print("\n❌ Basic tests failed")
        sys.exit(1)
    
    # Run pytest discovery
    if not run_command(["python", "-m", "pytest", "--collect-only"], "Test discovery"):
        print("\n❌ Test discovery failed")
        sys.exit(1)
    
    print("\n🎉 Project verification completed successfully!")
    print("\n📋 Next steps:")
    print("1. Install development dependencies: pip install -r requirements-dev.txt")
    print("2. Run unit tests: python -m pytest tests/unit/")
    print("3. Run integration tests: python -m pytest tests/integration/")
    print("4. Run all tests: python -m pytest")
    print("5. Use the test runner: python tests/run_tests.py --help")


if __name__ == "__main__":
    main() 