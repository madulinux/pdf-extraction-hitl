"""
Templates Service
Business logic for template management
"""
from typing import Dict, Any, Optional, List
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import json

from .models import Template, TemplateConfig
from .repositories import TemplateRepository
from core.templates.analyzer import TemplateAnalyzer
from shared.exceptions import NotFoundError, ValidationError


class TemplateService:
    """Service layer for template operations"""
    
    def __init__(self, repository: TemplateRepository, upload_folder: str, template_folder: str):
        self.repository = repository
        self.upload_folder = upload_folder
        self.template_folder = template_folder
        self.analyzer = TemplateAnalyzer()
    
    def analyze_and_create(self, file: FileStorage, template_name: str) -> Dict[str, Any]:
        """
        Analyze PDF template and create template record
        
        Args:
            file: Uploaded PDF file
            template_name: Name for the template
            
        Returns:
            Dictionary with template data and config
        """
        # Validate template name
        if not template_name or template_name.strip() == '':
            raise ValidationError("Template name is required")
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(self.upload_folder, filename)
        file.save(filepath)
        
        # Store in database first to get template_id
        template_id = self.repository.create(
            name=template_name,
            filename=filename,
            config_path='',  # Will update after analysis
            field_count=0  # Will update after analysis
        )
        
        # Analyze template with template_id and name
        config = self.analyzer.analyze_template(filepath, template_id, template_name)
        
        # Save configuration
        config_filename = f"{timestamp}_config.json"
        config_path = os.path.join(self.template_folder, config_filename)
        self.analyzer.save_config(config, config_path)
        
        # Update template with config path and field count
        self.repository.update(
            template_id=template_id,
            config_path=config_path,
            field_count=config['metadata']['field_count']
        )
        
        return {
            'template_id': template_id,
            'template_name': template_name,
            'filename': filename,
            'field_count': config['metadata']['field_count'],
            'config': config
        }
    
    def get_all(self) -> List[Dict]:
        """Get all templates"""
        templates = self.repository.find_all()
        return [template.to_dict() for template in templates]
    
    def get_by_id(self, template_id: int, include_config: bool = True) -> Optional[Dict]:
        """
        Get template by ID with optional configuration
        
        Args:
            template_id: Template ID
            include_config: Whether to include configuration
            
        Returns:
            Template data with config or None if not found
        """
        template = self.repository.find_by_id(template_id)
        
        if not template:
            return None
        
        result = template.to_dict()
        
        # Load configuration if requested
        if include_config:
            config_path = template.config_path
            if not os.path.isabs(config_path):
                config_path = os.path.join(self.template_folder, config_path)
            
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                result['config'] = config
            else:
                result['config'] = None
        
        return result
    
    
    def check_template(self, template_name: str) -> Optional[Dict]:
        """
        Check template by name
        
        Args:
            template_name: Template name
            
        Returns:
            Template data with config or None if not found
        """
        template = self.repository.find_by_name(template_name)
        
        if not template:
            return None
        
        result = template.to_dict()
        
        
        return {
            'template_id': result['id'],
            'template_name': result['name'],
            'filename': result['filename'],
            'field_count': result['field_count'],
            'config': result['config_path']
        }
    
    def get_by_name(self, template_name: str) -> Optional[Dict]:
        """
        Get template by name
        
        Args:
            template_name: Template name
            
        Returns:
            Template data with config or None if not found
        """
        template = self.repository.find_by_name(template_name)
        
        if not template:
            return None
        
        result = template.to_dict()
        
        return result

    def delete(self, template_id: int) -> bool:
        """
        Delete template
        
        Args:
            template_id: Template ID
            
        Returns:
            True if deleted, False if not found
        """
        template = self.repository.find_by_id(template_id)
        
        if not template:
            return False
        
        # Delete from database
        self.repository.delete(template_id)
        
        # Optionally delete files (commented out for safety)
        # os.remove(os.path.join(self.upload_folder, template.filename))
        # os.remove(template.config_path)
        
        return True
