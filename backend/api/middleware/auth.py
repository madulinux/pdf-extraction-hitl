"""
Authentication Middleware
JWT token verification and role-based access control
"""
from functools import wraps
from flask import request, g
from typing import Callable

from core.auth.utils import JWTManager
from utils.response import APIResponse
from shared.exceptions import AuthenticationError, AuthorizationError


def require_auth(f: Callable) -> Callable:
    """
    Decorator to require authentication
    Verifies JWT token and sets user info in request context
    
    Usage:
        @require_auth
        def my_route():
            user_id = g.user_id
            user_role = g.user_role
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Get token from Authorization header OR query string (for image requests)
        auth_header = request.headers.get('Authorization', '')
        token = None
        
        if auth_header:
            # Extract token from header
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]
        
        # Fallback: Check query string (for <img> tags that can't set headers)
        if not token:
            token = request.args.get('token')
        
        if not token:
            return APIResponse.unauthorized("Missing authorization token")
        
        try:
            # Verify token
            payload = JWTManager.decode_token(token)
            
            # Set user info in request context
            g.user_id = payload['user_id']
            g.username = payload['username']
            g.user_role = payload['role']
            
        except ValueError as e:
            return APIResponse.unauthorized(str(e))
        except Exception as e:
            return APIResponse.unauthorized("Invalid token")
        
        return f(*args, **kwargs)
    
    return decorated


def require_role(*allowed_roles: str) -> Callable:
    """
    Decorator to require specific role(s)
    Must be used after @require_auth
    
    Usage:
        @require_auth
        @require_role('admin')
        def admin_only_route():
            pass
        
        @require_auth
        @require_role('admin', 'user')
        def admin_or_user_route():
            pass
    
    Args:
        allowed_roles: One or more allowed roles
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated(*args, **kwargs):
            # Check if user_role is set (should be set by require_auth)
            if not hasattr(g, 'user_role'):
                return APIResponse.unauthorized("Authentication required")
            
            # Check if user has required role
            if g.user_role not in allowed_roles:
                return APIResponse.forbidden(
                    f"Insufficient permissions. Required role: {', '.join(allowed_roles)}"
                )
            
            return f(*args, **kwargs)
        
        return decorated
    
    return decorator


def optional_auth(f: Callable) -> Callable:
    """
    Decorator for optional authentication
    Sets user info if token is present, but doesn't require it
    
    Usage:
        @optional_auth
        def my_route():
            if hasattr(g, 'user_id'):
                # User is authenticated
                pass
            else:
                # Anonymous user
                pass
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization', '')
        
        if auth_header:
            try:
                # Extract token
                parts = auth_header.split()
                if len(parts) == 2 and parts[0].lower() == 'bearer':
                    token = parts[1]
                    
                    # Verify token
                    payload = JWTManager.decode_token(token)
                    
                    # Set user info in request context
                    g.user_id = payload['user_id']
                    g.username = payload['username']
                    g.user_role = payload['role']
            except:
                # Invalid token, but that's okay for optional auth
                pass
        
        return f(*args, **kwargs)
    
    return decorated
