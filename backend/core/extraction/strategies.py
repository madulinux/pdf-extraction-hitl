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
    if 'locations' in field_config:
        return field_config['locations']
    
    return []


class ExtractionStrategy(ABC):
    """Base class for extraction strategies"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def extract(self, pdf_path: str, field_config: Dict, all_words: List[Dict]) -> Optional[FieldValue]:
        """Extract a field value from PDF"""
        pass
    
    def _post_process_value(
        self, 
        value: str, 
        field_name: str, 
        full_text: str
    ) -> str:
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
            if (cleaned[0] in '""\'\u201c\u201d' and cleaned[-1] in '""\'\u201c\u201d'):
                cleaned = cleaned[1:-1].strip()
        
        # 3. Remove surrounding parentheses (universal rule)
        # Common in PDF text where names/values are wrapped in parentheses
        if len(cleaned) >= 2:
            if cleaned[0] == '(' and cleaned[-1] == ')':
                cleaned = cleaned[1:-1].strip()
        
        # 4. Normalize whitespace (universal rule)
        cleaned = ' '.join(cleaned.split())
        
        # NOTE: For more advanced cleaning (removing specific prefixes/suffixes),
        # the system should LEARN from user feedback, not use hardcoded rules.
        # Future enhancement: Use ML to learn cleaning patterns from corrections.
        
        return cleaned


class RuleBasedExtractionStrategy(ExtractionStrategy):
    """
    Rule-based extraction using regex patterns and positional rules.
    Good for structured documents with consistent layouts.
    """
    
    def extract(self, pdf_path: str, field_config: Dict, all_words: List[Dict]) -> Optional[FieldValue]:
        """
        Extract field using rule-based approach with adaptive learned patterns
        
        Args:
            pdf_path: Path to PDF file
            field_config: Field configuration with location(s) and regex
            all_words: All extracted words from PDF
            
        Returns:
            FieldValue if extraction successful, None otherwise
        """
        field_name = field_config.get('field_name', 'unknown')
        
        # Get patterns: base pattern + learned patterns from feedback
        patterns = self._get_all_patterns(field_config)
        
        # Get all locations (backward compatible)
        locations = get_field_locations(field_config)
        
        if not locations:
            return None
        
        # ✅ CRITICAL: Try learned patterns FIRST (by priority)
        # Learned patterns are more specific and should override base pattern
        # Only fallback to base pattern if NO learned pattern matches
        
        # Separate learned patterns from base pattern
        learned_patterns = [p for p in patterns if p.get('pattern_id') is not None]
        base_patterns = [p for p in patterns if p.get('pattern_id') is None]
        
        # Sort learned patterns by priority (highest first)
        learned_patterns.sort(key=lambda x: x.get('priority', 0), reverse=True)
        
        best_result = None
        best_confidence = 0.0
        best_pattern_id = None
        
        for location in locations:
            # Try learned patterns first
            for pattern_info in learned_patterns:
                pattern_id = pattern_info.get('pattern_id')
                
                try:
                    result = self._extract_from_location(
                        location, field_name, pattern_info['pattern'], all_words
                    )
                    
                    if result and result.confidence > best_confidence:
                        best_result = result
                        best_confidence = result.confidence
                        best_pattern_id = pattern_id
                        # Track which pattern was used
                        best_result.metadata['pattern_used'] = pattern_info.get('description', 'learned')
                        best_result.metadata['pattern_type'] = pattern_info.get('type', 'learned')
                        best_result.metadata['pattern_id'] = pattern_id
                        
                        # ✅ Track successful pattern match
                        self._update_pattern_usage(pattern_id, matched=True)
                        
                        # ✅ IMPORTANT: If learned pattern matches, use it immediately
                        # Don't try base pattern (which always matches with .+)
                        self.logger.info(f"✅ [{field_name}] Using learned pattern (priority={pattern_info.get('priority')}): {pattern_info['pattern'][:50]}")
                        return best_result
                    else:
                        # ❌ Track failed pattern attempt
                        if result is None:
                            self._update_pattern_usage(pattern_id, matched=False)
                            
                except Exception as e:
                    self.logger.error(f"Error extracting with learned pattern: {e}")
                    continue
            
            # If no learned pattern matched, try base pattern as fallback
            for pattern_info in base_patterns:
                try:
                    result = self._extract_from_location(
                        location, field_name, pattern_info['pattern'], all_words
                    )
                    
                    if result and result.confidence > best_confidence:
                        best_result = result
                        best_confidence = result.confidence
                        # Track which pattern was used
                        best_result.metadata['pattern_used'] = pattern_info.get('description', 'base')
                        best_result.metadata['pattern_type'] = pattern_info.get('type', 'manual')
                        best_result.metadata['pattern_id'] = None
                        
                        self.logger.info(f"⚠️ [{field_name}] Fallback to base pattern: {pattern_info['pattern'][:50]}")
                            
                except Exception as e:
                    self.logger.error(f"Error extracting from location: {e}")
                    continue
        
        return best_result
    
    def extract_all(self, pdf_path: str, field_config: Dict, all_words: List[Dict]) -> List[FieldValue]:
        """
        Extract field from ALL locations (for conflict detection)
        
        Args:
            pdf_path: Path to PDF file
            field_config: Field configuration with location(s)
            all_words: All extracted words from PDF
            
        Returns:
            List of FieldValue from all locations
        """
        field_name = field_config.get('field_name', 'unknown')
        
        # Get pattern from validation_rules or use smart default
        validation_rules = field_config.get('validation_rules', {})
        regex_pattern = validation_rules.get('pattern') or self._get_default_pattern(field_config)
        
        locations = get_field_locations(field_config)
        
        results = []
        for idx, location in enumerate(locations):
            try:
                result = self._extract_from_location(
                    location, field_name, regex_pattern, all_words
                )
                if result:
                    # Add location metadata
                    result.metadata['location_index'] = idx
                    result.metadata['page'] = location.get('page', 0)
                    result.metadata['label'] = location.get('context', {}).get('label')
                    results.append(result)
            except Exception as e:
                self.logger.error(f"Error extracting from location {idx}: {e}")
                continue
        
        return results
    
    def _get_all_patterns(self, field_config: Dict) -> List[Dict]:
        """
        Get all patterns: base pattern + learned patterns from database/config
        
        Returns:
            List of pattern dicts with 'pattern', 'description', 'type'
        """
        field_name = field_config.get('field_name', 'unknown')
        patterns = []
        
        # Base pattern (from validation_rules or catch-all default)
        validation_rules = field_config.get('validation_rules', {})
        base_pattern = validation_rules.get('pattern') or self._get_default_pattern(field_config)
        
        patterns.append({
            'pattern': base_pattern,
            'description': 'base_pattern',
            'type': 'manual',
            'pattern_id': None,
            'source': 'validation_rules' if validation_rules.get('pattern') else 'default'
        })
        
        # Log base pattern being used
        self.logger.info(f"📋 [{field_name}] Base pattern: {base_pattern[:50]}... (source: {patterns[0]['source']})")
        
        # Try to load learned patterns from database first
        db_patterns = self._load_patterns_from_db(field_config)
        if db_patterns:
            self.logger.info(f"🎓 [{field_name}] Loaded {len(db_patterns)} learned patterns from database")
            for idx, p in enumerate(db_patterns[:3]):  # Log top 3
                self.logger.info(f"   Pattern {idx+1}: {p['type']} - {p['pattern'][:50]}... (priority: {p.get('priority', 0)})")
            patterns.extend(db_patterns)
        else:
            # Fallback: Load from JSON config (backward compatibility)
            rules = field_config.get('rules', {})
            learned_patterns = rules.get('learned_patterns', [])
            
            if learned_patterns:
                self.logger.debug(f"Found {len(learned_patterns)} learned patterns in config")
                for lp in learned_patterns:
                    patterns.append({
                        'pattern': lp.get('pattern', r'.+'),
                        'description': lp.get('description', 'learned'),
                        'type': lp.get('type', 'learned'),
                        'frequency': lp.get('frequency', 0),
                        'pattern_id': None
                    })
        
        return patterns
    
    def _load_patterns_from_db(self, field_config: Dict) -> List[Dict]:
        """
        Load learned patterns from database
        
        Returns:
            List of pattern dicts or empty list
        """
        try:
            # Get template_id and field_name from config
            template_id = field_config.get('template_id')
            field_name = field_config.get('field_name')
            
            if not template_id or not field_name:
                return []
            
            # Import here to avoid circular dependency
            from database.db_manager import DatabaseManager
            from database.repositories.config_repository import ConfigRepository
            
            db = DatabaseManager()
            config_repo = ConfigRepository(db)
            
            # Get active config
            config = config_repo.get_active_config(template_id)
            if not config:
                return []
            
            # Get field config
            field_cfg = config_repo.get_field_config_by_name(
                config_id=config['id'],
                field_name=field_name
            )
            
            if not field_cfg:
                return []
            
            # Get learned patterns
            learned = config_repo.get_learned_patterns(
                field_config_id=field_cfg['id'],
                active_only=True
            )
            
            # Convert to pattern dicts
            patterns = []
            for lp in learned:
                patterns.append({
                    'pattern': lp['pattern'],
                    'description': lp.get('description', 'learned'),
                    'type': lp.get('pattern_type', 'learned'),
                    'frequency': lp.get('frequency', 0),
                    'priority': lp.get('priority', 0),
                    'pattern_id': lp['id']  # Store ID for usage tracking
                })
            
            # Sort by priority and frequency
            patterns.sort(key=lambda x: (x.get('priority', 0), x.get('frequency', 0)), reverse=True)
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Failed to load patterns from database: {e}")
            return []
    
    def _update_pattern_usage(self, pattern_id: int, matched: bool):
        """
        Update pattern usage statistics
        
        Args:
            pattern_id: Pattern ID
            matched: True if pattern matched successfully
        """
        try:
            from database.db_manager import DatabaseManager
            from database.repositories.config_repository import ConfigRepository
            
            db = DatabaseManager()
            config_repo = ConfigRepository(db)
            
            config_repo.update_pattern_usage(pattern_id, matched)
            
        except Exception as e:
            self.logger.error(f"Failed to update pattern usage: {e}")
    
    def _get_default_pattern(self, field_config: Dict) -> str:
        """
        Get default pattern - always use catch-all
        
        ❌ NO HARDCODING: Pattern learning happens from user feedback,
        not from predefined rules.
        
        Args:
            field_config: Field configuration from database
            
        Returns:
            Default catch-all regex pattern
        """
        # Always use catch-all pattern
        # Real patterns will be learned from user feedback
        return r'.+'
    
    def _extract_from_location(
        self, 
        location: Dict, 
        field_name: str, 
        regex_pattern: str, 
        all_words: List[Dict]
    ) -> Optional[FieldValue]:
        """Extract field from a specific location using context-aware approach"""
        try:
            # Get context information
            context = location.get('context', {})
            label = context.get('label')
            label_pos = context.get('label_position')
            
            # Strategy 1: Try label-based extraction (most accurate)
            if label and label_pos:
                self.logger.debug(f"Trying label-based extraction for {field_name} with label: {label}")
                result = self._extract_with_label(
                    label, label_pos, field_name, regex_pattern, all_words, context
                )
                if result:
                    self.logger.info(f"✅ Label-based extraction succeeded for {field_name}")
                    return result
                else:
                    self.logger.debug(f"Label-based extraction failed, falling back to position-based")
            
            # Strategy 2: Fall back to position-based extraction
            return self._extract_with_position(location, field_name, regex_pattern, all_words)
            
        except Exception as e:
            self.logger.error(f"Rule-based extraction failed for {field_name}: {e}")
            return None
    
    def _extract_with_label(
        self,
        label: str,
        label_pos: Dict,
        field_name: str,
        regex_pattern: str,
        all_words: List[Dict],
        context: Dict
    ) -> Optional[FieldValue]:
        """Extract field value using label as anchor point"""
        try:
            # Find words AFTER the label (on same line)
            label_x1 = label_pos.get('x1', 0)
            label_y0 = label_pos.get('y0', 0)
            label_y1 = label_pos.get('y1', 0)
            label_y_center = (label_y0 + label_y1) / 2
            
            # ✅ NEW: Get next field boundary (Y and X)
            next_field_y = context.get('next_field_y')
            
            # ✅ CRITICAL: Get X-boundary from words_after (for fields on same line)
            # This prevents extracting into next field when they're on same line
            words_after = context.get('words_after', [])
            next_field_x = None
            if words_after and len(words_after) > 0:
                # First word after is likely the next field marker
                next_field_x = words_after[0].get('x')
            
            # Collect candidate words after label
            # ✅ NEW: Stop at next field boundary (Y or X)
            candidate_words = []
            for word in all_words:
                word_x0 = word.get('x0', 0)
                word_y = word.get('top', 0)
                word_y_center = (word.get('top', 0) + word.get('bottom', 0)) / 2
                
                # ✅ CRITICAL: For same-line fields, ONLY use X-boundary
                # If next_field_x exists, it means next field is on same line
                # In this case, ignore Y-boundary (it's unreliable for same-line fields)
                if next_field_x:
                    # Same-line field: use X-boundary only
                    if word_x0 >= next_field_x and abs(word_y_center - label_y_center) < 10:
                        break
                else:
                    # Different-line field: use Y-boundary
                    if next_field_y and word_y >= next_field_y:
                        break
                
                # Word is after label and on same line
                if word_x0 > label_x1 and abs(word_y_center - label_y_center) < 10:
                    candidate_words.append({
                        'word': word,
                        'distance': word_x0 - label_x1
                    })
            
            # Sort by distance (closest first)
            candidate_words.sort(key=lambda w: w['distance'])
            
            # Combine words into text
            candidate_text = ' '.join(w['word'].get('text', '') for w in candidate_words)
            
            # Apply regex pattern
            if candidate_text:
                match = re.search(regex_pattern, candidate_text)
                if match:
                    raw_value = match.group(0).strip()
                    cleaned_value = self._post_process_value(raw_value, field_name, candidate_text)
                    
                    # Higher confidence for label-based extraction
                    confidence = self._calculate_confidence(
                        cleaned_value, regex_pattern, len(candidate_words), field_name, raw_value
                    )
                    confidence = min(confidence + 0.15, 1.0)  # Boost confidence
                    
                    return FieldValue(
                        field_id=field_name,
                        field_name=field_name,
                        value=cleaned_value,
                        confidence=confidence,
                        method='rule_based',
                        metadata={
                            'extraction_type': 'label-based',
                            'label': label,
                            'label_position': label_pos,
                            'regex_pattern': regex_pattern,
                            'candidate_words_count': len(candidate_words),
                            'raw_value': raw_value
                        }
                    )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Label-based extraction failed: {e}")
            return None
    
    def _extract_with_position(
        self,
        location: Dict,
        field_name: str,
        regex_pattern: str,
        all_words: List[Dict]
    ) -> Optional[FieldValue]:
        """Extract field value using position-based approach (fallback)"""
        try:
            # Define search area
            # CRITICAL FIX: Search from LEFT of marker (where data actually is!)
            # Data REPLACES marker at same position, not appended after it
            marker_x0 = location.get('x0', 0)
            marker_x1 = location.get('x1', 0)
            marker_y0 = location.get('y0', 0)
            marker_y1 = location.get('y1', 0)
            marker_y_center = (marker_y0 + marker_y1) / 2
            
            # ✅ NEW: Get context for boundary detection
            context = location.get('context', {})
            next_field_y = context.get('next_field_y')
            
            # ✅ CRITICAL: Get X-boundary from words_after (for fields on same line)
            words_after = context.get('words_after', [])
            next_field_x = None
            if words_after and len(words_after) > 0:
                next_field_x = words_after[0].get('x')
            
            # Start search BEFORE marker to catch data that overlaps
            x0 = marker_x0 - 50  # Buffer to catch data slightly before marker
            y0 = marker_y0 - 10  # Expand vertical search
            x1 = marker_x1 + 400  # Search well beyond marker
            y1 = marker_y1 + 10  # Expand vertical search
            
            # Find words in the search area with boundary checking
            candidate_words = []
            for word in all_words:
                word_x0 = word.get('x0', 0)
                word_x1 = word.get('x1', 0)
                word_y = word.get('top', 0)
                word_y_center = (word.get('top', 0) + word.get('bottom', 0)) / 2
                
                # Basic area check
                if not (word_x0 >= x0 and word_x1 <= x1 and
                        word_y >= y0 and word.get('bottom', 0) <= y1):
                    continue
                
                # ✅ CRITICAL: For same-line fields, ONLY use X-boundary
                # If next_field_x exists, it means next field is on same line
                # In this case, ignore Y-boundary (it's unreliable for same-line fields)
                if next_field_x:
                    # Same-line field: use X-boundary only
                    if word_x0 >= next_field_x and abs(word_y_center - marker_y_center) < 10:
                        continue
                else:
                    # Different-line field: use Y-boundary
                    if next_field_y and word_y >= next_field_y:
                        continue
                
                candidate_words.append(word)
            
            # Sort by position (left to right, top to bottom)
            candidate_words.sort(key=lambda w: (w.get('top', 0), w.get('x0', 0)))
            
            # Combine words into text
            candidate_text = ' '.join(w.get('text', '') for w in candidate_words)
            
            # Apply regex pattern
            if candidate_text:
                match = re.search(regex_pattern, candidate_text)
                if match:
                    raw_value = match.group(0).strip()
                    
                    # Post-process: Clean up the value
                    cleaned_value = self._post_process_value(
                        raw_value, 
                        field_name, 
                        candidate_text
                    )
                    
                    # Calculate confidence based on match quality
                    confidence = self._calculate_confidence(
                        cleaned_value, 
                        regex_pattern, 
                        len(candidate_words),
                        field_name,
                        raw_value  # Pass raw value for comparison
                    )
                    
                    return FieldValue(
                        field_id=field_name,
                        field_name=field_name,
                        value=cleaned_value,
                        confidence=confidence,
                        method='rule_based',
                        metadata={
                            'regex_pattern': regex_pattern,
                            'search_area': {'x0': x0, 'y0': y0, 'x1': x1, 'y1': y1},
                            'candidate_words_count': len(candidate_words),
                            'raw_value': raw_value  # Store raw for debugging
                        }
                    )
            
            self.logger.debug(f"No match found for field {field_name}")
            return None
            
        except Exception as e:
            self.logger.error(f"Rule-based extraction failed for {field_name}: {e}")
            return None
    
    def _calculate_confidence(
        self, 
        value: str, 
        pattern: str, 
        word_count: int,
        field_name: str,
        raw_value: str = None
    ) -> float:
        """
        Calculate confidence score based on extraction quality
        Uses pattern matching and data characteristics (not hardcoded rules)
        
        Args:
            value: Cleaned extracted value
            pattern: Regex pattern used
            word_count: Number of words found
            field_name: Name of the field
            raw_value: Original value before cleaning (optional)
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not value:
            return 0.0
        
        confidence = 0.5  # Base confidence
        
        # Penalty if value was heavily cleaned (indicates noisy extraction)
        if raw_value and raw_value != value:
            cleaning_ratio = 1 - (len(value) / len(raw_value))
            if cleaning_ratio > 0.3:  # More than 30% was removed
                confidence -= 0.2
            elif cleaning_ratio > 0.15:  # 15-30% removed
                confidence -= 0.1
        
        # 1. Pattern match quality (most important)
        if re.fullmatch(pattern, value):
            # Perfect pattern match
            confidence += 0.3
        elif re.search(pattern, value):
            # Partial pattern match
            confidence += 0.15
        else:
            # No pattern match - suspicious
            confidence -= 0.2
        
        # 2. Value length appropriateness
        value_length = len(value)
        if value_length == 0:
            confidence = 0.0
        elif value_length == 1:
            # Single character is usually incomplete/wrong
            confidence -= 0.25
        elif 2 <= value_length <= 3:
            # Very short - might be incomplete
            confidence -= 0.1
        elif 4 <= value_length <= 100:
            # Reasonable length
            confidence += 0.1
        elif value_length > 100:
            # Very long - might include extra text
            confidence += 0.05
        
        # 3. Word count (indicates completeness)
        if word_count >= 3:
            confidence += 0.15  # Multiple words = more complete
        elif word_count == 2:
            confidence += 0.1
        elif word_count == 1:
            confidence += 0.0  # Neutral
        
        # Penalty for excessive word count (likely includes extra text)
        if word_count > 10:
            confidence -= 0.15  # Too many words - probably captured extra text
        elif word_count > 7:
            confidence -= 0.1
        
        # 4. Pattern complexity match
        # If pattern is complex but value is simple, likely wrong
        pattern_has_classes = bool(re.search(r'\\[dDwWsS]', pattern))
        pattern_has_quantifiers = bool(re.search(r'[+*{]', pattern))
        
        if pattern_has_classes or pattern_has_quantifiers:
            # Complex pattern expects structured data
            if value_length < 3:
                confidence -= 0.15
        
        return max(0.0, min(1.0, confidence))


class PositionExtractionStrategy(ExtractionStrategy):
    """
    Position-based extraction using coordinate information.
    Good for forms with fixed layouts.
    """
    
    def extract(self, pdf_path: str, field_config: Dict, all_words: List[Dict]) -> Optional[FieldValue]:
        """
        Extract field using position-based approach
        
        Args:
            pdf_path: Path to PDF file
            field_config: Field configuration with location(s)
            all_words: All extracted words from PDF
            
        Returns:
            FieldValue if extraction successful, None otherwise
        """
        field_name = field_config.get('field_name', 'unknown')
        
        # Get all locations (backward compatible)
        locations = get_field_locations(field_config)
        
        if not locations:
            return None
        
        # Try extraction for each location
        best_result = None
        best_confidence = 0.0
        
        for location in locations:
            try:
                result = self._extract_from_location(location, field_name, all_words)
                
                if result and result.confidence > best_confidence:
                    best_result = result
                    best_confidence = result.confidence
            except Exception as e:
                self.logger.error(f"Error extracting from location: {e}")
                continue
        
        return best_result
    
    def _extract_from_location(
        self, 
        location: Dict, 
        field_name: str, 
        all_words: List[Dict]
    ) -> Optional[FieldValue]:
        """Extract field from a specific location"""
        try:
            # CRITICAL FIX: Data is AT marker position, not after it!
            marker_x0 = location.get('x0', 0)
            marker_x1 = location.get('x1', 0)
            marker_y0 = location.get('y0', 0)
            marker_y1 = location.get('y1', 0)
            marker_y_center = (marker_y0 + marker_y1) / 2
            
            # Collect all words in the marker area and beyond
            candidate_words = []
            
            for word in all_words:
                word_x0 = word.get('x0', 0)
                word_x1 = word.get('x1', 0)
                word_y_center = (word.get('top', 0) + word.get('bottom', 0)) / 2
                y_distance = abs(word_y_center - marker_y_center)
                
                # Include words that:
                # 1. Start at or after marker start (with buffer)
                # 2. Are on the same line (within 10 points vertically)
                if word_x0 >= (marker_x0 - 50) and y_distance < 10:
                    candidate_words.append({
                        'word': word,
                        'x0': word_x0,
                        'distance': word_x0 - marker_x0  # Distance from marker start
                    })
            
            # Sort by horizontal position (left to right)
            candidate_words.sort(key=lambda w: w['x0'])
            
            # ✅ NEW: Get next field boundary (Y and X)
            context = location.get('context', {})
            next_field_y = context.get('next_field_y') if context else None
            
            # ✅ CRITICAL: Get X-boundary from words_after (for fields on same line)
            words_after = context.get('words_after', []) if context else []
            next_field_x = None
            if words_after and len(words_after) > 0:
                next_field_x = words_after[0].get('x')
            
            # Extract ALL words from marker position onwards (same line)
            # ✅ NEW: Stop at next field boundary (Y or X)
            # This handles multi-word values like "Ophelia Yuniar, S.Kom"
            value_words = []
            first_word_pos = None
            
            if candidate_words:
                for cw in candidate_words:
                    word_x0 = cw['word'].get('x0', 0)
                    word_y = cw['word'].get('top', 0)
                    
                    # ✅ CRITICAL: For same-line fields, ONLY use X-boundary
                    # If next_field_x exists, it means next field is on same line
                    if next_field_x:
                        # Same-line field: use X-boundary only
                        if word_x0 >= next_field_x:
                            break
                    else:
                        # Different-line field: use Y-boundary
                        if next_field_y and word_y >= next_field_y:
                            break
                    
                    if cw['distance'] >= -10:  # At or after marker
                        value_words.append(cw['word'].get('text', ''))
                        if first_word_pos is None:
                            first_word_pos = {
                                'x0': cw['word'].get('x0'),
                                'y0': cw['word'].get('top')
                            }
            
            if value_words:
                value = ' '.join(value_words).strip()
                
                # Base confidence for position-based
                confidence = 0.90 if len(value) > 0 else 0.4
                
                # Boost confidence if context validates the extraction
                context = location.get('context', {})
                if context:
                    confidence = self._validate_with_context(value, context, confidence)
                
                return FieldValue(
                    field_id=field_name,
                    field_name=field_name,
                    value=value,
                    confidence=confidence,
                    method='position_based',
                    metadata={
                        'marker_position': {'x1': marker_x1, 'y0': marker_y0, 'y1': marker_y1},
                        'value_position': first_word_pos,
                        'word_count': len(value_words),
                        'context_validated': bool(context)
                    }
                )
            
            self.logger.debug(f"No word found near marker for field {field_name}")
            return None
            
        except Exception as e:
            self.logger.error(f"Position-based extraction failed for {field_name}: {e}")
            return None
    
    def _validate_with_context(
        self,
        value: str,
        context: Dict,
        base_confidence: float
    ) -> float:
        """
        Validate extracted value using context information
        Boosts confidence if context supports the extraction
        """
        confidence = base_confidence
        
        # Check if label exists (indicates structured field)
        if context.get('label'):
            confidence = min(confidence + 0.05, 1.0)
            self.logger.debug(f"Context has label, boosting confidence")
        
        # Check if words_before exist (indicates context awareness)
        words_before = context.get('words_before', [])
        if words_before:
            confidence = min(confidence + 0.03, 1.0)
            self.logger.debug(f"Context has {len(words_before)} words before")
        
        # Penalize if value is empty but context suggests there should be data
        if not value and (context.get('label') or words_before):
            confidence = max(confidence - 0.3, 0.0)
            self.logger.warning(f"Empty value but context suggests data should exist")
        
        return confidence


class CRFExtractionStrategy(ExtractionStrategy):
    """
    CRF-based extraction using machine learning.
    Improves with training data from user feedback.
    """
    
    def __init__(self, model_path: Optional[str] = None):
        super().__init__()
        self.model = None
        self.model_path = model_path
        self.model_mtime = None  # Track model file modification time
        
        if model_path:
            self._load_model(model_path)
    
    def _load_model(self, model_path: str, force_reload: bool = False):
        """
        Load trained CRF model with hot reload support
        
        Args:
            model_path: Path to model file
            force_reload: Force reload even if file hasn't changed
        """
        try:
            import joblib
            import os
            
            if not os.path.exists(model_path):
                print(f"❌ [CRF] Model file not found: {model_path}")
                self.model = None
                self.model_mtime = None
                return
            
            # Check if model file has been updated
            current_mtime = os.path.getmtime(model_path)
            
            if not force_reload and self.model is not None and self.model_mtime == current_mtime:
                # Model already loaded and file hasn't changed
                return
            
            print(f"🔍 [CRF] Loading model from: {model_path}")
            self.model = joblib.load(model_path)
            self.model_mtime = current_mtime
            print(f"✅ [CRF] Model loaded successfully (mtime: {current_mtime})")
            print(f"✅ [CRF] Model type: {type(self.model)}")
            
            # ✅ DEBUG: Show what labels the model knows
            if hasattr(self.model, 'classes_'):
                print(f"📋 [CRF] Model knows these labels: {self.model.classes_}")
            
        except Exception as e:
            print(f"❌ [CRF] Error loading model: {e}")
            import traceback
            print(traceback.format_exc())
            self.model = None
            self.model_mtime = None
    
    def reload_model_if_updated(self):
        """Check and reload model if file has been updated"""
        if self.model_path:
            self._load_model(self.model_path, force_reload=False)
    
    def extract(self, pdf_path: str, field_config: Dict, all_words: List[Dict]) -> Optional[FieldValue]:
        """
        Extract field using CRF model with hot reload support
        
        Args:
            pdf_path: Path to PDF file
            field_config: Field configuration
            all_words: All extracted words from PDF
            
        Returns:
            FieldValue if extraction successful, None otherwise
        """
        field_name = field_config.get('field_name', 'unknown')
        
        # 🔥 HOT RELOAD: Check if model has been updated
        self.reload_model_if_updated()
        
        if not self.model:
            print(f"❌ [CRF] Model not available for field '{field_name}'")
            return None
        
        print(f"🤖 [CRF] Model IS available, extracting '{field_name}'...")
        
        try:
            # Get all locations for context
            locations = get_field_locations(field_config)
            context = locations[0].get('context', {}) if locations else {}
            
            # ✅ FIELD-AWARE: Prepare features with target field indicator
            # This tells the model which field we're looking for
            features = self._extract_features(
                all_words, field_name, field_config, context,
                target_field=field_name  # ✅ NEW: Pass target field
            )
            
            # Predict using CRF model
            predictions = self.model.predict([features])[0]
            marginals = self.model.predict_marginals([features])[0]
            
            # Extract tokens labeled for this field
            target_label = f'B-{field_name.upper()}'
            inside_label = f'I-{field_name.upper()}'
            
            print(f"🔍 [CRF] Looking for labels: {target_label}, {inside_label}")
            print(f"🔍 [CRF] Predictions sample (first 10): {predictions[:10]}")
            print(f"🔍 [CRF] Unique labels in predictions: {set(predictions)}")
            
            extracted_tokens = []
            confidences = []
            
            # ✅ ADAPTIVE: Get next field boundary (Y and X)
            next_field_y = context.get('next_field_y')
            print(f"   📏 [Debug] next_field_y from context: {next_field_y}")
            
            # ✅ CRITICAL: Get X-boundary from words_after (for fields on same line)
            words_after = context.get('words_after', [])
            next_field_x = None
            if words_after and len(words_after) > 0:
                next_field_x = words_after[0].get('x')
                print(f"   📏 [Debug] next_field_x from words_after: {next_field_x}")
            
            # ✅ ADAPTIVE: Get typical field length (learned from training data)
            typical_length = context.get('typical_length')
            max_length = int(typical_length * 1.3) if typical_length else None  # 1.3x = 30% tolerance
            print(f"   📏 [Debug] typical_length: {typical_length}, max_length: {max_length}")
            
            # ✅ ADAPTIVE: Track parentheses state to skip content inside
            inside_parentheses = False
            
            # ✅ Let model learn boundaries from training data
            # But enforce hard stop at next_field_y/X (adaptive, not hardcoded!)
            for i, (pred, marginal) in enumerate(zip(predictions, marginals)):
                if pred in [target_label, inside_label]:
                    if i < len(all_words):
                        word = all_words[i]
                        word_x0 = word.get('x0', 0)
                        word_y = word.get('top', 0)
                        word_text = word.get('text', '')
                        
                        # ✅ CRITICAL: For same-line fields, ONLY use X-boundary
                        # If next_field_x exists, it means next field is on same line
                        if next_field_x:
                            # Same-line field: use X-boundary only
                            if word_x0 >= next_field_x:
                                print(f"   🛑 [Adaptive] Stopped at next field X boundary (word_x0={word_x0} >= next_field_x={next_field_x})")
                                print(f"   📊 [Adaptive] Extracted {len(extracted_tokens)} tokens before X boundary")
                                break
                        else:
                            # Different-line field: use Y-boundary
                            if next_field_y and word_y >= next_field_y:
                                print(f"   🛑 [Adaptive] Stopped at next field Y boundary (word_y={word_y} >= next_field_y={next_field_y})")
                                print(f"   📊 [Adaptive] Extracted {len(extracted_tokens)} tokens before boundary")
                                break
                        
                        # ✅ ADAPTIVE: Stop if extracted length exceeds typical length (learned from training)
                        current_length = len(' '.join(extracted_tokens + [word_text]))
                        if max_length and current_length > max_length:
                            print(f"   🛑 [Adaptive] Stopped at length limit (current={current_length} > max={max_length})")
                            print(f"   📊 [Adaptive] Extracted {len(extracted_tokens)} tokens before length limit")
                            break
                        
                        # ✅ ADAPTIVE: Track and skip ALL content inside parentheses
                        # This prevents extracting metadata like "(Supervisor: Dr. John)"
                        if word_text == '(':
                            inside_parentheses = True
                            continue
                        elif word_text == ')':
                            inside_parentheses = False
                            continue
                        elif inside_parentheses:
                            continue  # Skip content inside parentheses
                        
                        conf = marginal.get(pred, 0.0)
                        extracted_tokens.append(word_text)
                        confidences.append(conf)
            
            if extracted_tokens:
                raw_value = ' '.join(extracted_tokens)
                import numpy as np
                avg_confidence = float(np.mean(confidences)) if confidences else 0.5
                
                # ✅ ADAPTIVE: Remove text BEFORE label (if label exists in extracted text)
                # This is NOT hardcoded - it uses label from context dynamically
                label = context.get('label', '')
                if label and label in raw_value:
                    # Find label position and take only text AFTER it
                    parts = raw_value.split(label, 1)
                    if len(parts) > 1:
                        raw_value = parts[1].strip()
                        print(f"   🎯 [Adaptive] Removed text before label '{label}'")
                
                # ✅ CRITICAL FIX: Apply post-processing like rule-based does
                # This removes parentheses, trailing commas, etc.
                cleaned_value = self._post_process_value(raw_value, field_name, raw_value)
                
                print(f"✅ [CRF] Extracted '{field_name}': {cleaned_value[:50]}... (conf: {avg_confidence:.2f})")
                if raw_value != cleaned_value:
                    print(f"   🧹 Cleaned: '{raw_value}' → '{cleaned_value}'")
                
                return FieldValue(
                    field_id=field_name,
                    field_name=field_name,
                    value=cleaned_value,  # ✅ Use cleaned value
                    confidence=avg_confidence,
                    method='crf',
                    metadata={
                        'model_path': self.model_path,
                        'token_count': len(extracted_tokens),
                        'confidence_scores': confidences,
                        'raw_value': raw_value  # Keep raw for debugging
                    }
                )
            
            # ✅ DETAILED LOGGING: Why CRF returned None
            print(f"⚠️ [CRF] No tokens found for '{field_name}'")
            print(f"   Looking for: {target_label}, {inside_label}")
            print(f"   Total predictions: {len(predictions)}")
            print(f"   Unique labels predicted: {set(predictions)}")
            
            # Count how many times target field was predicted (even if not selected)
            target_count = sum(1 for p in predictions if field_name.upper() in p)
            if target_count > 0:
                print(f"   ⚠️ Model predicted {target_count} tokens with '{field_name.upper()}' but none matched B-/I- pattern!")
                # Show sample predictions with indices
                related_preds = [(i, all_words[i]['text'], p) for i, p in enumerate(predictions) if field_name.upper() in p and i < len(all_words)]
                print(f"   Sample predictions: {related_preds[:5]}")
            else:
                print(f"   ℹ️ Model did not predict any tokens for this field")
            
            self.logger.debug(f"⚠️ CRF: No tokens found for '{field_name}' (predicted {target_count} related tokens)")
            return None
            
        except Exception as e:
            self.logger.error(f"CRF extraction failed for {field_name}: {e}")
            return None
    
    def _extract_features(
        self, 
        words: List[Dict], 
        field_name: str,
        field_config: Dict,
        context: Dict,
        target_field: str = None  # ✅ NEW: Target field for field-aware features
    ) -> List[Dict[str, Any]]:
        """
        Extract features from words for CRF model with context information
        MUST match exactly with AdaptiveLearner._extract_word_features!
        
        Args:
            words: List of word dictionaries
            field_name: Name of the field being extracted
            field_config: Field configuration
            context: Context information (label, position, etc.)
            target_field: Target field name for field-aware features
        """
        features = []
        
        # Extract context information
        label = context.get('label', '')
        label_pos = context.get('label_position', {})
        words_before = context.get('words_before', [])
        words_after = context.get('words_after', [])
        
        # Build context text for matching
        context_before_text = ' '.join(w.get('text', '') if isinstance(w, dict) else str(w) for w in words_before).lower()
        context_after_text = ' '.join(w.get('text', '') if isinstance(w, dict) else str(w) for w in words_after).lower()
        
        # Import regex for pattern matching
        import re
        
        for i, word in enumerate(words):
            text = word.get('text', '')
            word_x = word.get('x0', 0)
            word_y = word.get('top', 0)
            
            word_features = {
                # Lexical features
                'word': text,
                'word.lower': text.lower(),
                'word.isupper': text.isupper(),
                'word.istitle': text.istitle(),
                'word.isdigit': text.isdigit(),
                'word.isalpha': text.isalpha(),
                'word.isalnum': text.isalnum(),
                'word.length': len(text),
                
                # Orthographic features
                'has_digit': any(c.isdigit() for c in text),
                'has_upper': any(c.isupper() for c in text),
                'has_hyphen': '-' in text,
                'has_dot': '.' in text,
                'has_comma': ',' in text,
                'has_slash': '/' in text,
                
                # Layout features (normalized)
                'x0_norm': word.get('x0', 0) / 1000,
                'y0_norm': word.get('top', 0) / 1000,
                'width': (word.get('x1', 0) - word.get('x0', 0)) / 1000,
                'height': (word.get('bottom', 0) - word.get('top', 0)) / 1000,
                
                # ✅ NEW: Date-specific features (PATTERN-BASED, NOT HARDCODED!)
                'is_capitalized_word': text.istitle() and text.isalpha() and len(text) > 2,  # Likely month/location
                'is_year': text.isdigit() and len(text) == 4 and 1900 <= int(text) <= 2100,
                'is_day_number': text.isdigit() and len(text) <= 2 and (1 <= int(text) <= 31 if text.isdigit() else False),
                'is_date_separator': text in [',', '-', '/', '.'],
                'looks_like_date_pattern': bool(re.match(r'\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4}', text)),
                'has_numeric_context': False,  # Will be set below based on neighbors
                
                # ✅ NEW: Boundary detection features (MUST MATCH learner.py!)
                'is_after_punctuation': False,
                'is_before_punctuation': False,
                'is_after_newline': False,
                'position_in_line': 0,
                
                # Context features
                'has_label': bool(label),
                'label_text': label.lower() if label else '',
                'in_context_before': text.lower() in context_before_text,
                'in_context_after': text.lower() in context_after_text,
            }
            
            # ✅ ENHANCED: Distance from label with stronger constraints (MUST match learner.py!)
            if label_pos:
                label_x0 = label_pos.get('x0', 0)
                label_x1 = label_pos.get('x1', 0)
                label_y0 = label_pos.get('y0', 0)
                label_y1 = label_pos.get('y1', 0)
                
                distance_x = word_x - label_x1
                distance_y = abs(word_y - label_y0)
                
                # ✅ ENHANCED: Stronger positional constraints for complex layouts
                is_after_label = distance_x > 0
                is_before_label = word_x < label_x0
                is_above_label = word_y < label_y0
                is_below_label = word_y > label_y1
                is_same_line = distance_y < 10
                
                word_features['distance_from_label_x'] = distance_x / 100  # Normalized
                word_features['distance_from_label_y'] = distance_y / 100
                word_features['after_label'] = is_after_label
                word_features['before_label'] = is_before_label  # ✅ NEW
                word_features['above_label'] = is_above_label    # ✅ NEW
                word_features['below_label'] = is_below_label    # ✅ NEW
                word_features['same_line_as_label'] = is_same_line
                word_features['near_label'] = distance_x < 50 and is_same_line
                word_features['valid_position'] = is_after_label and is_same_line  # ✅ NEW
            else:
                word_features['distance_from_label_x'] = 0
                word_features['distance_from_label_y'] = 0
                word_features['after_label'] = False
                word_features['before_label'] = False
                word_features['above_label'] = False
                word_features['below_label'] = False
                word_features['same_line_as_label'] = False
                word_features['near_label'] = False
                word_features['valid_position'] = False
            
            # ✅ NEW: Next field boundary features (MUST match learner.py!)
            next_field_y = context.get('next_field_y')
            if next_field_y is not None:
                distance_to_next = next_field_y - word_y
                word_features['has_next_field'] = True
                word_features['distance_to_next_field'] = distance_to_next / 100
                word_features['before_next_field'] = distance_to_next > 0
                word_features['near_next_field'] = 0 < distance_to_next < 20
                word_features['far_from_next_field'] = distance_to_next > 50
            else:
                word_features['has_next_field'] = False
                word_features['distance_to_next_field'] = 0
                word_features['before_next_field'] = False
                word_features['near_next_field'] = False
                word_features['far_from_next_field'] = False
            
            # Prefix and suffix features
            if len(text) > 1:
                word_features['prefix-2'] = text[:2]
                word_features['suffix-2'] = text[-2:]
            if len(text) > 2:
                word_features['prefix-3'] = text[:3]
                word_features['suffix-3'] = text[-3:]
            
            # ✅ ENHANCED: Extended context window (2-3 words) - MUST MATCH learner.py!
            if i > 0:
                prev_word = words[i - 1].get('text', '')
                prev_y = words[i - 1].get('top', 0)
                
                # Context features (previous word)
                word_features['prev_word'] = prev_word.lower()
                word_features['prev_word.isupper'] = prev_word.isupper()
                word_features['prev_word.istitle'] = prev_word.istitle()
                word_features['prev_word.isdigit'] = prev_word.isdigit()
                
                # ✅ NEW: 2-word context (critical for multi-word prefixes like "Jalan W.R.")
                if i > 1:
                    prev2_word = words[i - 2].get('text', '')
                    word_features['prev2_word'] = prev2_word.lower()
                    word_features['prev2_word.istitle'] = prev2_word.istitle()
                    # Bigram feature (2-word sequence before current word)
                    word_features['prev_bigram'] = f"{prev2_word.lower()}_{prev_word.lower()}"
                
                # ✅ NEW: 3-word context (for longer prefixes)
                if i > 2:
                    prev3_word = words[i - 3].get('text', '')
                    word_features['prev3_word'] = prev3_word.lower()
                    # Trigram feature
                    word_features['prev_trigram'] = f"{prev3_word.lower()}_{prev2_word.lower() if i > 1 else ''}_{prev_word.lower()}"
                
                # Boundary features
                word_features['is_after_punctuation'] = prev_word in [',', '.', ':', ';', ')', '(']
                word_features['is_after_newline'] = abs(word_y - prev_y) > 10
                
                # Numeric context (for dates, numbers, etc.)
                word_features['has_numeric_context'] = (
                    prev_word.isdigit() or 
                    word_features['is_year'] or 
                    word_features['is_day_number'] or
                    (prev_word.istitle() and prev_word.isalpha() and len(prev_word) > 2)  # Capitalized word (month/location)
                )
            else:
                word_features['BOS'] = True
            
            # ✅ ENHANCED: Extended next word context - MUST MATCH learner.py!
            if i < len(words) - 1:
                next_word = words[i + 1].get('text', '')
                
                word_features['next_word'] = next_word.lower()
                word_features['next_word.isupper'] = next_word.isupper()
                word_features['next_word.istitle'] = next_word.istitle()
                word_features['next_word.isdigit'] = next_word.isdigit()
                
                # ✅ NEW: 2-word lookahead context
                if i < len(words) - 2:
                    next2_word = words[i + 2].get('text', '')
                    word_features['next2_word'] = next2_word.lower()
                    word_features['next2_word.istitle'] = next2_word.istitle()
                    # Bigram feature (2-word sequence after current word)
                    word_features['next_bigram'] = f"{next_word.lower()}_{next2_word.lower()}"
                
                # ✅ NEW: 3-word lookahead context
                if i < len(words) - 3:
                    next3_word = words[i + 3].get('text', '')
                    word_features['next3_word'] = next3_word.lower()
                    # Trigram feature
                    word_features['next_trigram'] = f"{next_word.lower()}_{next2_word.lower() if i < len(words) - 2 else ''}_{next3_word.lower()}"
                
                # Boundary features
                word_features['is_before_punctuation'] = next_word in [',', '.', ':', ';', ')', '(']
                
                # Enhance numeric context with next word
                if not word_features['has_numeric_context']:
                    word_features['has_numeric_context'] = (
                        next_word.isdigit() or
                        (next_word.istitle() and next_word.isalpha() and len(next_word) > 2)
                    )
            else:
                word_features['EOS'] = True
            
            # Position in line (for boundary detection)
            word_features['position_in_line'] = sum(
                1 for w in words[:i] 
                if abs(w.get('top', 0) - word_y) < 5
            )
            
            # ✅ CRITICAL: Add field-aware feature for target field
            # This tells the model which field we're currently extracting
            # During training: all fields in document have this feature set to True
            # During inference: only the target field has this feature set to True
            if target_field:
                word_features[f'target_field_{target_field}'] = True
                # Debug: Log first word to verify feature is added
                if i == 0:
                    print(f"🔍 [CRF] Added field-aware feature: target_field_{target_field}=True")
            
            features.append(word_features)
        
        return features
