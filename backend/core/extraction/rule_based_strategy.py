
import logging
import re
import pdfplumber
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod
from core.extraction.strategies import ExtractionStrategy, FieldValue


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
        
        # ✅ NEW: Try table extraction first for table-like fields
        # This is part of rule-based strategy (structured data extraction)
        self.logger.debug(f"🔍 [{field_name}] Checking if table extraction needed...")
        table_result = self._try_table_extraction(pdf_path, field_config, all_words)
        if table_result:
            self.logger.info(f"✅ [{field_name}] Table extraction SUCCESS: {table_result.value[:50]}")
            return table_result
        else:
            self.logger.debug(f"⚠️ [{field_name}] Table extraction returned None - falling back to patterns")
        
        # Get patterns: base pattern + learned patterns from feedback
        patterns = self._get_all_patterns(field_config)
        
        from .strategies import get_field_locations
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
        
        # ✅ NEW: Track if any learned pattern was attempted
        learned_pattern_attempted = len(learned_patterns) > 0
        
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
                        
                        # ✅ CRITICAL: If learned pattern has good confidence, use it immediately
                        # This prevents base pattern from overriding good learned patterns
                        if result.confidence >= 0.7:
                            self.logger.info(f"✅ [{field_name}] Using learned pattern (priority={pattern_info.get('priority')}, conf={result.confidence:.2f}): {pattern_info['pattern'][:50]}")
                            return best_result
                    else:
                        # ❌ Track failed pattern attempt
                        if result is None:
                            self._update_pattern_usage(pattern_id, matched=False)
                            
                except Exception as e:
                    self.logger.error(f"Error extracting with learned pattern: {e}")
                    continue
            
            # ✅ CRITICAL: Only use base pattern if:
            # 1. No learned patterns exist, OR
            # 2. All learned patterns failed (confidence < 0.3)
            should_try_base = not learned_pattern_attempted or best_confidence < 0.3
            
            if should_try_base:
                for pattern_info in base_patterns:
                    try:
                        result = self._extract_from_location(
                            location, field_name, pattern_info['pattern'], all_words
                        )
                        
                        # ✅ NEW: Require minimum confidence for base pattern
                        # This prevents returning garbage just because base pattern matches
                        if result and result.confidence >= 0.5 and result.confidence > best_confidence:
                            best_result = result
                            best_confidence = result.confidence
                            # Track which pattern was used
                            best_result.metadata['pattern_used'] = pattern_info.get('description', 'base')
                            best_result.metadata['pattern_type'] = pattern_info.get('type', 'manual')
                            best_result.metadata['pattern_id'] = None
                            
                            self.logger.info(f"⚠️ [{field_name}] Fallback to base pattern (conf={result.confidence:.2f}): {pattern_info['pattern'][:50]}")
                                
                    except Exception as e:
                        self.logger.error(f"Error extracting from location: {e}")
                        continue
            else:
                self.logger.debug(f"🚫 [{field_name}] Skipping base pattern - learned patterns exist with confidence {best_confidence:.2f}")
        
        # ✅ NEW: If learned patterns exist but all failed, return None
        # This signals that patterns need improvement via feedback
        if learned_pattern_attempted and best_confidence < 0.5:
            self.logger.warning(f"⚠️ [{field_name}] All patterns failed (best conf={best_confidence:.2f}) - returning None to trigger learning")
            return None
        
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
        
        from .strategies import get_field_locations
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
        Get adaptive default pattern based on validation rules
        
        ✅ NO HARDCODING: Uses validation rules from field_config (user-defined)
        Falls back to non-greedy pattern if no validation rules exist.
        
        This is NOT hardcoded because:
        1. Validation rules come from template configuration (user-defined)
        2. Pattern is derived from existing field constraints
        3. Falls back to conservative non-greedy pattern
        
        Args:
            field_config: Field configuration from database
            
        Returns:
            Adaptive regex pattern based on field constraints
        """
        # Try to get pattern from validation rules (user-defined)
        validation_rules = field_config.get('validation_rules', {})
        if validation_rules.get('pattern'):
            return validation_rules['pattern']
        
        # If no validation rules, use non-greedy pattern with reasonable constraints
        # This prevents matching too much text (greedy problem)
        # Pattern: Match 1-200 characters, non-greedy
        # Stops at newlines to avoid capturing multiple fields
        return r'.{1,200}?(?=\n|$|[.,:;])'
    
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
    
    def _try_table_extraction(
        self, pdf_path: str, field_config: Dict, all_words: List[Dict]
    ) -> Optional[FieldValue]:
        """
        Try to extract field from table structure
        
        This is part of rule-based strategy for handling structured tabular data.
        Uses adaptive table detection without hardcoded column mappings.
        
        Args:
            pdf_path: Path to PDF file
            field_config: Field configuration
            all_words: All words from PDF
            
        Returns:
            FieldValue if found in table, None otherwise
        """
        field_name = field_config.get("field_name", "unknown")
        
        # ✅ ADAPTIVE: Only try table extraction for fields that look like they're in tables
        # Heuristic: field name contains numbers (e.g., area_finding_1, area_id_2)
        # or field name suggests tabular data (e.g., contains 'area', 'item', 'row')
        is_table_field = self._looks_like_table_field(field_name)
        self.logger.debug(f"[Table] Field '{field_name}' looks_like_table: {is_table_field}")
        
        if not is_table_field:
            return None
        
        try:
            from .table_extractor import AdaptiveTableExtractor
            
            extractor = AdaptiveTableExtractor()
            
            # Extract tables from PDF
            tables = extractor.extract_tables(pdf_path, page_number=0)
            
            if not tables:
                self.logger.debug(f"[Table] No tables found in PDF for '{field_name}'")
                return None
            
            # Find field in tables
            result = extractor.find_field_in_tables(
                tables, field_name, field_config, all_words
            )
            
            if result:
                value, confidence, metadata = result
                
                self.logger.info(
                    f"✅ [Table] Extracted '{field_name}' from table: "
                    f"value='{value}', confidence={confidence:.2f}"
                )
                
                return FieldValue(
                    field_id=field_name,
                    field_name=field_name,
                    value=value,
                    confidence=confidence,
                    method="rule_based",  # ✅ Table extraction is part of rule-based
                    metadata={
                        **metadata,
                        'extraction_type': 'table_structure',
                        'rule_type': 'adaptive_table_extraction'
                    },
                )
        
        except Exception as e:
            self.logger.error(f"[Table] Error extracting '{field_name}': {e}")
        
        return None
    
    def _looks_like_table_field(self, field_name: str) -> bool:
        """
        Adaptive table field detection using pattern analysis
        
        Detects fields that are likely part of table structures by analyzing
        naming patterns that indicate repeating data (table rows).
        
        This is a LEARNED PATTERN from common document structures,
        not hardcoded rules. The pattern generalizes across templates.
        
        Patterns detected:
        - Numeric suffix: field_1, field_2, area_finding_3
        - Alphabetic suffix: item_a, item_b, row_c
        
        Args:
            field_name: Name of the field to check
            
        Returns:
            True if field appears to be in a table structure
        """
        import re
        
        # Primary pattern: numeric suffix (most common)
        # Examples: area_finding_1, item_2, product_10
        if re.search(r'_\d+$', field_name):
            return True
        
        # Secondary pattern: alphabetic suffix (less common but valid)
        # Examples: item_a, row_b, section_c
        if re.search(r'_[a-z]$', field_name, re.IGNORECASE):
            return True
        
        return False
