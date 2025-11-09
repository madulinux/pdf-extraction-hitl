"""
Adaptive Rule-Based Pattern Optimizer

Learns new regex patterns and position adjustments from user feedback.
Aligned with thesis objectives:
- Tujuan 1: Model pembelajaran adaptif yang meningkatkan akurasi
- Tujuan 2: Integrasi pendekatan berbasis aturan dan pembelajaran mesin
- Tujuan 3: Mekanisme feedback untuk perbaikan berkelanjutan
"""
import logging
import re
import json
from typing import Dict, List, Optional, Set, Tuple
from collections import Counter, defaultdict
from datetime import datetime
import os


class RulePatternOptimizer:
    """
    Analyzes feedback to discover and suggest new regex patterns
    for rule-based extraction strategy.
    
    Now integrated with database for persistent pattern storage.
    """
    
    def __init__(self, db_manager=None, config_repository=None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.db = db_manager
        self.config_repo = config_repository
        
        # Initialize config repository if not provided
        if self.db and not self.config_repo:
            from database.repositories.config_repository import ConfigRepository
            self.config_repo = ConfigRepository(self.db)
        
    def analyze_feedback_patterns(
        self,
        template_id: int,
        field_name: str,
        min_frequency: int = 3
    ) -> Dict:
        """
        Analyze feedback to discover common patterns
        
        Args:
            template_id: Template ID
            field_name: Field name to analyze
            min_frequency: Minimum occurrences to consider a pattern
            
        Returns:
            Dict with pattern suggestions and statistics
        """
        if not self.db:
            self.logger.warning("No database manager provided")
            return {}
        
        self.logger.info(f"🔍 Analyzing feedback patterns for {field_name} (template {template_id})")
        
        # Get all feedback for this field
        query = """
            SELECT f.corrected_value, f.raw_value, f.field_name,
                   d.file_path
            FROM feedback f
            JOIN documents d ON f.document_id = d.id
            WHERE d.template_id = ? AND f.field_name = ?
            ORDER BY f.created_at DESC
        """
        
        cursor = self.db.conn.execute(query, (template_id, field_name))
        feedbacks = cursor.fetchall()
        
        if not feedbacks:
            self.logger.info(f"No feedback found for {field_name}")
            return {}
        
        self.logger.info(f"Found {len(feedbacks)} feedback entries")
        
        # Analyze patterns
        corrected_values = [f[0] for f in feedbacks if f[0]]
        raw_values = [f[1] for f in feedbacks if f[1]]
        
        analysis = {
            'field_name': field_name,
            'template_id': template_id,
            'total_feedback': len(feedbacks),
            'unique_corrected': len(set(corrected_values)),
            'patterns': self._discover_patterns(corrected_values, min_frequency),
            'common_errors': self._analyze_extraction_errors(raw_values, corrected_values),
            'suggestions': []
        }
        
        # Generate regex suggestions
        analysis['suggestions'] = self._generate_regex_suggestions(
            analysis['patterns'],
            corrected_values
        )
        
        return analysis
    
    def _discover_patterns(
        self,
        values: List[str],
        min_frequency: int
    ) -> Dict:
        """
        Discover common patterns in corrected values
        
        Returns:
            Dict with pattern types and examples
        """
        patterns = {
            'token_shapes': Counter(),
            'delimiters': Counter(),
            'lengths': Counter(),
            'prefixes': Counter(),
            'suffixes': Counter(),
            'word_counts': Counter()
        }
        
        for value in values:
            if not value:
                continue
            
            # Token shape (e.g., "Aa" for "Jakarta", "9" for "123")
            shape = self._get_token_shape(value)
            patterns['token_shapes'][shape] += 1
            
            # Delimiters
            delimiters = re.findall(r'[,.\-/\\:;]', value)
            for delim in delimiters:
                patterns['delimiters'][delim] += 1
            
            # Length
            patterns['lengths'][len(value)] += 1
            
            # Prefix (first 3 chars)
            if len(value) >= 3:
                patterns['prefixes'][value[:3]] += 1
            
            # Suffix (last 3 chars)
            if len(value) >= 3:
                patterns['suffixes'][value[-3:]] += 1
            
            # Word count
            word_count = len(value.split())
            patterns['word_counts'][word_count] += 1
        
        # Filter by frequency
        filtered = {}
        for key, counter in patterns.items():
            filtered[key] = {
                k: v for k, v in counter.most_common()
                if v >= min_frequency
            }
        
        return filtered
    
    def _get_token_shape(self, text: str) -> str:
        """
        Get token shape pattern
        Examples:
            "Jakarta" -> "Aa+"
            "123" -> "9+"
            "ABC-123" -> "A+-9+"
        """
        shape = []
        prev_type = None
        
        for char in text:
            if char.isupper():
                char_type = 'A'
            elif char.islower():
                char_type = 'a'
            elif char.isdigit():
                char_type = '9'
            elif char.isspace():
                char_type = ' '
            else:
                char_type = char  # Keep special chars as-is
            
            if char_type == prev_type and char_type in ['A', 'a', '9']:
                if not shape[-1].endswith('+'):
                    shape[-1] += '+'
            else:
                shape.append(char_type)
                prev_type = char_type
        
        return ''.join(shape)
    
    def _analyze_extraction_errors(
        self,
        raw_values: List[str],
        corrected_values: List[str]
    ) -> Dict:
        """
        Analyze common extraction errors
        
        Returns:
            Dict with error patterns
        """
        errors = {
            'too_long': 0,
            'too_short': 0,
            'extra_prefix': [],
            'extra_suffix': [],
            'missing_parts': 0
        }
        
        for raw, corrected in zip(raw_values, corrected_values):
            if not raw or not corrected:
                continue
            
            # Length comparison
            if len(raw) > len(corrected) * 1.5:
                errors['too_long'] += 1
                
                # Check for extra prefix
                if corrected in raw:
                    idx = raw.index(corrected)
                    if idx > 0:
                        prefix = raw[:idx].strip()
                        if prefix:
                            errors['extra_prefix'].append(prefix)
                    
                    # Check for extra suffix
                    end_idx = idx + len(corrected)
                    if end_idx < len(raw):
                        suffix = raw[end_idx:].strip()
                        if suffix:
                            errors['extra_suffix'].append(suffix)
            
            elif len(raw) < len(corrected) * 0.5:
                errors['too_short'] += 1
                errors['missing_parts'] += 1
        
        # Get most common extra prefixes/suffixes
        if errors['extra_prefix']:
            errors['common_prefixes'] = [
                p for p, c in Counter(errors['extra_prefix']).most_common(5)
            ]
        
        if errors['extra_suffix']:
            errors['common_suffixes'] = [
                s for s, c in Counter(errors['extra_suffix']).most_common(5)
            ]
        
        return errors
    
    def _generate_regex_suggestions(
        self,
        patterns: Dict,
        sample_values: List[str]
    ) -> List[Dict]:
        """
        Generate regex pattern suggestions based on discovered patterns
        
        Returns:
            List of regex suggestions with metadata
        """
        suggestions = []
        
        # Suggestion 1: Based on token shapes
        if patterns.get('token_shapes'):
            for shape, freq in list(patterns['token_shapes'].items())[:3]:
                regex = self._shape_to_regex(shape)
                suggestions.append({
                    'type': 'token_shape',
                    'pattern': regex,
                    'description': f'Matches shape: {shape}',
                    'frequency': freq,
                    'examples': [v for v in sample_values if self._get_token_shape(v) == shape][:3]
                })
        
        # Suggestion 2: Based on word counts
        if patterns.get('word_counts'):
            for word_count, freq in list(patterns['word_counts'].items())[:2]:
                if word_count == 1:
                    regex = r'\S+'
                    desc = 'Single word'
                elif word_count == 2:
                    regex = r'\S+\s+\S+'
                    desc = 'Two words'
                else:
                    regex = r'(?:\S+\s+){' + str(word_count-1) + r'}\S+'
                    desc = f'{word_count} words'
                
                suggestions.append({
                    'type': 'word_count',
                    'pattern': regex,
                    'description': desc,
                    'frequency': freq,
                    'examples': [v for v in sample_values if len(v.split()) == word_count][:3]
                })
        
        # Suggestion 3: Based on delimiters
        if patterns.get('delimiters'):
            for delim, freq in list(patterns['delimiters'].items())[:2]:
                escaped_delim = re.escape(delim)
                regex = r'[^' + escaped_delim + r']+(?:' + escaped_delim + r'[^' + escaped_delim + r']+)*'
                
                suggestions.append({
                    'type': 'delimiter',
                    'pattern': regex,
                    'description': f'Text with {delim} delimiter',
                    'frequency': freq,
                    'examples': [v for v in sample_values if delim in v][:3]
                })
        
        return suggestions
    
    def _shape_to_regex(self, shape: str) -> str:
        """
        Convert token shape to regex pattern
        
        Examples:
            "Aa+" -> r"[A-Z][a-z]+"
            "9+" -> r"\d+"
            "A+-9+" -> r"[A-Z]+-\d+"
        """
        regex_parts = []
        i = 0
        
        while i < len(shape):
            char = shape[i]
            
            # Check if next char is '+'
            is_repeated = (i + 1 < len(shape) and shape[i + 1] == '+')
            
            if char == 'A':
                regex_parts.append('[A-Z]+' if is_repeated else '[A-Z]')
                i += 2 if is_repeated else 1
            elif char == 'a':
                regex_parts.append('[a-z]+' if is_repeated else '[a-z]')
                i += 2 if is_repeated else 1
            elif char == '9':
                regex_parts.append(r'\d+' if is_repeated else r'\d')
                i += 2 if is_repeated else 1
            elif char == ' ':
                regex_parts.append(r'\s+')
                i += 1
            else:
                # Special character - escape it
                regex_parts.append(re.escape(char))
                i += 1
        
        return ''.join(regex_parts)
    
    def update_template_config(
        self,
        config_path: str,
        field_name: str,
        new_patterns: List[Dict],
        backup: bool = True
    ) -> bool:
        """
        Update template configuration with new patterns
        
        Args:
            config_path: Path to template config JSON
            field_name: Field to update
            new_patterns: List of pattern dicts with 'pattern' and 'description'
            backup: Create backup before updating
            
        Returns:
            True if successful
        """
        try:
            # Load current config
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Backup if requested
            if backup:
                backup_path = f"{config_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                with open(backup_path, 'w') as f:
                    json.dump(config, f, indent=2)
                self.logger.info(f"📦 Backup created: {backup_path}")
            
            # Update field patterns
            if 'fields' not in config:
                config['fields'] = {}
            
            if field_name not in config['fields']:
                config['fields'][field_name] = {}
            
            if 'rules' not in config['fields'][field_name]:
                config['fields'][field_name]['rules'] = {}
            
            if 'learned_patterns' not in config['fields'][field_name]['rules']:
                config['fields'][field_name]['rules']['learned_patterns'] = []
            
            # Add new patterns with metadata
            for pattern_info in new_patterns:
                pattern_entry = {
                    'pattern': pattern_info['pattern'],
                    'description': pattern_info.get('description', ''),
                    'type': pattern_info.get('type', 'learned'),
                    'frequency': pattern_info.get('frequency', 0),
                    'added_at': datetime.now().isoformat(),
                    'examples': pattern_info.get('examples', [])[:3]  # Keep max 3 examples
                }
                
                # Check if pattern already exists
                existing = config['fields'][field_name]['rules']['learned_patterns']
                if not any(p['pattern'] == pattern_entry['pattern'] for p in existing):
                    existing.append(pattern_entry)
                    self.logger.info(f"✅ Added pattern: {pattern_entry['pattern']}")
            
            # Save updated config
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            self.logger.info(f"💾 Config updated: {config_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update config: {e}")
            return False
    
    def apply_patterns_to_db(
        self,
        template_id: int,
        field_name: str,
        patterns: List[Dict],
        job_type: str = 'auto'
    ) -> Dict:
        """
        Apply learned patterns directly to database
        
        Args:
            template_id: Template ID
            field_name: Field name
            patterns: List of pattern dicts
            job_type: Job type (auto, manual, scheduled)
            
        Returns:
            Dict with results
        """
        if not self.config_repo:
            self.logger.error("Config repository not initialized")
            return {'success': False, 'error': 'No config repository'}
        
        try:
            # Create learning job
            job_id = self.config_repo.create_learning_job(
                template_id=template_id,
                field_name=field_name,
                job_type=job_type
            )
            
            self.config_repo.update_learning_job(
                job_id=job_id,
                status='running'
            )
            
            # Get active config
            config = self.config_repo.get_active_config(template_id)
            if not config:
                # Create new config if doesn't exist
                config_id = self.config_repo.create_config(
                    template_id=template_id,
                    description=f"Auto-created for pattern learning",
                    created_by='system'
                )
            else:
                config_id = config['id']
            
            # Get or create field config
            field_config = self.config_repo.get_field_config_by_name(
                config_id=config_id,
                field_name=field_name
            )
            
            if not field_config:
                self.logger.warning(f"Field config not found for {field_name}, skipping")
                self.config_repo.update_learning_job(
                    job_id=job_id,
                    status='failed',
                    error_message=f"Field config not found: {field_name}"
                )
                return {'success': False, 'error': 'Field config not found'}
            
            field_config_id = field_config['id']
            
            # Add patterns to database
            patterns_added = 0
            for pattern_info in patterns:
                try:
                    pattern_id = self.config_repo.add_learned_pattern(
                        field_config_id=field_config_id,
                        pattern=pattern_info['pattern'],
                        pattern_type=pattern_info.get('type', 'learned'),
                        description=pattern_info.get('description', ''),
                        frequency=pattern_info.get('frequency', 0),
                        match_rate=pattern_info.get('match_rate'),
                        priority=pattern_info.get('priority', 0),
                        examples=pattern_info.get('examples', [])[:3],
                        metadata=pattern_info.get('metadata', {})
                    )
                    patterns_added += 1
                    self.logger.info(f"✅ Added pattern {pattern_id}: {pattern_info['pattern'][:50]}")
                except Exception as e:
                    self.logger.error(f"Failed to add pattern: {e}")
            
            # Update job status
            self.config_repo.update_learning_job(
                job_id=job_id,
                status='completed',
                patterns_discovered=len(patterns),
                patterns_applied=patterns_added,
                result_summary={
                    'field_name': field_name,
                    'patterns_added': patterns_added,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            self.logger.info(f"✅ Applied {patterns_added}/{len(patterns)} patterns to database")
            
            return {
                'success': True,
                'job_id': job_id,
                'patterns_added': patterns_added,
                'field_config_id': field_config_id
            }
            
        except Exception as e:
            self.logger.error(f"Failed to apply patterns to database: {e}")
            if 'job_id' in locals():
                self.config_repo.update_learning_job(
                    job_id=job_id,
                    status='failed',
                    error_message=str(e)
                )
            return {'success': False, 'error': str(e)}
    
    def validate_patterns(
        self,
        patterns: List[str],
        test_values: List[str]
    ) -> Dict:
        """
        Validate regex patterns against test values
        
        Returns:
            Dict with validation results
        """
        results = {}
        
        for pattern in patterns:
            try:
                regex = re.compile(pattern)
                matches = 0
                examples = []
                
                for value in test_values:
                    match = regex.search(value)
                    if match:
                        matches += 1
                        if len(examples) < 3:
                            examples.append({
                                'value': value,
                                'matched': match.group(0)
                            })
                
                results[pattern] = {
                    'valid': True,
                    'matches': matches,
                    'match_rate': matches / len(test_values) if test_values else 0,
                    'examples': examples
                }
                
            except re.error as e:
                results[pattern] = {
                    'valid': False,
                    'error': str(e)
                }
        
        return results
