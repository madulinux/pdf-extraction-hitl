"""
API-Based Experiment Automation Script
Simulates real user workflow through API endpoints

This script automates the complete extraction workflow:
1. Login to get authentication token
2. Extract documents via API (POST /api/v1/extraction/extract)
3. Submit feedback/corrections via API (POST /api/v1/extraction/validate)
4. Track metrics and results

Usage:
    python run_api_experiment.py --template-id 1 --batch-size 5 --pdf-dir experiments/generator/storage/output/certificate_template
"""

import requests
import json
import os
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import glob
import re

class APIExperimentRunner:
    """Automation runner for extraction experiments via API"""
    
    def __init__(self, base_url: str = "http://localhost:8000", username: str = "madulinux", password: str = "justice#404"):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.token = None
        self.session = requests.Session()
        
    def login(self) -> bool:
        """Login and get authentication token"""
        print("🔐 Logging in...")
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/login",
                json={
                    "username": self.username,
                    "password": self.password
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("data", {}).get("tokens", {}).get("access_token")
                
                if self.token:
                    self.session.headers.update({
                        "Authorization": f"Bearer {self.token}"
                    })
                    print(f"✅ Login successful! Token: {self.token[:20]}...")
                    return True
                else:
                    print("❌ Login failed: No token in response")
                    return False
            else:
                print(f"❌ Login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def extract_document(self, pdf_path: str, template_id: int) -> Tuple[bool, Dict]:
        """
        Extract document via API
        
        Returns:
            (success, result_data)
        """
        try:
            with open(pdf_path, 'rb') as f:
                files = {'file': (os.path.basename(pdf_path), f, 'application/pdf')}
                data = {'template_id': template_id}
                
                response = self.session.post(
                    f"{self.base_url}/api/v1/extraction/extract",
                    files=files,
                    data=data
                )
            
            if response.status_code == 200:
                result = response.json()
                return True, result.get("data", {})
            else:
                print(f"  ❌ Extraction failed: {response.status_code} - {response.text[:200]}")
                return False, {}
                
        except Exception as e:
            print(f"  ❌ Extraction error: {e}")
            return False, {}
    
    def submit_feedback(self, document_id: int, corrections: Dict) -> Tuple[bool, Dict]:
        """
        Submit feedback/corrections via API
        
        Returns:
            (success, result_data)
        """
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/extraction/validate",
                json={
                    "document_id": document_id,
                    "corrections": corrections
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return True, result.get("data", {})
            else:
                print(f"  ❌ Feedback submission failed: {response.status_code} - {response.text[:200]}")
                return False, {}
                
        except Exception as e:
            print(f"  ❌ Feedback error: {e}")
            return False, {}
    
    def check_active_training_jobs(self, template_id: int, debug: bool = False) -> Tuple[bool, int]:
        """
        Check if there are active training jobs for the template
        
        Returns:
            (has_active_jobs, active_count)
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/jobs",
                params={
                    "job_type": "auto_training",
                    "status": "pending,running"
                }
            )
            
            if debug:
                print(f"      [DEBUG] Jobs API status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                if debug:
                    print(f"      [DEBUG] Response type: {type(result)}")
                
                # Handle different response structures
                if isinstance(result, dict):
                    # Standard APIResponse format: {"data": {"jobs": [...]}}
                    data = result.get("data", {})
                    if isinstance(data, dict):
                        jobs = data.get("jobs", [])
                    elif isinstance(data, list):
                        # Sometimes data is directly a list
                        jobs = data
                    else:
                        jobs = []
                elif isinstance(result, list):
                    # Direct list response
                    jobs = result
                else:
                    jobs = []
                
                if debug:
                    print(f"      [DEBUG] Total jobs found: {len(jobs)}")
                
                # Filter jobs for this template
                active_jobs = []
                for job in jobs:
                    if not isinstance(job, dict):
                        continue
                    
                    payload = job.get("payload", {})
                    if not isinstance(payload, dict):
                        continue
                    
                    job_template_id = payload.get("template_id")
                    job_status = job.get("status")
                    
                    if debug:
                        print(f"      [DEBUG] Job: template_id={job_template_id}, status={job_status}, type={job.get('job_type')}")
                    
                    if (job_template_id == template_id and 
                        job_status in ["pending", "running"]):
                        active_jobs.append(job)
                        if debug:
                            print(f"      [DEBUG] ✓ Matched active job for template {template_id}")
                
                if debug:
                    print(f"      [DEBUG] Active jobs for template {template_id}: {len(active_jobs)}")
                
                return len(active_jobs) > 0, len(active_jobs)
            else:
                if debug:
                    print(f"      [DEBUG] Jobs API failed: {response.status_code}")
                # If endpoint fails, assume no active jobs to continue
                return False, 0
                
        except Exception as e:
            print(f"  ⚠️  Warning: Could not check training jobs: {e}")
            if debug:
                import traceback
                print(f"      [DEBUG] Exception: {traceback.format_exc()}")
            return False, 0
    
    def wait_for_training_completion(self, template_id: int, max_wait_seconds: int = 300, check_interval: int = 10, debug: bool = False):
        """
        Wait for active training jobs to complete
        
        Args:
            template_id: Template ID to check
            max_wait_seconds: Maximum time to wait (default: 5 minutes)
            check_interval: Seconds between checks (default: 10 seconds)
            debug: Enable debug logging (default: False)
        """
        print(f"    🔍 Checking for active training jobs (template_id={template_id})...")
        has_active, count = self.check_active_training_jobs(template_id, debug=debug)
        
        if not has_active:
            print(f"    ✅ No active training jobs found, continuing...")
            return
        
        print(f"    ⏳ Waiting for {count} active training job(s) to complete...")
        
        elapsed = 0
        while elapsed < max_wait_seconds:
            time.sleep(check_interval)
            elapsed += check_interval
            
            has_active, count = self.check_active_training_jobs(template_id, debug=debug)
            
            if not has_active:
                print(f"    ✅ Training completed! (waited {elapsed}s)")
                return
            
            print(f"    ⏳ Still training... ({elapsed}s elapsed, {count} job(s) active)")
        
        print(f"    ⚠️  Warning: Training still active after {max_wait_seconds}s, continuing anyway...")
    
    def load_ground_truth(self, pdf_path: str) -> Dict:
        """Load ground truth JSON for a PDF file"""
        json_path = pdf_path.replace('.pdf', '.json')
        
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                return json.load(f)
        else:
            print(f"  ⚠️  Warning: Ground truth not found for {os.path.basename(pdf_path)}")
            return {}
    
    def compare_and_get_corrections(self, extracted_data: Dict, ground_truth: Dict) -> Dict:
        """
        Compare extracted data with ground truth and return corrections
        
        Returns:
            Dictionary of corrections {field_name: correct_value}
        """
        corrections = {}
        
        for field_name, correct_value in ground_truth.items():
            extracted_value = extracted_data.get(field_name, "")
            
            # Strict comparison - only strip whitespace
            extracted_normalized = normalize_whitespace(extracted_value)
            correct_normalized = normalize_whitespace(correct_value)
            
            if extracted_normalized != correct_normalized:
                corrections[field_name] = correct_value
        
        return corrections
    
    def calculate_accuracy(self, extracted_data: Dict, ground_truth: Dict) -> Tuple[int, int]:
        """
        Calculate accuracy metrics
        
        Returns:
            (correct_fields, total_fields)
        """
        total_fields = len(ground_truth)
        correct_fields = 0
        
        for field_name, correct_value in ground_truth.items():
            extracted_value = extracted_data.get(field_name, "")
            
            extracted_normalized = str(extracted_value).strip()
            correct_normalized = str(correct_value).strip()
            
            if extracted_normalized == correct_normalized:
                correct_fields += 1
        
        return correct_fields, total_fields


def get_template_directory(template_id: int, base_dir: str = "experiments/generator/storage/output") -> str:
    """
    Get PDF directory based on template ID
    
    Template mapping:
        1 = form_template
        2 = table_template
        3 = letter_template
        4 = mixed_template
    """
    template_map = {
        1: "form_template",
        2: "table_template",
        3: "letter_template",
        4: "mixed_template"
    }
    
    template_name = template_map.get(template_id)
    if not template_name:
        raise ValueError(f"Unknown template ID: {template_id}. Valid IDs: {list(template_map.keys())}")
    
    return os.path.join(base_dir, template_name)



def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text for comparison
    
    This function makes comparison tolerant to whitespace differences:
    - Multiple spaces → single space
    - Tabs → spaces
    - Newlines → spaces
    - Leading/trailing whitespace removed
    
    Args:
        text: Input text
        
    Returns:
        Normalized text with single spaces
        
    Examples:
        "John  Doe" → "John Doe"
        "John\tDoe" → "John Doe"
        "John\nDoe" → "John Doe"
        "  John Doe  " → "John Doe"
    """
    if not text:
        return ""
    
    # Convert to string if not already
    text = str(text)
    
    # Replace all whitespace characters (spaces, tabs, newlines) with single space
    normalized = re.sub(r'\s+', ' ', text)
    
    # Strip leading/trailing whitespace
    normalized = normalized.strip()
    
    return normalized

def run_experiment(
    template_id: int,
    pdf_dir: str = None,
    batch_size: int = 5,
    base_url: str = "http://localhost:8000",
    username: str = "admin",
    password: str = "admin123",
    wait_for_training: bool = True,
    max_wait_seconds: int = 300,
    debug: bool = False
):
    """
    Run automated experiment via API
    
    Args:
        template_id: Template ID to use for extraction
        pdf_dir: Directory containing PDF files and ground truth JSON (auto-detected if None)
        batch_size: Number of documents per batch before triggering training
        base_url: API base URL
        username: Login username
        password: Login password
        wait_for_training: Wait for training jobs to complete before next batch (default: True)
        max_wait_seconds: Maximum seconds to wait for training (default: 300)
    """
    
    # Auto-detect PDF directory based on template ID if not provided
    if pdf_dir is None:
        pdf_dir = get_template_directory(template_id)
        print(f"📁 Auto-detected PDF directory: {pdf_dir}")
    
    # Validate directory exists
    if not os.path.exists(pdf_dir):
        raise FileNotFoundError(f"PDF directory not found: {pdf_dir}")
    
    print("=" * 80)
    print("🧪 API-BASED EXPERIMENT AUTOMATION")
    print("=" * 80)
    print(f"📋 Configuration:")
    print(f"  - Template ID: {template_id}")
    print(f"  - PDF Directory: {pdf_dir}")
    print(f"  - Batch Size: {batch_size}")
    print(f"  - API URL: {base_url}")
    print("=" * 80)
    print()
    
    # Initialize runner
    runner = APIExperimentRunner(base_url, username, password)
    
    # Step 1: Login
    if not runner.login():
        print("❌ Failed to login. Exiting...")
        return
    
    print()
    
    # Step 2: Get PDF files
    pdf_pattern = os.path.join(pdf_dir, "*.pdf")
    pdf_files = sorted(glob.glob(pdf_pattern))
    
    if not pdf_files:
        print(f"❌ No PDF files found in {pdf_dir}")
        return
    
    print(f"📁 Found {len(pdf_files)} PDF files")
    print()
    
    # Step 3: Process documents in batches
    total_batches = (len(pdf_files) + batch_size - 1) // batch_size
    
    # Metrics tracking
    total_documents = 0
    total_extractions_success = 0
    total_feedbacks_submitted = 0
    total_corrections = 0
    total_fields = 0
    total_correct_fields = 0
    
    batch_results = []
    
    print(f"🔄 Starting experiment ({total_batches} batches)...\n")
    
    for batch_num in range(1, total_batches + 1):
        start_idx = (batch_num - 1) * batch_size
        end_idx = min(start_idx + batch_size, len(pdf_files))
        batch_pdfs = pdf_files[start_idx:end_idx]
        
        print(f"📦 Batch {batch_num}/{total_batches} (Documents {start_idx+1}-{end_idx})")
        print("-" * 80)
        
        # Wait for any active training jobs to complete before processing new batch
        if wait_for_training and batch_num > 1:  # Skip check for first batch
            runner.wait_for_training_completion(template_id, max_wait_seconds=max_wait_seconds, debug=debug)
        
        
        batch_correct = 0
        batch_total = 0
        batch_corrections_count = 0
        
        for idx, pdf_path in enumerate(batch_pdfs, start=start_idx+1):
            pdf_name = os.path.basename(pdf_path)
            print(f"  [{idx}/{len(pdf_files)}] Processing: {pdf_name}")
            
            # Load ground truth
            ground_truth = runner.load_ground_truth(pdf_path)
            
            if not ground_truth:
                print(f"  ⏭️  Skipping (no ground truth)")
                continue
            
            # Extract via API
            print(f"    📄 Extracting...")
            success, extract_result = runner.extract_document(pdf_path, template_id)
            
            if not success:
                print(f"    ❌ Extraction failed")
                continue
            
            total_extractions_success += 1
            total_documents += 1
            
            # Get extraction results
            document_id = extract_result.get("document_id")
            extraction_result = extract_result.get("results", {})
            extracted_data = extraction_result.get("extracted_data", {})
            
            print(f"    ✅ Extracted (Document ID: {document_id})")
            
            # Calculate accuracy before feedback
            correct, total = runner.calculate_accuracy(extracted_data, ground_truth)
            accuracy = (correct / total * 100) if total > 0 else 0
            
            batch_correct += correct
            batch_total += total
            total_fields += total
            total_correct_fields += correct
            
            print(f"    📊 Initial Accuracy: {correct}/{total} ({accuracy:.1f}%)")
            
            # Get corrections
            corrections = runner.compare_and_get_corrections(extracted_data, ground_truth)
            
            # Always submit feedback (even with empty corrections for training on correct data)
            if corrections:
                print(f"    🔧 Submitting {len(corrections)} corrections...")
            else:
                print(f"    ✨ Perfect extraction! Submitting as correct data for training...")
            
            # Submit feedback via API
            success, feedback_result = runner.submit_feedback(document_id, corrections)
            
            if success:
                total_feedbacks_submitted += 1
                total_corrections += len(corrections)
                batch_corrections_count += len(corrections)
                
                # Check if training was triggered
                auto_training = feedback_result.get("auto_training", {})
                if auto_training.get("triggered"):
                    print(f"    🎯 Auto-training triggered! Status: {auto_training.get('status')}")
                
                print(f"    ✅ Feedback submitted successfully")
            else:
                print(f"    ❌ Feedback submission failed")
            
            print()
            
            # Small delay to avoid overwhelming the API
            time.sleep(0.5)
        
        # Batch summary
        batch_accuracy = (batch_correct / batch_total * 100) if batch_total > 0 else 0
        batch_results.append({
            "batch": batch_num,
            "documents": len(batch_pdfs),
            "correct_fields": batch_correct,
            "total_fields": batch_total,
            "accuracy": batch_accuracy,
            "corrections": batch_corrections_count
        })
        
        print(f"📊 Batch {batch_num} Summary:")
        print(f"  - Accuracy: {batch_correct}/{batch_total} ({batch_accuracy:.2f}%)")
        print(f"  - Corrections: {batch_corrections_count}")
        print()
        print("=" * 80)
        print()
    
    # Final summary
    print("🎉 EXPERIMENT COMPLETED!")
    print("=" * 80)
    print(f"📊 Overall Results:")
    print(f"  - Total Documents Processed: {total_documents}")
    print(f"  - Successful Extractions: {total_extractions_success}")
    print(f"  - Feedbacks Submitted: {total_feedbacks_submitted}")
    print(f"  - Total Corrections: {total_corrections}")
    print(f"  - Overall Accuracy: {total_correct_fields}/{total_fields} ({(total_correct_fields/total_fields*100) if total_fields > 0 else 0:.2f}%)")
    print()
    
    print("📈 Batch-by-Batch Results:")
    print("-" * 80)
    for result in batch_results:
        print(f"  Batch {result['batch']}: {result['accuracy']:.2f}% accuracy, {result['corrections']} corrections")
    print("=" * 80)
    
    # Save results to file
    results_file = f"experiment_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "config": {
                "template_id": template_id,
                "batch_size": batch_size,
                "pdf_dir": pdf_dir
            },
            "summary": {
                "total_documents": total_documents,
                "successful_extractions": total_extractions_success,
                "feedbacks_submitted": total_feedbacks_submitted,
                "total_corrections": total_corrections,
                "total_fields": total_fields,
                "correct_fields": total_correct_fields,
                "overall_accuracy": (total_correct_fields/total_fields*100) if total_fields > 0 else 0
            },
            "batch_results": batch_results
        }, f, indent=2)
    
    print(f"\n💾 Results saved to: {results_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Run API-based extraction experiment",
        epilog="""
Template ID mapping:
  1 = form_template
  2 = table_template
  3 = letter_template
  4 = mixed_template

Examples:
  # Auto-detect PDF directory based on template ID
  python run_api_experiment.py --template-id 1 --batch-size 5
  
  # Specify custom PDF directory
  python run_api_experiment.py --template-id 1 --pdf-dir /path/to/pdfs --batch-size 5
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--template-id", type=int, required=True, 
                        help="Template ID (1=form, 2=table, 3=letter, 4=mixed)")
    parser.add_argument("--pdf-dir", type=str, default=None, 
                        help="Directory containing PDF files (auto-detected if not specified)")
    parser.add_argument("--batch-size", type=int, default=5, 
                        help="Batch size for incremental learning (default: 5)")
    parser.add_argument("--api-url", type=str, default="http://localhost:8000", 
                        help="API base URL (default: http://localhost:8000)")
    parser.add_argument("--username", type=str, default="madulinux", 
                        help="Login username (default: madulinux)")
    parser.add_argument("--password", type=str, default="justice#404", 
                        help="Login password (default: justice#404)")
    parser.add_argument("--wait-for-training", action="store_true", default=True,
                        help="Wait for training jobs to complete before next batch (default: True)")
    parser.add_argument("--no-wait-for-training", dest="wait_for_training", action="store_false",
                        help="Don't wait for training jobs (process all batches immediately)")
    parser.add_argument("--max-wait-seconds", type=int, default=300,
                        help="Maximum seconds to wait for training completion (default: 300)")
    parser.add_argument("--debug", action="store_true", default=False,
                        help="Enable debug logging for training job checks")
    
    args = parser.parse_args()
    
    # Validate template ID
    if args.template_id not in [1, 2, 3, 4]:
        print(f"❌ Error: Invalid template ID: {args.template_id}")
        print("Valid template IDs: 1 (form), 2 (table), 3 (letter), 4 (mixed)")
        sys.exit(1)
    
    # Run experiment
    run_experiment(
        template_id=args.template_id,
        pdf_dir=args.pdf_dir,
        batch_size=args.batch_size,
        base_url=args.api_url,
        username=args.username,
        password=args.password,
        wait_for_training=args.wait_for_training,
        max_wait_seconds=args.max_wait_seconds,
        debug=args.debug
    )


if __name__ == "__main__":
    main()
