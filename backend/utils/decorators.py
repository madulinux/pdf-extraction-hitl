"""
Custom Decorators for Route Handlers
Centralized error handling and validation
"""
from functools import wraps
from flask import request
from utils.response import APIResponse
from utils.validators import Validator

def handle_errors(f):
    """
    Decorator for consistent error handling
    Catches exceptions and returns standardized error responses
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except FileNotFoundError as e:
            return APIResponse.not_found(str(e))
        except ValueError as e:
            return APIResponse.bad_request(str(e))
        except Exception as e:
            print(f"Unexpected error in {f.__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            return APIResponse.internal_error(f"An unexpected error occurred: {str(e)}")
    
    return decorated_function

def validate_file_upload(allowed_extensions=None):
    """
    Decorator to validate file uploads
    
    Args:
        allowed_extensions: Set of allowed file extensions
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'file' not in request.files:
                return APIResponse.bad_request("No file part in request")
            
            file = request.files['file']
            is_valid, error_msg = Validator.validate_file(file, allowed_extensions)
            
            if not is_valid:
                return APIResponse.bad_request(error_msg)
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def validate_json_fields(required_fields):
    """
    Decorator to validate required JSON fields
    
    Args:
        required_fields: List of required field names
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return APIResponse.bad_request("Request must be JSON")
            
            data = request.get_json()
            is_valid, errors = Validator.validate_required_fields(data, required_fields)
            
            if not is_valid:
                return APIResponse.bad_request("Validation failed", errors)
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator
