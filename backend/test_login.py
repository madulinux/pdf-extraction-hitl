#!/usr/bin/env python3
"""
Test login functionality
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.auth.repositories import UserRepository
from core.auth.services import AuthService
from core.auth.models import LoginRequest
from core.auth.utils import PasswordHasher

# Test 1: Check if user exists
print("=" * 50)
print("TEST 1: Check if user exists")
print("=" * 50)

db_path = 'data/app.db'
user_repo = UserRepository(db_path)
user_data = user_repo.find_by_username('admin')

if user_data:
    print(f"✅ User found: {user_data['username']}")
    print(f"   Email: {user_data['email']}")
    print(f"   Role: {user_data['role']}")
    print(f"   Active: {user_data['is_active']}")
    print(f"   Password hash length: {len(user_data['password_hash'])}")
else:
    print("❌ User not found!")
    sys.exit(1)

# Test 2: Verify password
print("\n" + "=" * 50)
print("TEST 2: Verify password")
print("=" * 50)

password = 'admin123'
password_hash = user_data['password_hash']

print(f"Password: {password}")
print(f"Hash: {password_hash[:20]}...")

is_valid = PasswordHasher.verify(password, password_hash)
print(f"Password valid: {is_valid}")

if not is_valid:
    print("\n❌ Password verification failed!")
    print("   This means the password hash in database is wrong")
    sys.exit(1)
else:
    print("✅ Password verification successful!")

# Test 3: Full login flow
print("\n" + "=" * 50)
print("TEST 3: Full login flow")
print("=" * 50)

auth_service = AuthService(user_repo)
login_request = LoginRequest(username='admin', password='admin123')

try:
    tokens = auth_service.login(login_request)
    print("✅ Login successful!")
    print(f"   Access token: {tokens.access_token[:50]}...")
    print(f"   Refresh token: {tokens.refresh_token[:50]}...")
except Exception as e:
    print(f"❌ Login failed: {e}")
    sys.exit(1)

print("\n" + "=" * 50)
print("ALL TESTS PASSED! ✅")
print("=" * 50)
