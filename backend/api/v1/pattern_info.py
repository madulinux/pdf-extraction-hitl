"""
Pattern Information API (Refactored)

Clean architecture: Routes -> Service -> Repository
No direct database queries in routes!
"""
from flask import Blueprint
from utils.response import APIResponse
from utils.decorators import handle_errors
from api.middleware.auth import require_auth
from core.patterns.services import PatternService

pattern_info_bp = Blueprint('pattern_info', __name__, url_prefix='/api/v1/patterns')


@pattern_info_bp.route('/template/<int:template_id>', methods=['GET'])
@handle_errors
@require_auth
def get_template_patterns(template_id):
    """
    Get all patterns (base + learned) for a template
    
    Returns pattern information for each field:
    - Base pattern (from validation_rules or default)
    - Learned patterns (from database)
    - Pattern statistics (usage count, effectiveness)
    """
    service = PatternService()
    result = service.get_template_patterns(template_id)
    return APIResponse.success(result, "Pattern information retrieved successfully")


@pattern_info_bp.route('/field/<int:template_id>/<field_name>', methods=['GET'])
@handle_errors
@require_auth
def get_field_patterns(template_id, field_name):
    """
    Get detailed pattern information for a specific field
    
    Includes:
    - Current patterns
    - Pattern effectiveness
    - Learning history
    - Feedback examples
    """
    service = PatternService()
    result = service.get_field_patterns(template_id, field_name)
    return APIResponse.success(result, "Pattern information retrieved successfully")


@pattern_info_bp.route('/learning-jobs/<int:template_id>', methods=['GET'])
@handle_errors
@require_auth
def get_learning_jobs(template_id):
    """
    Get pattern learning job history for a template
    """
    service = PatternService()
    result = service.get_learning_jobs(template_id)
    return APIResponse.success(result, "Pattern learning job history retrieved successfully")
