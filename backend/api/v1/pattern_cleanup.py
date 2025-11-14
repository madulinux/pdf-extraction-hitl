"""
Pattern Cleanup API

Provides endpoints for cleaning up duplicate patterns and managing pattern health.
"""

from flask import Blueprint, request, jsonify
from database.db_manager import DatabaseManager
from database.repositories.config_repository import ConfigRepository
from utils.response import APIResponse
from utils.decorators import handle_errors
from api.middleware.auth import require_auth
import logging

logger = logging.getLogger(__name__)

pattern_cleanup_bp = Blueprint('pattern_cleanup', __name__, url_prefix='/api/v1/patterns')


@pattern_cleanup_bp.route('/cleanup', methods=['POST'])
@handle_errors
@require_auth
def cleanup_duplicate_patterns():
    """
    Cleanup duplicate patterns
    
    POST /api/v1/patterns/cleanup
    {
        "field_config_id": 6  // Optional: specific field, or null for all
    }
    
    Returns:
        {
            "success": true,
            "data": {
                "patterns_merged": 10,
                "duplicates_deleted": 45
            }
        }
    """
    # Get JSON data if Content-Type is application/json, otherwise use empty dict
    data = request.get_json(silent=True) or {}
    field_config_id = data.get('field_config_id')
    
    db = DatabaseManager()
    config_repo = ConfigRepository(db)
    
    logger.info(f"🧹 Starting pattern cleanup for field_config_id={field_config_id or 'ALL'}")
    
    result = config_repo.cleanup_duplicate_patterns(field_config_id)
    
    if result['success']:
        return APIResponse.success(
            result,
            f"Cleaned up {result['duplicates_deleted']} duplicate patterns"
        )
    else:
        return APIResponse.error(
            result.get('error', 'Cleanup failed'),
            500
        )


@pattern_cleanup_bp.route('/deactivate-low-performing', methods=['POST'])
@handle_errors
@require_auth
def deactivate_low_performing():
    """
    Deactivate patterns with low performance
    
    POST /api/v1/patterns/deactivate-low-performing
    {
        "field_config_id": 6,
        "min_usage": 10,
        "min_match_rate": 0.3
    }
    
    Returns:
        {
            "success": true,
            "data": {
                "deactivated_count": 5
            }
        }
    """
    data = request.get_json()
    
    if not data or 'field_config_id' not in data:
        return APIResponse.error("field_config_id is required", 400)
    
    field_config_id = data['field_config_id']
    min_usage = data.get('min_usage', 10)
    min_match_rate = data.get('min_match_rate', 0.3)
    
    db = DatabaseManager()
    config_repo = ConfigRepository(db)
    
    logger.info(
        f"🗑️  Deactivating low-performing patterns: "
        f"field_config_id={field_config_id}, "
        f"min_usage={min_usage}, min_match_rate={min_match_rate}"
    )
    
    deactivated = config_repo.deactivate_low_performing_patterns(
        field_config_id=field_config_id,
        min_usage=min_usage,
        min_match_rate=min_match_rate
    )
    
    return APIResponse.success(
        {'deactivated_count': deactivated},
        f"Deactivated {deactivated} low-performing patterns"
    )


@pattern_cleanup_bp.route('/auto-cleanup', methods=['POST'])
@handle_errors
@require_auth
def auto_cleanup_patterns():
    """
    Automatically cleanup poorly performing patterns
    
    POST /api/v1/patterns/auto-cleanup
    {
        "template_id": 1,  // Optional
        "field_name": "kabupaten_daftar",  // Optional
        "dry_run": false  // Optional: preview without applying
    }
    
    Returns:
        {
            "success": true,
            "data": {
                "total_evaluated": 20,
                "deactivated": [...],
                "deleted": [...],
                "kept": [...]
            }
        }
    """
    data = request.get_json(silent=True) or {}
    template_id = data.get('template_id')
    field_name = data.get('field_name')
    dry_run = data.get('dry_run', False)
    
    db = DatabaseManager()
    
    logger.info(
        f"🧹 Auto-cleanup patterns: "
        f"template_id={template_id}, field_name={field_name}, dry_run={dry_run}"
    )
    
    try:
        from core.learning.pattern_cleaner import get_pattern_cleaner
        
        cleaner = get_pattern_cleaner(db)
        result = cleaner.cleanup_poor_patterns(
            template_id=template_id,
            field_name=field_name,
            dry_run=dry_run
        )
        
        if result.get('success') is False:
            return APIResponse.error(result.get('error', 'Cleanup failed'), 500)
        
        message = f"Evaluated {result['total_evaluated']} patterns"
        if not dry_run:
            message += f", deactivated {len(result['deactivated'])}, deleted {len(result['deleted'])}"
        else:
            message += " (dry run - no changes made)"
        
        return APIResponse.success(result, message)
        
    except Exception as e:
        logger.error(f"Auto-cleanup failed: {e}", exc_info=True)
        return APIResponse.error(str(e), 500)


@pattern_cleanup_bp.route('/cleanup-report', methods=['GET'])
@handle_errors
@require_auth
def get_cleanup_report():
    """
    Get report of patterns that need cleanup
    
    GET /api/v1/patterns/cleanup-report?template_id=1
    
    Returns:
        {
            "success": true,
            "data": {
                "total_patterns": 20,
                "needs_deactivation": 3,
                "needs_deletion": 1,
                "healthy": 16,
                "details": [...]
            }
        }
    """
    template_id = request.args.get('template_id', type=int)
    
    db = DatabaseManager()
    
    logger.info(f"📊 Getting cleanup report for template_id={template_id}")
    
    try:
        from core.learning.pattern_cleaner import get_pattern_cleaner
        
        cleaner = get_pattern_cleaner(db)
        report = cleaner.get_cleanup_report(template_id=template_id)
        
        return APIResponse.success(
            report,
            f"Found {report['needs_deactivation']} patterns needing deactivation, "
            f"{report['needs_deletion']} needing deletion"
        )
        
    except Exception as e:
        logger.error(f"Failed to get cleanup report: {e}", exc_info=True)
        return APIResponse.error(str(e), 500)


@pattern_cleanup_bp.route('/stats', methods=['GET'])
@handle_errors
@require_auth
def get_pattern_stats():
    """
    Get pattern statistics
    
    GET /api/v1/patterns/stats?template_id=1
    
    Returns:
        {
            "success": true,
            "data": {
                "total_patterns": 160,
                "unique_patterns": 50,
                "duplicate_patterns": 110,
                "active_patterns": 150,
                "inactive_patterns": 10,
                "patterns_with_usage": 20,
                "patterns_without_usage": 140
            }
        }
    """
    template_id = request.args.get('template_id', type=int)
    
    if not template_id:
        return APIResponse.error("template_id is required", 400)
    
    db = DatabaseManager()
    
    # Get statistics
    stats_query = """
        SELECT 
            COUNT(*) as total_patterns,
            COUNT(DISTINCT pattern || field_config_id) as unique_patterns,
            SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_patterns,
            SUM(CASE WHEN is_active = 0 THEN 1 ELSE 0 END) as inactive_patterns,
            SUM(CASE WHEN COALESCE(usage_count, 0) > 0 THEN 1 ELSE 0 END) as patterns_with_usage,
            SUM(CASE WHEN COALESCE(usage_count, 0) = 0 THEN 1 ELSE 0 END) as patterns_without_usage
        FROM learned_patterns lp
        JOIN field_configs fc ON lp.field_config_id = fc.id
        JOIN template_configs tc ON fc.config_id = tc.id
        WHERE tc.template_id = ?
    """
    
    stats = db.execute_query(stats_query, (template_id,))
    
    if stats and len(stats) > 0:
        result = dict(stats[0])
        result['duplicate_patterns'] = result['total_patterns'] - result['unique_patterns']
        
        return APIResponse.success(result, "Pattern statistics retrieved")
    else:
        return APIResponse.error("No patterns found", 404)


@pattern_cleanup_bp.route('/duplicates', methods=['GET'])
@handle_errors
@require_auth
def get_duplicate_patterns():
    """
    Get list of duplicate patterns
    
    GET /api/v1/patterns/duplicates?template_id=1
    
    Returns:
        {
            "success": true,
            "data": {
                "duplicates": [
                    {
                        "pattern": "\\d+\\s+[A-Z][a-z]+\\s+\\d+",
                        "field_name": "event_date",
                        "count": 4,
                        "ids": [144, 101, 48, 14],
                        "total_frequency": 54
                    }
                ]
            }
        }
    """
    template_id = request.args.get('template_id', type=int)
    
    if not template_id:
        return APIResponse.error("template_id is required", 400)
    
    db = DatabaseManager()
    
    duplicates_query = """
        SELECT 
            lp.pattern,
            fc.field_name,
            COUNT(*) as count,
            GROUP_CONCAT(lp.id) as ids,
            SUM(COALESCE(lp.frequency, 0)) as total_frequency,
            MAX(COALESCE(lp.priority, 0)) as max_priority
        FROM learned_patterns lp
        JOIN field_configs fc ON lp.field_config_id = fc.id
        JOIN template_configs tc ON fc.config_id = tc.id
        WHERE tc.template_id = ?
        GROUP BY lp.field_config_id, lp.pattern
        HAVING COUNT(*) > 1
        ORDER BY count DESC, total_frequency DESC
    """
    
    duplicates = db.execute_query(duplicates_query, (template_id,))
    
    # Convert to list of dicts
    result = []
    for dup in duplicates:
        result.append({
            'pattern': dup['pattern'],
            'field_name': dup['field_name'],
            'count': dup['count'],
            'ids': [int(x) for x in dup['ids'].split(',')],
            'total_frequency': dup['total_frequency'],
            'max_priority': dup['max_priority']
        })
    
    return APIResponse.success(
        {'duplicates': result},
        f"Found {len(result)} duplicate patterns"
    )
