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
    extraction_time_ms: Optional[int]
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    validated_at: Optional[datetime] = None
    used_for_training: Optional[int] = 0
    experiment_phase: Optional[str] = None  # For experiment tracking
    created_by: Optional[int] = None
    updated_by: Optional[int] = None

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "template_id": self.template_id,
            "filename": self.filename,
            "file_path": self.file_path,
            "extraction_result": self.extraction_result,
            "extraction_time_ms": self.extraction_time_ms,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "validated_at": self.validated_at,
            "used_for_training": self.used_for_training,
            "experiment_phase": self.experiment_phase,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
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
            "document_id": self.document_id,
            "results": self.results,
            "confidence_scores": self.confidence_scores,
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
            "id": self.id,
            "document_id": self.document_id,
            "field_corrections": self.field_corrections,
            "feedback_path": self.feedback_path,
            "used_for_training": self.used_for_training,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
