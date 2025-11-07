"""
Preview API Routes
Template preview generation endpoints
"""
from flask import Blueprint, request, send_file, current_app

from core.preview import PreviewService
from utils.response import APIResponse
from utils.decorators import handle_errors
from api.middleware.auth import require_auth
import os


# Create blueprint
preview_bp = Blueprint('preview_v1', __name__, url_prefix='/api/v1/preview')


def get_preview_service():
    """Get preview service instance"""
    from database.db_manager import DatabaseManager
    return PreviewService(DatabaseManager())


@preview_bp.route('/template/<int:template_id>', methods=['GET'])
@handle_errors
@require_auth
def get_template_preview(template_id):
    """
    Generate preview image for template
    
    Query params:
    - highlight_field: Field name to highlight (optional)
    - page: Page number to preview (optional, default: 1)
    
    Returns:
        200: Preview image (PNG)
        404: Template not found
        401: Unauthorized
    """
    highlight_field = request.args.get('highlight_field')
    page_number = request.args.get('page', 1, type=int)
    
    service = get_preview_service()
    
    try:
        preview_path = service.generate_preview(
            template_id=template_id,
            highlight_field=highlight_field,
            upload_folder=current_app.config['UPLOAD_FOLDER'],
            template_folder=current_app.config['TEMPLATE_FOLDER'],
            preview_folder=current_app.config.get('PREVIEW_FOLDER', 'previews'),
            page_number=page_number
        )
        
        return send_file(preview_path, mimetype='image/png')
    
    except ValueError as e:
        return APIResponse.not_found(str(e))
    except FileNotFoundError as e:
        return APIResponse.not_found(str(e))


@preview_bp.route('/config/<int:template_id>', methods=['GET'])
@handle_errors
@require_auth
def get_template_config(template_id):
    """
    Get template configuration
    
    Returns:
        200: Template configuration
        404: Template not found
        401: Unauthorized
    """
    service = get_preview_service()
    
    try:
        config = service.get_template_config(
            template_id=template_id,
            template_folder=current_app.config['TEMPLATE_FOLDER']
        )
        
        return APIResponse.success(
            config,
            "Template configuration retrieved successfully"
        )
    
    except ValueError as e:
        return APIResponse.not_found(str(e))
    except FileNotFoundError as e:
        return APIResponse.not_found(str(e))


@preview_bp.route('/pages/<int:template_id>', methods=['GET'])
@handle_errors
@require_auth
def get_template_pages(template_id):
    """
    Get total number of pages in template PDF
    
    Returns:
        200: Page count
        404: Template not found
        401: Unauthorized
    """
    service = get_preview_service()
    
    try:
        page_count = service.get_pdf_page_count(
            template_id=template_id,
            upload_folder=current_app.config['UPLOAD_FOLDER']
        )
        
        return APIResponse.success(
            {'template_id': template_id, 'total_pages': page_count},
            "Page count retrieved successfully"
        )
    
    except ValueError as e:
        return APIResponse.not_found(str(e))
    except FileNotFoundError as e:
        return APIResponse.not_found(str(e))
