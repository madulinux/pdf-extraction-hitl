"""
Auth Utilities
Password hashing and JWT token management
"""
import bcrypt
import jwt
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional
import os


class PasswordHasher:
    """Password hashing utilities using bcrypt"""
    
    @staticmethod
    def hash(password: str) -> str:
        """
        Hash a password using bcrypt
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify(password: str, password_hash: str) -> bool:
        """
        Verify a password against its hash
        
        Args:
            password: Plain text password
            password_hash: Hashed password
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                password_hash.encode('utf-8')
            )
        except Exception:
            return False


class JWTManager:
    """JWT token management"""
    
    # Get secret key from environment or use default (change in production!)
    SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-this-in-production')
    ALGORITHM = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour
    REFRESH_TOKEN_EXPIRE_DAYS = 30  # 30 days
    
    @classmethod
    def create_access_token(cls, user_id: int, username: str, role: str) -> str:
        """
        Create JWT access token
        
        Args:
            user_id: User ID
            username: Username
            role: User role
            
        Returns:
            JWT access token
        """
        now = datetime.utcnow()
        expires = now + timedelta(minutes=cls.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        payload = {
            'user_id': user_id,
            'username': username,
            'role': role,
            'type': 'access',
            'iat': now,
            'exp': expires
        }
        
        token = jwt.encode(payload, cls.SECRET_KEY, algorithm=cls.ALGORITHM)
        return token
    
    @classmethod
    def create_refresh_token(cls) -> str:
        """
        Create refresh token (random string)
        
        Returns:
            Refresh token
        """
        return secrets.token_urlsafe(32)
    
    @classmethod
    def decode_token(cls, token: str) -> Optional[Dict]:
        """
        Decode and verify JWT token
        
        Args:
            token: JWT token
            
        Returns:
            Decoded payload or None if invalid
        """
        try:
            payload = jwt.decode(
                token,
                cls.SECRET_KEY,
                algorithms=[cls.ALGORITHM]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")
    
    @classmethod
    def get_refresh_token_expiry(cls) -> datetime:
        """
        Get refresh token expiry datetime
        
        Returns:
            Expiry datetime
        """
        return datetime.utcnow() + timedelta(days=cls.REFRESH_TOKEN_EXPIRE_DAYS)
