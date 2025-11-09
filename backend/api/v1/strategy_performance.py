"""
Strategy Performance API Endpoints

Provides endpoints for retrieving and analyzing extraction strategy performance.
"""
from flask import Blueprint, request, jsonify
from core.extraction.strategy_performance_service import StrategyPerformanceService
# from api.middleware.auth import require_auth  # TODO: Re-enable after testing

strategy_performance_bp = Blueprint('strategy_performance', __name__, url_prefix='/api/v1')


@strategy_performance_bp.route('/templates/<int:template_id>/strategy-performance', methods=['GET'])
# @require_auth  # TODO: Re-enable after testing
def get_template_performance(template_id: int):
    """
    Get all strategy performance data for a template
    ---
    tags:
      - Strategy Performance
    parameters:
      - name: template_id
        in: path
        type: integer
        required: true
        description: Template ID
    responses:
      200:
        description: List of all performance records
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                  template_id:
                    type: integer
                  field_name:
                    type: string
                  strategy_type:
                    type: string
                  accuracy:
                    type: number
                  total_extractions:
                    type: integer
                  correct_extractions:
                    type: integer
            count:
              type: integer
      500:
        description: Server error
    """
    try:
        service = StrategyPerformanceService()
        performance = service.get_template_performance(template_id)
        
        return jsonify({
            'success': True,
            'data': performance,
            'count': len(performance)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@strategy_performance_bp.route('/templates/<int:template_id>/strategy-performance/stats', methods=['GET'])
# # @require_auth  # TODO: Re-enable after testing  # Temporarily disabled for testing
def get_strategy_stats(template_id: int):
    """
    Get aggregated statistics for each strategy
    
    GET /api/v1/templates/1/strategy-performance/stats
    
    Returns:
        Aggregated statistics per strategy (avg accuracy, best/worst fields, etc.)
    """
    try:
        service = StrategyPerformanceService()
        stats = service.get_strategy_stats(template_id)
        
        return jsonify({
            'success': True,
            'data': stats,
            'template_id': template_id
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@strategy_performance_bp.route('/templates/<int:template_id>/strategy-performance/fields/<field_name>', methods=['GET'])
# @require_auth  # TODO: Re-enable after testing
def get_field_performance(template_id: int, field_name: str):
    """
    Get performance comparison for a specific field
    
    GET /api/v1/templates/1/strategy-performance/fields/recipient_name
    
    Returns:
        Performance data for all strategies for the specified field
    """
    try:
        service = StrategyPerformanceService()
        comparison = service.get_field_comparison(template_id, field_name)
        
        return jsonify({
            'success': True,
            'data': comparison
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@strategy_performance_bp.route('/templates/<int:template_id>/strategy-performance/comparison', methods=['GET'])
# @require_auth  # TODO: Re-enable after testing
def get_all_fields_comparison(template_id: int):
    """
    Get strategy comparison for all fields
    
    GET /api/v1/templates/1/strategy-performance/comparison
    
    Returns:
        Comparison of strategies for each field, showing which strategy performs best
    """
    try:
        service = StrategyPerformanceService()
        comparisons = service.get_all_fields_comparison(template_id)
        
        return jsonify({
            'success': True,
            'data': comparisons,
            'template_id': template_id,
            'total_fields': len(comparisons)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@strategy_performance_bp.route('/templates/<int:template_id>/strategy-performance/best', methods=['GET'])
# @require_auth  # TODO: Re-enable after testing
def get_best_strategies(template_id: int):
    """
    Get best performing strategy for each field
    
    GET /api/v1/templates/1/strategy-performance/best
    
    Returns:
        Dictionary mapping field names to their best performing strategy
    """
    try:
        service = StrategyPerformanceService()
        comparisons = service.get_all_fields_comparison(template_id)
        
        # Extract best strategy for each field
        best_strategies = {
            comp['field_name']: {
                'strategy': comp['best_strategy'],
                'accuracy': comp['best_accuracy']
            }
            for comp in comparisons
            if comp['best_strategy']
        }
        
        return jsonify({
            'success': True,
            'data': best_strategies,
            'template_id': template_id
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@strategy_performance_bp.route('/templates/<int:template_id>/strategy-performance/<strategy_type>', methods=['GET'])
# @require_auth  # TODO: Re-enable after testing
def get_strategy_fields(template_id: int, strategy_type: str):
    """
    Get all fields and their performance for a specific strategy
    
    GET /api/v1/templates/1/strategy-performance/crf
    
    Returns:
        Performance data for all fields using the specified strategy
    """
    try:
        service = StrategyPerformanceService()
        all_performance = service.get_template_performance(template_id)
        
        # Filter by strategy type
        strategy_performance = [
            p for p in all_performance
            if p['strategy_type'] == strategy_type
        ]
        
        # Sort by accuracy descending
        strategy_performance.sort(key=lambda x: x['accuracy'], reverse=True)
        
        # Calculate summary
        if strategy_performance:
            avg_accuracy = sum(p['accuracy'] for p in strategy_performance) / len(strategy_performance)
            total_extractions = sum(p['total_extractions'] for p in strategy_performance)
            total_correct = sum(p['correct_extractions'] for p in strategy_performance)
        else:
            avg_accuracy = 0.0
            total_extractions = 0
            total_correct = 0
        
        return jsonify({
            'success': True,
            'data': {
                'strategy_type': strategy_type,
                'fields': strategy_performance,
                'summary': {
                    'avg_accuracy': round(avg_accuracy * 100, 2),
                    'total_fields': len(strategy_performance),
                    'total_extractions': total_extractions,
                    'total_correct': total_correct
                }
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
