"""
Dashboard API Routes
System-wide overview and aggregate metrics endpoints
"""
from flask import Blueprint, request
from utils.response import APIResponse
from utils.decorators import handle_errors
from api.middleware.auth import require_auth
from database.db_manager import DatabaseManager
from core.learning.metrics import PerformanceMetrics


# Create blueprint
dashboard_bp = Blueprint('dashboard_v1', __name__, url_prefix='/api/v1/dashboard')


@dashboard_bp.route('/overview', methods=['GET'])
@handle_errors
@require_auth
def get_system_overview():
    """
    Get system-wide overview metrics across all templates
    
    Query Parameters:
        - phase: Filter by experiment phase (baseline, adaptive, all, or omit for production)
    
    Returns:
        200: System-wide metrics including:
            - Total documents across all templates
            - Overall accuracy
            - Total feedback
            - Template summaries
            - Recent activity
        401: Unauthorized
    """
    # Get optional phase filter
    experiment_phase = request.args.get('phase', None)
    
    # Validate phase value
    valid_phases = [None, 'baseline', 'adaptive', 'all']
    if experiment_phase not in valid_phases:
        return APIResponse.bad_request(
            f"Invalid phase. Must be one of: baseline, adaptive, all, or omit for production"
        )
    
    db = DatabaseManager()
    
    # Get all templates using repository
    from database.repositories.template_repository import TemplateRepository
    template_repo = TemplateRepository(db)
    templates = template_repo.find_all()
    
    # Load from experiment results files
    import json
    import os
    
    results_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'experiments', 'results')
    
    # Aggregate metrics
    total_documents = 0
    total_feedback = 0
    total_fields = 0
    total_correct_fields = 0
    template_summaries = []
    all_improvements = []
    
    for template in templates:
        try:
            # Load adaptive results
            adaptive_file = os.path.join(results_dir, f'adaptive_template_{template.id}.json')
            
            if not os.path.exists(adaptive_file):
                print(f"Template {template.id}: No experiment results file")
                continue
            
            with open(adaptive_file, 'r') as f:
                adaptive_data = json.load(f)
            
            # Extract metrics
            metrics = adaptive_data['metrics']
            total_docs = adaptive_data.get('total_documents', 35)
            total_corrections = adaptive_data.get('total_corrections', 0)
            improvement = adaptive_data.get('improvement', 0) * 100
            
            # Calculate fields
            template_fields = total_docs * template.field_count
            template_correct = int(template_fields * metrics['accuracy'])
            
            # Aggregate
            total_documents += total_docs
            total_feedback += total_corrections
            total_fields += template_fields
            total_correct_fields += template_correct
            all_improvements.append(improvement)
            
            # Calculate learning efficiency: improvement per feedback (as percentage points)
            # Example: 23.24% improvement / 32 corrections = 0.726% per correction
            learning_eff = (improvement / total_corrections) if total_corrections > 0 else 0
            
            # Template summary
            template_summaries.append({
                'id': template.id,
                'name': template.name,
                'type': _infer_template_type(template.name),
                'documents': total_docs,
                'validated': total_docs,  # All experiment docs are validated
                'accuracy': metrics['accuracy'],
                'feedback_count': total_corrections,
                'field_count': template.field_count,
                'status': 'active',
                'learning_efficiency': learning_eff / 100  # Convert to decimal for display
            })
            
            print(f"Template {template.id} ({template.name}): {total_docs} docs, {metrics['accuracy']*100:.2f}% accuracy, {total_corrections} corrections")
            
        except Exception as e:
            print(f"Error loading experiment results for template {template.id}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Calculate overall metrics
    overall_accuracy = total_correct_fields / total_fields if total_fields > 0 else 0
    avg_learning_efficiency = sum(all_improvements) / len(all_improvements) if all_improvements else 0
    
    return APIResponse.success({
        'system_stats': {
            'total_documents': total_documents,
            'total_validated': total_documents,  # All experiment docs are validated
            'total_feedback': total_feedback,
            'total_fields': total_fields,
            'overall_accuracy': overall_accuracy,
            'validation_rate': 1.0,  # 100% for experiments
            'active_templates': len(template_summaries),
            'total_templates': len(templates),
            # HITL-specific metrics (Tujuan #2 & #3)
            'avg_feedback_per_doc': total_feedback / total_documents if total_documents > 0 else 0,
            'learning_efficiency': avg_learning_efficiency / 100,  # As decimal
            'feedback_utilization_rate': 1.0  # 100% feedback used in experiments
        },
        'template_summaries': template_summaries,
        'hitl_learning_metrics': {
            'learning_efficiency': avg_learning_efficiency / 100,
            'feedback_utilization_rate': 1.0,
            'total_feedback': total_feedback,
            'avg_improvement_per_feedback': avg_learning_efficiency
        },
        'phase': experiment_phase or 'production'
    }, f"System overview retrieved successfully (phase: {experiment_phase or 'production'})")


@dashboard_bp.route('/template-comparison', methods=['GET'])
@handle_errors
@require_auth
def get_template_comparison():
    """
    Get comparison metrics across all templates
    
    Query Parameters:
        - phase: Filter by experiment phase
    
    Returns:
        200: Comparison data for all templates
        401: Unauthorized
    """
    experiment_phase = request.args.get('phase', None)
    
    # Validate phase value
    valid_phases = [None, 'baseline', 'adaptive', 'all']
    if experiment_phase not in valid_phases:
        return APIResponse.bad_request(
            f"Invalid phase. Must be one of: baseline, adaptive, all, or omit for production"
        )
    
    db = DatabaseManager()
    metrics_service = PerformanceMetrics(db)
    
    # Get all templates using repository
    from database.repositories.template_repository import TemplateRepository
    template_repo = TemplateRepository(db)
    templates = template_repo.find_all()
    
    comparison_data = []
    
    for template in templates:
        try:
            metrics = metrics_service.get_template_metrics(template.id, experiment_phase)
            overview = metrics.get('overview', {})
            
            comparison_data.append({
                'template_id': template.id,
                'template_name': template.name,
                'template_type': _infer_template_type(template.name),
                'accuracy': overview.get('overall_accuracy', 0),
                'documents': overview.get('total_documents', 0),
                'feedback_count': metrics.get('feedback_stats', {}).get('total_feedback', 0),
                'avg_confidence': _calculate_avg_confidence(metrics),
                'strategy_preference': _get_dominant_strategy(metrics)
            })
        except:
            comparison_data.append({
                'template_id': template.id,
                'template_name': template.name,
                'template_type': _infer_template_type(template.name),
                'accuracy': 0,
                'documents': 0,
                'feedback_count': 0,
                'avg_confidence': 0,
                'strategy_preference': 'unknown'
            })
    
    return APIResponse.success({
        'templates': comparison_data,
        'phase': experiment_phase or 'production'
    })


# Recent activity endpoint removed - not needed for thesis dashboard


# System health endpoint removed - not needed for thesis dashboard


# Helper functions
def _infer_template_type(template_name):
    """Infer template type from name"""
    name_lower = template_name.lower()
    if 'form' in name_lower:
        return 'form'
    elif 'table' in name_lower:
        return 'table'
    elif 'letter' in name_lower:
        return 'letter'
    elif 'mixed' in name_lower:
        return 'mixed'
    else:
        return 'unknown'


# Recent activity removed - not needed for thesis dashboard


# Strategy distribution removed - not needed for thesis dashboard (uses database queries)


# Helper functions for confidence and strategy removed - not needed for thesis dashboard


# Strategy performance comparison removed - not needed for thesis dashboard (uses database queries)


@dashboard_bp.route('/learning-curves', methods=['GET'])
@handle_errors
@require_auth
def get_learning_curves():
    """
    Get learning curves data for all templates (for thesis visualization)
    Shows accuracy progression across batches
    
    Query Parameters:
        - phase: Filter by experiment phase (default: adaptive)
    
    Returns:
        200: Learning curves data for all templates
        401: Unauthorized
    """
    experiment_phase = request.args.get('phase', 'adaptive')
    
    db = DatabaseManager()
    metrics_service = PerformanceMetrics(db)
    
    # Get all templates
    from database.repositories.template_repository import TemplateRepository
    template_repo = TemplateRepository(db)
    templates = template_repo.find_all()
    
    learning_curves = []
    
    # Load learning curves from experiment results files
    import json
    import os
    
    results_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'experiments', 'results')
    
    for template in templates:
        try:
            # Load from experiment results file
            results_file = os.path.join(results_dir, f'adaptive_template_{template.id}.json')
            
            if not os.path.exists(results_file):
                print(f"Template {template.id} ({template.name}): No experiment results file found")
                continue
            
            with open(results_file, 'r') as f:
                experiment_data = json.load(f)
            
            learning_curve_data = experiment_data.get('learning_curve', [])
            
            if not learning_curve_data:
                print(f"Template {template.id} ({template.name}): No learning curve data")
                continue
            
            print(f"Template {template.id} ({template.name}): {len(learning_curve_data)} batches from experiment results")
            
            # Convert experiment learning curve data to dashboard format
            batches = []
            for batch_data in learning_curve_data:
                batch_num = batch_data.get('batch', 0)
                accuracy = batch_data.get('accuracy', 0) * 100  # Convert to percentage
                feedback_count = batch_data.get('total_corrections', 0)
                docs_with_feedback = batch_data.get('documents_with_feedback', 0)
                
                batches.append({
                    'batch_number': batch_num,
                    'accuracy': accuracy,
                    'documents': [],  # Not needed for visualization
                    'feedback_count': feedback_count
                })
                
                print(f"    Batch {batch_num}: {accuracy:.2f}% accuracy, {feedback_count} corrections")
            
            if batches:
                learning_curves.append({
                    'template_id': template.id,
                    'template_name': template.name,
                    'template_type': _infer_template_type(template.name),
                    'batches': batches,
                    'final_accuracy': batches[-1]['accuracy'] if batches else 0,
                    'improvement': (batches[-1]['accuracy'] - batches[0]['accuracy']) if len(batches) > 1 else 0
                })
        except Exception as e:
            print(f"Error getting learning curve for template {template.id}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    return APIResponse.success({
        'learning_curves': learning_curves,
        'phase': experiment_phase
    })


@dashboard_bp.route('/baseline-comparison', methods=['GET'])
@handle_errors
@require_auth
def get_baseline_comparison():
    """
    Get baseline vs adaptive comparison
    Shows improvement from baseline to adaptive learning
    Load data from experiment results files
    """
    db = DatabaseManager()
    
    # Get all templates
    from database.repositories.template_repository import TemplateRepository
    template_repo = TemplateRepository(db)
    templates = template_repo.find_all()
    
    comparison_data = []
    
    # Load from experiment results files
    import json
    import os
    
    results_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'experiments', 'results')
    
    for template in templates:
        try:
            # Load baseline results
            baseline_file = os.path.join(results_dir, f'baseline_template_{template.id}.json')
            adaptive_file = os.path.join(results_dir, f'adaptive_template_{template.id}.json')
            
            if not os.path.exists(baseline_file) or not os.path.exists(adaptive_file):
                print(f"Template {template.id}: Missing experiment results files")
                continue
            
            with open(baseline_file, 'r') as f:
                baseline_data = json.load(f)
            
            with open(adaptive_file, 'r') as f:
                adaptive_data = json.load(f)
            
            # Extract metrics from experiment results
            baseline_metrics = baseline_data['metrics']
            adaptive_metrics = adaptive_data['metrics']
            
            baseline_acc = baseline_metrics['accuracy'] * 100
            baseline_precision = baseline_metrics['precision'] * 100
            baseline_recall = baseline_metrics['recall'] * 100
            baseline_f1 = baseline_metrics['f1_score'] * 100
            
            adaptive_acc = adaptive_metrics['accuracy'] * 100
            adaptive_precision = adaptive_metrics['precision'] * 100
            adaptive_recall = adaptive_metrics['recall'] * 100
            adaptive_f1 = adaptive_metrics['f1_score'] * 100
            
            improvement = adaptive_acc - baseline_acc
            batch_count = adaptive_data.get('total_batches', 7)
            total_docs = adaptive_data.get('total_documents', 35)
            
            print(f"Template {template.id} ({template.name}): Baseline={baseline_acc:.2f}%, Adaptive={adaptive_acc:.2f}%, Improvement=+{improvement:.2f}%")
            
            comparison_data.append({
                'template_id': template.id,
                'template_name': template.name,
                'template_type': _infer_template_type(template.name),
                'documents': total_docs,
                'baseline': {
                    'accuracy': baseline_acc,
                    'precision': baseline_precision,
                    'recall': baseline_recall,
                    'f1': baseline_f1
                },
                'adaptive': {
                    'accuracy': adaptive_acc,
                    'precision': adaptive_precision,
                    'recall': adaptive_recall,
                    'f1': adaptive_f1
                },
                'improvement': improvement,
                'batches': batch_count
            })
        except Exception as e:
            print(f"Error getting comparison for template {template.id}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Calculate averages
    if comparison_data:
        avg_baseline_acc = sum(t['baseline']['accuracy'] for t in comparison_data) / len(comparison_data)
        avg_adaptive_acc = sum(t['adaptive']['accuracy'] for t in comparison_data) / len(comparison_data)
        avg_improvement = avg_adaptive_acc - avg_baseline_acc
        avg_docs = sum(t['documents'] for t in comparison_data) / len(comparison_data)
        avg_batches = sum(t['batches'] for t in comparison_data) / len(comparison_data)
        
        summary = {
            'documents': int(avg_docs),
            'baseline_accuracy': avg_baseline_acc,
            'adaptive_accuracy': avg_adaptive_acc,
            'improvement': avg_improvement,
            'batches': int(avg_batches)
        }
    else:
        summary = None
    
    return APIResponse.success({
        'comparison': comparison_data,
        'summary': summary
    })
