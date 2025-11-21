#!/usr/bin/env python3
"""
Generate additional analysis and visualizations for thesis
"""
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle
import seaborn as sns

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

def load_all_data():
    """Load all experiment data"""
    templates = {
        1: "Form Template",
        2: "Table Template", 
        3: "Letter Template",
        4: "Mixed Template"
    }
    
    data = {}
    for tid, tname in templates.items():
        data[tid] = {
            'name': tname,
            'baseline': json.load(open(f'baseline_template_{tid}.json')),
            'adaptive': json.load(open(f'adaptive_template_{tid}.json')),
            'comparison': json.load(open(f'comparison_template_{tid}.json')),
            'learning_curve': json.load(open(f'learning_curve_{tid}.json'))
        }
    
    return data


def generate_error_reduction_chart(data):
    """Generate error reduction visualization"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    templates = [data[tid]['name'] for tid in sorted(data.keys())]
    
    # Chart 1: FP and FN reduction
    baseline_fp = [data[tid]['baseline']['metrics']['false_positives'] for tid in sorted(data.keys())]
    adaptive_fp = [data[tid]['adaptive']['metrics']['false_positives'] for tid in sorted(data.keys())]
    baseline_fn = [data[tid]['baseline']['metrics']['false_negatives'] for tid in sorted(data.keys())]
    adaptive_fn = [data[tid]['adaptive']['metrics']['false_negatives'] for tid in sorted(data.keys())]
    
    x = np.arange(len(templates))
    width = 0.35
    
    # False Positives
    ax1.bar(x - width/2, baseline_fp, width, label='Baseline FP', color='#ef4444', alpha=0.7)
    ax1.bar(x + width/2, adaptive_fp, width, label='Adaptive FP', color='#10b981', alpha=0.7)
    
    ax1.set_xlabel('Template Type', fontsize=12, fontweight='bold')
    ax1.set_ylabel('False Positives Count', fontsize=12, fontweight='bold')
    ax1.set_title('False Positives Reduction', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(templates, rotation=15, ha='right')
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Add reduction percentage labels
    for i, (b, a) in enumerate(zip(baseline_fp, adaptive_fp)):
        if b > 0:
            reduction = ((b - a) / b) * 100
            ax1.text(i, max(b, a) + 10, f'-{reduction:.1f}%', 
                    ha='center', fontsize=10, fontweight='bold', color='#10b981')
    
    # Chart 2: Overall error rate
    baseline_errors = [(data[tid]['baseline']['metrics']['false_positives'] + 
                       data[tid]['baseline']['metrics']['false_negatives']) 
                      for tid in sorted(data.keys())]
    adaptive_errors = [(data[tid]['adaptive']['metrics']['false_positives'] + 
                       data[tid]['adaptive']['metrics']['false_negatives']) 
                      for tid in sorted(data.keys())]
    
    ax2.bar(x - width/2, baseline_errors, width, label='Baseline Errors', color='#ef4444', alpha=0.7)
    ax2.bar(x + width/2, adaptive_errors, width, label='Adaptive Errors', color='#10b981', alpha=0.7)
    
    ax2.set_xlabel('Template Type', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Total Errors (FP + FN)', fontsize=12, fontweight='bold')
    ax2.set_title('Total Error Reduction', fontsize=14, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(templates, rotation=15, ha='right')
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Add reduction percentage labels
    for i, (b, a) in enumerate(zip(baseline_errors, adaptive_errors)):
        if b > 0:
            reduction = ((b - a) / b) * 100
            ax2.text(i, max(b, a) + 10, f'-{reduction:.1f}%', 
                    ha='center', fontsize=10, fontweight='bold', color='#10b981')
    
    plt.tight_layout()
    plt.savefig('error_reduction_analysis.png', dpi=300, bbox_inches='tight')
    print("✅ Error reduction chart saved: error_reduction_analysis.png")


def generate_learning_efficiency_chart(data):
    """Generate learning efficiency visualization"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    templates = [data[tid]['name'] for tid in sorted(data.keys())]
    
    # Chart 1: Corrections vs Improvement
    corrections = [data[tid]['adaptive']['total_corrections'] for tid in sorted(data.keys())]
    improvements = [data[tid]['comparison']['improvement']['absolute'] * 100 for tid in sorted(data.keys())]
    
    colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444']
    
    ax1.scatter(corrections, improvements, s=300, c=colors, alpha=0.6, edgecolors='black', linewidth=2)
    
    # Add labels
    for i, (x, y, name) in enumerate(zip(corrections, improvements, templates)):
        ax1.annotate(name, (x, y), xytext=(5, 5), textcoords='offset points', 
                    fontsize=9, fontweight='bold')
    
    # Add trend line
    z = np.polyfit(corrections, improvements, 1)
    p = np.poly1d(z)
    x_trend = np.linspace(min(corrections), max(corrections), 100)
    ax1.plot(x_trend, p(x_trend), "r--", alpha=0.5, linewidth=2, label='Trend')
    
    ax1.set_xlabel('Total Corrections', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Improvement (%)', fontsize=12, fontweight='bold')
    ax1.set_title('Learning Efficiency: Corrections vs Improvement', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=10)
    
    # Chart 2: Corrections per percentage point
    corr_per_pp = [c / i if i > 0 else 0 for c, i in zip(corrections, improvements)]
    
    bars = ax2.barh(templates, corr_per_pp, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
    
    # Add value labels
    for i, (bar, val) in enumerate(zip(bars, corr_per_pp)):
        ax2.text(val + 0.05, i, f'{val:.2f}', va='center', fontsize=11, fontweight='bold')
    
    # Add efficiency threshold line
    ax2.axvline(x=2.0, color='red', linestyle='--', linewidth=2, alpha=0.5, label='Efficiency Threshold')
    
    ax2.set_xlabel('Corrections per Percentage Point', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Template Type', fontsize=12, fontweight='bold')
    ax2.set_title('Learning Efficiency Comparison', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='x')
    ax2.legend(fontsize=10)
    
    plt.tight_layout()
    plt.savefig('learning_efficiency_analysis.png', dpi=300, bbox_inches='tight')
    print("✅ Learning efficiency chart saved: learning_efficiency_analysis.png")


def generate_confidence_analysis(data):
    """Generate confidence score analysis"""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Confidence Score Analysis', fontsize=16, fontweight='bold')
    
    for idx, tid in enumerate(sorted(data.keys())):
        ax = axes[idx // 2, idx % 2]
        
        baseline = data[tid]['baseline']
        adaptive = data[tid]['adaptive']
        
        # Get field-level confidence
        baseline_fields = baseline['field_accuracy']
        adaptive_fields = adaptive['field_accuracy']
        
        # Extract confidence scores
        field_names = []
        baseline_conf = []
        adaptive_conf = []
        
        for field_name in sorted(baseline_fields.keys())[:10]:  # Top 10 fields
            if field_name in adaptive_fields:
                field_names.append(field_name.replace('_', '\n'))
                baseline_conf.append(baseline_fields[field_name].get('avg_confidence', 0) * 100)
                adaptive_conf.append(adaptive_fields[field_name].get('avg_confidence', 0) * 100)
        
        x = np.arange(len(field_names))
        width = 0.35
        
        ax.bar(x - width/2, baseline_conf, width, label='Baseline', color='#3b82f6', alpha=0.7)
        ax.bar(x + width/2, adaptive_conf, width, label='Adaptive', color='#10b981', alpha=0.7)
        
        ax.set_xlabel('Field Name', fontsize=10, fontweight='bold')
        ax.set_ylabel('Avg Confidence (%)', fontsize=10, fontweight='bold')
        ax.set_title(f'{data[tid]["name"]}', fontsize=12, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(field_names, rotation=45, ha='right', fontsize=8)
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3, axis='y')
        ax.set_ylim([0, 110])
    
    plt.tight_layout()
    plt.savefig('confidence_analysis.png', dpi=300, bbox_inches='tight')
    print("✅ Confidence analysis saved: confidence_analysis.png")


def generate_batch_progression_detailed(data):
    """Generate detailed batch progression analysis"""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Detailed Batch Progression Analysis', fontsize=16, fontweight='bold')
    
    for idx, tid in enumerate(sorted(data.keys())):
        ax = axes[idx // 2, idx % 2]
        
        curve = data[tid]['learning_curve']
        
        # Extract data
        batches = [c['batch'] for c in curve]
        accuracies = [c['accuracy'] * 100 for c in curve]
        
        # Calculate improvement per batch
        improvements = [0]
        for i in range(1, len(accuracies)):
            improvements.append(accuracies[i] - accuracies[i-1])
        
        # Create dual-axis plot
        ax2 = ax.twinx()
        
        # Plot accuracy
        line1 = ax.plot(batches, accuracies, 'o-', linewidth=2.5, markersize=8, 
                       label='Accuracy', color='#10b981')
        
        # Plot improvement per batch
        bars = ax2.bar(batches[1:], improvements[1:], alpha=0.3, 
                      label='Improvement/Batch', color='#3b82f6', width=0.6)
        
        # Styling
        ax.set_xlabel('Batch Number', fontsize=11, fontweight='bold')
        ax.set_ylabel('Accuracy (%)', fontsize=11, fontweight='bold', color='#10b981')
        ax2.set_ylabel('Improvement per Batch (%)', fontsize=11, fontweight='bold', color='#3b82f6')
        ax.set_title(f'{data[tid]["name"]}', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='y', labelcolor='#10b981')
        ax2.tick_params(axis='y', labelcolor='#3b82f6')
        
        # Add baseline reference
        baseline_acc = data[tid]['baseline']['metrics']['accuracy'] * 100
        ax.axhline(y=baseline_acc, color='#ef4444', linestyle='--', 
                  linewidth=1.5, alpha=0.5, label='Baseline')
        
        # Combine legends
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, loc='lower right', fontsize=9)
    
    plt.tight_layout()
    plt.savefig('batch_progression_detailed.png', dpi=300, bbox_inches='tight')
    print("✅ Batch progression detailed saved: batch_progression_detailed.png")


def generate_field_difficulty_analysis(data):
    """Analyze field difficulty across templates"""
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Collect all fields and their baseline accuracy
    field_difficulty = {}
    
    for tid in sorted(data.keys()):
        baseline_fields = data[tid]['baseline']['field_accuracy']
        
        for field_name, stats in baseline_fields.items():
            if field_name not in field_difficulty:
                field_difficulty[field_name] = []
            field_difficulty[field_name].append(stats['accuracy'] * 100)
    
    # Calculate average difficulty
    field_avg = {k: np.mean(v) for k, v in field_difficulty.items()}
    
    # Sort by difficulty (lowest accuracy = most difficult)
    sorted_fields = sorted(field_avg.items(), key=lambda x: x[1])[:15]  # Top 15 most difficult
    
    field_names = [f[0].replace('_', '\n') for f in sorted_fields]
    accuracies = [f[1] for f in sorted_fields]
    
    # Color code by difficulty
    colors = ['#ef4444' if acc < 50 else '#f59e0b' if acc < 75 else '#10b981' 
              for acc in accuracies]
    
    bars = ax.barh(field_names, accuracies, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
    
    # Add value labels
    for i, (bar, val) in enumerate(zip(bars, accuracies)):
        ax.text(val + 1, i, f'{val:.1f}%', va='center', fontsize=10, fontweight='bold')
    
    # Add difficulty zones
    ax.axvline(x=50, color='red', linestyle='--', linewidth=2, alpha=0.3, label='High Difficulty')
    ax.axvline(x=75, color='orange', linestyle='--', linewidth=2, alpha=0.3, label='Medium Difficulty')
    
    ax.set_xlabel('Baseline Accuracy (%)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Field Name', fontsize=12, fontweight='bold')
    ax.set_title('Field Difficulty Analysis (15 Most Challenging Fields)', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='x')
    ax.legend(fontsize=10)
    ax.set_xlim([0, 105])
    
    plt.tight_layout()
    plt.savefig('field_difficulty_analysis.png', dpi=300, bbox_inches='tight')
    print("✅ Field difficulty analysis saved: field_difficulty_analysis.png")


def generate_statistical_summary():
    """Generate statistical summary table"""
    data = load_all_data()
    
    summary = {
        'Overall Statistics': {},
        'Template-Specific': {}
    }
    
    # Overall statistics
    all_baseline_acc = [data[tid]['baseline']['metrics']['accuracy'] for tid in data.keys()]
    all_adaptive_acc = [data[tid]['adaptive']['metrics']['accuracy'] for tid in data.keys()]
    all_improvements = [data[tid]['comparison']['improvement']['percentage'] for tid in data.keys()]
    
    summary['Overall Statistics'] = {
        'Baseline Accuracy': {
            'Mean': np.mean(all_baseline_acc) * 100,
            'Std': np.std(all_baseline_acc) * 100,
            'Min': np.min(all_baseline_acc) * 100,
            'Max': np.max(all_baseline_acc) * 100
        },
        'Adaptive Accuracy': {
            'Mean': np.mean(all_adaptive_acc) * 100,
            'Std': np.std(all_adaptive_acc) * 100,
            'Min': np.min(all_adaptive_acc) * 100,
            'Max': np.max(all_adaptive_acc) * 100
        },
        'Improvement': {
            'Mean': np.mean(all_improvements),
            'Std': np.std(all_improvements),
            'Min': np.min(all_improvements),
            'Max': np.max(all_improvements)
        }
    }
    
    # Save to JSON
    with open('statistical_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("✅ Statistical summary saved: statistical_summary.json")
    
    return summary


def main():
    """Generate all additional analyses"""
    print("="*80)
    print("Generating Additional Analysis and Visualizations")
    print("="*80)
    print()
    
    # Load data
    print("📊 Loading experiment data...")
    data = load_all_data()
    print(f"✅ Loaded data for {len(data)} templates\n")
    
    # Generate visualizations
    print("🎨 Generating visualizations...")
    print()
    
    generate_error_reduction_chart(data)
    generate_learning_efficiency_chart(data)
    generate_confidence_analysis(data)
    generate_batch_progression_detailed(data)
    generate_field_difficulty_analysis(data)
    
    print()
    print("📈 Generating statistical summary...")
    summary = generate_statistical_summary()
    
    print()
    print("="*80)
    print("✅ All Additional Analyses Generated Successfully!")
    print("="*80)
    print()
    print("📁 Generated Files:")
    print("   1. error_reduction_analysis.png")
    print("   2. learning_efficiency_analysis.png")
    print("   3. confidence_analysis.png")
    print("   4. batch_progression_detailed.png")
    print("   5. field_difficulty_analysis.png")
    print("   6. statistical_summary.json")
    print()
    print("📊 Statistical Summary:")
    print(f"   Baseline Accuracy: {summary['Overall Statistics']['Baseline Accuracy']['Mean']:.2f}% ± {summary['Overall Statistics']['Baseline Accuracy']['Std']:.2f}%")
    print(f"   Adaptive Accuracy: {summary['Overall Statistics']['Adaptive Accuracy']['Mean']:.2f}% ± {summary['Overall Statistics']['Adaptive Accuracy']['Std']:.2f}%")
    print(f"   Average Improvement: {summary['Overall Statistics']['Improvement']['Mean']:.2f}% ± {summary['Overall Statistics']['Improvement']['Std']:.2f}%")
    print()


if __name__ == '__main__':
    main()
