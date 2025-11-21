# Document processing module

import logging

# Configure logging
logger = logging.getLogger("docservice.processor")

# Import all public functions
from .variable_extractor import extract_variables_from_template
from .template_processor import process_template, process_image_variables
from .pdf_converter import convert_docx_to_pdf
from .html_converter import docx_to_html
from .utils import suggest_variable_type

# Export all public functions
__all__ = [
    'extract_variables_from_template',
    'process_template',
    'process_image_variables',
    'convert_docx_to_pdf',
    'docx_to_html',
    'suggest_variable_type'
]
