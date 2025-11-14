"""
Adaptive Table Extraction Strategy
Automatically detects and extracts data from tables in PDF documents
WITHOUT hardcoded column indices or field mappings
"""

import pdfplumber
from typing import Dict, List, Optional, Tuple, Any
import logging
from difflib import SequenceMatcher


class AdaptiveTableExtractor:
    """
    Adaptive table extractor that learns table structure from field configurations
    and extracts data without hardcoded mappings
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def extract_tables(self, pdf_path: str, page_number: int = 0) -> List[List[List[str]]]:
        """
        Extract all tables from a PDF page
        
        Args:
            pdf_path: Path to PDF file
            page_number: Page number (0-indexed)
            
        Returns:
            List of tables, where each table is a list of rows, 
            and each row is a list of cell values
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if page_number >= len(pdf.pages):
                    self.logger.warning(f"Page {page_number} not found in PDF")
                    return []
                
                page = pdf.pages[page_number]
                
                # Extract tables with settings optimized for complex layouts
                tables = page.extract_tables({
                    'vertical_strategy': 'lines_strict',  # Use explicit lines
                    'horizontal_strategy': 'lines_strict',
                    'snap_tolerance': 3,  # Snap to lines within 3 pixels
                    'join_tolerance': 3,  # Join lines within 3 pixels
                    'edge_min_length': 3,  # Minimum line length
                    'min_words_vertical': 1,  # Minimum words to detect vertical boundary
                    'min_words_horizontal': 1,  # Minimum words to detect horizontal boundary
                    'text_tolerance': 3,
                    'intersection_tolerance': 3,
                })
                
                # Clean tables (remove None values, strip whitespace)
                cleaned_tables = []
                for table in tables:
                    cleaned_table = []
                    for row in table:
                        cleaned_row = [
                            cell.strip() if cell else '' 
                            for cell in row
                        ]
                        cleaned_table.append(cleaned_row)
                    cleaned_tables.append(cleaned_table)
                
                self.logger.info(f"📊 Extracted {len(cleaned_tables)} tables from page {page_number}")
                return cleaned_tables
                
        except Exception as e:
            self.logger.error(f"Error extracting tables: {e}")
            return []
    
    def find_field_in_tables(
        self, 
        tables: List[List[List[str]]], 
        field_name: str,
        field_config: Dict,
        all_words: List[Dict]
    ) -> Optional[Tuple[str, float, Dict]]:
        """
        Find field value in tables using adaptive matching
        
        Args:
            tables: List of extracted tables
            field_name: Name of field to find
            field_config: Field configuration with hints
            all_words: All words from PDF (for context)
            
        Returns:
            Tuple of (value, confidence, metadata) or None
        """
        if not tables:
            return None
        
        # Get field hints from config
        field_label = field_config.get('label', '')
        field_pattern = field_config.get('base_pattern', '')
        
        # Try to find field using multiple strategies
        result = None
        
        # Strategy 1: Match by field label in header row
        result = self._find_by_header_match(tables, field_name, field_label)
        if result:
            return result
        
        # Strategy 2: Match by field name pattern
        result = self._find_by_name_pattern(tables, field_name)
        if result:
            return result
        
        # Strategy 3: Match by position and context
        result = self._find_by_position_context(tables, field_name, all_words)
        if result:
            return result
        
        return None
    
    def _find_by_header_match(
        self, 
        tables: List[List[List[str]]], 
        field_name: str,
        field_label: str
    ) -> Optional[Tuple[str, float, Dict]]:
        """
        Find field by matching header row with field label
        
        Strategy:
        1. Look for header row (usually first row)
        2. Find column that matches field label
        3. Extract values from that column in subsequent rows
        """
        if not field_label:
            return None
        
        for table_idx, table in enumerate(tables):
            if len(table) < 2:  # Need at least header + 1 data row
                continue
            
            header_row = table[0]
            
            # Find column index by matching header with field label
            col_idx = self._find_matching_column(header_row, field_label, field_name)
            
            if col_idx is not None:
                # Extract values from this column
                values = []
                for row_idx in range(1, len(table)):  # Skip header
                    cell_value = table[row_idx][col_idx] if col_idx < len(table[row_idx]) else ''
                    if cell_value and cell_value.strip():
                        values.append(cell_value.strip())
                
                if values:
                    # For multi-row fields (e.g., area_finding_1, area_finding_2)
                    # Extract specific row based on field name suffix
                    row_number = self._extract_row_number(field_name)
                    
                    if row_number is not None and row_number <= len(values):
                        value = values[row_number - 1]  # 1-indexed to 0-indexed
                        confidence = 0.9  # High confidence for header match
                        
                        self.logger.info(
                            f"✅ [Table] Found '{field_name}' by header match: "
                            f"table={table_idx}, col={col_idx}, row={row_number}, value='{value}'"
                        )
                        
                        return (value, confidence, {
                            'method': 'table_header_match',
                            'table_index': table_idx,
                            'column_index': col_idx,
                            'row_number': row_number,
                            'header': header_row[col_idx]
                        })
                    elif row_number is None and len(values) == 1:
                        # Single value field
                        value = values[0]
                        confidence = 0.9
                        
                        self.logger.info(
                            f"✅ [Table] Found '{field_name}' by header match: "
                            f"table={table_idx}, col={col_idx}, value='{value}'"
                        )
                        
                        return (value, confidence, {
                            'method': 'table_header_match',
                            'table_index': table_idx,
                            'column_index': col_idx,
                            'header': header_row[col_idx]
                        })
        
        return None
    
    def _find_by_name_pattern(
        self, 
        tables: List[List[List[str]]], 
        field_name: str
    ) -> Optional[Tuple[str, float, Dict]]:
        """
        Find field by matching field name pattern with table content
        
        Strategy:
        1. Parse field name to extract semantic meaning
           e.g., 'area_finding_1' -> look for 'finding' or 'observation'
        2. Match with table headers
        3. Extract corresponding values
        """
        # Extract keywords from field name
        keywords = self._extract_keywords_from_field_name(field_name)
        
        if not keywords:
            return None
        
        # ✅ CRITICAL: Sort keywords by specificity (longer = more specific)
        # This prevents 'area' from matching before 'finding'
        # Example: 'area_finding_1' -> ['finding', 'area'] (finding first!)
        keywords.sort(key=len, reverse=True)
        
        for table_idx, table in enumerate(tables):
            if len(table) < 2:
                continue
            
            header_row = table[0]
            
            # ✅ NEW: Try to find best matching column using ALL keywords
            # Score each column by how many keywords it contains
            best_col_idx = None
            best_score = 0
            best_keyword = None
            
            for col_idx, header in enumerate(header_row):
                if not header:
                    continue
                
                header_lower = header.lower()
                score = 0
                matched_keyword = None
                
                # Count how many keywords match this header
                for keyword in keywords:
                    if keyword in header_lower:
                        # Longer keywords get higher score (more specific)
                        score += len(keyword)
                        if matched_keyword is None:
                            matched_keyword = keyword
                
                # Update best match
                if score > best_score:
                    best_score = score
                    best_col_idx = col_idx
                    best_keyword = matched_keyword
            
            # If we found a matching column
            if best_col_idx is not None:
                # Extract value
                row_number = self._extract_row_number(field_name)
                
                if row_number is not None and row_number < len(table):
                    value = table[row_number][best_col_idx] if best_col_idx < len(table[row_number]) else ''
                    
                    if value and value.strip():
                        confidence = 0.8  # Good confidence for keyword match
                        
                        self.logger.info(
                            f"✅ [Table] Found '{field_name}' by keyword '{best_keyword}': "
                            f"table={table_idx}, col={best_col_idx}, row={row_number}, value='{value}'"
                        )
                        
                        return (value.strip(), confidence, {
                            'method': 'table_keyword_match',
                            'table_index': table_idx,
                            'column_index': best_col_idx,
                            'row_number': row_number,
                            'keyword': best_keyword,
                            'header': header_row[best_col_idx],
                            'match_score': best_score
                        })
        
        return None
    
    def _find_by_position_context(
        self, 
        tables: List[List[List[str]]], 
        field_name: str,
        all_words: List[Dict]
    ) -> Optional[Tuple[str, float, Dict]]:
        """
        Find field by analyzing position and context from all_words
        
        Strategy:
        1. Find approximate Y-position of field from all_words
        2. Find table that contains this Y-position
        3. Extract value from corresponding row
        """
        # This is a fallback strategy - implement if needed
        # For now, return None to keep it simple
        return None
    
    def _find_matching_column(
        self, 
        header_row: List[str], 
        field_label: str,
        field_name: str
    ) -> Optional[int]:
        """
        Find column index that matches field label or field name
        
        Uses fuzzy matching to handle variations in header text
        """
        if not header_row:
            return None
        
        best_match_idx = None
        best_match_score = 0.0
        
        for idx, header in enumerate(header_row):
            if not header:
                continue
            
            header_lower = header.lower().strip()
            
            # Direct match with field label
            if field_label and field_label.lower() in header_lower:
                return idx
            
            # Fuzzy match with field label
            if field_label:
                score = SequenceMatcher(None, field_label.lower(), header_lower).ratio()
                if score > best_match_score and score > 0.6:
                    best_match_score = score
                    best_match_idx = idx
            
            # Match with field name keywords
            keywords = self._extract_keywords_from_field_name(field_name)
            for keyword in keywords:
                if keyword.lower() in header_lower:
                    # Exact keyword match is better than fuzzy match
                    if best_match_score < 0.8:
                        best_match_score = 0.8
                        best_match_idx = idx
        
        return best_match_idx if best_match_score > 0.6 else None
    
    def _find_column_by_keyword(
        self, 
        header_row: List[str], 
        keyword: str
    ) -> Optional[int]:
        """Find column index by keyword match"""
        for idx, header in enumerate(header_row):
            if header and keyword.lower() in header.lower():
                return idx
        return None
    
    def _extract_keywords_from_field_name(self, field_name: str) -> List[str]:
        """
        Extract keywords from field name (NO HARDCODING!)
        
        ✅ ADAPTIVE: Only uses the field name itself, no predefined mappings.
        This ensures the method works for ANY template, not just specific ones.
        
        Strategy:
        1. Split field name by underscores
        2. Filter out numbers and short parts
        3. Use actual field name parts as keywords
        
        Examples:
        - 'area_finding_1' -> ['area', 'finding']
        - 'area_recomendation_2' -> ['area', 'recomendation']
        - 'area_id_3' -> ['area', 'id']
        - 'client_name' -> ['client', 'name']
        - 'project_location_2' -> ['project', 'location']
        
        The table headers will be matched using fuzzy matching,
        so even if the exact keyword isn't in the header, similar
        words will still match (e.g., 'finding' matches 'Observation/Finding').
        
        Args:
            field_name: Name of the field
            
        Returns:
            List of keywords extracted from field name
        """
        keywords = []
        
        # Split by underscore and filter
        parts = field_name.split('_')
        for part in parts:
            # Skip numbers (e.g., '1', '2', '3')
            if part.isdigit():
                continue
            
            # Skip very short parts (e.g., 'a', 'b')
            if len(part) < 2:
                continue
            
            # Add alphabetic parts as keywords
            if part.isalpha():
                keywords.append(part.lower())
        
        return keywords
    
    def _extract_row_number(self, field_name: str) -> Optional[int]:
        """
        Extract row number from field name
        
        Examples:
        - 'area_finding_1' -> 1
        - 'area_finding_2' -> 2
        - 'client_name' -> None (no row number)
        """
        parts = field_name.split('_')
        for part in reversed(parts):  # Check from end
            if part.isdigit():
                return int(part)
        return None
    
    def get_table_structure_info(
        self, 
        tables: List[List[List[str]]]
    ) -> List[Dict[str, Any]]:
        """
        Get structural information about extracted tables
        
        Returns:
            List of table info dicts with headers, row count, column count, etc.
        """
        table_info = []
        
        for idx, table in enumerate(tables):
            if not table:
                continue
            
            info = {
                'table_index': idx,
                'row_count': len(table),
                'column_count': len(table[0]) if table else 0,
                'header_row': table[0] if table else [],
                'has_header': self._looks_like_header(table[0]) if table else False,
                'sample_rows': table[1:3] if len(table) > 1 else []  # First 2 data rows
            }
            
            table_info.append(info)
        
        return table_info
    
    def _looks_like_header(self, row: List[str]) -> bool:
        """
        Check if a row looks like a header row (NO HARDCODING!)
        
        ✅ ADAPTIVE: Uses general heuristics that work for ANY table,
        not specific keywords that only work for certain templates.
        
        Heuristics:
        1. Contains mostly text (not pure numbers)
        2. Cells are relatively short (headers are usually concise)
        3. Contains capitalized words (headers often capitalized)
        4. First row of table (most common position)
        
        Args:
            row: List of cell values in the row
            
        Returns:
            True if row appears to be a header
        """
        if not row:
            return False
        
        # Filter out empty cells
        non_empty_cells = [cell for cell in row if cell and cell.strip()]
        if not non_empty_cells:
            return False
        
        # Heuristic 1: Contains mostly text (not pure numbers)
        # Pure number cells are likely data, not headers
        text_cells = sum(1 for cell in non_empty_cells if not cell.strip().isdigit())
        text_ratio = text_cells / len(non_empty_cells)
        
        # Heuristic 2: Cells are relatively short (headers are concise)
        # Average header cell length is typically < 30 characters
        avg_length = sum(len(cell) for cell in non_empty_cells) / len(non_empty_cells)
        is_short = avg_length < 30
        
        # Heuristic 3: Contains capitalized words (headers often capitalized)
        has_capitals = any(
            any(word[0].isupper() for word in cell.split() if word)
            for cell in non_empty_cells
        )
        
        # Decision: Row is likely a header if:
        # - Mostly text (not numbers) AND
        # - Either short cells OR has capitalized words
        return text_ratio > 0.5 and (is_short or has_capitals)
