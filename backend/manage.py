#!/usr/bin/env python3
"""
Database Management CLI
Commands: migrate, migrate:fresh, seed
"""
import sys
import os
import sqlite3
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import DatabaseManager
from core.auth.repositories import UserRepository
from core.auth.services import AuthService
from core.auth.models import RegisterRequest

def migrate():
    """Run database migrations"""
    print("🔄 Running migrations...")
    db = DatabaseManager()
    print("✅ Migrations completed successfully!")
    print(f"📁 Database location: {db.db_path}")

def migrate_fresh():
    """Drop all tables and re-run migrations"""
    print("⚠️  WARNING: This will delete all data!")
    confirm = input("Are you sure? (yes/no): ")
    
    if confirm.lower() != 'yes':
        print("❌ Migration cancelled")
        return
    
    db = DatabaseManager()
    
    # Delete database file
    if os.path.exists(db.db_path):
        os.remove(db.db_path)
        print("🗑️  Database deleted")

    # Delete ./templates/ and ./uploads/ and ./previews/ folder and files
    template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    if os.path.exists(template_folder):
        for root, dirs, files in os.walk(template_folder):
            for file in files:
                os.remove(os.path.join(root, file))
            for dir in dirs:
                os.rmdir(os.path.join(root, dir))
        os.rmdir(template_folder)
        print("🗑️  Template folder deleted")

    # Delete ./uploads/ folder and files
    upload_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    if os.path.exists(upload_folder):
        for root, dirs, files in os.walk(upload_folder):
            for file in files:
                os.remove(os.path.join(root, file))
            for dir in dirs:
                os.rmdir(os.path.join(root, dir))
        os.rmdir(upload_folder)
        print("🗑️  Uploads folder deleted")

    # Delete ./previews/ folder and files
    preview_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'previews')
    if os.path.exists(preview_folder):
        for root, dirs, files in os.walk(preview_folder):
            for file in files:
                os.remove(os.path.join(root, file))
            for dir in dirs:
                os.rmdir(os.path.join(root, dir))
        os.rmdir(preview_folder)
        print("🗑️  Previews folder deleted")

    # Delete ./feedback/ folder and files
    feedback_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'feedback')
    if os.path.exists(feedback_folder):
        for root, dirs, files in os.walk(feedback_folder):
            for file in files:
                os.remove(os.path.join(root, file))
            for dir in dirs:
                os.rmdir(os.path.join(root, dir))
        os.rmdir(feedback_folder)
        print("🗑️  Feedback folder deleted" )

    # Delete ./data/strategy_performance.json
    strategy_performance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'strategy_performance.json')
    if os.path.exists(strategy_performance_path):
        os.remove(strategy_performance_path)
        print("🗑️  Strategy performance deleted")

    # Delete ./models/ folder contents (trained CRF models)
    models_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models')
    if os.path.exists(models_folder):
        for root, dirs, files in os.walk(models_folder, topdown=False):
            for file in files:
                os.remove(os.path.join(root, file))
                print(f"   🗑️  Deleted model: {file}")
        print("🗑️  Models folder cleaned")

    # Delete log files
    log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.log')
    if os.path.exists(log_file):
        os.remove(log_file)
        print("🗑️  Log file deleted")

    # Re-create database
    print("🔄 Creating fresh database...")
    db = DatabaseManager()
    print("✅ Fresh database created successfully!")
    print(f"📁 Database location: {db.db_path}")
    seed()

def seed():
    """Seed database with initial data"""
    print("🌱 Seeding database...")
    
    db = DatabaseManager()
    user_repo = UserRepository(db.db_path)  # Pass db_path string, not db object
    auth_service = AuthService(user_repo)
    
    username = "madulinux"
    password = "justice#404"
    # Check if admin exists
    existing_admin = user_repo.find_by_username(username)
    if existing_admin:
        print("ℹ️  Admin user already exists")
    else:
        # Create admin user
        admin_request = RegisterRequest(
            username=username,
            email='madulinux@gmail.com',
            password=password,
            full_name='Administrator'
        )
        admin_user = auth_service.register(admin_request)
        # Update role to admin manually using SQL
        conn = user_repo._get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET role = ? WHERE id = ?', ('admin', admin_user.id))
        conn.commit()
        conn.close()
    
    # Check if test user exists
    # existing_user = user_repo.find_by_username('user')
    # if existing_user:
    #     print("ℹ️  Test user already exists")
    # else:
    #     # Create test user
    #     user_request = RegisterRequest(
    #         username='user',
    #         email='user@example.com',
    #         password='justice#404',
    #         full_name='Test User'
    #     )
    #     test_user = auth_service.register(user_request)
    
    print("\n📊 Seeding completed!")
    print("\n🔑 Default credentials:")
    print("   Admin: " + username + " / " + password)

def show_help():
    """Show available commands"""
    print("""
        📚 Database Management Commands

        Usage: python manage.py [command]

        Commands:
        migrate         Run database migrations
        migrate:fresh   Drop all tables and re-run migrations (⚠️  deletes all data)
        seed            Seed database with initial data
        run             Run the application
        help            Show this help message

        Examples:
        python manage.py migrate
        python manage.py migrate:fresh
        python manage.py seed
        python manage.py run
        
        # Fresh start with seed data
        python manage.py migrate:fresh && python manage.py seed
        """)

def main():
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1]
    
    commands = {
        'migrate': migrate,
        'migrate:fresh': migrate_fresh,
        'seed': seed,
        'run': run,
        'help': show_help,
    }
    
    if command in commands:
        commands[command]()
    else:
        print(f"❌ Unknown command: {command}")
        print("Run 'python manage.py help' for available commands")

def run():
    """Run the application"""
    print("Running the application...")
    # run flask app with gunicorn (development server) dengan live reload dan logging debug mode ke console dan file app.log
    os.system('gunicorn -w 4 app:app --reload --log-level debug')

if __name__ == '__main__':
    main()
