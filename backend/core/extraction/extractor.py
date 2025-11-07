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
        
        # Initialize hybrid strategy
        self.hybrid_strategy = HybridExtractionStrategy()
    
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
        
        self.hybrid_strategy.learn_from_feedback(
            template_id=template_id,
            extraction_results=extraction_results,
            corrections=corrections
        )
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for this template
        
        Returns:
            Dictionary with performance metrics
        """
        template_id = self.config.get('template_id', 0)
        return self.hybrid_strategy.get_performance_metrics(template_id)
