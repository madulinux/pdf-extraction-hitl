from typing import Dict, List, Optional
from core.extraction.strategies import ExtractionStrategy, FieldValue


class PositionExtractionStrategy(ExtractionStrategy):
    """
    Position-based extraction using coordinate information.
    Good for forms with fixed layouts.
    """

    def extract(
        self, pdf_path: str, field_config: Dict, all_words: List[Dict]
    ) -> Optional[FieldValue]:
        """
        Extract field using position-based approach

        Args:
            pdf_path: Path to PDF file
            field_config: Field configuration with location(s)
            all_words: All extracted words from PDF

        Returns:
            FieldValue if extraction successful, None otherwise
        """
        field_name = field_config.get("field_name", "unknown")

        from .strategies import get_field_locations
        # Get all locations (backward compatible)
        locations = get_field_locations(field_config)

        if not locations:
            return None

        # Try extraction for each location
        best_result = None
        best_confidence = 0.0

        for location in locations:
            try:
                result = self._extract_from_location(location, field_name, all_words)

                if result and result.confidence > best_confidence:
                    best_result = result
                    best_confidence = result.confidence
            except Exception as e:
                self.logger.error(f"Error extracting from location: {e}")
                continue

        return best_result

    def _extract_from_location(
        self, location: Dict, field_name: str, all_words: List[Dict]
    ) -> Optional[FieldValue]:
        """Extract field from a specific location"""
        try:
            # CRITICAL FIX: Data is AT marker position, not after it!
            marker_x0 = location.get("x0", 0)
            marker_x1 = location.get("x1", 0)
            marker_y0 = location.get("y0", 0)
            marker_y1 = location.get("y1", 0)
            marker_y_center = (marker_y0 + marker_y1) / 2

            # Collect all words in the marker area and beyond
            candidate_words = []

            for word in all_words:
                word_x0 = word.get("x0", 0)
                word_x1 = word.get("x1", 0)
                word_y_center = (word.get("top", 0) + word.get("bottom", 0)) / 2
                y_distance = abs(word_y_center - marker_y_center)

                # Include words that:
                # 1. Start at or after marker start (with buffer)
                # 2. Are on the same line (within 10 points vertically)
                if word_x0 >= (marker_x0 - 50) and y_distance < 10:
                    candidate_words.append(
                        {
                            "word": word,
                            "x0": word_x0,
                            "distance": word_x0
                            - marker_x0,  # Distance from marker start
                        }
                    )

            # Sort by horizontal position (left to right)
            candidate_words.sort(key=lambda w: w["x0"])

            # ✅ NEW: Get next field boundary (Y and X)
            context = location.get("context", {})
            next_field_y = context.get("next_field_y") if context else None

            # ✅ CRITICAL: Get X-boundary from words_after (for fields on same line)
            words_after = context.get("words_after", []) if context else []
            next_field_x = None
            if words_after and len(words_after) > 0:
                next_field_x = words_after[0].get("x")

            # Extract ALL words from marker position onwards (same line)
            # ✅ NEW: Stop at next field boundary (Y or X)
            # This handles multi-word values like "Ophelia Yuniar, S.Kom"
            value_words = []
            first_word_pos = None

            if candidate_words:
                for cw in candidate_words:
                    word_x0 = cw["word"].get("x0", 0)
                    word_y = cw["word"].get("top", 0)

                    # ✅ CRITICAL: For same-line fields, ONLY use X-boundary
                    # If next_field_x exists, it means next field is on same line
                    if next_field_x:
                        # Same-line field: use X-boundary only
                        if word_x0 >= next_field_x:
                            break
                    else:
                        # Different-line field: use Y-boundary
                        if next_field_y and word_y >= next_field_y:
                            break

                    if cw["distance"] >= -10:  # At or after marker
                        value_words.append(cw["word"].get("text", ""))
                        if first_word_pos is None:
                            first_word_pos = {
                                "x0": cw["word"].get("x0"),
                                "y0": cw["word"].get("top"),
                            }

            if value_words:
                value = " ".join(value_words).strip()

                # Base confidence for position-based
                confidence = 0.90 if len(value) > 0 else 0.4

                # Boost confidence if context validates the extraction
                context = location.get("context", {})
                if context:
                    confidence = self._validate_with_context(value, context, confidence)

                return FieldValue(
                    field_id=field_name,
                    field_name=field_name,
                    value=value,
                    confidence=confidence,
                    method="position_based",
                    metadata={
                        "marker_position": {
                            "x1": marker_x1,
                            "y0": marker_y0,
                            "y1": marker_y1,
                        },
                        "value_position": first_word_pos,
                        "word_count": len(value_words),
                        "context_validated": bool(context),
                    },
                )

            self.logger.debug(f"No word found near marker for field {field_name}")
            return None

        except Exception as e:
            self.logger.error(f"Position-based extraction failed for {field_name}: {e}")
            return None

    def _validate_with_context(
        self, value: str, context: Dict, base_confidence: float
    ) -> float:
        """
        Validate extracted value using context information
        Boosts confidence if context supports the extraction
        """
        confidence = base_confidence

        # Check if label exists (indicates structured field)
        if context.get("label"):
            confidence = min(confidence + 0.05, 1.0)
            self.logger.debug(f"Context has label, boosting confidence")

        # Check if words_before exist (indicates context awareness)
        words_before = context.get("words_before", [])
        if words_before:
            confidence = min(confidence + 0.03, 1.0)
            self.logger.debug(f"Context has {len(words_before)} words before")

        # Penalize if value is empty but context suggests there should be data
        if not value and (context.get("label") or words_before):
            confidence = max(confidence - 0.3, 0.0)
            self.logger.warning(f"Empty value but context suggests data should exist")

        return confidence
