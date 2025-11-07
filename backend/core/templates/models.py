"""
Templates Domain Models
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, List


@dataclass
class Template:
    """Template model"""
    id: int
    name: str
    filename: str
    config_path: str
    field_count: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'filename': self.filename,
            'config_path': self.config_path,
            'field_count': self.field_count,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class TemplateConfig:
    """Template configuration model"""
    template_id: int
    fields: Dict
    metadata: Dict
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'template_id': self.template_id,
            'fields': self.fields,
            'metadata': self.metadata
        }


@dataclass
class FieldInfo:
    """Field information model"""
    name: str
    location: Dict
    context: Dict
    pattern: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'location': self.location,
            'context': self.context,
            'pattern': self.pattern
        }
