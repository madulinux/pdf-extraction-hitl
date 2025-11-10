"""
Extraction Domain
Document extraction and validation
"""
from .models import Document, ExtractionResult
from .extractor import DataExtractor

# Note: ExtractionService not imported here to avoid circular import
# Import directly: from core.extraction.services import ExtractionService

__all__ = ['Document', 'ExtractionResult', 'DataExtractor']
