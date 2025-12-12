"""
Templates Service
Business logic for template management
"""

from typing import Dict, Any, Optional, List
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import json

from .models import Template, TemplateConfig
from database.repositories.template_repository import TemplateRepository
from core.templates.analyzer import TemplateAnalyzer
from shared.exceptions import NotFoundError, ValidationError


class TemplateService:
    """Service layer for template operations"""

    def __init__(
        self,
        repository: TemplateRepository,
        upload_folder: str,
        template_folder: str,
        model_folder: str,
    ):
        self.repository = repository
        self.upload_folder = upload_folder
        self.template_folder = template_folder
        self.model_folder = model_folder
        self.analyzer = TemplateAnalyzer()

    def analyze_and_create(
        self, file: FileStorage, template_name: str
    ) -> Dict[str, Any]:
        """
        Analyze PDF template and create template record

        Args:
            file: Uploaded PDF file
            template_name: Name for the template

        Returns:
            Dictionary with template data and config
        """
        # Validate template name
        if not template_name or template_name.strip() == "":
            raise ValidationError("Template name is required")

        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(self.upload_folder, filename)
        file.save(filepath)

        # Store in database first to get template_id
        template_id = self.repository.create(
            name=template_name,
            filename=filename,
            config_path="",  # Will update after analysis
            field_count=0,  # Will update after analysis
        )

        # Analyze template with template_id and name
        config = self.analyzer.analyze_template(filepath, template_id, template_name)

        # Save configuration to JSON (for backward compatibility)
        config_filename = f"{timestamp}_config.json"
        config_path = os.path.join(self.template_folder, config_filename)
        self.analyzer.save_config(config, config_path)

        # 🆕 Also save to database for new system
        try:
            from core.templates.config_loader import get_config_loader
            from database.db_manager import DatabaseManager

            db = DatabaseManager()
            config_loader = get_config_loader(
                db_manager=db, template_folder=self.template_folder
            )

            # Migrate to database
            db_config_id = config_loader.save_config_to_database(
                template_id=template_id, config=config, created_by="system"
            )

            if db_config_id:
                self.analyzer.logger.info(
                    f"✅ Config saved to database (ID: {db_config_id})"
                )
        except Exception as e:
            self.analyzer.logger.warning(f"Failed to save config to database: {e}")
            # Don't fail the whole operation

        # Update template with config path and field count
        self.repository.update(
            template_id=template_id,
            config_path=config_path,
            field_count=config["metadata"]["field_count"],
        )

        return {
            "template_id": template_id,
            "template_name": template_name,
            "filename": filename,
            "field_count": config["metadata"]["field_count"],
            "config": config,
        }

    def get_all(self) -> List[Dict]:
        """Get all templates"""
        templates = self.repository.find_all()
        return [template.to_dict() for template in templates]

    def get_by_id(
        self, template_id: int, include_config: bool = True
    ) -> Optional[Dict]:
        """
        Get template by ID with optional configuration

        Args:
            template_id: Template ID
            include_config: Whether to include configuration

        Returns:
            Template data with config or None if not found
        """
        template = self.repository.find_by_id(template_id)

        if not template:
            return None

        result = template.to_dict()

        # Load configuration if requested
        if include_config:
            from core.templates.config_loader import get_config_loader
            from database.db_manager import DatabaseManager

            db = DatabaseManager()
            config_loader = get_config_loader(
                db_manager=db, template_folder=self.template_folder
            )

            config = config_loader.load_config(
                template_id=template_id,
                config_path=template.config_path,  # Fallback to JSON
            )
            result["config"] = config

        return result

    def check_template(self, template_name: str) -> Optional[Dict]:
        """
        Check template by name

        Args:
            template_name: Template name

        Returns:
            Template data with config or None if not found
        """
        template = self.repository.find_by_name(template_name)

        if not template:
            return None

        result = template.to_dict()

        return {
            "template_id": result["id"],
            "template_name": result["name"],
            "filename": result["filename"],
            "field_count": result["field_count"],
            "config": result["config_path"],
        }

    def get_by_name(self, template_name: str) -> Optional[Dict]:
        """
        Get template by name

        Args:
            template_name: Template name

        Returns:
            Template data with config or None if not found
        """
        template = self.repository.find_by_name(template_name)

        if not template:
            return None

        result = template.to_dict()

        return result

    def analyze_and_create_bulk(
        self,
        files: List[FileStorage],
        name_mode: str = "filename",
        name_prefix: str = "",
    ) -> Dict[str, Any]:
        """Analyze and create multiple templates in bulk.

        Args:
            files: List of uploaded PDF files
            name_mode: Naming mode for templates. Supported: 'filename'
            name_prefix: Optional prefix to prepend to generated names

        Returns:
            Bulk result summary
        """
        if name_mode not in {"filename"}:
            raise ValidationError("Invalid name_mode. Supported: filename")

        results: Dict[str, Any] = {
            "total": len(files),
            "successful": 0,
            "failed": 0,
            "templates": [],
            "errors": [],
        }

        for file in files:
            try:
                raw_name = os.path.splitext(file.filename or "")[0]
                template_name = raw_name
                if name_prefix:
                    template_name = f"{name_prefix}{template_name}"

                # Fallback if filename is empty after normalization
                if not template_name or template_name.strip() == "":
                    template_name = "Unnamed Template"

                created = self.analyze_and_create(file, template_name)
                results["successful"] += 1
                results["templates"].append(
                    {
                        "template_id": created.get("template_id"),
                        "template_name": created.get("template_name"),
                        "filename": created.get("filename"),
                        "field_count": created.get("field_count"),
                    }
                )

            except Exception as e:
                results["failed"] += 1
                results["errors"].append(
                    {"filename": getattr(file, "filename", ""), "error": str(e)}
                )

        return results

    def delete(self, template_id: int) -> bool:
        """
        Delete template

        Args:
            template_id: Template ID

        Returns:
            True if deleted, False if not found
        """
        template = self.repository.find_by_id(template_id)

        if not template:
            return False

        # Delete from database
        self.repository.delete(template_id)
        os.remove(os.path.join(self.upload_folder, template.filename))
        os.remove(
            os.path.join(self.model_folder, f"template_{template_id}_model.joblib")
        )
        os.remove(
            os.path.join(self.model_folder, f"template_{template_id}_patterns.json")
        )
        os.remove(template.config_path)

        # Delete models .joblib

        return True
