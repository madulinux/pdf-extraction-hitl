"""
Data Loader Utility
Load experiment results from JSON files instead of hardcoding
"""

import json
from pathlib import Path
from typing import Dict, List


def load_experiment_results(results_dir: Path = None) -> Dict:
    """
    Load all experiment results from JSON files
    
    Returns:
        Dictionary with baseline and adaptive results for all templates
    """
    if results_dir is None:
        results_dir = Path(__file__).parent / 'results'
    
    data = {
        'baseline': {},
        'adaptive': {}
    }
    
    # Load baseline results
    for i in range(1, 5):
        baseline_file = results_dir / f'baseline_template_{i}.json'
        if baseline_file.exists():
            with open(baseline_file, 'r') as f:
                baseline_data = json.load(f)
                template_name = baseline_data['template_name']
                data['baseline'][template_name] = baseline_data
    
    # Load adaptive results
    for i in range(1, 5):
        adaptive_file = results_dir / f'adaptive_template_{i}.json'
        if adaptive_file.exists():
            with open(adaptive_file, 'r') as f:
                adaptive_data = json.load(f)
                template_name = adaptive_data['template_name']
                data['adaptive'][template_name] = adaptive_data
    
    return data


def extract_metrics_by_template(experiment_results: Dict) -> Dict:
    """
    Extract metrics organized by template type
    
    Returns:
        {
            'baseline': {'Form': {...}, 'Table': {...}, ...},
            'adaptive': {'Form': {...}, 'Table': {...}, ...}
        }
    """
    # Map template names to display names
    template_map = {
        'form_template': 'Form',
        'table_template': 'Table',
        'letter_template': 'Letter',
        'mixed_template': 'Mixed'
    }
    
    result = {
        'baseline': {},
        'adaptive': {}
    }
    
    for phase in ['baseline', 'adaptive']:
        for template_name, data in experiment_results[phase].items():
            display_name = template_map.get(template_name, template_name)
            
            metrics = data['metrics']
            result[phase][display_name] = {
                'accuracy': metrics['accuracy'] * 100,  # Convert to percentage
                'precision': metrics['precision'] * 100,
                'recall': metrics['recall'] * 100,
                'f1': metrics['f1_score'] * 100
            }
    
    return result


def get_baseline_data() -> Dict:
    """Get baseline data from experiments"""
    results = load_experiment_results()
    metrics = extract_metrics_by_template(results)
    return metrics['baseline']


def get_adaptive_data() -> Dict:
    """Get adaptive data from experiments"""
    results = load_experiment_results()
    metrics = extract_metrics_by_template(results)
    return metrics['adaptive']


def load_learning_curves() -> Dict:
    """Load learning curve data from all templates"""
    results_dir = Path(__file__).parent / 'results'
    learning_curves = {}
    
    for i in range(1, 5):
        filename = f'learning_curve_{i}.json'
        filepath = results_dir / filename
        
        if filepath.exists():
            with open(filepath, 'r') as f:
                learning_curves[i] = json.load(f)
    
    return learning_curves


if __name__ == '__main__':
    # Test the data loader
    print("=" * 60)
    print("TESTING DATA LOADER")
    print("=" * 60)
    
    # Load all results
    results = load_experiment_results()
    print(f"\nLoaded {len(results['baseline'])} baseline templates")
    print(f"Loaded {len(results['adaptive'])} adaptive templates")
    
    # Extract metrics
    metrics = extract_metrics_by_template(results)
    
    print("\n" + "=" * 60)
    print("BASELINE METRICS")
    print("=" * 60)
    for template, data in metrics['baseline'].items():
        print(f"\n{template}:")
        for metric, value in data.items():
            print(f"  {metric}: {value:.2f}%")
    
    print("\n" + "=" * 60)
    print("ADAPTIVE METRICS")
    print("=" * 60)
    for template, data in metrics['adaptive'].items():
        print(f"\n{template}:")
        for metric, value in data.items():
            print(f"  {metric}: {value:.2f}%")
    
    # Load learning curves
    curves = load_learning_curves()
    print(f"\n" + "=" * 60)
    print(f"LEARNING CURVES")
    print("=" * 60)
    print(f"Loaded {len(curves)} learning curves")
    for template_id, curve in curves.items():
        print(f"\nTemplate {template_id}: {len(curve)} batches")
        print(f"  Initial accuracy: {curve[0]['accuracy']*100:.2f}%")
        print(f"  Final accuracy: {curve[-1]['accuracy']*100:.2f}%")
