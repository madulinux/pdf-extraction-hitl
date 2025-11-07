"""
Extraction Domain Models
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class Document:
    """Document model"""
    id: int
    template_id: int
    filename: str
    file_path: str
    extraction_result: Optional[str]
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'template_id': self.template_id,
            'filename': self.filename,
            'file_path': self.file_path,
            'extraction_result': self.extraction_result,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class ExtractionResult:
    """Extraction result model"""
    document_id: int
    results: Dict[str, Any]
    confidence_scores: Dict[str, float]
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'document_id': self.document_id,
            'results': self.results,
            'confidence_scores': self.confidence_scores
        }


@dataclass
class Feedback:
    """Feedback model"""
    id: int
    document_id: int
    field_corrections: Dict
    feedback_path: str
    used_for_training: bool
    created_at: datetime
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'document_id': self.document_id,
            'field_corrections': self.field_corrections,
            'feedback_path': self.feedback_path,
            'used_for_training': self.used_for_training,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
