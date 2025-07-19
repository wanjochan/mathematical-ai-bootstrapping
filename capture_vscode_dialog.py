"""Capture VSCode dialog content using deep UI Automation scanning"""

import json
from pywinauto import Desktop
from pywinauto.application import Application

def get_control_details(control, depth=0, max_depth=10):
    """Recursively get control details"""
    if depth > max_depth:
        return None
        
    try:
        info = {
            'depth': depth,
            'type': control.element_info.control_type,
            'name': control.element_info.name or '',
            'class_name': control.element_info.class_name or '',
            'automation_id': control.element_info.automation_id or '',
            'is_visible': control.is_visible(),
            'is_enabled': control.is_enabled(),
            'rectangle': str(control.rectangle()),
            'children': []
        }
        
        # Try to get text content
        try:
            texts = control.texts()
            if texts:
                info['texts'] = texts
        except:
            pass
            
        # Get value for certain control types
        if control.element_info.control_type in ['Edit', 'Text', 'Document']:
            try:
                info['value'] = control.get_value()
            except:
                pass
                
        # Check for dialog-like patterns
        name_lower = info['name'].lower()
        if any(keyword in name_lower for keyword in ['dialog', 'roo code', 'chat', 'conversation', 'message']):
            info['is_dialog_element'] = True
            
        # Recursively get children
        try:
            for child in control.children():
                child_info = get_control_details(child, depth + 1, max_depth)
                if child_info:
                    info['children'].append(child_info)
        except:
            pass
            
        return info
        
    except Exception as e:
        return {'error': str(e), 'depth': depth}

def find_vscode_dialogs():
    """Find VSCode windows and scan for dialogs"""
    desktop = Desktop(backend="uia")
    results = []
    
    print("Scanning for VSCode windows and dialogs...")
    
    for window in desktop.windows():
        try:
            title = window.window_text()
            
            # Check if it's VSCode
            if ('Visual Studio Code' in title or 'VSCode' in title or 
                window.class_name() == 'Chrome_WidgetWin_1'):
                
                print(f"\nFound VSCode window: {title}")
                
                # Deep scan the window
                window_details = get_control_details(window, max_depth=15)
                
                # Find dialog elements
                dialogs = find_dialogs_in_tree(window_details)
                
                if dialogs:
                    print(f"  Found {len(dialogs)} dialog-related elements")
                    for dialog in dialogs:
                        print(f"    - {dialog['type']}: {dialog['name'][:80]}")
                        if 'texts' in dialog:
                            for text in dialog['texts'][:3]:  # First 3 texts
                                print(f"      Text: {text[:100]}")
                
                results.append({
                    'window_title': title,
                    'window_details': window_details,
                    'dialogs_found': dialogs
                })
                
        except Exception as e:
            print(f"Error processing window: {e}")
    
    return results

def find_dialogs_in_tree(node, path=""):
    """Recursively find dialog-related elements in the control tree"""
    dialogs = []
    
    if not node or 'error' in node:
        return dialogs
    
    # Check current node
    name = node.get('name', '').lower()
    type_name = node.get('type', '').lower()
    
    # Look for dialog indicators
    if ('dialog' in name or 'roo code' in name or 'chat' in name or 
        'conversation' in name or 'message' in name or
        'dialog' in type_name or node.get('is_dialog_element')):
        
        dialog_info = {
            'path': path,
            'type': node.get('type'),
            'name': node.get('name'),
            'depth': node.get('depth'),
            'is_visible': node.get('is_visible'),
            'rectangle': node.get('rectangle')
        }
        
        if 'texts' in node:
            dialog_info['texts'] = node['texts']
        if 'value' in node:
            dialog_info['value'] = node['value']
            
        dialogs.append(dialog_info)
    
    # Check children
    for i, child in enumerate(node.get('children', [])):
        child_path = f"{path}/{node.get('type')}[{i}]"
        dialogs.extend(find_dialogs_in_tree(child, child_path))
    
    return dialogs

def main():
    print("VSCode Dialog Content Scanner")
    print("=" * 60)
    print("Looking for ROO CODE dialog and other UI elements...\n")
    
    results = find_vscode_dialogs()
    
    # Save results
    output_file = "vscode_dialog_scan.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n\nDetailed scan saved to: {output_file}")
    
    # Print summary
    total_dialogs = sum(len(r['dialogs_found']) for r in results)
    print(f"\nSummary: Found {total_dialogs} dialog-related elements in {len(results)} VSCode windows")

if __name__ == "__main__":
    main()