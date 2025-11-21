"""
Prepare Ground Truth from JSON Files
Copy JSON files from generator output to ground_truth directory

Usage:
    python prepare_ground_truth_from_json.py --source experiments/generator/storage/output/form_template
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import json
import shutil
import argparse
from pathlib import Path


def prepare_ground_truth_from_json(source_folder: str, output_dir: str = "data/ground_truth"):
    """
    Copy JSON ground truth files from generator output
    
    Args:
        source_folder: Folder containing PDF and JSON files
        output_dir: Output directory for ground truth
    """
    print("="*70)
    print("📁 PREPARE GROUND TRUTH FROM JSON")
    print("="*70)
    print(f"Source: {source_folder}")
    print(f"Output: {output_dir}")
    print()
    
    # Get JSON files
    source_path = Path(source_folder)
    if not source_path.exists():
        print(f"❌ Source folder not found: {source_folder}")
        return
    
    json_files = sorted(list(source_path.glob("*.json")))
    
    if not json_files:
        print(f"❌ No JSON files found in {source_folder}")
        return
    
    print(f"📄 Found {len(json_files)} JSON files")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Copy JSON files
    copied_count = 0
    
    for json_file in json_files:
        try:
            # Read JSON to validate
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            # Copy to ground_truth folder with same filename
            dest_file = os.path.join(output_dir, json_file.name)
            shutil.copy2(json_file, dest_file)
            
            copied_count += 1
            
        except Exception as e:
            print(f"  ⚠️  Error copying {json_file.name}: {str(e)}")
    
    # Summary
    print()
    print("="*70)
    print("📊 SUMMARY")
    print("="*70)
    print(f"Total JSON files: {len(json_files)}")
    print(f"Copied: {copied_count}")
    print(f"Output directory: {output_dir}")
    print("="*70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Prepare ground truth from JSON files')
    parser.add_argument('--source', type=str, required=True,
                       help='Source folder containing JSON files')
    parser.add_argument('--output-dir', type=str, default='data/ground_truth',
                       help='Output directory for ground truth')
    
    args = parser.parse_args()
    
    prepare_ground_truth_from_json(args.source, args.output_dir)
