"""
Batch Seeder - Seed multiple templates at once

This script automates the complete workflow:
1. Generate documents using generator
2. Upload templates
3. Extract and validate all documents
4. Generate summary report

Usage:
    # Seed all templates with default counts
    python batch_seeder.py --all
    
    # Seed specific templates
    python batch_seeder.py --templates certificate_template invoice_template --count 30
    
    # Generate documents first, then seed
    python batch_seeder.py --all --generate --count 40
"""

import sys
import os
import time
import json
import subprocess
from pathlib import Path
from typing import Dict, List
import logging

from automated_seeder import AutomatedSeeder

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Template configurations
TEMPLATE_CONFIGS = {
    'certificate_template': {
        'name': 'Sertifikat Pelatihan',
        'default_count': 10,
        'priority': 1
    },
    'invoice_template': {
        'name': 'Invoice',
        'default_count': 10,
        'priority': 2
    },
    'contract_template': {
        'name': 'Kontrak Kerja',
        'default_count': 10,
        'priority': 3
    },
    'job_application_template': {
        'name': 'Lamaran Kerja',
        'default_count': 10,
        'priority': 4
    },
    'medical_form_template': {
        'name': 'Form Medis',
        'default_count': 10,
        'priority': 5
    }
}


class BatchSeeder:
    """Batch seeder for multiple templates"""
    
    def __init__(self, api_base_url: str = 'http://localhost:8000/api/v1', username: str = 'admin', password: str = 'admin123'):
        self.api_base_url = api_base_url
        self.seeder = AutomatedSeeder(api_base_url, username, password)
        self.results = []
        
    def generate_documents(self, template_type: str, count: int, use_word: bool = False) -> bool:
        """
        Generate documents using the generator script
        
        Args:
            template_type: Template type
            count: Number of documents to generate
            use_word: Use Microsoft Word instead of LibreOffice
            
        Returns:
            True if successful
        """
        logger.info(f"📝 Generating {count} documents for {template_type}...")
        
        cmd_dir = Path(__file__).parent.parent / 'cmd'
        cmd = [
            'python', 'main.py', 'generate-documents',
            '--count', str(count),
            '--workers', '4',
            '--template', template_type
        ]
        
        if use_word:
            cmd.append('--use-word')
        
        try:
            result = subprocess.run(
                cmd,
                cwd=str(cmd_dir),
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            if result.returncode == 0:
                logger.info(f"✅ Documents generated successfully")
                return True
            else:
                logger.error(f"❌ Generation failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"❌ Generation timed out after 5 minutes")
            return False
        except Exception as e:
            logger.error(f"❌ Generation error: {str(e)}")
            return False
    
    def seed_template(self, template_type: str, count: int = None) -> Dict:
        """
        Seed a single template
        
        Args:
            template_type: Template type
            count: Number of documents (None = use default)
            
        Returns:
            Seeding result
        """
        config = TEMPLATE_CONFIGS.get(template_type)
        if not config:
            logger.error(f"❌ Unknown template type: {template_type}")
            return {'success': False, 'error': 'Unknown template type'}
        
        if count is None:
            count = config['default_count']
        
        logger.info(f"\n{'='*70}")
        logger.info(f"🎯 Seeding: {config['name']} ({template_type})")
        logger.info(f"📊 Target: {count} documents")
        logger.info(f"{'='*70}\n")
        
        result = self.seeder.seed_template(template_type, count)
        self.results.append(result)
        
        return result
    
    def seed_all(self, count: int = None, generate: bool = False, use_word: bool = False):
        """
        Seed all templates
        
        Args:
            count: Override count for all templates (None = use defaults)
            generate: Generate documents first
            use_word: Use Microsoft Word for generation
        """
        logger.info("\n" + "🚀" * 35)
        logger.info("BATCH SEEDING - ALL TEMPLATES")
        logger.info("🚀" * 35 + "\n")
        
        start_time = time.time()
        
        # Sort templates by priority
        templates = sorted(
            TEMPLATE_CONFIGS.items(),
            key=lambda x: x[1]['priority']
        )
        
        for template_type, config in templates:
            doc_count = count if count else config['default_count']
            
            # Generate documents if requested
            if generate:
                success = self.generate_documents(template_type, doc_count, use_word)
                if not success:
                    logger.warning(f"⚠️  Skipping {template_type} due to generation failure")
                    continue
            
            # Seed the template
            result = self.seed_template(template_type, doc_count)
            
            # Small delay between templates
            time.sleep(2)
        
        # Print overall summary
        self.print_summary(time.time() - start_time)
    
    def print_summary(self, total_time: float):
        """Print overall summary of all seeding operations"""
        logger.info("\n" + "=" * 70)
        logger.info("📊 BATCH SEEDING SUMMARY")
        logger.info("=" * 70)
        
        successful = [r for r in self.results if r.get('success')]
        failed = [r for r in self.results if not r.get('success')]
        
        logger.info(f"\nTemplates processed: {len(successful)}/{len(self.results)}")
        logger.info(f"Failed: {len(failed)}")
        
        if successful:
            logger.info(f"\n{'Template':<30} {'Docs':<8} {'Accuracy':<12} {'Status'}")
            logger.info("-" * 70)
            
            for result in successful:
                template = result['template_type']
                config = TEMPLATE_CONFIGS.get(template, {})
                name = config.get('name', template)
                docs = result['documents_processed']
                accuracy = result['overall_accuracy'] * 100
                status = "✅ Success"
                
                logger.info(f"{name:<30} {docs:<8} {accuracy:>6.2f}%     {status}")
            
            # Overall statistics
            total_docs = sum(r['documents_processed'] for r in successful)
            total_fields = sum(r['total_fields'] for r in successful)
            correct_fields = sum(r['correct_fields'] for r in successful)
            
            overall_accuracy = correct_fields / total_fields if total_fields > 0 else 0
            
            logger.info("\n" + "-" * 70)
            logger.info(f"{'TOTAL':<30} {total_docs:<8} {overall_accuracy*100:>6.2f}%")
            logger.info("-" * 70)
            
            logger.info(f"\nTotal fields evaluated: {total_fields}")
            if total_fields > 0:
                logger.info(f"Correct: {correct_fields} ({correct_fields/total_fields*100:.1f}%)")
                logger.info(f"Incorrect: {total_fields - correct_fields} ({(total_fields-correct_fields)/total_fields*100:.1f}%)")
            else:
                logger.info(f"⚠️ No fields extracted")
        
        if failed:
            logger.info(f"\n❌ Failed templates:")
            for result in failed:
                logger.info(f"  - {result.get('template_type', 'unknown')}: {result.get('error')}")
        
        logger.info(f"\n⏱️  Total time: {total_time:.2f} seconds")
        logger.info(f"⏱️  Avg time per template: {total_time/len(self.results):.2f} seconds")
        logger.info("=" * 70)
        
        # Save detailed results to JSON
        self.save_results()
    
    def save_results(self):
        """Save detailed results to JSON file"""
        output_dir = Path(__file__).parent / 'results'
        output_dir.mkdir(exist_ok=True)
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"batch_seeding_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump({
                'timestamp': timestamp,
                'results': self.results
            }, f, indent=2)
        
        logger.info(f"\n💾 Detailed results saved to: {output_file}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Batch seeder for multiple templates')
    parser.add_argument('--all', action='store_true',
                       help='Seed all templates')
    parser.add_argument('--templates', nargs='+',
                       choices=list(TEMPLATE_CONFIGS.keys()),
                       help='Specific templates to seed')
    parser.add_argument('--count', type=int,
                       help='Override document count for all templates')
    parser.add_argument('--generate', action='store_true',
                       help='Generate documents first before seeding')
    parser.add_argument('--use-word', action='store_true',
                       help='Use Microsoft Word for document generation')
    parser.add_argument('--api-url', type=str, default='http://localhost:8000/api/v1',
                       help='API base URL')
    parser.add_argument('--username', type=str, default='admin',
                       help='Username for authentication (default: admin)')
    parser.add_argument('--password', type=str, default='admin123',
                       help='Password for authentication (default: admin123)')
    
    args = parser.parse_args()
    
    if not args.all and not args.templates:
        parser.error("Either --all or --templates must be specified")
    
    # Initialize batch seeder with authentication
    batch_seeder = BatchSeeder(
        api_base_url=args.api_url,
        username=args.username,
        password=args.password
    )
    
    # Run seeding
    if args.all:
        batch_seeder.seed_all(
            count=args.count,
            generate=args.generate,
            use_word=args.use_word
        )
    else:
        for template in args.templates:
            if args.generate:
                config = TEMPLATE_CONFIGS[template]
                doc_count = args.count if args.count else config['default_count']
                batch_seeder.generate_documents(template, doc_count, args.use_word)
            
            batch_seeder.seed_template(template, args.count)
        
        # Print summary
        batch_seeder.print_summary(0)
    
    logger.info("\n✅ Batch seeding completed!")


if __name__ == '__main__':
    main()
