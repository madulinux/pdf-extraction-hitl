"""
Learning API Routes
Adaptive learning and model training endpoints
"""
from flask import Blueprint, request, current_app

from core.learning import ModelService
from utils.response import APIResponse
from utils.decorators import handle_errors
from api.middleware.auth import require_auth, require_role
from shared.exceptions import ValidationError
import os


# Create blueprint
learning_bp = Blueprint('learning_v1', __name__, url_prefix='/api/v1/learning')


def get_model_service():
    """Get model service instance"""
    from database.db_manager import DatabaseManager
    return ModelService(DatabaseManager())


@learning_bp.route('/train', methods=['POST'])
@handle_errors
@require_auth
@require_role('admin', 'user')
def train_model():
    """
    Train/retrain CRF model using feedback
    
    Request Body:
    {
        "template_id": int,
        "use_all_feedback": bool (optional)
    }
    
    Returns:
        200: Training successful
        400: Validation error
        401: Unauthorized
    """
    data = request.get_json()
    
    if not data or 'template_id' not in data:
        return APIResponse.bad_request("template_id is required")
    
    template_id = data['template_id']
    use_all_feedback = data.get('use_all_feedback', False)
    
    service = get_model_service()
    
    try:
        result = service.retrain_model(
            template_id=template_id,
            use_all_feedback=use_all_feedback,
            model_folder=current_app.config['MODEL_FOLDER']
        )
        
        return APIResponse.success(
            result,
            "Model trained successfully"
        )
    
    except ValueError as e:
        return APIResponse.bad_request(str(e))


@learning_bp.route('/history/<int:template_id>', methods=['GET'])
@handle_errors
@require_auth
def get_training_history(template_id):
    """
    Get training history for a template
    
    Returns:
        200: Training history
        401: Unauthorized
    """
    service = get_model_service()
    history = service.get_training_history(template_id)
    
    return APIResponse.success(
        data={
            'template_id': template_id,
            'history': history
        },
        message="Training history retrieved successfully",
        meta={'count': len(history)}
    )


@learning_bp.route('/metrics/<int:template_id>', methods=['GET'])
@handle_errors
@require_auth
def get_model_metrics(template_id):
    """
    Get latest model metrics for a template
    
    Returns:
        200: Model metrics
        404: No training history found
        401: Unauthorized
    """
    service = get_model_service()
    metrics = service.get_latest_metrics(template_id)
    
    if not metrics:
        return APIResponse.not_found("No training history found for this template")
    
    return APIResponse.success(
        metrics,
        "Model metrics retrieved successfully"
    )


@learning_bp.route('/feedback-stats/<int:template_id>', methods=['GET'])
@handle_errors
@require_auth
def get_feedback_stats(template_id):
    """
    Get feedback statistics for a template
    
    Returns:
        200: Feedback statistics
        401: Unauthorized
    """
    service = get_model_service()
    stats = service.get_feedback_statistics(template_id)
    
    return APIResponse.success(
        stats,
        "Feedback statistics retrieved successfully"
    )


@learning_bp.route('/performance/<int:template_id>', methods=['GET'])
@handle_errors
@require_auth
def get_performance_metrics(template_id):
    """
    Get comprehensive performance metrics for a template
    
    Returns:
        200: Performance metrics including:
            - Overall accuracy
            - Field-level performance
            - Strategy distribution
            - Accuracy over time
            - Feedback statistics
        401: Unauthorized
    """
    from database.db_manager import DatabaseManager
    from core.learning.metrics import PerformanceMetrics
    
    db = DatabaseManager()
    metrics_service = PerformanceMetrics(db)
    metrics = metrics_service.get_template_metrics(template_id)
    
    return APIResponse.success(
        metrics,
        "Performance metrics retrieved successfully"
    )


@learning_bp.route('/validate-check', methods=['POST'])
@handle_errors
@require_auth
def check_validation_needed():
    """
    Active Learning: Check if document needs validation
    
    Request Body:
    {
        "extraction_result": {...},
        "threshold": 0.7 (optional)
    }
    
    Returns:
        200: Validation recommendation
        400: Validation error
        401: Unauthorized
    """
    from core.learning.metrics import PerformanceMetrics
    from database.db_manager import DatabaseManager
    
    data = request.get_json()
    
    if not data or 'extraction_result' not in data:
        return APIResponse.bad_request("extraction_result is required")
    
    extraction_result = data['extraction_result']
    threshold = data.get('threshold', 0.7)
    
    db = DatabaseManager()
    metrics_service = PerformanceMetrics(db)
    
    should_validate, reason = metrics_service.should_request_validation(
        extraction_result,
        threshold
    )
    
    return APIResponse.success({
        'should_validate': should_validate,
        'reason': reason,
        'threshold': threshold
    })
