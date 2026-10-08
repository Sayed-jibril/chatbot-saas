#!/usr/bin/env python
"""
User Management Script for BotSaaS
Run with: python manage_users.py [command] [options]
"""

import sys
import os
import argparse
import uuid
from datetime import datetime
import bcrypt
import time

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import project modules
try:
    from app.database import db
    from app.auth import hash_password
    from app.config import Config
except ImportError as e:
    print(f"Error importing project modules: {e}")
    print("Make sure you're running this script from the project root directory.")
    sys.exit(1)

# Color codes for terminal output


class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")


def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.END}")


def print_info(message):
    print(f"{Colors.BLUE}ℹ {message}{Colors.END}")


def print_warning(message):
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")


def print_table(headers, rows):
    """Print a formatted table"""
    # Calculate column widths
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    # Print headers
    header_line = " | ".join([h.ljust(col_widths[i])
                             for i, h in enumerate(headers)])
    print(header_line)
    print("-" * len(header_line))

    # Print rows
    for row in rows:
        print(" | ".join([str(cell).ljust(col_widths[i])
              for i, cell in enumerate(row)]))


def check_db_connection():
    """Check if database is connected"""
    try:
        # Simple query to test connection
        result = db.execute("SELECT 1", fetch_one=True)
        return True
    except Exception as e:
        print_error(f"Database connection failed: {e}")
        print_info("Please check:")
        print_info("1. MySQL is running")
        print_info("2. Database credentials in .env are correct")
        print_info("3. Database 'chatbot_saas' exists")
        return False


def create_admin(args):
    """Create a new admin user"""
    print(f"{Colors.BOLD}Creating new admin user...{Colors.END}")

    # Get user input
    if not args.email:
        args.email = input("Email: ").strip()
    if not args.name:
        args.name = input("Full Name: ").strip()
    if not args.password:
        import getpass
        args.password = getpass.getpass("Password: ")
        confirm = getpass.getpass("Confirm Password: ")
        if args.password != confirm:
            print_error("Passwords do not match")
            return

    # Validate input
    if not args.email or not args.name or not args.password:
        print_error("Email, name, and password are required")
        return

    try:
        # Check if user exists
        existing = db.execute(
            "SELECT id FROM users WHERE email = %s",
            (args.email,),
            fetch_one=True
        )

        if existing:
            print_error(f"User with email {args.email} already exists")
            return

        # Create user
        user_id = str(uuid.uuid4())
        password_hash = hash_password(args.password)

        # Admin gets business plan with high limits
        plan_type = 'business'
        token_limit = 1000000  # 1M tokens for admin

        db.execute(
            """INSERT INTO users (id, name, email, password_hash, plan_type, token_limit, created_at)
               VALUES (%s, %s, %s, %s, %s, %s, NOW())""",
            (user_id, args.name, args.email, password_hash, plan_type, token_limit)
        )

        print_success(f"Admin user created successfully!")
        print_info(f"Email: {args.email}")
        print_info(f"Name: {args.name}")
        print_info(f"Plan: {plan_type}")
        print_info(f"Token Limit: {token_limit}")

    except Exception as e:
        print_error(f"Failed to create admin: {e}")
        import traceback
        traceback.print_exc()


def create_user(args):
    """Create a new regular user"""
    print(f"{Colors.BOLD}Creating new regular user...{Colors.END}")

    # Get user input
    if not args.email:
        args.email = input("Email: ").strip()
    if not args.name:
        args.name = input("Full Name: ").strip()
    if not args.password:
        import getpass
        args.password = getpass.getpass("Password: ")
        confirm = getpass.getpass("Confirm Password: ")
        if args.password != confirm:
            print_error("Passwords do not match")
            return

    # Validate input
    if not args.email or not args.name or not args.password:
        print_error("Email, name, and password are required")
        return

    # Select plan
    if not args.plan:
        print("\nSelect plan:")
        print("1. Free (1 bot, 5 documents, 10K tokens)")
        print("2. Pro (5 bots, 100 documents, 100K tokens)")
        print("3. Business (100 bots, 1000 documents, 1M tokens)")
        choice = input("Enter choice (1-3) [1]: ").strip() or "1"

        plan_map = {"1": "free", "2": "pro", "3": "business"}
        args.plan = plan_map.get(choice, "free")

    # Set token limit based on plan
    token_limits = {
        'free': 10000,
        'pro': 100000,
        'business': 1000000
    }
    token_limit = token_limits.get(args.plan, 10000)

    try:
        # Check if user exists
        existing = db.execute(
            "SELECT id FROM users WHERE email = %s",
            (args.email,),
            fetch_one=True
        )

        if existing:
            print_error(f"User with email {args.email} already exists")
            return

        # Create user
        user_id = str(uuid.uuid4())
        password_hash = hash_password(args.password)

        db.execute(
            """INSERT INTO users (id, name, email, password_hash, plan_type, token_limit, created_at)
               VALUES (%s, %s, %s, %s, %s, %s, NOW())""",
            (user_id, args.name, args.email, password_hash, args.plan, token_limit)
        )

        print_success(f"User created successfully!")
        print_info(f"Email: {args.email}")
        print_info(f"Name: {args.name}")
        print_info(f"Plan: {args.plan}")
        print_info(f"Token Limit: {token_limit}")

    except Exception as e:
        print_error(f"Failed to create user: {e}")


def list_users(args):
    """List all users"""
    print(f"{Colors.BOLD}Listing all users...{Colors.END}\n")

    try:
        users = db.execute(
            """SELECT id, name, email, plan_type, tokens_used, token_limit, created_at 
               FROM users ORDER BY created_at DESC""",
            fetch_all=True
        )

        if not users:
            print_warning("No users found")
            return

        # Prepare data for table
        headers = ["ID", "Name", "Email", "Plan",
                   "Tokens Used", "Token Limit", "Created"]
        rows = []
        for user in users:
            rows.append([
                user['id'][:8] + "...",  # Truncate UUID
                user['name'],
                user['email'],
                user['plan_type'],
                f"{user['tokens_used']:,}",
                f"{user['token_limit']:,}",
                user['created_at'].strftime(
                    '%Y-%m-%d') if user['created_at'] else 'N/A'
            ])

        print_table(headers, rows)
        print(f"\n{Colors.BOLD}Total users: {len(users)}{Colors.END}")

    except Exception as e:
        print_error(f"Failed to list users: {e}")


def delete_user(args):
    """Delete a user"""
    if not args.email and not args.id:
        print_error("Please provide either --email or --id")
        return

    try:
        # Find user
        if args.id:
            user = db.execute(
                "SELECT id, name, email FROM users WHERE id = %s",
                (args.id,),
                fetch_one=True
            )
        else:
            user = db.execute(
                "SELECT id, name, email FROM users WHERE email = %s",
                (args.email,),
                fetch_one=True
            )

        if not user:
            print_error("User not found")
            return

        # Confirm deletion
        print_warning(
            f"About to delete user: {user['name']} ({user['email']})")
        print_warning(
            "This will delete ALL bots, documents, and conversations for this user!")

        confirm = input("Are you sure? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print_info("Deletion cancelled")
            return

        # Delete user (cascade will delete related records)
        db.execute("DELETE FROM users WHERE id = %s", (user['id'],))
        print_success(f"User {user['email']} deleted successfully")

    except Exception as e:
        print_error(f"Failed to delete user: {e}")


def reset_password(args):
    """Reset user password"""
    if not args.email:
        args.email = input("Email: ").strip()

    try:
        # Find user
        user = db.execute(
            "SELECT id, name, email FROM users WHERE email = %s",
            (args.email,),
            fetch_one=True
        )

        if not user:
            print_error(f"User with email {args.email} not found")
            return

        # Get new password
        import getpass
        print(f"Resetting password for: {user['name']} ({user['email']})")
        new_password = getpass.getpass("New password: ")
        confirm = getpass.getpass("Confirm password: ")

        if new_password != confirm:
            print_error("Passwords do not match")
            return

        # Update password
        password_hash = hash_password(new_password)

        db.execute(
            "UPDATE users SET password_hash = %s WHERE id = %s",
            (password_hash, user['id'])
        )
        print_success(f"Password reset successfully for {user['email']}")

    except Exception as e:
        print_error(f"Failed to reset password: {e}")


def set_plan(args):
    """Change user's plan"""
    if not args.email:
        args.email = input("Email: ").strip()

    try:
        # Find user
        user = db.execute(
            "SELECT id, name, email, plan_type FROM users WHERE email = %s",
            (args.email,),
            fetch_one=True
        )

        if not user:
            print_error(f"User with email {args.email} not found")
            return

        print(f"Current plan for {user['name']}: {user['plan_type']}")

        # Select new plan
        if not args.plan:
            print("\nSelect new plan:")
            print("1. Free (1 bot, 5 documents, 10K tokens)")
            print("2. Pro (5 bots, 100 documents, 100K tokens)")
            print("3. Business (100 bots, 1000 documents, 1M tokens)")
            choice = input("Enter choice (1-3): ").strip()

            plan_map = {"1": "free", "2": "pro", "3": "business"}
            args.plan = plan_map.get(choice)

            if not args.plan:
                print_error("Invalid choice")
                return

        # Set token limit based on plan
        token_limits = {
            'free': 10000,
            'pro': 100000,
            'business': 1000000
        }
        token_limit = token_limits.get(args.plan, 10000)

        db.execute(
            "UPDATE users SET plan_type = %s, token_limit = %s WHERE id = %s",
            (args.plan, token_limit, user['id'])
        )
        print_success(f"Plan updated to {args.plan} for {user['email']}")

    except Exception as e:
        print_error(f"Failed to update plan: {e}")


def main():
    parser = argparse.ArgumentParser(description='BotSaaS User Management')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Create admin command
    admin_parser = subparsers.add_parser(
        'create-admin', help='Create admin user')
    admin_parser.add_argument('--email', help='Admin email')
    admin_parser.add_argument('--name', help='Admin name')
    admin_parser.add_argument('--password', help='Admin password')

    # Create user command
    user_parser = subparsers.add_parser(
        'create-user', help='Create regular user')
    user_parser.add_argument('--email', help='User email')
    user_parser.add_argument('--name', help='User name')
    user_parser.add_argument('--password', help='User password')
    user_parser.add_argument(
        '--plan', choices=['free', 'pro', 'business'], help='User plan')

    # List users command
    subparsers.add_parser('list-users', help='List all users')

    # Delete user command
    delete_parser = subparsers.add_parser('delete-user', help='Delete user')
    delete_parser.add_argument('--email', help='User email')
    delete_parser.add_argument('--id', help='User ID')

    # Reset password command
    reset_parser = subparsers.add_parser(
        'reset-password', help='Reset user password')
    reset_parser.add_argument('--email', help='User email')

    # Set plan command
    plan_parser = subparsers.add_parser('set-plan', help='Change user plan')
    plan_parser.add_argument('--email', help='User email')
    plan_parser.add_argument(
        '--plan', choices=['free', 'pro', 'business'], help='New plan')

    args = parser.parse_args()

    # Check database connection
    print_info("Testing database connection...")
    time.sleep(1)  # Give time for connection to establish

    if not check_db_connection():
        print_error("Cannot connect to database. Please check:")
        print_error("1. Is MySQL running?")
        print_error("2. Are your .env credentials correct?")
        print_error("3. Does the database 'chatbot_saas' exist?")
        sys.exit(1)

    print_success("Database connection successful!")
    print()

    # Execute command
    if args.command == 'create-admin':
        create_admin(args)
    elif args.command == 'create-user':
        create_user(args)
    elif args.command == 'list-users':
        list_users(args)
    elif args.command == 'delete-user':
        delete_user(args)
    elif args.command == 'reset-password':
        reset_password(args)
    elif args.command == 'set-plan':
        set_plan(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
