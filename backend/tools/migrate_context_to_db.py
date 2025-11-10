"""
Migrate Context Data from JSON to Database

This script reads context information from JSON template config
and populates the field_contexts table in database.
"""

import sys
import os
import json
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from database.repositories.config_repository import ConfigRepository

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def migrate_context_from_json(json_path: str, template_id: int):
    """
    Migrate context data from JSON config to database
    
    Args:
        json_path: Path to JSON config file
        template_id: Template ID in database
    """
    logger.info(f"📖 Reading JSON config: {json_path}")
    
    with open(json_path, 'r') as f:
        config = json.load(f)
    
    fields = config.get('fields', {})
    logger.info(f"   Found {len(fields)} fields")
    
    # Initialize database
    db = DatabaseManager()
    repo = ConfigRepository(db)
    
    # Get active config
    config_header = repo.get_active_config(template_id)
    if not config_header:
        logger.error(f"❌ No active config found for template {template_id}")
        return
    
    config_id = config_header['id']
    logger.info(f"   Using config_id: {config_id}")
    
    total_contexts = 0
    
    # Process each field
    for field_name, field_config in fields.items():
        locations = field_config.get('locations', [])
        
        if not locations:
            logger.warning(f"⚠️  No locations for field: {field_name}")
            continue
        
        # Get field_config_id from database
        field_configs = repo.get_field_configs(config_id)
        field_cfg = next((fc for fc in field_configs if fc['field_name'] == field_name), None)
        
        if not field_cfg:
            logger.warning(f"⚠️  Field not found in database: {field_name}")
            continue
        
        field_config_id = field_cfg['id']
        
        # Get field_locations from database
        db_locations = repo.get_field_locations(field_config_id)
        
        # Match JSON locations with database locations
        for i, json_loc in enumerate(locations):
            context = json_loc.get('context', {})
            
            if not context:
                continue
            
            # Find matching database location
            if i < len(db_locations):
                db_loc = db_locations[i]
                field_location_id = db_loc['id']
                
                # Prepare context data
                label = context.get('label', '')
                label_position = context.get('label_position', {})
                words_before = context.get('words_before', [])
                words_after = context.get('words_after', [])
                
                # Insert into field_contexts table
                conn = db.get_connection()
                cursor = conn.cursor()
                
                try:
                    cursor.execute("""
                        INSERT INTO field_contexts (
                            field_location_id,
                            label,
                            label_position,
                            words_before,
                            words_after
                        ) VALUES (?, ?, ?, ?, ?)
                    """, (
                        field_location_id,
                        label,
                        json.dumps(label_position) if label_position else None,
                        json.dumps(words_before) if words_before else None,
                        json.dumps(words_after) if words_after else None
                    ))
                    
                    conn.commit()
                    total_contexts += 1
                    logger.info(f"   ✅ {field_name}: Added context (label: '{label}')")
                    
                except Exception as e:
                    logger.error(f"   ❌ {field_name}: Failed to insert context: {e}")
                    conn.rollback()
                    
                finally:
                    conn.close()
    
    logger.info(f"\n✅ Migration complete! Added {total_contexts} contexts")


if __name__ == '__main__':
    # Default: migrate certificate template
    json_path = 'templates/20251111_014520_config.json'
    template_id = 1
    
    if len(sys.argv) > 1:
        json_path = sys.argv[1]
    if len(sys.argv) > 2:
        template_id = int(sys.argv[2])
    
    logger.info("=" * 80)
    logger.info("🔄 MIGRATE CONTEXT DATA FROM JSON TO DATABASE")
    logger.info("=" * 80)
    logger.info(f"JSON config: {json_path}")
    logger.info(f"Template ID: {template_id}")
    logger.info("")
    
    migrate_context_from_json(json_path, template_id)
    
    logger.info("\n✅ All done!")
