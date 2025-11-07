"""
Template Analyzer
Core logic extracted from example-code/app/template_analysis/strategies.py
"""
import pdfplumber
import re
import json
from typing import Dict, List, Tuple, Any
from core.patterns import PatternManager


class TemplateAnalyzer:
    """Analyzes PDF templates to identify extractable fields"""
    
    def __init__(self):
        self.pattern_manager = PatternManager()
        self.fields = []
        self.text_content = ""
        self.pages_text = []
        self.words_by_page = []
        
    def analyze_template(self, pdf_path: str, template_id: int = 0, template_name: str = "unknown") -> Dict[str, Any]:
        """
        Analyze a PDF template to identify fields
        Core implementation from example code
        
        Args:
            pdf_path: Path to PDF template file
            template_id: Template ID for tracking
            template_name: Template name for identification
        """
        # Reset state
        self.fields = []
        self.text_content = ""
        self.pages_text = []
        self.words_by_page = []
        
        # Extract template content - EXACT from example
        self._extract_template_content(pdf_path)
        
        # Identify variable markers - EXACT from example
        self._identify_variable_markers()
        
        # Convert to our format with multi-location support
        fields_dict = {}
        
        # Group fields by name (to handle duplicate markers)
        fields_by_name = {}
        for field_data in self.fields:
            field_name = field_data["name"]
            if field_name not in fields_by_name:
                fields_by_name[field_name] = []
            fields_by_name[field_name].append(field_data)
        
        # Build field config with locations array
        for field_name, field_occurrences in fields_by_name.items():
            pattern = self.pattern_manager.get_pattern_for_field(field_name)
            
            # Build locations array
            locations = []
            for field_data in field_occurrences:
                page_idx = field_data["page"]
                marker_x = field_data["x"]
                marker_y = field_data["y"]
                marker_width = field_data["width"]
                marker_height = field_data["height"]
                
                # Extract context with positions
                context = self._extract_context_words(
                    page_idx, marker_x, marker_y, marker_width, marker_height
                )
                
                locations.append({
                    'page': page_idx,
                    'x0': marker_x,
                    'y0': marker_y,
                    'x1': marker_x + marker_width,
                    'y1': marker_y + marker_height,
                    'context': context
                })
            
            fields_dict[field_name] = {
                'marker_text': field_occurrences[0]["marker"],
                'pattern': pattern,
                'locations': locations
            }
        
        return {
            'template_id': template_id,  # Add template metadata
            'template_name': template_name,  # Add template metadata
            'fields': fields_dict,
            'metadata': {
                'field_count': len(fields_dict),
                'pages': len(self.pages_text)
            }
        }
    
    def _extract_template_content(self, template_path: str) -> None:
        """
        Extract text content and words from the template PDF.
        EXACT implementation from example code
        """
        with pdfplumber.open(template_path) as pdf:
            self.pages_text = []
            self.words_by_page = []
            
            for page in pdf.pages:
                page_text = page.extract_text()
                self.pages_text.append(page_text)
                self.words_by_page.append(page.extract_words())
                
            self.text_content = "\n".join(self.pages_text)
    
    def _identify_variable_markers(self) -> None:
        """
        Identify variable markers in the template.
        Updated to support duplicate markers across pages
        """
        marker_count = 0
        
        # Enhanced pattern to handle various variable formats
        standard_pattern = r'\{([a-zA-Z0-9_]+)\}|\$\{([a-zA-Z0-9_]+)\}'
        
        # Process each page separately
        for page_idx, page_text in enumerate(self.pages_text):
            # Find all markers on this page (including duplicates)
            for match in re.finditer(standard_pattern, page_text):
                name = match.group(1) or match.group(2)
                marker_text = match.group(0)
                
                marker_count += 1
                
                start_pos = match.start()
                end_pos = match.end()
                
                print(f"Found marker: {marker_text} at position {start_pos}-{end_pos} on page {page_idx + 1}")
                
                # Find bounding box for this marker
                bbox = self._find_bbox_for_text(marker_text, page_idx, start_pos)
                
                # Prepare field data
                field_data = {
                    "name": name,
                    "marker": marker_text,
                    "page": page_idx,
                    "x": bbox[0],
                    "y": bbox[1],
                    "width": bbox[2] - bbox[0],
                    "height": bbox[3] - bbox[1],
                    "position": {
                        "page": page_idx,
                        "text_pos": (start_pos, end_pos),
                        "bbox": bbox
                    }
                }
                
                self.fields.append(field_data)
        
        print(f"Total markers found: {marker_count}")
    
    def _find_bbox_for_text(self, text: str, page_num: int, text_pos: int) -> List[float]:
        """
        Find the bounding box for a text segment on a page.
        Enhanced to handle exact matching for markers
        """
        if page_num >= len(self.words_by_page):
            return [0, 0, 0, 0]
        
        words = self.words_by_page[page_num]
        
        # STEP 1: Try EXACT match first (most accurate)
        for word in words:
            if word.get('text', '') == text:
                return [word['x0'], word['top'], word['x1'], word['bottom']]
        
        # STEP 2: Try finding in words, but check if it's a complete marker
        # This handles cases like "{tempat_lahir}, {tanggal_lahir}" in one word
        for word in words:
            word_text = word.get('text', '')
            if text in word_text:
                # Check if this is the ONLY marker or if there are multiple
                # Count how many markers in this word
                marker_count = word_text.count('{')
                
                if marker_count == 1:
                    # Only one marker in word, safe to use
                    return [word['x0'], word['top'], word['x1'], word['bottom']]
                else:
                    # Multiple markers in word - need to find exact position
                    # Try to split by common separators
                    parts = re.split(r'[,\s]+', word_text)
                    for part in parts:
                        if text == part.strip():
                            # Found exact match in split parts
                            # Estimate position based on part index
                            part_index = parts.index(part)
                            # Simple estimation: divide word width by number of parts
                            part_width = (word['x1'] - word['x0']) / len(parts)
                            x0 = word['x0'] + (part_index * part_width)
                            x1 = x0 + part_width
                            return [x0, word['top'], x1, word['bottom']]
        
        # If not found, return a default bbox
        return [0, 0, 0, 0]
    
    def _extract_context_words(
        self, 
        page_idx: int, 
        marker_x: float, 
        marker_y: float, 
        marker_width: float, 
        marker_height: float
    ) -> Dict[str, Any]:
        """
        Extract context words around a marker position
        Finds words before (left) and after (right) the marker
        
        Args:
            page_idx: Page index
            marker_x: Marker x position
            marker_y: Marker y position
            marker_width: Marker width
            marker_height: Marker height
            
        Returns:
            Dictionary with context information
        """
        if page_idx >= len(self.words_by_page):
            return {'label': None, 'words_before': [], 'words_after': []}
        
        words = self.words_by_page[page_idx]
        marker_x1 = marker_x + marker_width
        marker_y_center = marker_y + (marker_height / 2)
        
        words_before = []
        words_after = []
        label_text = None
        
        for word in words:
            word_x0 = word.get('x0', 0)
            word_x1 = word.get('x1', 0)
            word_y_center = (word.get('top', 0) + word.get('bottom', 0)) / 2
            word_text = word.get('text', '')
            
            # Check if on same line (within 10 points vertically)
            if abs(word_y_center - marker_y_center) < 10:
                # Word is before marker (to the left)
                if word_x1 < marker_x:
                    words_before.append({
                        'text': word_text,
                        'x0': word_x0,
                        'x1': word_x1,
                        'distance': marker_x - word_x1
                    })
                # Word is after marker (to the right)
                elif word_x0 > marker_x1:
                    words_after.append({
                        'text': word_text,
                        'x0': word_x0,
                        'x1': word_x1,
                        'distance': word_x0 - marker_x1
                    })
        
        # Sort by distance (closest first)
        words_before.sort(key=lambda w: w['distance'])
        words_after.sort(key=lambda w: w['distance'])
        
        # Find label (typically the closest word before, often ending with ':')
        label_position = None
        if words_before:
            closest = words_before[0]
            # Check if it looks like a label (ends with ':' or is close)
            if closest['text'].endswith(':') or closest['distance'] < 20:
                label_text = closest['text']
                label_position = {
                    'x0': closest['x0'],
                    'y0': marker_y,
                    'x1': closest['x1'],
                    'y1': marker_y + marker_height
                }
        
        # Build enhanced words_before with positions (center point)
        words_before_enhanced = []
        for w in words_before[:5]:  # Keep top 5
            word_y_center = marker_y + (marker_height / 2)
            words_before_enhanced.append({
                'text': w['text'],
                'x': (w['x0'] + w['x1']) / 2,  # Center X
                'y': word_y_center  # Center Y (approximate)
            })
        
        # Build enhanced words_after with positions (center point)
        words_after_enhanced = []
        for w in words_after[:5]:  # Keep top 5
            word_y_center = marker_y + (marker_height / 2)
            words_after_enhanced.append({
                'text': w['text'],
                'x': (w['x0'] + w['x1']) / 2,  # Center X
                'y': word_y_center  # Center Y (approximate)
            })
        
        return {
            'label': label_text,
            'label_position': label_position,
            'words_before': words_before_enhanced,
            'words_after': words_after_enhanced
        }
    
    def save_config(self, config: Dict, output_path: str):
        """Save configuration to JSON file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
    
    def load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
