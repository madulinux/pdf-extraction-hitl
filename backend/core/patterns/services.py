"""
Pattern Service

Business logic layer for pattern operations.
Follows clean architecture: Routes -> Service -> Repository
"""

from typing import Dict, List, Optional
from database.repositories.config_repository import ConfigRepository
from database.db_manager import DatabaseManager
from database.repositories.template_repository import TemplateRepository


class PatternService:
    """Service for pattern-related operations"""

    def __init__(self, db_manager: DatabaseManager = None):
        """
        Initialize service

        Args:
            db_manager: DatabaseManager instance (optional)
        """
        self.db = db_manager or DatabaseManager()
        self.config_repo = ConfigRepository(self.db)
        self.template_repo = TemplateRepository(self.db)

    def get_template_patterns(self, template_id: int) -> Dict:
        """
        Get all patterns for a template with statistics

        Args:
            template_id: Template ID

        Returns:
            Dict with fields, patterns, and statistics
        """
        # Get template info
        template = self.template_repo.find_by_id(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")

        # Load template config
        from core.templates.config_loader import get_config_loader

        config_loader = get_config_loader(db_manager=self.db)
        config = config_loader.load_config(template_id)

        if not config:
            raise ValueError(f"Template configuration for {template_id} not found")

        # Get all learned patterns grouped by field
        learned_patterns_by_field = (
            self.config_repo.get_all_learned_patterns_by_template(
                template_id, active_only=True
            )
        )

        # Build response for each field
        fields_patterns = {}

        for field_name, field_config in config.get("fields", {}).items():
            # Get base pattern
            validation_rules = field_config.get("validation_rules", {})
            base_pattern = validation_rules.get("pattern", r".+")
            base_source = (
                "validation_rules" if validation_rules.get("pattern") else "default"
            )

            # Get learned patterns for this field
            learned_patterns = learned_patterns_by_field.get(field_name, [])

            # Get statistics
            stats = self.config_repo.get_pattern_statistics(template_id, field_name)

            fields_patterns[field_name] = {
                "base_pattern": {
                    "pattern": base_pattern,
                    "source": base_source,
                    "description": "Base extraction pattern",
                },
                "learned_patterns": learned_patterns,
                "statistics": stats,
                "total_patterns": 1 + len(learned_patterns),
            }

        return {
            "template_id": template_id,
            "template_name": template.name,
            "fields": fields_patterns,
            "summary": {
                "total_fields": len(fields_patterns),
                "fields_with_learned_patterns": sum(
                    1 for f in fields_patterns.values() if f["learned_patterns"]
                ),
                "total_learned_patterns": sum(
                    len(f["learned_patterns"]) for f in fields_patterns.values()
                ),
            },
        }

    def get_field_patterns(self, template_id: int, field_name: str) -> Dict:
        """
        Get detailed pattern information for a specific field

        Args:
            template_id: Template ID
            field_name: Field name

        Returns:
            Dict with field patterns, history, and examples
        """
        # Get field config
        from core.templates.config_loader import get_config_loader

        config_loader = get_config_loader(db_manager=self.db)
        config = config_loader.load_config(template_id)

        if not config or field_name not in config.get("fields", {}):
            raise ValueError(
                f"Field '{field_name}' not found in template {template_id}"
            )

        field_config = config["fields"][field_name]

        # Get base pattern
        validation_rules = field_config.get("validation_rules", {})
        base_pattern = validation_rules.get("pattern", r".+")
        base_source = (
            "validation_rules" if validation_rules.get("pattern") else "default"
        )

        # Get learned patterns
        learned_patterns = self.config_repo.get_learned_patterns_by_field(
            template_id, field_name, active_only=True
        )

        # Get learning history
        learning_history = self.config_repo.get_learning_jobs(
            template_id, field_name=field_name, limit=10
        )

        # Get feedback examples
        feedback_examples = self.config_repo.get_feedback_examples(
            template_id, field_name, limit=5
        )

        # Get statistics
        stats = self.config_repo.get_pattern_statistics(template_id, field_name)

        return {
            "field_name": field_name,
            "field_type": field_config.get("field_type", "text"),
            "base_pattern": {"pattern": base_pattern, "source": base_source},
            "learned_patterns": [dict(lp) for lp in learned_patterns],
            "learning_history": [dict(lh) for lh in learning_history],
            "feedback_examples": [dict(fe) for fe in feedback_examples],
            "statistics": stats,
        }

    def get_learning_jobs(
        self, template_id: int, field_name: Optional[str] = None, limit: int = 50
    ) -> Dict:
        """
        Get pattern learning job history

        Args:
            template_id: Template ID
            field_name: Optional field name filter
            limit: Maximum number of jobs

        Returns:
            Dict with jobs and summary
        """
        jobs = self.config_repo.get_learning_jobs(
            template_id, field_name=field_name, limit=limit
        )

        return {
            "template_id": template_id,
            "field_name": field_name,
            "jobs": [dict(job) for job in jobs],
            "total_jobs": len(jobs),
        }
