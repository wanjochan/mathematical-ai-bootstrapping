"""Extract complete Roo Code dialog conversation content"""

import json
from pywinauto import Desktop
from pywinauto.application import Application

def extract_text_content(control, depth=0, max_depth=20):
    """Extract all text content from a control and its children"""
    texts = []
    
    if depth > max_depth:
        return texts
        
    try:
        # Get control info
        control_type = control.element_info.control_type
        control_name = control.element_info.name or ''
        
        # Add control name if it has meaningful text
        if control_name and not control_name.startswith('\ue'):  # Skip icon characters
            texts.append({
                'type': control_type,
                'text': control_name,
                'depth': depth
            })
        
        # Try to get text content
        try:
            control_texts = control.texts()
            for text in control_texts:
                if text and not text.startswith('\ue'):  # Skip icon characters
                    texts.append({
                        'type': control_type,
                        'text': text,
                        'depth': depth
                    })
        except:
            pass
            
        # Special handling for Edit and Document controls
        if control_type in ['Edit', 'Document', 'Text']:
            try:
                value = control.get_value()
                if value and not value.startswith('\ue'):
                    texts.append({
                        'type': control_type,
                        'text': value,
                        'depth': depth,
                        'is_value': True
                    })
            except:
                pass
        
        # Recursively process children
        try:
            for child in control.children():
                child_texts = extract_text_content(child, depth + 1, max_depth)
                texts.extend(child_texts)
        except:
            pass
            
    except Exception as e:
        pass
        
    return texts

def find_roo_code_dialog():
    """Find and extract Roo Code dialog content"""
    desktop = Desktop(backend="uia")
    
    print("Searching for VSCode windows with Roo Code dialog...")
    
    for window in desktop.windows():
        try:
            title = window.window_text()
            
            # Check if it's VSCode
            if ('Visual Studio Code' in title or window.class_name() == 'Chrome_WidgetWin_1'):
                print(f"\nFound VSCode: {title}")
                
                # Extract all text content
                all_texts = extract_text_content(window)
                
                # Filter for Roo Code related content
                roo_code_texts = []
                in_roo_code_section = False
                
                for text_info in all_texts:
                    text = text_info['text']
                    
                    # Check if we're in Roo Code section
                    if 'Roo Code' in text:
                        in_roo_code_section = True
                    
                    # Collect conversation-like content
                    if in_roo_code_section or any(keyword in text.lower() for keyword in 
                        ['task:', 'message', 'chat', 'based on', 'understand', 'conversation',
                         'architecture', 'analysis', 'cybercorp', 'component', 'system']):
                        
                        # Skip UI elements and icons
                        if not any(skip in text for skip in ['Button', 'Toggle', 'Ctrl+', 'Alt+', '...']):
                            roo_code_texts.append(text_info)
                
                if roo_code_texts:
                    return {
                        'window_title': title,
                        'conversation': roo_code_texts
                    }
                    
        except Exception as e:
            print(f"Error processing window: {e}")
    
    return None

def main():
    print("Roo Code Dialog Content Extractor")
    print("=" * 60)
    
    result = find_roo_code_dialog()
    
    if result:
        print(f"\nFound Roo Code dialog in: {result['window_title']}")
        print("\nConversation content:")
        print("-" * 60)
        
        # Group and display conversation
        current_depth = -1
        for item in result['conversation']:
            # Add indentation based on depth
            indent = "  " * (item['depth'] // 2)
            
            # Clean up the text
            text = item['text'].strip()
            
            # Skip very short texts
            if len(text) < 5:
                continue
                
            # Print with context
            if 'Task:' in text:
                print(f"\n{indent}[TASK] {text}")
            elif item.get('is_value'):
                print(f"{indent}[INPUT] {text}")
            elif len(text) > 100:
                print(f"\n{indent}[MESSAGE] {text[:200]}...")
            else:
                print(f"{indent}{text}")
        
        # Save to file
        with open('roo_code_conversation.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print("\n\nFull conversation saved to: roo_code_conversation.json")
    else:
        print("\nNo Roo Code dialog found!")

if __name__ == "__main__":
    main()