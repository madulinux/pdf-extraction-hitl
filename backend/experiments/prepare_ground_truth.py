"""
Prepare Ground Truth Script
Exports extraction results as ground truth for evaluation

Usage:
    python prepare_ground_truth.py --template-id 1
    python prepare_ground_truth.py --template-id 1 --experiment-phase baseline
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from database.db_manager import DatabaseManager
from database.repositories.document_repository import DocumentRepository
from database.repositories.feedback_repository import FeedbackRepository
import json
import argparse


def prepare_ground_truth(template_id: int, experiment_phase: str = None, output_dir: str = "data/ground_truth"):
    """
    Prepare ground truth from validated documents
    
    Ground truth = extraction_result + corrections from feedback
    """
    db = DatabaseManager()
    doc_repo = DocumentRepository(db)
    feedback_repo = FeedbackRepository(db)
    
    print("="*70)
    print("📁 PREPARE GROUND TRUTH")
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
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Process each document
    created_count = 0
    updated_count = 0
    skipped_count = 0
    
    for doc in documents:
        doc_id = doc['id']
        output_file = os.path.join(output_dir, f"{doc_id}.json")
        
        # Parse extraction result
        try:
            extraction_result = json.loads(doc['extraction_result'] or '{}')
        except:
            print(f"  ⚠️  Failed to parse extraction_result for document {doc_id}")
            skipped_count += 1
            continue
        
        extracted_data = extraction_result.get('extracted_data', {})
        
        # Get feedback (corrections)
        feedbacks = feedback_repo.find_by_document_id(doc_id)
        
        # Apply corrections to create ground truth
        ground_truth = extracted_data.copy()
        for fb in feedbacks:
            field_name = fb['field_name']
            corrected_value = fb['corrected_value']
            ground_truth[field_name] = corrected_value
        
        # Save ground truth
        with open(output_file, 'w') as f:
            json.dump(ground_truth, f, indent=2)
        
        # Check if file existed before
        if os.path.exists(output_file):
            updated_count += 1
        else:
            created_count += 1
        
        print(f"  ✅ Document {doc_id}: {len(ground_truth)} fields ({len(feedbacks)} corrections)")
    
    # Summary
    print()
    print("="*70)
    print("📊 SUMMARY")
    print("="*70)
    print(f"Total Documents: {len(documents)}")
    print(f"Created: {created_count}")
    print(f"Updated: {updated_count}")
    print(f"Skipped: {skipped_count}")
    print(f"Output Directory: {output_dir}")
    print("="*70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Prepare ground truth from validated documents')
    parser.add_argument('--template-id', type=int, required=True, help='Template ID')
    parser.add_argument('--experiment-phase', type=str, default=None, 
                       help='Experiment phase filter (baseline, adaptive, or omit for all)')
    parser.add_argument('--output-dir', type=str, default='data/ground_truth',
                       help='Output directory for ground truth files')
    
    args = parser.parse_args()
    
    prepare_ground_truth(args.template_id, args.experiment_phase, args.output_dir)
