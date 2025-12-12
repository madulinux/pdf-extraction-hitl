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
        template_folder=current_app.config['TEMPLATE_FOLDER'],
        model_folder=current_app.config['MODEL_FOLDER']
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


@templates_bp.route('/bulk', methods=['POST'])
@handle_errors
@require_auth
@require_role('admin', 'user')
def create_templates_bulk():
    """Analyze and create multiple templates in bulk.

    Request: multipart/form-data
    - files: Multiple PDF files
    - name_mode: (Optional) currently supports 'filename'
    - name_prefix: (Optional) prefix for generated template names

    Returns:
        201: Bulk template creation results
        400: Validation error
        401: Unauthorized
    """
    if 'files' not in request.files:
        return APIResponse.bad_request("No files provided")

    files = request.files.getlist('files')
    if not files or len(files) == 0:
        return APIResponse.bad_request("No files selected")

    # Validate all files are PDFs
    for file in files:
        if file.filename == '':
            return APIResponse.bad_request("Empty filename detected")
        if not file.filename.lower().endswith('.pdf'):
            return APIResponse.bad_request(f"File {file.filename} is not a PDF")

    name_mode = request.form.get('name_mode', 'filename')
    name_prefix = request.form.get('name_prefix', '')

    service = get_template_service()

    try:
        result = service.analyze_and_create_bulk(
            files=files,
            name_mode=name_mode,
            name_prefix=name_prefix,
        )

        return APIResponse.created(
            result,
            f"Bulk template upload completed: {result['successful']} successful, {result['failed']} failed"
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


@templates_bp.route('/<int:template_id>/fields/<field_name>/pattern', methods=['PATCH'])
@handle_errors
@require_auth
@require_role('admin', 'user')
def update_field_pattern(template_id, field_name):
    """
    Update base_pattern for a specific field
    
    Request JSON:
        {
            "base_pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
        }
    
    Returns:
        200: Pattern updated successfully
        400: Invalid pattern or validation error
        404: Template or field not found
        401: Unauthorized
    """
    data = request.get_json()
    
    if not data or 'base_pattern' not in data:
        return APIResponse.error("base_pattern is required", 400)
    
    base_pattern = data['base_pattern']
    
    # Allow NULL/empty to enable pure adaptive learning
    if base_pattern:
        # Validate and sanitize regex pattern
        is_valid, error_msg, sanitized = Validator.validate_regex_pattern(base_pattern, sanitize=True)
        
        if not is_valid:
            return APIResponse.error(error_msg, 400)
        
        base_pattern = sanitized
    else:
        # NULL pattern for pure adaptive learning
        base_pattern = None
    
    # Update field config in database
    from database.repositories.config_repository import ConfigRepository
    db = DatabaseManager()
    config_repo = ConfigRepository(db)
    
    try:
        # Get active config
        config = config_repo.get_active_config(template_id)
        if not config:
            return APIResponse.not_found(f"No active config found for template {template_id}")
        
        # Get field config
        field_cfg = config_repo.get_field_config_by_name(config['id'], field_name)
        if not field_cfg:
            return APIResponse.not_found(f"Field '{field_name}' not found in template {template_id}")
        
        # Update base_pattern
        config_repo.update_field_config(
            field_config_id=field_cfg['id'],
            base_pattern=base_pattern
        )
        
        return APIResponse.success(
            data={
                'template_id': template_id,
                'field_name': field_name,
                'base_pattern': base_pattern,
                'sanitized': base_pattern != data.get('base_pattern') if base_pattern else False
            },
            message="Field pattern updated successfully"
        )
    
    except Exception as e:
        return APIResponse.error(f"Failed to update pattern: {str(e)}", 500)


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
