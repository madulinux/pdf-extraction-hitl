"""
Input Validation Utilities
Centralized validation logic
"""
import re
from typing import Optional, Tuple
from werkzeug.datastructures import FileStorage

class Validator:
    """Input validation utilities"""
    
    ALLOWED_PDF_EXTENSIONS = {'pdf'}
    MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
    
    @staticmethod
    def validate_file(file: Optional[FileStorage], allowed_extensions: set = None) -> Tuple[bool, Optional[str]]:
        """
        Validate uploaded file
        
        Args:
            file: Uploaded file
            allowed_extensions: Set of allowed extensions
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if allowed_extensions is None:
            allowed_extensions = Validator.ALLOWED_PDF_EXTENSIONS
        
        if not file:
            return False, "No file provided"
        
        if file.filename == '':
            return False, "No file selected"
        
        # Check extension
        if '.' not in file.filename:
            return False, "File has no extension"
        
        ext = file.filename.rsplit('.', 1)[1].lower()
        if ext not in allowed_extensions:
            return False, f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        
        return True, None
    
    @staticmethod
    def validate_required_fields(data: dict, required_fields: list) -> Tuple[bool, Optional[dict]]:
        """
        Validate required fields in request data
        
        Args:
            data: Request data
            required_fields: List of required field names
            
        Returns:
            Tuple of (is_valid, errors_dict)
        """
        errors = {}
        
        for field in required_fields:
            if field not in data or data[field] is None or data[field] == '':
                errors[field] = f"{field} is required"
        
        if errors:
            return False, errors
        
        return True, None
    
    @staticmethod
    def sanitize_regex_pattern(pattern: str) -> str:
        """
        Sanitize regex pattern to plain string format (remove delimiters)
        
        Converts various regex formats to plain string:
        - JavaScript: /pattern/flags -> pattern
        - Python raw: r'pattern' -> pattern
        - Already plain: pattern -> pattern
        
        Args:
            pattern: Regex pattern in any format
            
        Returns:
            Plain regex pattern string (no delimiters)
        """
        if not pattern:
            return pattern
        
        pattern = pattern.strip()
        
        # Remove JavaScript regex delimiters: /pattern/flags
        if pattern.startswith('/'):
            # Find last slash (before flags)
            last_slash = pattern.rfind('/')
            if last_slash > 0:
                pattern = pattern[1:last_slash]
        
        # Remove Python raw string prefix: r'pattern' or r"pattern"
        if pattern.startswith(('r"', "r'")):
            pattern = pattern[2:-1]  # Remove r" and closing "
        elif pattern.startswith(('R"', "R'")):
            pattern = pattern[2:-1]  # Remove R" and closing "
        
        # Remove quotes if wrapped: 'pattern' or "pattern"
        if (pattern.startswith('"') and pattern.endswith('"')) or \
           (pattern.startswith("'") and pattern.endswith("'")):
            pattern = pattern[1:-1]
        
        return pattern
    
    @staticmethod
    def validate_regex_pattern(pattern: str, sanitize: bool = True) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate and optionally sanitize regex pattern
        
        Args:
            pattern: Regex pattern string (can have delimiters)
            sanitize: If True, remove delimiters before validation
            
        Returns:
            Tuple of (is_valid, error_message, sanitized_pattern)
        """
        if not pattern:
            return False, "Pattern cannot be empty", None
        
        # Sanitize pattern if requested
        if sanitize:
            sanitized = Validator.sanitize_regex_pattern(pattern)
        else:
            sanitized = pattern
        
        # Validate the sanitized pattern
        try:
            re.compile(sanitized)
            return True, None, sanitized
        except re.error as e:
            return False, f"Invalid regex pattern: {str(e)}", None
    
    @staticmethod
    def validate_positive_integer(value: any, field_name: str = "value") -> Tuple[bool, Optional[str]]:
        """
        Validate positive integer
        
        Args:
            value: Value to validate
            field_name: Field name for error message
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            int_value = int(value)
            if int_value <= 0:
                return False, f"{field_name} must be a positive integer"
            return True, None
        except (ValueError, TypeError):
            return False, f"{field_name} must be a valid integer"
