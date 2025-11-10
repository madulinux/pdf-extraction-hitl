"""
Templates API Routes
Template management endpoints
"""
from flask import Blueprint, request, g, current_app

from core.templates.services import TemplateService
from database.repositories.template_repository import TemplateRepository
from utils.response import APIResponse
from utils.decorators import handle_errors
from api.middleware.auth import require_auth, require_role
from utils.validators import Validator
from shared.exceptions import ValidationError, NotFoundError
from database.db_manager import DatabaseManager
import os


# Create blueprint
templates_bp = Blueprint('templates', __name__, url_prefix='/api/v1/templates')

# Initialize service (will be done in app factory later)
def get_template_service():
    """Get template service instance"""
    db_path = os.getenv('DATABASE_PATH', 'data/app.db')
    db = DatabaseManager()
    repository = TemplateRepository(db)
    return TemplateService(
        repository=repository,
        upload_folder=current_app.config['UPLOAD_FOLDER'],
        template_folder=current_app.config['TEMPLATE_FOLDER']
    )


@templates_bp.route('', methods=['POST'])
@handle_errors
@require_auth
@require_role('admin', 'user')
def create_template():
    """
    Analyze and create a new template
    
    Request: multipart/form-data
    - file: PDF file
    - template_name: Template name
    
    Returns:
        201: Template created successfully
        400: Validation error
        401: Unauthorized
    """
    # Validate file
    if 'file' not in request.files:
        return APIResponse.bad_request("No file provided")
    
    file = request.files['file']
    
    if file.filename == '':
        return APIResponse.bad_request("No file selected")
    
    if not file.filename.lower().endswith('.pdf'):
        return APIResponse.bad_request("Only PDF files are allowed")
    
    # Get template name
    template_name = request.form.get('template_name', 'Unnamed Template')
    
    # Create template
    service = get_template_service()
    
    try:
        result = service.analyze_and_create(file, template_name)
        
        return APIResponse.created(
            result,
            f"Template analyzed successfully. Found {result['field_count']} fields."
        )
    
    except ValidationError as e:
        return APIResponse.bad_request(str(e))


@templates_bp.route('', methods=['GET'])
@handle_errors
@require_auth
def list_templates():
    """
    Get all templates
    
    Returns:
        200: List of templates
        401: Unauthorized
    """
    service = get_template_service()
    templates = service.get_all()
    
    return APIResponse.success(
        data={'templates': templates},
        message="Templates retrieved successfully",
        meta={'count': len(templates)}
    )

@templates_bp.route('/check/<template_name>', methods=['GET'])
@handle_errors
@require_auth
def check_template(template_name):
    """
    Check if template exists
    
    Returns:
        200: List of templates
        401: Unauthorized
    """
    service = get_template_service()
    templates = service.check_template(template_name)
    
    return APIResponse.success(
        data=templates,
        message="Templates retrieved successfully",
    )

@templates_bp.route('/<int:template_id>', methods=['GET'])
@handle_errors
@require_auth
def get_template(template_id):
    """
    Get template by ID
    
    Query params:
    - include_config: boolean (default: true)
    
    Returns:
        200: Template details
        404: Template not found
        401: Unauthorized
    """
    include_config = request.args.get('include_config', 'true').lower() == 'true'
    
    service = get_template_service()
    template = service.get_by_id(template_id, include_config=include_config)
    
    if not template:
        return APIResponse.not_found(f"Template with ID {template_id} not found")
    
    return APIResponse.success(
        data={'template': template},
        message="Template retrieved successfully"
    )


@templates_bp.route('/<int:template_id>', methods=['DELETE'])
@handle_errors
@require_auth
@require_role('admin')
def delete_template(template_id):
    """
    Delete a template (admin only)
    
    Returns:
        200: Template deleted
        404: Template not found
        401: Unauthorized
        403: Forbidden
    """
    service = get_template_service()
    success = service.delete(template_id)
    
    if not success:
        return APIResponse.not_found(f"Template with ID {template_id} not found")
    
    return APIResponse.success(
        data={'template_id': template_id},
        message="Template deleted successfully"
    )
