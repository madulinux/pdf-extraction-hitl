#!/usr/bin/env python3
"""
Comprehensive Extraction Pipeline Tracer
Traces every step of extraction and learning to identify why accuracy isn't improving
"""
import sys
sys.path.insert(0, '/Users/madulinux/Documents/S2 UNAS/TESIS/Project/backend')

import json
import os
from datetime import datetime
from database.db_manager import DatabaseManager
from core.learning.metrics import PerformanceMetrics
import logging

# Setup detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trace_extraction.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ExtractionTracer:
    """Comprehensive tracer for extraction pipeline"""
    
    def __init__(self, template_id: int = 1):
        self.db = DatabaseManager()
        self.template_id = template_id
        self.trace_results = []
        
    def trace_full_pipeline(self):
        """Trace entire pipeline from data to results"""
        print("=" * 100)
        print("🔍 COMPREHENSIVE EXTRACTION PIPELINE TRACE")
        print("=" * 100)
        
        # Step 1: Check training data
        print("\n📊 STEP 1: TRAINING DATA ANALYSIS")
        print("-" * 100)
        self._trace_training_data()
        
        # Step 2: Check model status
        print("\n🤖 STEP 2: MODEL STATUS")
        print("-" * 100)
        self._trace_model_status()
        
        # Step 3: Check feedback quality
        print("\n💬 STEP 3: FEEDBACK QUALITY")
        print("-" * 100)
        self._trace_feedback_quality()
        
        # Step 4: Check extraction results
        print("\n📄 STEP 4: EXTRACTION RESULTS ANALYSIS")
        print("-" * 100)
        self._trace_extraction_results()
        
        # Step 5: Check strategy usage
        print("\n🎯 STEP 5: STRATEGY USAGE ANALYSIS")
        print("-" * 100)
        self._trace_strategy_usage()
        
        # Step 6: Check field-specific issues
        print("\n🔍 STEP 6: FIELD-SPECIFIC ANALYSIS")
        print("-" * 100)
        self._trace_field_issues()
        
        # Step 7: Check model features
        print("\n🧬 STEP 7: MODEL FEATURES ANALYSIS")
        print("-" * 100)
        self._trace_model_features()
        
        # Step 8: Recommendations
        print("\n💡 STEP 8: RECOMMENDATIONS")
        print("-" * 100)
        self._generate_recommendations()
        
        print("\n" + "=" * 100)
        print("✅ TRACE COMPLETE")
        print("=" * 100)
        
    def _trace_training_data(self):
        """Check training data quantity and quality"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Count total documents
        cursor.execute('''
            SELECT COUNT(*) FROM documents WHERE template_id = ?
        ''', (self.template_id,))
        total_docs = cursor.fetchone()[0]
        
        # Count validated documents
        cursor.execute('''
            SELECT COUNT(*) FROM documents 
            WHERE template_id = ? AND status = 'validated'
        ''', (self.template_id,))
        validated_docs = cursor.fetchone()[0]
        
        # Count total feedback
        cursor.execute('''
            SELECT COUNT(*) FROM feedback f
            JOIN documents d ON f.document_id = d.id
            WHERE d.template_id = ?
        ''', (self.template_id,))
        total_feedback = cursor.fetchone()[0]
        
        # Count feedback by field
        cursor.execute('''
            SELECT f.field_name, COUNT(*) as count
            FROM feedback f
            JOIN documents d ON f.document_id = d.id
            WHERE d.template_id = ?
            GROUP BY f.field_name
            ORDER BY count DESC
        ''', (self.template_id,))
        feedback_by_field = cursor.fetchall()
        
        conn.close()
        
        print(f"📊 Total Documents: {total_docs}")
        print(f"✅ Validated Documents: {validated_docs} ({validated_docs/total_docs*100:.1f}%)")
        print(f"💬 Total Feedback: {total_feedback}")
        print(f"📈 Avg Feedback per Doc: {total_feedback/total_docs:.2f}")
        
        print(f"\n📋 Feedback Distribution by Field:")
        for field_name, count in feedback_by_field:
            print(f"   {field_name:30s}: {count:4d} corrections")
        
        # Check if enough training data
        if total_feedback < 100:
            print(f"\n⚠️  WARNING: Only {total_feedback} feedback items. Need at least 100 for good training.")
        elif total_feedback < 500:
            print(f"\n⚠️  CAUTION: {total_feedback} feedback items. More data recommended (500+).")
        else:
            print(f"\n✅ GOOD: {total_feedback} feedback items available for training.")
            
    def _trace_model_status(self):
        """Check model training history and status"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Get training history
        cursor.execute('''
            SELECT 
                id, model_path, training_samples, accuracy,
                precision_score, recall_score, f1_score, trained_at
            FROM training_history
            WHERE template_id = ?
            ORDER BY trained_at DESC
            LIMIT 10
        ''', (self.template_id,))
        training_history = cursor.fetchall()
        
        conn.close()
        
        if not training_history:
            print("❌ NO MODEL TRAINED YET!")
            print("   → Model has never been trained for this template")
            print("   → CRF strategy will not be available")
            return
        
        print(f"📚 Training History (Last 10):")
        print(f"{'ID':<5} {'Samples':<10} {'Accuracy':<10} {'Precision':<10} {'Recall':<10} {'F1':<10} {'Date':<20}")
        print("-" * 100)
        
        for record in training_history:
            print(f"{record[0]:<5} {record[2]:<10} {record[3]:<10.4f} {record[4]:<10.4f} {record[5]:<10.4f} {record[6]:<10.4f} {record[7]:<20}")
        
        # Check if model file exists
        latest_model = training_history[0]
        model_path = latest_model[1]
        
        if os.path.exists(model_path):
            print(f"\n✅ Model file exists: {model_path}")
            print(f"   Size: {os.path.getsize(model_path) / 1024:.2f} KB")
        else:
            print(f"\n❌ Model file NOT FOUND: {model_path}")
            print(f"   → CRF strategy will fail!")
            
        # Check accuracy trend
        if len(training_history) >= 3:
            recent_accuracies = [r[3] for r in training_history[:3]]
            if recent_accuracies[0] < recent_accuracies[-1]:
                print(f"\n⚠️  WARNING: Model accuracy DECREASING!")
                print(f"   Latest: {recent_accuracies[0]:.4f}")
                print(f"   Previous: {recent_accuracies[-1]:.4f}")
            elif abs(recent_accuracies[0] - recent_accuracies[-1]) < 0.01:
                print(f"\n⚠️  WARNING: Model accuracy STAGNANT!")
                print(f"   No improvement in last 3 trainings")
            else:
                print(f"\n✅ Model accuracy improving")
                
    def _trace_feedback_quality(self):
        """Check quality of feedback data"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Get sample feedback
        cursor.execute('''
            SELECT 
                f.field_name, f.original_value, f.corrected_value,
                f.confidence_score
            FROM feedback f
            JOIN documents d ON f.document_id = d.id
            WHERE d.template_id = ?
            ORDER BY f.created_at DESC
            LIMIT 20
        ''', (self.template_id,))
        feedback_samples = cursor.fetchall()
        
        conn.close()
        
        print("📝 Recent Feedback Samples (Last 20):")
        print(f"{'Field':<25} {'Original':<30} {'Corrected':<30} {'Confidence':<10}")
        print("-" * 100)
        
        empty_corrections = 0
        same_corrections = 0
        
        for fb in feedback_samples[:10]:  # Show first 10
            field = fb[0][:24]
            original = str(fb[1])[:29] if fb[1] else "(empty)"
            corrected = str(fb[2])[:29] if fb[2] else "(empty)"
            confidence = fb[3] if fb[3] else 0.0
            
            print(f"{field:<25} {original:<30} {corrected:<30} {confidence:<10.2f}")
            
            if not fb[2]:
                empty_corrections += 1
            if fb[1] == fb[2]:
                same_corrections += 1
        
        print(f"\n📊 Feedback Quality Metrics:")
        print(f"   Empty corrections: {empty_corrections}/20")
        print(f"   Same as original: {same_corrections}/20")
        
        if empty_corrections > 5:
            print(f"\n⚠️  WARNING: Too many empty corrections ({empty_corrections}/20)")
            print(f"   → This will confuse the model!")
        
        if same_corrections > 10:
            print(f"\n⚠️  WARNING: Too many unchanged values ({same_corrections}/20)")
            print(f"   → Model not learning from these")
            
    def _trace_extraction_results(self):
        """Analyze extraction results"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Get recent extractions
        cursor.execute('''
            SELECT 
                id, extraction_result, status, created_at
            FROM documents
            WHERE template_id = ?
            ORDER BY created_at DESC
            LIMIT 10
        ''', (self.template_id,))
        recent_docs = cursor.fetchall()
        
        conn.close()
        
        print("📄 Recent Extraction Results (Last 10):")
        
        for doc in recent_docs:
            doc_id = doc[0]
            result_json = doc[1]
            status = doc[2]
            
            if not result_json:
                print(f"\n❌ Document {doc_id}: NO EXTRACTION RESULT")
                continue
            
            try:
                result = json.loads(result_json)
                extracted_data = result.get('extracted_data', {})
                extraction_methods = result.get('extraction_methods', {})
                confidence_scores = result.get('confidence_scores', {})
                
                print(f"\n📄 Document {doc_id} ({status}):")
                print(f"   Fields extracted: {len(extracted_data)}")
                
                # Show extraction methods used
                method_counts = {}
                for method in extraction_methods.values():
                    method_counts[method] = method_counts.get(method, 0) + 1
                
                print(f"   Methods used: {method_counts}")
                
                # Show average confidence
                if confidence_scores:
                    avg_conf = sum(confidence_scores.values()) / len(confidence_scores)
                    print(f"   Avg confidence: {avg_conf:.2f}")
                    
            except Exception as e:
                print(f"\n❌ Document {doc_id}: Error parsing result - {e}")
                
    def _trace_strategy_usage(self):
        """Analyze which strategies are being used"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Get strategy performance
        cursor.execute('''
            SELECT 
                strategy_name, field_name, 
                total_attempts, successful_extractions, accuracy
            FROM strategy_performance
            WHERE template_id = ?
            ORDER BY accuracy DESC
        ''', (self.template_id,))
        strategy_perf = cursor.fetchall()
        
        conn.close()
        
        if not strategy_perf:
            print("❌ NO STRATEGY PERFORMANCE DATA!")
            print("   → Strategy performance tracking may not be working")
            return
        
        print("🎯 Strategy Performance by Field:")
        print(f"{'Strategy':<20} {'Field':<25} {'Attempts':<10} {'Success':<10} {'Accuracy':<10}")
        print("-" * 100)
        
        strategy_totals = {}
        
        for perf in strategy_perf[:20]:  # Top 20
            strategy = perf[0]
            field = perf[1][:24]
            attempts = perf[2]
            success = perf[3]
            accuracy = perf[4]
            
            print(f"{strategy:<20} {field:<25} {attempts:<10} {success:<10} {accuracy:<10.2f}")
            
            if strategy not in strategy_totals:
                strategy_totals[strategy] = {'attempts': 0, 'success': 0}
            strategy_totals[strategy]['attempts'] += attempts
            strategy_totals[strategy]['success'] += success
        
        print(f"\n📊 Overall Strategy Usage:")
        for strategy, stats in strategy_totals.items():
            accuracy = stats['success'] / stats['attempts'] * 100 if stats['attempts'] > 0 else 0
            print(f"   {strategy:<20}: {stats['attempts']:4d} attempts, {stats['success']:4d} success ({accuracy:.1f}%)")
            
        # Check if CRF is being used
        if 'crf' not in strategy_totals or strategy_totals['crf']['attempts'] == 0:
            print(f"\n⚠️  WARNING: CRF strategy NOT BEING USED!")
            print(f"   → Model may not be loaded properly")
            print(f"   → Check model path and file existence")
            
    def _trace_field_issues(self):
        """Identify problematic fields"""
        metrics_service = PerformanceMetrics(self.db)
        metrics = metrics_service.get_template_metrics(self.template_id)
        
        field_performance = metrics.get('field_performance', {})
        error_patterns = metrics.get('error_patterns', {})
        
        print("🔍 Field-Specific Issues:")
        
        # Sort by accuracy
        sorted_fields = sorted(
            field_performance.items(),
            key=lambda x: x[1].get('accuracy', 0)
        )
        
        print(f"\n📉 Worst Performing Fields:")
        print(f"{'Field':<30} {'Accuracy':<10} {'Corrections':<12} {'Avg Confidence':<15}")
        print("-" * 100)
        
        for field_name, perf in sorted_fields[:10]:
            accuracy = perf.get('accuracy', 0)
            corrections = perf.get('corrections', 0)
            avg_conf = perf.get('avg_confidence', 0)
            
            print(f"{field_name:<30} {accuracy:<10.2f} {corrections:<12} {avg_conf:<15.2f}")
        
        # Show error patterns
        problematic_fields = error_patterns.get('most_problematic_fields', [])
        if problematic_fields:
            print(f"\n⚠️  Most Problematic Fields:")
            for field_info in problematic_fields[:5]:
                field_name = field_info['field_name']
                error_count = field_info['error_count']
                print(f"   {field_name}: {error_count} errors")
                
                # Show examples
                examples = field_info.get('examples', [])
                for ex in examples[:2]:
                    print(f"      Original: {ex['original']}")
                    print(f"      Corrected: {ex['corrected']}")
                    
    def _trace_model_features(self):
        """Check if model is using correct features"""
        print("🧬 Model Feature Analysis:")
        
        # Check if model file exists and can be loaded
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT model_path FROM training_history
            WHERE template_id = ?
            ORDER BY trained_at DESC
            LIMIT 1
        ''', (self.template_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            print("❌ No model found")
            return
        
        model_path = result[0]
        
        if not os.path.exists(model_path):
            print(f"❌ Model file not found: {model_path}")
            return
        
        try:
            import joblib
            model = joblib.load(model_path)
            
            print(f"✅ Model loaded successfully")
            print(f"   Type: {type(model).__name__}")
            
            # Try to get feature info
            if hasattr(model, 'state_features_'):
                print(f"   State features: {len(model.state_features_)} features")
                
                # Check for field-aware features
                field_aware_count = 0
                for feature in model.state_features_:
                    if 'target_field_' in feature:
                        field_aware_count += 1
                
                print(f"   Field-aware features: {field_aware_count}")
                
                if field_aware_count == 0:
                    print(f"\n❌ CRITICAL: NO FIELD-AWARE FEATURES!")
                    print(f"   → This is the bug we fixed before!")
                    print(f"   → Model cannot distinguish between fields")
                    print(f"   → Need to retrain with target_fields parameter")
                else:
                    print(f"\n✅ Field-aware features present")
                    
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            
    def _generate_recommendations(self):
        """Generate actionable recommendations"""
        print("💡 RECOMMENDATIONS:")
        print()
        
        recommendations = []
        
        # Check training data
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM feedback f
            JOIN documents d ON f.document_id = d.id
            WHERE d.template_id = ?
        ''', (self.template_id,))
        total_feedback = cursor.fetchone()[0]
        
        # Check model status
        cursor.execute('''
            SELECT model_path FROM training_history
            WHERE template_id = ?
            ORDER BY trained_at DESC
            LIMIT 1
        ''', (self.template_id,))
        model_result = cursor.fetchone()
        
        # Check CRF usage
        cursor.execute('''
            SELECT COUNT(*) FROM strategy_performance
            WHERE template_id = ? AND strategy_name = 'crf'
        ''', (self.template_id,))
        crf_usage = cursor.fetchone()[0]
        
        conn.close()
        
        # Generate recommendations
        if total_feedback < 100:
            recommendations.append({
                'priority': 'HIGH',
                'issue': 'Insufficient training data',
                'detail': f'Only {total_feedback} feedback items',
                'action': 'Collect at least 100 feedback items before training'
            })
        
        if not model_result or not os.path.exists(model_result[0]):
            recommendations.append({
                'priority': 'CRITICAL',
                'issue': 'Model not trained or missing',
                'detail': 'CRF model file not found',
                'action': 'Train model using: python -m core.learning.services'
            })
        
        if crf_usage == 0:
            recommendations.append({
                'priority': 'HIGH',
                'issue': 'CRF strategy not being used',
                'detail': 'Model may not be loaded in extraction',
                'action': 'Check model path in extraction service'
            })
        
        # Check for field-aware features
        if model_result and os.path.exists(model_result[0]):
            try:
                import joblib
                model = joblib.load(model_result[0])
                if hasattr(model, 'state_features_'):
                    field_aware_count = sum(1 for f in model.state_features_ if 'target_field_' in f)
                    if field_aware_count == 0:
                        recommendations.append({
                            'priority': 'CRITICAL',
                            'issue': 'Model missing field-aware features',
                            'detail': 'Model cannot distinguish between fields',
                            'action': 'Retrain model with target_fields parameter (see CRITICAL_BUG_FIX_FIELD_AWARE_TRAINING.md)'
                        })
            except:
                pass
        
        # Print recommendations
        if not recommendations:
            print("✅ No critical issues found!")
            print("   System appears to be functioning correctly")
        else:
            for i, rec in enumerate(recommendations, 1):
                print(f"{i}. [{rec['priority']}] {rec['issue']}")
                print(f"   Detail: {rec['detail']}")
                print(f"   Action: {rec['action']}")
                print()

if __name__ == '__main__':
    tracer = ExtractionTracer(template_id=1)
    tracer.trace_full_pipeline()
