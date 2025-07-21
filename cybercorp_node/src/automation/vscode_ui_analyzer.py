"""VSCode UI structure analysis utilities"""

from typing import Dict, Any, List, Optional, Tuple


class VSCodeUIAnalyzer:
    """Analyzes VSCode UI structure and extracts elements"""
    
    def __init__(self):
        """Initialize VSCodeUIAnalyzer"""
        self.ui_elements = {}
        self.roo_code_elements = {}
        
    def analyze_structure(self, structure: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Analyze UI structure and categorize elements by type
        
        Args:
            structure: VSCode UI structure data
            
        Returns:
            Dictionary with elements categorized by type
        """
        categorized = {}
        
        content_areas = structure.get('content_areas', [])
        
        for area in content_areas:
            if isinstance(area, dict):
                elem_type = area.get('type', 'Unknown')
                
                if elem_type not in categorized:
                    categorized[elem_type] = []
                    
                categorized[elem_type].append(area)
                
        self.ui_elements = categorized
        return categorized
        
    def find_elements_by_type(self, structure: Dict[str, Any], 
                            element_type: str) -> List[Dict[str, Any]]:
        """Find all elements of specific type
        
        Args:
            structure: VSCode UI structure data
            element_type: Type of element to find (Edit, Button, etc.)
            
        Returns:
            List of matching elements
        """
        matching_elements = []
        
        content_areas = structure.get('content_areas', [])
        
        for area in content_areas:
            if isinstance(area, dict) and area.get('type') == element_type:
                matching_elements.append(area)
                
        return matching_elements
        
    def find_elements_by_name(self, structure: Dict[str, Any], 
                            name_pattern: str) -> List[Dict[str, Any]]:
        """Find elements by name pattern
        
        Args:
            structure: VSCode UI structure data
            name_pattern: Pattern to search for in element names
            
        Returns:
            List of matching elements
        """
        matching_elements = []
        
        content_areas = structure.get('content_areas', [])
        
        for area in content_areas:
            if isinstance(area, dict):
                name = area.get('name', '')
                if name_pattern.lower() in name.lower():
                    matching_elements.append(area)
                    
        return matching_elements
        
    def find_roo_code_elements(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Find Roo Code specific UI elements
        
        Args:
            structure: VSCode UI structure data
            
        Returns:
            Dictionary with Roo Code elements
        """
        roo_elements = {
            'input_box': None,
            'send_button': None,
            'content_area': None,
            'cancel_button': None,
            'mode_button': None,
            'model_button': None
        }
        
        content_areas = structure.get('content_areas', [])
        
        for area in content_areas:
            if not isinstance(area, dict):
                continue
                
            elem_type = area.get('type', '')
            name = area.get('name', '')
            texts = area.get('texts', [])
            
            # Find input box
            if elem_type == 'Edit' and any('type' in str(t).lower() for t in texts):
                roo_elements['input_box'] = area
                
            # Find send button
            elif elem_type == 'Button' and 'send' in name.lower():
                roo_elements['send_button'] = area
                
            # Find cancel button
            elif elem_type == 'Button' and name == 'Cancel':
                roo_elements['cancel_button'] = area
                
            # Find mode button (Ask, Code, etc.)
            elif elem_type == 'Button' and any(mode in name for mode in ['❓ Ask', '💻 Code']):
                roo_elements['mode_button'] = area
                
            # Find model selector
            elif elem_type == 'Button' and any('sonnet' in name.lower() or 'opus' in name.lower()):
                roo_elements['model_button'] = area
                
            # Find main content area
            elif elem_type == 'Document' and 'Roo Code' in name:
                roo_elements['content_area'] = area
                
        self.roo_code_elements = roo_elements
        return roo_elements
        
    def extract_text_content(self, structure: Dict[str, Any]) -> List[str]:
        """Extract all text content from UI structure
        
        Args:
            structure: VSCode UI structure data
            
        Returns:
            List of all text content
        """
        all_texts = []
        
        content_areas = structure.get('content_areas', [])
        
        for area in content_areas:
            if not isinstance(area, dict):
                continue
                
            # Extract from texts field
            texts = area.get('texts', [])
            if isinstance(texts, list):
                for text in texts:
                    if isinstance(text, str) and text.strip():
                        all_texts.append(text)
                    elif isinstance(text, list):
                        # Handle nested lists (like table cells)
                        for nested in text:
                            if isinstance(nested, list):
                                all_texts.extend([str(t) for t in nested if t])
                            elif nested:
                                all_texts.append(str(nested))
                                
            # Also extract from name field
            name = area.get('name', '')
            if name and name not in all_texts:
                all_texts.append(name)
                
        return all_texts
        
    def find_roo_conversation(self, structure: Dict[str, Any]) -> Optional[str]:
        """Extract Roo Code conversation content
        
        Args:
            structure: VSCode UI structure data
            
        Returns:
            Conversation content if found
        """
        # Look for Document type with substantial text
        for area in structure.get('content_areas', []):
            if not isinstance(area, dict):
                continue
                
            if area.get('type') == 'Document':
                texts = area.get('texts', [])
                if texts and isinstance(texts[0], str) and len(texts[0]) > 500:
                    return texts[0]
                    
        return None
        
    def get_ui_summary(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Get summary of UI structure
        
        Args:
            structure: VSCode UI structure data
            
        Returns:
            Summary dictionary
        """
        self.analyze_structure(structure)
        
        summary = {
            'window_title': structure.get('window_title', 'Unknown'),
            'is_active': structure.get('is_active', False),
            'element_counts': {},
            'has_roo_code': False,
            'total_elements': len(structure.get('content_areas', []))
        }
        
        # Count elements by type
        for elem_type, elements in self.ui_elements.items():
            summary['element_counts'][elem_type] = len(elements)
            
        # Check for Roo Code
        roo_elements = self.find_roo_code_elements(structure)
        summary['has_roo_code'] = any(v is not None for v in roo_elements.values())
        
        return summary
        
    def find_clickable_elements(self, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find all clickable elements (buttons, links, etc.)
        
        Args:
            structure: VSCode UI structure data
            
        Returns:
            List of clickable elements
        """
        clickable_types = ['Button', 'Hyperlink', 'MenuItem', 'TabItem', 'CheckBox']
        clickable_elements = []
        
        for area in structure.get('content_areas', []):
            if isinstance(area, dict) and area.get('type') in clickable_types:
                clickable_elements.append(area)
                
        return clickable_elements
        
    def find_input_elements(self, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find all input elements
        
        Args:
            structure: VSCode UI structure data
            
        Returns:
            List of input elements
        """
        input_types = ['Edit', 'ComboBox']
        input_elements = []
        
        for area in structure.get('content_areas', []):
            if isinstance(area, dict) and area.get('type') in input_types:
                input_elements.append(area)
                
        return input_elements