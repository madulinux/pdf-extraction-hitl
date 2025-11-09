"""
Config Repository

Handles database operations for template configurations and learned patterns.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import json


class ConfigRepository:
    """Repository for template configuration data"""
    
    def __init__(self, db_manager):
        """
        Initialize repository
        
        Args:
            db_manager: DatabaseManager instance
        """
        self.db = db_manager
    
    # ========================================================================
    # Template Config Operations
    # ========================================================================
    
    def create_config(
        self,
        template_id: int,
        description: str = None,
        created_by: str = None
    ) -> int:
        """
        Create a new template configuration
        
        Args:
            template_id: Template ID
            description: Optional description
            created_by: User who created the config
            
        Returns:
            config_id: ID of created config
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get next version number
            cursor.execute("""
                SELECT COALESCE(MAX(version), 0) + 1 as next_version
                FROM template_configs
                WHERE template_id = ?
            """, (template_id,))
            
            next_version = cursor.fetchone()['next_version']
            
            # Deactivate previous configs
            cursor.execute("""
                UPDATE template_configs
                SET is_active = 0
                WHERE template_id = ? AND is_active = 1
            """, (template_id,))
            
            # Create new config
            cursor.execute("""
                INSERT INTO template_configs 
                (template_id, version, description, created_by, is_active)
                VALUES (?, ?, ?, ?, 1)
            """, (template_id, next_version, description, created_by))
            
            config_id = cursor.lastrowid
            
            # Log change
            self._log_config_change(
                cursor, config_id, 'created', created_by,
                {'version': next_version, 'description': description}
            )
            
            conn.commit()
            return config_id
            
        finally:
            conn.close()
    
    def get_active_config(self, template_id: int) -> Optional[Dict]:
        """
        Get active configuration for a template
        
        Args:
            template_id: Template ID
            
        Returns:
            Config dict or None
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM template_configs
                WHERE template_id = ? AND is_active = 1
                ORDER BY version DESC
                LIMIT 1
            """, (template_id,))
            
            row = cursor.fetchone()
            return dict(row) if row else None
            
        finally:
            conn.close()
    
    # ========================================================================
    # Field Config Operations
    # ========================================================================
    
    def create_field_config(
        self,
        config_id: int,
        field_name: str,
        field_type: str = None,
        base_pattern: str = None,
        confidence_threshold: float = 0.7,
        extraction_order: int = 0,
        is_required: bool = False,
        validation_rules: Dict = None
    ) -> int:
        """
        Create field configuration
        
        Args:
            config_id: Template config ID
            field_name: Field name
            field_type: Field type
            base_pattern: Base regex pattern
            confidence_threshold: Minimum confidence
            extraction_order: Order of extraction
            is_required: Whether field is required
            validation_rules: Validation rules dict
            
        Returns:
            field_config_id: ID of created field config
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO field_configs 
                (config_id, field_name, field_type, base_pattern, 
                 confidence_threshold, extraction_order, is_required, validation_rules)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                config_id, field_name, field_type, base_pattern,
                confidence_threshold, extraction_order, is_required,
                json.dumps(validation_rules) if validation_rules else None
            ))
            
            field_config_id = cursor.lastrowid
            conn.commit()
            return field_config_id
            
        finally:
            conn.close()
    
    def get_field_configs(self, config_id: int) -> List[Dict]:
        """
        Get all field configurations for a config
        
        Args:
            config_id: Template config ID
            
        Returns:
            List of field config dicts
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM field_configs
                WHERE config_id = ?
                ORDER BY extraction_order, field_name
            """, (config_id,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        finally:
            conn.close()
    
    def get_field_config_by_name(
        self,
        config_id: int,
        field_name: str
    ) -> Optional[Dict]:
        """
        Get specific field configuration
        
        Args:
            config_id: Template config ID
            field_name: Field name
            
        Returns:
            Field config dict or None
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM field_configs
                WHERE config_id = ? AND field_name = ?
            """, (config_id, field_name))
            
            row = cursor.fetchone()
            return dict(row) if row else None
            
        finally:
            conn.close()
    
    # ========================================================================
    # Field Location Operations
    # ========================================================================
    
    def create_field_location(
        self,
        field_config_id: int,
        page: int,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
        label: str = None,
        location_index: int = 0
    ) -> int:
        """
        Create field location
        
        Args:
            field_config_id: Field config ID
            page: Page number
            x0, y0, x1, y1: Bounding box coordinates
            label: Context label
            location_index: Location index for multi-location fields
            
        Returns:
            location_id: ID of created location
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO field_locations 
                (field_config_id, page, x0, y0, x1, y1, label, location_index)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (field_config_id, page, x0, y0, x1, y1, label, location_index))
            
            location_id = cursor.lastrowid
            conn.commit()
            return location_id
            
        finally:
            conn.close()
    
    def get_field_locations(self, field_config_id: int) -> List[Dict]:
        """
        Get all locations for a field
        
        Args:
            field_config_id: Field config ID
            
        Returns:
            List of location dicts
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM field_locations
                WHERE field_config_id = ?
                ORDER BY location_index, page
            """, (field_config_id,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        finally:
            conn.close()
    
    # ========================================================================
    # Learned Pattern Operations (Adaptive!)
    # ========================================================================
    
    def add_learned_pattern(
        self,
        field_config_id: int,
        pattern: str,
        pattern_type: str,
        description: str = None,
        frequency: int = 0,
        match_rate: float = None,
        priority: int = 0,
        examples: List[str] = None,
        metadata: Dict = None
    ) -> int:
        """
        Add a learned pattern
        
        Args:
            field_config_id: Field config ID
            pattern: Regex pattern
            pattern_type: Type (token_shape, delimiter, word_count, custom)
            description: Pattern description
            frequency: How many times seen in feedback
            match_rate: Success rate
            priority: Priority (higher = tried first)
            examples: Example values
            metadata: Additional metadata
            
        Returns:
            pattern_id: ID of created pattern
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO learned_patterns 
                (field_config_id, pattern, pattern_type, description, 
                 frequency, match_rate, priority, examples, metadata, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                field_config_id, pattern, pattern_type, description,
                frequency, match_rate, priority,
                json.dumps(examples) if examples else None,
                json.dumps(metadata) if metadata else None
            ))
            
            pattern_id = cursor.lastrowid
            conn.commit()
            return pattern_id
            
        finally:
            conn.close()
    
    def get_learned_patterns(
        self,
        field_config_id: int,
        active_only: bool = True
    ) -> List[Dict]:
        """
        Get learned patterns for a field
        
        Args:
            field_config_id: Field config ID
            active_only: Only return active patterns
            
        Returns:
            List of pattern dicts
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            query = """
                SELECT * FROM learned_patterns
                WHERE field_config_id = ?
            """
            
            if active_only:
                query += " AND is_active = 1"
            
            query += " ORDER BY priority DESC, match_rate DESC, frequency DESC"
            
            cursor.execute(query, (field_config_id,))
            
            rows = cursor.fetchall()
            patterns = []
            
            for row in rows:
                pattern_dict = dict(row)
                # Parse JSON fields
                if pattern_dict.get('examples'):
                    pattern_dict['examples'] = json.loads(pattern_dict['examples'])
                if pattern_dict.get('metadata'):
                    pattern_dict['metadata'] = json.loads(pattern_dict['metadata'])
                patterns.append(pattern_dict)
            
            return patterns
            
        finally:
            conn.close()
    
    def update_pattern_usage(
        self,
        pattern_id: int,
        was_successful: bool = True
    ) -> None:
        """
        Update pattern usage statistics
        
        Args:
            pattern_id: Pattern ID
            was_successful: Whether pattern matched successfully
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE learned_patterns
                SET usage_count = usage_count + 1,
                    success_count = success_count + ?,
                    last_used_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (1 if was_successful else 0, pattern_id))
            
            conn.commit()
            
        finally:
            conn.close()
    
    def deactivate_pattern(self, pattern_id: int) -> None:
        """
        Deactivate a learned pattern
        
        Args:
            pattern_id: Pattern ID
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE learned_patterns
                SET is_active = 0
                WHERE id = ?
            """, (pattern_id,))
            
            conn.commit()
            
        finally:
            conn.close()
    
    # ========================================================================
    # Pattern Learning Jobs
    # ========================================================================
    
    def create_learning_job(
        self,
        template_id: int,
        field_name: str = None,
        job_type: str = 'auto'
    ) -> int:
        """
        Create a pattern learning job
        
        Args:
            template_id: Template ID
            field_name: Optional specific field
            job_type: Job type (manual, auto, scheduled)
            
        Returns:
            job_id: ID of created job
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO pattern_learning_jobs 
                (template_id, field_name, job_type, status)
                VALUES (?, ?, ?, 'pending')
            """, (template_id, field_name, job_type))
            
            job_id = cursor.lastrowid
            conn.commit()
            return job_id
            
        finally:
            conn.close()
    
    def update_learning_job(
        self,
        job_id: int,
        status: str = None,
        feedback_count: int = None,
        patterns_discovered: int = None,
        patterns_applied: int = None,
        error_message: str = None,
        result_summary: Dict = None
    ) -> None:
        """
        Update learning job status
        
        Args:
            job_id: Job ID
            status: New status
            feedback_count: Number of feedback analyzed
            patterns_discovered: Number of patterns discovered
            patterns_applied: Number of patterns applied
            error_message: Error message if failed
            result_summary: Result summary dict
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            updates = []
            params = []
            
            if status:
                updates.append("status = ?")
                params.append(status)
                
                if status in ['completed', 'failed']:
                    updates.append("completed_at = CURRENT_TIMESTAMP")
            
            if feedback_count is not None:
                updates.append("feedback_count = ?")
                params.append(feedback_count)
            
            if patterns_discovered is not None:
                updates.append("patterns_discovered = ?")
                params.append(patterns_discovered)
            
            if patterns_applied is not None:
                updates.append("patterns_applied = ?")
                params.append(patterns_applied)
            
            if error_message:
                updates.append("error_message = ?")
                params.append(error_message)
            
            if result_summary:
                updates.append("result_summary = ?")
                params.append(json.dumps(result_summary))
            
            if updates:
                params.append(job_id)
                query = f"""
                    UPDATE pattern_learning_jobs
                    SET {', '.join(updates)}
                    WHERE id = ?
                """
                cursor.execute(query, params)
                conn.commit()
            
        finally:
            conn.close()
    
    def get_recent_jobs(
        self,
        template_id: int,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get recent learning jobs
        
        Args:
            template_id: Template ID
            limit: Maximum number of jobs
            
        Returns:
            List of job dicts
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM pattern_learning_jobs
                WHERE template_id = ?
                ORDER BY started_at DESC
                LIMIT ?
            """, (template_id, limit))
            
            rows = cursor.fetchall()
            jobs = []
            
            for row in rows:
                job_dict = dict(row)
                if job_dict.get('result_summary'):
                    job_dict['result_summary'] = json.loads(job_dict['result_summary'])
                jobs.append(job_dict)
            
            return jobs
            
        finally:
            conn.close()
    
    # ========================================================================
    # Helper Methods
    # ========================================================================
    
    def _log_config_change(
        self,
        cursor,
        config_id: int,
        change_type: str,
        changed_by: str,
        changes: Dict
    ) -> None:
        """Log configuration change"""
        cursor.execute("""
            INSERT INTO config_change_history 
            (config_id, change_type, changed_by, changes)
            VALUES (?, ?, ?, ?)
        """, (config_id, change_type, changed_by, json.dumps(changes)))
    
    def get_config_history(
        self,
        config_id: int,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get configuration change history
        
        Args:
            config_id: Config ID
            limit: Maximum number of records
            
        Returns:
            List of change history dicts
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM config_change_history
                WHERE config_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (config_id, limit))
            
            rows = cursor.fetchall()
            history = []
            
            for row in rows:
                hist_dict = dict(row)
                if hist_dict.get('changes'):
                    hist_dict['changes'] = json.loads(hist_dict['changes'])
                history.append(hist_dict)
            
            return history
            
        finally:
            conn.close()
