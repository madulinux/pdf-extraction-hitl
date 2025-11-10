"""
Automated Seeder for BAB 4 Dataset Generation

This script automates the process of:
1. Uploading template
2. Generating documents with ground truth
3. Extracting data from generated documents
4. Auto-correcting based on ground truth
5. Validating documents

Usage:
    python automated_seeder.py --template certificate --count 30
"""

import sys
import os
import time
import json
import requests
from pathlib import Path
from typing import Dict, List, Tuple
import logging

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent / "cmd"))

from utils.document_processor import process_template, convert_docx_to_pdf

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")


class AutomatedSeeder:
    """Automated seeder for generating and uploading test data"""

    def __init__(
        self,
        api_base_url: str = API_BASE_URL,
        username: str = "admin",
        password: str = "admin123",
    ):
        self.api_base_url = api_base_url
        self.session = requests.Session()
        self.access_token = None
        self.refresh_token = None

        # Auto-login if credentials provided
        if username and password:
            self.login(username, password)

    def login(self, username: str, password: str) -> Dict:
        """
        Login to get access token

        Args:
            username: Username
            password: Password

        Returns:
            Login result with tokens
        """
        logger.info(f"🔐 Logging in as: {username}")

        url = f"{self.api_base_url}/auth/login"

        response = self.session.post(
            url, json={"username": username, "password": password}
        )
        response.raise_for_status()

        result = response.json()
        tokens = result.get("data", {}).get("tokens", {})

        self.access_token = tokens.get("access_token")
        self.refresh_token = tokens.get("refresh_token")

        # Set default authorization header
        self.session.headers.update({"Authorization": f"Bearer {self.access_token}"})

        logger.info(f"✅ Login successful")
        return result

    def refresh_access_token(self) -> Dict:
        """
        Refresh access token using refresh token

        Returns:
            New tokens
        """
        logger.info("🔄 Refreshing access token")

        url = f"{self.api_base_url}/auth/refresh"

        response = self.session.post(url, json={"refresh_token": self.refresh_token})
        response.raise_for_status()

        result = response.json()
        tokens = result.get("data", {}).get("tokens", {})

        self.access_token = tokens.get("access_token")
        self.refresh_token = tokens.get("refresh_token")

        # Update authorization header
        self.session.headers.update({"Authorization": f"Bearer {self.access_token}"})

        logger.info(f"✅ Token refreshed")
        return result

    def ceck_template(self, template_name: str) -> Dict:
        """
        Check if template exists

        Args:
            template_name: Name of the template

        Returns:
            Template info if exists, None otherwise
        """
        logger.info(f"Checking template: {template_name}")

        url = f"{self.api_base_url}/templates/check/{template_name}"

        try:
            response = self.session.get(url)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                # Token expired, try to refresh
                logger.info("🔄 Token expired, refreshing...")
                self.refresh_access_token()
                # Retry request
                response = self.session.get(url)
                response.raise_for_status()
            else:
                return None

        result = response.json()
        data = result.get("data", {})
        return data

    def upload_template(self, template_path: str, template_name: str) -> Dict:
        """
        Upload template PDF to system

        Args:
            template_path: Path to template PDF file
            template_name: Name for the template

        Returns:
            Template info with template_id
        """

        check = self.ceck_template(template_name)

        if check:
            logger.info(f"Template {template_name} already exists")
            return check

        logger.info(f"📤 Uploading template: {template_name}")

        url = f"{self.api_base_url}/templates"

        with open(template_path, "rb") as f:
            files = {"file": (os.path.basename(template_path), f, "application/pdf")}
            data = {"template_name": template_name}

            try:
                response = self.session.post(url, files=files, data=data)
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 401:
                    # Token expired, try to refresh
                    logger.info("🔄 Token expired, refreshing...")
                    self.refresh_access_token()
                    # Retry request
                    response = self.session.post(url, files=files, data=data)
                    response.raise_for_status()
                else:
                    raise

        result = response.json()
        data = result.get("data", {})
        template_id = data.get("template_id")

        logger.info(f"✅ Template uploaded successfully. ID: {template_id}")
        return data

    def extract_document(self, pdf_path: str, template_id: int) -> Dict:
        """
        Extract data from document

        Args:
            pdf_path: Path to target PDF
            template_id: Template ID to use

        Returns:
            Extraction results
        """
        logger.info(f"🔍 Extracting document: {os.path.basename(pdf_path)}")

        url = f"{self.api_base_url}/extraction/extract"

        with open(pdf_path, "rb") as f:
            files = {"file": (os.path.basename(pdf_path), f, "application/pdf")}
            data = {"template_id": template_id}

            response = self.session.post(url, files=files, data=data)
            response.raise_for_status()

        result = response.json()
        data = result.get("data", {})
        document_id = data.get("document_id")

        logger.info(f"✅ Extraction complete. Document ID: {document_id}")
        return data

    def submit_corrections(self, document_id: int, corrections: Dict) -> Dict:
        """
        Submit corrections for a document

        Args:
            document_id: Document ID
            corrections: Dictionary of field corrections

        Returns:
            Validation result
        """
        # force corrections = True
        # if not corrections:
        #     logger.info(f"✅ No corrections needed for document {document_id}")
        #     return {"status": "no_corrections"}

        logger.info(
            f"📝 Submitting {len(corrections)} corrections for document {document_id}"
        )

        url = f"{self.api_base_url}/extraction/validate"

        response = self.session.post(
            url, json={"corrections": corrections, "document_id": document_id}
        )
        response.raise_for_status()

        result = response.json()
        logger.info(f"✅ Corrections submitted successfully")
        return result.get("data", {})

    def compare_and_correct(self, extracted_data: Dict, ground_truth: Dict) -> Dict:
        """
        Compare extracted data with ground truth and generate corrections

        Args:
            extracted_data: Data extracted by system
            ground_truth: Ground truth from JSON

        Returns:
            Dictionary of corrections (only fields that differ)
        """
        corrections = {}

        for field_name, true_value in ground_truth.items():
            extracted_value = extracted_data.get(field_name, "")

            # Normalize for comparison (handle newlines, multiple spaces, strip whitespace)
            # This ensures values like "Line1\nLine2" match "Line1 Line2"
            true_normalized = ' '.join(str(true_value).split())
            extracted_normalized = ' '.join(str(extracted_value).split())

            if true_normalized != extracted_normalized:
                corrections[field_name] = true_value
                logger.debug(f"  ❌ {field_name}: '{extracted_value}' → '{true_value}'")
            else:
                logger.debug(f"  ✅ {field_name}: Correct")

        return corrections

    def process_single_document(
        self, pdf_path: str, json_path: str, template_id: int
    ) -> Dict:
        """
        Process a single document: extract → compare → correct

        Args:
            pdf_path: Path to generated PDF
            json_path: Path to ground truth JSON
            template_id: Template ID

        Returns:
            Processing result with stats
        """
        try:
            # 1. Load ground truth
            with open(json_path, "r") as f:
                ground_truth = json.load(f)

            # 2. Extract data
            extraction_result = self.extract_document(pdf_path, template_id)
            document_id = extraction_result["document_id"]
            results = extraction_result["results"]
            extracted_data = results["extracted_data"]

            # sleep for 1 second
            time.sleep(0.5)

            # 3. Compare and generate corrections
            corrections = self.compare_and_correct(extracted_data, ground_truth)

            # sleep for 1 second
            time.sleep(0.5)

            # 4. Submit corrections
            validation_result = self.submit_corrections(document_id, corrections)

            # 5. Return stats
            return {
                "success": True,
                "document_id": document_id,
                "total_fields": len(ground_truth),
                "correct_fields": len(ground_truth) - len(corrections),
                "incorrect_fields": len(corrections),
                "accuracy": (
                    (len(ground_truth) - len(corrections)) / len(ground_truth)
                    if ground_truth
                    else 0
                ),
                "corrections": corrections,
            }

        except Exception as e:
            logger.error(f"❌ Error processing document: {str(e)}")
            return {"success": False, "error": str(e), "pdf_path": pdf_path}

    def seed_template(
        self,
        template_type: str,
        count: int,
        template_pdf_path: str = None,
        output_dir: str = None,
    ) -> Dict:
        """
        Seed a complete template with N documents

        Args:
            template_type: Type of template (e.g., 'certificate_template')
            count: Number of documents to generate
            template_pdf_path: Path to template PDF (optional, will auto-detect)
            output_dir: Output directory (optional, will auto-detect)

        Returns:
            Seeding summary with statistics
        """
        logger.info("=" * 70)
        logger.info(f"🚀 Starting automated seeding for: {template_type}")
        logger.info(f"📊 Target documents: {count}")
        logger.info("=" * 70)

        start_time = time.time()

        # 1. Auto-detect paths if not provided
        if template_pdf_path is None:
            template_pdf_path = f"../cmd/storage/templates/pdf/{template_type}.pdf"

        if output_dir is None:
            output_dir = f"../cmd/storage/output/{template_type}"

        # 2. Upload template (once)
        try:
            template_result = self.upload_template(template_pdf_path, template_type)
            template_id = template_result["template_id"]
        except Exception as e:
            logger.error(f"❌ Failed to upload template: {str(e)}")
            return {"success": False, "error": str(e)}

        # 3. Get list of generated documents
        output_path = Path(output_dir)
        pdf_files = sorted(output_path.glob("*.pdf"))[:count]

        if len(pdf_files) < count:
            logger.warning(
                f"⚠️  Only found {len(pdf_files)} documents, expected {count}"
            )
            logger.warning(
                f"    Please run: python ../cmd/main.py generate-documents --count {count}"
            )

        # 4. Process each document
        results = []
        for i, pdf_file in enumerate(pdf_files, 1):
            json_file = pdf_file.with_suffix(".json")

            if not json_file.exists():
                logger.warning(f"⚠️  Missing ground truth JSON for: {pdf_file.name}")
                continue

            logger.info(
                f"\n📄 Processing document {i}/{len(pdf_files)}: {pdf_file.name}"
            )

            result = self.process_single_document(
                str(pdf_file), str(json_file), template_id
            )
            results.append(result)

            # Small delay to avoid overwhelming the API
            time.sleep(0.5)

        # 5. Calculate summary statistics
        successful = [r for r in results if r.get("success")]
        failed = [r for r in results if not r.get("success")]

        total_fields = sum(r.get("total_fields", 0) for r in successful)
        correct_fields = sum(r.get("correct_fields", 0) for r in successful)
        incorrect_fields = sum(r.get("incorrect_fields", 0) for r in successful)

        overall_accuracy = correct_fields / total_fields if total_fields > 0 else 0

        elapsed_time = time.time() - start_time

        # 6. Print summary
        logger.info("\n" + "=" * 70)
        logger.info("📊 SEEDING SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Template: {template_type}")
        logger.info(f"Template ID: {template_id}")
        logger.info(f"Documents processed: {len(successful)}/{len(results)}")
        logger.info(f"Failed: {len(failed)}")
        logger.info(f"\nField Statistics:")
        logger.info(f"  Total fields: {total_fields}")
        if total_fields > 0:
            logger.info(
                f"  Correct: {correct_fields} ({correct_fields/total_fields*100:.1f}%)"
            )
            logger.info(
                f"  Incorrect: {incorrect_fields} ({incorrect_fields/total_fields*100:.1f}%)"
            )
            logger.info(f"  Overall accuracy: {overall_accuracy*100:.2f}%")
        else:
            logger.info(f"  ⚠️ No fields extracted (all documents failed)")
        logger.info(f"\nTime elapsed: {elapsed_time:.2f} seconds")
        logger.info(f"Avg time per document: {elapsed_time/len(results):.2f} seconds")
        logger.info("=" * 70)

        #  delete output path and files output_path
        for file in output_path.glob("*"):
            file.unlink()

        return {
            "success": True,
            "template_id": template_id,
            "template_type": template_type,
            "documents_processed": len(successful),
            "documents_failed": len(failed),
            "total_fields": total_fields,
            "correct_fields": correct_fields,
            "incorrect_fields": incorrect_fields,
            "overall_accuracy": overall_accuracy,
            "elapsed_time": elapsed_time,
            "results": results,
        }


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Automated seeder for BAB 4 dataset")
    parser.add_argument(
        "--template",
        type=str,
        required=True,
        choices=[
            "certificate_template",
            "contract_template",
            "invoice_template",
            "job_application_template",
            "medical_form_template",
        ],
        help="Template type to seed",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=30,
        help="Number of documents to process (default: 30)",
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8000/api/v1",
        help="API base URL (default: http://localhost:8000/api/v1)",
    )
    parser.add_argument(
        "--username",
        type=str,
        default="admin",
        help="Username for authentication (default: admin)",
    )
    parser.add_argument(
        "--password",
        type=str,
        default="admin123",
        help="Password for authentication (default: admin123)",
    )

    args = parser.parse_args()

    # Initialize seeder with authentication
    seeder = AutomatedSeeder(
        api_base_url=args.api_url, username=args.username, password=args.password
    )

    # Run seeding
    result = seeder.seed_template(template_type=args.template, count=args.count)

    if result["success"]:
        logger.info("\n✅ Seeding completed successfully!")
        logger.info(f"📊 Overall accuracy: {result['overall_accuracy']*100:.2f}%")
    else:
        logger.error("\n❌ Seeding failed!")
        logger.error(f"Error: {result.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
