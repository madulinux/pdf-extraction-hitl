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
import time  # ✅ NEW: For extraction time tracking
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

# from .position_based_strategy import PositionExtractionStrategy
# from .rule_based_strategy import RuleBasedExtractionStrategy


class StrategyType(Enum):
    """Enumeration of available extraction strategies"""
    RULE_BASED = "rule_based"
    POSITION_BASED = "position_based"
    CRF = "crf"
    
    @staticmethod
    def normalize(method: str) -> str:
        """
        Normalize strategy type to standard enum value
        
        Handles legacy/variant naming:
        - 'crf-model' → 'crf'
        - 'rule-based' → 'rule_based'
        - 'rule-based-label' → 'rule_based'
        - 'position-based' → 'position_based'
        
        Args:
            method: Strategy method name (can be variant)
            
        Returns:
            Normalized strategy type matching enum value
        """
        if not method:
            return "rule_based"  # Default fallback
        
        method_lower = method.lower().strip()
        
        # CRF variants
        if 'crf' in method_lower:
            return StrategyType.CRF.value
        
        # Rule-based variants
        if 'rule' in method_lower:
            return StrategyType.RULE_BASED.value
        
        # Position-based variants
        if 'position' in method_lower:
            return StrategyType.POSITION_BASED.value
        
        # If already normalized, return as-is
        try:
            for st in StrategyType:
                if method_lower == st.value:
                    return st.value
        except:
            pass
        
        # Fallback to rule_based
        return StrategyType.RULE_BASED.value


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
    
    # ✅ CONFIG: Adaptive threshold configuration
    CONFIDENCE_THRESHOLDS = {
        'high_performance': {'min_accuracy': 0.7, 'min_attempts': 10, 'threshold': 0.3},
        'medium_performance': {'min_accuracy': 0.5, 'min_attempts': 5, 'threshold': 0.4},
        'low_performance': {'min_accuracy': 0.0, 'min_attempts': 0, 'threshold': 0.5}
    }
    
    # ✅ CONFIG: Adaptive weighting configuration
    SCORING_WEIGHTS = {
        'proven': {'min_attempts': 10, 'confidence': 0.15, 'strategy': 0.05, 'performance': 0.80},
        'established': {'min_attempts': 5, 'confidence': 0.20, 'strategy': 0.10, 'performance': 0.70},
        'new': {'min_attempts': 0, 'confidence': 0.35, 'strategy': 0.25, 'performance': 0.40}
    }
    
    def __init__(self, db = None, performance_file: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.db = db  # ✅ Store database connection for performance queries
        
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
            StrategyType.RULE_BASED: 0.5,
            StrategyType.POSITION_BASED: 0.4,
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
        # ✅ NEW: Start timing extraction
        start_time = time.time()
        
        template_id = template_config.get('template_id', 0)
        template_name = template_config.get('template_name', 'unknown')
        
        print(f"🔍 [HybridStrategy] Starting extraction for template {template_name}")
        
        # Initialize CRF strategy if model available
        print(f"🔍 [HybridStrategy] Checking model path: {model_path}")
        if model_path:
            if os.path.exists(model_path):
                print(f"✅ [HybridStrategy] Model file exists: {model_path}")
                self.crf_strategy = CRFExtractionStrategy(model_path)
                
                # ✅ ADAPTIVE: Set initial weight based on historical performance
                crf_weight = self._get_adaptive_crf_weight(template_id)
                self.strategy_weights[StrategyType.CRF] = crf_weight
                print(f"✅ [HybridStrategy] CRF strategy initialized with adaptive weight {crf_weight:.2f}")
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
                'strategies_used': [],
                'all_strategies_attempted': []  # ✅ Track ALL strategies (for performance tracking)
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
                    'field_name': field_name,  # ✅ Fixed: use 'field_name' not 'field'
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
                    
                    # ✅ CRITICAL: Copy all_strategies_attempted for performance tracking
                    if 'all_strategies_attempted' in metadata:
                        strategy_info['all_strategies_attempted'] = metadata['all_strategies_attempted']
                
                results['metadata']['strategies_used'].append(strategy_info)
                
                # Add conflict info if detected
                if 'conflict' in extraction_result:
                    results['conflicts'][field_name] = extraction_result['conflict']
            else:
                results['extracted_data'][field_name] = ''
                results['confidence_scores'][field_name] = 0.0
                results['extraction_methods'][field_name] = 'none'
        
        # ✅ NEW: Calculate extraction time
        extraction_time_ms = int((time.time() - start_time) * 1000)
        results['extraction_time_ms'] = extraction_time_ms
        
        self.logger.info(f"Extraction completed: {len(results['extracted_data'])} fields in {extraction_time_ms}ms")
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
            temp_field_config = field_config.copy()
            temp_field_config['locations'] = [location]
            
            # Extract using all strategies
            strategy_results = self._extract_field_with_strategies(
                pdf_path, temp_field_config, all_words, context
            )
            
            # Combine strategy results
            final_result = self._combine_strategy_results(
                strategy_results, context, field_name
            )
            
            if final_result:
                result_dict = {
                    'value': final_result.value,
                    'confidence': final_result.confidence,
                    'method': final_result.method,
                    'location_index': location_idx,
                    'page': location.get('page', 0),
                    'label': location.get('context', {}).get('label')
                }
                
                # ✅ CRITICAL: Preserve all_strategies_attempted from final_result
                if 'all_strategies_attempted' in final_result.metadata:
                    result_dict['all_strategies_attempted'] = final_result.metadata['all_strategies_attempted']
                
                all_extraction_results.append(result_dict)
        
        # If no results from any location, return None
        if not all_extraction_results:
            return None
        
        # Detect conflicts
        conflict_info = detect_conflicts(field_name, all_extraction_results)
        
        # Select best result
        best_result = max(all_extraction_results, key=lambda r: r['confidence'])
        
        # ✅ FIX: Preserve all_strategies_attempted from best result
        metadata = {
            'location_index': best_result.get('location_index', 0),
            'page': best_result.get('page', 0),
            'label': best_result.get('label')
        }
        
        # ✅ CRITICAL: Copy all_strategies_attempted if present
        if 'all_strategies_attempted' in best_result:
            metadata['all_strategies_attempted'] = best_result['all_strategies_attempted']
        
        result = {
            'value': best_result['value'],
            'confidence': best_result['confidence'],
            'method': best_result['method'],
            'metadata': metadata
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
        
        # ✅ CRITICAL: Always try CRF if model available (for performance tracking)
        if self.crf_strategy:
            self.logger.debug(f"  🤖 Trying CRF strategy for '{field_name}'...")
            try:
                crf_result = self.crf_strategy.extract(pdf_path, field_config, all_words)
                # ✅ ALWAYS store result (even if None) for performance tracking
                results[StrategyType.CRF] = crf_result
                if crf_result:
                    self.logger.info(f"  ✅ CRF: {crf_result.value[:50]}... (conf: {crf_result.confidence:.4f})")
                else:
                    # ✅ Log when CRF returns None (important for debugging)
                    self.logger.warning(f"  ⚠️ CRF returned None for '{field_name}' - model may not have learned this field yet")
            except Exception as e:
                self.logger.error(f"  ❌ CRF extraction failed for '{field_name}': {e}")
                # ✅ Store None to track failure in performance
                results[StrategyType.CRF] = None
        else:
            self.logger.debug(f"  ⚠️ CRF strategy not available (model not loaded)")
        
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
        # ✅ ADAPTIVE CONFIDENCE THRESHOLD
        # Filter results based on adaptive minimum confidence
        # Lower threshold for strategies with proven track record
        field_performance = self._get_field_performance_from_db(context.template_id, field_name)
        
        valid_results = []
        for st, fv in strategy_results.items():
            if fv is None:
                continue
            
            # Get historical performance for this strategy
            perf_data = field_performance.get(st.value, {'accuracy': 0.5, 'attempts': 0})
            hist_accuracy = perf_data.get('accuracy', 0.5) if isinstance(perf_data, dict) else perf_data
            hist_attempts = perf_data.get('attempts', 0) if isinstance(perf_data, dict) else 0
            
            # ✅ ADAPTIVE THRESHOLD based on historical performance (CONFIG-DRIVEN)
            min_confidence = self._get_confidence_threshold(hist_accuracy, hist_attempts)
            
            # ✅ CRITICAL: Hard minimum threshold to reject extremely low confidence
            # Even if historical performance is good, reject if confidence < 0.3
            # This prevents selecting garbage results from poorly trained models
            # Lowered to 0.3 to allow fallback for marginal results
            HARD_MIN_CONFIDENCE = 0.3
            effective_min_confidence = max(min_confidence, HARD_MIN_CONFIDENCE)
            
            # Accept result if confidence meets adaptive threshold
            if fv.confidence >= effective_min_confidence:
                valid_results.append((st, fv))
                self.logger.debug(
                    f"  ✅ {st.value}: conf={fv.confidence:.2f} >= threshold={effective_min_confidence:.2f} "
                    f"(adaptive={min_confidence:.2f}, hard_min={HARD_MIN_CONFIDENCE:.2f}, hist_acc={hist_accuracy:.2f})"
                )
            else:
                self.logger.debug(
                    f"  ❌ {st.value}: conf={fv.confidence:.2f} < threshold={effective_min_confidence:.2f} "
                    f"(adaptive={min_confidence:.2f}, hard_min={HARD_MIN_CONFIDENCE:.2f}) - REJECTED"
                )
        
        if not valid_results:
            self.logger.warning(f"  ⚠️ No strategies met confidence threshold for '{field_name}'")
            
            # Count how many strategies returned results
            non_none_results = sum(1 for fv in strategy_results.values() if fv is not None)
            self.logger.info(f"  📊 Strategy results: {non_none_results}/{len(strategy_results)} strategies returned results")
            
            # ✅ IMPROVED FALLBACK: Use best available result even if below threshold
            # Find the best result among all strategies (even if below threshold)
            best_result = None
            best_confidence = 0.0
            best_strategy = None
            
            for strategy_type, field_value in strategy_results.items():
                # ✅ FIX: Check field_value exists and has confidence, don't check if value is truthy
                # Empty string '' is a valid value that should be considered
                # Accept ANY result with confidence > 0 (even 0.01)
                if field_value and field_value.confidence > 0 and field_value.confidence > best_confidence:
                    best_result = field_value
                    best_confidence = field_value.confidence
                    best_strategy = strategy_type
                    self.logger.debug(f"    🔍 Found candidate: {strategy_type.value} (conf={field_value.confidence:.2f}, value='{field_value.value}')")
            
            # If we found any result, use it as fallback
            if best_result:
                self.logger.info(f"  🔄 Using fallback: {best_strategy.value} (confidence: {best_confidence:.2f}, value: '{best_result.value}')")
                from .strategies import FieldValue
                fallback_result = FieldValue(
                    field_id=field_name,
                    field_name=field_name,
                    value=best_result.value,
                    confidence=best_confidence,
                    method=f'{best_strategy.value}_fallback',
                    metadata={
                        'all_strategies_attempted': {
                            st.value: {
                                'success': fv is not None,
                                'confidence': fv.confidence if fv else 0.0,
                                'value': fv.value if fv else None
                            }
                            for st, fv in strategy_results.items()
                        },
                        'selected_by': 'fallback',
                        'reason': 'best_below_threshold',
                        'original_strategy': best_strategy.value
                    }
                )
                return fallback_result
            
            # If absolutely no results, return empty
            self.logger.warning(f"  ⚠️ No fallback available for '{field_name}' - returning method='none'")
            from .strategies import FieldValue
            dummy_result = FieldValue(
                field_id=field_name,
                field_name=field_name,
                value='',
                confidence=0.0,
                method='none',
                metadata={
                    'all_strategies_attempted': {
                        st.value: {
                            'success': fv is not None,
                            'confidence': fv.confidence if fv else 0.0,
                            'value': fv.value if fv else None
                        }
                        for st, fv in strategy_results.items()
                    },
                    'selected_by': 'none_valid',
                    'reason': 'all_strategies_failed'
                }
            )
            return dummy_result
        
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
        
        # ✅ NEW: Log scoring details for debugging
        self.logger.info(f"\n🎯 Scoring {len(valid_results)} strategies for field '{field_name}':")
        
        # ✅ Load performance from DATABASE (not JSON file)
        field_performance = self._get_field_performance_from_db(context.template_id, field_name)
        
        for strategy_type, field_value in valid_results:
            # Get strategy weight
            strategy_weight = self.strategy_weights.get(strategy_type, 0.5)
            
            # ✅ Get historical performance from DATABASE for this specific field
            perf_data = field_performance.get(strategy_type.value, {'accuracy': 0.5, 'attempts': 0})
            
            # Extract accuracy and attempts
            if isinstance(perf_data, dict):
                performance_score = perf_data.get('accuracy', 0.5)
                attempts = perf_data.get('attempts', 0)
            else:
                # Backward compatibility: if perf_data is just a number
                performance_score = perf_data
                attempts = 0
            
            # ✅ ADAPTIVE WEIGHTING based on data availability (CONFIG-DRIVEN)
            weights = self._get_scoring_weights(attempts)
            
            # Combined score (ADAPTIVE FORMULA)
            combined_score = (
                field_value.confidence * weights['confidence'] +
                strategy_weight * weights['strategy'] +
                performance_score * weights['performance']
            )
            
            # ✅ NEW: Log each strategy's scoring with adaptive weights
            self.logger.info(
                f"  {strategy_type.value:15s}: "
                f"conf={field_value.confidence:.4f}×{weights['confidence']:.2f}={field_value.confidence*weights['confidence']:.4f} + "
                f"weight={strategy_weight:.2f}×{weights['strategy']:.2f}={strategy_weight*weights['strategy']:.4f} + "
                f"perf={performance_score:.4f}×{weights['performance']:.2f}={performance_score*weights['performance']:.4f} "
                f"(attempts={attempts}) = {combined_score:.4f} | value='{field_value.value[:30]}...'"
            )
            
            scored_results.append((combined_score, field_value, strategy_type))
        
        # Select best result (highest score wins, no override)
        scored_results.sort(key=lambda x: x[0], reverse=True)
        best_score, best_result, best_strategy = scored_results[0]
        
        # ✅ Log winner with comparison
        self.logger.info(f"  🏆 Winner: {best_strategy.value} (score: {best_score:.4f})")
        if len(scored_results) > 1:
            runner_up_score, runner_up_result, runner_up_strategy = scored_results[1]
            self.logger.info(
                f"  🥈 Runner-up: {runner_up_strategy.value} (score: {runner_up_score:.4f}, "
                f"margin: {best_score - runner_up_score:.4f})"
            )
        
        # Update result metadata
        best_result.confidence = min(best_score, 1.0)
        best_result.method = best_strategy.value  # ✅ Direct strategy name (no 'hybrid-' prefix)
        best_result.metadata['hybrid_score'] = best_score
        best_result.metadata['strategy_count'] = len(valid_results)
        best_result.metadata['all_strategies'] = [st.value for st, _ in valid_results]
        best_result.metadata['selected_by'] = 'hybrid_strategy'  # ✅ Track that hybrid made the selection
        
        # ✅ NEW: Track ALL strategies attempted (including None results) for performance tracking
        best_result.metadata['all_strategies_attempted'] = {
            st.value: {
                'success': fv is not None,
                'confidence': fv.confidence if fv else 0.0,
                'value': fv.value if fv else None
            }
            for st, fv in strategy_results.items()
        }
        
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
        
        # ✅ CRITICAL: Update performance for ALL strategies attempted (not just selected)
        strategies_used = extraction_results.get('metadata', {}).get('strategies_used', [])
        
        for strategy_info in strategies_used:
            field_name = strategy_info.get('field_name')  # ✅ FIXED: use 'field_name' not 'field'
            method = strategy_info.get('method', '')
            confidence = strategy_info.get('confidence', 0.0)
            
            # ✅ CRITICAL: Skip if field_name is None (should not happen with correct metadata)
            if not field_name:
                self.logger.warning(f"⚠️ Skipping strategy_info with missing field_name: {strategy_info}")
                continue
            
            # Check if this field was corrected
            was_correct = field_name not in corrections
            
            # ✅ Update performance for SELECTED strategy
            self._update_strategy_performance(
                template_id, field_name, method, was_correct, confidence
            )
            
            # ✅ CRITICAL: Track performance for ALL attempted strategies
            # This ensures CRF gets tracked even when not selected
            all_attempted = strategy_info.get('all_strategies_attempted', {})
            for strategy_name, strategy_data in all_attempted.items():
                if strategy_name != method:  # Don't double-count the selected strategy
                    # ✅ FIX: Check if this strategy's value matches the corrected value
                    # If field was corrected, check against corrected value
                    # If field was NOT corrected, it means selected strategy was correct
                    strategy_value = strategy_data.get('value', '')
                    
                    if field_name in corrections:
                        # Field was corrected - check if this strategy had the right value
                        corrected_value = corrections[field_name]
                        
                        # ✅ CRITICAL FIX: Normalize whitespace for comparison
                        # Handle newlines, multiple spaces, leading/trailing whitespace
                        strategy_value_norm = ' '.join(str(strategy_value).split())
                        corrected_value_norm = ' '.join(str(corrected_value).split())
                        
                        strategy_was_correct = (strategy_value_norm == corrected_value_norm)
                        
                        # ✅ DEBUG: Log comparison for troubleshooting
                        if strategy_was_correct:
                            self.logger.info(f"    ✅ {strategy_name} had CORRECT value for '{field_name}'")
                        else:
                            self.logger.debug(f"    ❌ {strategy_name} had WRONG value for '{field_name}'")
                            self.logger.debug(f"       Strategy: '{strategy_value_norm[:50]}'")
                            self.logger.debug(f"       Corrected: '{corrected_value_norm[:50]}'")
                    else:
                        # Field was NOT corrected - selected strategy was correct
                        # Check if this strategy also had the same (correct) value
                        selected_value = extraction_results.get('extracted_data', {}).get(field_name, '')
                        
                        # ✅ CRITICAL FIX: Normalize whitespace for comparison
                        strategy_value_norm = ' '.join(str(strategy_value).split())
                        selected_value_norm = ' '.join(str(selected_value).split())
                        
                        strategy_was_correct = (strategy_value_norm == selected_value_norm)
                    
                    self._update_strategy_performance(
                        template_id, 
                        field_name,
                        strategy_name, 
                        was_correct=strategy_was_correct,  # ✅ Based on actual value comparison
                        confidence=strategy_data.get('confidence', 0.0)
                    )
        
        # Adjust strategy weights based on performance
        self._adjust_strategy_weights(template_id)
        
        # Save performance history
        self._save_performance_history()
        
        self.logger.info(f"Feedback learning completed. Overall accuracy: {accuracy:.2%}")
    
    def _update_strategy_performance(
        self,
        template_id: int,
        field_name: str,
        method: str,
        was_correct: bool,
        confidence: float
    ) -> None:
        """
        Update performance metrics for a strategy
        
        ✅ UPDATED: Now tracks per-field performance in database with normalized strategy types
        """
        # ✅ NORMALIZE strategy type to standard enum value
        normalized_method = StrategyType.normalize(method)
        
        # ✅ Update database performance tracking (per-field)
        if self.db:
            try:
                from database.repositories.strategy_performance_repository import StrategyPerformanceRepository
                perf_repo = StrategyPerformanceRepository(self.db)
                perf_repo.update_performance(
                    template_id=template_id,
                    field_name=field_name,
                    strategy_type=normalized_method,  # ✅ Use normalized value
                    was_correct=was_correct
                )
            except Exception as e:
                self.logger.error(f"Failed to update database performance: {e}")
        
        # ✅ Also update JSON file (legacy) - use normalized method
        template_key = str(template_id)
        
        if template_key not in self.performance_history:
            self.performance_history[template_key] = {}
        
        if normalized_method not in self.performance_history[template_key]:
            self.performance_history[template_key][normalized_method] = {
                'accuracy': 0.0,
                'precision': 0.0,
                'recall': 0.0,
                'f1_score': 0.0,
                'confidence_avg': 0.0,
                'extraction_count': 0,
                'correct_count': 0,
                'last_updated': datetime.now().isoformat()
            }
        
        perf = self.performance_history[template_key][normalized_method]
        
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
    
    def _get_adaptive_crf_weight(self, template_id: int) -> float:
        """
        Calculate adaptive CRF weight based on historical performance
        
        Args:
            template_id: Template ID
            
        Returns:
            Weight between 0.3 and 0.9
        """
        if not self.db:
            return 0.5  # Default neutral weight
        
        try:
            conn = self.db.get_connection()
            cursor = conn.execute("""
                SELECT AVG(accuracy) as avg_accuracy, COUNT(*) as total_fields
                FROM strategy_performance
                WHERE template_id = ? AND strategy_type = 'crf'
                AND total_extractions >= 5
            """, (template_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row and row['avg_accuracy'] is not None and row['total_fields'] > 0:
                avg_accuracy = row['avg_accuracy']
                total_fields = row['total_fields']
                
                # ✅ ADAPTIVE FORMULA:
                # - If CRF performs well (>70%): weight 0.7-0.9
                # - If CRF performs OK (50-70%): weight 0.5-0.7
                # - If CRF performs poorly (<50%): weight 0.3-0.5
                # - More fields = more confidence in the weight
                
                confidence_factor = min(1.0, total_fields / 10.0)  # Max confidence at 10+ fields
                base_weight = 0.3 + (avg_accuracy * 0.6)  # Scale 0.3-0.9
                adaptive_weight = base_weight * confidence_factor + 0.5 * (1 - confidence_factor)
                
                return max(0.3, min(0.9, adaptive_weight))
            else:
                # No historical data: start with moderate weight
                return 0.5
                
        except Exception as e:
            self.logger.error(f"Error calculating adaptive CRF weight: {e}")
            return 0.5
    
    def _get_confidence_threshold(self, accuracy: float, attempts: int) -> float:
        """
        Get adaptive confidence threshold based on historical performance
        
        Args:
            accuracy: Historical accuracy (0.0-1.0)
            attempts: Number of attempts
            
        Returns:
            Minimum confidence threshold (0.3-0.5)
        """
        for level, config in self.CONFIDENCE_THRESHOLDS.items():
            if accuracy >= config['min_accuracy'] and attempts >= config['min_attempts']:
                return config['threshold']
        
        # Default: low performance threshold
        return self.CONFIDENCE_THRESHOLDS['low_performance']['threshold']
    
    def _get_scoring_weights(self, attempts: int) -> Dict[str, float]:
        """
        Get adaptive scoring weights based on number of attempts
        
        Args:
            attempts: Number of historical attempts
            
        Returns:
            Dict with 'confidence', 'strategy', 'performance' weights
        """
        if attempts >= self.SCORING_WEIGHTS['proven']['min_attempts']:
            return {
                'confidence': self.SCORING_WEIGHTS['proven']['confidence'],
                'strategy': self.SCORING_WEIGHTS['proven']['strategy'],
                'performance': self.SCORING_WEIGHTS['proven']['performance']
            }
        elif attempts >= self.SCORING_WEIGHTS['established']['min_attempts']:
            return {
                'confidence': self.SCORING_WEIGHTS['established']['confidence'],
                'strategy': self.SCORING_WEIGHTS['established']['strategy'],
                'performance': self.SCORING_WEIGHTS['established']['performance']
            }
        else:
            return {
                'confidence': self.SCORING_WEIGHTS['new']['confidence'],
                'strategy': self.SCORING_WEIGHTS['new']['strategy'],
                'performance': self.SCORING_WEIGHTS['new']['performance']
            }
    
    def _get_field_performance_from_db(self, template_id: int, field_name: str) -> Dict[str, Dict]:
        """
        Get strategy performance for a specific field from database
        
        Returns:
            Dict mapping strategy_type -> {'accuracy': float, 'attempts': int}
        """
        if not self.db:
            return {}
        
        try:
            conn = self.db.get_connection()
            cursor = conn.execute("""
                SELECT strategy_type, accuracy, total_extractions
                FROM strategy_performance
                WHERE template_id = ? AND field_name = ?
                ORDER BY accuracy DESC
            """, (template_id, field_name))
            
            performance = {}
            for row in cursor.fetchall():
                strategy_type = row['strategy_type']
                accuracy = row['accuracy']
                attempts = row['total_extractions']
                performance[strategy_type] = {
                    'accuracy': accuracy,
                    'attempts': attempts
                }
            
            conn.close()
            return performance
        except Exception as e:
            self.logger.error(f"Error loading field performance from DB: {e}")
            return {}
    
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
