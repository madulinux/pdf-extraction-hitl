"""
Standardized API Response Utilities
Ensures consistent response format across all endpoints
"""
from flask import jsonify
from typing import Any, Optional, Dict
from datetime import datetime

class APIResponse:
    """Standardized API response builder"""
    
    @staticmethod
    def success(data: Any = None, message: str = "Success", meta: Optional[Dict] = None, status_code: int = 200):
        """
        Success response format
        
        Args:
            data: Response data
            message: Success message
            meta: Additional metadata (pagination, etc)
            status_code: HTTP status code
            
        Returns:
            Flask JSON response
        """
        response = {
            'success': True,
            'message': message,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        
        if meta:
            response['meta'] = meta
        
        return jsonify(response), status_code
    
    @staticmethod
    def error(message: str, errors: Optional[Dict] = None, status_code: int = 400):
        """
        Error response format
        
        Args:
            message: Error message
            errors: Detailed error information
            status_code: HTTP status code
            
        Returns:
            Flask JSON response
        """
        response = {
            'success': False,
            'message': message,
            'data': None,
            'timestamp': datetime.now().isoformat()
        }
        
        if errors:
            response['errors'] = errors
        
        return jsonify(response), status_code
    
    @staticmethod
    def created(data: Any, message: str = "Resource created successfully", status_code: int = 201):
        """Created response (201)"""
        return APIResponse.success(data, message, status_code=status_code)
    
    @staticmethod
    def not_found(message: str = "Resource not found"):
        """Not found response (404)"""
        return APIResponse.error(message, status_code=404)
    
    @staticmethod
    def bad_request(message: str = "Bad request", errors: Optional[Dict] = None):
        """Bad request response (400)"""
        return APIResponse.error(message, errors, status_code=400)
    
    @staticmethod
    def internal_error(message: str = "Internal server error", errors: Optional[Dict] = None):
        """Internal server error response (500)"""
        return APIResponse.error(message, errors, status_code=500)
    
    @staticmethod
    def unauthorized(message: str = "Unauthorized"):
        """Unauthorized response (401)"""
        return APIResponse.error(message, status_code=401)
    
    @staticmethod
    def forbidden(message: str = "Forbidden"):
        """Forbidden response (403)"""
        return APIResponse.error(message, status_code=403)
