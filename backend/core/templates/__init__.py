"""
Templates Domain
Template analysis and management
"""
from .models import Template, TemplateConfig

# Note: TemplateService not imported here to avoid circular import
# Import directly: from core.templates.services import TemplateService

__all__ = ['Template', 'TemplateConfig']
