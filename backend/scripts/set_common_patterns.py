#!/usr/bin/env python3
"""
Script to set common regex patterns for template fields
Useful for quickly setting up base patterns before adaptive learning
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from database.repositories.config_repository import ConfigRepository

# Common patterns mapping with capturing groups for extraction
# Patterns use () to extract value from within text
# Example: r'(\d+)' will extract "27" from ": 27 Tahun"
COMMON_PATTERNS = {
    'email': r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
    'phone': r'(\+?[0-9]{1,4}?[-.\\s]?\\(?[0-9]{1,3}?\\)?[-.\\s]?[0-9]{1,4}[-.\\s]?[0-9]{1,4}[-.\\s]?[0-9]{1,9})',
    'date_dd_mm_yyyy': r'(\d{2}-\d{2}-\d{4})',
    'date_yyyy_mm_dd': r'(\d{4}-\d{2}-\d{2})',
    'number': r'(\d+)',
    'decimal': r'(\d+\.\d+)',
    'text': r'([a-zA-Z\s]+)',
    'alphanumeric': r'([a-zA-Z0-9]+)',
    'nik': r'(\d{16})',  # Indonesian NIK (16 digits)
    'any': r'(.+)',
}

# Field name to pattern type mapping (customize this)
FIELD_PATTERN_MAP = {
    'email': 'email',
    'no_hp': 'phone',
    'tanggal_lahir': 'date_dd_mm_yyyy',
    'tanggal_daftar': 'date_dd_mm_yyyy',
    'usia': 'number',
    'nik': 'nik',
    'nama_lengkap': 'text',
    'tempat_lahir': 'text',
    'alamat': 'any',
    'desa': 'text',
    'kecamatan': 'text',
    'kabupaten': 'text',
    'kabupaten_daftar': 'text',
    'jenis_kelamin': 'text',
    'status_kawin': 'text',
}


def set_patterns_for_template(template_id: int, field_map: dict = None, dry_run: bool = False):
    """
    Set common patterns for template fields
    
    Args:
        template_id: Template ID
        field_map: Custom field to pattern type mapping (optional)
        dry_run: If True, only show what would be updated
    """
    if field_map is None:
        field_map = FIELD_PATTERN_MAP
    
    db = DatabaseManager()
    config_repo = ConfigRepository(db)
    
    # Get active config
    config = config_repo.get_active_config(template_id)
    if not config:
        print(f"❌ No active config found for template {template_id}")
        return
    
    print(f"📋 Template ID: {template_id}")
    print(f"📋 Config ID: {config['id']}")
    print(f"📋 Config Version: {config['version']}")
    print()
    
    # Get all field configs
    field_configs = config_repo.get_field_configs(config['id'])
    
    updated_count = 0
    skipped_count = 0
    
    for field_cfg in field_configs:
        field_name = field_cfg['field_name']
        current_pattern = field_cfg.get('base_pattern')
        
        # Check if field has mapping
        if field_name not in field_map:
            print(f"⏭️  {field_name}: No pattern mapping defined")
            skipped_count += 1
            continue
        
        pattern_type = field_map[field_name]
        new_pattern = COMMON_PATTERNS.get(pattern_type)
        
        if not new_pattern:
            print(f"❌ {field_name}: Invalid pattern type '{pattern_type}'")
            skipped_count += 1
            continue
        
        # Skip if already has pattern
        if current_pattern:
            print(f"⏭️  {field_name}: Already has pattern (skipping)")
            skipped_count += 1
            continue
        
        # Update pattern
        if dry_run:
            print(f"🔍 {field_name}: Would set to '{new_pattern}' ({pattern_type})")
        else:
            try:
                config_repo.update_field_config(
                    field_config_id=field_cfg['id'],
                    base_pattern=new_pattern
                )
                print(f"✅ {field_name}: Set to '{new_pattern}' ({pattern_type})")
                updated_count += 1
            except Exception as e:
                print(f"❌ {field_name}: Failed to update - {e}")
                skipped_count += 1
    
    print()
    print(f"📊 Summary:")
    print(f"   Updated: {updated_count}")
    print(f"   Skipped: {skipped_count}")
    print(f"   Total: {len(field_configs)}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Set common patterns for template fields')
    parser.add_argument('template_id', type=int, help='Template ID')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be updated without making changes')
    
    args = parser.parse_args()
    
    print("🔧 Setting Common Patterns for Template Fields")
    print("=" * 60)
    print()
    
    set_patterns_for_template(args.template_id, dry_run=args.dry_run)
    
    if args.dry_run:
        print()
        print("💡 This was a dry run. Use without --dry-run to apply changes.")
