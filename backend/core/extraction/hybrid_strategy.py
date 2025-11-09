"""
Hybrid Extraction Strategy Module

Implements adaptive hybrid extraction combining multiple strategies.
Aligned with thesis research objectives:
- Tujuan 1: Model pembelajaran adaptif yang meningkatkan akurasi
- Tujuan 2: Integrasi pendekatan berbasis aturan dan pembelajaran mesin
- Tujuan 4: Evaluasi performa model pembelajaran adaptif
"""
import logging
import json
import os
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

from .strategies import (
    ExtractionStrategy,
    RuleBasedExtractionStrategy,
    PositionExtractionStrategy,
    CRFExtractionStrategy,
    FieldValue
)


class StrategyType(Enum):
    """Enumeration of available extraction strategies"""
    RULE_BASED = "rule_based"
    POSITION_BASED = "position_based"
    CRF = "crf"
    HYBRID = "hybrid"


@dataclass
class StrategyPerformance:
    """Performance metrics for extraction strategies"""
    strategy_type: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    confidence_avg: float
    extraction_count: int
    last_updated: str


@dataclass
class ExtractionContext:
    """Context information for extraction decisions"""
    template_id: int
    template_name: str
    template_complexity: float
    field_count: int
    has_model: bool
    historical_performance: Dict[str, Any]


class HybridExtractionStrategy:
    """
    Hybrid extraction strategy combining rule-based and ML approaches.
    
    Features:
    1. Adaptive strategy selection based on context
    2. Weighted result combination
    3. Performance tracking and learning
    4. Continuous improvement from feedback
    """
    
    def __init__(self, performance_file: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        
        # Initialize strategies
        self.rule_based_strategy = RuleBasedExtractionStrategy()
        self.position_strategy = PositionExtractionStrategy()
        self.crf_strategy = None  # Initialized per-template
        
        # Performance tracking
        self.performance_file = performance_file or 'data/strategy_performance.json'
        self.performance_history: Dict[str, Dict[str, StrategyPerformance]] = {}
        self._load_performance_history()
        
        # Strategy weights (adaptive - will be updated based on performance)
        self.strategy_weights = {
            StrategyType.RULE_BASED: 0.4,
            StrategyType.POSITION_BASED: 0.5,
            StrategyType.CRF: 0.0,  # Increases with training
        }
    
    def extract_all_fields(
        self,
        pdf_path: str,
        template_config: Dict[str, Any],
        model_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract all fields from PDF using hybrid approach
        
        Args:
            pdf_path: Path to PDF file
            template_config: Template configuration
            model_path: Path to CRF model (optional)
            
        Returns:
            Dictionary with extraction results
        """
        template_id = template_config.get('template_id', 0)
        template_name = template_config.get('template_name', 'unknown')
        
        print(f"🔍 [HybridStrategy] Starting extraction for template {template_name}")
        
        # Initialize CRF strategy if model available
        print(f"🔍 [HybridStrategy] Checking model path: {model_path}")
        if model_path:
            if os.path.exists(model_path):
                print(f"✅ [HybridStrategy] Model file exists: {model_path}")
                self.crf_strategy = CRFExtractionStrategy(model_path)
                self.strategy_weights[StrategyType.CRF] = 0.7  # High weight for trained model
                print(f"✅ [HybridStrategy] CRF strategy initialized with weight 0.7")
            else:
                print(f"❌ [HybridStrategy] Model file NOT found: {model_path}")
        else:
            print(f"⚠️ [HybridStrategy] No model path provided")
        
        # Analyze extraction context
        context = self._analyze_context(template_config, model_path)
        
        # Extract words from PDF
        all_words = self._extract_words_from_pdf(pdf_path)
        
        # Extract each field
        results = {
            'extracted_data': {},
            'confidence_scores': {},
            'extraction_methods': {},
            'conflicts': {},  # NEW: Conflict detection
            'metadata': {
                'pdf_path': pdf_path,
                'template_id': template_id,
                'template_name': template_name,
                'strategies_used': []
            }
        }
        
        fields = template_config.get('fields', {})
        for field_name, field_config in fields.items():
            field_config['field_name'] = field_name
            
            # Extract with conflict detection
            extraction_result = self._extract_field_with_conflict_detection(
                pdf_path, field_config, all_words, context, field_name
            )
            
            if extraction_result:
                results['extracted_data'][field_name] = extraction_result['value']
                results['confidence_scores'][field_name] = extraction_result['confidence']
                results['extraction_methods'][field_name] = extraction_result['method']
                
                # Add to strategies_used
                strategy_info = {
                    'field': field_name,
                    'method': extraction_result['method'],
                    'confidence': extraction_result['confidence']
                }
                
                # Add location info if available
                if 'metadata' in extraction_result:
                    metadata = extraction_result['metadata']
                    if 'location_index' in metadata:
                        strategy_info['location_index'] = metadata['location_index']
                    if 'page' in metadata:
                        strategy_info['page'] = metadata['page']
                    if 'label' in metadata:
                        strategy_info['label'] = metadata['label']
                
                results['metadata']['strategies_used'].append(strategy_info)
                
                # Add conflict info if detected
                if 'conflict' in extraction_result:
                    results['conflicts'][field_name] = extraction_result['conflict']
            else:
                results['extracted_data'][field_name] = ''
                results['confidence_scores'][field_name] = 0.0
                results['extraction_methods'][field_name] = 'none'
        
        self.logger.info(f"Extraction completed: {len(results['extracted_data'])} fields")
        if results['conflicts']:
            self.logger.info(f"Conflicts detected in {len(results['conflicts'])} fields")
        
        return results
    
    def _analyze_context(
        self,
        template_config: Dict[str, Any],
        model_path: Optional[str]
    ) -> ExtractionContext:
        """Analyze extraction context for strategy selection"""
        template_id = template_config.get('template_id', 0)
        template_name = template_config.get('template_name', 'unknown')
        fields = template_config.get('fields', {})
        
        # Calculate template complexity
        field_count = len(fields)
        complexity = min(field_count / 20.0, 1.0)  # Normalize to 0-1
        
        # Get historical performance
        historical_perf = self.performance_history.get(str(template_id), {})
        
        return ExtractionContext(
            template_id=template_id,
            template_name=template_name,
            template_complexity=complexity,
            field_count=field_count,
            has_model=model_path is not None and os.path.exists(model_path) if model_path else False,
            historical_performance=historical_perf
        )
    
    def _extract_field_with_conflict_detection(
        self,
        pdf_path: str,
        field_config: Dict,
        all_words: List[Dict],
        context: ExtractionContext,
        field_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Extract field with conflict detection across multiple locations
        
        Args:
            pdf_path: Path to PDF file
            field_config: Field configuration
            all_words: All extracted words
            context: Extraction context
            field_name: Field name
            
        Returns:
            Extraction result with conflict info if detected
        """
        from .strategies import get_field_locations
        from .conflict_detector import detect_conflicts
        
        locations = get_field_locations(field_config)
        
        # If single location, use normal extraction
        if len(locations) <= 1:
            strategy_results = self._extract_field_with_strategies(
                pdf_path, field_config, all_words, context
            )
            final_result = self._combine_strategy_results(
                strategy_results, context, field_name
            )
            
            if final_result:
                return {
                    'value': final_result.value,
                    'confidence': final_result.confidence,
                    'method': final_result.method,
                    'metadata': final_result.metadata
                }
            return None
        
        # Multiple locations - extract from all locations using ALL strategies
        all_extraction_results = []
        
        # ✅ FIX: Extract using ALL strategies (not just rule-based)
        # This ensures CRF and other strategies are also used for multi-location fields
        for location_idx, location in enumerate(locations):
            # Create temporary field config with single location
            temp_field_config = {**field_config, 'location': location}
            
            # Extract using all strategies
            strategy_results = self._extract_field_with_strategies(
                pdf_path, temp_field_config, all_words, context
            )
            
            # Combine strategy results
            final_result = self._combine_strategy_results(
                strategy_results, context, field_name
            )
            
            if final_result:
                all_extraction_results.append({
                    'value': final_result.value,
                    'confidence': final_result.confidence,
                    'method': final_result.method,
                    'location_index': location_idx,
                    'page': location.get('page', 0),
                    'label': location.get('context', {}).get('label')
                })
        
        # If no results from any location, return None
        if not all_extraction_results:
            return None
        
        # Detect conflicts
        conflict_info = detect_conflicts(field_name, all_extraction_results)
        
        # Select best result
        best_result = max(all_extraction_results, key=lambda r: r['confidence'])
        
        result = {
            'value': best_result['value'],
            'confidence': best_result['confidence'],
            'method': best_result['method'],
            'metadata': {
                'location_index': best_result.get('location_index', 0),
                'page': best_result.get('page', 0),
                'label': best_result.get('label')
            }
        }
        
        # If conflict detected, add conflict info and possibly update value
        if conflict_info:
            result['conflict'] = conflict_info
            
            # If auto-resolved, use selected value
            if conflict_info.get('auto_resolved'):
                result['value'] = conflict_info['selected_value']
                # Slightly reduce confidence
                result['confidence'] = min(result['confidence'] * 0.95, 1.0)
        
        return result
    
    def _extract_field_with_strategies(
        self,
        pdf_path: str,
        field_config: Dict,
        all_words: List[Dict],
        context: ExtractionContext
    ) -> Dict[StrategyType, Optional[FieldValue]]:
        """Extract field using multiple strategies"""
        field_name = field_config.get('field_name', 'unknown')
        results = {}
        
        self.logger.debug(f"🔍 Extracting field '{field_name}' with multiple strategies")
        
        # Always try rule-based (baseline)
        try:
            rule_result = self.rule_based_strategy.extract(pdf_path, field_config, all_words)
            results[StrategyType.RULE_BASED] = rule_result
            if rule_result:
                self.logger.debug(f"  ✅ Rule-based: {rule_result.value[:50]}... (conf: {rule_result.confidence})")
        except Exception as e:
            self.logger.error(f"Rule-based extraction failed: {e}")
            results[StrategyType.RULE_BASED] = None
        
        # Try position-based for structured templates (increased threshold)
        if context.template_complexity < 0.85:  # Increased from 0.7 to enable for more templates
            try:
                pos_result = self.position_strategy.extract(pdf_path, field_config, all_words)
                results[StrategyType.POSITION_BASED] = pos_result
                if pos_result:
                    self.logger.debug(f"  ✅ Position-based: {pos_result.value[:50]}... (conf: {pos_result.confidence})")
            except Exception as e:
                self.logger.error(f"Position-based extraction failed: {e}")
                results[StrategyType.POSITION_BASED] = None
        
        # Try CRF if model available
        if self.crf_strategy:
            self.logger.debug(f"  🤖 Trying CRF strategy for '{field_name}'...")
            try:
                crf_result = self.crf_strategy.extract(pdf_path, field_config, all_words)
                results[StrategyType.CRF] = crf_result
                if crf_result:
                    self.logger.info(f"  ✅ CRF: {crf_result.value[:50]}... (conf: {crf_result.confidence})")
                else:
                    self.logger.warning(f"  ⚠️ CRF returned None for '{field_name}'")
            except Exception as e:
                self.logger.error(f"CRF extraction failed for '{field_name}': {e}")
                results[StrategyType.CRF] = None
        else:
            self.logger.debug(f"  ⚠️ CRF strategy not available for '{field_name}'")
        
        return results
    
    def _combine_strategy_results(
        self,
        strategy_results: Dict[StrategyType, Optional[FieldValue]],
        context: ExtractionContext,
        field_name: str
    ) -> Optional[FieldValue]:
        """
        Combine results from multiple strategies using adaptive weighting
        
        Scoring formula:
        - Strategy confidence: 40%
        - Strategy weight: 30%
        - Historical performance: 30%
        """
        valid_results = [(st, fv) for st, fv in strategy_results.items() if fv is not None]
        
        if not valid_results:
            return None
        
        if len(valid_results) == 1:
            strategy_type, field_value = valid_results[0]
            self.logger.info(f"  ✅ Only one valid strategy: {strategy_type.value}")
            
            # ✅ FIX: Add all_strategies_attempted even for single strategy
            field_value.metadata['all_strategies_attempted'] = {
                st.value: {
                    'success': fv is not None,
                    'confidence': fv.confidence if fv else 0.0,
                    'value': fv.value if fv else None
                }
                for st, fv in strategy_results.items()
            }
            field_value.metadata['selected_by'] = 'single_valid_strategy'
            
            return field_value
        
        # Score each result
        scored_results = []
        for strategy_type, field_value in valid_results:
            # Get strategy weight
            strategy_weight = self.strategy_weights.get(strategy_type, 0.5)
            
            # Get historical performance
            hist_perf = context.historical_performance.get(strategy_type.value, {})
            performance_score = hist_perf.get('accuracy', 0.5) if hist_perf else 0.5
            
            # Combined score
            combined_score = (
                field_value.confidence * 0.4 +
                strategy_weight * 0.3 +
                performance_score * 0.3
            )
            
            scored_results.append((combined_score, field_value, strategy_type))
        
        # Select best result
        scored_results.sort(key=lambda x: x[0], reverse=True)
        best_score, best_result, best_strategy = scored_results[0]
        
        # ✅ FIX: Check if another strategy has significantly higher confidence
        # If confidence difference > 0.1, prefer the higher confidence result
        for score, result, strategy in scored_results[1:]:
            if result.confidence > best_result.confidence + 0.1:
                # Use the one with higher confidence
                self.logger.info(
                    f"🔄 Overriding {best_strategy.value} (conf: {best_result.confidence:.2f}, score: {best_score:.2f}) "
                    f"with {strategy.value} (conf: {result.confidence:.2f}, score: {score:.2f}) "
                    f"due to significantly higher confidence"
                )
                best_score = score
                best_result = result
                best_strategy = strategy
                break
        
        # Update result metadata
        best_result.confidence = min(best_score, 1.0)
        best_result.method = f'hybrid-{best_strategy.value}'
        best_result.metadata['hybrid_score'] = best_score
        best_result.metadata['strategy_count'] = len(valid_results)
        best_result.metadata['all_strategies'] = [st.value for st, _ in valid_results]
        
        return best_result
    
    def learn_from_feedback(
        self,
        template_id: int,
        extraction_results: Dict[str, Any],
        corrections: Dict[str, str]
    ) -> None:
        """
        Learn from user feedback to improve future extractions
        
        This implements adaptive learning by:
        1. Analyzing which strategies performed well
        2. Updating strategy weights
        3. Recording performance metrics
        """
        self.logger.info(f"Learning from feedback for template {template_id}")
        
        # Analyze feedback
        total_fields = len(extraction_results.get('extracted_data', {}))
        correct_fields = total_fields - len(corrections)
        accuracy = correct_fields / total_fields if total_fields > 0 else 0.0
        
        # Update performance for each strategy used
        strategies_used = extraction_results.get('metadata', {}).get('strategies_used', [])
        
        for strategy_info in strategies_used:
            field_name = strategy_info.get('field')
            method = strategy_info.get('method', '')
            confidence = strategy_info.get('confidence', 0.0)
            
            # Check if this field was corrected
            was_correct = field_name not in corrections
            
            # Update strategy performance
            self._update_strategy_performance(
                template_id, method, was_correct, confidence
            )
        
        # Adjust strategy weights based on performance
        self._adjust_strategy_weights(template_id)
        
        # Save performance history
        self._save_performance_history()
        
        self.logger.info(f"Feedback learning completed. Overall accuracy: {accuracy:.2%}")
    
    def _update_strategy_performance(
        self,
        template_id: int,
        method: str,
        was_correct: bool,
        confidence: float
    ) -> None:
        """Update performance metrics for a strategy"""
        template_key = str(template_id)
        
        if template_key not in self.performance_history:
            self.performance_history[template_key] = {}
        
        if method not in self.performance_history[template_key]:
            self.performance_history[template_key][method] = {
                'accuracy': 0.0,
                'precision': 0.0,
                'recall': 0.0,
                'f1_score': 0.0,
                'confidence_avg': 0.0,
                'extraction_count': 0,
                'correct_count': 0,
                'last_updated': datetime.now().isoformat()
            }
        
        perf = self.performance_history[template_key][method]
        
        # Update counts
        perf['extraction_count'] += 1
        if was_correct:
            perf['correct_count'] += 1
        
        # Update accuracy
        perf['accuracy'] = perf['correct_count'] / perf['extraction_count']
        
        # Update average confidence (exponential moving average)
        alpha = 0.3  # Smoothing factor
        perf['confidence_avg'] = (
            alpha * confidence + (1 - alpha) * perf['confidence_avg']
        )
        
        perf['last_updated'] = datetime.now().isoformat()
    
    def _adjust_strategy_weights(self, template_id: int) -> None:
        """Adjust strategy weights based on performance"""
        template_key = str(template_id)
        
        if template_key not in self.performance_history:
            return
        
        # Get performance for each strategy
        performances = self.performance_history[template_key]
        
        # Calculate new weights based on accuracy
        total_accuracy = 0.0
        strategy_accuracies = {}
        
        for method, perf in performances.items():
            if 'rule' in method:
                strategy_type = StrategyType.RULE_BASED
            elif 'position' in method:
                strategy_type = StrategyType.POSITION_BASED
            elif 'crf' in method:
                strategy_type = StrategyType.CRF
            else:
                continue
            
            accuracy = perf.get('accuracy', 0.0)
            strategy_accuracies[strategy_type] = accuracy
            total_accuracy += accuracy
        
        # Update weights (normalize to sum to 1.0)
        if total_accuracy > 0:
            for strategy_type, accuracy in strategy_accuracies.items():
                self.strategy_weights[strategy_type] = accuracy / total_accuracy
        
        self.logger.info(f"Updated strategy weights: {self.strategy_weights}")
    
    def get_performance_metrics(
        self,
        template_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get performance metrics for evaluation
        
        Returns metrics for thesis evaluation (BAB 4)
        """
        if template_id:
            template_key = str(template_id)
            return self.performance_history.get(template_key, {})
        else:
            # Aggregate across all templates
            return {
                'templates': len(self.performance_history),
                'total_extractions': sum(
                    sum(perf.get('extraction_count', 0) for perf in template_perf.values())
                    for template_perf in self.performance_history.values()
                ),
                'strategy_weights': self.strategy_weights,
                'per_template': self.performance_history
            }
    
    def _extract_words_from_pdf(self, pdf_path: str) -> List[Dict]:
        """Extract all words from PDF"""
        import pdfplumber
        
        all_words = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    words = page.extract_words(x_tolerance=3, y_tolerance=3)
                    all_words.extend(words)
        except Exception as e:
            self.logger.error(f"Error extracting words from PDF: {e}")
        
        return all_words
    
    def _load_performance_history(self) -> None:
        """Load performance history from file"""
        try:
            if os.path.exists(self.performance_file):
                with open(self.performance_file, 'r') as f:
                    self.performance_history = json.load(f)
                self.logger.info(f"Loaded performance history from {self.performance_file}")
        except Exception as e:
            self.logger.error(f"Error loading performance history: {e}")
            self.performance_history = {}
    
    def _save_performance_history(self) -> None:
        """Save performance history to file"""
        try:
            os.makedirs(os.path.dirname(self.performance_file), exist_ok=True)
            with open(self.performance_file, 'w') as f:
                json.dump(self.performance_history, f, indent=2)
            self.logger.info(f"Saved performance history to {self.performance_file}")
        except Exception as e:
            self.logger.error(f"Error saving performance history: {e}")
