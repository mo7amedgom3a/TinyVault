#!/usr/bin/env python3
"""
Test database connectivity and models.
"""
import asyncio
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

async def test_database():
    """Test database functionality."""
    try:
        from app.database import init_db, close_db
        from app.models import User, Item
        
        print("🔧 Testing database connection...")
        
        # Initialize database
        await init_db()
        print("✅ Database initialized successfully")
        
        # Test model creation (this will create tables)
        print("📋 Testing model creation...")
        
        # Close database
        await close_db()
        print("✅ Database connection closed successfully")
        
        print("\n🎉 All database tests passed!")
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_database()) 