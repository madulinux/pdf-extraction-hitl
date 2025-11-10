"""
Pattern Statistics API

Provides endpoints for managing pattern statistics (prefix/suffix/noise learning).
"""

from flask import Blueprint, request, jsonify
from database.db_manager import DatabaseManager
from database.repositories.config_repository import ConfigRepository
from utils.response import APIResponse
from utils.decorators import handle_errors
from api.middleware.auth import require_auth
import logging

logger = logging.getLogger(__name__)

pattern_statistics_bp = Blueprint('pattern_statistics', __name__, url_prefix='/api/v1/pattern-statistics')


@pattern_statistics_bp.route('/analyze/<int:template_id>', methods=['POST'])
@handle_errors
@require_auth
def analyze_and_update(template_id: int):
    """
    Analyze feedback and update pattern statistics
    
    POST /api/v1/pattern-statistics/analyze/1
    {
        "min_frequency_threshold": 3  // Optional
    }
    
    Returns:
        {
            "success": true,
            "data": {
                "updates": 15,
                "fields_analyzed": 5
            }
        }
    """
    data = request.get_json(silent=True) or {}
    min_frequency = data.get('min_frequency_threshold', 3)
    
    db = DatabaseManager()
    config_repo = ConfigRepository(db)
    
    logger.info(f"🔍 Analyzing pattern statistics for template {template_id}")
    
    result = config_repo.analyze_and_update_pattern_statistics(
        template_id=template_id,
        min_frequency_threshold=min_frequency
    )
    
    if result['success']:
        return APIResponse.success(
            result,
            result.get('message', 'Pattern statistics updated')
        )
    else:
        return APIResponse.error(
            result.get('error', 'Analysis failed'),
            500
        )


@pattern_statistics_bp.route('/template/<int:template_id>', methods=['GET'])
@handle_errors
@require_auth
def get_template_statistics(template_id: int):
    """
    Get all pattern statistics for a template
    
    GET /api/v1/pattern-statistics/template/1
    
    Returns:
        {
            "success": true,
            "data": {
                "event_date": {
                    "common_prefixes": ["tanggal"],
                    "common_suffixes": [],
                    "structural_noise": {"has_trailing_comma": 5},
                    "sample_count": 180
                },
                ...
            }
        }
    """
    db = DatabaseManager()
    config_repo = ConfigRepository(db)
    
    statistics = config_repo.get_all_pattern_statistics(
        template_id=template_id,
        active_only=True
    )
    
    return APIResponse.success(
        statistics,
        f"Pattern statistics for template {template_id}"
    )


@pattern_statistics_bp.route('/field/<int:field_config_id>', methods=['GET'])
@handle_errors
@require_auth
def get_field_statistics(field_config_id: int):
    """
    Get pattern statistics for a specific field
    
    GET /api/v1/pattern-statistics/field/6?type=prefix&min_frequency=3
    
    Query params:
        type: Filter by statistic_type (prefix, suffix, structural_noise)
        min_frequency: Minimum frequency threshold
    
    Returns:
        {
            "success": true,
            "data": [
                {
                    "statistic_type": "prefix",
                    "pattern_value": "tanggal",
                    "frequency": 15,
                    "confidence": 0.85,
                    "sample_count": 180
                }
            ]
        }
    """
    statistic_type = request.args.get('type')
    min_frequency = request.args.get('min_frequency', type=int, default=2)
    
    db = DatabaseManager()
    config_repo = ConfigRepository(db)
    
    statistics = config_repo.get_pattern_statistics(
        field_config_id=field_config_id,
        statistic_type=statistic_type,
        active_only=True,
        min_frequency=min_frequency
    )
    
    return APIResponse.success(
        statistics,
        f"Pattern statistics for field {field_config_id}"
    )
