"""
Extraction API Routes
Document extraction endpoints (using core services)
"""
from flask import Blueprint, request, current_app

from core.extraction.services import ExtractionService
from core.extraction.repositories import DocumentRepository, FeedbackRepository
from utils.response import APIResponse
from utils.decorators import handle_errors
from api.middleware.auth import require_auth
from shared.exceptions import ValidationError, NotFoundError
import os


# Create blueprint
extraction_bp = Blueprint('extraction_v1', __name__, url_prefix='/api/v1/extraction')


def get_extraction_service():
    """Get extraction service instance"""
    db_path = os.getenv('DATABASE_PATH', 'data/app.db')
    document_repo = DocumentRepository(db_path)
    feedback_repo = FeedbackRepository(db_path)
    
    return ExtractionService(
        document_repo=document_repo,
        feedback_repo=feedback_repo,
        upload_folder=current_app.config['UPLOAD_FOLDER'],
        model_folder=current_app.config['MODEL_FOLDER'],
        feedback_folder=current_app.config['FEEDBACK_FOLDER']
    )


@extraction_bp.route('/extract', methods=['POST'])
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
    if 'file' not in request.files:
        return APIResponse.bad_request("No file provided")
    
    file = request.files['file']
    template_id = request.form.get('template_id')
    
    if not template_id:
        return APIResponse.bad_request("Template ID is required")
    
    if file.filename == '':
        return APIResponse.bad_request("No file selected")
    
    if not file.filename.lower().endswith('.pdf'):
        return APIResponse.bad_request("Only PDF files are allowed")
    
    # Get template config path
    from database.db_manager import DatabaseManager
    db = DatabaseManager()
    template = db.get_template(int(template_id))
    
    if not template:
        return APIResponse.not_found(f"Template with ID {template_id} not found")
    
    # Extract document
    service = get_extraction_service()
    
    try:
        result = service.extract_document(
            file=file,
            template_id=int(template_id),
            template_config_path=template['config_path']
        )
        
        return APIResponse.success(
            result,
            "Data extracted successfully"
        )
    
    except NotFoundError as e:
        return APIResponse.not_found(str(e))
    except Exception as e:
        return APIResponse.internal_error(f"Extraction failed: {str(e)}")


@extraction_bp.route('/validate', methods=['POST'])
@handle_errors
@require_auth
def validate_corrections():
    """
    Save user corrections as feedback
    
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
    
    if 'document_id' not in data or 'corrections' not in data:
        return APIResponse.bad_request("document_id and corrections are required")
    
    service = get_extraction_service()
    
    try:
        result = service.save_corrections(
            document_id=data['document_id'],
            corrections=data['corrections']
        )
        
        return APIResponse.success(
            result,
            "Corrections saved successfully"
        )
    
    except NotFoundError as e:
        return APIResponse.not_found(str(e))


@extraction_bp.route('/documents', methods=['GET'])
@handle_errors
@require_auth
def list_documents():
    """
    Get all documents
    
    Returns:
        200: List of documents
        401: Unauthorized
    """
    service = get_extraction_service()
    documents = service.get_all_documents()
    
    return APIResponse.success(
        data={'documents': documents},
        message="Documents retrieved successfully",
        meta={'count': len(documents)}
    )


@extraction_bp.route('/documents/<int:document_id>', methods=['GET'])
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
        data={'document': document},
        message="Document retrieved successfully"
    )


@extraction_bp.route('/documents/<int:document_id>/preview', methods=['GET'])
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
    
    file_path = document.get('file_path')
    if not file_path or not os.path.exists(file_path):
        return APIResponse.not_found("Document file not found")
    
    return send_file(
        file_path,
        mimetype='application/pdf',
        as_attachment=False,
        download_name=document.get('filename', 'document.pdf')
    )
