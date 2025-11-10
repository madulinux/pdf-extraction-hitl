"""
Data Extractor - Facade/Adapter for Hybrid Extraction Strategy

This module provides backward compatibility with existing services
while using the new hybrid extraction strategy internally.
"""
from typing import Dict, Any, Optional
from .hybrid_strategy import HybridExtractionStrategy


class DataExtractor:
    """
    Data extractor using hybrid strategy.
    
    This is a facade/adapter that maintains backward compatibility
    with existing code while using the new hybrid extraction strategy.
    """
    
    def __init__(self, template_config: Dict[str, Any], model_path: Optional[str] = None):
        """
        Initialize extractor with template configuration
        
        Args:
            template_config: Template configuration dictionary
            model_path: Path to trained CRF model (optional)
        """
        self.config = template_config
        self.model_path = model_path
        
        print(f"🔍 [DataExtractor] Initialized with model_path: {model_path}")
        
        # Initialize database connection
        from database.db_manager import DatabaseManager
        template_id = template_config.get('template_id', 0)
        db = DatabaseManager() if template_id > 0 else None
        
        # Initialize hybrid strategy with database connection
        self.hybrid_strategy = HybridExtractionStrategy(db=db)
        
        # Initialize post-processor (adaptive, learns from feedback)
        from core.extraction.post_processor import AdaptivePostProcessor
        
        try:
            print(f"🔧 [DataExtractor] Initializing PostProcessor for template {template_id}...")
            self.post_processor = AdaptivePostProcessor(template_id, db)
            print(f"✅ [DataExtractor] PostProcessor initialized successfully")
            print(f"   Loaded patterns for {len(self.post_processor.learned_patterns)} fields")
        except Exception as e:
            print(f"⚠️ Post-processor initialization failed: {e}")
            print(f"   Continuing without post-processing...")
            import traceback
            traceback.print_exc()
            self.post_processor = None
    
    def extract(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract data from a filled PDF document
        
        Args:
            pdf_path: Path to the filled PDF file
            
        Returns:
            Dictionary containing extracted data with confidence scores
            Format matches the old extractor for backward compatibility:
            {
                'extracted_data': {...},
                'confidence_scores': {...},
                'extraction_method': {...},
                'metadata': {...}
            }
        """
        # Use hybrid strategy for extraction
        print(f"🔍 [DataExtractor] Calling hybrid_strategy.extract_all_fields with model_path: {self.model_path}")
        results = self.hybrid_strategy.extract_all_fields(
            pdf_path=pdf_path,
            template_config=self.config,
            model_path=self.model_path
        )
        
        # Apply post-processing (adaptive cleaning based on learned patterns)
        if self.post_processor:
            # ✅ CRITICAL: Reload patterns before processing to get latest learned patterns
            self.post_processor.reload_patterns()
            print(f"🧹 [DataExtractor] Applying adaptive post-processing...")
            results = self.post_processor.process_results(results)
        else:
            print(f"⚠️ [DataExtractor] Post-processing skipped (not initialized)")
        
        # Ensure backward compatibility with old format
        # Old format used 'extraction_method' (singular)
        # New format uses 'extraction_methods' (plural)
        # if 'extraction_methods' in results and 'extraction_method' not in results:
        #     results['extraction_method'] = results['extraction_methods']
        
        return results
    
    def learn_from_feedback(
        self,
        extraction_results: Dict[str, Any],
        corrections: Dict[str, str]
    ) -> None:
        """
        Learn from user feedback to improve future extractions
        
        Args:
            extraction_results: Previous extraction results
            corrections: Dictionary of field corrections {field_name: corrected_value}
        """
        template_id = self.config.get('template_id', 0)
        
        # 1. Hybrid strategy learning (strategy weights, performance tracking)
        self.hybrid_strategy.learn_from_feedback(
            template_id=template_id,
            extraction_results=extraction_results,
            corrections=corrections
        )
        
        # 2. Post-processor learning (cleaning patterns)
        if self.post_processor:
            try:
                self.post_processor.learn_from_feedback(
                    extraction_results=extraction_results,
                    corrections=corrections
                )
                print(f"✅ Post-processor learned from {len(corrections)} corrections")
            except Exception as e:
                print(f"⚠️ Post-processor learning failed: {e}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for this template
        
        Returns:
            Dictionary with performance metrics
        """
        template_id = self.config.get('template_id', 0)
        return self.hybrid_strategy.get_performance_metrics(template_id)
