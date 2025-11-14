"""
Extraction Strategies Module

Implements different extraction strategies:
- Rule-based extraction (regex + position)
- Position-based extraction (coordinate-based)
- CRF-based extraction (machine learning)
"""

import logging
import re
import pdfplumber
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass
class FieldValue:
    """Extracted field value with metadata"""

    field_id: str
    field_name: str
    value: str
    confidence: float
    method: str
    metadata: Dict[str, Any]


def get_field_locations(field_config: Dict) -> List[Dict]:
    """
    Get all locations for a field (backward compatible)

    Supports both old format (single location) and new format (locations array)

    Args:
        field_config: Field configuration

    Returns:
        List of location dictionaries
    """
    # New format: locations array
    if "locations" in field_config:
        return field_config["locations"]

    return []


class ExtractionStrategy(ABC):
    """Base class for extraction strategies"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def extract(
        self, pdf_path: str, field_config: Dict, all_words: List[Dict]
    ) -> Optional[FieldValue]:
        """Extract a field value from PDF"""
        pass

    def _post_process_value(self, value: str, field_name: str, full_text: str) -> str:
        """
        Post-process extracted value using general text normalization
        NO HARDCODED RULES - uses universal text cleaning heuristics

        This method applies ONLY general text normalization that would apply
        to ANY field in ANY template. No field-specific or template-specific logic.

        Args:
            value: Raw extracted value
            field_name: Name of the field (not used - kept for future ML-based cleaning)
            full_text: Full candidate text for context (not used - kept for future)

        Returns:
            Cleaned value
        """
        if not value:
            return value

        cleaned = value.strip()

        # 1. Remove leading/trailing punctuation (universal rule)
        # This is a general text normalization, not field-specific
        while cleaned and cleaned[0] in '":;-.,!?':
            cleaned = cleaned[1:].strip()

        while cleaned and cleaned[-1] in '":;-.,!?':
            cleaned = cleaned[:-1].strip()

        # 2. Remove surrounding quotes (universal rule)
        if len(cleaned) >= 2:
            if cleaned[0] in '""\'\u201c\u201d' and cleaned[-1] in '""\'\u201c\u201d':
                cleaned = cleaned[1:-1].strip()

        # 3. Remove surrounding parentheses (universal rule)
        # Common in PDF text where names/values are wrapped in parentheses
        if len(cleaned) >= 2:
            if cleaned[0] == "(" and cleaned[-1] == ")":
                cleaned = cleaned[1:-1].strip()

        # 4. Normalize whitespace (universal rule)
        cleaned = " ".join(cleaned.split())

        # NOTE: For more advanced cleaning (removing specific prefixes/suffixes),
        # the system should LEARN from user feedback, not use hardcoded rules.
        # Future enhancement: Use ML to learn cleaning patterns from corrections.

        return cleaned
