"""
Auth API Routes
Authentication endpoints
"""
from flask import Blueprint, request, g

from core.auth.models import RegisterRequest, LoginRequest
from core.auth.services import AuthService
from core.auth.repositories import UserRepository
from utils.response import APIResponse
from utils.decorators import handle_errors
from api.middleware.auth import require_auth
from shared.exceptions import ValidationError, AuthenticationError
import os


# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')

# Initialize service
db_path = os.getenv('DATABASE_PATH', 'data/app.db')
user_repository = UserRepository(db_path)
auth_service = AuthService(user_repository)


@auth_bp.route('/register', methods=['POST'])
@handle_errors
def register():
    """
    Register a new user
    
    Request Body:
    {
        "username": "string",
        "email": "string",
        "password": "string",
        "full_name": "string" (optional)
    }
    
    Returns:
        201: User created successfully
        400: Validation error
    """
    data = request.get_json()
    
    # Validate required fields
    if not data:
        return APIResponse.bad_request("Request body is required")
    
    required_fields = ['username', 'email', 'password']
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        return APIResponse.bad_request(
            "Missing required fields",
            {'missing_fields': missing_fields}
        )
    
    # Create request model
    register_request = RegisterRequest(
        username=data['username'],
        email=data['email'],
        password=data['password'],
        full_name=data.get('full_name')
    )
    
    try:
        # Register user
        user = auth_service.register(register_request)
        
        return APIResponse.created(
            {'user': user.to_dict()},
            "User registered successfully"
        )
    
    except ValidationError as e:
        return APIResponse.bad_request(str(e))


@auth_bp.route('/login', methods=['POST'])
@handle_errors
def login():
    """
    Login user
    
    Request Body:
    {
        "username": "string",
        "password": "string"
    }
    
    Returns:
        200: Login successful with tokens
        401: Invalid credentials
    """
    data = request.get_json()
    
    # Validate required fields
    if not data:
        return APIResponse.bad_request("Request body is required")
    
    required_fields = ['username', 'password']
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        return APIResponse.bad_request(
            "Missing required fields",
            {'missing_fields': missing_fields}
        )
    
    # Create request model
    login_request = LoginRequest(
        username=data['username'],
        password=data['password']
    )
    
    try:
        # Login
        tokens = auth_service.login(login_request)
        
        return APIResponse.success(
            {'tokens': tokens.to_dict()},
            "Login successful"
        )
    
    except AuthenticationError as e:
        return APIResponse.unauthorized(str(e))


@auth_bp.route('/refresh', methods=['POST'])
@handle_errors
def refresh_token():
    """
    Refresh access token
    
    Request Body:
    {
        "refresh_token": "string"
    }
    
    Returns:
        200: New tokens
        401: Invalid or expired refresh token
    """
    data = request.get_json()
    
    if not data or 'refresh_token' not in data:
        return APIResponse.bad_request("Refresh token is required")
    
    try:
        # Refresh tokens
        tokens = auth_service.refresh_access_token(data['refresh_token'])
        
        return APIResponse.success(
            {'tokens': tokens.to_dict()},
            "Token refreshed successfully"
        )
    
    except AuthenticationError as e:
        return APIResponse.unauthorized(str(e))


@auth_bp.route('/logout', methods=['POST'])
@handle_errors
@require_auth
def logout():
    """
    Logout user
    
    Request Body:
    {
        "refresh_token": "string"
    }
    
    Returns:
        200: Logout successful
    """
    data = request.get_json()
    
    if not data or 'refresh_token' not in data:
        return APIResponse.bad_request("Refresh token is required")
    
    # Logout
    auth_service.logout(data['refresh_token'])
    
    return APIResponse.success(
        None,
        "Logout successful"
    )


@auth_bp.route('/me', methods=['GET'])
@handle_errors
@require_auth
def get_current_user():
    """
    Get current authenticated user
    
    Returns:
        200: User info
        401: Not authenticated
    """
    # Get user from service
    user = auth_service.get_user_by_id(g.user_id)
    
    if not user:
        return APIResponse.not_found("User not found")
    
    return APIResponse.success(
        {'user': user.to_dict()},
        "User retrieved successfully"
    )


@auth_bp.route('/verify', methods=['GET'])
@handle_errors
@require_auth
def verify_token():
    """
    Verify if token is valid
    
    Returns:
        200: Token is valid
        401: Token is invalid
    """
    return APIResponse.success(
        {
            'user_id': g.user_id,
            'username': g.username,
            'role': g.user_role
        },
        "Token is valid"
    )
