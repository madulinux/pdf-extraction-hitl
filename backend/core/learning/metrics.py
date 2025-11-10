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


class PerformanceMetrics:
    """Service for tracking and analyzing performance metrics"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.document_repository = DocumentRepository(db_manager)
        self.feedback_repository = FeedbackRepository(db_manager)
        self.strategy_performance_repository = StrategyPerformanceRepository(db_manager)

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
            }
        )

        # First, count ALL extractions from documents
        for doc in documents:
            if doc["extraction_result"]:
                try:
                    result = json.loads(doc["extraction_result"])
                    extracted_data = result.get("extracted_data", {})
                    confidences = result.get("confidence_scores", {})

                    for field_name, value in extracted_data.items():
                        if value:  # Only count non-empty extractions
                            field_stats[field_name]["total_extractions"] += 1

                            # Track confidence
                            if (
                                field_name in confidences
                                and confidences[field_name] is not None
                            ):
                                field_stats[field_name]["avg_confidence"].append(
                                    confidences[field_name]
                                )
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
        self, documents: List, feedbacks: List, batch_size: int = 50
    ) -> Dict[str, Any]:
        """
        Calculate learning progress over batches of documents
        Shows how accuracy improves as model learns from feedback
        """
        if not documents:
            return {
                "batches": [],
                "improvement_rate": 0.0,
                "first_batch_accuracy": 0.0,
                "last_batch_accuracy": 0.0,
            }

        # Group feedback by document
        feedback_by_doc = defaultdict(list)
        for fb in feedbacks:
            feedback_by_doc[fb["document_id"]].append(fb)

        # Calculate accuracy per batch
        batches = []
        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i : i + batch_size]
            total_fields = 0
            correct_fields = 0

            for doc in batch_docs:
                try:
                    result = json.loads(doc["extraction_result"])
                    extracted = result.get("extracted_data", {})
                    doc_feedbacks = feedback_by_doc.get(doc["id"], [])

                    fields_count = len([v for v in extracted.values() if v])
                    incorrect_count = len(doc_feedbacks)

                    total_fields += fields_count
                    correct_fields += max(0, fields_count - incorrect_count)
                except:
                    pass

            if total_fields > 0:
                accuracy = correct_fields / total_fields
                batches.append(
                    {
                        "batch_number": len(batches) + 1,
                        "start_doc": i + 1,
                        "end_doc": min(i + batch_size, len(documents)),
                        "accuracy": round(accuracy, 3),
                        "total_fields": total_fields,
                        "correct_fields": correct_fields,
                    }
                )

        # Calculate improvement rate
        if len(batches) >= 2:
            first_acc = batches[0]["accuracy"]
            last_acc = batches[-1]["accuracy"]
            improvement = (
                ((last_acc - first_acc) / first_acc * 100) if first_acc > 0 else 0
            )
        else:
            first_acc = batches[0]["accuracy"] if batches else 0.0
            last_acc = first_acc
            improvement = 0.0

        return {
            "batches": batches,
            "improvement_rate": round(improvement, 2),
            "first_batch_accuracy": round(first_acc, 3),
            "last_batch_accuracy": round(last_acc, 3),
            "total_batches": len(batches),
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
