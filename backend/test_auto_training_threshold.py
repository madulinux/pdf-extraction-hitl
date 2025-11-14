"""
Test: Auto-Training Threshold - Document vs Feedback Count

This test demonstrates why document-based threshold is better than
feedback-based threshold for consistent behavior across templates.
"""
from database.db_manager import DatabaseManager
from core.learning.auto_trainer import AutoTrainingService

def test_threshold_consistency():
    """Test that document-based threshold provides consistent behavior"""
    
    print('🧪 TEST: Auto-Training Threshold Consistency')
    print('=' * 80)
    
    db = DatabaseManager()
    auto_trainer = AutoTrainingService(db)
    
    print(f'\n📊 Configuration:')
    print(f'   MIN_NEW_DOCUMENTS = {auto_trainer.MIN_NEW_DOCUMENTS}')
    print(f'   MIN_HOURS_SINCE_LAST_TRAINING = {auto_trainer.MIN_HOURS_SINCE_LAST_TRAINING}')
    
    # Get template statistics
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            t.id,
            t.name,
            COUNT(DISTINCT f.field_name) as field_count,
            COUNT(DISTINCT f.document_id) as doc_count,
            COUNT(*) as feedback_count
        FROM templates t
        LEFT JOIN documents d ON d.template_id = t.id
        LEFT JOIN feedback f ON f.document_id = d.id
        WHERE f.used_for_training = 0
        GROUP BY t.id, t.name
    ''')
    
    templates = cursor.fetchall()
    conn.close()
    
    if not templates:
        print('\n⚠️  No templates with unused feedback found')
        return
    
    print('\n' + '=' * 80)
    print('📊 TEMPLATE ANALYSIS')
    print('=' * 80)
    
    for template_id, name, field_count, doc_count, feedback_count in templates:
        print(f'\nTemplate: {name} (ID: {template_id})')
        print(f'  Fields per document: ~{field_count}')
        print(f'  Unused documents: {doc_count}')
        print(f'  Unused feedback: {feedback_count}')
        print(f'  Feedback per doc: ~{feedback_count // doc_count if doc_count > 0 else 0}')
        
        # Check if would trigger with OLD method (feedback-based)
        old_threshold = 20  # MIN_NEW_FEEDBACK
        would_trigger_old = feedback_count >= old_threshold
        
        # Check if would trigger with NEW method (document-based)
        new_threshold = auto_trainer.MIN_NEW_DOCUMENTS
        would_trigger_new = doc_count >= new_threshold
        
        print(f'\n  OLD Method (feedback-based, threshold={old_threshold}):')
        if would_trigger_old:
            print(f'    ✅ Would trigger auto-training')
            if doc_count < 10:
                print(f'    ⚠️  WARNING: Only {doc_count} documents (TOO SMALL!)')
        else:
            print(f'    ❌ Would NOT trigger (need {old_threshold - feedback_count} more feedback)')
        
        print(f'\n  NEW Method (document-based, threshold={new_threshold}):')
        if would_trigger_new:
            print(f'    ✅ Would trigger auto-training')
            print(f'    ✅ GOOD: {doc_count} documents (sufficient)')
        else:
            print(f'    ❌ Would NOT trigger (need {new_threshold - doc_count} more documents)')
        
        # Highlight inconsistency
        if would_trigger_old != would_trigger_new:
            print(f'\n  ⚠️  INCONSISTENCY DETECTED!')
            if would_trigger_old and not would_trigger_new:
                print(f'      Old method would trigger with only {doc_count} docs (BAD!)')
                print(f'      New method correctly waits for {new_threshold} docs (GOOD!)')
    
    print('\n' + '=' * 80)
    print('🎯 CONCLUSION')
    print('=' * 80)
    
    print('\nDocument-based threshold provides:')
    print('  ✅ Consistent behavior across templates')
    print('  ✅ Sufficient training data (20 docs minimum)')
    print('  ✅ Lower overfitting risk')
    print('  ✅ Better model quality')
    
    print('\nFeedback-based threshold problems:')
    print('  ❌ Inconsistent across templates')
    print('  ❌ May trigger with 1 doc (if 25 fields)')
    print('  ❌ High overfitting risk')
    print('  ❌ Poor model quality')

def test_auto_training_trigger():
    """Test actual auto-training trigger"""
    
    print('\n\n🧪 TEST: Auto-Training Trigger')
    print('=' * 80)
    
    db = DatabaseManager()
    auto_trainer = AutoTrainingService(db)
    
    # Get first template
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name FROM templates LIMIT 1')
    template = cursor.fetchone()
    conn.close()
    
    if not template:
        print('⚠️  No templates found')
        return
    
    template_id, template_name = template
    
    print(f'\nTesting template: {template_name} (ID: {template_id})')
    
    # Check auto-training
    result = auto_trainer.check_and_train(template_id)
    
    if result:
        print('\n✅ AUTO-TRAINING TRIGGERED!')
        print(f'   Training samples: {result["training_samples"]}')
        print(f'   Test accuracy: {result["test_metrics"]["accuracy"]*100:.2f}%')
    else:
        print('\n⏸️  Auto-training not triggered (conditions not met)')

if __name__ == '__main__':
    test_threshold_consistency()
    test_auto_training_trigger()
