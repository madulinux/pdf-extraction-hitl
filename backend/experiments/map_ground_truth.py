"""
Map Ground Truth to Document IDs
Create mapping between uploaded documents and their ground truth JSON files

Usage:
    python map_ground_truth.py --template-id 1 --experiment-phase baseline
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from database.db_manager import DatabaseManager
from database.repositories.document_repository import DocumentRepository
import json
import argparse
from pathlib import Path


def map_ground_truth(template_id: int, experiment_phase: str = None, ground_truth_dir: str = "data/ground_truth"):
    """
    Map uploaded documents to their ground truth JSON files
    
    Args:
        template_id: Template ID
        experiment_phase: Experiment phase filter
        ground_truth_dir: Directory containing ground truth JSON files
    """
    db = DatabaseManager()
    doc_repo = DocumentRepository(db)
    
    print("="*70)
    print("🗺️  MAP GROUND TRUTH TO DOCUMENTS")
    print("="*70)
    print(f"Template ID: {template_id}")
    print(f"Experiment Phase: {experiment_phase or 'all'}")
    print()
    
    # Get documents
    if experiment_phase:
        documents = doc_repo.find_by_template_and_phase(template_id, experiment_phase)
    else:
        documents = doc_repo.find_by_template_id(template_id)
    
    if not documents:
        print(f"❌ No documents found")
        return
    
    print(f"📄 Found {len(documents)} documents")
    
    # Create ground truth directory
    os.makedirs(ground_truth_dir, exist_ok=True)
    
    # Map each document to its ground truth
    mapped_count = 0
    missing_count = 0
    
    for doc in documents:
        doc_id = doc['id']
        filename = doc['filename']
        
        # Extract original filename (remove timestamp prefix added by upload)
        # Uploaded: 20251117_010724_2025-11-17_005231_797796_0.pdf
        # Original: 2025-11-17_005231_797796_0.pdf
        # Pattern: YYYYMMDD_HHMMSS_<original_filename>
        
        # Remove first timestamp prefix (YYYYMMDD_HHMMSS_)
        parts = filename.split('_', 2)  # Split max 2 times
        if len(parts) >= 3:
            original_filename = parts[2]  # Get everything after second underscore
        else:
            original_filename = filename
        
        json_filename = original_filename.replace('.pdf', '.json')
        
        # Try to find JSON in generator output folders
        json_found = False
        json_data = None
        
        # Search in all template folders
        template_folders = [
            'experiments/generator/storage/output/form_template',
            'experiments/generator/storage/output/letter_template',
            'experiments/generator/storage/output/table_template',
            'experiments/generator/storage/output/mixed_template'
        ]
        
        for folder in template_folders:
            json_path = os.path.join(folder, json_filename)
            if os.path.exists(json_path):
                with open(json_path, 'r') as f:
                    json_data = json.load(f)
                json_found = True
                break
        
        if json_found:
            # Save ground truth with document_id as filename
            gt_path = os.path.join(ground_truth_dir, f"{doc_id}.json")
            with open(gt_path, 'w') as f:
                json.dump(json_data, f, indent=2)
            
            mapped_count += 1
            print(f"  ✅ Document {doc_id} ({filename}) → {gt_path}")
        else:
            missing_count += 1
            print(f"  ⚠️  Document {doc_id} ({filename}) → JSON not found")
    
    # Summary
    print()
    print("="*70)
    print("📊 SUMMARY")
    print("="*70)
    print(f"Total Documents: {len(documents)}")
    print(f"Mapped: {mapped_count}")
    print(f"Missing: {missing_count}")
    print(f"Ground Truth Directory: {ground_truth_dir}")
    print("="*70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Map ground truth to document IDs')
    parser.add_argument('--template-id', type=int, required=True, help='Template ID')
    parser.add_argument('--experiment-phase', type=str, default=None,
                       help='Experiment phase filter (baseline, adaptive, or omit for all)')
    parser.add_argument('--ground-truth-dir', type=str, default='data/ground_truth',
                       help='Ground truth directory')
    
    args = parser.parse_args()
    
    map_ground_truth(args.template_id, args.experiment_phase, args.ground_truth_dir)
