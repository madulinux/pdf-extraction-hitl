"""
Baseline System Resource Measurement
Measure memory and CPU usage of the Python process during typical operations
"""

import psutil
import time
import json
import os
from pathlib import Path
import numpy as np


def get_process_info():
    """Get current process resource usage"""
    process = psutil.Process()
    
    # Memory info (in MB)
    mem_info = process.memory_info()
    memory_rss_mb = mem_info.rss / (1024 * 1024)  # Resident Set Size
    memory_vms_mb = mem_info.vms / (1024 * 1024)  # Virtual Memory Size
    
    # CPU percent
    cpu_percent = process.cpu_percent(interval=0.1)
    
    # Number of threads
    num_threads = process.num_threads()
    
    return {
        'memory_rss_mb': memory_rss_mb,
        'memory_vms_mb': memory_vms_mb,
        'cpu_percent': cpu_percent,
        'num_threads': num_threads
    }


def get_system_info():
    """Get system information"""
    print("=" * 60)
    print("SYSTEM INFORMATION")
    print("=" * 60)
    
    # CPU info
    cpu_count_physical = psutil.cpu_count(logical=False)
    cpu_count_logical = psutil.cpu_count(logical=True)
    cpu_freq = psutil.cpu_freq()
    
    print(f"\nCPU:")
    print(f"  Physical cores: {cpu_count_physical}")
    print(f"  Logical cores: {cpu_count_logical}")
    if cpu_freq:
        print(f"  Current frequency: {cpu_freq.current:.0f} MHz")
        print(f"  Max frequency: {cpu_freq.max:.0f} MHz")
    
    # Memory info
    mem = psutil.virtual_memory()
    print(f"\nSystem Memory:")
    print(f"  Total: {mem.total / (1024**3):.2f} GB")
    print(f"  Available: {mem.available / (1024**3):.2f} GB")
    print(f"  Used: {mem.used / (1024**3):.2f} GB ({mem.percent}%)")
    
    return {
        'cpu_count_physical': cpu_count_physical,
        'cpu_count_logical': cpu_count_logical,
        'cpu_freq_current': cpu_freq.current if cpu_freq else None,
        'cpu_freq_max': cpu_freq.max if cpu_freq else None,
        'memory_total_gb': mem.total / (1024**3),
        'memory_available_gb': mem.available / (1024**3),
        'memory_used_gb': mem.used / (1024**3),
        'memory_percent': mem.percent
    }


def measure_baseline():
    """Measure baseline resource usage"""
    print("\n" + "=" * 60)
    print("BASELINE MEASUREMENT (Python Process)")
    print("=" * 60)
    
    measurements = []
    
    print("\nMeasuring baseline over 10 samples...")
    for i in range(10):
        time.sleep(0.5)
        info = get_process_info()
        measurements.append(info)
        
        if i % 2 == 0:
            print(f"  Sample {i+1}: Memory={info['memory_rss_mb']:.1f} MB, CPU={info['cpu_percent']:.1f}%")
    
    # Calculate statistics
    memory_values = [m['memory_rss_mb'] for m in measurements]
    cpu_values = [m['cpu_percent'] for m in measurements]
    
    result = {
        'measurements': measurements,
        'memory_mean': np.mean(memory_values),
        'memory_min': np.min(memory_values),
        'memory_max': np.max(memory_values),
        'memory_std': np.std(memory_values),
        'cpu_mean': np.mean(cpu_values),
        'cpu_min': np.min(cpu_values),
        'cpu_max': np.max(cpu_values),
        'cpu_std': np.std(cpu_values)
    }
    
    print("\n" + "=" * 60)
    print("BASELINE STATISTICS")
    print("=" * 60)
    print(f"\nMemory (RSS):")
    print(f"  Mean: {result['memory_mean']:.1f} MB")
    print(f"  Range: {result['memory_min']:.1f} - {result['memory_max']:.1f} MB")
    print(f"  Std Dev: {result['memory_std']:.2f} MB")
    
    print(f"\nCPU Usage:")
    print(f"  Mean: {result['cpu_mean']:.1f}%")
    print(f"  Range: {result['cpu_min']:.1f} - {result['cpu_max']:.1f}%")
    print(f"  Std Dev: {result['cpu_std']:.2f}%")
    
    return result


def measure_with_imports():
    """Measure resource usage after importing heavy libraries"""
    print("\n" + "=" * 60)
    print("MEASUREMENT WITH IMPORTS")
    print("=" * 60)
    
    print("\nImporting libraries...")
    
    # Measure before imports
    before = get_process_info()
    print(f"Before imports: Memory={before['memory_rss_mb']:.1f} MB")
    
    # Import heavy libraries
    import pandas as pd
    import sklearn_crfsuite
    import pdfplumber
    
    # Measure after imports
    after = get_process_info()
    print(f"After imports: Memory={after['memory_rss_mb']:.1f} MB")
    print(f"Memory increase: {after['memory_rss_mb'] - before['memory_rss_mb']:.1f} MB")
    
    # Measure over time
    measurements = []
    print("\nMeasuring with imports over 10 samples...")
    for i in range(10):
        time.sleep(0.5)
        info = get_process_info()
        measurements.append(info)
        
        if i % 2 == 0:
            print(f"  Sample {i+1}: Memory={info['memory_rss_mb']:.1f} MB, CPU={info['cpu_percent']:.1f}%")
    
    # Calculate statistics
    memory_values = [m['memory_rss_mb'] for m in measurements]
    cpu_values = [m['cpu_percent'] for m in measurements]
    
    result = {
        'before': before,
        'after': after,
        'memory_increase': after['memory_rss_mb'] - before['memory_rss_mb'],
        'measurements': measurements,
        'memory_mean': np.mean(memory_values),
        'memory_min': np.min(memory_values),
        'memory_max': np.max(memory_values),
        'memory_std': np.std(memory_values),
        'cpu_mean': np.mean(cpu_values),
        'cpu_min': np.min(cpu_values),
        'cpu_max': np.max(cpu_values),
        'cpu_std': np.std(cpu_values)
    }
    
    print("\n" + "=" * 60)
    print("WITH IMPORTS STATISTICS")
    print("=" * 60)
    print(f"\nMemory (RSS):")
    print(f"  Mean: {result['memory_mean']:.1f} MB")
    print(f"  Range: {result['memory_min']:.1f} - {result['memory_max']:.1f} MB")
    print(f"  Import overhead: {result['memory_increase']:.1f} MB")
    
    print(f"\nCPU Usage:")
    print(f"  Mean: {result['cpu_mean']:.1f}%")
    print(f"  Range: {result['cpu_min']:.1f} - {result['cpu_max']:.1f}%")
    
    return result


def measure_model_loading():
    """Measure resource usage when loading CRF models"""
    print("\n" + "=" * 60)
    print("MEASUREMENT WITH MODEL LOADING")
    print("=" * 60)
    
    import joblib
    
    models_dir = Path(__file__).parent.parent / 'models'
    
    if not models_dir.exists():
        print("⚠️ Models directory not found")
        return None
    
    # Measure before loading
    before = get_process_info()
    print(f"\nBefore loading models: Memory={before['memory_rss_mb']:.1f} MB")
    
    # Load all models
    models = []
    for i in range(1, 5):
        model_file = models_dir / f'template_{i}_model.joblib'
        if model_file.exists():
            print(f"Loading {model_file.name}...")
            model = joblib.load(model_file)
            models.append(model)
    
    # Measure after loading
    after = get_process_info()
    print(f"After loading models: Memory={after['memory_rss_mb']:.1f} MB")
    print(f"Memory increase: {after['memory_rss_mb'] - before['memory_rss_mb']:.1f} MB")
    
    # Measure over time
    measurements = []
    print("\nMeasuring with loaded models over 10 samples...")
    for i in range(10):
        time.sleep(0.5)
        info = get_process_info()
        measurements.append(info)
        
        if i % 2 == 0:
            print(f"  Sample {i+1}: Memory={info['memory_rss_mb']:.1f} MB, CPU={info['cpu_percent']:.1f}%")
    
    # Calculate statistics
    memory_values = [m['memory_rss_mb'] for m in measurements]
    cpu_values = [m['cpu_percent'] for m in measurements]
    
    result = {
        'before': before,
        'after': after,
        'memory_increase': after['memory_rss_mb'] - before['memory_rss_mb'],
        'num_models': len(models),
        'measurements': measurements,
        'memory_mean': np.mean(memory_values),
        'memory_min': np.min(memory_values),
        'memory_max': np.max(memory_values),
        'memory_std': np.std(memory_values),
        'cpu_mean': np.mean(cpu_values),
        'cpu_min': np.min(cpu_values),
        'cpu_max': np.max(cpu_values),
        'cpu_std': np.std(cpu_values)
    }
    
    print("\n" + "=" * 60)
    print("WITH MODELS LOADED STATISTICS")
    print("=" * 60)
    print(f"\nMemory (RSS):")
    print(f"  Mean: {result['memory_mean']:.1f} MB")
    print(f"  Range: {result['memory_min']:.1f} - {result['memory_max']:.1f} MB")
    print(f"  Model loading overhead: {result['memory_increase']:.1f} MB")
    
    print(f"\nCPU Usage:")
    print(f"  Mean: {result['cpu_mean']:.1f}%")
    print(f"  Range: {result['cpu_min']:.1f} - {result['cpu_max']:.1f}%")
    
    return result


def save_results(system_info, baseline, with_imports, with_models):
    """Save measurement results"""
    output_dir = Path(__file__).parent / 'results'
    output_file = output_dir / 'baseline_resource_measurement.json'
    
    results = {
        'system_info': system_info,
        'baseline': baseline,
        'with_imports': with_imports,
        'with_models': with_models,
        'note': 'Measured using psutil on actual system'
    }
    
    # Convert numpy types
    def convert_types(obj):
        if isinstance(obj, dict):
            return {k: convert_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_types(v) for v in obj]
        elif isinstance(obj, (np.integer, np.floating)):
            return float(obj)
        else:
            return obj
    
    results = convert_types(results)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Results saved to: {output_file}")


if __name__ == '__main__':
    print("Starting baseline resource measurement...\n")
    
    # Get system info
    system_info = get_system_info()
    
    # Measure baseline
    baseline = measure_baseline()
    
    # Measure with imports
    with_imports = measure_with_imports()
    
    # Measure with model loading
    with_models = measure_model_loading()
    
    # Save results
    save_results(system_info, baseline, with_imports, with_models)
    
    print("\n" + "=" * 60)
    print("✅ BASELINE RESOURCE MEASUREMENT COMPLETE!")
    print("=" * 60)
    
    print("\n📊 SUMMARY:")
    print(f"\nBaseline (Python only):")
    print(f"  Memory: {baseline['memory_mean']:.1f} MB")
    print(f"  CPU: {baseline['cpu_mean']:.1f}%")
    
    if with_imports:
        print(f"\nWith Libraries Imported:")
        print(f"  Memory: {with_imports['memory_mean']:.1f} MB (+{with_imports['memory_increase']:.1f} MB)")
        print(f"  CPU: {with_imports['cpu_mean']:.1f}%")
    
    if with_models:
        print(f"\nWith Models Loaded:")
        print(f"  Memory: {with_models['memory_mean']:.1f} MB (+{with_models['memory_increase']:.1f} MB)")
        print(f"  CPU: {with_models['cpu_mean']:.1f}%")
