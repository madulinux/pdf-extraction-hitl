"""
Adaptive Learner Service
Implements incremental learning using CRF model with user feedback
"""
import sklearn_crfsuite
from sklearn_crfsuite import metrics
import joblib
import json
import os
from typing import Dict, List, Tuple, Any
import numpy as np
import time

class AdaptiveLearner:
    """Handles adaptive learning from user feedback"""
    
    def __init__(self, model_path: str = None):
        """
        Initialize adaptive learner
        
        Args:
            model_path: Path to existing model (if any)
        """
        self.model_path = model_path
        self.model = None
        
        if model_path and os.path.exists(model_path):
            self.model = self._load_model(model_path)
        else:
            # Initialize new CRF model with optimized hyperparameters for high accuracy
            # ✅ Default params match grid search best results (c1=0.01, c2=0.01)
            self.model = sklearn_crfsuite.CRF(
                algorithm='lbfgs',
                c1=0.01,              # ✅ Optimal L1 from grid search (prevents overfitting)
                c2=0.01,              # ✅ Optimal L2 from grid search (better generalization)
                max_iterations=100,   # ⚡ Reduced from 100 (faster training, still good accuracy)
                all_possible_transitions=True,
                verbose=False,
                num_memories=12       # ⚡ L-BFGS memory size (lower = faster, less memory)
            )
    
    def prepare_training_data(self, feedback_list: List[Dict[str, Any]], 
                             pdf_words_list: List[List[Dict]]) -> Tuple[List, List]:
        """
        Convert feedback into training data with BIO tagging
        
        Args:
            feedback_list: List of feedback dictionaries
            pdf_words_list: List of word lists from corresponding PDFs
            
        Returns:
            Tuple of (X_train, y_train) for CRF model
        """
        X_train = []
        y_train = []
        
        for feedback, words in zip(feedback_list, pdf_words_list):
            # Create BIO labels for this document
            features, labels = self._create_bio_sequence(feedback, words)
            X_train.append(features)
            y_train.append(labels)
        
        return X_train, y_train
    
    def _create_bio_sequence(
        self, 
        feedback: Dict[str, Any], 
        words: List[Dict],
        field_config: Dict = None
    ) -> Tuple[List[Dict], List[str]]:
        """
        Create BIO-tagged sequence from feedback with context
        
        Args:
            feedback: Feedback dictionary with corrected values
            words: List of word dictionaries from PDF
            field_config: Field configuration with context (NEW)
            
        Returns:
            Tuple of (features, labels)
        """
        field_name = feedback['field_name']
        corrected_value = feedback['corrected_value']
        
        # ✅ Extract context from field_config
        context = {}
        if field_config:
            locations = field_config.get('locations', [])
            if locations:
                # Use first location's context for training
                context = locations[0].get('context', {})
            elif 'context' in field_config:
                # Backward compatibility: old format
                context = field_config.get('context', {})
        
        # Tokenize corrected value
        corrected_tokens = corrected_value.split()
        
        features = []
        labels = []
        
        # ✅ ADAPTIVE: Find best matching sequence in PDF words
        # Instead of exact token matching, use sequence-based fuzzy matching
        word_texts = [w['text'] for w in words]
        matched_indices = self._find_best_sequence_match(word_texts, corrected_tokens)
        
        # Create BIO labels based on matched sequence
        for i, word in enumerate(words):
            # ✅ Extract features with context
            word_features = self._extract_word_features(
                word, words, i,
                field_config=field_config,
                context=context
            )
            
            # ✅ CRITICAL FIX: Add field-aware feature for THIS field only
            # This matches inference behavior where only target field is active
            word_features[f'target_field_{field_name}'] = True
            
            features.append(word_features)
            
            # Determine BIO label based on matched sequence
            if i in matched_indices:
                # This word is part of the matched sequence
                seq_position = matched_indices.index(i)
                if seq_position == 0:
                    labels.append(f'B-{field_name.upper()}')
                else:
                    labels.append(f'I-{field_name.upper()}')
            else:
                labels.append('O')
        
        return features, labels
    
    def _find_best_sequence_match(
        self, 
        word_texts: List[str], 
        target_tokens: List[str]
    ) -> List[int]:
        """
        Find the best matching sequence of words in PDF that matches target tokens.
        Uses fuzzy matching and sequence alignment to handle variations.
        
        Args:
            word_texts: List of word texts from PDF
            target_tokens: List of tokens from corrected value
            
        Returns:
            List of indices in word_texts that match the target sequence
        """
        if not target_tokens:
            return []
        
        best_match_indices = []
        best_match_score = 0
        
        # Try to find the best contiguous sequence
        for start_idx in range(len(word_texts)):
            for end_idx in range(start_idx + 1, min(start_idx + len(target_tokens) * 2, len(word_texts) + 1)):
                candidate_words = word_texts[start_idx:end_idx]
                
                # Calculate match score using fuzzy matching
                score = self._calculate_sequence_match_score(candidate_words, target_tokens)
                
                if score > best_match_score:
                    best_match_score = score
                    best_match_indices = list(range(start_idx, end_idx))
        
        # If no good match found, fall back to token-by-token matching
        if best_match_score < 0.5:
            best_match_indices = []
            for token in target_tokens:
                try:
                    idx = word_texts.index(token)
                    if idx not in best_match_indices:
                        best_match_indices.append(idx)
                except ValueError:
                    # Token not found, try fuzzy match
                    for i, word in enumerate(word_texts):
                        if i not in best_match_indices and self._fuzzy_match(word, token):
                            best_match_indices.append(i)
                            break
        
        return sorted(best_match_indices)
    
    def _calculate_sequence_match_score(
        self, 
        candidate_words: List[str], 
        target_tokens: List[str]
    ) -> float:
        """
        Calculate how well a candidate sequence matches target tokens.
        
        Args:
            candidate_words: Candidate word sequence from PDF
            target_tokens: Target token sequence
            
        Returns:
            Match score between 0 and 1
        """
        if not candidate_words or not target_tokens:
            return 0.0
        
        # Join and compare as strings (case-insensitive)
        candidate_text = ' '.join(candidate_words).lower()
        target_text = ' '.join(target_tokens).lower()
        
        # Calculate similarity using longest common subsequence
        from difflib import SequenceMatcher
        matcher = SequenceMatcher(None, candidate_text, target_text)
        similarity = matcher.ratio()
        
        # Bonus for exact length match
        length_ratio = min(len(candidate_words), len(target_tokens)) / max(len(candidate_words), len(target_tokens))
        
        # Combined score
        score = similarity * 0.8 + length_ratio * 0.2
        
        return score
    
    def _fuzzy_match(self, word: str, token: str, threshold: float = 0.8) -> bool:
        """
        Check if word fuzzy matches token.
        
        Args:
            word: Word from PDF
            token: Target token
            threshold: Similarity threshold
            
        Returns:
            True if match, False otherwise
        """
        from difflib import SequenceMatcher
        matcher = SequenceMatcher(None, word.lower(), token.lower())
        return matcher.ratio() >= threshold
    
    def _extract_word_features(
        self, 
        word: Dict, 
        all_words: List[Dict], 
        index: int,
        field_config: Dict = None,
        context: Dict = None
    ) -> Dict[str, Any]:
        """
        Extract features for a single word
        
        Features include:
        - Lexical features (word form, case, digits)
        - Orthographic features (capitalization patterns)
        - Layout features (position on page)
        - Context features (surrounding words)
        - Label features (from template context)
        - Distance features (spatial relationships)
        - Date features (semantic date recognition)
        - Boundary features (entity boundary detection)
        
        MUST match extraction features in strategies.py!
        """
        import re
        
        text = word['text']
        word_x = word.get('x0', 0)
        word_y = word.get('top', 0)
        
        features = {
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
            'x0_norm': word['x0'] / 1000,
            'y0_norm': word['top'] / 1000,
            'width': (word['x1'] - word['x0']) / 1000,
            'height': (word['bottom'] - word['top']) / 1000,
            
            # ✅ NEW: Date-specific features (PATTERN-BASED, NOT HARDCODED!)
            'is_capitalized_word': text.istitle() and text.isalpha() and len(text) > 2,  # Likely month/location
            'is_year': text.isdigit() and len(text) == 4 and 1900 <= int(text) <= 2100,
            'is_day_number': text.isdigit() and len(text) <= 2 and (1 <= int(text) <= 31 if text.isdigit() else False),
            'is_date_separator': text in [',', '-', '/', '.'],
            'looks_like_date_pattern': bool(re.match(r'\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4}', text)),
            'has_numeric_context': False,  # Will be set below based on neighbors
            
            # ✅ NEW: Boundary detection features (HIGH IMPACT!)
            'is_after_punctuation': False,
            'is_before_punctuation': False,
            'is_after_newline': False,
            'position_in_line': 0,
            
            # ✅ NEW: Field length indicators (pattern-based)
            'is_short_field': len(text) <= 5,  # Likely age, temp, etc.
            'is_medium_field': 5 < len(text) <= 20,  # Likely name, date
            'is_long_field': len(text) > 20,  # Likely address, text
            'word_count_in_sequence': 1,  # Will be updated based on position
        }
        
        # ✅ NEW: Context features (label, distance, spatial)
        if context:
            label = context.get('label', '')
            label_pos = context.get('label_position', {})
            words_before = context.get('words_before', [])
            words_after = context.get('words_after', [])
            
            # Build context text for matching
            context_before_text = ' '.join(
                w.get('text', '') if isinstance(w, dict) else str(w) 
                for w in words_before
            ).lower()
            context_after_text = ' '.join(
                w.get('text', '') if isinstance(w, dict) else str(w) 
                for w in words_after
            ).lower()
            
            # Label features
            features.update({
                'has_label': bool(label),
                'label_text': label.lower() if label else '',
                'in_context_before': text.lower() in context_before_text,
                'in_context_after': text.lower() in context_after_text,
            })
            
            # Distance features (spatial relationships)
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
                
                features.update({
                    'distance_from_label_x': distance_x / 100,  # Normalized
                    'distance_from_label_y': distance_y / 100,
                    'after_label': is_after_label,
                    'before_label': is_before_label,  # ✅ NEW: Penalize words before label
                    'above_label': is_above_label,    # ✅ NEW: Penalize words above label
                    'below_label': is_below_label,    # ✅ NEW: Detect words below label
                    'same_line_as_label': is_same_line,
                    'near_label': distance_x < 50 and is_same_line,
                    'valid_position': is_after_label and is_same_line,  # ✅ NEW: Strong constraint
                })
            else:
                # Default values when no label position
                features.update({
                    'distance_from_label_x': 0,
                    'distance_from_label_y': 0,
                    'after_label': False,
                    'before_label': False,
                    'above_label': False,
                    'below_label': False,
                    'same_line_as_label': False,
                    'near_label': False,
                    'valid_position': False,
                })
            
            # ✅ NEW: Next field boundary features (CRITICAL for stopping extraction)
            next_field_y = context.get('next_field_y')
            if next_field_y is not None:
                distance_to_next = next_field_y - word_y
                features.update({
                    'has_next_field': True,
                    'distance_to_next_field': distance_to_next / 100,  # Normalized
                    'before_next_field': distance_to_next > 0,
                    'near_next_field': 0 < distance_to_next < 20,
                    'far_from_next_field': distance_to_next > 50,
                })
            else:
                features.update({
                    'has_next_field': False,
                    'distance_to_next_field': 0,
                    'before_next_field': False,
                    'near_next_field': False,
                    'far_from_next_field': False,
                })
        else:
            # Default values when no context
            features.update({
                'has_label': False,
                'label_text': '',
                'in_context_before': False,
                'in_context_after': False,
                'distance_from_label_x': 0,
                'distance_from_label_y': 0,
                'after_label': False,
                'before_label': False,
                'above_label': False,
                'below_label': False,
                'same_line_as_label': False,
                'near_label': False,
                'valid_position': False,
                'has_next_field': False,
                'distance_to_next_field': 0,
                'before_next_field': False,
                'near_next_field': False,
                'far_from_next_field': False,
            })
        
        # Prefix and suffix features
        if len(text) > 1:
            features['prefix-2'] = text[:2]
            features['suffix-2'] = text[-2:]
        if len(text) > 2:
            features['prefix-3'] = text[:3]
            features['suffix-3'] = text[-3:]
        
        # ✅ ENHANCED: Extended context window (2-3 words) for better prefix/suffix detection
        if index > 0:
            prev_word = all_words[index - 1]['text']
            prev_y = all_words[index - 1].get('top', 0)
            
            # Context features (previous word)
            features['prev_word'] = prev_word.lower()
            features['prev_word.isupper'] = prev_word.isupper()
            features['prev_word.istitle'] = prev_word.istitle()
            features['prev_word.isdigit'] = prev_word.isdigit()
            
            # ✅ NEW: 2-word context (critical for multi-word prefixes like "Jalan W.R.")
            if index > 1:
                prev2_word = all_words[index - 2]['text']
                features['prev2_word'] = prev2_word.lower()
                features['prev2_word.istitle'] = prev2_word.istitle()
                # Bigram feature (2-word sequence before current word)
                features['prev_bigram'] = f"{prev2_word.lower()}_{prev_word.lower()}"
            
            # ✅ NEW: 3-word context (for longer prefixes)
            if index > 2:
                prev3_word = all_words[index - 3]['text']
                features['prev3_word'] = prev3_word.lower()
                # Trigram feature
                features['prev_trigram'] = f"{prev3_word.lower()}_{prev2_word.lower() if index > 1 else ''}_{prev_word.lower()}"
            
            # Boundary features
            features['is_after_punctuation'] = prev_word in [',', '.', ':', ';', ')', '(']
            features['is_after_newline'] = abs(word_y - prev_y) > 10
            
            # Numeric context (for dates, numbers, etc.)
            features['has_numeric_context'] = (
                prev_word.isdigit() or 
                features['is_year'] or 
                features['is_day_number'] or
                (prev_word.istitle() and prev_word.isalpha() and len(prev_word) > 2)  # Capitalized word (month/location)
            )
        else:
            features['BOS'] = True  # Beginning of sequence
        
        # ✅ ENHANCED: Extended next word context
        if index < len(all_words) - 1:
            next_word = all_words[index + 1]['text']
            
            features['next_word'] = next_word.lower()
            features['next_word.isupper'] = next_word.isupper()
            features['next_word.istitle'] = next_word.istitle()
            features['next_word.isdigit'] = next_word.isdigit()
            
            # ✅ NEW: 2-word lookahead context
            if index < len(all_words) - 2:
                next2_word = all_words[index + 2]['text']
                features['next2_word'] = next2_word.lower()
                features['next2_word.istitle'] = next2_word.istitle()
                # Bigram feature (2-word sequence after current word)
                features['next_bigram'] = f"{next_word.lower()}_{next2_word.lower()}"
            
            # ✅ NEW: 3-word lookahead context
            if index < len(all_words) - 3:
                next3_word = all_words[index + 3]['text']
                features['next3_word'] = next3_word.lower()
                # Trigram feature
                features['next_trigram'] = f"{next_word.lower()}_{next2_word.lower() if index < len(all_words) - 2 else ''}_{next3_word.lower()}"
            
            # Boundary features
            features['is_before_punctuation'] = next_word in [',', '.', ':', ';', ')', '(']
            
            # Enhance numeric context with next word
            if not features['has_numeric_context']:
                features['has_numeric_context'] = (
                    next_word.isdigit() or
                    (next_word.istitle() and next_word.isalpha() and len(next_word) > 2)
                )
        else:
            features['EOS'] = True  # End of sequence
        
        # Position in line (for boundary detection)
        features['position_in_line'] = sum(
            1 for w in all_words[:index] 
            if abs(w.get('top', 0) - word_y) < 5
        )
        
        # ✅ NEW: Column-based features for multi-column layout
        x_coords = [w.get('x0', 0) for w in all_words]
        column_boundaries = self._detect_column_boundaries(x_coords)
        column_idx = self._get_column_index(word_x, column_boundaries)
        features['column_index'] = column_idx
        features['in_first_column'] = column_idx == 0
        features['in_second_column'] = column_idx == 1
        features['in_third_column'] = column_idx == 2
        features['in_fourth_column'] = column_idx == 3
        
        # ✅ NEW: Line group features for text wrapping detection
        line_groups = self._detect_line_groups(all_words)
        line_group_idx = self._get_line_group_index(index, line_groups)
        features['line_group_index'] = line_group_idx
        features['is_first_line_in_group'] = self._is_first_line_in_group(index, line_groups)
        features['is_continuation_line'] = self._is_continuation_line(index, line_groups)
        
        # ✅ NEW: Sequence position features (for Finding vs Recommendation)
        features['relative_x_position'] = word_x / max(x_coords) if x_coords else 0
        features['is_left_aligned'] = word_x < 200  # Typically Finding
        features['is_right_aligned'] = word_x > 400  # Typically Recommendation
        features['is_center_aligned'] = 200 <= word_x <= 400
        
        # ✅ NEW: Delimiter detection (for Finding/Recommendation separation)
        features['is_delimiter'] = text in ['|', '/', '\\', ':', ';']
        features['after_delimiter'] = False
        if index > 0 and all_words[index-1].get('text', '') in ['|', '/', '\\', ':', ';']:
            features['after_delimiter'] = True
        
        # ✅ NEW: Number sequence detection (for Area ID, No, etc.)
        features['is_sequence_number'] = text.isdigit() and len(text) <= 2
        features['is_long_number'] = text.isdigit() and len(text) > 5  # Area Code
        features['after_sequence_number'] = False
        if index > 0 and all_words[index-1].get('text', '').isdigit() and len(all_words[index-1].get('text', '')) <= 2:
            features['after_sequence_number'] = True
        
        # ✅ NEW: Sentence boundary features (for Finding vs Recommendation)
        features['starts_with_capital'] = text and text[0].isupper()
        features['after_period'] = index > 0 and all_words[index-1].get('text', '') == '.'
        features['before_period'] = index < len(all_words) - 1 and all_words[index+1].get('text', '') == '.'
        
        # ✅ NEW: Word density features (for table detection)
        words_in_same_line = [w for w in all_words if abs(w.get('top', 0) - word_y) < 5]
        features['words_in_line'] = len(words_in_same_line)
        features['is_dense_line'] = len(words_in_same_line) > 10  # Likely table row
        features['is_sparse_line'] = len(words_in_same_line) < 5
        
        return features
    
    def _get_context_for_word(self, word: Dict, field_contexts: Dict[str, Dict]) -> Dict:
        """
        Get the most relevant context for a word based on its position
        
        Args:
            word: Word dictionary with position info
            field_contexts: Map of field_name -> context dict
            
        Returns:
            Context dict (label, label_position, etc.) or empty dict
        """
        if not field_contexts:
            return {}
        
        word_x = word.get('x0', 0)
        word_y = word.get('top', 0)
        
        # Find closest context based on spatial proximity
        best_context = {}
        min_distance = float('inf')
        
        for field_name, context in field_contexts.items():
            label_pos = context.get('label_position', {})
            if not label_pos:
                continue
            
            # Calculate distance from word to label
            label_x = label_pos.get('x1', 0)  # Right edge of label
            label_y = label_pos.get('y0', 0)  # Top of label
            
            # Horizontal distance (word should be after label)
            dx = word_x - label_x
            dy = abs(word_y - label_y)
            
            # Only consider words that are after the label (dx > 0)
            # and on the same line or nearby (dy < 50)
            if dx > 0 and dy < 50:
                distance = (dx**2 + dy**2)**0.5
                
                if distance < min_distance:
                    min_distance = distance
                    best_context = context
        
        return best_context
    
    def train(self, X_train: List[List[Dict]], y_train: List[List[str]], 
              c1: float = None, c2: float = None, 
              max_iterations: int = 100,
              skip_evaluation: bool = False) -> Dict[str, float]:
        """
        Train or retrain the CRF model
        
        Args:
            X_train: List of feature sequences
            y_train: List of label sequences
            c1: L1 regularization parameter (optional, for grid search)
            c2: L2 regularization parameter (optional, for grid search)
            max_iterations: Maximum L-BFGS iterations (default: 100)
            skip_evaluation: Skip training evaluation for speed (default: False)
            
        Returns:
            Dictionary of evaluation metrics (empty if skip_evaluation=True)
        """
        if not X_train or not y_train:
            raise ValueError("Training data cannot be empty")
        
        # ✅ Update regularization params if provided (for grid search)
        if c1 is not None or c2 is not None:
            self.model = sklearn_crfsuite.CRF(
                algorithm='lbfgs',
                c1=c1 if c1 is not None else 0.01,
                c2=c2 if c2 is not None else 0.01,
                max_iterations=max_iterations,
                all_possible_transitions=True,
                verbose=False,
                num_memories=12,
            )
        
        # ⚡ Train the model (this is the bottleneck)
        self.model.fit(X_train, y_train)
        
        # ⚡ OPTIMIZATION: Skip evaluation for production (saves ~20-30% time)
        if skip_evaluation:
            return {}
        
        # Evaluate on training data (for monitoring)
        y_pred = self.model.predict(X_train)
        
        # Calculate metrics
        labels = list(self.model.classes_)
        labels.remove('O')  # Remove 'O' label for entity-level metrics
        
        metrics_dict = {
            'accuracy': metrics.flat_accuracy_score(y_train, y_pred),
            'precision': metrics.flat_precision_score(y_train, y_pred, 
                                                     average='weighted', labels=labels),
            'recall': metrics.flat_recall_score(y_train, y_pred, 
                                               average='weighted', labels=labels),
            'f1': metrics.flat_f1_score(y_train, y_pred, 
                                       average='weighted', labels=labels)
        }
        
        return metrics_dict
    
    def incremental_train(self, X_new: List[List[Dict]], y_new: List[List[str]], 
                         X_old: List[List[Dict]] = None, 
                         y_old: List[List[str]] = None,
                         skip_evaluation: bool = True) -> Dict[str, float]:
        """
        Perform incremental training by combining old and new data
        
        Args:
            X_new: New feature sequences
            y_new: New label sequences
            X_old: Previous training features (optional)
            y_old: Previous training labels (optional)
            skip_evaluation: Skip training evaluation for speed (default: True)
            
        Returns:
            Dictionary of evaluation metrics (empty if skip_evaluation=True)
        """
        # Combine old and new data if available
        if X_old and y_old:
            X_combined = X_old + X_new
            y_combined = y_old + y_new
        else:
            X_combined = X_new
            y_combined = y_new
        
        # ⚡ Train with fewer iterations for incremental (model already converged)
        # Use 100 iterations instead of 100 for ~5x speedup
        return self.train(X_combined, y_combined, 
                         max_iterations=100, 
                         skip_evaluation=skip_evaluation)
    
    def save_model(self, output_path: str):
        """Save trained model to file"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        joblib.dump(self.model, output_path)
        self.model_path = output_path
    
    def _load_model(self, model_path: str):
        """Load trained model from file"""
        try:
            return joblib.load(model_path)
        except Exception as e:
            print(f"Error loading model from {model_path}: {e}")
            return None
    
    def _detect_column_boundaries(self, x_coords: List[float]) -> List[float]:
        """
        Detect column boundaries from X-coordinates using clustering
        
        Args:
            x_coords: List of X-coordinates
            
        Returns:
            List of column boundary X-coordinates
        """
        if not x_coords:
            return []
        
        # Use simple histogram-based approach
        import numpy as np
        
        x_array = np.array(x_coords)
        # Create histogram with 20 bins
        hist, bin_edges = np.histogram(x_array, bins=20)
        
        # Find peaks (local maxima) in histogram
        peaks = []
        for i in range(1, len(hist) - 1):
            if hist[i] > hist[i-1] and hist[i] > hist[i+1] and hist[i] > 5:
                # Peak found, use bin center as column boundary
                peak_x = (bin_edges[i] + bin_edges[i+1]) / 2
                peaks.append(peak_x)
        
        return sorted(peaks)
    
    def _get_column_index(self, x: float, column_boundaries: List[float]) -> int:
        """Get column index for a given X-coordinate"""
        if not column_boundaries:
            return 0
        
        for i, boundary in enumerate(column_boundaries):
            if x < boundary:
                return i
        
        return len(column_boundaries)
    
    def _detect_line_groups(self, words: List[Dict]) -> List[List[int]]:
        """Detect line groups for text wrapping detection"""
        if not words:
            return []
        
        # Group words by Y-coordinate (same line)
        lines = {}
        for i, word in enumerate(words):
            y = round(word.get('top', 0), 1)
            if y not in lines:
                lines[y] = []
            lines[y].append(i)
        
        # Sort lines by Y-coordinate
        sorted_y = sorted(lines.keys())
        
        # Group consecutive lines that are close together
        line_groups = []
        current_group = []
        prev_y = None
        
        for y in sorted_y:
            if prev_y is None:
                current_group = lines[y]
            else:
                if y - prev_y < 20:
                    current_group.extend(lines[y])
                else:
                    if current_group:
                        line_groups.append(current_group)
                    current_group = lines[y]
            prev_y = y
        
        if current_group:
            line_groups.append(current_group)
        
        return line_groups
    
    def _get_line_group_index(self, word_idx: int, line_groups: List[List[int]]) -> int:
        """Get line group index for a given word index"""
        for i, group in enumerate(line_groups):
            if word_idx in group:
                return i
        return -1
    
    def _is_first_line_in_group(self, word_idx: int, line_groups: List[List[int]]) -> bool:
        """Check if word is on the first line of its group"""
        for group in line_groups:
            if word_idx in group:
                return word_idx == group[0] or word_idx in group[:5]
        return False
    
    def _is_continuation_line(self, word_idx: int, line_groups: List[List[int]]) -> bool:
        """Check if word is on a continuation line (wrapped text)"""
        for group in line_groups:
            if word_idx in group:
                return word_idx not in group[:5]
        return False
    
    def get_feature_importance(self) -> Dict[str, float]:
        """
        Get feature importance from the trained model
        
        Returns:
            Dictionary of feature names and their weights
        """
        if not self.model:
            return {}
        
        try:
            # Get state features (transition weights)
            state_features = self.model.state_features_
            
            # Aggregate feature weights
            feature_weights = {}
            for (label, feature), weight in state_features.items():
                if feature not in feature_weights:
                    feature_weights[feature] = 0
                feature_weights[feature] += abs(weight)
            
            # Sort by importance
            sorted_features = dict(sorted(feature_weights.items(), 
                                        key=lambda x: x[1], reverse=True))
            
            return sorted_features
        except Exception as e:
            print(f"Error getting feature importance: {e}")
            return {}
    
    def evaluate(self, X_test: List[List[Dict]], 
                y_test: List[List[str]]) -> Dict[str, Any]:
        """
        Evaluate model on test data
        
        Args:
            X_test: Test feature sequences
            y_test: Test label sequences
            
        Returns:
            Dictionary with detailed evaluation metrics
        """
        if not self.model:
            raise ValueError("Model not trained yet")
        
        y_pred = self.model.predict(X_test)
        
        labels = list(self.model.classes_)
        labels.remove('O')
        
        # Calculate metrics
        # ✅ Use zero_division=0 to suppress warnings for missing labels in small datasets
        results = {
            'accuracy': metrics.flat_accuracy_score(y_test, y_pred),
            'precision': metrics.flat_precision_score(y_test, y_pred, 
                                                     average='weighted', labels=labels,
                                                     zero_division=0),
            'recall': metrics.flat_recall_score(y_test, y_pred, 
                                               average='weighted', labels=labels,
                                               zero_division=0),
            'f1': metrics.flat_f1_score(y_test, y_pred, 
                                       average='weighted', labels=labels,
                                       zero_division=0),
            'classification_report': metrics.flat_classification_report(
                y_test, y_pred, labels=labels, digits=3, zero_division=0
            )
        }
        
        return results
