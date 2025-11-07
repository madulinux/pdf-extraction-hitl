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
            # Initialize new CRF model with improved hyperparameters
            self.model = sklearn_crfsuite.CRF(
                algorithm='lbfgs',
                c1=0.05,              # ✅ Stronger L1 regularization (feature selection)
                c2=0.15,              # ✅ Stronger L2 regularization (prevent overfitting)
                max_iterations=200,   # ✅ More training iterations for convergence
                all_possible_transitions=True,
                verbose=False
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
    
    def _create_bio_sequence_multi(self, feedbacks: List[Dict[str, Any]], 
                                   words: List[Dict]) -> Tuple[List[Dict], List[str]]:
        """
        Create BIO-tagged sequence from multiple feedbacks (for one document)
        Uses sequence matching for accurate BIO tagging
        
        Args:
            feedbacks: List of feedback dictionaries with corrected values
            words: List of word dictionaries from PDF
            
        Returns:
            Tuple of (features, labels)
        """
        features = []
        labels = ['O'] * len(words)  # Initialize all as 'O'
        
        # Extract features for all words first
        for i, word in enumerate(words):
            word_features = self._extract_word_features(word, words, i)
            features.append(word_features)
        
        # Find and label sequences for each feedback
        for feedback in feedbacks:
            field_name = feedback['field_name']
            corrected_value = feedback['corrected_value']
            
            if not corrected_value or not corrected_value.strip():
                print(f"⚠️ [Learner] Skipping {field_name}: empty value")
                continue
            
            # ✅ FIX: Better tokenization - normalize spaces
            corrected_value_normalized = ' '.join(corrected_value.split())
            corrected_tokens = corrected_value_normalized.split()
            
            # Find exact sequence in words
            word_texts = [w['text'] for w in words]
            
            # ✅ Strategy 1: Exact match
            found = False
            for i in range(len(word_texts) - len(corrected_tokens) + 1):
                match = True
                for j, token in enumerate(corrected_tokens):
                    if word_texts[i + j] != token:
                        match = False
                        break
                
                if match:
                    labels[i] = f'B-{field_name.upper()}'
                    for j in range(1, len(corrected_tokens)):
                        labels[i + j] = f'I-{field_name.upper()}'
                    found = True
                    print(f"✅ [Learner] Labeled {field_name}: '{corrected_value}' (exact match at position {i})")
                    break
            
            # ✅ Strategy 2: Case-insensitive match
            if not found:
                word_texts_lower = [w.lower() for w in word_texts]
                corrected_tokens_lower = [t.lower() for t in corrected_tokens]
                
                for i in range(len(word_texts_lower) - len(corrected_tokens_lower) + 1):
                    match = True
                    for j, token in enumerate(corrected_tokens_lower):
                        if word_texts_lower[i + j] != token:
                            match = False
                            break
                    
                    if match:
                        labels[i] = f'B-{field_name.upper()}'
                        for j in range(1, len(corrected_tokens)):
                            labels[i + j] = f'I-{field_name.upper()}'
                        found = True
                        print(f"✅ [Learner] Labeled {field_name}: '{corrected_value}' (case-insensitive match at position {i})")
                        break
            
            # ✅ Strategy 3: Substring match (for partial matches)
            if not found:
                # Try to find as a single concatenated string (handles spacing issues)
                corrected_concat = ''.join(corrected_tokens).lower()
                
                for i in range(len(word_texts)):
                    # Try different window sizes
                    for window_size in range(len(corrected_tokens), min(len(corrected_tokens) + 3, len(word_texts) - i + 1)):
                        window_concat = ''.join(word_texts[i:i+window_size]).lower()
                        
                        if corrected_concat in window_concat or window_concat in corrected_concat:
                            # Found partial match
                            labels[i] = f'B-{field_name.upper()}'
                            for j in range(1, window_size):
                                if i + j < len(labels):
                                    labels[i + j] = f'I-{field_name.upper()}'
                            found = True
                            print(f"✅ [Learner] Labeled {field_name}: '{corrected_value}' (substring match at position {i}, window={window_size})")
                            break
                    if found:
                        break
            
            if not found:
                print(f"⚠️ [Learner] Could NOT find '{corrected_value}' for {field_name} in document!")
                print(f"   💡 Hint: Check if value exists in PDF with different spacing/formatting")
        
        return features, labels
    
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
        
        # Find matching tokens in the word list
        for i, word in enumerate(words):
            word_text = word['text']
            
            # ✅ Extract features with context
            word_features = self._extract_word_features(
                word, words, i,
                field_config=field_config,
                context=context
            )
            features.append(word_features)
            
            # Determine BIO label
            if word_text in corrected_tokens:
                token_idx = corrected_tokens.index(word_text)
                if token_idx == 0:
                    labels.append(f'B-{field_name.upper()}')
                else:
                    labels.append(f'I-{field_name.upper()}')
            else:
                labels.append('O')
        
        return features, labels
    
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
                label_x1 = label_pos.get('x1', 0)
                label_y = label_pos.get('y0', 0)
                
                distance_x = word_x - label_x1
                distance_y = abs(word_y - label_y)
                
                features.update({
                    'distance_from_label_x': distance_x / 100,  # Normalized
                    'distance_from_label_y': distance_y / 100,
                    'after_label': distance_x > 0,
                    'same_line_as_label': distance_y < 10,
                    'near_label': distance_x < 50 and distance_y < 10,
                })
            else:
                # Default values when no label position
                features.update({
                    'distance_from_label_x': 0,
                    'distance_from_label_y': 0,
                    'after_label': False,
                    'same_line_as_label': False,
                    'near_label': False,
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
                'same_line_as_label': False,
                'near_label': False,
            })
        
        # Prefix and suffix features
        if len(text) > 1:
            features['prefix-2'] = text[:2]
            features['suffix-2'] = text[-2:]
        if len(text) > 2:
            features['prefix-3'] = text[:3]
            features['suffix-3'] = text[-3:]
        
        # ✅ NEW: Set date context and boundary features
        if index > 0:
            prev_word = all_words[index - 1]['text']
            prev_y = all_words[index - 1].get('top', 0)
            
            # Context features (previous word)
            features['prev_word'] = prev_word.lower()
            features['prev_word.isupper'] = prev_word.isupper()
            features['prev_word.istitle'] = prev_word.istitle()
            features['prev_word.isdigit'] = prev_word.isdigit()
            
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
        
        # Context features (next word)
        if index < len(all_words) - 1:
            next_word = all_words[index + 1]['text']
            
            features['next_word'] = next_word.lower()
            features['next_word.isupper'] = next_word.isupper()
            features['next_word.istitle'] = next_word.istitle()
            features['next_word.isdigit'] = next_word.isdigit()
            
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
        
        return features
    
    def train(self, X_train: List[List[Dict]], y_train: List[List[str]]) -> Dict[str, float]:
        """
        Train or retrain the CRF model
        
        Args:
            X_train: List of feature sequences
            y_train: List of label sequences
            
        Returns:
            Dictionary of evaluation metrics
        """
        if not X_train or not y_train:
            raise ValueError("Training data cannot be empty")
        
        # Train the model
        self.model.fit(X_train, y_train)
        
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
                         y_old: List[List[str]] = None) -> Dict[str, float]:
        """
        Perform incremental training by combining old and new data
        
        Args:
            X_new: New feature sequences
            y_new: New label sequences
            X_old: Previous training features (optional)
            y_old: Previous training labels (optional)
            
        Returns:
            Dictionary of evaluation metrics
        """
        # Combine old and new data if available
        if X_old and y_old:
            X_combined = X_old + X_new
            y_combined = y_old + y_new
        else:
            X_combined = X_new
            y_combined = y_new
        
        # Train with combined data
        return self.train(X_combined, y_combined)
    
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
        results = {
            'accuracy': metrics.flat_accuracy_score(y_test, y_pred),
            'precision': metrics.flat_precision_score(y_test, y_pred, 
                                                     average='weighted', labels=labels),
            'recall': metrics.flat_recall_score(y_test, y_pred, 
                                               average='weighted', labels=labels),
            'f1': metrics.flat_f1_score(y_test, y_pred, 
                                       average='weighted', labels=labels),
            'classification_report': metrics.flat_classification_report(
                y_test, y_pred, labels=labels, digits=3
            )
        }
        
        return results
