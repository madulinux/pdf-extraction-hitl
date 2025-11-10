"""
Preview Service
Business logic for template preview generation

Separation of Concerns:
- Routes: HTTP handling
- Service: Business logic (THIS FILE)
- Database: Data access
"""

from typing import Dict, Any, Optional, Tuple
import os
import json
from pdf2image import convert_from_path
from PIL import Image, ImageDraw, ImageFont
import pdfplumber

from database.db_manager import DatabaseManager
from database.repositories.template_repository import TemplateRepository


class PreviewService:
    """Service layer for preview operations"""

    def __init__(
        self,
        db_manager: Optional[DatabaseManager] = None,
        template_repo: Optional[TemplateRepository] = None,
    ):
        self.db = db_manager or DatabaseManager()
        self.template_repo = template_repo or TemplateRepository(db_manager=self.db)

    def generate_preview(
        self,
        template_id: int,
        highlight_field: Optional[str],
        upload_folder: str,
        template_folder: str,
        preview_folder: str,
        page_number: int = 1,
    ) -> str:
        """
        Generate preview image for template

        Args:
            template_id: Template ID
            highlight_field: Optional field name to highlight
            upload_folder: Folder where PDFs are stored
            template_folder: Folder where configs are stored
            preview_folder: Folder to save preview images
            page_number: Page number to preview (default: 1)

        Returns:
            Path to generated preview image
        """
        # Get template info
        template = self.template_repo.find_by_id(template_id)
        if not template:
            raise ValueError(f"Template with ID {template_id} not found")

        # Get template config
        # Load config from database or JSON
        from core.templates.config_loader import get_config_loader

        config_loader = get_config_loader(
            db_manager=self.db, template_folder=template_folder
        )

        config = config_loader.load_config(
            template_id=template_id, config_path=template.config_path
        )

        if not config:
            raise FileNotFoundError("Template configuration not found")

        # Get PDF path
        pdf_path = os.path.join(upload_folder, template.filename)
        if not os.path.exists(pdf_path):
            raise FileNotFoundError("Template PDF file not found")

        # Generate preview filename
        if highlight_field:
            preview_filename = f"template_{template_id}_page_{page_number}_highlight_{highlight_field}.png"
        else:
            preview_filename = f"template_{template_id}_page_{page_number}_preview.png"
        preview_path = os.path.join(preview_folder, preview_filename)

        # Always regenerate if highlight is specified, otherwise check cache
        if highlight_field or not os.path.exists(preview_path):
            self._generate_preview_image(
                pdf_path, config, preview_path, highlight_field, page_number
            )

        return preview_path

    def get_template_config(
        self, template_id: int, template_folder: str
    ) -> Dict[str, Any]:
        """
        Get template configuration

        Args:
            template_id: Template ID
            template_folder: Folder where configs are stored

        Returns:
            Template configuration
        """
        # Get template info
        template = self.template_repo.find_by_id(template_id)
        if not template:
            raise ValueError(f"Template with ID {template_id} not found")

        # Get template config from database or JSON
        from core.templates.config_loader import get_config_loader
        from database.db_manager import DatabaseManager

        db = DatabaseManager()
        config_loader = get_config_loader(
            db_manager=db, template_folder=template_folder
        )

        config = config_loader.load_config(
            template_id=template_id, config_path=template.config_path
        )

        if not config:
            raise FileNotFoundError("Template configuration not found")

        return {
            "template_id": template_id,
            "template_name": template.name,
            "filename": template.filename,
            "config": config,
        }

    def get_pdf_page_count(self, template_id: int, upload_folder: str) -> int:
        """
        Get total number of pages in template PDF

        Args:
            template_id: Template ID
            upload_folder: Folder where PDFs are stored

        Returns:
            Number of pages in PDF
        """
        # Get template info
        template = self.template_repo.find_by_id(template_id)
        if not template:
            raise ValueError(f"Template with ID {template_id} not found")

        # Get PDF path
        pdf_path = os.path.join(upload_folder, template.filename)
        if not os.path.exists(pdf_path):
            raise FileNotFoundError("Template PDF file not found")

        # Count pages
        with pdfplumber.open(pdf_path) as pdf:
            return len(pdf.pages)

    def _generate_preview_image(
        self,
        pdf_path: str,
        config: Dict,
        output_path: str,
        highlight_field: Optional[str],
        page_number: int = 1,
    ):
        """Generate preview image with field overlays and overlap resolution"""
        # Convert specific page to image with higher DPI for better quality
        images = convert_from_path(
            pdf_path, first_page=page_number, last_page=page_number, dpi=200
        )
        if not images:
            raise RuntimeError("Failed to generate preview image")

        # Get base image
        base_image = images[0]
        img_width, img_height = base_image.size

        # Create drawing context
        draw = ImageDraw.Draw(base_image, "RGBA")

        # Load fonts
        font, font_small = self._load_fonts()

        # Get PDF dimensions for coordinate conversion
        with pdfplumber.open(pdf_path) as pdf:
            # Use the specified page (pdfplumber uses 0-indexed pages)
            pdf_page = pdf.pages[page_number - 1]
            pdf_width = pdf_page.width
            pdf_height = pdf_page.height

        # Calculate scale factors
        scale_x = img_width / pdf_width
        scale_y = img_height / pdf_height

        # Prepare field positions for overlap resolution
        field_positions = []
        fields = config.get("fields", {})

        for field_name, field_data in fields.items():
            # Support both old format (single location) and new format (locations array)
            locations = []
            if "locations" in field_data:
                # New format: array of locations
                locations = field_data["locations"]
            elif "location" in field_data:
                # Old format: single location
                locations = [field_data["location"]]

            # Process each location
            for location in locations:
                # Skip fields not on current page
                # Config stores 0-indexed page, we use 1-indexed page_number
                field_page = location.get("page", 0) + 1  # Convert to 1-indexed
                if field_page != page_number:
                    continue

                # Get coordinates
                x0 = location.get("x0", 0)
                y0 = location.get("y0", 0)
                x1 = location.get("x1", 0)
                y1 = location.get("y1", 0)

                # Convert PDF coordinates to image coordinates
                img_x0 = x0 * scale_x
                img_y0 = y0 * scale_y
                img_x1 = x1 * scale_x
                img_y1 = y1 * scale_y

                field_positions.append(
                    {
                        "name": field_name,
                        "x": img_x0,
                        "y": img_y0,
                        "width": img_x1 - img_x0,
                        "height": img_y1 - img_y0,
                        "pdf_x": x0,
                        "pdf_y": y0,
                        "is_highlighted": (highlight_field == field_name),
                    }
                )

        # Resolve overlapping fields
        resolved_positions = self._resolve_overlapping_fields(field_positions)

        # Draw fields with resolved positions
        for field_pos in resolved_positions:
            self._draw_field_overlay(
                draw,
                field_pos["name"],
                (
                    field_pos["x"],
                    field_pos["y"],
                    field_pos["x"] + field_pos["width"],
                    field_pos["y"] + field_pos["height"],
                ),
                (field_pos["pdf_x"], field_pos["pdf_y"]),
                field_pos["is_highlighted"],
                font,
                font_small,
            )

        # Save the image
        base_image.save(output_path, "PNG")

    def _resolve_overlapping_fields(self, field_positions: list[Dict]) -> list[Dict]:
        """Resolve overlapping field positions using smart repositioning"""
        if not field_positions:
            return []

        # Sort fields by y-coordinate first, then x-coordinate
        sorted_fields = sorted(field_positions, key=lambda f: (f["y"], f["x"]))
        resolved_fields = []

        for current_field in sorted_fields:
            # Check for overlaps with already resolved fields
            overlapping = True
            attempts = 0
            max_attempts = 10

            original_x = current_field["x"]
            original_y = current_field["y"]

            while overlapping and attempts < max_attempts:
                overlapping = False

                for resolved_field in resolved_fields:
                    if self._fields_overlap(current_field, resolved_field):
                        overlapping = True
                        # Apply smart repositioning
                        current_field = self._reposition_field(
                            current_field, resolved_field, attempts
                        )
                        break

                attempts += 1

            # If we couldn't resolve overlap, use original position with small offset
            if overlapping:
                current_field["x"] = original_x + (attempts * 5)
                current_field["y"] = original_y + (attempts * 3)

            resolved_fields.append(current_field)

        return resolved_fields

    def _fields_overlap(self, field1: Dict, field2: Dict) -> bool:
        """Check if two fields overlap - using ACTUAL overlap, not margin-based"""
        # NO MARGIN - check actual overlap only
        # This prevents false positives for fields that are close but not overlapping

        x1_left = field1["x"]
        x1_right = field1["x"] + field1["width"]
        y1_top = field1["y"]
        y1_bottom = field1["y"] + field1["height"]

        x2_left = field2["x"]
        x2_right = field2["x"] + field2["width"]
        y2_top = field2["y"]
        y2_bottom = field2["y"] + field2["height"]

        # Check if rectangles ACTUALLY overlap (no margin)
        # Only return true if they truly overlap, not just close
        return not (
            x1_right <= x2_left
            or x2_right <= x1_left
            or y1_bottom <= y2_top
            or y2_bottom <= y1_top
        )

    def _reposition_field(
        self, current_field: Dict, blocking_field: Dict, attempt: int
    ) -> Dict:
        """Reposition a field to avoid overlap"""
        repositioned = current_field.copy()

        # Try different repositioning strategies based on attempt number
        if attempt % 4 == 0:  # Move right
            repositioned["x"] = blocking_field["x"] + blocking_field["width"] + 10
        elif attempt % 4 == 1:  # Move down
            repositioned["y"] = blocking_field["y"] + blocking_field["height"] + 5
        elif attempt % 4 == 2:  # Move left (if possible)
            new_x = blocking_field["x"] - current_field["width"] - 10
            if new_x > 0:
                repositioned["x"] = new_x
            else:
                repositioned["x"] = current_field["x"] + 15
        else:  # Move up (if possible)
            new_y = blocking_field["y"] - current_field["height"] - 5
            if new_y > 0:
                repositioned["y"] = new_y
            else:
                repositioned["y"] = current_field["y"] + 10

        return repositioned

    def _load_fonts(self) -> Tuple[ImageFont.FreeTypeFont, ImageFont.FreeTypeFont]:
        """Load fonts with fallback"""
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
            font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 12)
        except:
            try:
                font = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16
                )
                font_small = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12
                )
            except:
                font = ImageFont.load_default()
                font_small = ImageFont.load_default()
        return font, font_small

    def _draw_field_overlay(
        self,
        draw: ImageDraw.Draw,
        field_name: str,
        img_coords: Tuple[float, float, float, float],
        pdf_coords: Tuple[float, float],
        is_highlighted: bool,
        font: ImageFont.FreeTypeFont,
        font_small: ImageFont.FreeTypeFont,
    ):
        """Draw field overlay on image"""
        img_x0, img_y0, img_x1, img_y1 = img_coords
        x0, y0 = pdf_coords

        # Set colors
        if is_highlighted:
            box_color = (239, 68, 68, 80)
            border_color = (239, 68, 68, 255)
            label_bg_color = (239, 68, 68, 255)
        else:
            box_color = (59, 130, 246, 60)
            border_color = (59, 130, 246, 255)
            label_bg_color = (59, 130, 246, 255)

        # Draw filled rectangle
        draw.rectangle(
            [(img_x0, img_y0), (img_x1, img_y1)],
            fill=box_color,
            outline=border_color,
            width=3 if is_highlighted else 2,
        )

        # Draw label
        label_text = field_name
        bbox = draw.textbbox((0, 0), label_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Label position (above the box)
        label_x = img_x0
        label_y = max(0, img_y0 - text_height - 8)

        # Draw label background
        draw.rectangle(
            [(label_x, label_y), (label_x + text_width + 8, label_y + text_height + 6)],
            fill=label_bg_color,
        )

        # Draw label text
        draw.text(
            (label_x + 4, label_y + 2), label_text, fill=(255, 255, 255, 255), font=font
        )

        # Draw coordinates
        coord_text = f"({int(x0)}, {int(y0)})"
        draw.text(
            (img_x0 + 2, img_y1 + 2), coord_text, fill=border_color, font=font_small
        )
