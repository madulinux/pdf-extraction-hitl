"""
Pattern Manager Service
Manages regex patterns for field extraction with learning capability
Implements separation of concerns for pattern management
"""
from typing import Dict, List, Optional, Tuple
from database.db_manager import DatabaseManager

class PatternManager:
    """
    Manages regex patterns with adaptive learning from user usage
    Separates pattern logic from template analysis
    """
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager or DatabaseManager()
        self._default_patterns = self._get_default_patterns()
    
    def _get_default_patterns(self) -> Dict[str, str]:
        """Default fallback patterns"""
        return {
            'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            'phone': r'[\d\-\+\(\)\s]{10,}',
            'telepon': r'[\d\-\+\(\)\s]{10,}',
            'hp': r'[\d\-\+\(\)\s]{10,}',
            'tanggal': r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}',
            'date': r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}',
            'nik': r'\d{16}',
            'ktp': r'\d{16}',
            'nomor': r'[A-Za-z0-9/\-\.]+',
            'number': r'[A-Za-z0-9/\-\.]+',
            'kode': r'[A-Za-z0-9/\-\.]+',
            'jumlah': r'\d+',
            'qty': r'\d+',
            'quantity': r'\d+',
            'harga': r'[\d\.,]+',
            'price': r'[\d\.,]+',
            'rate': r'[\d\.,]+',
            'amount': r'[\d\.,]+',
            'nama': r'[A-Za-z\s\.]+',
            'name': r'[A-Za-z\s\.]+',
            'alamat': r'[A-Za-z0-9\s\.,\-]+',
            'address': r'[A-Za-z0-9\s\.,\-]+',
        }
    
    def get_pattern_for_field(self, field_name: str, user_id: Optional[int] = None) -> str:
        """
        Get best regex pattern for a field name
        Priority: User's learned pattern > Global learned pattern > Default pattern
        
        Args:
            field_name: Name of the field
            user_id: Optional user ID for personalized patterns
            
        Returns:
            Regex pattern string
        """
        field_lower = field_name.lower()
        
        # 1. Try user-specific learned pattern (highest priority)
        if user_id:
            user_pattern = self._get_user_pattern(field_lower, user_id)
            if user_pattern:
                return user_pattern
        
        # 2. Try global learned pattern (from all users)
        global_pattern = self._get_global_pattern(field_lower)
        if global_pattern:
            return global_pattern
        
        # 3. Try default patterns (keyword matching)
        # for keyword, pattern in self._default_patterns.items():
        #     if keyword in field_lower:
        #         return pattern
        
        # 4. Fallback: any text
        return r'.+'
    
    def _get_user_pattern(self, field_name: str, user_id: int) -> Optional[str]:
        """Get user-specific learned pattern"""
        try:
            query = """
                SELECT regex_pattern, usage_count 
                FROM field_patterns 
                WHERE field_name = ? AND user_id = ?
                ORDER BY usage_count DESC, updated_at DESC
                LIMIT 1
            """
            result = self.db.execute_query(query, (field_name, user_id))
            if result:
                return result[0]['regex_pattern']
        except Exception as e:
            print(f"Error getting user pattern: {e}")
        return None
    
    def _get_global_pattern(self, field_name: str) -> Optional[str]:
        """Get most commonly used pattern across all users"""
        try:
            query = """
                SELECT regex_pattern, SUM(usage_count) as total_usage
                FROM field_patterns 
                WHERE field_name = ?
                GROUP BY regex_pattern
                ORDER BY total_usage DESC, MAX(updated_at) DESC
                LIMIT 1
            """
            result = self.db.execute_query(query, (field_name,))
            if result:
                return result[0]['regex_pattern']
        except Exception as e:
            print(f"Error getting global pattern: {e}")
        return None
    
    def learn_pattern(self, field_name: str, regex_pattern: str, user_id: Optional[int] = None) -> bool:
        """
        Learn/update pattern from user usage
        Increments usage count for adaptive learning
        
        Args:
            field_name: Name of the field
            regex_pattern: Regex pattern used
            user_id: Optional user ID
            
        Returns:
            Success status
        """
        try:
            field_lower = field_name.lower()
            
            # Check if pattern already exists
            query = """
                SELECT id, usage_count 
                FROM field_patterns 
                WHERE field_name = ? AND regex_pattern = ? AND user_id = ?
            """
            result = self.db.execute_query(query, (field_lower, regex_pattern, user_id))
            
            if result:
                # Update existing pattern - increment usage
                pattern_id = result[0]['id']
                new_count = result[0]['usage_count'] + 1
                update_query = """
                    UPDATE field_patterns 
                    SET usage_count = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """
                self.db.execute_update(update_query, (new_count, pattern_id))
            else:
                # Insert new pattern
                insert_query = """
                    INSERT INTO field_patterns (field_name, regex_pattern, user_id, usage_count)
                    VALUES (?, ?, ?, 1)
                """
                self.db.execute_update(insert_query, (field_lower, regex_pattern, user_id))
            
            return True
        except Exception as e:
            print(f"Error learning pattern: {e}")
            return False
    
    def get_pattern_suggestions(self, field_name: str, user_id: Optional[int] = None, limit: int = 5) -> List[Dict]:
        """
        Get pattern suggestions for a field
        Returns multiple options sorted by usage
        
        Args:
            field_name: Name of the field
            user_id: Optional user ID for personalized suggestions
            limit: Maximum number of suggestions
            
        Returns:
            List of pattern suggestions with metadata
        """
        suggestions = []
        field_lower = field_name.lower()
        
        try:
            # Get learned patterns
            query = """
                SELECT regex_pattern, usage_count, user_id,
                       CASE WHEN user_id = ? THEN 1 ELSE 0 END as is_user_pattern
                FROM field_patterns 
                WHERE field_name = ?
                ORDER BY is_user_pattern DESC, usage_count DESC, updated_at DESC
                LIMIT ?
            """
            results = self.db.execute_query(query, (user_id, field_lower, limit))
            
            for row in results:
                suggestions.append({
                    'pattern': row['regex_pattern'],
                    'usage_count': row['usage_count'],
                    'source': 'user' if row['is_user_pattern'] else 'global',
                    'confidence': min(0.9, 0.5 + (row['usage_count'] * 0.1))
                })
        except Exception as e:
            print(f"Error getting pattern suggestions: {e}")
        
        # Add default pattern if not in suggestions
        default_pattern = None
        # for keyword, pattern in self._default_patterns.items():
        #     if keyword in field_lower:
        #         default_pattern = pattern
        #         break
        
        if default_pattern and not any(s['pattern'] == default_pattern for s in suggestions):
            suggestions.append({
                'pattern': default_pattern,
                'usage_count': 0,
                'source': 'default',
                'confidence': 0.5
            })
        
        return suggestions[:limit]
    
    def update_pattern(self, field_name: str, old_pattern: str, new_pattern: str, 
                      user_id: Optional[int] = None) -> bool:
        """
        Update a pattern (e.g., when user edits it)
        
        Args:
            field_name: Name of the field
            old_pattern: Current pattern
            new_pattern: New pattern to use
            user_id: Optional user ID
            
        Returns:
            Success status
        """
        # Learn the new pattern
        return self.learn_pattern(field_name, new_pattern, user_id)
    
    def get_field_statistics(self, field_name: Optional[str] = None) -> List[Dict]:
        """
        Get statistics about field patterns
        Useful for analytics and debugging
        
        Args:
            field_name: Optional field name to filter
            
        Returns:
            List of statistics
        """
        try:
            if field_name:
                query = """
                    SELECT field_name, regex_pattern, 
                           COUNT(DISTINCT user_id) as user_count,
                           SUM(usage_count) as total_usage,
                           MAX(updated_at) as last_used
                    FROM field_patterns 
                    WHERE field_name = ?
                    GROUP BY field_name, regex_pattern
                    ORDER BY total_usage DESC
                """
                return self.db.execute_query(query, (field_name.lower(),))
            else:
                query = """
                    SELECT field_name, 
                           COUNT(DISTINCT regex_pattern) as pattern_count,
                           COUNT(DISTINCT user_id) as user_count,
                           SUM(usage_count) as total_usage
                    FROM field_patterns 
                    GROUP BY field_name
                    ORDER BY total_usage DESC
                    LIMIT 20
                """
                return self.db.execute_query(query)
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return []
