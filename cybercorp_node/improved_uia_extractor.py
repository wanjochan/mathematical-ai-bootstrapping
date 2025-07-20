"""Improved UIA structure extractor for Cursor/VSCode"""

import json
from pywinauto import Desktop, Application
from pywinauto.backend import registry
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_full_ui_structure(hwnd):
    """Get complete UI structure from a window"""
    try:
        # Connect to the window
        app = Application(backend="uia").connect(handle=hwnd)
        window = app.window(handle=hwnd)
        
        # Extract full structure
        structure = extract_element_structure(window)
        return structure
        
    except Exception as e:
        logger.error(f"Error getting UI structure: {e}")
        return None

def extract_element_structure(element, depth=0, max_depth=15):
    """Extract complete structure of an UI element"""
    if depth > max_depth:
        return {"error": "Max depth reached"}
        
    try:
        # Get element properties
        elem_info = element.element_info
        
        structure = {
            'ControlType': elem_info.control_type,
            'Name': elem_info.name or '',
            'AutomationId': element.automation_id() if hasattr(element, 'automation_id') else '',
            'ClassName': elem_info.class_name or '',
            'IsEnabled': elem_info.enabled,
            'IsVisible': elem_info.visible,
            'IsKeyboardFocusable': getattr(elem_info, 'keyboard_focusable', False),
            'Rectangle': str(elem_info.rectangle),
            'Children': {}
        }
        
        # Add value for editable controls
        if elem_info.control_type in ['Edit', 'ComboBox']:
            try:
                structure['Value'] = element.get_value() if hasattr(element, 'get_value') else ''
            except:
                structure['Value'] = ''
        
        # Get all texts
        try:
            texts = element.texts()
            if texts:
                structure['Texts'] = texts
        except:
            pass
            
        # Get children
        try:
            children = element.children()
            for i, child in enumerate(children):
                child_key = f"child_{i}"
                
                # Add more descriptive key if possible
                try:
                    child_name = child.element_info.name
                    child_type = child.element_info.control_type
                    child_id = child.automation_id() if hasattr(child, 'automation_id') else ''
                    
                    if child_id:
                        child_key = f"{child_type}_{child_id}_{i}"
                    elif child_name:
                        # Sanitize name for use as key
                        safe_name = ''.join(c if c.isalnum() else '_' for c in child_name[:30])
                        child_key = f"{child_type}_{safe_name}_{i}"
                    else:
                        child_key = f"{child_type}_{i}"
                        
                except:
                    pass
                    
                structure['Children'][child_key] = extract_element_structure(child, depth + 1, max_depth)
                
        except Exception as e:
            logger.debug(f"Error getting children at depth {depth}: {e}")
            
        return structure
        
    except Exception as e:
        logger.error(f"Error extracting element structure: {e}")
        return {"error": str(e)}

def find_cursor_elements(structure, results=None, path=""):
    """Find Cursor-specific elements in the structure"""
    if results is None:
        results = {
            'chat_inputs': [],
            'editable_elements': [],
            'buttons': [],
            'chat_areas': []
        }
        
    if isinstance(structure, dict):
        control_type = structure.get('ControlType', '')
        name = structure.get('Name', '').lower()
        automation_id = structure.get('AutomationId', '').lower()
        is_enabled = structure.get('IsEnabled', False)
        
        # Check for chat input areas
        chat_keywords = ['chat', 'message', 'type', 'input', 'composer', 'prompt', 'ask', 'send']
        if any(keyword in name or keyword in automation_id for keyword in chat_keywords):
            if control_type == 'Edit' and is_enabled:
                results['chat_inputs'].append({
                    'path': path,
                    'name': structure.get('Name'),
                    'automationId': structure.get('AutomationId'),
                    'value': structure.get('Value', '')
                })
            else:
                results['chat_areas'].append({
                    'path': path,
                    'name': structure.get('Name'),
                    'type': control_type,
                    'automationId': structure.get('AutomationId')
                })
        
        # Collect all editable elements
        if control_type == 'Edit' and is_enabled:
            results['editable_elements'].append({
                'path': path,
                'name': structure.get('Name'),
                'automationId': structure.get('AutomationId'),
                'value': structure.get('Value', ''),
                'rectangle': structure.get('Rectangle', '')
            })
            
        # Collect buttons
        if control_type == 'Button' and is_enabled:
            results['buttons'].append({
                'path': path,
                'name': structure.get('Name'),
                'automationId': structure.get('AutomationId')
            })
        
        # Process children
        children = structure.get('Children', {})
        for child_key, child_value in children.items():
            child_path = f"{path}/{child_key}" if path else child_key
            find_cursor_elements(child_value, results, child_path)
            
    return results

def test_cursor_window():
    """Test with known Cursor window"""
    cursor_hwnd = 5898916  # Known Cursor window handle
    
    print("Getting full UI structure for Cursor...")
    structure = get_full_ui_structure(cursor_hwnd)
    
    if structure:
        # Save full structure
        filename = "cursor_full_structure.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(structure, f, indent=2, ensure_ascii=False)
        print(f"Saved full structure to {filename}")
        
        # Find Cursor elements
        print("\nAnalyzing structure for Cursor elements...")
        results = find_cursor_elements(structure)
        
        print(f"\nFound {len(results['chat_inputs'])} chat input elements:")
        for elem in results['chat_inputs']:
            print(f"  - {elem['name']} at {elem['path']}")
            
        print(f"\nFound {len(results['editable_elements'])} total editable elements:")
        for elem in results['editable_elements'][:5]:  # Show first 5
            print(f"  - {elem['name']} at {elem['path']}")
            
        print(f"\nFound {len(results['chat_areas'])} chat-related areas:")
        for elem in results['chat_areas']:
            print(f"  - {elem['name']} ({elem['type']}) at {elem['path']}")
            
        # Save analysis results
        results_filename = "cursor_analysis_results.json"
        with open(results_filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\nSaved analysis results to {results_filename}")
        
    else:
        print("Failed to get UI structure")

if __name__ == "__main__":
    test_cursor_window()