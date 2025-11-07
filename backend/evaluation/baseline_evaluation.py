"""
Baseline Evaluation Script for BAB 4.2.1
Evaluasi Akurasi Ekstraksi

This script evaluates:
1. Overall system performance (accuracy, precision, recall, F1)
2. Per-field performance metrics
3. Confusion matrix
4. Strategy comparison (Rule vs CRF vs Hybrid)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from difflib import SequenceMatcher
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

from database.db_manager import DatabaseManager
from core.learning.services import ModelService


class BaselineEvaluator:
    """Evaluator for baseline system performance"""
    
    def __init__(self, template_id: int = 1, similarity_threshold: float = 0.8):
        self.template_id = template_id
        self.similarity_threshold = similarity_threshold
        # Fix: Use absolute path to backend/data/app.db
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'app.db')
        self.db = DatabaseManager(db_path)
    
    def string_similarity(self, a: str, b: str) -> float:
        """
        Calculate string similarity using SequenceMatcher
        
        Args:
            a: First string
            b: Second string
            
        Returns:
            Similarity score between 0 and 1
        """
        if not a and not b:
            return 1.0
        if not a or not b:
            return 0.0
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()
    
    def token_overlap(self, a: str, b: str) -> float:
        """
        Calculate token overlap ratio
        
        Args:
            a: First string
            b: Second string (ground truth)
            
        Returns:
            Overlap ratio between 0 and 1
        """
        if not b:
            return 1.0 if not a else 0.0
        if not a:
            return 0.0
        
        tokens_a = set(a.lower().split())
        tokens_b = set(b.lower().split())
        
        if not tokens_b:
            return 1.0
        
        overlap = len(tokens_a & tokens_b)
        return overlap / len(tokens_b)
    
    def is_match(self, extracted: str, ground_truth: str, use_fuzzy: bool = True) -> tuple:
        """
        Determine if extraction matches ground truth
        
        Args:
            extracted: Extracted value
            ground_truth: Ground truth value
            use_fuzzy: Use fuzzy matching (default True)
            
        Returns:
            Tuple of (is_correct: bool, similarity_score: float)
        """
        if use_fuzzy:
            similarity = self.string_similarity(extracted, ground_truth)
            is_correct = similarity >= self.similarity_threshold
            return is_correct, similarity
        else:
            is_correct = extracted == ground_truth
            return is_correct, 1.0 if is_correct else 0.0
        
    def evaluate_overall_performance(self) -> Dict:
        """
        Evaluate overall system performance
        
        Returns:
            Dict with overall metrics
        """
        print("\n" + "="*60)
        print("📊 BASELINE EVALUATION - Overall Performance")
        print(f"   Similarity Threshold: {self.similarity_threshold*100:.0f}%")
        print("="*60)
        
        # Get all validated documents
        documents = self.db.get_validated_documents(self.template_id)
        
        if not documents:
            print("❌ No validated documents found!")
            print("   Tip: Make sure you have documents with status='validated'")
            print("   Check: SELECT * FROM documents WHERE template_id=1 AND status='validated';")
            return {
                'total_documents': 0,
                'total_fields': 0,
                'accuracy': 0.0,
                'precision': 0.0,
                'recall': 0.0,
                'f1_score': 0.0,
                'avg_similarity': 0.0
            }
        
        print(f"\n✅ Found {len(documents)} validated documents")
        
        # Collect predictions and ground truth
        correct_count = 0
        total_count = 0
        similarity_scores = []
        field_names = set()
        
        for doc in documents:
            # Get extraction results (predictions)
            extraction_result = json.loads(doc['extraction_result'])
            extracted_data = extraction_result.get('extracted_data', {})
            
            # Get ground truth from feedback (corrections)
            feedback_list = self.db.get_feedback_by_document(doc['id'])
            corrections = {fb['field_name']: fb['corrected_value'] for fb in feedback_list}
            
            # For each extracted field, determine ground truth
            for field_name, extracted_value in extracted_data.items():
                # If field was corrected, use corrected value as ground truth
                if field_name in corrections:
                    ground_truth_value = corrections[field_name]
                else:
                    # No correction = extraction was correct (validated document)
                    ground_truth_value = extracted_value
                
                # Use fuzzy matching
                is_correct, similarity = self.is_match(extracted_value, ground_truth_value, use_fuzzy=True)
                
                if is_correct:
                    correct_count += 1
                total_count += 1
                similarity_scores.append(similarity)
                
                # Track field names
                field_names.add(field_name)
        
        # Calculate metrics
        accuracy = correct_count / total_count if total_count > 0 else 0.0
        avg_similarity = np.mean(similarity_scores) if similarity_scores else 0.0
        
        # For precision/recall/F1: calculate based on correct vs incorrect
        precision = correct_count / total_count if total_count > 0 else 0.0
        recall = accuracy  # Same as accuracy in this context
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        results = {
            'total_documents': len(documents),
            'total_fields': total_count,
            'correct_fields': correct_count,
            'incorrect_fields': total_count - correct_count,
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'avg_similarity': avg_similarity,
            'similarity_threshold': self.similarity_threshold
        }
        
        # Print results
        print("\n📈 Overall Metrics (Fuzzy Matching):")
        print(f"   Total Documents: {results['total_documents']}")
        print(f"   Total Fields Evaluated: {results['total_fields']}")
        print(f"   Correct Fields: {results['correct_fields']}")
        print(f"   Incorrect Fields: {results['incorrect_fields']}")
        print(f"   Accuracy:  {results['accuracy']:.4f} ({results['accuracy']*100:.2f}%)")
        print(f"   Avg Similarity: {results['avg_similarity']:.4f} ({results['avg_similarity']*100:.2f}%)")
        print(f"   Precision: {results['precision']:.4f} ({results['precision']*100:.2f}%)")
        print(f"   Recall:    {results['recall']:.4f} ({results['recall']*100:.2f}%)")
        print(f"   F1-Score:  {results['f1_score']:.4f} ({results['f1_score']*100:.2f}%)")
        
        return results
    
    def evaluate_per_field_performance(self) -> pd.DataFrame:
        """
        Evaluate performance per field
        
        Returns:
            DataFrame with per-field metrics
        """
        print("\n" + "="*60)
        print("📊 BASELINE EVALUATION - Per-Field Performance")
        print("="*60)
        
        # Get all validated documents
        documents = self.db.get_validated_documents(self.template_id)
        
        if not documents:
            print("❌ No validated documents found!")
            return pd.DataFrame()
        
        # Collect per-field results
        field_results = {}
        
        for doc in documents:
            extraction_result = json.loads(doc['extraction_result'])
            extracted_data = extraction_result.get('extracted_data', {})
            
            # Get corrections from feedback
            feedback_list = self.db.get_feedback_by_document(doc['id'])
            corrections = {fb['field_name']: fb['corrected_value'] for fb in feedback_list}
            
            # Evaluate each field
            for field_name, extracted_value in extracted_data.items():
                if field_name not in field_results:
                    field_results[field_name] = {
                        'correct': 0,
                        'incorrect': 0,
                        'total': 0,
                        'similarities': []
                    }
                
                # Determine ground truth
                if field_name in corrections:
                    ground_truth_value = corrections[field_name]
                else:
                    # No correction = extraction was correct
                    ground_truth_value = extracted_value
                
                # Use fuzzy matching
                is_correct, similarity = self.is_match(extracted_value, ground_truth_value, use_fuzzy=True)
                
                field_results[field_name]['total'] += 1
                field_results[field_name]['similarities'].append(similarity)
                if is_correct:
                    field_results[field_name]['correct'] += 1
                else:
                    field_results[field_name]['incorrect'] += 1
        
        # Calculate metrics per field
        df_data = []
        for field_name, stats in field_results.items():
            total = stats['total']
            correct = stats['correct']
            incorrect = stats['incorrect']
            similarities = stats['similarities']
            
            accuracy = correct / total if total > 0 else 0
            avg_similarity = np.mean(similarities) if similarities else 0
            precision = correct / (correct + incorrect) if (correct + incorrect) > 0 else 0
            recall = correct / total if total > 0 else 0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            
            df_data.append({
                'field_name': field_name,
                'total': total,
                'correct': correct,
                'incorrect': incorrect,
                'accuracy': accuracy,
                'avg_similarity': avg_similarity,
                'precision': precision,
                'recall': recall,
                'f1_score': f1
            })
        
        df = pd.DataFrame(df_data)
        
        if not df.empty:
            df = df.sort_values('f1_score', ascending=False)
        
        # Print results
        print("\n📈 Per-Field Metrics:")
        if not df.empty:
            print(df.to_string(index=False))
        else:
            print("   No data to display")
        
        # Save to CSV
        output_file = 'evaluation/results/per_field_metrics.csv'
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        df.to_csv(output_file, index=False)
        print(f"\n💾 Results saved to: {output_file}")
        
        return df
    
    def compare_strategies(self) -> pd.DataFrame:
        """
        Compare different extraction strategies
        
        Returns:
            DataFrame with strategy comparison
        """
        print("\n" + "="*60)
        print("📊 BASELINE EVALUATION - Strategy Comparison")
        print("="*60)
        
        print("\n⚠️  Note: This requires implementing baseline strategies")
        print("    For now, showing current hybrid strategy results")
        
        # TODO: Implement rule-based only, CRF only, template matching only
        # For now, just return current results
        
        strategies = {
            'Hybrid (Current)': self.evaluate_overall_performance()
        }
        
        df_data = []
        for strategy_name, metrics in strategies.items():
            df_data.append({
                'strategy': strategy_name,
                'accuracy': metrics.get('accuracy', 0),
                'precision': metrics.get('precision', 0),
                'recall': metrics.get('recall', 0),
                'f1_score': metrics.get('f1_score', 0)
            })
        
        df = pd.DataFrame(df_data)
        
        print("\n📈 Strategy Comparison:")
        print(df.to_string(index=False))
        
        return df
    
    def generate_confusion_matrix(self):
        """Generate confusion matrix for field-level predictions"""
        print("\n" + "="*60)
        print("📊 BASELINE EVALUATION - Confusion Matrix")
        print("="*60)
        
        # Get all validated documents
        documents = self.db.get_validated_documents(self.template_id)
        
        if not documents:
            print("❌ No validated documents found!")
            return
        
        # Collect predictions
        y_true = []
        y_pred = []
        
        for doc in documents:
            extraction_result = json.loads(doc['extraction_result'])
            extracted_data = extraction_result.get('extracted_data', {})
            
            # Get corrections from feedback
            feedback_list = self.db.get_feedback_by_document(doc['id'])
            corrections = {fb['field_name']: fb['corrected_value'] for fb in feedback_list}
            
            for field_name, extracted_value in extracted_data.items():
                # Determine ground truth
                if field_name in corrections:
                    ground_truth_value = corrections[field_name]
                else:
                    ground_truth_value = extracted_value
                
                # Use fuzzy matching
                is_correct, _ = self.is_match(extracted_value, ground_truth_value, use_fuzzy=True)
                
                # Binary: 1 = correct, 0 = incorrect
                y_true.append(1)
                y_pred.append(1 if is_correct else 0)
        
        # Generate confusion matrix
        cm = confusion_matrix(y_true, y_pred)
        
        # Plot
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                    xticklabels=['Incorrect', 'Correct'],
                    yticklabels=['Ground Truth'])
        plt.title('Confusion Matrix - Field-Level Extraction')
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        
        output_file = 'evaluation/results/confusion_matrix.png'
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"\n💾 Confusion matrix saved to: {output_file}")
        
        plt.close()
    
    def run_full_evaluation(self):
        """Run complete baseline evaluation"""
        print("\n" + "🚀"*30)
        print("STARTING BASELINE EVALUATION")
        print("🚀"*30)
        
        # 1. Overall performance
        overall_results = self.evaluate_overall_performance()
        
        # 2. Per-field performance
        per_field_results = self.evaluate_per_field_performance()
        
        # 3. Strategy comparison
        strategy_comparison = self.compare_strategies()
        
        # 4. Confusion matrix
        self.generate_confusion_matrix()
        
        # Save summary
        summary = {
            'overall_metrics': overall_results,
            'per_field_metrics': per_field_results.to_dict('records') if not per_field_results.empty else [],
            'strategy_comparison': strategy_comparison.to_dict('records') if not strategy_comparison.empty else []
        }
        
        output_file = 'evaluation/results/baseline_evaluation_summary.json'
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print("\n" + "✅"*30)
        print("BASELINE EVALUATION COMPLETE")
        print("✅"*30)
        print(f"\n📁 Results saved to: evaluation/results/")
        
        return summary


if __name__ == '__main__':
    evaluator = BaselineEvaluator(template_id=1)
    results = evaluator.run_full_evaluation()
