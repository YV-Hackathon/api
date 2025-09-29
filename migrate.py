#!/usr/bin/env python3
"""
Database migration script for the Church Management System FastAPI application.
This script provides convenient commands for managing database migrations.
"""

import sys
import os
import subprocess
import argparse

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False

def migrate_up():
    """Apply all pending migrations"""
    return run_command("alembic upgrade head", "Applying migrations")

def migrate_down():
    """Rollback the last migration"""
    return run_command("alembic downgrade -1", "Rolling back migration")

def migrate_create(message):
    """Create a new migration"""
    if not message:
        message = input("Enter migration description: ")
    return run_command(f'alembic revision --autogenerate -m "{message}"', f"Creating migration: {message}")

def migrate_history():
    """Show migration history"""
    return run_command("alembic history", "Showing migration history")

def migrate_current():
    """Show current migration status"""
    return run_command("alembic current", "Showing current migration status")

def migrate_reset():
    """Reset database and apply all migrations"""
    print("⚠️  This will drop all data and recreate the database!")
    confirm = input("Are you sure? (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ Reset cancelled")
        return False
    
    # Drop all tables and recreate
    if run_command("alembic downgrade base", "Dropping all tables"):
        return run_command("alembic upgrade head", "Applying all migrations")
    return False

def main():
    parser = argparse.ArgumentParser(description="Database migration management")
    parser.add_argument('command', choices=[
        'up', 'down', 'create', 'history', 'current', 'reset'
    ], help='Migration command to run')
    parser.add_argument('-m', '--message', help='Migration message (for create command)')
    
    args = parser.parse_args()
    
    if args.command == 'up':
        migrate_up()
    elif args.command == 'down':
        migrate_down()
    elif args.command == 'create':
        migrate_create(args.message)
    elif args.command == 'history':
        migrate_history()
    elif args.command == 'current':
        migrate_current()
    elif args.command == 'reset':
        migrate_reset()

if __name__ == "__main__":
    main()
