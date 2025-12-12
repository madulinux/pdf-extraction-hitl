#!/usr/bin/env python3
"""
Database Management CLI
Commands: migrate, migrate:fresh, seed
"""
import sys
import os
import sqlite3
from pathlib import Path
from dotenv import load_dotenv

# Load .env file FIRST before any other imports
load_dotenv()

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import DatabaseManager
from core.auth.repositories import UserRepository
from core.auth.services import AuthService
from core.auth.models import RegisterRequest
from core.learning.services import ModelService
from database.repositories.job_repository import JobRepository
from core.learning.auto_trainer import get_auto_training_service
import time
import shutil

def safe_remove_folder(folder_path, folder_name="folder"):
    """
    Safely remove a folder and its contents.
    Handles Docker volume mounts gracefully.
    """
    if not os.path.exists(folder_path):
        return
    
    try:
        # Delete all files and subdirectories
        for root, dirs, files in os.walk(folder_path, topdown=False):
            for file in files:
                try:
                    os.remove(os.path.join(root, file))
                except Exception as e:
                    print(f"⚠️  Warning: Could not delete file {file}: {e}")
            
            for dir in dirs:
                try:
                    os.rmdir(os.path.join(root, dir))
                except OSError:
                    pass  # Skip if directory is not empty or is a mount point
        
        # Try to remove the folder itself (will fail if it's a Docker volume mount)
        try:
            os.rmdir(folder_path)
            print(f"🗑️  {folder_name} deleted")
        except OSError:
            print(f"🗑️  {folder_name} contents cleared (folder is a volume mount)")
    except Exception as e:
        print(f"⚠️  Warning: Could not fully clean {folder_name}: {e}")

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

    if confirm.lower() != "yes":
        print("❌ Migration cancelled")
        return

    db = DatabaseManager()

    # Delete database file
    if os.path.exists(db.db_path):
        os.remove(db.db_path)
        print("🗑️  Database deleted")

    # Delete folders using safe removal (handles Docker volume mounts)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    safe_remove_folder(
        os.path.join(base_dir, "templates"),
        "Templates folder"
    )
    
    safe_remove_folder(
        os.path.join(base_dir, "uploads"),
        "Uploads folder"
    )
    
    safe_remove_folder(
        os.path.join(base_dir, "previews"),
        "Previews folder"
    )
    
    safe_remove_folder(
        os.path.join(base_dir, "feedback"),
        "Feedback folder"
    )

    # Delete ./data/strategy_performance.json
    strategy_performance_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "data", "strategy_performance.json"
    )
    if os.path.exists(strategy_performance_path):
        os.remove(strategy_performance_path)
        print("🗑️  Strategy performance deleted")

    # Delete ./models/ folder contents (trained CRF models) - may be volume mount
    models_folder = os.path.join(base_dir, "models")
    if os.path.exists(models_folder):
        try:
            for root, dirs, files in os.walk(models_folder, topdown=False):
                for file in files:
                    try:
                        os.remove(os.path.join(root, file))
                        print(f"   🗑️  Deleted model: {file}")
                    except Exception as e:
                        print(f"   ⚠️  Could not delete {file}: {e}")
            print("🗑️  Models folder cleaned")
        except Exception as e:
            print(f"⚠️  Warning: Could not fully clean models folder: {e}")

    # Delete ./data/* files (but preserve ground_truth if it's read-only mount)
    data_folder = os.path.join(base_dir, "data")
    if os.path.exists(data_folder):
        try:
            for root, dirs, files in os.walk(data_folder, topdown=False):
                # Skip ground_truth folder (read-only mount)
                if 'ground_truth' in root:
                    continue
                    
                for file in files:
                    try:
                        os.remove(os.path.join(root, file))
                        print(f"   🗑️  Deleted data file: {file}")
                    except Exception as e:
                        print(f"   ⚠️  Could not delete {file}: {e}")
            print("🗑️  Data folder cleaned (preserved ground_truth)")
        except Exception as e:
            print(f"⚠️  Warning: Could not fully clean data folder: {e}")

    # Delete log files
    log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.log")
    if os.path.exists(log_file):
        os.remove(log_file)
        print("🗑️  Log file deleted")

    # Re-create database
    print("🔄 Creating fresh database...")
    db = DatabaseManager()
    print("✅ Fresh database created successfully!")
    print(f"📁 Database location: {db.db_path}")
    # seed()


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
            email="madulinux@gmail.com",
            password=password,
            full_name="Administrator",
        )
        admin_user = auth_service.register(admin_request)
        # Update role to admin manually using SQL
        conn = user_repo._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET role = ? WHERE id = ?", ("admin", admin_user.id)
        )
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


def train():
    """Train or retrain a model"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Train extraction model')
    parser.add_argument('--template-id', type=int, required=True,
                       help='Template ID to train')
    parser.add_argument('--mode', choices=['full', 'incremental'], default='full',
                       help='Training mode: full or incremental (default: full)')
    parser.add_argument('--use-all', action='store_true',
                       help='Use all feedback (not just unused)')
    parser.add_argument('--force-validation', action='store_true',
                       help='Force validation even for incremental')
    parser.add_argument('--workers', type=int, default=None,
                       help='Number of parallel workers for PDF extraction (default: CPU count)')
    parser.add_argument('--no-parallel', action='store_true',
                       help='Disable parallel processing (slower but less memory)')
    parser.add_argument('--max-iterations', type=int, default=500,
                       help='Maximum L-BFGS iterations for CRF training (default: 500)')
    parser.add_argument('--fast', action='store_true',
                       help='Fast training mode (50 iterations, ~2x faster)')
    
    
    # Parse only the arguments after 'train'
    args = parser.parse_args(sys.argv[2:])
    
    # Determine workers
    if args.no_parallel:
        workers = 1
    elif args.workers:
        workers = args.workers
    else:
        import multiprocessing
        workers = multiprocessing.cpu_count()
    
    # Determine max iterations
    if args.fast:
        max_iterations = 50
    else:
        max_iterations = args.max_iterations
    
    print(f"\n🎓 Training Model")
    print(f"   Template ID: {args.template_id}")
    print(f"   Mode: {args.mode}")
    print(f"   Use all feedback: {args.use_all}")
    print(f"   Force validation: {args.force_validation}")
    print(f"   Parallel workers: {workers} {'(disabled)' if args.no_parallel else ''}")
    print(f"   Max iterations: {max_iterations} {'(fast mode)' if args.fast else ''}")
    print()
    
    start_time = time.time()
    try:
        db = DatabaseManager()
        service = ModelService(db)
        
        is_incremental = (args.mode == 'incremental')
        
        # Set parallel workers in service
        if hasattr(service, 'set_parallel_workers'):
            service.set_parallel_workers(workers)
        
        # Set max iterations in service
        if hasattr(service, 'set_max_iterations'):
            service.set_max_iterations(max_iterations)
        
        result = service.retrain_model(
            template_id=args.template_id,
            use_all_feedback=args.use_all,
            model_folder='models',
            is_incremental=is_incremental,
            force_validation=args.force_validation
        )
        
        print(f"\n✅ Training completed successfully!")
        print(f"   Training samples: {result.get('training_samples', 0)}")
        print(f"   Test accuracy: {result.get('test_accuracy', 0):.2%}")
        print(f"   Model saved to: models/template_{args.template_id}_model.joblib")
        
        end_time = time.time()
        print(f"\nTraining time: {end_time - start_time:.2f} seconds")
    except Exception as e:
        end_time = time.time()
        print(f"\nTraining time: {end_time - start_time:.2f} seconds")
        print(f"\n❌ Training failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def worker():
    """Background worker to process queued jobs (auto_training)."""
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Background job worker")
    parser.add_argument("--sleep", type=int, default=5,
                        help="Sleep seconds between job polls (default: 5)")
    args = parser.parse_args(sys.argv[2:])

    print("🔧 Starting worker for auto_training jobs...")

    db = DatabaseManager()
    job_repo = JobRepository(db)

    try:
        while True:
            job = job_repo.fetch_next_pending_auto_training()
            if not job:
                # No jobs, sleep then continue
                time.sleep(args.sleep)
                continue

            job_id = job["id"] if isinstance(job, dict) else job["id"]
            template_id = job["template_id"]

            print(f"\n⚙️  Processing job {job_id} for template {template_id}...")
            job_repo.mark_running(job_id)

            try:
                payload = json.loads(job["payload"])
                model_folder = payload.get("model_folder", "models")
                is_first_training = payload.get("is_first_training", False)

                auto_trainer = get_auto_training_service(db)
                result = auto_trainer.check_and_train(
                    template_id=template_id,
                    model_folder=model_folder,
                    force_first_training=is_first_training,
                )

                if result:
                    accuracy = result['test_metrics'].get('accuracy')
                    if accuracy is not None:
                        print(
                            f"✅ Auto-training completed for template {template_id}: "
                            f"{result['training_samples']} samples, "
                            f"{accuracy*100:.2f}% accuracy"
                        )
                    else:
                        print(
                            f"✅ Auto-training completed for template {template_id}: "
                            f"{result['training_samples']} samples (metrics not evaluated)"
                        )
                    job_repo.mark_completed(job_id)
                else:
                    print(f"ℹ️  Auto-training skipped for template {template_id} (conditions not met)")
                    # Mark as completed even if skipped (not an error, just conditions not met)
                    job_repo.mark_completed(job_id)

            except Exception as e:
                print(f"❌ Job {job_id} failed: {e}")
                import traceback
                traceback.print_exc()
                
                # Mark job as failed and log to failed_jobs table
                job_repo.mark_failed(job_id, str(e))

    except KeyboardInterrupt:
        print("\n🛑 Worker stopped by user")


def show_help():
    """Show available commands"""
    print(
        """
    📚 Available Commands:
    ==================
        migrate         Run database migrations
        migrate:fresh   Drop all tables and re-run migrations (⚠️  deletes all data)
        seed            Seed database with initial data
        train           Train or retrain extraction model
        worker          Run background worker to process jobs (auto_training)
        runserver       Run the application
        help            Show this help message

        Examples:
        python manage.py migrate
        python manage.py migrate:fresh
        python manage.py seed
        python manage.py train --template-id 1 --mode full --use-all
        python manage.py train --template-id 1 --mode full --use-all --workers 8
        python manage.py train --template-id 1 --mode full --use-all --no-parallel
        python manage.py train --template-id 2 --mode incremental --use-all
        python manage.py worker --sleep 5
        python manage.py runserver --background
        python manage.py stopserver
        python manage.py restartserver
        python manage.py logserver
        
        # Fresh start with seed data
        python manage.py migrate:fresh && python manage.py seed
        
        # Training Performance Options:
        --workers N          Use N parallel workers for PDF extraction (default: CPU count)
        --no-parallel        Disable parallel processing (slower but less memory)
        --max-iterations N   Maximum L-BFGS iterations for CRF (default: 100)
        --fast               Fast training mode (50 iterations, ~2x faster)
        
        # Train model after seeding
        python manage.py train --template-id 1 --mode full
        """
    )


def runserver():
    """Run the application"""
    print("Running the application...")
    # run flask app with gunicorn (development server) dengan live reload dan logging debug mode ke console
    os.system(
        "gunicorn --timeout 120 --graceful-timeout 300 -w 16 app:app --reload --log-level debug"
    )


def main():
    if len(sys.argv) < 2:
        show_help()
        return

    command = sys.argv[1]

    commands = {
        "migrate": migrate,
        "migrate:fresh": migrate_fresh,
        "seed": seed,
        "train": train,
        "runserver": runserver,
        "stopserver": stopserver,
        "restartserver": restartserver,
        "logserver": logserver,
        "help": show_help,
        "worker": worker,
    }

    if command in commands:
        commands[command]()
    else:
        print(f"❌ Unknown command: {command}")
        print("Run 'python manage.py help' for available commands")


def logserver():
    """Show server log"""
    print("Showing server log...")
    os.system("tail -f server.log")

def restartserver():
    """Restart the application"""
    print("Restarting the application...")
    stopserver()
    runserver()

def stopserver():
    """Stop the application"""
    print("Stopping the application...")
    # stop gunicorn server
    os.system("pkill -f gunicorn")

def runserver():
    """Run the application"""
    print("Running the application...")
    # run flask app with gunicorn (development server) dengan live reload dan logging debug mode ke console
    # run on background with nohup log to file
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--background", action="store_true")
    args = parser.parse_args(sys.argv[2:])

    try:
        if args.background:
            os.system(
                "nohup gunicorn --timeout 240 --graceful-timeout 600 -w 8 app:app > server.log 2>&1 &"
            )
        else:
            os.system(
                "gunicorn --timeout 120 --graceful-timeout 300 -w 8 app:app --reload --log-level debug"
            )
    except Exception as e:
        print(f"❌ Failed to run server: {e}")
    
    print("✅ Server started successfully!")


if __name__ == "__main__":
    main()
