"""
Template Configuration Loader

Abstracts config loading from JSON files or database.
Provides backward compatibility during migration.
"""
import os
import json
import logging
from typing import Dict, Optional, Any
from pathlib import Path


class TemplateConfigLoader:
    """
    Loads template configuration from database or JSON (fallback)
    """
    
    def __init__(self, db_manager=None, template_folder: str = None):
        """
        Initialize config loader
        
        Args:
            db_manager: DatabaseManager instance (optional)
            template_folder: Path to template JSON folder (for fallback)
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.db = db_manager
        self.template_folder = template_folder
        
        # Initialize config repository if DB available
        self.config_repo = None
        if self.db:
            try:
                from database.repositories.config_repository import ConfigRepository
                self.config_repo = ConfigRepository(self.db)
            except Exception as e:
                self.logger.warning(f"Failed to initialize ConfigRepository: {e}")
    
    def load_config(
        self,
        template_id: int,
        config_path: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Load template configuration from database or JSON
        
        Args:
            template_id: Template ID
            config_path: Path to JSON config (fallback)
            
        Returns:
            Configuration dict or None
        """
        # Try database first
        if self.config_repo:
            try:
                config = self._load_from_database(template_id)
                if config:
                    self.logger.debug(f"✅ Loaded config for template {template_id} from database")
                    return config
            except Exception as e:
                self.logger.warning(f"Failed to load from database: {e}")
        
        # Fallback to JSON
        # if config_path:
        #     try:
        #         config = self._load_from_json(config_path)
        #         if config:
        #             self.logger.debug(f"⚠️ Loaded config for template {template_id} from JSON (fallback)")
        #             return config
        #     except Exception as e:
        #         self.logger.error(f"Failed to load from JSON: {e}")
        
        self.logger.error(f"❌ Failed to load config for template {template_id}")
        return None
    
    def _load_from_database(self, template_id: int) -> Optional[Dict[str, Any]]:
        """
        Load config from database
        
        Returns:
            Config dict in same format as JSON
        """
        if not self.config_repo:
            return None
        
        # Get active config
        config_header = self.config_repo.get_active_config(template_id)
        if not config_header:
            return None
        
        config_id = config_header['id']
        
        # Get field configs
        field_configs = self.config_repo.get_field_configs(config_id)
        
        # Build config dict (compatible with JSON format)
        config = {
            'template_id': template_id,
            'template_name': config_header.get('template_name', f'template_{template_id}'),
            'version': config_header.get('version', 1),
            'fields': {}
        }
        
        # Convert field configs to JSON format
        for field_cfg in field_configs:
            field_name = field_cfg['field_name']
            
            # Get locations for this field
            locations = self.config_repo.get_field_locations(field_cfg['id'])
            
            # Get learned patterns
            learned_patterns = self.config_repo.get_learned_patterns(
                field_config_id=field_cfg['id'],
                active_only=True
            )
            
            # Build field config
            field_config = {
                'field_name': field_name,
                'field_type': field_cfg.get('field_type', 'text'),
                'template_id': template_id,
                'regex_pattern': field_cfg.get('base_pattern', r'.+'),
                'confidence_threshold': field_cfg.get('confidence_threshold', 0.7),
                'is_required': field_cfg.get('is_required', False),
                'locations': []
            }
            
            # Add locations with full context
            for loc in locations:
                location = {
                    'page': loc.get('page', 0),
                    'x0': loc['x0'],
                    'y0': loc['y0'],
                    'x1': loc['x1'],
                    'y1': loc['y1']
                }
                
                # Get context from field_contexts table
                context = self.config_repo.get_field_context(loc['id'])
                if context:
                    import json
                    location['context'] = {
                        'label': context.get('label', ''),
                        'label_position': json.loads(context['label_position']) if context.get('label_position') else {},
                        'words_before': json.loads(context['words_before']) if context.get('words_before') else [],
                        'words_after': json.loads(context['words_after']) if context.get('words_after') else [],
                        'next_field_y': context.get('next_field_y')  # ✅ CRITICAL: Load boundary hint!
                    }
                elif loc.get('label'):
                    # Fallback to simple label (backward compatibility)
                    location['context'] = {'label': loc['label']}
                
                field_config['locations'].append(location)
            
            # Add learned patterns (for backward compatibility)
            if learned_patterns:
                field_config['rules'] = {
                    'learned_patterns': []
                }
                for lp in learned_patterns:
                    field_config['rules']['learned_patterns'].append({
                        'pattern': lp['pattern'],
                        'type': lp.get('pattern_type', 'learned'),
                        'description': lp.get('description', ''),
                        'frequency': lp.get('frequency', 0),
                        'priority': lp.get('priority', 0),
                        'pattern_id': lp['id']
                    })
            
            config['fields'][field_name] = field_config
        
        # Add metadata
        config['metadata'] = {
            'field_count': len(field_configs),
            'version': config_header.get('version', 1),
            'created_at': config_header.get('created_at'),
            'source': 'database'
        }
        
        return config
    
    def _load_from_json(self, config_path: str) -> Optional[Dict[str, Any]]:
        """
        Load config from JSON file
        
        Returns:
            Config dict
        """
        if not config_path:
            return None
        
        # Make absolute path if needed
        if not os.path.isabs(config_path) and self.template_folder:
            config_path = os.path.join(self.template_folder, config_path)
        
        if not os.path.exists(config_path):
            return None
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Add source metadata
        if 'metadata' not in config:
            config['metadata'] = {}
        config['metadata']['source'] = 'json'
        
        return config
    
    def save_config_to_database(
        self,
        template_id: int,
        config: Dict[str, Any],
        created_by: str = 'system'
    ) -> Optional[int]:
        """
        Save/migrate JSON config to database
        
        Args:
            template_id: Template ID
            config: Config dict (from JSON)
            created_by: User who created this config
            
        Returns:
            Config ID or None
        """
        if not self.config_repo:
            self.logger.error("Config repository not available")
            return None
        
        try:
            # Check if config already exists
            existing = self.config_repo.get_active_config(template_id)
            if existing:
                self.logger.info(f"Config already exists for template {template_id}")
                return existing['id']
            
            # Create new config
            config_id = self.config_repo.create_config(
                template_id=template_id,
                description=f"Migrated from JSON: {config.get('template_name', 'unknown')}",
                created_by=created_by
            )
            
            # Add fields
            fields = config.get('fields', {})
            for field_name, field_cfg in fields.items():
                # Create field config
                field_config_id = self.config_repo.create_field_config(
                    config_id=config_id,
                    field_name=field_name,
                    field_type=field_cfg.get('field_type', 'text'),
                    base_pattern=field_cfg.get('regex_pattern', r'.+'),
                    confidence_threshold=field_cfg.get('confidence_threshold', 0.7),
                    is_required=field_cfg.get('is_required', False)
                )
                
                # Add locations
                locations = field_cfg.get('locations', [])
                if not locations and 'location' in field_cfg:
                    # Single location (old format)
                    locations = [field_cfg['location']]
                
                for idx, loc in enumerate(locations):
                    # Create field location
                    field_location_id = self.config_repo.create_field_location(
                        field_config_id=field_config_id,
                        page=loc.get('page', 0),
                        x0=loc['x0'],
                        y0=loc['y0'],
                        x1=loc['x1'],
                        y1=loc['y1'],
                        label=loc.get('context', {}).get('label'),
                        location_index=idx
                    )
                    
                    # ✅ NEW: Save context data to field_contexts table
                    context = loc.get('context', {})
                    if context and field_location_id:
                        self.config_repo.create_field_context(
                            field_location_id=field_location_id,
                            label=context.get('label', ''),
                            label_position=context.get('label_position', {}),
                            words_before=context.get('words_before', []),
                            words_after=context.get('words_after', []),
                            next_field_y=context.get('next_field_y')  # ✅ NEW
                        )
                
                # Add learned patterns if any
                learned_patterns = field_cfg.get('rules', {}).get('learned_patterns', [])
                for lp in learned_patterns:
                    self.config_repo.add_learned_pattern(
                        field_config_id=field_config_id,
                        pattern=lp['pattern'],
                        pattern_type=lp.get('type', 'learned'),
                        description=lp.get('description', ''),
                        frequency=lp.get('frequency', 0),
                        priority=lp.get('priority', 0)
                    )
            
            self.logger.info(f"✅ Migrated config for template {template_id} to database")
            return config_id
            
        except Exception as e:
            self.logger.error(f"Failed to save config to database: {e}", exc_info=True)
            return None


# Singleton instance
_config_loader_instance = None


def get_config_loader(db_manager=None, template_folder: str = None):
    """
    Get singleton config loader instance
    
    Args:
        db_manager: DatabaseManager instance
        template_folder: Template folder path
        
    Returns:
        TemplateConfigLoader instance
    """
    global _config_loader_instance
    
    if _config_loader_instance is None:
        if db_manager is None:
            try:
                from database.db_manager import DatabaseManager
                db_manager = DatabaseManager()
            except:
                pass  # OK to not have DB for JSON-only mode
        
        _config_loader_instance = TemplateConfigLoader(
            db_manager=db_manager,
            template_folder=template_folder
        )
    
    return _config_loader_instance
