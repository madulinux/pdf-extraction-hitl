"""
Patterns API Routes
Pattern learning endpoints
"""
from flask import Blueprint, request, g

from core.patterns import PatternManager
from utils.response import APIResponse
from utils.decorators import handle_errors
from api.middleware.auth import require_auth, optional_auth


# Create blueprint
patterns_bp = Blueprint('patterns_v1', __name__, url_prefix='/api/v1/patterns')

# Initialize pattern manager
pattern_manager = PatternManager()


@patterns_bp.route('/learn', methods=['POST'])
@handle_errors
@optional_auth
def learn_pattern():
    """
    Learn a new pattern for a field
    
    Request Body:
    {
        "field_name": string,
        "regex_pattern": string,
        "user_id": int (optional, from auth)
    }
    
    Returns:
        201: Pattern learned
        400: Validation error
    """
    data = request.get_json()
    
    if not data:
        return APIResponse.bad_request("Request body is required")
    
    if 'field_name' not in data or 'regex_pattern' not in data:
        return APIResponse.bad_request("field_name and regex_pattern are required")
    
    # Get user_id from auth if available
    user_id = getattr(g, 'user_id', None) or data.get('user_id')
    
    result = pattern_manager.learn_pattern(
        field_name=data['field_name'],
        regex_pattern=data['regex_pattern'],
        user_id=user_id
    )
    
    return APIResponse.created(
        result,
        "Pattern learned successfully"
    )


@patterns_bp.route('/field/<field_name>', methods=['GET'])
@handle_errors
@optional_auth
def get_field_pattern(field_name):
    """
    Get pattern for a specific field
    
    Returns:
        200: Pattern found
        404: Pattern not found
    """
    # Get user_id from auth if available
    user_id = getattr(g, 'user_id', None)
    
    pattern = pattern_manager.get_pattern_for_field(field_name, user_id)
    
    if not pattern:
        return APIResponse.not_found(f"No pattern found for field '{field_name}'")
    
    return APIResponse.success(
        data={'field_name': field_name, 'pattern': pattern},
        message="Pattern retrieved successfully"
    )


@patterns_bp.route('/all', methods=['GET'])
@handle_errors
@optional_auth
def get_all_patterns():
    """
    Get all patterns
    
    Returns:
        200: All patterns
    """
    # Get user_id from auth if available
    user_id = getattr(g, 'user_id', None)
    
    patterns = pattern_manager.get_all_patterns(user_id)
    
    return APIResponse.success(
        data={'patterns': patterns},
        message="Patterns retrieved successfully",
        meta={'count': len(patterns)}
    )


@patterns_bp.route('/validate', methods=['POST'])
@handle_errors
def validate_pattern():
    """
    Validate a regex pattern
    
    Request Body:
    {
        "regex_pattern": string,
        "test_string": string
    }
    
    Returns:
        200: Validation result
        400: Invalid request
    """
    data = request.get_json()
    
    if not data or 'regex_pattern' not in data or 'test_string' not in data:
        return APIResponse.bad_request("regex_pattern and test_string are required")
    
    is_valid, result = pattern_manager.validate_pattern(
        data['regex_pattern'],
        data['test_string']
    )
    
    return APIResponse.success(
        data={
            'is_valid': is_valid,
            'matches': result if is_valid else None,
            'error': result if not is_valid else None
        },
        message="Pattern validated"
    )
