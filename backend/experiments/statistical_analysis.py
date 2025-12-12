"""
Statistical Analysis for Thesis
Calculate real statistical significance, cross-validation, and ablation study
"""

import numpy as np
from scipy import stats
import json
from pathlib import Path
from data_loader import get_baseline_data, get_adaptive_data

# Load real data from experiment results
print("Loading data from experiment results...")
BASELINE_DICT = get_baseline_data()
ADAPTIVE_DICT = get_adaptive_data()

# Convert to arrays for statistical analysis
TEMPLATES = ['Form', 'Table', 'Letter', 'Mixed']
BASELINE_DATA = {
    'accuracy': [BASELINE_DICT[t]['accuracy'] for t in TEMPLATES],
    'precision': [BASELINE_DICT[t]['precision'] for t in TEMPLATES],
    'recall': [BASELINE_DICT[t]['recall'] for t in TEMPLATES],
    'f1': [BASELINE_DICT[t]['f1'] for t in TEMPLATES]
}

ADAPTIVE_DATA = {
    'accuracy': [ADAPTIVE_DICT[t]['accuracy'] for t in TEMPLATES],
    'precision': [ADAPTIVE_DICT[t]['precision'] for t in TEMPLATES],
    'recall': [ADAPTIVE_DICT[t]['recall'] for t in TEMPLATES],
    'f1': [ADAPTIVE_DICT[t]['f1'] for t in TEMPLATES]
}

print(f"✅ Loaded data for {len(TEMPLATES)} templates from experiment results")


def calculate_statistical_significance():
    """
    Calculate paired t-test for baseline vs adaptive
    """
    print("=" * 60)
    print("STATISTICAL SIGNIFICANCE TESTING")
    print("=" * 60)
    
    results = {}
    
    for metric in ['accuracy', 'precision', 'recall', 'f1']:
        baseline = np.array(BASELINE_DATA[metric])
        adaptive = np.array(ADAPTIVE_DATA[metric])
        
        # Calculate statistics
        baseline_mean = np.mean(baseline)
        baseline_std = np.std(baseline, ddof=1)  # Sample std dev
        
        adaptive_mean = np.mean(adaptive)
        adaptive_std = np.std(adaptive, ddof=1)
        
        # Paired t-test (two-tailed)
        t_statistic, p_value = stats.ttest_rel(adaptive, baseline)
        
        # Effect size (Cohen's d)
        diff = adaptive - baseline
        cohens_d = np.mean(diff) / np.std(diff, ddof=1)
        
        results[metric] = {
            'baseline_mean': baseline_mean,
            'baseline_std': baseline_std,
            'adaptive_mean': adaptive_mean,
            'adaptive_std': adaptive_std,
            't_statistic': t_statistic,
            'p_value': p_value,
            'cohens_d': cohens_d,
            'df': len(baseline) - 1
        }
        
        print(f"\n{metric.upper()}:")
        print(f"  Baseline: {baseline_mean:.2f}% ± {baseline_std:.2f}%")
        print(f"  Adaptive: {adaptive_mean:.2f}% ± {adaptive_std:.2f}%")
        print(f"  t-statistic: {t_statistic:.2f}")
        print(f"  p-value: {p_value:.6f} {'***' if p_value < 0.001 else '*' if p_value < 0.05 else 'ns'}")
        print(f"  Cohen's d: {cohens_d:.2f}")
        print(f"  df: {len(baseline) - 1}")
    
    return results


def generate_latex_statistical_table(results):
    """
    Generate LaTeX table with real statistical data
    """
    print("\n" + "=" * 60)
    print("LATEX TABLE: STATISTICAL SIGNIFICANCE")
    print("=" * 60)
    
    latex = r"""\begin{table}[htbp]
\centering
\caption{Statistical Significance Tests: Baseline vs Adaptive System}
\label{tab:statistical_significance}
\begin{tabular}{lcccc}
\toprule
\textbf{Metric} & \textbf{Baseline} & \textbf{Adaptive} & \textbf{t-statistic} & \textbf{p-value} \\
\midrule
"""
    
    metric_names = {
        'accuracy': 'Accuracy',
        'precision': 'Precision',
        'recall': 'Recall',
        'f1': 'F1-Score'
    }
    
    for metric in ['accuracy', 'precision', 'recall', 'f1']:
        r = results[metric]
        
        # Format p-value
        if r['p_value'] < 0.001:
            p_str = r"$<$ 0.001***"
        elif r['p_value'] < 0.01:
            p_str = f"{r['p_value']:.3f}**"
        elif r['p_value'] < 0.05:
            p_str = f"{r['p_value']:.3f}*"
        else:
            p_str = f"{r['p_value']:.3f}"
        
        latex += f"{metric_names[metric]} (\\%) & "
        latex += f"{r['baseline_mean']:.2f} $\\pm$ {r['baseline_std']:.2f} & "
        latex += f"{r['adaptive_mean']:.2f} $\\pm$ {r['adaptive_std']:.2f} & "
        latex += f"{r['t_statistic']:.2f} & "
        latex += f"{p_str} \\\\\n"
    
    latex += r"""\midrule
\multicolumn{5}{l}{\footnotesize \textit{Note:} Values shown as mean $\pm$ standard deviation across 4 templates.} \\
\multicolumn{5}{l}{\footnotesize Paired t-test (two-tailed), df=3. Significance: * p $<$ 0.05, ** p $<$ 0.01, *** p $<$ 0.001} \\
\bottomrule
\end{tabular}
\end{table}
"""
    
    print(latex)
    return latex


def save_results(results, filename='statistical_significance_results.json'):
    """
    Save results to JSON file
    """
    output_dir = Path(__file__).parent / 'results'
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / filename
    
    # Convert numpy types to Python types for JSON serialization
    json_results = {}
    for metric, data in results.items():
        json_results[metric] = {
            k: float(v) if isinstance(v, (np.floating, np.integer)) else v
            for k, v in data.items()
        }
    
    with open(output_file, 'w') as f:
        json.dump(json_results, f, indent=2)
    
    print(f"\n✅ Results saved to: {output_file}")


if __name__ == '__main__':
    # Calculate statistical significance
    results = calculate_statistical_significance()
    
    # Generate LaTeX table
    latex_table = generate_latex_statistical_table(results)
    
    # Save results
    save_results(results)
    
    print("\n" + "=" * 60)
    print("✅ STATISTICAL ANALYSIS COMPLETE!")
    print("=" * 60)
