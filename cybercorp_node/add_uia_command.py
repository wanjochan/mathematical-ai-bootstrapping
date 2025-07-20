"""Add generic UIA structure command to client.py"""

# This shows the code to add to client.py

def get_window_uia_structure(hwnd):
    """Get complete UIA structure of any window"""
    try:
        from pywinauto import Application
        import logging
        
        # Connect to the window
        app = Application(backend="uia").connect(handle=hwnd)
        window = app.window(handle=hwnd)
        
        def extract_structure(element, depth=0, max_depth=15):
            """Extract complete element structure"""
            if depth > max_depth:
                return {"error": "Max depth reached"}
                
            try:
                elem_info = element.element_info
                
                structure = {
                    'ControlType': elem_info.control_type,
                    'Name': elem_info.name or '',
                    'AutomationId': element.automation_id() if hasattr(element, 'automation_id') else '',
                    'ClassName': elem_info.class_name or '',
                    'IsEnabled': elem_info.enabled,
                    'IsVisible': elem_info.visible,
                    'Rectangle': str(elem_info.rectangle),
                    'Children': {}
                }
                
                # Add value for editable controls
                if elem_info.control_type in ['Edit', 'ComboBox']:
                    try:
                        structure['Value'] = element.get_value() if hasattr(element, 'get_value') else ''
                        structure['IsKeyboardFocusable'] = getattr(elem_info, 'keyboard_focusable', False)
                    except:
                        structure['Value'] = ''
                
                # Get texts
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
                        child_name = ''
                        child_type = ''
                        child_id = ''
                        
                        try:
                            child_info = child.element_info
                            child_name = child_info.name or ''
                            child_type = child_info.control_type
                            child_id = child.automation_id() if hasattr(child, 'automation_id') else ''
                        except:
                            pass
                        
                        # Create descriptive key
                        if child_id:
                            child_key = f"{child_type}_{child_id}_{i}"
                        elif child_name:
                            safe_name = ''.join(c if c.isalnum() else '_' for c in child_name[:20])
                            child_key = f"{child_type}_{safe_name}_{i}"
                        else:
                            child_key = f"{child_type}_{i}"
                            
                        structure['Children'][child_key] = extract_structure(child, depth + 1, max_depth)
                        
                except Exception as e:
                    logging.debug(f"Error getting children: {e}")
                    
                return structure
                
            except Exception as e:
                return {"error": str(e)}
        
        # Extract full structure
        return extract_structure(window)
        
    except Exception as e:
        logging.error(f"Error getting UIA structure: {e}")
        return {"error": str(e)}

# Add this to the command execution section in client.py:
"""
elif command == 'get_window_uia_structure':
    hwnd = params.get('hwnd')
    if hwnd:
        result = get_window_uia_structure(hwnd)
    else:
        error = "Missing hwnd parameter"
"""