"""
Test password hash from migration
"""
from core.auth.utils import PasswordHasher

# Hash from migration
migration_hash = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIeWEgEjqK'

# Test password
password = 'justice#404'

# Verify
hasher = PasswordHasher()
is_valid = hasher.verify(password, migration_hash)

print(f"Password: {password}")
print(f"Hash: {migration_hash}")
print(f"Valid: {is_valid}")

if not is_valid:
    print("\n❌ Migration hash is INVALID!")
    print("Generating correct hash...")
    correct_hash = hasher.hash(password)
    print(f"Correct hash: {correct_hash}")
    print("\nUpdate migration file with this hash!")
