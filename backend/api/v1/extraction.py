"""
Extraction API Routes
Document extraction endpoints (using core services)
"""

from flask import Blueprint, request, current_app

from core.extraction.services import ExtractionService
from database.repositories.document_repository import DocumentRepository
from database.repositories.feedback_repository import FeedbackRepository
from database.repositories.template_repository import TemplateRepository
from database.repositories.training_repository import TrainingRepository
from utils.response import APIResponse
from utils.decorators import handle_errors
from api.middleware.auth import require_auth
from shared.exceptions import ValidationError, NotFoundError
from database.db_manager import DatabaseManager
import os


# Create blueprint
extraction_bp = Blueprint("extraction_v1", __name__, url_prefix="/api/v1/extraction")


def get_extraction_service():
    """Get extraction service instance"""
    db_path = os.getenv("DATABASE_PATH", "data/app.db")
    db = DatabaseManager()
    document_repo = DocumentRepository(db)
    feedback_repo = FeedbackRepository(db)
    template_repo = TemplateRepository(db)
    training_repo = TrainingRepository(db)
    return ExtractionService(
        document_repo=document_repo,
        feedback_repo=feedback_repo,
        template_repo=template_repo,
        training_repo=training_repo,
        upload_folder=current_app.config["UPLOAD_FOLDER"],
        model_folder=current_app.config["MODEL_FOLDER"],
        feedback_folder=current_app.config["FEEDBACK_FOLDER"],
    )


@extraction_bp.route("/extract", methods=["POST"])
@handle_errors
@require_auth
def extract_document():
    """
    Extract data from filled PDF document

    Request: multipart/form-data
    - file: PDF file
    - template_id: Template ID

    Returns:
        200: Extraction successful
        400: Validation error
        401: Unauthorized
    """
    # Validate file
    if "file" not in request.files:
        return APIResponse.bad_request("No file provided")

    file = request.files["file"]
    template_id = request.form.get("template_id")

    if not template_id:
        return APIResponse.bad_request("Template ID is required")

    if file.filename == "":
        return APIResponse.bad_request("No file selected")

    if not file.filename.lower().endswith(".pdf"):
        return APIResponse.bad_request("Only PDF files are allowed")

    # Extract document (config will be loaded from DB or JSON automatically)
    service = get_extraction_service()
    template = service.template_repo.find_by_id(int(template_id))

    if not template:
        return APIResponse.not_found(f"Template with ID {template_id} not found")

    try:
        result = service.extract_document(
            file=file,
            template_id=int(template_id),
            template_config_path=template.config_path,
        )

        return APIResponse.success(result, "Data extracted successfully")

    except NotFoundError as e:
        return APIResponse.not_found(str(e))
    except Exception as e:
        return APIResponse.internal_error(f"Extraction failed: {str(e)}")


@extraction_bp.route("/validate", methods=["POST"])
@handle_errors
@require_auth
def validate_corrections():
    """
    Save user corrections as feedback and trigger adaptive learning

    Request Body:
    {
        "document_id": int,
        "corrections": {...}
    }

    Returns:
        200: Corrections saved
        400: Validation error
        401: Unauthorized
    """
    data = request.get_json()

    if not data:
        return APIResponse.bad_request("Request body is required")

    if "document_id" not in data or "corrections" not in data:
        return APIResponse.bad_request("document_id and corrections are required")

    service = get_extraction_service()

    try:
        # Save corrections (returns all_fields + corrected_fields)
        result = service.save_corrections(
            document_id=data["document_id"], corrections=data["corrections"]
        )

        # ✨ NEW: Trigger adaptive pattern learning via service layer
        # ✅ GOOD: Uses clean architecture (Route -> Service -> Repository)
        # ✅ GOOD: Learns from ALL fields (corrected + validated)
        try:
            from core.learning.services import ModelService

            learning_service = ModelService()
            learning_result = learning_service.trigger_adaptive_learning(
                document_id=data["document_id"],
                all_fields=result.get("all_fields", {}),  # ✅ All extracted fields
                corrected_fields=result.get(
                    "corrected_fields", {}
                ),  # ✅ Only corrected
            )

            # Add learning info to response
            result["learning"] = learning_result

        except Exception as e:
            # Don't fail the request if auto-learning fails
            current_app.logger.warning(f"Auto-learning trigger failed: {e}")
            result["learning"] = {"success": False, "error": str(e)}
        
        # 🤖 AUTO-TRAINING: Check if model should be retrained automatically
        try:
            from core.learning.auto_trainer import get_auto_training_service
            from database.repositories.document_repository import DocumentRepository
            from database.db_manager import DatabaseManager
            
            # Get template_id from document
            db = DatabaseManager()
            doc_repo = DocumentRepository(db)
            document = doc_repo.find_by_id(data["document_id"])
            
            if document:
                template_id = document.template_id
                auto_trainer = get_auto_training_service()
                
                # Check and trigger auto-training if conditions are met
                training_result = auto_trainer.check_and_train(
                    template_id=template_id,
                    model_folder=current_app.config['MODEL_FOLDER']
                )
                
                if training_result:
                    result["auto_training"] = {
                        "triggered": True,
                        "accuracy": training_result['test_metrics']['accuracy'],
                        "samples": training_result['training_samples']
                    }
                    current_app.logger.info(f"Auto-training triggered for template {template_id}")
                else:
                    result["auto_training"] = {"triggered": False}
                    
        except Exception as e:
            # Don't fail the request if auto-training fails
            current_app.logger.warning(f"Auto-training check failed: {e}")
            result["auto_training"] = {"triggered": False, "error": str(e)}

        return APIResponse.success(result, "Corrections saved successfully")

    except NotFoundError as e:
        return APIResponse.not_found(str(e))


@extraction_bp.route("/documents", methods=["GET"])
@handle_errors
@require_auth
def list_documents():
    """
    Get all documents

    Returns:
        200: List of documents
        401: Unauthorized
    """

    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 10, type=int)
    search = request.args.get("search", None)
    template_id = request.args.get("template_id", None)

    service = get_extraction_service()
    documents, meta = service.get_all_documents(page, page_size, search, template_id)

    return APIResponse.success(
        data={"documents": documents},
        message="Documents retrieved successfully",
        meta=meta,
    )


@extraction_bp.route("/documents/<int:document_id>", methods=["GET"])
@handle_errors
@require_auth
def get_document(document_id):
    """
    Get document by ID

    Returns:
        200: Document details
        404: Document not found
        401: Unauthorized
    """
    service = get_extraction_service()
    document = service.get_document_by_id(document_id)

    if not document:
        return APIResponse.not_found(f"Document with ID {document_id} not found")

    return APIResponse.success(
        data={"document": document}, message="Document retrieved successfully"
    )


@extraction_bp.route("/documents/<int:document_id>/preview", methods=["GET"])
@handle_errors
@require_auth
def preview_document(document_id):
    """
    Get document PDF for preview

    Returns:
        200: PDF file
        404: Document not found
        401: Unauthorized
    """
    from flask import send_file

    service = get_extraction_service()
    document = service.get_document_by_id(document_id)

    if not document:
        return APIResponse.not_found(f"Document with ID {document_id} not found")

    file_path = document.get("file_path")
    if not file_path or not os.path.exists(file_path):
        return APIResponse.not_found("Document file not found")

    return send_file(
        file_path,
        mimetype="application/pdf",
        as_attachment=False,
        download_name=document.get("filename", "document.pdf"),
    )
