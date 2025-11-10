"""
Data Quality API Endpoints

Provides endpoints for checking and retrieving data quality metrics.
"""

from flask import Blueprint, request, jsonify
from database.db_manager import DatabaseManager
from database.repositories.data_quality_repository import DataQualityRepository
from core.learning.training_utils import (
    validate_training_data_diversity,
    detect_data_leakage,
    get_training_recommendations,
)
import time
import json
from utils.response import APIResponse
from utils.decorators import handle_errors
from api.middleware.auth import require_auth
from shared.exceptions import ValidationError, NotFoundError
from database.repositories.template_repository import TemplateRepository

data_quality_bp = Blueprint("data_quality", __name__, url_prefix="/api/v1")
db = DatabaseManager()


@data_quality_bp.route(
    "/templates/<int:template_id>/data-quality/latest", methods=["GET"]
)
@require_auth
@handle_errors
def get_latest_metrics(template_id: int):
    """
    Get latest data quality metrics for a template

    GET /api/v1/templates/1/data-quality/latest
    """
    try:
        dq_repo = DataQualityRepository(db)
        metrics = dq_repo.get_latest_by_template(template_id)

        if not metrics:
            return NotFoundError(
                "No data quality metrics found for this template", template_id
            )

        return APIResponse.success(
            {"data": metrics, "meta": {"template_id": template_id}}
        )

    except Exception as e:
        return APIResponse.error(str(e))


@data_quality_bp.route(
    "/templates/<int:template_id>/data-quality/history", methods=["GET"]
)
@require_auth
@handle_errors
def get_metrics_history(template_id: int):
    """
    Get history of data quality metrics for a template

    GET /api/v1/templates/1/data-quality/history?limit=10
    """
    try:
        limit = request.args.get("limit", 10, type=int)

        dq_repo = DataQualityRepository(db)
        metrics_list = dq_repo.get_all_by_template(template_id, limit=limit)

        return APIResponse.success(
            {
                "data": metrics_list,
                "meta": {"template_id": template_id, "count": len(metrics_list)},
            }
        )

    except Exception as e:
        return APIResponse.error(str(e))


@data_quality_bp.route("/data-quality/summary", methods=["GET"])
@require_auth
@handle_errors
def get_all_templates_summary():
    """
    Get summary of latest metrics for all templates

    GET /api/v1/data-quality/summary
    """
    try:
        dq_repo = DataQualityRepository(db)
        summaries = dq_repo.get_all_templates_summary()

        return APIResponse.success(
            {"data": summaries, "meta": {"count": len(summaries)}}
        )

    except Exception as e:
        return APIResponse.error(str(e))


@data_quality_bp.route(
    "/templates/<int:template_id>/data-quality/check", methods=["POST"]
)
@require_auth
@handle_errors
def check_data_quality(template_id: int):
    """
    On-demand data quality check for a template

    POST /api/v1/templates/1/data-quality/check
    Body: {
        "check_leakage": true,  // optional, default true
        "check_diversity": true,  // optional, default true
        "save_to_db": true  // optional, default true
    }
    """

    try:
        data = request.get_json() or {}
        check_leakage = data.get("check_leakage", True)
        check_diversity = data.get("check_diversity", True)
        save_to_db = data.get("save_to_db", True)

        # Get template

        template_repo = TemplateRepository(db)
        template = template_repo.find_by_id(template_id)
        if not template:
            return NotFoundError(f"Template with ID {template_id} not found")

        # Load template config from database or JSON
        from core.templates.config_loader import get_config_loader

        config_loader = get_config_loader(db_manager=db)
        config = config_loader.load_config(
            template_id=template_id, config_path=template.config_path
        )

        if not config:
            return NotFoundError(
                f"Failed to load configuration for template {template_id}"
            )

        # Prepare training data (reuse logic from retrain_model)
        from core.learning.data_preparation import prepare_training_data_from_feedback
        from database.repositories.feedback_repository import FeedbackRepository
        from database.repositories.document_repository import DocumentRepository
        
        feedback_repo = FeedbackRepository(db)
        document_repo = DocumentRepository(db)

        feedback_by_doc = feedback_repo.find_by_document_id(template_id)
        validated_docs = document_repo.find_validated_documents(template_id)

        print(f"📊 Preparing data for quality check...")
        print(f"   Feedback documents: {len(feedback_by_doc)}")
        print(f"   Validated documents: {len(validated_docs)}")

        X_train, y_train = prepare_training_data_from_feedback(
            feedback_by_doc=feedback_by_doc,
            validated_documents=validated_docs,
            template_config=config,
        )

        if len(X_train) == 0:
            return ValidationError(
                "No training data available for quality check", template_id
            )

        print(f"   Total training samples: {len(X_train)}")

        # Initialize results
        diversity_metrics = {}
        leakage_results = {"leakage_detected": False}
        validation_start_time = time.time()

        # Check diversity
        if check_diversity:
            print(f"\n🔍 Checking diversity...")
            diversity_metrics = validate_training_data_diversity(X_train, y_train)

        # Check leakage
        if check_leakage:
            print(f"\n🔍 Checking data leakage...")
            from core.learning.training_utils import split_training_data

            X_train_split, X_test_split, _, _ = split_training_data(
                X_train, y_train, test_size=0.2, random_state=42
            )
            leakage_results = detect_data_leakage(X_train_split, X_test_split)

        # Get recommendations
        recommendations = get_training_recommendations(
            num_samples=len(X_train),
            diversity_score=diversity_metrics.get("diversity_score", 0.5),
            has_leakage=leakage_results.get("leakage_detected", False),
        )

        validation_duration = time.time() - validation_start_time

        # Save to database if requested
        metric_id = None
        if save_to_db:
            dq_repo = DataQualityRepository(db)
            metric_id = dq_repo.save_metrics(
                template_id=template_id,
                validation_type="on_demand",
                total_samples=len(X_train),
                diversity_metrics=diversity_metrics,
                leakage_results=leakage_results,
                recommendations=recommendations,
                validation_duration=validation_duration,
                triggered_by="api",
                notes="On-demand quality check via API",
            )
            print(f"   💾 Metrics saved to database (ID: {metric_id})")

        return APIResponse.success(
            {
                "data": {
                    "template_id": template_id,
                    "metric_id": metric_id,
                    "validation_duration_seconds": validation_duration,
                    "results": {
                        "total_samples": len(X_train),
                        "diversity_metrics": diversity_metrics,
                        "leakage_results": leakage_results,
                        "recommendations": recommendations,
                    },
                }
            }
        )

    except Exception as e:
        import traceback

        traceback.print_exc()
        return APIResponse.error(str(e))
