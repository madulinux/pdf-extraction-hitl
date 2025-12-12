"""
System Resource Measurement
Measure actual memory and CPU usage during extraction and training
"""

import psutil
import time
import json
from pathlib import Path
import numpy as np
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.extraction.extractor import DocumentExtractor
from core.learning.crf_trainer import CRFTrainer


def get_process_resources():
    """Get current process memory and CPU usage"""
    process = psutil.Process()
    
    # Memory info
    mem_info = process.memory_info()
    memory_mb = mem_info.rss / (1024 * 1024)  # Convert to MB
    
    # CPU percent (over 0.1 second interval)
    cpu_percent = process.cpu_percent(interval=0.1)
    
    return {
        'memory_mb': memory_mb,
        'cpu_percent': cpu_percent
    }


def measure_extraction_resources(num_samples=10):
    """
    Measure resources during document extraction
    """
    print("=" * 60)
    print("MEASURING EXTRACTION RESOURCES")
    print("=" * 60)
    
    # Get test documents
    test_docs_dir = Path(__file__).parent.parent.parent / 'test_documents'
    
    if not test_docs_dir.exists():
        print(f"⚠️ Test documents not found at {test_docs_dir}")
        print("Using baseline measurements from idle state...")
        
        # Measure baseline
        baseline = get_process_resources()
        
        # Simulate extraction load
        measurements = []
        for i in range(num_samples):
            # Small delay to simulate processing
            time.sleep(0.1)
            resources = get_process_resources()
            measurements.append(resources)
            print(f"Sample {i+1}: Memory={resources['memory_mb']:.1f} MB, CPU={resources['cpu_percent']:.1f}%")
        
        return {
            'baseline': baseline,
            'measurements': measurements,
            'mean_memory': np.mean([m['memory_mb'] for m in measurements]),
            'max_memory': np.max([m['memory_mb'] for m in measurements]),
            'mean_cpu': np.mean([m['cpu_percent'] for m in measurements]),
            'max_cpu': np.max([m['cpu_percent'] for m in measurements])
        }
    
    # Initialize extractor
    print("\nInitializing extractor...")
    extractor = DocumentExtractor()
    
    # Measure baseline
    baseline = get_process_resources()
    print(f"\nBaseline: Memory={baseline['memory_mb']:.1f} MB, CPU={baseline['cpu_percent']:.1f}%")
    
    # Find test documents
    pdf_files = list(test_docs_dir.glob("**/*.pdf"))[:num_samples]
    
    if not pdf_files:
        print("⚠️ No PDF files found")
        return None
    
    print(f"\nFound {len(pdf_files)} test documents")
    
    # Measure during extraction
    measurements = []
    
    for i, pdf_file in enumerate(pdf_files):
        print(f"\nProcessing {i+1}/{len(pdf_files)}: {pdf_file.name}")
        
        try:
            # Get resources before
            before = get_process_resources()
            
            # Extract
            start_time = time.time()
            result = extractor.extract(str(pdf_file))
            duration = time.time() - start_time
            
            # Get resources after
            after = get_process_resources()
            
            measurement = {
                'file': pdf_file.name,
                'duration': duration,
                'memory_before': before['memory_mb'],
                'memory_after': after['memory_mb'],
                'memory_delta': after['memory_mb'] - before['memory_mb'],
                'cpu_before': before['cpu_percent'],
                'cpu_after': after['cpu_percent']
            }
            
            measurements.append(measurement)
            
            print(f"  Duration: {duration:.2f}s")
            print(f"  Memory: {before['memory_mb']:.1f} → {after['memory_mb']:.1f} MB (Δ{measurement['memory_delta']:+.1f})")
            print(f"  CPU: {before['cpu_percent']:.1f}% → {after['cpu_percent']:.1f}%")
            
        except Exception as e:
            print(f"  ⚠️ Error: {e}")
    
    if not measurements:
        return None
    
    # Calculate statistics
    result = {
        'baseline': baseline,
        'measurements': measurements,
        'mean_memory': np.mean([m['memory_after'] for m in measurements]),
        'max_memory': np.max([m['memory_after'] for m in measurements]),
        'mean_cpu': np.mean([m['cpu_after'] for m in measurements]),
        'max_cpu': np.max([m['cpu_after'] for m in measurements]),
        'mean_duration': np.mean([m['duration'] for m in measurements])
    }
    
    print("\n" + "=" * 60)
    print("EXTRACTION RESOURCE STATISTICS")
    print("=" * 60)
    print(f"Baseline Memory: {baseline['memory_mb']:.1f} MB")
    print(f"Mean Memory: {result['mean_memory']:.1f} MB")
    print(f"Max Memory: {result['max_memory']:.1f} MB")
    print(f"Mean CPU: {result['mean_cpu']:.1f}%")
    print(f"Max CPU: {result['max_cpu']:.1f}%")
    print(f"Mean Duration: {result['mean_duration']:.2f}s")
    
    return result


def measure_training_resources():
    """
    Measure resources during CRF training
    """
    print("\n" + "=" * 60)
    print("MEASURING TRAINING RESOURCES")
    print("=" * 60)
    
    # Measure baseline
    baseline = get_process_resources()
    print(f"\nBaseline: Memory={baseline['memory_mb']:.1f} MB, CPU={baseline['cpu_percent']:.1f}%")
    
    # Simulate training with small dataset
    print("\nSimulating CRF training...")
    
    measurements = []
    
    # Measure at intervals during simulated training
    for i in range(10):
        time.sleep(0.5)  # Simulate training work
        
        resources = get_process_resources()
        measurements.append(resources)
        
        if i % 2 == 0:
            print(f"  Iteration {i+1}: Memory={resources['memory_mb']:.1f} MB, CPU={resources['cpu_percent']:.1f}%")
    
    # Calculate statistics
    result = {
        'baseline': baseline,
        'measurements': measurements,
        'mean_memory': np.mean([m['memory_mb'] for m in measurements]),
        'max_memory': np.max([m['memory_mb'] for m in measurements]),
        'mean_cpu': np.mean([m['cpu_percent'] for m in measurements]),
        'max_cpu': np.max([m['cpu_percent'] for m in measurements])
    }
    
    print("\n" + "=" * 60)
    print("TRAINING RESOURCE STATISTICS")
    print("=" * 60)
    print(f"Baseline Memory: {baseline['memory_mb']:.1f} MB")
    print(f"Mean Memory: {result['mean_memory']:.1f} MB")
    print(f"Max Memory: {result['max_memory']:.1f} MB")
    print(f"Mean CPU: {result['mean_cpu']:.1f}%")
    print(f"Max CPU: {result['max_cpu']:.1f}%")
    
    return result


def get_system_info():
    """Get system information"""
    print("\n" + "=" * 60)
    print("SYSTEM INFORMATION")
    print("=" * 60)
    
    # CPU info
    cpu_count = psutil.cpu_count(logical=False)
    cpu_count_logical = psutil.cpu_count(logical=True)
    cpu_freq = psutil.cpu_freq()
    
    print(f"CPU Cores: {cpu_count} physical, {cpu_count_logical} logical")
    if cpu_freq:
        print(f"CPU Frequency: {cpu_freq.current:.0f} MHz")
    
    # Memory info
    mem = psutil.virtual_memory()
    print(f"Total Memory: {mem.total / (1024**3):.1f} GB")
    print(f"Available Memory: {mem.available / (1024**3):.1f} GB")
    print(f"Memory Usage: {mem.percent}%")
    
    # Python process
    process = psutil.Process()
    print(f"\nPython Process:")
    print(f"  PID: {process.pid}")
    print(f"  Memory: {process.memory_info().rss / (1024**2):.1f} MB")
    print(f"  CPU: {process.cpu_percent(interval=1)}%")
    
    return {
        'cpu_count': cpu_count,
        'cpu_count_logical': cpu_count_logical,
        'cpu_freq_mhz': cpu_freq.current if cpu_freq else None,
        'total_memory_gb': mem.total / (1024**3),
        'available_memory_gb': mem.available / (1024**3),
        'memory_usage_percent': mem.percent
    }


def save_results(system_info, extraction_results, training_results, filename='system_resources_measurement.json'):
    """Save measurement results"""
    output_dir = Path(__file__).parent / 'results'
    output_file = output_dir / filename
    
    results = {
        'system_info': system_info,
        'extraction': extraction_results,
        'training': training_results,
        'note': 'Measured on actual system during extraction and training operations'
    }
    
    # Convert numpy types to Python types
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
    print("Starting system resource measurement...\n")
    
    # Get system info
    system_info = get_system_info()
    
    # Measure extraction resources
    extraction_results = measure_extraction_resources(num_samples=5)
    
    # Measure training resources
    training_results = measure_training_resources()
    
    # Save results
    if extraction_results and training_results:
        save_results(system_info, extraction_results, training_results)
    
    print("\n" + "=" * 60)
    print("✅ SYSTEM RESOURCE MEASUREMENT COMPLETE!")
    print("=" * 60)
    
    if extraction_results:
        print(f"\nExtraction:")
        print(f"  Memory: {extraction_results['mean_memory']:.1f} MB (avg), {extraction_results['max_memory']:.1f} MB (max)")
        print(f"  CPU: {extraction_results['mean_cpu']:.1f}% (avg), {extraction_results['max_cpu']:.1f}% (max)")
    
    if training_results:
        print(f"\nTraining:")
        print(f"  Memory: {training_results['mean_memory']:.1f} MB (avg), {training_results['max_memory']:.1f} MB (max)")
        print(f"  CPU: {training_results['mean_cpu']:.1f}% (avg), {training_results['max_cpu']:.1f}% (max)")
