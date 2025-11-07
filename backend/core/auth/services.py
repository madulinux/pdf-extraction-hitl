"""
Auth Services
Business logic for authentication and authorization
"""
from typing import Optional
from datetime import datetime

from .models import User, TokenPair, RegisterRequest, LoginRequest
from .repositories import UserRepository
from .utils import PasswordHasher, JWTManager
from shared.exceptions import AuthenticationError, ValidationError


class AuthService:
    """Authentication service"""
    
    def __init__(self, repository: UserRepository):
        self.repository = repository
    
    def register(self, request: RegisterRequest) -> User:
        """
        Register a new user
        
        Args:
            request: Registration request
            
        Returns:
            Created user
            
        Raises:
            ValidationError: If validation fails
        """
        # Validate username
        if self.repository.username_exists(request.username):
            raise ValidationError("Username already exists")
        
        # Validate email
        if self.repository.email_exists(request.email):
            raise ValidationError("Email already exists")
        
        # Validate password strength
        if len(request.password) < 6:
            raise ValidationError("Password must be at least 6 characters")
        
        # Hash password
        password_hash = PasswordHasher.hash(request.password)
        
        # Create user
        user_id = self.repository.create(
            username=request.username,
            email=request.email,
            password_hash=password_hash,
            full_name=request.full_name,
            role='user'  # Default role
        )
        
        # Get created user
        user = self.repository.find_by_id(user_id)
        
        return user
    
    def login(self, request: LoginRequest) -> TokenPair:
        """
        Authenticate user and generate tokens
        
        Args:
            request: Login request
            
        Returns:
            Token pair
            
        Raises:
            AuthenticationError: If authentication fails
        """
        # Find user (includes password_hash)
        user_data = self.repository.find_by_username(request.username)
        
        if not user_data:
            raise AuthenticationError("Invalid username or password")
        
        # Check if user is active
        if not user_data['is_active']:
            raise AuthenticationError("User account is inactive")
        
        # Verify password
        if not PasswordHasher.verify(request.password, user_data['password_hash']):
            raise AuthenticationError("Invalid username or password")
        
        # Generate tokens
        access_token = JWTManager.create_access_token(
            user_id=user_data['id'],
            username=user_data['username'],
            role=user_data['role']
        )
        
        refresh_token = JWTManager.create_refresh_token()
        
        # Save refresh token
        expires_at = JWTManager.get_refresh_token_expiry()
        self.repository.save_refresh_token(
            user_id=user_data['id'],
            token=refresh_token,
            expires_at=expires_at
        )
        
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token
        )
    
    def refresh_access_token(self, refresh_token: str) -> TokenPair:
        """
        Refresh access token using refresh token
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            New token pair
            
        Raises:
            AuthenticationError: If refresh token is invalid
        """
        # Find refresh token
        token_data = self.repository.find_refresh_token(refresh_token)
        
        if not token_data:
            raise AuthenticationError("Invalid refresh token")
        
        # Check if token is expired
        expires_at = datetime.fromisoformat(token_data['expires_at'])
        if datetime.utcnow() > expires_at:
            # Delete expired token
            self.repository.delete_refresh_token(refresh_token)
            raise AuthenticationError("Refresh token has expired")
        
        # Get user
        user = self.repository.find_by_id(token_data['user_id'])
        
        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive")
        
        # Generate new tokens
        access_token = JWTManager.create_access_token(
            user_id=user.id,
            username=user.username,
            role=user.role
        )
        
        new_refresh_token = JWTManager.create_refresh_token()
        
        # Delete old refresh token
        self.repository.delete_refresh_token(refresh_token)
        
        # Save new refresh token
        expires_at = JWTManager.get_refresh_token_expiry()
        self.repository.save_refresh_token(
            user_id=user.id,
            token=new_refresh_token,
            expires_at=expires_at
        )
        
        return TokenPair(
            access_token=access_token,
            refresh_token=new_refresh_token
        )
    
    def logout(self, refresh_token: str):
        """
        Logout user by deleting refresh token
        
        Args:
            refresh_token: Refresh token to delete
        """
        self.repository.delete_refresh_token(refresh_token)
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.repository.find_by_id(user_id)
    
    def verify_token(self, token: str) -> dict:
        """
        Verify access token
        
        Args:
            token: Access token
            
        Returns:
            Token payload
            
        Raises:
            AuthenticationError: If token is invalid
        """
        try:
            payload = JWTManager.decode_token(token)
            return payload
        except ValueError as e:
            raise AuthenticationError(str(e))
