#!/usr/bin/env python3
"""
Test script to verify Alembic migration setup.
Run this script to test if migrations are working correctly.
"""

import os
import sys
import subprocess
from pathlib import Path


def test_alembic_setup():
    """Test if Alembic is properly configured."""
    print("🧪 Testing Alembic Migration Setup")
    print("=" * 50)
    
    # Check if migrations directory exists
    if not Path("migrations").exists():
        print("❌ Migrations directory not found!")
        print("   Run: python manage_migrations.py init")
        return False
    
    # Check if env.py exists
    if not Path("migrations/env.py").exists():
        print("❌ migrations/env.py not found!")
        return False
    
    # Check if script.py.mako exists
    if not Path("migrations/script.py.mako").exists():
        print("❌ migrations/script.py.mako not found!")
        return False
    
    print("✅ Basic migration files found")
    
    # Test alembic commands
    try:
        # Test current command
        result = subprocess.run(
            ["alembic", "current"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        print(f"✅ Alembic current: {result.stdout.strip()}")
        
        # Test history command
        result = subprocess.run(
            ["alembic", "history"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        print("✅ Alembic history command works")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Alembic command failed: {e}")
        return False
    except FileNotFoundError:
        print("❌ Alembic not found. Install with: pip install alembic")
        return False


def test_model_imports():
    """Test if models can be imported correctly."""
    print("\n🔍 Testing Model Imports")
    print("=" * 50)
    
    try:
        # Test importing models
        from app.models import User, Item
        print("✅ User model imported successfully")
        print("✅ Item model imported successfully")
        
        # Test importing database
        from app.database import Base, engine
        print("✅ Database components imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


def test_migration_generation():
    """Test if migrations can be generated."""
    print("\n📝 Testing Migration Generation")
    print("=" * 50)
    
    try:
        # Try to generate a test migration
        result = subprocess.run(
            ["alembic", "revision", "--autogenerate", "-m", "test migration"],
            capture_output=True,
            text=True,
            check=True
        )
        print("✅ Test migration generated successfully")
        
        # Clean up test migration
        # Find the generated file and remove it
        versions_dir = Path("migrations/versions")
        if versions_dir.exists():
            for file in versions_dir.glob("*test_migration.py"):
                file.unlink()
                print(f"✅ Cleaned up test migration: {file.name}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Migration generation failed: {e}")
        if e.stderr:
            print(f"   Error details: {e.stderr}")
        return False


def main():
    """Run all tests."""
    print("🚀 TinyVault Migration Setup Test")
    print("=" * 50)
    
    tests = [
        ("Alembic Setup", test_alembic_setup),
        ("Model Imports", test_model_imports),
        ("Migration Generation", test_migration_generation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        if test_func():
            passed += 1
            print(f"✅ {test_name}: PASSED")
        else:
            print(f"❌ {test_name}: FAILED")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your migration setup is working correctly.")
        print("\n📚 Next steps:")
        print("   1. Create your first migration: python manage_migrations.py create 'initial schema'")
        print("   2. Apply migrations: python manage_migrations.py run")
        print("   3. Check status: python manage_migrations.py current")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        print("\n🔧 Troubleshooting:")
        print("   1. Ensure Alembic is installed: pip install alembic")
        print("   2. Check your database configuration")
        print("   3. Verify model imports work correctly")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 