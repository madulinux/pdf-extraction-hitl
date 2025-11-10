"""
Adaptive Post-Processor for Extraction Results

This module provides pattern-based post-processing that learns from feedback,
NOT hardcoded rules. It analyzes feedback history to identify common noise
patterns and applies learned cleaning rules.

Key Principles:
1. Pattern-based, not hardcoded
2. Learns from feedback data
3. Template-specific patterns
4. No field-specific logic
"""

import re
import json
from typing import Dict, List, Any, Optional
from collections import Counter
from pathlib import Path


class AdaptivePostProcessor:
    """
    Post-processor that learns cleaning patterns from feedback
    
    This class analyzes feedback history to identify common patterns
    of noise (prefixes, suffixes, structural markers) and applies
    learned cleaning rules to improve extraction accuracy.
    
    IMPORTANT: This is NOT hardcoded! Patterns are learned from data.
    """
    
    def __init__(self, template_id: int, db_manager=None):
        """
        Initialize post-processor
        
        Args:
            template_id: Template ID
            db_manager: Database manager instance (optional)
        """
        self.template_id = template_id
        self.db = db_manager
        self.learned_patterns = self._load_patterns_from_database()
    
    def reload_patterns(self) -> None:
        """
        Reload learned patterns from database
        
        This should be called before each extraction to ensure
        the latest learned patterns are used.
        """
        self.learned_patterns = self._load_patterns_from_database()
    
    def _load_patterns_from_database(self) -> Dict:
        """
        Load pattern statistics from database
        
        Returns:
            Dictionary of learned patterns per field
        """
        if not self.db:
            return {}
        
        try:
            from database.repositories.config_repository import ConfigRepository
            config_repo = ConfigRepository(self.db)
            
            # Get all pattern statistics for this template
            patterns = config_repo.get_all_pattern_statistics(
                template_id=self.template_id,
                active_only=True
            )
            
            return patterns
        
        except Exception as e:
            print(f"⚠️ Could not load pattern statistics from database: {e}")
            # Fallback to old method
            return self._load_or_learn_patterns()
    
    def _load_or_learn_patterns(self) -> Dict:
        """
        DEPRECATED: Load cached patterns or learn from feedback
        
        This is kept for backward compatibility only.
        New code should use _load_patterns_from_database()
        
        Returns:
            Dictionary of learned patterns per field
        """
        # Try to load cached patterns
        cache_path = Path(f"models/template_{self.template_id}_patterns.json")
        
        if cache_path.exists():
            try:
                with open(cache_path, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        
        # Learn patterns from feedback if DB available
        if self.db:
            return self._learn_patterns_from_feedback()
        
        return {}
    
    def _learn_patterns_from_feedback(self) -> Dict:
        """
        Analyze feedback to learn common noise patterns
        
        Returns:
            Dictionary of patterns per field
        """
        # Get all feedbacks for this template
        feedbacks = self._get_template_feedbacks()
        
        if not feedbacks:
            return {}
        
        patterns = {}
        
        # Group by field_name
        fields = set(f['field_name'] for f in feedbacks)
        
        for field_name in fields:
            field_feedbacks = [f for f in feedbacks if f['field_name'] == field_name]
            
            patterns[field_name] = {
                'common_prefixes': self._find_common_prefixes(field_feedbacks),
                'common_suffixes': self._find_common_suffixes(field_feedbacks),
                'structural_noise': self._find_structural_noise(field_feedbacks),
                'sample_count': len(field_feedbacks)
            }
        
        # Cache patterns
        self._cache_patterns(patterns)
        
        return patterns
    
    def _get_template_feedbacks(self) -> List[Dict]:
        """
        Get all feedbacks for this template
        
        Returns:
            List of feedback dictionaries
        """
        if not self.db:
            return []
        
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT f.field_name, f.original_value, f.corrected_value
                FROM feedback f
                JOIN documents d ON f.document_id = d.id
                WHERE d.template_id = ?
                AND f.original_value IS NOT NULL
                AND f.corrected_value IS NOT NULL
                AND f.original_value != f.corrected_value
            ''', (self.template_id,))
            
            feedbacks = []
            for row in cursor.fetchall():
                feedbacks.append({
                    'field_name': row['field_name'],
                    'original_value': row['original_value'],
                    'corrected_value': row['corrected_value']
                })
            
            conn.close()
            return feedbacks
        except Exception as e:
            # Database might be empty or table doesn't exist yet
            print(f"⚠️ Could not load feedbacks: {e}")
            return []
    
    def _find_common_prefixes(self, feedbacks: List[Dict]) -> List[str]:
        """
        Find common prefixes that were removed in corrections
        
        Args:
            feedbacks: List of feedback for a specific field
            
        Returns:
            List of common prefixes (frequency > 10%)
        """
        prefixes = []
        
        for fb in feedbacks:
            original = str(fb['original_value']).strip()
            corrected = str(fb['corrected_value']).strip()
            
            # If corrected is substring of original (at the end)
            if corrected and corrected in original:
                idx = original.find(corrected)
                if idx > 0:
                    # Extract prefix
                    prefix = original[:idx].strip()
                    if prefix:
                        prefixes.append(prefix.lower())
        
        # Count frequency
        counter = Counter(prefixes)
        threshold = max(2, len(feedbacks) * 0.1)  # At least 2 occurrences or 10%
        
        return [p for p, count in counter.most_common(10) if count >= threshold]
    
    def _find_common_suffixes(self, feedbacks: List[Dict]) -> List[str]:
        """
        Find common suffixes that were removed in corrections
        
        Args:
            feedbacks: List of feedback for a specific field
            
        Returns:
            List of common suffixes (frequency > 10%)
        """
        suffixes = []
        
        for fb in feedbacks:
            original = str(fb['original_value']).strip()
            corrected = str(fb['corrected_value']).strip()
            
            # If corrected is substring of original (at the beginning)
            if corrected and corrected in original:
                idx = original.find(corrected)
                end_idx = idx + len(corrected)
                if end_idx < len(original):
                    # Extract suffix
                    suffix = original[end_idx:].strip()
                    if suffix:
                        suffixes.append(suffix.lower())
        
        # Count frequency
        counter = Counter(suffixes)
        threshold = max(2, len(feedbacks) * 0.1)
        
        return [s for s, count in counter.most_common(10) if count >= threshold]
    
    def _find_structural_noise(self, feedbacks: List[Dict]) -> Dict:
        """
        Find common structural noise patterns (parentheses, quotes, etc.)
        
        Args:
            feedbacks: List of feedback for a specific field
            
        Returns:
            Dictionary of structural noise patterns
        """
        patterns = {
            'has_parentheses_both': 0,  # Both start and end
            'has_parentheses_start': 0,  # Only start
            'has_parentheses_end': 0,    # Only end
            'has_quotes': 0,
            'has_brackets': 0,
            'has_trailing_comma': 0,     # ✅ NEW: Trailing comma
            'has_trailing_period': 0,    # ✅ NEW: Trailing period
        }
        
        for fb in feedbacks:
            original = str(fb['original_value']).strip()
            corrected = str(fb['corrected_value']).strip()
            
            # Check if parentheses were removed
            orig_start_paren = original.startswith('(')
            orig_end_paren = original.endswith(')')
            corr_start_paren = corrected.startswith('(')
            corr_end_paren = corrected.endswith(')')
            
            if orig_start_paren and orig_end_paren:
                if not (corr_start_paren and corr_end_paren):
                    patterns['has_parentheses_both'] += 1
            elif orig_start_paren and not orig_end_paren:
                if not corr_start_paren:
                    patterns['has_parentheses_start'] += 1
            elif not orig_start_paren and orig_end_paren:
                if not corr_end_paren:
                    patterns['has_parentheses_end'] += 1
            
            # Check if quotes were removed
            if original.startswith('"') and original.endswith('"'):
                if not (corrected.startswith('"') and corrected.endswith('"')):
                    patterns['has_quotes'] += 1
            
            # Check if brackets were removed
            if original.startswith('[') and original.endswith(']'):
                if not (corrected.startswith('[') and corrected.endswith(']')):
                    patterns['has_brackets'] += 1
            
            # ✅ NEW: Check if trailing punctuation was removed
            if original.endswith(',') and not corrected.endswith(','):
                patterns['has_trailing_comma'] += 1
            
            if original.endswith('.') and not corrected.endswith('.'):
                patterns['has_trailing_period'] += 1
        
        return patterns
    
    def _cache_patterns(self, patterns: Dict):
        """
        Cache learned patterns to file
        
        Args:
            patterns: Patterns dictionary to cache
        """
        cache_path = Path(f"models/template_{self.template_id}_patterns.json")
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(cache_path, 'w') as f:
                json.dump(patterns, f, indent=2)
        except Exception as e:
            print(f"⚠️ Failed to cache patterns: {e}")
    
    def clean_value(self, field_name: str, value: str, context: Dict = None) -> str:
        """
        Clean extracted value using learned patterns
        
        Args:
            field_name: Name of the field
            value: Extracted value to clean
            context: Optional context (PDF words, etc.)
            
        Returns:
            Cleaned value
        """
        if not value or not isinstance(value, str):
            return value
        
        original_value = value
        
        # 1. Remove structural noise (learned from feedback)
        value = self._remove_structural_noise(field_name, value)
        
        # 2. Remove learned prefixes/suffixes
        value = self._remove_learned_noise(field_name, value)
        
        # 3. Clean whitespace
        value = self._clean_whitespace(value)
        
        # Log if changed
        if value != original_value:
            print(f"   🧹 Cleaned {field_name}: '{original_value}' → '{value}'")
        
        return value
    
    def _remove_structural_noise(self, field_name: str, value: str) -> str:
        """
        Remove structural noise based on learned patterns
        
        Args:
            field_name: Field name
            value: Value to clean
            
        Returns:
            Cleaned value
        """
        patterns = self.learned_patterns.get(field_name, {})
        structural = patterns.get('structural_noise', {})
        
        # ✅ IMPROVED: Remove parentheses based on learned patterns
        # Both start and end
        if structural.get('has_parentheses_both', 0) > 0:
            if value.startswith('(') and value.endswith(')'):
                value = value[1:-1].strip()
        
        # Only start
        if structural.get('has_parentheses_start', 0) > 0:
            if value.startswith('(') and not value.endswith(')'):
                value = value[1:].strip()
        
        # Only end
        if structural.get('has_parentheses_end', 0) > 0:
            if not value.startswith('(') and value.endswith(')'):
                value = value[:-1].strip()
        
        # Remove quotes if learned pattern
        if structural.get('has_quotes', 0) > 0:
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1].strip()
        
        # Remove brackets if learned pattern
        if structural.get('has_brackets', 0) > 0:
            if value.startswith('[') and value.endswith(']'):
                value = value[1:-1].strip()
        
        # ✅ NEW: Remove trailing punctuation if learned pattern
        if structural.get('has_trailing_comma', 0) > 0:
            if value.endswith(','):
                value = value[:-1].strip()
        
        if structural.get('has_trailing_period', 0) > 0:
            if value.endswith('.'):
                value = value[:-1].strip()
        
        return value
    
    def _remove_learned_noise(self, field_name: str, value: str) -> str:
        """
        Remove noise based on learned prefix/suffix patterns
        
        Args:
            field_name: Field name
            value: Value to clean
            
        Returns:
            Cleaned value
        """
        patterns = self.learned_patterns.get(field_name, {})
        
        # Remove common prefixes (case-insensitive)
        for prefix in patterns.get('common_prefixes', []):
            if value.lower().startswith(prefix):
                value = value[len(prefix):].strip()
                # Remove quotes/parentheses after prefix removal
                value = value.strip('"').strip('(').strip(')').strip()
                break  # Only remove one prefix
        
        # Remove common suffixes (case-insensitive + pattern matching)
        for suffix in patterns.get('common_suffixes', []):
            # Handle generalized patterns (case-insensitive)
            suffix_lower = suffix.lower()
            if '[date]' in suffix_lower:
                # Match any date pattern: ", DD Month YYYY"
                import re
                # Escape special regex chars except [date]
                pattern = re.escape(suffix)
                pattern = pattern.replace(r'\[date\]', r'\d{1,2}\s+\w+\s+\d{4}')
                pattern = pattern.replace(r'\[DATE\]', r'\d{1,2}\s+\w+\s+\d{4}')
                if re.search(pattern, value, re.IGNORECASE):
                    value = re.sub(pattern, '', value, flags=re.IGNORECASE).strip()
                    value = value.strip('"').strip('(').strip(')').strip()
                    break
            elif '[name]' in suffix_lower:
                # Match any name pattern: ") (Name" (may not have closing paren)
                import re
                # Escape special regex chars except [name]
                pattern = re.escape(suffix)
                pattern = pattern.replace(r'\[name\]', r'.+')
                pattern = pattern.replace(r'\[NAME\]', r'.+')
                if re.search(pattern, value):
                    value = re.sub(pattern, '', value).strip()
                    value = value.strip('"').strip('(').strip(')').strip()
                    break
            elif value.lower().endswith(suffix_lower):
                # Exact match
                value = value[:-len(suffix)].strip()
                value = value.strip('"').strip('(').strip(')').strip()
                break
        
        return value
    
    def _clean_whitespace(self, value: str) -> str:
        """
        Clean excessive whitespace
        
        Args:
            value: Value to clean
            
        Returns:
            Cleaned value
        """
        # Replace multiple spaces with single space
        value = re.sub(r' +', ' ', value)
        
        # Remove leading/trailing whitespace
        value = value.strip()
        
        return value
    
    def process_results(self, results: Dict) -> Dict:
        """
        Process all extraction results
        
        Args:
            results: Extraction results dictionary
            
        Returns:
            Processed results
        """
        print(f"🧹 [PostProcessor] process_results called with {len(results.get('extracted_data', {}))} fields")
        
        if 'extracted_data' not in results:
            print(f"⚠️ [PostProcessor] No extracted_data in results!")
            return results
        
        extracted_data = results['extracted_data']
        cleaned_count = 0
        
        # Clean each field
        for field_name, value in extracted_data.items():
            if isinstance(value, str):
                cleaned = self.clean_value(field_name, value)
                if cleaned != value:
                    print(f"   🧹 Cleaned {field_name}: '{value}' → '{cleaned}'")
                    cleaned_count += 1
                extracted_data[field_name] = cleaned
        
        print(f"✅ [PostProcessor] Cleaned {cleaned_count}/{len(extracted_data)} fields")
        results['extracted_data'] = extracted_data
        
        return results
    
    def learn_from_feedback(
        self,
        extraction_results: Dict[str, Any],
        corrections: Dict[str, str]
    ) -> None:
        """
        Learn cleaning patterns from user feedback
        
        This method analyzes the differences between extracted values and
        corrected values to identify common noise patterns (prefixes, suffixes,
        structural markers like parentheses, quotes, etc.)
        
        Args:
            extraction_results: Original extraction results
            corrections: Dictionary of corrections {field_name: corrected_value}
        """
        if not self.db:
            return
        
        extracted_data = extraction_results.get('extracted_data', {})
        
        # Analyze each correction to identify patterns
        for field_name, corrected_value in corrections.items():
            original_value = extracted_data.get(field_name, '')
            
            if not original_value or not corrected_value:
                continue
            
            # Analyze structural noise (parentheses, quotes, etc.)
            self._analyze_structural_noise(field_name, original_value, corrected_value)
            
            # Analyze prefix/suffix patterns
            self._analyze_prefix_suffix(field_name, original_value, corrected_value)
        
        # Re-learn patterns from all feedback (force reload from database)
        if self.db:
            self.learned_patterns = self._learn_patterns_from_feedback()
        else:
            self.learned_patterns = self._load_or_learn_patterns()
    
    def _analyze_structural_noise(
        self,
        field_name: str,
        original: str,
        corrected: str
    ) -> None:
        """
        Analyze structural noise patterns (parentheses, quotes, trailing punctuation)
        
        Args:
            field_name: Field name
            original: Original extracted value
            corrected: Corrected value
        """
        # Check for parentheses removal
        if original.startswith('(') and original.endswith(')'):
            if corrected == original[1:-1].strip():
                print(f"  📝 Learned: {field_name} has extra parentheses (both)")
        
        # Check for quote removal
        if original.startswith('"') and original.endswith('"'):
            if corrected == original[1:-1].strip():
                print(f"  📝 Learned: {field_name} has extra quotes")
        
        # Check for trailing comma removal
        if original.endswith(',') and not corrected.endswith(','):
            if corrected == original[:-1].strip():
                print(f"  📝 Learned: {field_name} has trailing comma")
        
        # Check for trailing period removal
        if original.endswith('.') and not corrected.endswith('.'):
            if corrected == original[:-1].strip():
                print(f"  📝 Learned: {field_name} has trailing period")
    
    def _analyze_prefix_suffix(
        self,
        field_name: str,
        original: str,
        corrected: str
    ) -> None:
        """
        Analyze prefix/suffix patterns
        
        Args:
            field_name: Field name
            original: Original extracted value
            corrected: Corrected value
        """
        # Check if corrected is a substring of original
        if corrected in original:
            # Find prefix
            prefix_idx = original.index(corrected)
            if prefix_idx > 0:
                prefix = original[:prefix_idx]
                print(f"  📝 Learned: {field_name} has prefix '{prefix}'")
            
            # Find suffix
            suffix_idx = prefix_idx + len(corrected)
            if suffix_idx < len(original):
                suffix = original[suffix_idx:]
                print(f"  📝 Learned: {field_name} has suffix '{suffix}'")
