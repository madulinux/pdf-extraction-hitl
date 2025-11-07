"""
Auth Repositories
Data access layer for authentication
"""
from typing import Optional, Dict
from datetime import datetime
import sqlite3

from .models import User


class UserRepository:
    """Repository for user data access"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.Connection(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def create(
        self,
        username: str,
        email: str,
        password_hash: str,
        full_name: Optional[str] = None,
        role: str = 'user'
    ) -> int:
        """
        Create a new user
        
        Args:
            username: Username
            email: Email address
            password_hash: Hashed password
            full_name: Full name (optional)
            role: User role (default: 'user')
            
        Returns:
            User ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, full_name, role)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, email, password_hash, full_name, role))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return user_id
    
    def find_by_id(self, user_id: int) -> Optional[User]:
        """Find user by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, full_name, role, is_active, created_at, updated_at
            FROM users
            WHERE id = ?
        ''', (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return User(
            id=row['id'],
            username=row['username'],
            email=row['email'],
            full_name=row['full_name'],
            role=row['role'],
            is_active=bool(row['is_active']),
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
        )
    
    def find_by_username(self, username: str) -> Optional[Dict]:
        """
        Find user by username (includes password_hash for authentication)
        
        Returns:
            User dict with password_hash or None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, password_hash, full_name, role, is_active, created_at, updated_at
            FROM users
            WHERE username = ?
        ''', (username,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return dict(row)
    
    def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, full_name, role, is_active, created_at, updated_at
            FROM users
            WHERE email = ?
        ''', (email,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return User(
            id=row['id'],
            username=row['username'],
            email=row['email'],
            full_name=row['full_name'],
            role=row['role'],
            is_active=bool(row['is_active']),
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
        )
    
    def username_exists(self, username: str) -> bool:
        """Check if username exists"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as count FROM users WHERE username = ?', (username,))
        result = cursor.fetchone()
        conn.close()
        
        return result['count'] > 0
    
    def email_exists(self, email: str) -> bool:
        """Check if email exists"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as count FROM users WHERE email = ?', (email,))
        result = cursor.fetchone()
        conn.close()
        
        return result['count'] > 0
    
    def save_refresh_token(self, user_id: int, token: str, expires_at: datetime) -> int:
        """Save refresh token"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO refresh_tokens (user_id, token, expires_at)
            VALUES (?, ?, ?)
        ''', (user_id, token, expires_at.isoformat()))
        
        token_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return token_id
    
    def find_refresh_token(self, token: str) -> Optional[Dict]:
        """Find refresh token"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, user_id, token, expires_at, created_at
            FROM refresh_tokens
            WHERE token = ?
        ''', (token,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return dict(row)
    
    def delete_refresh_token(self, token: str):
        """Delete refresh token"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM refresh_tokens WHERE token = ?', (token,))
        
        conn.commit()
        conn.close()
    
    def delete_user_refresh_tokens(self, user_id: int):
        """Delete all refresh tokens for a user"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM refresh_tokens WHERE user_id = ?', (user_id,))
        
        conn.commit()
        conn.close()
