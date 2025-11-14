"""
Performance Metrics Service
Tracks and analyzes system performance over time
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import json
from database.repositories.document_repository import DocumentRepository
from database.repositories.feedback_repository import FeedbackRepository
from database.db_manager import DatabaseManager
from database.repositories.strategy_performance_repository import (
    StrategyPerformanceRepository,
)
import logging


class PerformanceMetrics:
    """Service for tracking and analyzing performance metrics"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.document_repository = DocumentRepository(db_manager)
        self.feedback_repository = FeedbackRepository(db_manager)
        self.strategy_performance_repository = StrategyPerformanceRepository(db_manager)
        self.logger = logging.getLogger(__name__)

    def get_template_metrics(self, template_id: int) -> Dict[str, Any]:
        """
        Get comprehensive metrics for a template

        Returns:
            Dictionary with metrics including:
            - Overall accuracy
            - Field-level performance
            - Strategy distribution
            - Improvement over time
        """
        # conn = self.db.get_connection()
        # cursor = conn.cursor()

        # Get all documents for this template

        documents = self.document_repository.find_by_template_id(template_id)

        # cursor.execute('''
        #     SELECT
        #         id,
        #         extraction_result,
        #         status,
        #         created_at
        #     FROM documents
        #     WHERE template_id = ?
        #     ORDER BY created_at ASC
        # ''', (template_id,))

        # documents = cursor.fetchall()

        feedbacks = self.feedback_repository.find_by_template_id(template_id)

        # Get all feedback for this template
        # cursor.execute('''
        #     SELECT
        #         f.document_id,
        #         f.field_name,
        #         f.original_value,
        #         f.corrected_value,
        #         f.confidence_score,
        #         f.created_at
        #     FROM feedback f
        #     JOIN documents d ON f.document_id = d.id
        #     WHERE d.template_id = ?
        #     ORDER BY f.created_at ASC
        # ''', (template_id,))

        # feedbacks = cursor.fetchall()
        # conn.close()

        # Calculate metrics
        metrics = {
            "overview": self._calculate_overview(documents, feedbacks),
            "field_performance": self._calculate_field_performance(
                documents, feedbacks
            ),  # ✅ FIXED: Pass documents
            "field_metrics_detailed": self._calculate_field_metrics_detailed(
                documents, feedbacks
            ),  # ✅ NEW: Precision, Recall, F1
            "strategy_distribution": self._calculate_strategy_distribution(documents),
            "strategy_performance": self._calculate_strategy_performance(template_id),
            "accuracy_over_time": self._calculate_accuracy_over_time(
                documents, feedbacks
            ),
            "feedback_stats": self._calculate_feedback_stats(feedbacks),
            "learning_progress": self._calculate_learning_progress(
                documents, feedbacks
            ),  # ✅ NEW
            "confidence_trends": self._calculate_confidence_trends(documents),  # ✅ NEW
            "error_patterns": self._calculate_error_patterns(feedbacks),  # ✅ NEW
            "performance_stats": self._calculate_performance_stats(
                documents
            ),  # ✅ NEW: Extraction time
            "ablation_study": self._calculate_ablation_study(
                documents, feedbacks
            ),  # ✅ NEW: Strategy comparison
            "time_trends": self._calculate_time_trends(documents),  # ✅ NEW: Time trends
            
            # ✅ PHASE 1: Critical metrics for thesis
            "hitl_metrics": self._calculate_hitl_metrics(documents, feedbacks, template_id),  # Human-in-the-Loop
            "adaptive_learning_status": self._calculate_adaptive_learning_status(template_id),  # Pattern learning
            "incremental_learning": self._calculate_incremental_learning(documents, feedbacks),  # Batch progress
            "baseline_comparison": self._calculate_baseline_comparison(documents, feedbacks),  # vs Baseline
        }

        return metrics

    def _calculate_overview(self, documents: List, feedbacks: List) -> Dict[str, Any]:
        """Calculate overall metrics"""
        total_docs = len(documents)
        validated_docs = sum(1 for d in documents if d["status"] == "validated")
        total_corrections = len(feedbacks)

        # Calculate overall accuracy
        if total_docs > 0 and feedbacks:
            # Group feedback by document
            feedback_by_doc = defaultdict(list)
            for fb in feedbacks:
                feedback_by_doc[fb["document_id"]].append(fb)

            # Calculate accuracy per document
            accuracies = []
            for doc in documents:
                doc_feedbacks = feedback_by_doc.get(doc["id"], [])
                if doc_feedbacks:
                    # Parse extraction result
                    try:
                        result = json.loads(doc["extraction_result"])
                        total_fields = len(result.get("extracted_data", {}))
                        incorrect_fields = len(doc_feedbacks)
                        correct_fields = max(0, total_fields - incorrect_fields)

                        if total_fields > 0:
                            accuracy = correct_fields / total_fields
                            accuracies.append(accuracy)
                    except:
                        pass

            overall_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0.0
        else:
            overall_accuracy = 0.0

        return {
            "total_documents": total_docs,
            "validated_documents": validated_docs,
            "total_corrections": total_corrections,
            "overall_accuracy": round(overall_accuracy, 3),
            "validation_rate": (
                round(validated_docs / total_docs, 3) if total_docs > 0 else 0.0
            ),
        }

    def _calculate_field_performance(
        self, documents: List, feedbacks: List
    ) -> Dict[str, Any]:
        """
        Calculate per-field performance metrics
        Uses ALL extractions from documents, not just feedbacks
        """
        field_stats = defaultdict(
            lambda: {
                "total_extractions": 0,
                "correct_extractions": 0,
                "corrections": 0,
                "avg_confidence": [],
                "crf": 0,
                "rule_based": 0,
                "position_based": 0,
                "all_strategies_attempted": {
                    "crf": 0,
                    "rule_based": 0,
                    "position_based": 0,
                },
            }
        )

        # First, count ALL extractions from documents
        for doc in documents:
            if doc["extraction_result"]:
                try:
                    result = json.loads(doc["extraction_result"])
                    extracted_data = result.get("extracted_data", {})
                    confidences = result.get("confidence_scores", {})
                    extraction_method = result.get("extraction_methods", {})
                    strategies_used = result.get("metadata", {}).get("strategies_used", [])

                    for field_name, value in extracted_data.items():
                        if value:  # Only count non-empty extractions
                            field_stats[field_name]["total_extractions"] += 1

                            # Track strategies used
                            # search where strategies_used.field_name == field_name
                            # strategies_used = next(
                            #     (item["all_strategies_attempted"] for item in strategies_used if item.get("field_name") == field_name),
                            #     [] # Default value if no match is found
                            # )

                            for item in strategies_used:
                                if item.get("field_name") == field_name:
                                    for strategy in item.get("all_strategies_attempted", []):
                                        field_stats[field_name]["all_strategies_attempted"][strategy] += 1
                                    
                            
                            # Track confidence
                            if (
                                field_name in confidences
                                and confidences[field_name] is not None
                            ):
                                field_stats[field_name]["avg_confidence"].append(
                                    confidences[field_name]
                                )

                            # Track extraction method
                            if (
                                field_name in extraction_method
                                and extraction_method[field_name] == "crf"
                            ):
                                field_stats[field_name]["crf"] += 1
                            elif (
                                field_name in extraction_method
                                and extraction_method[field_name] == "rule_based"
                            ):
                                field_stats[field_name]["rule_based"] += 1
                            elif (
                                field_name in extraction_method
                                and extraction_method[field_name] == "position_based"
                            ):
                                field_stats[field_name]["position_based"] += 1
                            

                except:
                    pass

        # Then, count corrections from feedbacks
        for fb in feedbacks:
            field_name = fb["field_name"]

            # ✅ Normalize whitespace for comparison (same as hybrid_strategy.py)
            original_normalized = " ".join(str(fb["original_value"]).split())
            corrected_normalized = " ".join(str(fb["corrected_value"]).split())

            # Count as correction if values differ (after normalization)
            if original_normalized != corrected_normalized:
                field_stats[field_name]["corrections"] += 1

        # Calculate accuracy per field
        result = {}
        for field_name, stats in field_stats.items():
            total = stats["total_extractions"]
            corrections = stats["corrections"]
            correct = total - corrections
            accuracy = correct / total if total > 0 else 0.0

            avg_conf = (
                sum(stats["avg_confidence"]) / len(stats["avg_confidence"])
                if stats["avg_confidence"]
                else 0.0
            )

            result[field_name] = {
                "accuracy": round(accuracy, 3),
                "total_extractions": total,
                "correct_extractions": correct,
                "corrections": corrections,
                "avg_confidence": round(avg_conf, 3),
                "crf": stats["crf"],
                "rule_based": stats["rule_based"],
                "position_based": stats["position_based"],
                "all_strategies_attempted": stats["all_strategies_attempted"],
            }

        return result

    def _calculate_field_metrics_detailed(
        self, documents: List, feedbacks: List
    ) -> Dict[str, Any]:
        """
        Calculate Precision, Recall, F1-Score per field

        Definitions for our context:
        - TP (True Positive): Field extracted correctly (no correction needed)
        - FP (False Positive): Field extracted incorrectly (correction provided)
        - FN (False Negative): Field not extracted (empty/null) but should have value

        Note: We don't use TN (True Negative) because all fields must be extracted
        """
        field_stats = defaultdict(
            lambda: {
                "tp": 0,  # Correct extractions
                "fp": 0,  # Incorrect extractions (with corrections)
                "fn": 0,  # Missing extractions (empty but should have value)
            }
        )

        # Count TP and FN from documents
        for doc in documents:
            if doc["extraction_result"]:
                try:
                    result = json.loads(doc["extraction_result"])
                    extracted_data = result.get("extracted_data", {})

                    for field_name, value in extracted_data.items():
                        if value and str(value).strip():  # Has value
                            field_stats[field_name][
                                "tp"
                            ] += 1  # Assume correct initially
                        else:  # Empty/null
                            field_stats[field_name]["fn"] += 1  # Missing extraction
                except:
                    pass

        # Adjust TP/FP based on corrections
        for fb in feedbacks:
            field_name = fb["field_name"]

            # Normalize for comparison
            original = " ".join(str(fb["original_value"]).split())
            corrected = " ".join(str(fb["corrected_value"]).split())

            if original != corrected:
                # Was counted as TP, but actually FP
                if field_stats[field_name]["tp"] > 0:
                    field_stats[field_name]["tp"] -= 1
                field_stats[field_name]["fp"] += 1

        # Calculate metrics
        result = {}
        for field_name, stats in field_stats.items():
            tp = stats["tp"]
            fp = stats["fp"]
            fn = stats["fn"]

            # Precision: Of all extracted values, how many are correct?
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0

            # Recall: Of all values that should be extracted, how many are?
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0

            # F1-Score: Harmonic mean of precision and recall
            f1_score = (
                2 * (precision * recall) / (precision + recall)
                if (precision + recall) > 0
                else 0.0
            )

            result[field_name] = {
                "precision": round(precision, 3),
                "recall": round(recall, 3),
                "f1_score": round(f1_score, 3),
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "support": tp + fn,  # Total instances that should be extracted
            }

        return result

    def _calculate_strategy_distribution(self, documents: List) -> Dict[str, int]:
        """Calculate distribution of extraction strategies"""
        strategy_counts = defaultdict(int)

        for doc in documents:
            try:
                result = json.loads(doc["extraction_result"])
                methods = result.get("extraction_methods", {})

                for field_name, method in methods.items():
                    strategy_counts[method] += 1
            except:
                pass

        return dict(strategy_counts)

    def _calculate_strategy_performance(self, template_id: int) -> Dict[str, Any]:
        """
        Calculate performance metrics for each extraction strategy
        Uses the strategy_performance table that tracks ALL strategies (not just selected ones)
        """
        # conn = self.db.get_connection()
        # cursor = conn.cursor()

        # # Get strategy performance from database
        # cursor.execute(
        #     """
        #     SELECT
        #         strategy_type,
        #         field_name,
        #         accuracy,
        #         total_extractions,
        #         correct_extractions,
        #         last_updated
        #     FROM strategy_performance
        #     WHERE template_id = ?
        #     ORDER BY strategy_type, field_name
        # """,
        #     (template_id,),
        # )

        # rows = cursor.fetchall()
        # conn.close()
        rows = self.strategy_performance_repository.get_template_performance(
            template_id
        )

        # Group by strategy
        strategy_stats = defaultdict(
            lambda: {
                "total_attempts": 0,
                "total_correct": 0,
                "fields": {},
                "overall_accuracy": 0.0,
            }
        )

        for row in rows:
            strategy = row["strategy_type"]
            field = row["field_name"]
            accuracy = row["accuracy"]
            total = row["total_extractions"]
            correct = row["correct_extractions"]

            # Add to strategy totals
            strategy_stats[strategy]["total_attempts"] += total
            strategy_stats[strategy]["total_correct"] += correct

            # Add field-level stats
            strategy_stats[strategy]["fields"][field] = {
                "accuracy": round(accuracy, 3),
                "total": total,
                "correct": correct,
            }

        # Calculate overall accuracy per strategy
        result = {}
        for strategy, stats in strategy_stats.items():
            overall_acc = (
                stats["total_correct"] / stats["total_attempts"]
                if stats["total_attempts"] > 0
                else 0.0
            )

            result[strategy] = {
                "overall_accuracy": round(overall_acc, 3),
                "total_attempts": stats["total_attempts"],
                "total_correct": stats["total_correct"],
                "fields": stats["fields"],
            }

        return result

    def _calculate_accuracy_over_time(
        self, documents: List, feedbacks: List
    ) -> List[Dict[str, Any]]:
        """Calculate accuracy improvement over time"""
        if not documents:
            return []

        # Group feedback by document
        feedback_by_doc = defaultdict(list)
        for fb in feedbacks:
            feedback_by_doc[fb["document_id"]].append(fb)

        # Calculate accuracy for each document
        timeline = []
        for doc in documents:
            doc_feedbacks = feedback_by_doc.get(doc["id"], [])

            try:
                result = json.loads(doc["extraction_result"])
                total_fields = len(result.get("extracted_data", {}))
                incorrect_fields = len(doc_feedbacks)
                correct_fields = max(0, total_fields - incorrect_fields)

                if total_fields > 0:
                    accuracy = correct_fields / total_fields

                    timeline.append(
                        {
                            "timestamp": doc["created_at"],
                            "accuracy": round(accuracy, 3),
                            "document_id": doc["id"],
                            "total_fields": total_fields,
                            "correct_fields": correct_fields,
                        }
                    )
            except:
                pass

        return timeline

    def _calculate_feedback_stats(self, feedbacks: List) -> Dict[str, Any]:
        """Calculate feedback statistics"""
        if not feedbacks:
            return {"total_feedback": 0, "feedback_by_field": {}, "recent_feedback": []}

        # Group by field
        by_field = defaultdict(int)
        for fb in feedbacks:
            by_field[fb["field_name"]] += 1

        # Get recent feedback (last 10)
        recent = []
        for fb in sorted(feedbacks, key=lambda x: x["created_at"], reverse=True)[:10]:
            recent.append(
                {
                    "field_name": fb["field_name"],
                    "original_value": fb["original_value"],
                    "corrected_value": fb["corrected_value"],
                    "timestamp": fb["created_at"],
                }
            )

        return {
            "total_feedback": len(feedbacks),
            "feedback_by_field": dict(by_field),
            "recent_feedback": recent,
        }

    def _calculate_learning_progress(
        self, documents: List, feedbacks: List, batch_size: int = 5
    ) -> Dict[str, Any]:
        """
        Calculate learning progress over batches of documents
        Shows how accuracy improves as model learns from feedback
        
        Uses larger batch size and moving average for stability
        """
        if not documents:
            return {
                "batches": [],
                "improvement_rate": 0.0,
                "first_batch_accuracy": 0.0,
                "last_batch_accuracy": 0.0,
            }

        # Group feedback by document and field
        feedback_by_doc = defaultdict(list)
        feedback_by_field = defaultdict(int)
        for fb in feedbacks:
            feedback_by_doc[fb["document_id"]].append(fb)
            feedback_by_field[fb["field_name"]] += 1

        # Calculate accuracy per batch with field-level tracking
        batches = []
        field_accuracy_by_batch = defaultdict(lambda: defaultdict(lambda: {"correct": 0, "total": 0}))
        
        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i : i + batch_size]
            total_fields = 0
            correct_fields = 0
            field_stats = defaultdict(lambda: {"correct": 0, "total": 0})

            for doc in batch_docs:
                try:
                    result = json.loads(doc["extraction_result"])
                    extracted = result.get("extracted_data", {})
                    doc_feedbacks = feedback_by_doc.get(doc["id"], [])
                    
                    # Track per-field accuracy
                    feedback_fields = {fb["field_name"] for fb in doc_feedbacks}
                    
                    for field_name, value in extracted.items():
                        if value:  # Only count non-empty fields
                            field_stats[field_name]["total"] += 1
                            total_fields += 1
                            
                            if field_name not in feedback_fields:
                                field_stats[field_name]["correct"] += 1
                                correct_fields += 1
                except:
                    pass
            
            # Store field stats for this batch
            batch_num = len(batches) + 1
            for field_name, stats in field_stats.items():
                field_accuracy_by_batch[batch_num][field_name] = stats

            if total_fields > 0:
                accuracy = correct_fields / total_fields
                batches.append(
                    {
                        "batch_number": batch_num,
                        "start_doc": i + 1,
                        "end_doc": min(i + batch_size, len(documents)),
                        "accuracy": round(accuracy, 3),
                        "total_fields": total_fields,
                        "correct_fields": correct_fields,
                    }
                )

        # Apply moving average smoothing (window=3) for stability
        smoothed_batches = []
        window_size = 3
        for i, batch in enumerate(batches):
            # Calculate moving average
            start_idx = max(0, i - window_size + 1)
            window = batches[start_idx:i+1]
            avg_accuracy = sum(b["accuracy"] for b in window) / len(window)
            
            smoothed_batch = batch.copy()
            smoothed_batch["raw_accuracy"] = batch["accuracy"]
            smoothed_batch["accuracy"] = round(avg_accuracy, 3)
            smoothed_batches.append(smoothed_batch)
        
        # Calculate improvement rate (using smoothed values)
        if len(smoothed_batches) >= 2:
            first_acc = smoothed_batches[0]["accuracy"]
            last_acc = smoothed_batches[-1]["accuracy"]
            improvement = (
                ((last_acc - first_acc) / first_acc * 100) if first_acc > 0 else 0
            )
        else:
            first_acc = smoothed_batches[0]["accuracy"] if smoothed_batches else 0.0
            last_acc = first_acc
            improvement = 0.0
        
        # Calculate variance/stability metric
        if len(smoothed_batches) >= 2:
            accuracies = [b["accuracy"] for b in smoothed_batches]
            avg_acc = sum(accuracies) / len(accuracies)
            variance = sum((x - avg_acc) ** 2 for x in accuracies) / len(accuracies)
            stability_score = max(0, 1 - (variance ** 0.5))  # Higher = more stable
        else:
            stability_score = 1.0
        
        # Identify problematic fields (high error rate)
        problematic_fields = []
        if feedback_by_field:
            total_feedbacks = len(feedbacks)
            for field_name, error_count in sorted(feedback_by_field.items(), key=lambda x: x[1], reverse=True):
                error_rate = error_count / total_feedbacks
                if error_rate > 0.1:  # More than 10% of all errors
                    problematic_fields.append({
                        "field_name": field_name,
                        "error_count": error_count,
                        "error_rate": round(error_rate, 3)
                    })

        return {
            "batches": smoothed_batches,
            "improvement_rate": round(improvement, 2),
            "first_batch_accuracy": round(first_acc, 3),
            "last_batch_accuracy": round(last_acc, 3),
            "total_batches": len(smoothed_batches),
            "stability_score": round(stability_score, 3),
            "problematic_fields": problematic_fields[:5],  # Top 5
        }

    def _calculate_confidence_trends(self, documents: List) -> Dict[str, Any]:
        """
        Calculate confidence score trends over time
        Shows how confident the model is becoming
        """
        if not documents:
            return {"overall_trend": [], "by_strategy": {}, "avg_confidence": 0.0}

        # Overall confidence over time
        overall_trend = []
        strategy_confidences = defaultdict(list)
        all_confidences = []

        for doc in documents:
            try:
                result = json.loads(doc["extraction_result"])
                confidences = result.get("confidence_scores", {})
                methods = result.get("extraction_methods", {})

                if confidences:
                    avg_conf = sum(confidences.values()) / len(confidences)
                    overall_trend.append(
                        {
                            "timestamp": doc["created_at"],
                            "avg_confidence": round(avg_conf, 3),
                            "document_id": doc["id"],
                        }
                    )
                    all_confidences.append(avg_conf)

                    # Track by strategy
                    for field, method in methods.items():
                        if field in confidences:
                            strategy_confidences[method].append(confidences[field])
            except:
                pass

        # Calculate average confidence per strategy
        by_strategy = {}
        for strategy, confs in strategy_confidences.items():
            if confs:
                by_strategy[strategy] = {
                    "avg_confidence": round(sum(confs) / len(confs), 3),
                    "min_confidence": round(min(confs), 3),
                    "max_confidence": round(max(confs), 3),
                    "sample_count": len(confs),
                }

        return {
            "overall_trend": overall_trend[-100:],  # Last 100 documents
            "by_strategy": by_strategy,
            "avg_confidence": (
                round(sum(all_confidences) / len(all_confidences), 3)
                if all_confidences
                else 0.0
            ),
        }

    def _calculate_error_patterns(self, feedbacks: List) -> Dict[str, Any]:
        """
        Analyze error patterns to identify problematic fields
        Helps prioritize which fields need improvement
        """
        if not feedbacks:
            return {
                "most_problematic_fields": [],
                "error_frequency": {},
                "common_mistakes": [],
            }

        # Count errors per field
        error_counts = defaultdict(int)
        field_examples = defaultdict(list)

        for fb in feedbacks:
            # Normalize values
            original = " ".join(str(fb["original_value"]).split())
            corrected = " ".join(str(fb["corrected_value"]).split())

            # Only count actual corrections
            if original != corrected:
                field_name = fb["field_name"]
                error_counts[field_name] += 1

                # Store example (limit to 3 per field)
                if len(field_examples[field_name]) < 3:
                    field_examples[field_name].append(
                        {
                            "original": original[:50],  # Truncate long values
                            "corrected": corrected[:50],
                            "timestamp": fb["created_at"],
                        }
                    )

        # Sort fields by error count
        most_problematic = sorted(
            error_counts.items(), key=lambda x: x[1], reverse=True
        )[:10]

        problematic_fields = []
        for field, count in most_problematic:
            problematic_fields.append(
                {
                    "field_name": field,
                    "error_count": count,
                    "examples": field_examples[field],
                }
            )

        return {
            "most_problematic_fields": problematic_fields,
            "error_frequency": dict(error_counts),
            "total_unique_errors": len(error_counts),
        }

    def should_request_validation(
        self, extraction_result: Dict[str, Any], threshold: float = 0.7
    ) -> tuple[bool, str]:
        """
        Active Learning: Determine if document needs validation

        Args:
            extraction_result: Extraction result dictionary
            threshold: Confidence threshold for auto-accept

        Returns:
            (should_validate, reason)
        """
        confidence_scores = extraction_result.get("confidence_scores", {})

        if not confidence_scores:
            return True, "No confidence scores available"

        # Calculate average confidence
        avg_confidence = sum(confidence_scores.values()) / len(confidence_scores)

        # Check for low confidence
        if avg_confidence < threshold:
            return True, f"Low average confidence ({avg_confidence:.2f} < {threshold})"

        # Check for any very low confidence fields
        min_confidence = min(confidence_scores.values())
        if min_confidence < 0.5:
            low_fields = [
                field for field, conf in confidence_scores.items() if conf < 0.5
            ]
            return True, f"Very low confidence in fields: {', '.join(low_fields)}"

        # Check for strategy diversity (if all same strategy, might be template issue)
        methods = extraction_result.get("extraction_methods", {})
        unique_methods = set(methods.values())

        if len(unique_methods) == 1 and "rule-based" in unique_methods:
            return True, "All fields extracted by rule-based (template may need review)"

        # High confidence - can auto-accept
        return False, f"High confidence ({avg_confidence:.2f})"

    def _calculate_performance_stats(self, documents: List) -> Dict[str, Any]:
        """
        Calculate extraction time statistics

        Returns:
            Dictionary with time statistics in milliseconds
        """
        times = []
        times_by_strategy = defaultdict(list)

        for doc in documents:
            # Get extraction time from document
            try:
                extraction_time = (
                    doc["extraction_time_ms"]
                    if "extraction_time_ms" in doc.keys()
                    else 0
                )
            except (KeyError, AttributeError):
                extraction_time = 0

            if extraction_time > 0:
                times.append(extraction_time)

                # Get extraction methods to categorize by strategy
                if doc["extraction_result"]:
                    try:
                        result = json.loads(doc["extraction_result"])
                        methods = result.get("extraction_methods", {})

                        # Categorize by dominant strategy
                        strategy_counts = defaultdict(int)
                        for method in methods.values():
                            strategy_counts[method] += 1

                        if strategy_counts:
                            dominant_strategy = max(
                                strategy_counts.items(), key=lambda x: x[1]
                            )[0]
                            times_by_strategy[dominant_strategy].append(extraction_time)
                    except:
                        pass

        if not times:
            return {
                "avg_time_ms": 0,
                "min_time_ms": 0,
                "max_time_ms": 0,
                "total_time_sec": 0,
                "documents_timed": 0,
                "by_strategy": {},
            }

        # Calculate overall stats
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        total_time_sec = sum(times) / 1000

        # Calculate per-strategy stats
        strategy_stats = {}
        for strategy, strategy_times in times_by_strategy.items():
            if strategy_times:
                strategy_stats[strategy] = {
                    "avg_time_ms": round(sum(strategy_times) / len(strategy_times), 2),
                    "min_time_ms": min(strategy_times),
                    "max_time_ms": max(strategy_times),
                    "count": len(strategy_times),
                }

        return {
            "avg_time_ms": round(avg_time, 2),
            "min_time_ms": min_time,
            "max_time_ms": max_time,
            "total_time_sec": round(total_time_sec, 2),
            "documents_timed": len(times),
            "by_strategy": strategy_stats,
        }

    def _calculate_ablation_study(
        self, documents: List, feedbacks: List
    ) -> Dict[str, Any]:
        """
        Calculate ablation study - compare performance of different strategies
        
        Simulates what accuracy would be if we used ONLY one strategy
        vs the hybrid approach
        
        Returns:
            Dictionary with strategy comparisons
        """
        if not documents:
            return {
                "strategies": [],
                "hybrid_accuracy": 0.0,
                "best_single_strategy": None,
                "improvement_over_best": 0.0,
            }

        # Group feedback by document
        feedback_by_doc = defaultdict(list)
        for fb in feedbacks:
            feedback_by_doc[fb["document_id"]].append(fb)

        # Calculate accuracy for each strategy independently
        strategy_accuracies = defaultdict(lambda: {"correct": 0, "total": 0})
        hybrid_correct = 0
        hybrid_total = 0

        for doc in documents:
            if not doc["extraction_result"]:
                continue

            try:
                result = json.loads(doc["extraction_result"])
                extracted_data = result.get("extracted_data", {})
                extraction_methods = result.get("extraction_methods", {})
                
                # Get metadata with all strategies attempted
                metadata = result.get("metadata", {})
                strategies_used = metadata.get("strategies_used", [])

                doc_feedbacks = feedback_by_doc.get(doc["id"], [])
                corrections = {fb["field_name"]: fb["corrected_value"] for fb in doc_feedbacks}

                # For each field, check accuracy
                for field_name, extracted_value in extracted_data.items():
                    # Determine ground truth
                    if field_name in corrections:
                        ground_truth = corrections[field_name]
                    else:
                        ground_truth = extracted_value  # No correction = correct

                    # Normalize for comparison
                    extracted_norm = " ".join(str(extracted_value).split())
                    truth_norm = " ".join(str(ground_truth).split())
                    is_correct = extracted_norm == truth_norm

                    # Hybrid accuracy (what was actually selected)
                    hybrid_total += 1
                    if is_correct:
                        hybrid_correct += 1

                    # Find all strategies attempted for this field
                    field_strategies = {}
                    for strategy_info in strategies_used:
                        if strategy_info.get("field_name") == field_name:
                            all_attempted = strategy_info.get("all_strategies_attempted", {})
                            field_strategies = all_attempted
                            break

                    # For each strategy, check if it would have been correct
                    for strategy_name, strategy_result in field_strategies.items():
                        if strategy_result.get("success"):
                            strategy_value = strategy_result.get("value", "")
                            strategy_norm = " ".join(str(strategy_value).split())
                            strategy_correct = strategy_norm == truth_norm

                            strategy_accuracies[strategy_name]["total"] += 1
                            if strategy_correct:
                                strategy_accuracies[strategy_name]["correct"] += 1

            except Exception as e:
                continue

        # Calculate final accuracies
        hybrid_accuracy = hybrid_correct / hybrid_total if hybrid_total > 0 else 0.0

        strategies_comparison = []
        best_single_accuracy = 0.0
        best_single_strategy = None

        for strategy, stats in strategy_accuracies.items():
            if stats["total"] > 0:
                accuracy = stats["correct"] / stats["total"]
                strategies_comparison.append(
                    {
                        "strategy": strategy,
                        "accuracy": round(accuracy, 4),
                        "correct": stats["correct"],
                        "total": stats["total"],
                        "coverage": round(stats["total"] / hybrid_total, 4)
                        if hybrid_total > 0
                        else 0.0,
                    }
                )

                if accuracy > best_single_accuracy:
                    best_single_accuracy = accuracy
                    best_single_strategy = strategy

        # Sort by accuracy descending
        strategies_comparison.sort(key=lambda x: x["accuracy"], reverse=True)

        improvement = (
            ((hybrid_accuracy - best_single_accuracy) / best_single_accuracy * 100)
            if best_single_accuracy > 0
            else 0.0
        )

        return {
            "strategies": strategies_comparison,
            "hybrid_accuracy": round(hybrid_accuracy, 4),
            "hybrid_correct": hybrid_correct,
            "hybrid_total": hybrid_total,
            "best_single_strategy": best_single_strategy,
            "best_single_accuracy": round(best_single_accuracy, 4),
            "improvement_over_best": round(improvement, 2),
        }

    def _calculate_time_trends(self, documents: List) -> Dict[str, Any]:
        """
        Calculate extraction time trends over time
        
        Shows how extraction speed changes as more documents are processed
        (useful for detecting performance degradation or improvement)
        
        Returns:
            Dictionary with time trend data
        """
        if not documents:
            return {
                "trend_data": [],
                "avg_time_first_10": 0.0,
                "avg_time_last_10": 0.0,
                "performance_change": 0.0,
                "total_documents": 0,
            }

        # Collect time data with timestamps
        time_data = []
        for doc in documents:
            try:
                extraction_time = (
                    doc["extraction_time_ms"]
                    if "extraction_time_ms" in doc.keys()
                    else 0
                )
            except (KeyError, AttributeError):
                extraction_time = 0

            if extraction_time > 0:
                time_data.append(
                    {
                        "document_id": doc["id"],
                        "timestamp": doc["created_at"],
                        "extraction_time_ms": extraction_time,
                    }
                )

        if not time_data:
            return {
                "trend_data": [],
                "avg_time_first_10": 0.0,
                "avg_time_last_10": 0.0,
                "performance_change": 0.0,
                "total_documents": 0,
            }

        # Sort by timestamp
        time_data.sort(key=lambda x: x["timestamp"])

        # Calculate moving average (window size = 5)
        window_size = 5
        trend_with_ma = []
        for i, data_point in enumerate(time_data):
            # Calculate moving average
            start_idx = max(0, i - window_size + 1)
            window = time_data[start_idx : i + 1]
            ma = sum(d["extraction_time_ms"] for d in window) / len(window)

            trend_with_ma.append(
                {
                    "document_id": data_point["document_id"],
                    "timestamp": data_point["timestamp"],
                    "extraction_time_ms": data_point["extraction_time_ms"],
                    "moving_average": round(ma, 2),
                    "document_number": i + 1,
                }
            )

        # Calculate first 10 vs last 10 average
        first_10 = [d["extraction_time_ms"] for d in time_data[:10]]
        last_10 = [d["extraction_time_ms"] for d in time_data[-10:]]

        avg_first_10 = sum(first_10) / len(first_10) if first_10 else 0.0
        avg_last_10 = sum(last_10) / len(last_10) if last_10 else 0.0

        # Calculate performance change (negative = faster, positive = slower)
        performance_change = (
            ((avg_last_10 - avg_first_10) / avg_first_10 * 100)
            if avg_first_10 > 0
            else 0.0
        )

        return {
            "trend_data": trend_with_ma,
            "avg_time_first_10": round(avg_first_10, 2),
            "avg_time_last_10": round(avg_last_10, 2),
            "performance_change": round(performance_change, 2),
            "total_documents": len(time_data),
        }
    
    def _calculate_hitl_metrics(self, documents: List, feedbacks: List, template_id: int) -> Dict[str, Any]:
        """
        Calculate Human-in-the-Loop metrics
        Measures feedback quality, human effort, and learning efficiency
        """
        if not feedbacks:
            return {
                "feedback_quality": {
                    "avg_feedback_per_document": 0.0,
                    "feedback_acceptance_rate": 0.0,
                    "quality_score": 0.0
                },
                "human_effort": {
                    "total_corrections": 0,
                    "avg_corrections_per_document": 0.0,
                    "corrections_by_field": {}
                },
                "learning_efficiency": {
                    "feedback_to_improvement_ratio": 0.0,
                    "convergence_speed": 0.0
                }
            }
        
        # Feedback Quality
        feedback_by_doc = defaultdict(list)
        for fb in feedbacks:
            feedback_by_doc[fb["document_id"]].append(fb)
        
        avg_feedback_per_doc = len(feedbacks) / len(documents) if documents else 0.0
        
        # Corrections by field
        corrections_by_field = defaultdict(int)
        for fb in feedbacks:
            corrections_by_field[fb["field_name"]] += 1
        
        # Learning Efficiency: Calculate accuracy improvement per feedback
        if len(documents) >= 2:
            # Split into batches
            batch_size = 5
            batches = [documents[i:i+batch_size] for i in range(0, len(documents), batch_size)]
            
            improvements = []
            for i in range(1, len(batches)):
                prev_batch = batches[i-1]
                curr_batch = batches[i]
                
                # Calculate accuracy for each batch
                prev_acc = self._calculate_batch_accuracy(prev_batch, feedbacks)
                curr_acc = self._calculate_batch_accuracy(curr_batch, feedbacks)
                
                if prev_acc > 0:
                    improvement = curr_acc - prev_acc
                    improvements.append(improvement)
            
            avg_improvement = sum(improvements) / len(improvements) if improvements else 0.0
            feedback_count = len([fb for fb in feedbacks if fb["document_id"] in [d["id"] for d in documents[:len(batches)*batch_size]]])
            
            feedback_to_improvement = (avg_improvement / feedback_count * 100) if feedback_count > 0 else 0.0
        else:
            feedback_to_improvement = 0.0
        
        return {
            "feedback_quality": {
                "avg_feedback_per_document": round(avg_feedback_per_doc, 2),
                "total_feedback": len(feedbacks),
                "documents_with_feedback": len(feedback_by_doc),
                "quality_score": round(min(1.0, 1.0 / (avg_feedback_per_doc + 1)), 2)  # Lower feedback = higher quality
            },
            "human_effort": {
                "total_corrections": len(feedbacks),
                "avg_corrections_per_document": round(avg_feedback_per_doc, 2),
                "corrections_by_field": dict(sorted(corrections_by_field.items(), key=lambda x: x[1], reverse=True)[:10])
            },
            "learning_efficiency": {
                "feedback_to_improvement_ratio": round(feedback_to_improvement, 4),
                "total_batches": len(documents) // 5,
                "avg_improvement_per_batch": round(avg_improvement if 'avg_improvement' in locals() else 0.0, 4)
            }
        }
    
    def _calculate_adaptive_learning_status(self, template_id: int) -> Dict[str, Any]:
        """
        Calculate adaptive learning mechanism status
        Tracks pattern learning, auto-training, and confidence adjustment
        """
        try:
            # Get learned patterns with field_name from field_configs
            patterns_query = """
                SELECT 
                    lp.id,
                    lp.pattern,
                    lp.pattern_type,
                    lp.priority,
                    lp.frequency,
                    lp.usage_count,
                    lp.success_count,
                    lp.is_active,
                    fc.field_name
                FROM learned_patterns lp
                JOIN field_configs fc ON lp.field_config_id = fc.id
                JOIN template_configs tc ON fc.config_id = tc.id
                WHERE tc.template_id = ? AND lp.is_active = 1
            """
            patterns = self.db.execute_query(patterns_query, (template_id,))
            
            # Get learning jobs
            jobs_query = """
                SELECT 
                    id,
                    field_name,
                    status,
                    patterns_discovered,
                    patterns_applied,
                    started_at,
                    completed_at
                FROM pattern_learning_jobs
                WHERE template_id = ?
                ORDER BY started_at DESC
                LIMIT 10
            """
            jobs = self.db.execute_query(jobs_query, (template_id,))
            
            # Calculate pattern effectiveness
            pattern_effectiveness = {}
            for p in patterns:
                if p["usage_count"] > 0:
                    success_rate = p["success_count"] / p["usage_count"]
                    pattern_effectiveness[p["field_name"]] = round(success_rate, 3)
            
            # Calculate training frequency
            completed_jobs = [j for j in jobs if j["status"] == "completed"]
            if len(completed_jobs) >= 2:
                first_job = datetime.fromisoformat(completed_jobs[-1]["completed_at"])
                last_job = datetime.fromisoformat(completed_jobs[0]["completed_at"])
                days_diff = (last_job - first_job).days
                training_frequency = f"Every {days_diff // len(completed_jobs)} days" if days_diff > 0 else "N/A"
            else:
                training_frequency = "N/A"
            
            return {
                "pattern_learning": {
                    "total_patterns": len(patterns),
                    "active_patterns": len([p for p in patterns if p["is_active"]]),
                    "patterns_by_type": self._group_by_key(patterns, "pattern_type"),
                    "pattern_effectiveness": pattern_effectiveness,
                    "avg_pattern_usage": round(sum(p["usage_count"] for p in patterns) / len(patterns), 2) if patterns else 0.0
                },
                "auto_training": {
                    "total_jobs": len(jobs),
                    "completed_jobs": len(completed_jobs),
                    "failed_jobs": len([j for j in jobs if j["status"] == "failed"]),
                    "training_frequency": training_frequency,
                    "last_training": jobs[0]["completed_at"] if jobs else None,
                    "patterns_discovered_total": sum(j["patterns_discovered"] or 0 for j in completed_jobs)
                },
                "recent_jobs": [
                    {
                        "field_name": j["field_name"],
                        "status": j["status"],
                        "patterns_discovered": j["patterns_discovered"],
                        "patterns_applied": j["patterns_applied"],
                        "completed_at": j["completed_at"]
                    }
                    for j in jobs[:5]
                ]
            }
        except Exception as e:
            return {
                "pattern_learning": {"total_patterns": 0, "error": str(e)},
                "auto_training": {"total_jobs": 0, "error": str(e)},
                "recent_jobs": []
            }
    
    def _calculate_incremental_learning(self, documents: List, feedbacks: List) -> Dict[str, Any]:
        """
        Calculate incremental learning progress
        Tracks accuracy improvement across batches (5, 10, 15, 20 documents)
        """
        if len(documents) < 5:
            return {
                "batches": [],
                "summary": {
                    "total_batches": 0,
                    "avg_improvement_per_batch": 0.0,
                    "optimal_batch_size": 5
                }
            }
        
        # Sort documents by creation time
        sorted_docs = sorted(documents, key=lambda x: x["created_at"])
        
        batch_size = 5  # As per research document
        batches_data = []
        
        for i in range(0, len(sorted_docs), batch_size):
            batch_docs = sorted_docs[i:i+batch_size]
            if len(batch_docs) < batch_size:
                continue  # Skip incomplete batches
            
            batch_number = (i // batch_size) + 1
            
            # Calculate cumulative accuracy (all documents up to and including this batch)
            cumulative_docs = sorted_docs[:i+len(batch_docs)]
            cumulative_accuracy = self._calculate_batch_accuracy(cumulative_docs, feedbacks)
            
            # Calculate accuracy of previous cumulative (for improvement calculation)
            if i > 0:
                prev_cumulative_docs = sorted_docs[:i]
                prev_cumulative_accuracy = self._calculate_batch_accuracy(prev_cumulative_docs, feedbacks)
            else:
                prev_cumulative_accuracy = 0.0
            
            # Calculate accuracy of just this batch (for reference)
            batch_accuracy = self._calculate_batch_accuracy(batch_docs, feedbacks)
            
            # Count feedback in this batch
            batch_doc_ids = [d["id"] for d in batch_docs]
            batch_feedback_count = len([fb for fb in feedbacks if fb["document_id"] in batch_doc_ids])
            
            improvement = cumulative_accuracy - prev_cumulative_accuracy
            
            # Calculate learning efficiency (improvement per feedback)
            learning_efficiency = improvement / batch_feedback_count if batch_feedback_count > 0 else 0.0
            
            batches_data.append({
                "batch_number": batch_number,
                "batch_size": len(batch_docs),
                "document_range": f"{i+1}-{i+len(batch_docs)}",
                "accuracy_before": round(prev_cumulative_accuracy, 4),
                "accuracy_after": round(cumulative_accuracy, 4),
                "improvement": round(improvement, 4),
                "feedback_count": batch_feedback_count,
                "learning_efficiency": round(learning_efficiency, 4),
                "documents": [d["id"] for d in batch_docs]
            })
        
        # Calculate summary
        improvements = [b["improvement"] for b in batches_data if b["improvement"] > 0]
        avg_improvement = sum(improvements) / len(improvements) if improvements else 0.0
        
        # Find best batch by learning efficiency (not just raw improvement)
        best_batch = max(batches_data, key=lambda x: x["learning_efficiency"]) if batches_data else None
        
        # Calculate average learning efficiency
        efficiencies = [b["learning_efficiency"] for b in batches_data if b["learning_efficiency"] > 0]
        avg_efficiency = sum(efficiencies) / len(efficiencies) if efficiencies else 0.0
        
        return {
            "batches": batches_data,
            "summary": {
                "total_batches": len(batches_data),
                "avg_improvement_per_batch": round(avg_improvement, 4),
                "total_improvement": round(sum(improvements), 4),
                "avg_learning_efficiency": round(avg_efficiency, 4),  # New: avg improvement per feedback
                "best_batch_number": best_batch["batch_number"] if best_batch else None,
                "best_batch_efficiency": round(best_batch["learning_efficiency"], 4) if best_batch else 0.0,
                "batch_size_used": batch_size,
                "optimal_batch_size": batch_size  # Can be calculated based on diminishing returns
            }
        }
    
    def _calculate_baseline_comparison(self, documents: List, feedbacks: List) -> Dict[str, Any]:
        """
        Calculate baseline comparison between different extraction strategies
        Compares rule-based, CRF, position-based, and hybrid approaches
        """
        # Track metrics per strategy
        strategy_metrics = defaultdict(lambda: {"total": 0, "correct": 0, "time": []})
        
        # Track overall hybrid performance (final extraction result)
        hybrid_total = 0
        hybrid_correct = 0
        
        validated_count = 0
        skipped_count = 0
        
        for doc in documents:
            # Convert sqlite3.Row to dict for easier access
            doc_dict = dict(doc) if not isinstance(doc, dict) else doc
            
            # Only count validated documents (status='validated')
            if doc_dict.get("status") != "validated":
                skipped_count += 1
                continue
            
            validated_count += 1
                
            try:
                # Get extraction result - try different possible field names
                extraction_result_str = doc_dict.get("extraction_result") or doc_dict.get("result") or "{}"
                if isinstance(extraction_result_str, str):
                    result = json.loads(extraction_result_str)
                else:
                    result = extraction_result_str
                
                extracted_data = result.get("extracted_data", {})
                
                # Get metadata and extraction time from extraction_result
                metadata = result.get("metadata", {})
                strategies_used = metadata.get("strategies_used", [])
                extraction_time = result.get("extraction_time_ms", 0)  # From root level, not metadata
                
                # For each field, check if it was correct
                for field_name, value in extracted_data.items():
                    # Skip empty values
                    if not value or value == "":
                        continue
                    
                    hybrid_total += 1
                    
                    # Check if this field was corrected
                    was_corrected = any(
                        fb["field_name"] == field_name and fb["document_id"] == doc_dict["id"]
                        for fb in feedbacks
                    )
                    
                    if not was_corrected:
                        hybrid_correct += 1
                
                # Track per-strategy metrics
                # Count strategies used in this document for time distribution
                strategy_counts = {}
                for strategy_info in strategies_used:
                    strategy = strategy_info.get("method", "unknown")
                    if strategy not in ["none", "unknown"]:
                        if "_fallback" in strategy:
                            strategy = strategy.replace("_fallback", "")
                        strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
                
                # Distribute extraction time across strategies
                time_per_strategy = {}
                if extraction_time > 0 and strategy_counts:
                    total_fields = sum(strategy_counts.values())
                    for strategy, count in strategy_counts.items():
                        time_per_strategy[strategy] = (extraction_time * count) / total_fields
                
                for strategy_info in strategies_used:
                    strategy = strategy_info.get("method", "unknown")
                    field_name = strategy_info.get("field_name")
                    
                    # Skip 'none' strategy (complete failure)
                    if strategy in ["none", "unknown"]:
                        continue
                    
                    # Map fallback strategies to original strategy
                    if "_fallback" in strategy:
                        strategy = strategy.replace("_fallback", "")
                    
                    # Check if this field was corrected
                    was_correct = not any(
                        fb["field_name"] == field_name and fb["document_id"] == doc_dict["id"]
                        for fb in feedbacks
                    )
                    
                    strategy_metrics[strategy]["total"] += 1
                    if was_correct:
                        strategy_metrics[strategy]["correct"] += 1
                    
                    # Track distributed extraction time
                    if strategy in time_per_strategy:
                        strategy_metrics[strategy]["time"].append(time_per_strategy[strategy])
                        
            except Exception as e:
                self.logger.error(f"Error processing document {doc_dict.get('id')}: {str(e)}")
                continue
        
        # Calculate accuracy for each strategy
        systems = {}
        for strategy, metrics in strategy_metrics.items():
            # Skip 'none' and 'unknown' strategies
            if strategy in ["none", "unknown"]:
                continue
                
            accuracy = metrics["correct"] / metrics["total"] if metrics["total"] > 0 else 0.0
            avg_time = sum(metrics["time"]) / len(metrics["time"]) if metrics["time"] else 0.0
            
            systems[strategy] = {
                "accuracy": round(accuracy, 4),
                "precision": round(accuracy, 4),  # Simplified
                "recall": round(accuracy, 4),  # Simplified
                "f1_score": round(accuracy, 4),  # Simplified
                "total_extractions": metrics["total"],
                "correct_extractions": metrics["correct"],
                "avg_time_ms": round(avg_time, 2)
            }
        
        # Add hybrid system (overall extraction result)
        hybrid_acc = hybrid_correct / hybrid_total if hybrid_total > 0 else 0.0
        
        # Calculate average time across all strategies
        all_times = [t for m in strategy_metrics.values() for t in m["time"]]
        hybrid_avg_time = sum(all_times) / len(all_times) if all_times else 0.0
        
        systems["hybrid"] = {
            "accuracy": round(hybrid_acc, 4),
            "precision": round(hybrid_acc, 4),
            "recall": round(hybrid_acc, 4),
            "f1_score": round(hybrid_acc, 4),
            "total_extractions": hybrid_total,
            "correct_extractions": hybrid_correct,
            "avg_time_ms": round(hybrid_avg_time, 2)
        }
        
        # Calculate improvements
        rule_acc = systems.get("rule_based", {}).get("accuracy", 0.0)
        crf_acc = systems.get("crf", {}).get("accuracy", 0.0)
        
        return {
            "systems": systems,
            "comparison": {
                "best_strategy": max(systems.items(), key=lambda x: x[1]["accuracy"])[0] if systems else "none",
                "worst_strategy": min(systems.items(), key=lambda x: x[1]["accuracy"])[0] if systems else "none"
            },
            "improvement": {
                "hybrid_over_rule": round((hybrid_acc - rule_acc) * 100, 2) if rule_acc > 0 else 0.0,
                "hybrid_over_crf": round((hybrid_acc - crf_acc) * 100, 2) if crf_acc > 0 else 0.0,
                "hybrid_accuracy": round(hybrid_acc * 100, 2)
            }
        }
    
    def _calculate_batch_accuracy(self, batch_docs: List, all_feedbacks: List) -> float:
        """Helper: Calculate accuracy for a batch of documents"""
        if not batch_docs:
            return 0.0
        
        batch_doc_ids = [d["id"] for d in batch_docs]
        total_fields = 0
        correct_fields = 0
        
        for doc in batch_docs:
            try:
                result = json.loads(doc["extraction_result"])
                extracted_data = result.get("extracted_data", {})
                total_fields += len(extracted_data)
                
                # Count corrections for this document
                doc_corrections = len([
                    fb for fb in all_feedbacks 
                    if fb["document_id"] == doc["id"]
                ])
                
                correct_fields += max(0, len(extracted_data) - doc_corrections)
            except:
                continue
        
        return correct_fields / total_fields if total_fields > 0 else 0.0
    
    def _group_by_key(self, items: List[Dict], key: str) -> Dict[str, int]:
        """Helper: Group items by a key and count"""
        result = defaultdict(int)
        for item in items:
            result[item.get(key, "unknown")] += 1
        return dict(result)
