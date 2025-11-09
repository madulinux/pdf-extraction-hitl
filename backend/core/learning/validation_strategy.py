"""
Smart Validation Strategy

Determines when to run data quality checks based on context.
"""
import os
import json
from pathlib import Path
from typing import Dict, Any


class ValidationStrategy:
    """
    Smart strategy for when to run data quality validation
    """
    
    def __init__(self, template_id: int, validation_cache_dir: str = "data/validation_cache"):
        self.template_id = template_id
        self.validation_cache_dir = Path(validation_cache_dir)
        self.validation_cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.validation_cache_dir / f"template_{template_id}_validation.json"
    
    def should_validate(
        self,
        num_samples: int,
        is_incremental: bool = False,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Determine if validation should run
        
        Args:
            num_samples: Number of training samples
            is_incremental: Whether this is incremental training
            force: Force validation regardless of cache
            
        Returns:
            Dict with decision and reason
        """
        # Force validation
        if force:
            return {
                'should_validate': True,
                'reason': 'Forced validation',
                'skip_leakage': False,
                'skip_diversity': False
            }
        
        # Check cache
        cache = self._load_cache()
        
        # First training - ALWAYS validate
        if not cache:
            return {
                'should_validate': True,
                'reason': 'First training - baseline validation required',
                'skip_leakage': False,
                'skip_diversity': False
            }
        
        # Incremental training - SKIP validation
        if is_incremental:
            return {
                'should_validate': False,
                'reason': 'Incremental training - using cached validation',
                'skip_leakage': True,
                'skip_diversity': True
            }
        
        # Check if data changed significantly
        last_num_samples = cache.get('num_samples', 0)
        change_ratio = abs(num_samples - last_num_samples) / last_num_samples if last_num_samples > 0 else 1.0
        
        # Major change (>50%) - VALIDATE
        if change_ratio > 0.5:
            return {
                'should_validate': True,
                'reason': f'Major data change ({change_ratio:.1%}) - revalidation required',
                'skip_leakage': False,
                'skip_diversity': False
            }
        
        # Minor change (<50%) - SKIP full validation, only diversity
        if change_ratio > 0.1:
            return {
                'should_validate': True,
                'reason': f'Minor data change ({change_ratio:.1%}) - quick diversity check',
                'skip_leakage': True,  # Skip expensive leakage check
                'skip_diversity': False  # Quick diversity check
            }
        
        # No significant change - SKIP
        return {
            'should_validate': False,
            'reason': 'No significant data change - using cached validation',
            'skip_leakage': True,
            'skip_diversity': True
        }
    
    def save_validation_results(
        self,
        num_samples: int,
        diversity_metrics: Dict[str, Any],
        leakage_results: Dict[str, Any] = None
    ) -> None:
        """
        Save validation results to cache
        
        Args:
            num_samples: Number of training samples
            diversity_metrics: Diversity validation results
            leakage_results: Leakage detection results (optional)
        """
        cache = {
            'template_id': self.template_id,
            'num_samples': num_samples,
            'last_validated': str(os.path.getctime(self.cache_file)) if self.cache_file.exists() else None,
            'diversity_metrics': diversity_metrics,
            'leakage_results': leakage_results or {}
        }
        
        with open(self.cache_file, 'w') as f:
            json.dump(cache, f, indent=2)
    
    def _load_cache(self) -> Dict[str, Any]:
        """Load validation cache if exists"""
        if not self.cache_file.exists():
            return {}
        
        try:
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    
    def get_cached_results(self) -> Dict[str, Any]:
        """Get cached validation results"""
        return self._load_cache()


# Usage example
if __name__ == '__main__':
    strategy = ValidationStrategy(template_id=1)
    
    # First training
    decision = strategy.should_validate(num_samples=100)
    print(f"Decision: {decision}")
    # Output: {'should_validate': True, 'reason': 'First training...'}
    
    # Save results
    strategy.save_validation_results(
        num_samples=100,
        diversity_metrics={'diversity_score': 0.73},
        leakage_results={'leakage_detected': False}
    )
    
    # Incremental training
    decision = strategy.should_validate(num_samples=110, is_incremental=True)
    print(f"Decision: {decision}")
    # Output: {'should_validate': False, 'reason': 'Incremental training...'}
    
    # Major change
    decision = strategy.should_validate(num_samples=200)
    print(f"Decision: {decision}")
    # Output: {'should_validate': True, 'reason': 'Major data change (100%)...'}
