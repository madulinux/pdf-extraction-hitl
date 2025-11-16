from typing import Dict, List, Any, Optional
from .strategies import ExtractionStrategy, FieldValue, get_field_locations


class CRFExtractionStrategy(ExtractionStrategy):
    """
    CRF-based extraction using machine learning.
    Improves with training data from user feedback.
    """

    def __init__(self, model_path: Optional[str] = None):
        super().__init__()
        self.model = None
        self.model_path = model_path
        self.model_mtime = None  # Track model file modification time

        if model_path:
            self._load_model(model_path)

    def _load_model(self, model_path: str, force_reload: bool = False):
        """
        Load trained CRF model with hot reload support

        Args:
            model_path: Path to model file
            force_reload: Force reload even if file hasn't changed
        """
        try:
            import joblib
            import os

            if not os.path.exists(model_path):
                self.model = None
                self.model_mtime = None
                self.logger.error(f"❌ [CRF] Model file not found: {model_path}")
                return

            # Check if model file has been updated
            current_mtime = os.path.getmtime(model_path)

            if (
                not force_reload
                and self.model is not None
                and self.model_mtime == current_mtime
            ):
                # Model already loaded and file hasn't changed
                return

            # print(f"🔍 [CRF] Loading model from: {model_path}")
            self.model = joblib.load(model_path)
            self.model_mtime = current_mtime
            # print(f"✅ [CRF] Model loaded successfully (mtime: {current_mtime})")
            # print(f"✅ [CRF] Model type: {type(self.model)}")

            # ✅ DEBUG: Show what labels the model knows
            if hasattr(self.model, "classes_"):
                self.logger.info(f"📋 [CRF] Model knows these labels: {self.model.classes_}")

        except Exception as e:
            self.logger.error(f"❌ [CRF] Error loading model: {e}")
            import traceback

            self.logger.error(traceback.format_exc())
            self.model = None
            self.model_mtime = None

    def reload_model_if_updated(self):
        """Check and reload model if file has been updated"""
        if self.model_path:
            self._load_model(self.model_path, force_reload=False)

    def extract(
        self, pdf_path: str, field_config: Dict, all_words: List[Dict]
    ) -> Optional[FieldValue]:
        """
        Extract field using CRF model with hot reload support

        Args:
            pdf_path: Path to PDF file
            field_config: Field configuration
            all_words: All extracted words from PDF

        Returns:
            FieldValue if extraction successful, None otherwise
        """
        field_name = field_config.get("field_name", "unknown")

        # 🔥 HOT RELOAD: Check if model has been updated
        self.reload_model_if_updated()

        if not self.model:
            self.logger.error(f"❌ [CRF] Model not available for field '{field_name}'")
            return None

        self.logger.info(f"🤖 [CRF] Model IS available, extracting '{field_name}'...")

        try:
            # Get all locations for context
            locations = get_field_locations(field_config)
            context = locations[0].get("context", {}) if locations else {}

            # ✅ FIELD-AWARE: Prepare features with target field indicator
            # This tells the model which field we're looking for
            features = self._extract_features(
                all_words,
                field_name,
                field_config,
                context,
                target_field=field_name,  # ✅ NEW: Pass target field
            )

            # Predict using CRF model
            predictions = self.model.predict([features])[0]
            marginals = self.model.predict_marginals([features])[0]

            # Extract tokens labeled for this field
            target_label = f"B-{field_name.upper()}"
            inside_label = f"I-{field_name.upper()}"

            # print(f"🔍 [CRF] Looking for labels: {target_label}, {inside_label}")
            # print(f"🔍 [CRF] Predictions sample (first 10): {predictions[:10]}")
            # print(f"🔍 [CRF] Unique labels in predictions: {set(predictions)}")

            extracted_tokens = []
            confidences = []

            # ✅ ADAPTIVE: Get next field boundary (Y and X)
            next_field_y = context.get("next_field_y")
            # print(f"   📏 [Debug] next_field_y from context: {next_field_y}")

            # ✅ CRITICAL: Get X-boundary from words_after (for fields on same line)
            words_after = context.get("words_after", [])
            next_field_x = None
            if words_after and len(words_after) > 0:
                next_field_x = words_after[0].get("x")
                # print(f"   📏 [Debug] next_field_x from words_after: {next_field_x}")

            # ✅ ADAPTIVE: Get typical field length (learned from training data)
            typical_length = context.get("typical_length")
            max_length = (
                int(typical_length * 1.3) if typical_length else None
            )  # 1.3x = 30% tolerance
            # print(f"   📏 [Debug] typical_length: {typical_length}, max_length: {max_length}")

            # ✅ ADAPTIVE: Track parentheses state to skip content inside
            inside_parentheses = False

            # ✅ Let model learn boundaries from training data
            # But enforce hard stop at next_field_y/X (adaptive, not hardcoded!)
            for i, (pred, marginal) in enumerate(zip(predictions, marginals)):
                if pred in [target_label, inside_label]:
                    if i < len(all_words):
                        word = all_words[i]
                        word_x0 = word.get("x0", 0)
                        word_y = word.get("top", 0)
                        word_text = word.get("text", "")

                        # ✅ CRITICAL: For same-line fields, ONLY use X-boundary
                        # If next_field_x exists, it means next field is on same line
                        if next_field_x:
                            # Same-line field: use X-boundary only
                            if word_x0 >= next_field_x:
                                # print(f"   🛑 [Adaptive] Stopped at next field X boundary (word_x0={word_x0} >= next_field_x={next_field_x})")
                                # print(f"   📊 [Adaptive] Extracted {len(extracted_tokens)} tokens before X boundary")
                                break
                        else:
                            # Different-line field: use Y-boundary
                            if next_field_y and word_y >= next_field_y:
                                # print(f"   🛑 [Adaptive] Stopped at next field Y boundary (word_y={word_y} >= next_field_y={next_field_y})")
                                # print(f"   📊 [Adaptive] Extracted {len(extracted_tokens)} tokens before boundary")
                                break

                        # ✅ ADAPTIVE: Stop if extracted length exceeds typical length (learned from training)
                        current_length = len(" ".join(extracted_tokens + [word_text]))
                        if max_length and current_length > max_length:
                            # print(f"   🛑 [Adaptive] Stopped at length limit (current={current_length} > max={max_length})")
                            # print(f"   📊 [Adaptive] Extracted {len(extracted_tokens)} tokens before length limit")
                            break

                        # ✅ ADAPTIVE: Track and skip ALL content inside parentheses
                        # This prevents extracting metadata like "(Supervisor: Dr. John)"
                        if word_text == "(":
                            inside_parentheses = True
                            continue
                        elif word_text == ")":
                            inside_parentheses = False
                            continue
                        elif inside_parentheses:
                            continue  # Skip content inside parentheses

                        conf = marginal.get(pred, 0.0)
                        extracted_tokens.append(word_text)
                        confidences.append(conf)

            if extracted_tokens:
                raw_value = " ".join(extracted_tokens)
                import numpy as np

                avg_confidence = float(np.mean(confidences)) if confidences else 0.5

                # ✅ ADAPTIVE: Remove text BEFORE label (if label exists in extracted text)
                # This is NOT hardcoded - it uses label from context dynamically
                label = context.get("label", "")
                if label and label in raw_value:
                    # Find label position and take only text AFTER it
                    parts = raw_value.split(label, 1)
                    if len(parts) > 1:
                        raw_value = parts[1].strip()
                        # print(f"   🎯 [Adaptive] Removed text before label '{label}'")

                # ✅ CRITICAL FIX: Apply post-processing like rule-based does
                # This removes parentheses, trailing commas, etc.
                cleaned_value = self._post_process_value(
                    raw_value, field_name, raw_value
                )

                # print(f"✅ [CRF] Extracted '{field_name}': {cleaned_value[:50]}... (conf: {avg_confidence:.2f})")
                # if raw_value != cleaned_value:
                    # print(f"   🧹 Cleaned: '{raw_value}' → '{cleaned_value}'")

                return FieldValue(
                    field_id=field_name,
                    field_name=field_name,
                    value=cleaned_value,  # ✅ Use cleaned value
                    confidence=avg_confidence,
                    method="crf",
                    metadata={
                        "model_path": self.model_path,
                        "token_count": len(extracted_tokens),
                        "confidence_scores": confidences,
                        "raw_value": raw_value,  # Keep raw for debugging
                    },
                )

            # ✅ DETAILED LOGGING: Why CRF returned None
            # print(f"⚠️ [CRF] No tokens found for '{field_name}'")
            # print(f"   Looking for: {target_label}, {inside_label}")
            # print(f"   Total predictions: {len(predictions)}")
            # print(f"   Unique labels predicted: {set(predictions)}")

            # Count how many times target field was predicted (even if not selected)
            # target_count = sum(1 for p in predictions if field_name.upper() in p)
            # if target_count > 0:
                # print(f"   ⚠️ Model predicted {target_count} tokens with '{field_name.upper()}' but none matched B-/I- pattern!")
                # Show sample predictions with indices
                # related_preds = [
                #     (i, all_words[i]["text"], p)
                #     for i, p in enumerate(predictions)
                #     if field_name.upper() in p and i < len(all_words)
                # ]
                # print(f"   Sample predictions: {related_preds[:5]}")
            # else:
            #     print(f"   ℹ️ Model did not predict any tokens for this field")

            # self.logger.debug(f"⚠️ CRF: No tokens found for '{field_name}' (predicted {target_count} related tokens)")
            return None

        except Exception as e:
            self.logger.error(f"CRF extraction failed for {field_name}: {e}")
            return None

    def _extract_features(
        self,
        words: List[Dict],
        field_name: str,
        field_config: Dict,
        context: Dict,
        target_field: str = None,  # ✅ NEW: Target field for field-aware features
    ) -> List[Dict[str, Any]]:
        """
        Extract features from words for CRF model with context information
        MUST match exactly with AdaptiveLearner._extract_word_features!

        Args:
            words: List of word dictionaries
            field_name: Name of the field being extracted
            field_config: Field configuration
            context: Context information (label, position, etc.)
            target_field: Target field name for field-aware features
        """
        features = []

        # ✅ NEW: Detect column structure from X-coordinates
        x_coords = [w.get("x0", 0) for w in words]
        column_boundaries = self._detect_column_boundaries(x_coords)

        # ✅ NEW: Detect line groups for text wrapping
        line_groups = self._detect_line_groups(words)

        # Extract context information
        label = context.get("label", "")
        label_pos = context.get("label_position", {})
        words_before = context.get("words_before", [])
        words_after = context.get("words_after", [])

        # Build context text for matching
        context_before_text = " ".join(
            w.get("text", "") if isinstance(w, dict) else str(w) for w in words_before
        ).lower()
        context_after_text = " ".join(
            w.get("text", "") if isinstance(w, dict) else str(w) for w in words_after
        ).lower()

        # Import regex for pattern matching
        import re

        for i, word in enumerate(words):
            text = word.get("text", "")
            word_x = word.get("x0", 0)
            word_y = word.get("top", 0)

            word_features = {
                # Lexical features
                "word": text,
                "word.lower": text.lower(),
                "word.isupper": text.isupper(),
                "word.istitle": text.istitle(),
                "word.isdigit": text.isdigit(),
                "word.isalpha": text.isalpha(),
                "word.isalnum": text.isalnum(),
                "word.length": len(text),
                # Orthographic features
                "has_digit": any(c.isdigit() for c in text),
                "has_upper": any(c.isupper() for c in text),
                "has_hyphen": "-" in text,
                "has_dot": "." in text,
                "has_comma": "," in text,
                "has_slash": "/" in text,
                # Layout features (normalized)
                "x0_norm": word.get("x0", 0) / 1000,
                "y0_norm": word.get("top", 0) / 1000,
                "width": (word.get("x1", 0) - word.get("x0", 0)) / 1000,
                "height": (word.get("bottom", 0) - word.get("top", 0)) / 1000,
                # ✅ NEW: Date-specific features (PATTERN-BASED, NOT HARDCODED!)
                "is_capitalized_word": text.istitle()
                and text.isalpha()
                and len(text) > 2,  # Likely month/location
                "is_year": text.isdigit()
                and len(text) == 4
                and 1900 <= int(text) <= 2100,
                "is_day_number": text.isdigit()
                and len(text) <= 2
                and (1 <= int(text) <= 31 if text.isdigit() else False),
                "is_date_separator": text in [",", "-", "/", "."],
                "looks_like_date_pattern": bool(
                    re.match(r"\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4}", text)
                ),
                "has_numeric_context": False,  # Will be set below based on neighbors
                # ✅ NEW: Boundary detection features (MUST MATCH learner.py!)
                "is_after_punctuation": False,
                "is_before_punctuation": False,
                "is_after_newline": False,
                "position_in_line": 0,
                # Context features
                "has_label": bool(label),
                "label_text": label.lower() if label else "",
                "in_context_before": text.lower() in context_before_text,
                "in_context_after": text.lower() in context_after_text,
            }

            # ✅ ENHANCED: Distance from label with stronger constraints (MUST match learner.py!)
            if label_pos:
                label_x0 = label_pos.get("x0", 0)
                label_x1 = label_pos.get("x1", 0)
                label_y0 = label_pos.get("y0", 0)
                label_y1 = label_pos.get("y1", 0)

                distance_x = word_x - label_x1
                distance_y = abs(word_y - label_y0)

                # ✅ ENHANCED: Stronger positional constraints for complex layouts
                is_after_label = distance_x > 0
                is_before_label = word_x < label_x0
                is_above_label = word_y < label_y0
                is_below_label = word_y > label_y1
                is_same_line = distance_y < 10

                word_features["distance_from_label_x"] = distance_x / 100  # Normalized
                word_features["distance_from_label_y"] = distance_y / 100
                word_features["after_label"] = is_after_label
                word_features["before_label"] = is_before_label  # ✅ NEW
                word_features["above_label"] = is_above_label  # ✅ NEW
                word_features["below_label"] = is_below_label  # ✅ NEW
                word_features["same_line_as_label"] = is_same_line
                word_features["near_label"] = distance_x < 50 and is_same_line
                word_features["valid_position"] = (
                    is_after_label and is_same_line
                )  # ✅ NEW
            else:
                word_features["distance_from_label_x"] = 0
                word_features["distance_from_label_y"] = 0
                word_features["after_label"] = False
                word_features["before_label"] = False
                word_features["above_label"] = False
                word_features["below_label"] = False
                word_features["same_line_as_label"] = False
                word_features["near_label"] = False
                word_features["valid_position"] = False

            # ✅ NEW: Next field boundary features (MUST match learner.py!)
            next_field_y = context.get("next_field_y")
            if next_field_y is not None:
                distance_to_next = next_field_y - word_y
                word_features["has_next_field"] = True
                word_features["distance_to_next_field"] = distance_to_next / 100
                word_features["before_next_field"] = distance_to_next > 0
                word_features["near_next_field"] = 0 < distance_to_next < 20
                word_features["far_from_next_field"] = distance_to_next > 50
            else:
                word_features["has_next_field"] = False
                word_features["distance_to_next_field"] = 0
                word_features["before_next_field"] = False
                word_features["near_next_field"] = False
                word_features["far_from_next_field"] = False

            # Prefix and suffix features
            if len(text) > 1:
                word_features["prefix-2"] = text[:2]
                word_features["suffix-2"] = text[-2:]
            if len(text) > 2:
                word_features["prefix-3"] = text[:3]
                word_features["suffix-3"] = text[-3:]

            # ✅ ENHANCED: Extended context window (2-3 words) - MUST MATCH learner.py!
            if i > 0:
                prev_word = words[i - 1].get("text", "")
                prev_y = words[i - 1].get("top", 0)

                # Context features (previous word)
                word_features["prev_word"] = prev_word.lower()
                word_features["prev_word.isupper"] = prev_word.isupper()
                word_features["prev_word.istitle"] = prev_word.istitle()
                word_features["prev_word.isdigit"] = prev_word.isdigit()

                # ✅ NEW: 2-word context (critical for multi-word prefixes like "Jalan W.R.")
                if i > 1:
                    prev2_word = words[i - 2].get("text", "")
                    word_features["prev2_word"] = prev2_word.lower()
                    word_features["prev2_word.istitle"] = prev2_word.istitle()
                    # Bigram feature (2-word sequence before current word)
                    word_features["prev_bigram"] = (
                        f"{prev2_word.lower()}_{prev_word.lower()}"
                    )

                # ✅ NEW: 3-word context (for longer prefixes)
                if i > 2:
                    prev3_word = words[i - 3].get("text", "")
                    word_features["prev3_word"] = prev3_word.lower()
                    # Trigram feature
                    word_features["prev_trigram"] = (
                        f"{prev3_word.lower()}_{prev2_word.lower() if i > 1 else ''}_{prev_word.lower()}"
                    )

                # Boundary features
                word_features["is_after_punctuation"] = prev_word in [
                    ",",
                    ".",
                    ":",
                    ";",
                    ")",
                    "(",
                ]
                word_features["is_after_newline"] = abs(word_y - prev_y) > 10

                # Numeric context (for dates, numbers, etc.)
                word_features["has_numeric_context"] = (
                    prev_word.isdigit()
                    or word_features["is_year"]
                    or word_features["is_day_number"]
                    or (
                        prev_word.istitle()
                        and prev_word.isalpha()
                        and len(prev_word) > 2
                    )  # Capitalized word (month/location)
                )
            else:
                word_features["BOS"] = True

            # ✅ ENHANCED: Extended next word context - MUST MATCH learner.py!
            if i < len(words) - 1:
                next_word = words[i + 1].get("text", "")

                word_features["next_word"] = next_word.lower()
                word_features["next_word.isupper"] = next_word.isupper()
                word_features["next_word.istitle"] = next_word.istitle()
                word_features["next_word.isdigit"] = next_word.isdigit()

                # ✅ NEW: 2-word lookahead context
                if i < len(words) - 2:
                    next2_word = words[i + 2].get("text", "")
                    word_features["next2_word"] = next2_word.lower()
                    word_features["next2_word.istitle"] = next2_word.istitle()
                    # Bigram feature (2-word sequence after current word)
                    word_features["next_bigram"] = (
                        f"{next_word.lower()}_{next2_word.lower()}"
                    )

                # ✅ NEW: 3-word lookahead context
                if i < len(words) - 3:
                    next3_word = words[i + 3].get("text", "")
                    word_features["next3_word"] = next3_word.lower()
                    # Trigram feature
                    word_features["next_trigram"] = (
                        f"{next_word.lower()}_{next2_word.lower() if i < len(words) - 2 else ''}_{next3_word.lower()}"
                    )

                # Boundary features
                word_features["is_before_punctuation"] = next_word in [
                    ",",
                    ".",
                    ":",
                    ";",
                    ")",
                    "(",
                ]

                # Enhance numeric context with next word
                if not word_features["has_numeric_context"]:
                    word_features["has_numeric_context"] = next_word.isdigit() or (
                        next_word.istitle()
                        and next_word.isalpha()
                        and len(next_word) > 2
                    )
            else:
                word_features["EOS"] = True

            # Position in line (for boundary detection)
            word_features["position_in_line"] = sum(
                1 for w in words[:i] if abs(w.get("top", 0) - word_y) < 5
            )

            # ✅ NEW: Column-based features for multi-column layout
            column_idx = self._get_column_index(word_x, column_boundaries)
            word_features["column_index"] = column_idx
            word_features["in_first_column"] = column_idx == 0
            word_features["in_second_column"] = column_idx == 1
            word_features["in_third_column"] = column_idx == 2
            word_features["in_fourth_column"] = column_idx == 3

            # ✅ NEW: Line group features for text wrapping detection
            line_group_idx = self._get_line_group_index(i, line_groups)
            word_features["line_group_index"] = line_group_idx
            word_features["is_first_line_in_group"] = self._is_first_line_in_group(
                i, line_groups
            )
            word_features["is_continuation_line"] = self._is_continuation_line(
                i, line_groups
            )

            # ✅ NEW: Sequence position features (for Finding vs Recommendation)
            word_features["relative_x_position"] = (
                word_x / max(x_coords) if x_coords else 0
            )
            word_features["is_left_aligned"] = word_x < 200  # Typically Finding
            word_features["is_right_aligned"] = word_x > 400  # Typically Recommendation
            word_features["is_center_aligned"] = 200 <= word_x <= 400

            # ✅ NEW: Delimiter detection (for Finding/Recommendation separation)
            word_features["is_delimiter"] = text in ["|", "/", "\\", ":", ";"]
            word_features["after_delimiter"] = False
            if i > 0 and words[i - 1].get("text", "") in ["|", "/", "\\", ":", ";"]:
                word_features["after_delimiter"] = True

            # ✅ NEW: Number sequence detection (for Area ID, No, etc.)
            word_features["is_sequence_number"] = text.isdigit() and len(text) <= 2
            word_features["is_long_number"] = (
                text.isdigit() and len(text) > 5
            )  # Area Code
            word_features["after_sequence_number"] = False
            if (
                i > 0
                and words[i - 1].get("text", "").isdigit()
                and len(words[i - 1].get("text", "")) <= 2
            ):
                word_features["after_sequence_number"] = True

            # ✅ NEW: Sentence boundary features (for Finding vs Recommendation)
            word_features["starts_with_capital"] = text and text[0].isupper()
            word_features["after_period"] = (
                i > 0 and words[i - 1].get("text", "") == "."
            )
            word_features["before_period"] = (
                i < len(words) - 1 and words[i + 1].get("text", "") == "."
            )

            # ✅ NEW: Word density features (for table detection)
            words_in_same_line = [w for w in words if abs(w.get("top", 0) - word_y) < 5]
            word_features["words_in_line"] = len(words_in_same_line)
            word_features["is_dense_line"] = (
                len(words_in_same_line) > 10
            )  # Likely table row
            word_features["is_sparse_line"] = len(words_in_same_line) < 5

            # ✅ CRITICAL: Add field-aware feature for target field
            # This tells the model which field we're currently extracting
            # During training: all fields in document have this feature set to True
            # During inference: only the target field has this feature set to True
            if target_field:
                word_features[f"target_field_{target_field}"] = True
                # Debug: Log first word to verify feature is added
                # if i == 0:
                #     print(f"🔍 [CRF] Added field-aware feature: target_field_{target_field}=True")

            features.append(word_features)

        return features

    def _detect_column_boundaries(self, x_coords: List[float]) -> List[float]:
        """
        Detect column boundaries from X-coordinates using clustering

        Args:
            x_coords: List of X-coordinates

        Returns:
            List of column boundary X-coordinates
        """
        if not x_coords:
            return []

        # Use simple histogram-based approach
        # Group X-coordinates into bins and find peaks
        import numpy as np

        x_array = np.array(x_coords)
        # Create histogram with 20 bins
        hist, bin_edges = np.histogram(x_array, bins=20)

        # Find peaks (local maxima) in histogram
        peaks = []
        for i in range(1, len(hist) - 1):
            if hist[i] > hist[i - 1] and hist[i] > hist[i + 1] and hist[i] > 5:
                # Peak found, use bin center as column boundary
                peak_x = (bin_edges[i] + bin_edges[i + 1]) / 2
                peaks.append(peak_x)

        return sorted(peaks)

    def _get_column_index(self, x: float, column_boundaries: List[float]) -> int:
        """
        Get column index for a given X-coordinate

        Args:
            x: X-coordinate
            column_boundaries: List of column boundaries

        Returns:
            Column index (0-based)
        """
        if not column_boundaries:
            return 0

        for i, boundary in enumerate(column_boundaries):
            if x < boundary:
                return i

        return len(column_boundaries)

    def _detect_line_groups(self, words: List[Dict]) -> List[List[int]]:
        """
        Detect line groups for text wrapping detection
        Groups consecutive lines that are likely part of the same logical line

        Args:
            words: List of word dictionaries

        Returns:
            List of line groups, where each group is a list of word indices
        """
        if not words:
            return []

        # Group words by Y-coordinate (same line)
        lines = {}
        for i, word in enumerate(words):
            y = round(word.get("top", 0), 1)
            if y not in lines:
                lines[y] = []
            lines[y].append(i)

        # Sort lines by Y-coordinate
        sorted_y = sorted(lines.keys())

        # Group consecutive lines that are close together (likely wrapped text)
        line_groups = []
        current_group = []
        prev_y = None

        for y in sorted_y:
            if prev_y is None:
                current_group = lines[y]
            else:
                # If lines are close (< 20 pixels apart), they're likely part of same group
                if y - prev_y < 20:
                    current_group.extend(lines[y])
                else:
                    # Start new group
                    if current_group:
                        line_groups.append(current_group)
                    current_group = lines[y]

            prev_y = y

        # Add last group
        if current_group:
            line_groups.append(current_group)

        return line_groups

    def _get_line_group_index(self, word_idx: int, line_groups: List[List[int]]) -> int:
        """
        Get line group index for a given word index

        Args:
            word_idx: Word index
            line_groups: List of line groups

        Returns:
            Line group index (0-based), or -1 if not found
        """
        for i, group in enumerate(line_groups):
            if word_idx in group:
                return i
        return -1

    def _is_first_line_in_group(
        self, word_idx: int, line_groups: List[List[int]]
    ) -> bool:
        """
        Check if word is on the first line of its group

        Args:
            word_idx: Word index
            line_groups: List of line groups

        Returns:
            True if word is on first line of group
        """
        for group in line_groups:
            if word_idx in group:
                return word_idx == group[0] or word_idx in group[:5]  # First 5 words
        return False

    def _is_continuation_line(
        self, word_idx: int, line_groups: List[List[int]]
    ) -> bool:
        """
        Check if word is on a continuation line (wrapped text)

        Args:
            word_idx: Word index
            line_groups: List of line groups

        Returns:
            True if word is on a continuation line
        """
        for group in line_groups:
            if word_idx in group:
                return word_idx not in group[:5]  # Not in first 5 words
        return False
