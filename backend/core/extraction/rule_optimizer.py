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
        
        # ✅ CRITICAL: Learn from BOTH feedback AND validated data (like CRF does!)
        # This ensures patterns are learned from ALL correct values, not just corrections
        
        # 1. Get corrected values from feedback
        query_feedback = """
            SELECT f.corrected_value, f.original_value
            FROM feedback f
            JOIN documents d ON f.document_id = d.id
            WHERE d.template_id = ? AND f.field_name = ?
            ORDER BY f.created_at DESC
        """
        
        feedbacks = self.db.execute_query(query_feedback, (template_id, field_name))
        corrected_values = [f['corrected_value'] for f in feedbacks if f.get('corrected_value')]
        original_values = [f['original_value'] for f in feedbacks if f.get('original_value')]
        
        self.logger.info(f"Found {len(feedbacks)} feedback entries")
        
        # 2. Get validated values (correct extractions without feedback)
        query_validated = """
            SELECT d.id, d.extraction_result
            FROM documents d
            WHERE d.template_id = ? 
              AND d.status = 'validated'
              AND d.id NOT IN (
                  SELECT DISTINCT document_id 
                  FROM feedback 
                  WHERE field_name = ?
              )
            ORDER BY d.created_at DESC
        """
        
        validated_docs = self.db.execute_query(query_validated, (template_id, field_name))
        
        # Extract field values from validated documents
        import json
        validated_values = []
        for doc in validated_docs:
            try:
                extraction_result = json.loads(doc['extraction_result'])
                extracted_data = extraction_result.get('extracted_data', {})
                if field_name in extracted_data:
                    value = extracted_data[field_name]
                    if value and value.strip():
                        validated_values.append(value.strip())
            except:
                continue
        
        self.logger.info(f"Found {len(validated_values)} validated values (no feedback)")
        
        # Combine corrected + validated values for pattern discovery
        all_correct_values = corrected_values + validated_values
        self.logger.info(f"Total values for pattern analysis: {len(all_correct_values)} (feedback: {len(corrected_values)}, validated: {len(validated_values)})")
        
        if not all_correct_values:
            self.logger.info(f"No values found for pattern analysis")
            return {}
        
        analysis = {
            'field_name': field_name,
            'template_id': template_id,
            'total_feedback': len(feedbacks),
            'total_validated': len(validated_values),
            'total_values': len(all_correct_values),
            'unique_corrected': len(set(corrected_values)),
            'patterns': self._discover_patterns(all_correct_values, min_frequency),  # ✅ Use ALL values
            'common_errors': self._analyze_extraction_errors(original_values, corrected_values),
            'suggestions': []
        }
        
        # Generate regex suggestions from ALL correct values
        analysis['suggestions'] = self._generate_regex_suggestions(
            analysis['patterns'],
            all_correct_values  # ✅ Use ALL values for examples
        )
        
        return analysis
    
    def _discover_patterns(
        self,
        values: List[str],
        min_frequency: int
    ) -> Dict:
        """
        ✅ IMPROVED: Intelligent pattern discovery with data analysis
        
        Steps:
        1. Collect all values and their characteristics
        2. Analyze distribution (word counts, shapes, etc.)
        3. Detect variability (fixed vs variable length)
        4. Generate appropriate patterns (flexible vs strict)
        
        Returns:
            Dict with pattern types, examples, and insights
        """
        if not values:
            return {}
        
        self.logger.info(f"🔍 Analyzing {len(values)} values for pattern discovery")
        
        # Step 1: Collect characteristics
        patterns = {
            'token_shapes': Counter(),
            'delimiters': Counter(),
            'lengths': Counter(),
            'prefixes': Counter(),
            'suffixes': Counter(),
            'word_counts': Counter()
        }
        
        # Store per-value data for analysis
        value_data = []
        
        for value in values:
            if not value:
                continue
            
            words = value.split()
            word_count = len(words)
            
            value_info = {
                'value': value,
                'word_count': word_count,
                'length': len(value),
                'shape': self._get_token_shape(value),
                'words': words
            }
            value_data.append(value_info)
            
            # Token shape
            patterns['token_shapes'][value_info['shape']] += 1
            
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
            patterns['word_counts'][word_count] += 1
        
        # Step 2: Analyze distribution and variability
        insights = self._analyze_data_distribution(value_data, patterns)
        
        # Step 3: Filter by frequency
        filtered = {}
        for key, counter in patterns.items():
            filtered[key] = {
                k: v for k, v in counter.most_common()
                if v >= min_frequency
            }
        
        # Add insights to result
        filtered['insights'] = insights
        filtered['sample_size'] = len(value_data)
        
        self.logger.info(
            f"📊 Pattern insights: "
            f"word_count_variability={insights.get('word_count_variability')}, "
            f"has_capitalized={insights.get('has_capitalized_words')}, "
            f"recommended_flexibility={insights.get('recommended_flexibility')}"
        )
        
        return filtered
    
    def _analyze_data_distribution(
        self,
        value_data: List[Dict],
        patterns: Dict
    ) -> Dict:
        """
        Analyze data distribution to determine pattern flexibility
        
        Returns:
            Dict with insights about the data
        """
        if not value_data:
            return {}
        
        word_counts = [v['word_count'] for v in value_data]
        unique_word_counts = set(word_counts)
        
        # Calculate word count statistics
        min_words = min(word_counts)
        max_words = max(word_counts)
        avg_words = sum(word_counts) / len(word_counts)
        
        # Determine variability
        word_count_range = max_words - min_words
        word_count_variability = 'high' if word_count_range > 2 else 'medium' if word_count_range > 0 else 'low'
        
        # Check if data has capitalized words
        has_capitalized = any(
            any(word[0].isupper() for word in v['words'] if word)
            for v in value_data
        )
        
        # Check word count distribution
        word_count_dist = Counter(word_counts)
        most_common_count = word_count_dist.most_common(1)[0][0] if word_count_dist else 0
        
        # Determine recommended flexibility
        if word_count_variability == 'high':
            # High variability: use flexible pattern (min-max range)
            recommended_flexibility = 'flexible_range'
            recommended_min = min_words
            recommended_max = max_words
        elif word_count_variability == 'medium':
            # Medium variability: use flexible pattern with limited range
            recommended_flexibility = 'flexible_limited'
            recommended_min = min_words
            recommended_max = max_words
        else:
            # Low variability: can use specific pattern
            recommended_flexibility = 'specific'
            recommended_min = most_common_count
            recommended_max = most_common_count
        
        insights = {
            'word_count_variability': word_count_variability,
            'word_count_range': word_count_range,
            'min_words': min_words,
            'max_words': max_words,
            'avg_words': round(avg_words, 1),
            'unique_word_counts': sorted(list(unique_word_counts)),
            'most_common_word_count': most_common_count,
            'has_capitalized_words': has_capitalized,
            'recommended_flexibility': recommended_flexibility,
            'recommended_min_words': recommended_min,
            'recommended_max_words': recommended_max,
            'sample_size': len(value_data)
        }
        
        return insights
    
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
        ✅ IMPROVED: Generate regex patterns based on data insights
        
        Uses insights from _analyze_data_distribution to generate
        appropriate patterns (flexible vs strict) based on actual data
        
        Returns:
            List of regex suggestions with metadata
        """
        suggestions = []
        insights = patterns.get('insights', {})
        
        # ✅ CRITICAL: Use insights to generate intelligent patterns
        if patterns.get('token_shapes') and insights:
            has_capitalized = insights.get('has_capitalized_words', False)
            
            if has_capitalized:
                min_words = insights.get('recommended_min_words', 1)
                max_words = insights.get('recommended_max_words', 3)
                flexibility = insights.get('recommended_flexibility', 'flexible_range')
                
                # Generate flexible pattern based on actual data distribution
                if flexibility == 'flexible_range' or flexibility == 'flexible_limited':
                    # Data has variability: use flexible pattern
                    # Pattern: [A-Z][a-z]+(?:\s+[A-Z][a-z]+){min-1,max-1}
                    
                    if min_words == max_words:
                        # Same min/max: specific pattern with capturing group
                        if min_words == 1:
                            flexible_pattern = r'([A-Z][a-z]+)'
                            description = 'Single capitalized word'
                        else:
                            repeat = min_words - 1
                            flexible_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){' + str(repeat) + '})'
                            description = f'{min_words} capitalized words'
                    else:
                        # Variable: flexible range with capturing group
                        min_repeat = max(0, min_words - 1)
                        max_repeat = max_words - 1
                        flexible_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){' + str(min_repeat) + ',' + str(max_repeat) + '})'
                        description = f'Flexible: {min_words}-{max_words} capitalized words'
                    
                    # Count total frequency
                    total_freq = sum(freq for shape, freq in patterns['token_shapes'].items() if 'Aa+' in shape)
                    
                    # Get examples
                    flexible_examples = [v for v in sample_values if re.fullmatch(flexible_pattern, v)][:5]
                    
                    suggestions.append({
                        'type': 'token_shape_flexible',
                        'pattern': flexible_pattern,
                        'description': description,
                        'frequency': total_freq,
                        'priority': 10,  # ✅ Highest priority
                        'examples': flexible_examples,
                        'insights': {
                            'min_words': min_words,
                            'max_words': max_words,
                            'flexibility': flexibility,
                            'word_count_variability': insights.get('word_count_variability')
                        }
                    })
                    
                    self.logger.info(
                        f"✅ Generated flexible pattern: {flexible_pattern} "
                        f"(words: {min_words}-{max_words}, variability: {insights.get('word_count_variability')})"
                    )
                
                else:
                    # Low variability: use specific pattern with capturing group
                    most_common = insights.get('most_common_word_count', 1)
                    
                    if most_common == 1:
                        specific_pattern = r'([A-Z][a-z]+)'
                        description = 'Single capitalized word'
                    else:
                        repeat = most_common - 1
                        specific_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){' + str(repeat) + '})'
                        description = f'{most_common} capitalized words'
                    
                    total_freq = sum(freq for shape, freq in patterns['token_shapes'].items() if 'Aa+' in shape)
                    specific_examples = [v for v in sample_values if re.fullmatch(specific_pattern, v)][:5]
                    
                    suggestions.append({
                        'type': 'token_shape_specific',
                        'pattern': specific_pattern,
                        'description': description,
                        'frequency': total_freq,
                        'priority': 10,
                        'examples': specific_examples,
                        'insights': {
                            'word_count': most_common,
                            'flexibility': flexibility
                        }
                    })
        
        # Suggestion 2: Based on specific token shapes (lower priority, for fallback)
        if patterns.get('token_shapes'):
            for shape, freq in list(patterns['token_shapes'].items())[:2]:  # Limit to top 2
                regex = self._shape_to_regex(shape)
                suggestions.append({
                    'type': 'token_shape',
                    'pattern': regex,
                    'description': f'Matches shape: {shape}',
                    'frequency': freq,
                    'priority': 5,  # Lower than flexible
                    'examples': [v for v in sample_values if self._get_token_shape(v) == shape][:3]
                })
        
        # Suggestion 2: Based on word counts (DISABLED - too rigid!)
        # ❌ PROBLEM: Exact word count patterns like (?:\S+\s+){7}\S+ are too specific
        # They fail when data has slight variations (e.g., "Jalan KH" prefix missing)
        # This causes accuracy to DROP after learning more data!
        # 
        # SOLUTION: Use flexible patterns instead (e.g., .+, [^,]+, etc.)
        # if patterns.get('word_counts'):
        #     for word_count, freq in list(patterns['word_counts'].items())[:2]:
        #         if word_count == 1:
        #             regex = r'\S+'
        #             desc = 'Single word'
        #         elif word_count == 2:
        #             regex = r'\S+\s+\S+'
        #             desc = 'Two words'
        #         else:
        #             regex = r'(?:\S+\s+){' + str(word_count-1) + r'}\S+'
        #             desc = f'{word_count} words'
        #         
        #         suggestions.append({
        #             'type': 'word_count',
        #             'pattern': regex,
        #             'description': desc,
        #             'frequency': freq,
        #             'examples': [v for v in sample_values if len(v.split()) == word_count][:3]
        #         })
        
        # Suggestion 3: Based on delimiters with capturing group
        if patterns.get('delimiters'):
            for delim, freq in list(patterns['delimiters'].items())[:2]:
                escaped_delim = re.escape(delim)
                # Wrap in capturing group for extraction
                regex = r'([^' + escaped_delim + r']+(?:' + escaped_delim + r'[^' + escaped_delim + r']+)*)'
                
                suggestions.append({
                    'type': 'delimiter',
                    'pattern': regex,
                    'description': f'Text with {delim} delimiter',
                    'frequency': freq,
                    'priority': 3,  # Lower priority
                    'examples': [v for v in sample_values if delim in v][:3]
                })
        
        return suggestions
    
    def _shape_to_regex(self, shape: str) -> str:
        """
        Convert token shape to regex pattern with capturing group
        
        Examples:
            "Aa+" -> r"([A-Z][a-z]+)"
            "9+" -> r"(\\d+)"
            "A+-9+" -> r"([A-Z]+-\\d+)"
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
        
        # Wrap entire pattern in capturing group for extraction
        return '(' + ''.join(regex_parts) + ')'
    
    def update_template_config(
        self,
        config_path: str,
        field_name: str,
        new_patterns: List[Dict],
        backup: bool = True
    ) -> bool:
        """
        ⚠️ DEPRECATED: Update template config JSON file with new learned patterns
        
        Use apply_patterns_to_db() instead for database-backed configs.
        This method is kept for backward compatibility with JSON-only mode.
        
        Args:
            config_path: Path to template config JSON
            field_name: Field to update
            new_patterns: List of pattern dicts with 'pattern' and 'description'
            backup: Create backup before updating
            
        Returns:
            True if successful
        """
        self.logger.warning(
            "⚠️ update_template_config() is deprecated. "
            "Use apply_patterns_to_db() for database-backed configs."
        )
        
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
