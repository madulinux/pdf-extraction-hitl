#!/usr/bin/env python3
"""
Fix Feedback Data Consistency
Applies consistent cleaning rules to all feedback data
"""
import sys
sys.path.insert(0, '/Users/madulinux/Documents/S2 UNAS/TESIS/Project/backend')

import re
from database.db_manager import DatabaseManager

class FeedbackCleaner:
    """Clean and standardize feedback data"""
    
    def __init__(self):
        self.db = DatabaseManager()
        
    def analyze_inconsistencies(self, template_id: int = 1):
        """Analyze feedback for inconsistencies"""
        print("=" * 100)
        print("🔍 ANALYZING FEEDBACK INCONSISTENCIES")
        print("=" * 100)
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Get all feedback
        cursor.execute('''
            SELECT 
                f.id, f.field_name, f.original_value, f.corrected_value
            FROM feedback f
            JOIN documents d ON f.document_id = d.id
            WHERE d.template_id = ?
            ORDER BY f.field_name, f.created_at
        ''', (template_id,))
        
        feedbacks = cursor.fetchall()
        conn.close()
        
        # Analyze patterns by field
        field_patterns = {}
        
        for fb_id, field_name, original, corrected in feedbacks:
            if field_name not in field_patterns:
                field_patterns[field_name] = {
                    'total': 0,
                    'has_parentheses_original': 0,
                    'has_parentheses_corrected': 0,
                    'has_date_original': 0,
                    'has_date_corrected': 0,
                    'has_comma_original': 0,
                    'has_comma_corrected': 0,
                    'examples': []
                }
            
            patterns = field_patterns[field_name]
            patterns['total'] += 1
            
            # Check for parentheses
            if original and '(' in original:
                patterns['has_parentheses_original'] += 1
            if corrected and '(' in corrected:
                patterns['has_parentheses_corrected'] += 1
            
            # Check for dates
            date_pattern = r'\d{1,2}\s+\w+\s+\d{4}'
            if original and re.search(date_pattern, original):
                patterns['has_date_original'] += 1
            if corrected and re.search(date_pattern, corrected):
                patterns['has_date_corrected'] += 1
            
            # Check for commas
            if original and ',' in original:
                patterns['has_comma_original'] += 1
            if corrected and ',' in corrected:
                patterns['has_comma_corrected'] += 1
            
            # Store examples
            if len(patterns['examples']) < 5:
                patterns['examples'].append({
                    'id': fb_id,
                    'original': original,
                    'corrected': corrected
                })
        
        # Print analysis
        print("\n📊 INCONSISTENCY ANALYSIS BY FIELD")
        print("=" * 100)
        
        for field_name, patterns in sorted(field_patterns.items()):
            print(f"\n🔍 Field: {field_name}")
            print(f"   Total corrections: {patterns['total']}")
            
            # Parentheses analysis
            if patterns['has_parentheses_original'] > 0:
                removal_rate = (patterns['has_parentheses_original'] - patterns['has_parentheses_corrected']) / patterns['has_parentheses_original'] * 100
                print(f"   Parentheses: {patterns['has_parentheses_original']} original → {patterns['has_parentheses_corrected']} corrected ({removal_rate:.1f}% removed)")
                
                if 10 < removal_rate < 90:
                    print(f"   ⚠️  INCONSISTENT: Sometimes removed, sometimes kept!")
            
            # Date analysis
            if patterns['has_date_original'] > 0:
                removal_rate = (patterns['has_date_original'] - patterns['has_date_corrected']) / patterns['has_date_original'] * 100
                print(f"   Dates: {patterns['has_date_original']} original → {patterns['has_date_corrected']} corrected ({removal_rate:.1f}% removed)")
                
                if 10 < removal_rate < 90:
                    print(f"   ⚠️  INCONSISTENT: Sometimes removed, sometimes kept!")
            
            # Show examples
            print(f"\n   Examples:")
            for ex in patterns['examples'][:3]:
                orig = str(ex['original'])[:50] if ex['original'] else "(empty)"
                corr = str(ex['corrected'])[:50] if ex['corrected'] else "(empty)"
                print(f"      {orig} → {corr}")
        
        return field_patterns
    
    def define_cleaning_rules(self):
        """Define consistent cleaning rules for each field"""
        return {
            'supervisor_name': {
                'remove_parentheses': True,
                'remove_titles': False,  # Keep M.Pd, S.Farm, etc.
                'trim_whitespace': True,
            },
            'chairman_name': {
                'remove_parentheses': True,
                'remove_titles': False,
                'trim_whitespace': True,
            },
            'issue_place': {
                'remove_dates': True,  # Remove ", DD Month YYYY"
                'remove_parentheses': False,
                'trim_whitespace': True,
            },
            'event_name': {
                'remove_prefixes': False,  # Keep "Workshop", etc.
                'trim_whitespace': True,
            },
            'event_location': {
                'trim_whitespace': True,
            },
            'event_date': {
                'standardize_format': True,  # DD Month YYYY
                'trim_whitespace': True,
            },
            'issue_date': {
                'standardize_format': True,
                'trim_whitespace': True,
            },
            'recipient_name': {
                'remove_parentheses': True,
                'trim_whitespace': True,
            },
        }
    
    def apply_cleaning_rule(self, field_name: str, value: str, rules: dict) -> str:
        """Apply cleaning rules to a value"""
        if not value:
            return value
        
        cleaned = value
        field_rules = rules.get(field_name, {})
        
        # Remove parentheses
        if field_rules.get('remove_parentheses'):
            cleaned = re.sub(r'[()]', '', cleaned)
        
        # Remove dates (format: ", DD Month YYYY")
        if field_rules.get('remove_dates'):
            cleaned = re.sub(r',\s*\d{1,2}\s+\w+\s+\d{4}', '', cleaned)
        
        # Trim whitespace
        if field_rules.get('trim_whitespace'):
            cleaned = ' '.join(cleaned.split())
        
        return cleaned
    
    def preview_changes(self, template_id: int = 1, limit: int = 20):
        """Preview what changes would be made"""
        print("\n" + "=" * 100)
        print("👁️  PREVIEW CHANGES (First 20)")
        print("=" * 100)
        
        rules = self.define_cleaning_rules()
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                f.id, f.field_name, f.corrected_value
            FROM feedback f
            JOIN documents d ON f.document_id = d.id
            WHERE d.template_id = ?
            ORDER BY f.created_at DESC
            LIMIT ?
        ''', (template_id, limit))
        
        feedbacks = cursor.fetchall()
        conn.close()
        
        changes = []
        
        print(f"\n{'ID':<6} {'Field':<25} {'Current':<35} {'Cleaned':<35}")
        print("-" * 100)
        
        for fb_id, field_name, current_value in feedbacks:
            cleaned_value = self.apply_cleaning_rule(field_name, current_value, rules)
            
            if cleaned_value != current_value:
                changes.append((fb_id, field_name, current_value, cleaned_value))
                
                curr = str(current_value)[:34] if current_value else "(empty)"
                clean = str(cleaned_value)[:34] if cleaned_value else "(empty)"
                print(f"{fb_id:<6} {field_name:<25} {curr:<35} {clean:<35}")
        
        print(f"\n📊 Summary: {len(changes)} changes out of {len(feedbacks)} feedback items ({len(changes)/len(feedbacks)*100:.1f}%)")
        
        return changes
    
    def apply_fixes(self, template_id: int = 1, dry_run: bool = True):
        """Apply cleaning rules to all feedback"""
        print("\n" + "=" * 100)
        if dry_run:
            print("🔍 DRY RUN MODE (No changes will be made)")
        else:
            print("⚠️  APPLYING FIXES (Database will be modified!)")
        print("=" * 100)
        
        rules = self.define_cleaning_rules()
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Get all feedback
        cursor.execute('''
            SELECT 
                f.id, f.field_name, f.corrected_value
            FROM feedback f
            JOIN documents d ON f.document_id = d.id
            WHERE d.template_id = ?
        ''', (template_id,))
        
        feedbacks = cursor.fetchall()
        
        changes_made = 0
        
        for fb_id, field_name, current_value in feedbacks:
            cleaned_value = self.apply_cleaning_rule(field_name, current_value, rules)
            
            if cleaned_value != current_value:
                if not dry_run:
                    cursor.execute('''
                        UPDATE feedback
                        SET corrected_value = ?
                        WHERE id = ?
                    ''', (cleaned_value, fb_id))
                
                changes_made += 1
        
        if not dry_run:
            conn.commit()
            print(f"\n✅ Applied {changes_made} changes to database")
        else:
            print(f"\n📊 Would apply {changes_made} changes (dry run)")
        
        conn.close()
        
        return changes_made

if __name__ == '__main__':
    cleaner = FeedbackCleaner()
    
    # Step 1: Analyze inconsistencies
    print("\n🔍 STEP 1: Analyze Inconsistencies")
    cleaner.analyze_inconsistencies(template_id=1)
    
    # Step 2: Preview changes
    print("\n\n👁️  STEP 2: Preview Changes")
    cleaner.preview_changes(template_id=1, limit=50)
    
    # Step 3: Ask for confirmation
    print("\n\n" + "=" * 100)
    print("⚠️  WARNING: This will modify feedback data in the database!")
    print("=" * 100)
    response = input("\nApply fixes? (yes/no): ")
    
    if response.lower() == 'yes':
        print("\n🔧 Applying fixes...")
        changes = cleaner.apply_fixes(template_id=1, dry_run=False)
        print(f"\n✅ Done! Applied {changes} changes.")
        print("\n💡 Next steps:")
        print("   1. Retrain model with clean data")
        print("   2. Test extraction accuracy")
        print("   3. Monitor for improvements")
    else:
        print("\n❌ Cancelled. No changes made.")
