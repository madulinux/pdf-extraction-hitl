"""
Conflict Detection Module
Detects and analyzes value conflicts across multiple field locations
"""
from typing import List, Dict, Any, Optional
from difflib import SequenceMatcher
import logging


logger = logging.getLogger(__name__)


def calculate_similarity(str1: str, str2: str) -> float:
    """
    Calculate similarity between two strings using multiple metrics
    
    Args:
        str1: First string
        str2: Second string
        
    Returns:
        Similarity score between 0.0 and 1.0
    """
    if not str1 or not str2:
        return 0.0
    
    # Normalize strings
    s1 = str1.lower().strip()
    s2 = str2.lower().strip()
    
    # Exact match
    if s1 == s2:
        return 1.0
    
    # 1. Sequence matching (overall similarity)
    sequence_ratio = SequenceMatcher(None, s1, s2).ratio()
    
    # 2. Word-level matching (handles reordering)
    words1 = set(s1.split())
    words2 = set(s2.split())
    
    if not words1 or not words2:
        word_overlap = 0.0
    else:
        word_overlap = len(words1 & words2) / max(len(words1), len(words2))
    
    # 3. Substring matching (handles abbreviations)
    substring_match = 0.0
    if s1 in s2 or s2 in s1:
        substring_match = 0.5
    
    # Combined score (weighted)
    similarity = (
        sequence_ratio * 0.5 +
        word_overlap * 0.3 +
        substring_match * 0.2
    )
    
    return similarity


def determine_conflict_level(similarity: float) -> str:
    """
    Determine conflict severity level based on similarity
    
    Args:
        similarity: Similarity score (0.0 to 1.0)
        
    Returns:
        Conflict level: 'minor', 'moderate', or 'major'
    """
    if similarity > 0.8:
        return 'minor'
    elif similarity > 0.5:
        return 'moderate'
    else:
        return 'major'


def detect_conflicts(
    field_name: str,
    extraction_results: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """
    Detect conflicts in extraction results from multiple locations
    
    Args:
        field_name: Name of the field
        extraction_results: List of extraction results from different locations
                          Each result should have: value, confidence, location_index, page, label, method
        
    Returns:
        Conflict information dict if conflicts detected, None otherwise
    """
    if not extraction_results or len(extraction_results) < 2:
        return None
    
    # Get unique values
    unique_values = set(r['value'] for r in extraction_results if r['value'])
    
    if len(unique_values) <= 1:
        # No conflict - all values are the same
        return None
    
    # Calculate pairwise similarities
    similarity_scores = []
    values_list = list(unique_values)
    
    for i, val1 in enumerate(values_list):
        for val2 in values_list[i+1:]:
            sim = calculate_similarity(val1, val2)
            similarity_scores.append(sim)
    
    # Average similarity
    avg_similarity = sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0.0
    
    # Determine conflict level
    conflict_level = determine_conflict_level(avg_similarity)
    
    # Sort results by confidence (best first)
    sorted_results = sorted(extraction_results, key=lambda r: r['confidence'], reverse=True)
    best_result = sorted_results[0]
    
    # Auto-resolve minor conflicts (select longest/most complete value)
    auto_resolved = False
    selected_value = best_result['value']
    
    if conflict_level == 'minor' and avg_similarity > 0.8:
        # Auto-select longest value
        longest_result = max(extraction_results, key=lambda r: len(r['value']))
        selected_value = longest_result['value']
        auto_resolved = True
        logger.info(
            f"Auto-resolved minor conflict for '{field_name}': "
            f"Selected '{selected_value}' (most complete)"
        )
    
    # Generate suggestion
    suggestion = generate_suggestion(conflict_level, avg_similarity, unique_values)
    
    # Build conflict info
    conflict_info = {
        'detected': True,
        'level': conflict_level,
        'similarity': round(avg_similarity, 3),
        'all_values': [
            {
                'value': r['value'],
                'confidence': r['confidence'],
                'page': r.get('page', 0),
                'label': r.get('label'),
                'location_index': r.get('location_index', 0),
                'method': r.get('method', 'unknown')
            }
            for r in extraction_results
        ],
        'auto_resolved': auto_resolved,
        'requires_validation': conflict_level in ['moderate', 'major'],
        'suggestion': suggestion,
        'selected_value': selected_value
    }
    
    return conflict_info


def generate_suggestion(
    conflict_level: str,
    similarity: float,
    unique_values: set
) -> str:
    """
    Generate helpful suggestion based on conflict characteristics
    
    Args:
        conflict_level: Conflict severity level
        similarity: Similarity score
        unique_values: Set of unique values
        
    Returns:
        Suggestion text
    """
    if conflict_level == 'minor':
        return "Values are similar, likely same data with minor variations (abbreviation, formatting, etc.)"
    elif conflict_level == 'moderate':
        return "Values are somewhat different. Please verify which is correct."
    else:
        return "Values are very different. This may indicate a data entry error. Please review carefully."


def merge_extraction_results_with_conflicts(
    field_name: str,
    extraction_results: List[Dict[str, Any]],
    best_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Merge extraction results and add conflict detection
    
    Args:
        field_name: Field name
        extraction_results: All extraction results from different locations
        best_result: The best extraction result (highest confidence)
        
    Returns:
        Enhanced result with conflict information
    """
    # Detect conflicts
    conflict_info = detect_conflicts(field_name, extraction_results)
    
    # Build final result
    result = {
        'value': best_result['value'],
        'confidence': best_result['confidence'],
        'method': best_result['method'],
        'metadata': best_result.get('metadata', {})
    }
    
    # Add conflict info if detected
    if conflict_info:
        result['conflict'] = conflict_info
        
        # If auto-resolved, use selected value
        if conflict_info['auto_resolved']:
            result['value'] = conflict_info['selected_value']
            # Slightly reduce confidence for auto-resolved conflicts
            result['confidence'] = min(result['confidence'] * 0.95, 1.0)
    
    return result
