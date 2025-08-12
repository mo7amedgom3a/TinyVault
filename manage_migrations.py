#!/usr/bin/env python3
"""
Migration management script for TinyVault.
Provides easy-to-use commands for managing database migrations.
"""

import os
import sys
import subprocess
from pathlib import Path


def run_command(command, description):
    """Run a shell command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(f"Error details: {e.stderr}")
        return False


def check_alembic_installed():
    """Check if Alembic is installed."""
    try:
        import alembic
        return True
    except ImportError:
        print("❌ Alembic is not installed. Please install it first:")
        print("   pip install alembic")
        return False


def init_alembic():
    """Initialize Alembic if not already initialized."""
    if not Path("migrations").exists():
        print("🚀 Initializing Alembic...")
        if run_command("alembic init migrations", "Initializing Alembic"):
            print("✅ Alembic initialized successfully!")
        else:
            print("❌ Failed to initialize Alembic")
            return False
    return True


def create_migration(message):
    """Create a new migration."""
    if not message:
        message = "auto-generated migration"
    
    print(f"📝 Creating migration: {message}")
    if run_command(f"alembic revision --autogenerate -m '{message}'", "Creating migration"):
        print("✅ Migration created successfully!")
        return True
    else:
        print("❌ Failed to create migration")
        return False


def run_migrations():
    """Run all pending migrations."""
    print("🚀 Running migrations...")
    if run_command("alembic upgrade head", "Running migrations"):
        print("✅ All migrations applied successfully!")
        return True
    else:
        print("❌ Failed to run migrations")
        return False


def show_migration_history():
    """Show migration history."""
    print("📚 Migration history:")
    run_command("alembic history", "Showing migration history")


def show_current_revision():
    """Show current database revision."""
    print("📍 Current database revision:")
    run_command("alembic current", "Showing current revision")


def show_pending_migrations():
    """Show pending migrations."""
    print("⏳ Pending migrations:")
    run_command("alembic heads", "Showing pending migrations")


def rollback_migration(revision):
    """Rollback to a specific revision."""
    if not revision:
        print("❌ Please specify a revision to rollback to")
        return False
    
    print(f"⏪ Rolling back to revision: {revision}")
    if run_command(f"alembic downgrade {revision}", f"Rolling back to {revision}"):
        print(f"✅ Successfully rolled back to revision {revision}")
        return True
    else:
        print(f"❌ Failed to rollback to revision {revision}")
        return False


def show_help():
    """Show help information."""
    print("""
🔧 TinyVault Migration Manager

Usage: python manage_migrations.py <command> [options]

Commands:
  init              Initialize Alembic (if not already done)
  create <message>  Create a new migration with the given message
  run               Run all pending migrations
  history           Show migration history
  current           Show current database revision
  pending           Show pending migrations
  rollback <rev>    Rollback to a specific revision
  help              Show this help message

Examples:
  python manage_migrations.py init
  python manage_migrations.py create "add user preferences table"
  python manage_migrations.py run
  python manage_migrations.py rollback 001
  python manage_migrations.py history
""")


def main():
    """Main function to handle command line arguments."""
    if not check_alembic_installed():
        sys.exit(1)
    
    if len(sys.argv) < 2:
        show_help()
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "init":
        if not init_alembic():
            sys.exit(1)
    
    elif command == "create":
        message = sys.argv[2] if len(sys.argv) > 2 else "auto-generated migration"
        if not create_migration(message):
            sys.exit(1)
    
    elif command == "run":
        if not run_migrations():
            sys.exit(1)
    
    elif command == "history":
        show_migration_history()
    
    elif command == "current":
        show_current_revision()
    
    elif command == "pending":
        show_pending_migrations()
    
    elif command == "rollback":
        revision = sys.argv[2] if len(sys.argv) > 2 else None
        if not rollback_migration(revision):
            sys.exit(1)
    
    elif command == "help":
        show_help()
    
    else:
        print(f"❌ Unknown command: {command}")
        show_help()
        sys.exit(1)


if __name__ == "__main__":
    main() 