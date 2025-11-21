import logging

# Configure logging
logger = logging.getLogger("docservice")

# Re-export all functions from the new modules
from utils.document import (
    extract_variables_from_template,
    process_template,
    process_image_variables,
    convert_docx_to_pdf,
    docx_to_html,
    suggest_variable_type
)

# This file now only re-exports functions from the document module
# All implementations have been moved to the document/ directory
