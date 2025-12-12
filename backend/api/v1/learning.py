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
        "use_all_feedback": bool (optional, default: True),
        "is_incremental": bool (optional, default: False),
        "async_mode": bool (optional, default: from config)
    }
    
    Returns:
        200: Training successful or job enqueued
        400: Validation error
        401: Unauthorized
    """
    data = request.get_json()
    
    if not data or 'template_id' not in data:
        return APIResponse.bad_request("template_id is required")
    
    template_id = data['template_id']
    # ✅ Default to True for best accuracy and reliable grid search
    # Using False (only unused feedback) can result in small datasets
    use_all_feedback = data.get('use_all_feedback', True)
    # ✅ Incremental training: only use new feedback, faster training
    is_incremental = data.get('is_incremental', False)
    # ✅ Check if async mode is enabled (from request or config)
    async_mode = data.get('async_mode', current_app.config.get('ASYNC_AUTO_TRAINING', True))
    
    if async_mode:
        # ⚡ ASYNC MODE: Enqueue training job to background worker
        try:
            from database.repositories.job_repository import JobRepository
            from database.db_manager import DatabaseManager
            
            db = DatabaseManager()
            job_repo = JobRepository(db)
            model_folder = current_app.config['MODEL_FOLDER']
            
            # Check if there's already an active job
            if job_repo.has_active_auto_training_job(template_id):
                return APIResponse.bad_request(
                    f"Training job already active for template {template_id}"
                )
            
            # Enqueue manual training job
            job_id = job_repo.enqueue_manual_training_job(
                template_id=template_id,
                model_folder=model_folder,
                use_all_feedback=use_all_feedback,
                is_incremental=is_incremental
            )
            
            return APIResponse.success(
                {
                    'job_id': job_id,
                    'template_id': template_id,
                    'status': 'enqueued',
                    'mode': 'async'
                },
                f"Training job {job_id} enqueued successfully"
            )
            
        except Exception as e:
            current_app.logger.error(f"Failed to enqueue training job: {e}")
            return APIResponse.error(f"Failed to enqueue training job: {str(e)}")
    
    else:
        # 🔄 SYNC MODE: Run training immediately (blocking)
        service = get_model_service()
        
        try:
            result = service.retrain_model(
                template_id=template_id,
                use_all_feedback=use_all_feedback,
                model_folder=current_app.config['MODEL_FOLDER'],
                is_incremental=is_incremental
            )
            
            return APIResponse.success(
                {**result, 'mode': 'sync'},
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
    
    Query Parameters:
        - phase: Filter by experiment phase
            - 'baseline': Baseline experiment only
            - 'adaptive': Adaptive learning only
            - 'all': All documents (baseline + adaptive + production)
            - None (default): Production documents only
    
    Returns:
        200: Performance metrics including:
            - Overall accuracy
            - Field-level performance
            - Strategy distribution
            - Accuracy over time
            - Feedback statistics
        401: Unauthorized
    """
    from flask import request
    from database.db_manager import DatabaseManager
    from core.learning.metrics import PerformanceMetrics
    
    # Get optional phase filter
    experiment_phase = request.args.get('phase', None)
    
    # Validate phase value
    valid_phases = [None, 'baseline', 'adaptive', 'all']
    if experiment_phase not in valid_phases:
        return APIResponse.bad_request(
            f"Invalid phase. Must be one of: baseline, adaptive, all, or omit for production"
        )
    
    db = DatabaseManager()
    metrics_service = PerformanceMetrics(db)
    metrics = metrics_service.get_template_metrics(template_id, experiment_phase)
    
    return APIResponse.success(
        metrics,
        f"Performance metrics retrieved successfully (phase: {experiment_phase or 'production'})"
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
