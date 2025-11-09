"""
Strategy Performance Models

Pydantic models for strategy performance data validation.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class StrategyPerformanceBase(BaseModel):
    """Base model for strategy performance"""
    template_id: int = Field(..., description="Template ID")
    field_name: str = Field(..., description="Field name")
    strategy_type: str = Field(..., description="Strategy type (crf, rule_based, position_based)")
    
    class Config:
        from_attributes = True


class StrategyPerformanceCreate(StrategyPerformanceBase):
    """Model for creating strategy performance record"""
    accuracy: float = Field(default=0.0, ge=0.0, le=1.0)
    total_extractions: int = Field(default=0, ge=0)
    correct_extractions: int = Field(default=0, ge=0)


class StrategyPerformanceUpdate(BaseModel):
    """Model for updating strategy performance"""
    was_correct: bool = Field(..., description="Whether the extraction was correct")


class StrategyPerformance(StrategyPerformanceBase):
    """Complete strategy performance model"""
    id: int
    accuracy: float = Field(..., ge=0.0, le=1.0)
    total_extractions: int = Field(..., ge=0)
    correct_extractions: int = Field(..., ge=0)
    last_updated: datetime
    
    class Config:
        from_attributes = True


class StrategyPerformanceStats(BaseModel):
    """Aggregated statistics for strategy performance"""
    strategy_type: str
    total_fields: int
    avg_accuracy: float
    total_extractions: int
    total_correct: int
    best_field: Optional[str] = None
    best_field_accuracy: Optional[float] = None
    worst_field: Optional[str] = None
    worst_field_accuracy: Optional[float] = None


class StrategyComparison(BaseModel):
    """Comparison between strategies for a field"""
    field_name: str
    strategies: list[dict]  # List of {strategy_type, accuracy, total_extractions}
    best_strategy: str
    best_accuracy: float
