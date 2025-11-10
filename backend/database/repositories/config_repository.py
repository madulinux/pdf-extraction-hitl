"""
Config Repository

Handles database operations for template configurations and learned patterns.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import logging


class ConfigRepository:
    """Repository for template configuration data"""
    
    def __init__(self, db_manager):
        """
        Initialize repository
        
        Args:
            db_manager: DatabaseManager instance
        """
        self.db = db_manager
        self.logger = logging.getLogger(self.__class__.__name__)
    
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
    
    def create_field_context(
        self,
        field_location_id: int,
        label: str = '',
        label_position: Dict = None,
        words_before: List[Dict] = None,
        words_after: List[Dict] = None,
        next_field_y: float = None  # ✅ NEW
    ) -> int:
        """
        Create context information for a field location
        
        Args:
            field_location_id: Field location ID
            label: Label text (e.g., "Sertifikat:", "tanggal")
            label_position: Label bounding box {"x0": ..., "y0": ..., "x1": ..., "y1": ...}
            words_before: List of words before field [{"text": "...", "x": ..., "y": ...}, ...]
            words_after: List of words after field [{"text": "...", "x": ..., "y": ...}, ...]
            next_field_y: Y position of next field (for boundary detection)
            
        Returns:
            context_id: ID of created context
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO field_contexts 
                (field_location_id, label, label_position, words_before, words_after, next_field_y)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                field_location_id,
                label,
                json.dumps(label_position) if label_position else None,
                json.dumps(words_before) if words_before else None,
                json.dumps(words_after) if words_after else None,
                next_field_y  # ✅ NEW
            ))
            
            context_id = cursor.lastrowid
            conn.commit()
            return context_id
            
        finally:
            conn.close()
    
    def get_field_context(self, field_location_id: int) -> Optional[Dict]:
        """
        Get context information for a field location
        
        Args:
            field_location_id: Field location ID
            
        Returns:
            Context dict with label, label_position, words_before, words_after
            or None if not found
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    label,
                    label_position,
                    words_before,
                    words_after
                FROM field_contexts
                WHERE field_location_id = ?
                LIMIT 1
            """, (field_location_id,))
            
            row = cursor.fetchone()
            return dict(row) if row else None
            
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
        Add or update a learned pattern (UPSERT logic)
        
        If pattern already exists:
        - Increment frequency
        - Update match_rate if provided
        - Keep higher priority
        - Merge examples (keep unique, max 10)
        
        If pattern is new:
        - Insert new record
        
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
            pattern_id: ID of created/updated pattern
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # ✅ Check if pattern already exists
            cursor.execute("""
                SELECT id, frequency, priority, examples, match_rate
                FROM learned_patterns
                WHERE field_config_id = ? AND pattern = ?
            """, (field_config_id, pattern))
            
            existing = cursor.fetchone()
            
            if existing:
                # ✅ UPDATE existing pattern
                existing_id = existing['id']
                existing_frequency = existing['frequency'] or 0
                existing_priority = existing['priority'] or 0
                existing_examples = json.loads(existing['examples']) if existing['examples'] else []
                existing_match_rate = existing['match_rate']
                
                # Merge data
                new_frequency = existing_frequency + frequency
                new_priority = max(existing_priority, priority)
                
                # Merge examples (keep unique, max 10)
                merged_examples = list(set(existing_examples + (examples or [])))[:10]
                
                # Update match_rate (weighted average if both exist)
                if match_rate is not None and existing_match_rate is not None:
                    # Weighted average based on frequency
                    total_freq = new_frequency
                    new_match_rate = (
                        (existing_match_rate * existing_frequency + match_rate * frequency) / total_freq
                    )
                elif match_rate is not None:
                    new_match_rate = match_rate
                else:
                    new_match_rate = existing_match_rate
                
                # Try to update with updated_at, fallback if column doesn't exist
                try:
                    cursor.execute("""
                        UPDATE learned_patterns
                        SET frequency = ?,
                            priority = ?,
                            match_rate = ?,
                            examples = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (
                        new_frequency,
                        new_priority,
                        new_match_rate,
                        json.dumps(merged_examples),
                        existing_id
                    ))
                except Exception as e:
                    if 'no such column: updated_at' in str(e):
                        # Fallback: update without updated_at
                        cursor.execute("""
                            UPDATE learned_patterns
                            SET frequency = ?,
                                priority = ?,
                                match_rate = ?,
                                examples = ?
                            WHERE id = ?
                        """, (
                            new_frequency,
                            new_priority,
                            new_match_rate,
                            json.dumps(merged_examples),
                            existing_id
                        ))
                    else:
                        raise
                
                conn.commit()
                
                self.logger.info(
                    f"✅ Updated pattern {existing_id}: "
                    f"frequency {existing_frequency} → {new_frequency}, "
                    f"priority {existing_priority} → {new_priority}"
                )
                
                return existing_id
            
            else:
                # ✅ INSERT new pattern
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
                
                self.logger.info(f"✅ Inserted new pattern {pattern_id}: {pattern[:50]}")
                
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
    
    # ========================================================================
    # Pattern Operations
    # ========================================================================
    
    def get_learned_patterns_by_field(
        self,
        template_id: int,
        field_name: str,
        active_only: bool = True
    ) -> List[Dict]:
        """
        Get learned patterns for a specific field
        
        Args:
            template_id: Template ID
            field_name: Field name
            active_only: Only return active patterns
            
        Returns:
            List of pattern dicts
        """
        query = """
            SELECT 
                lp.id,
                lp.pattern_type,
                lp.pattern,
                lp.description,
                lp.frequency,
                lp.priority,
                lp.is_active,
                lp.added_at,
                lp.last_used_at,
                lp.usage_count,
                lp.success_count,
                lp.match_rate,
                lp.confidence_boost,
                lp.examples,
                lp.metadata
            FROM learned_patterns lp
            JOIN field_configs fc ON lp.field_config_id = fc.id
            JOIN template_configs tc ON fc.config_id = tc.id
            WHERE tc.template_id = ? AND fc.field_name = ?
        """
        
        params = [template_id, field_name]
        
        if active_only:
            query += " AND lp.is_active = 1"
        
        query += " ORDER BY lp.priority DESC, lp.frequency DESC"
        
        return self.db.execute_query(query, tuple(params))
    
    def get_all_learned_patterns_by_template(
        self,
        template_id: int,
        active_only: bool = True
    ) -> Dict[str, List[Dict]]:
        """
        Get all learned patterns grouped by field for a template
        
        Args:
            template_id: Template ID
            active_only: Only return active patterns
            
        Returns:
            Dict mapping field_name to list of patterns
        """
        query = """
            SELECT 
                fc.field_name,
                lp.id,
                lp.pattern_type,
                lp.pattern,
                lp.description,
                lp.frequency,
                lp.priority,
                lp.is_active,
                lp.added_at,
                lp.last_used_at,
                lp.usage_count,
                lp.success_count,
                lp.match_rate,
                lp.confidence_boost
            FROM learned_patterns lp
            JOIN field_configs fc ON lp.field_config_id = fc.id
            JOIN template_configs tc ON fc.config_id = tc.id
            WHERE tc.template_id = ?
        """
        
        params = [template_id]
        
        if active_only:
            query += " AND lp.is_active = 1"
        
        query += " ORDER BY fc.field_name, lp.priority DESC, lp.frequency DESC"
        
        rows = self.db.execute_query(query, tuple(params))
        
        # Group by field_name
        patterns_by_field = {}
        for row in rows:
            field_name = row['field_name']
            if field_name not in patterns_by_field:
                patterns_by_field[field_name] = []
            
            pattern_dict = {k: v for k, v in row.items() if k != 'field_name'}
            patterns_by_field[field_name].append(pattern_dict)
        
        return patterns_by_field
    
    def get_learning_jobs(
        self,
        template_id: int,
        field_name: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get pattern learning job history
        
        Args:
            template_id: Template ID
            field_name: Optional field name filter
            limit: Maximum number of records
            
        Returns:
            List of learning job dicts
        """
        query = """
            SELECT 
                id,
                field_name,
                job_type,
                status,
                feedback_count,
                patterns_discovered,
                patterns_applied,
                started_at,
                completed_at,
                error_message,
                result_summary
            FROM pattern_learning_jobs
            WHERE template_id = ?
        """
        
        params = [template_id]
        
        if field_name:
            query += " AND field_name = ?"
            params.append(field_name)
        
        query += " ORDER BY started_at DESC LIMIT ?"
        params.append(limit)
        
        return self.db.execute_query(query, tuple(params))
    
    def get_pattern_statistics(
        self,
        template_id: int,
        field_name: str
    ) -> Dict:
        """
        Get pattern usage statistics for a field
        
        Args:
            template_id: Template ID
            field_name: Field name
            
        Returns:
            Dict with statistics
        """
        # Get feedback count
        feedback_query = """
            SELECT COUNT(*) as count
            FROM feedback f
            JOIN documents d ON f.document_id = d.id
            WHERE d.template_id = ? AND f.field_name = ?
        """
        feedback_result = self.db.execute_query(feedback_query, (template_id, field_name))
        
        # Get extraction accuracy
        accuracy_query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN f.original_value = f.corrected_value THEN 1 ELSE 0 END) as correct
            FROM feedback f
            JOIN documents d ON f.document_id = d.id
            WHERE d.template_id = ? AND f.field_name = ?
        """
        accuracy_result = self.db.execute_query(accuracy_query, (template_id, field_name))
        
        total = accuracy_result[0]['total'] if accuracy_result else 0
        correct = accuracy_result[0]['correct'] if accuracy_result else 0
        accuracy = (correct / total * 100) if total > 0 else 0
        
        return {
            'total_feedback': feedback_result[0]['count'] if feedback_result else 0,
            'total_extractions': total,
            'correct_extractions': correct,
            'accuracy_percentage': round(accuracy, 2)
        }
    
    def get_feedback_examples(
        self,
        template_id: int,
        field_name: str,
        limit: int = 5
    ) -> List[Dict]:
        """
        Get recent feedback examples for a field
        
        Args:
            template_id: Template ID
            field_name: Field name
            limit: Maximum number of examples
            
        Returns:
            List of feedback example dicts
        """
        query = """
            SELECT 
                f.original_value,
                f.corrected_value,
                f.created_at
            FROM feedback f
            JOIN documents d ON f.document_id = d.id
            WHERE d.template_id = ? AND f.field_name = ?
            ORDER BY f.created_at DESC
            LIMIT ?
        """
        
        return self.db.execute_query(query, (template_id, field_name, limit))
    
    # ========================================================================
    # Pattern Usage Tracking (NEW!)
    # ========================================================================
    
    def update_pattern_usage(
        self,
        pattern_id: int,
        matched: bool
    ) -> None:
        """
        Update pattern usage statistics
        
        Args:
            pattern_id: Pattern ID
            matched: True if pattern successfully matched
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            if matched:
                # ✅ Pattern matched successfully
                cursor.execute("""
                    UPDATE learned_patterns
                    SET usage_count = COALESCE(usage_count, 0) + 1,
                        success_count = COALESCE(success_count, 0) + 1,
                        match_rate = CAST(COALESCE(success_count, 0) + 1 AS REAL) / (COALESCE(usage_count, 0) + 1),
                        last_used_at = CURRENT_TIMESTAMP,
                        confidence_boost = CASE
                            WHEN CAST(COALESCE(success_count, 0) + 1 AS REAL) / (COALESCE(usage_count, 0) + 1) >= 0.9 THEN 0.2
                            WHEN CAST(COALESCE(success_count, 0) + 1 AS REAL) / (COALESCE(usage_count, 0) + 1) >= 0.7 THEN 0.1
                            ELSE 0.0
                        END
                    WHERE id = ?
                """, (pattern_id,))
            else:
                # ❌ Pattern tried but didn't match
                cursor.execute("""
                    UPDATE learned_patterns
                    SET usage_count = COALESCE(usage_count, 0) + 1,
                        match_rate = CAST(COALESCE(success_count, 0) AS REAL) / (COALESCE(usage_count, 0) + 1),
                        last_used_at = CURRENT_TIMESTAMP,
                        confidence_boost = CASE
                            WHEN CAST(COALESCE(success_count, 0) AS REAL) / (COALESCE(usage_count, 0) + 1) < 0.3 THEN -0.1
                            ELSE COALESCE(confidence_boost, 0.0)
                        END
                    WHERE id = ?
                """, (pattern_id,))
            
            conn.commit()
            
        finally:
            conn.close()
    
    def deactivate_low_performing_patterns(
        self,
        field_config_id: int,
        min_usage: int = 10,
        min_match_rate: float = 0.3
    ) -> int:
        """
        Deactivate patterns with poor performance
        
        Args:
            field_config_id: Field config ID
            min_usage: Minimum usage before evaluation
            min_match_rate: Minimum match rate to keep active
            
        Returns:
            Number of patterns deactivated
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE learned_patterns
                SET is_active = 0
                WHERE field_config_id = ?
                  AND COALESCE(usage_count, 0) >= ?
                  AND COALESCE(match_rate, 0.0) < ?
                  AND is_active = 1
            """, (field_config_id, min_usage, min_match_rate))
            
            deactivated = cursor.rowcount
            conn.commit()
            
            self.logger.info(f"🗑️  Deactivated {deactivated} low-performing patterns")
            
            return deactivated
            
        finally:
            conn.close()
    
    def cleanup_duplicate_patterns(
        self,
        field_config_id: int = None
    ) -> Dict:
        """
        Merge duplicate patterns and keep the best one
        
        Args:
            field_config_id: Specific field config ID (None = all)
            
        Returns:
            Cleanup summary
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Find duplicates
            query = """
                SELECT 
                    field_config_id,
                    pattern,
                    COUNT(*) as count,
                    GROUP_CONCAT(id) as ids,
                    SUM(COALESCE(frequency, 0)) as total_frequency,
                    MAX(COALESCE(priority, 0)) as max_priority,
                    AVG(COALESCE(match_rate, 0.0)) as avg_match_rate
                FROM learned_patterns
            """
            
            if field_config_id:
                query += " WHERE field_config_id = ?"
                params = (field_config_id,)
            else:
                params = ()
            
            query += """
                GROUP BY field_config_id, pattern
                HAVING COUNT(*) > 1
            """
            
            cursor.execute(query, params)
            duplicates = cursor.fetchall()
            
            merged_count = 0
            deleted_count = 0
            
            for dup in duplicates:
                ids = [int(x) for x in dup['ids'].split(',')]
                keep_id = ids[0]  # Keep first one
                delete_ids = ids[1:]
                
                # Update the kept pattern with merged data
                # Note: updated_at column might not exist in older databases
                try:
                    cursor.execute("""
                        UPDATE learned_patterns
                        SET frequency = ?,
                            priority = ?,
                            match_rate = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (
                        dup['total_frequency'],
                        dup['max_priority'],
                        dup['avg_match_rate'],
                        keep_id
                    ))
                except Exception as e:
                    # Fallback: update without updated_at if column doesn't exist
                    if 'no such column: updated_at' in str(e):
                        cursor.execute("""
                            UPDATE learned_patterns
                            SET frequency = ?,
                                priority = ?,
                                match_rate = ?
                            WHERE id = ?
                        """, (
                            dup['total_frequency'],
                            dup['max_priority'],
                            dup['avg_match_rate'],
                            keep_id
                        ))
                    else:
                        raise
                
                # Delete duplicates
                placeholders = ','.join('?' * len(delete_ids))
                cursor.execute(f"""
                    DELETE FROM learned_patterns
                    WHERE id IN ({placeholders})
                """, delete_ids)
                
                merged_count += 1
                deleted_count += len(delete_ids)
                
                self.logger.info(
                    f"✅ Merged pattern {dup['pattern'][:50]}: "
                    f"kept ID {keep_id}, deleted {len(delete_ids)} duplicates"
                )
            
            conn.commit()
            
            return {
                'success': True,
                'patterns_merged': merged_count,
                'duplicates_deleted': deleted_count
            }
            
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Failed to cleanup duplicates: {e}")
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            conn.close()
    
    # ========================================================================
    # Pattern Statistics (Prefix/Suffix/Noise Learning)
    # ========================================================================
    
    def upsert_pattern_statistic(
        self,
        field_config_id: int,
        statistic_type: str,
        pattern_value: str,
        frequency: int = 1,
        confidence: float = 0.0,
        sample_count: int = 0,
        metadata: Dict = None
    ) -> int:
        """
        Add or update pattern statistic (UPSERT)
        
        Args:
            field_config_id: Field config ID
            statistic_type: 'prefix', 'suffix', 'structural_noise'
            pattern_value: The actual pattern (e.g., "tanggal", "has_parentheses_both")
            frequency: How many times seen
            confidence: Confidence score (0.0 - 1.0)
            sample_count: Total samples analyzed
            metadata: Additional info
            
        Returns:
            statistic_id: ID of created/updated statistic
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Check if exists
            cursor.execute("""
                SELECT id, frequency, sample_count
                FROM pattern_statistics
                WHERE field_config_id = ? 
                  AND statistic_type = ? 
                  AND pattern_value = ?
            """, (field_config_id, statistic_type, pattern_value))
            
            existing = cursor.fetchone()
            
            if existing:
                # UPDATE: increment frequency
                new_frequency = existing['frequency'] + frequency
                new_sample_count = max(existing['sample_count'], sample_count)
                
                cursor.execute("""
                    UPDATE pattern_statistics
                    SET frequency = ?,
                        confidence = ?,
                        sample_count = ?,
                        metadata = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    new_frequency,
                    confidence,
                    new_sample_count,
                    json.dumps(metadata) if metadata else None,
                    existing['id']
                ))
                
                conn.commit()
                return existing['id']
            
            else:
                # INSERT new statistic
                cursor.execute("""
                    INSERT INTO pattern_statistics
                    (field_config_id, statistic_type, pattern_value, 
                     frequency, confidence, sample_count, metadata, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                """, (
                    field_config_id,
                    statistic_type,
                    pattern_value,
                    frequency,
                    confidence,
                    sample_count,
                    json.dumps(metadata) if metadata else None
                ))
                
                statistic_id = cursor.lastrowid
                conn.commit()
                return statistic_id
        
        finally:
            conn.close()
    
    def get_pattern_statistics(
        self,
        field_config_id: int,
        statistic_type: str = None,
        active_only: bool = True,
        min_frequency: int = 2
    ) -> List[Dict]:
        """
        Get pattern statistics for a field
        
        Args:
            field_config_id: Field config ID
            statistic_type: Filter by type (None = all)
            active_only: Only return active statistics
            min_frequency: Minimum frequency threshold
            
        Returns:
            List of statistics
        """
        query = """
            SELECT 
                id,
                statistic_type,
                pattern_value,
                frequency,
                confidence,
                sample_count,
                is_active,
                metadata,
                created_at,
                updated_at
            FROM pattern_statistics
            WHERE field_config_id = ?
        """
        
        params = [field_config_id]
        
        if statistic_type:
            query += " AND statistic_type = ?"
            params.append(statistic_type)
        
        if active_only:
            query += " AND is_active = 1"
        
        if min_frequency > 0:
            query += " AND frequency >= ?"
            params.append(min_frequency)
        
        query += " ORDER BY frequency DESC, confidence DESC"
        
        return self.db.execute_query(query, tuple(params))
    
    def get_all_pattern_statistics(
        self,
        template_id: int,
        active_only: bool = True
    ) -> Dict[str, Dict]:
        """
        Get all pattern statistics for a template, grouped by field
        
        Args:
            template_id: Template ID
            active_only: Only return active statistics
            
        Returns:
            Dict mapping field_name to statistics
        """
        query = """
            SELECT 
                fc.field_name,
                ps.statistic_type,
                ps.pattern_value,
                ps.frequency,
                ps.confidence,
                ps.sample_count
            FROM pattern_statistics ps
            JOIN field_configs fc ON ps.field_config_id = fc.id
            JOIN template_configs tc ON fc.config_id = tc.id
            WHERE tc.template_id = ?
        """
        
        if active_only:
            query += " AND ps.is_active = 1"
        
        query += " ORDER BY fc.field_name, ps.frequency DESC"
        
        results = self.db.execute_query(query, (template_id,))
        
        # Group by field_name
        grouped = {}
        for row in results:
            field_name = row['field_name']
            if field_name not in grouped:
                grouped[field_name] = {
                    'common_prefixes': [],
                    'common_suffixes': [],
                    'structural_noise': {},
                    'sample_count': 0
                }
            
            stat_type = row['statistic_type']
            pattern_value = row['pattern_value']
            frequency = row['frequency']
            sample_count = row['sample_count']
            
            if stat_type == 'prefix':
                grouped[field_name]['common_prefixes'].append(pattern_value)
            elif stat_type == 'suffix':
                grouped[field_name]['common_suffixes'].append(pattern_value)
            elif stat_type == 'structural_noise':
                grouped[field_name]['structural_noise'][pattern_value] = frequency
            
            # Update sample count (use max)
            grouped[field_name]['sample_count'] = max(
                grouped[field_name]['sample_count'],
                sample_count
            )
        
        return grouped
    
    def analyze_and_update_pattern_statistics(
        self,
        template_id: int,
        min_frequency_threshold: int = 3
    ) -> Dict:
        """
        Analyze feedback and update pattern statistics
        
        Args:
            template_id: Template ID
            min_frequency_threshold: Minimum frequency to consider a pattern
            
        Returns:
            Summary of updates
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get all feedback for this template
            cursor.execute("""
                SELECT 
                    f.field_name,
                    f.original_value,
                    f.corrected_value,
                    fc.id as field_config_id
                FROM feedback f
                JOIN documents d ON f.document_id = d.id
                JOIN field_configs fc ON (
                    fc.field_name = f.field_name 
                    AND fc.config_id IN (
                        SELECT id FROM template_configs WHERE template_id = ?
                    )
                )
                WHERE d.template_id = ?
                  AND f.original_value != f.corrected_value
            """, (template_id, template_id))
            
            feedbacks = cursor.fetchall()
            
            if not feedbacks:
                return {'success': True, 'message': 'No corrections found', 'updates': 0}
            
            updates = 0
            field_stats = {}
            
            for fb in feedbacks:
                field_name = fb['field_name']
                field_config_id = fb['field_config_id']
                original = fb['original_value']
                corrected = fb['corrected_value']
                
                if field_name not in field_stats:
                    field_stats[field_name] = {
                        'field_config_id': field_config_id,
                        'prefixes': [],
                        'suffixes': [],
                        'structural': []
                    }
                
                # Detect prefix (what was removed from start)
                if original.startswith(corrected):
                    # Suffix was removed
                    suffix = original[len(corrected):].strip()
                    if suffix:
                        # Generalize date patterns in suffix
                        import re
                        # Pattern: ", DD Month YYYY" or ", DD MonthName YYYY"
                        suffix_generalized = re.sub(r',\s*\d{1,2}\s+\w+\s+\d{4}', ', [DATE]', suffix)
                        field_stats[field_name]['suffixes'].append(suffix_generalized)
                elif corrected in original:
                    # Prefix or suffix was removed
                    idx = original.index(corrected)
                    if idx > 0:
                        prefix = original[:idx].strip()
                        if prefix:
                            # Generalize location prefixes (e.g., "Utara,", "Selatan,")
                            import re
                            prefix_generalized = re.sub(r'^[A-Z][a-z]+,', '[LOCATION],', prefix)
                            field_stats[field_name]['prefixes'].append(prefix_generalized)
                    
                    end_idx = idx + len(corrected)
                    if end_idx < len(original):
                        suffix = original[end_idx:].strip()
                        if suffix:
                            # Generalize date patterns in suffix
                            import re
                            suffix_generalized = re.sub(r',\s*\d{1,2}\s+\w+\s+\d{4}', ', [DATE]', suffix)
                            # Generalize multiple names pattern (e.g., ") (Name" or ") (Name)")
                            suffix_generalized = re.sub(r'\)\s*\(.+', ') ([NAME]', suffix_generalized)
                            field_stats[field_name]['suffixes'].append(suffix_generalized)
                
                # Detect structural noise
                if ')' in original and ')' not in corrected:
                    field_stats[field_name]['structural'].append('has_parentheses_end')
                if '(' in original and '(' not in corrected:
                    field_stats[field_name]['structural'].append('has_parentheses_start')
                if original.endswith(',') and not corrected.endswith(','):
                    field_stats[field_name]['structural'].append('has_trailing_comma')
            
            # Update database
            for field_name, stats in field_stats.items():
                field_config_id = stats['field_config_id']
                
                # Count frequencies
                from collections import Counter
                
                prefix_counts = Counter(stats['prefixes'])
                for prefix, freq in prefix_counts.items():
                    if freq >= min_frequency_threshold:
                        self.upsert_pattern_statistic(
                            field_config_id=field_config_id,
                            statistic_type='prefix',
                            pattern_value=prefix.lower(),
                            frequency=freq,
                            confidence=freq / len(feedbacks),
                            sample_count=len(feedbacks)
                        )
                        updates += 1
                
                suffix_counts = Counter(stats['suffixes'])
                for suffix, freq in suffix_counts.items():
                    if freq >= min_frequency_threshold:
                        self.upsert_pattern_statistic(
                            field_config_id=field_config_id,
                            statistic_type='suffix',
                            pattern_value=suffix.lower(),
                            frequency=freq,
                            confidence=freq / len(feedbacks),
                            sample_count=len(feedbacks)
                        )
                        updates += 1
                
                structural_counts = Counter(stats['structural'])
                for noise_type, freq in structural_counts.items():
                    if freq >= min_frequency_threshold:
                        self.upsert_pattern_statistic(
                            field_config_id=field_config_id,
                            statistic_type='structural_noise',
                            pattern_value=noise_type,
                            frequency=freq,
                            confidence=freq / len(feedbacks),
                            sample_count=len(feedbacks)
                        )
                        updates += 1
            
            conn.commit()
            
            return {
                'success': True,
                'message': f'Updated {updates} pattern statistics',
                'updates': updates,
                'fields_analyzed': len(field_stats)
            }
        
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Failed to analyze pattern statistics: {e}")
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            conn.close()
