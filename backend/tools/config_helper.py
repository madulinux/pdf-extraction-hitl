"""
Config Helper for Debug/Trace Tools

Helper functions to load config from database or JSON for debugging tools.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def load_template_config(template_id, config_path=None):
    """
    Load template config from database or JSON
    
    Args:
        template_id: Template ID
        config_path: Optional JSON config path (fallback)
        
    Returns:
        Config dict or None
    """
    try:
        from core.templates.config_loader import get_config_loader
        from database.db_manager import DatabaseManager
        
        db = DatabaseManager()
        config_loader = get_config_loader(db_manager=db)
        
        config = config_loader.load_config(
            template_id=template_id,
            config_path=config_path
        )
        
        if config:
            source = config.get('metadata', {}).get('source', 'unknown')
            print(f"✅ Loaded config from {source}")
            return config
        else:
            print(f"❌ Failed to load config for template {template_id}")
            return None
            
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        
        # Fallback to JSON if provided
        if config_path:
            try:
                import json
                with open(config_path, 'r') as f:
                    config = json.load(f)
                print(f"⚠️ Loaded config from JSON (fallback)")
                return config
            except Exception as e2:
                print(f"❌ JSON fallback also failed: {e2}")
        
        return None
