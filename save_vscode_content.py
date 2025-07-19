"""Save VSCode content to file for analysis"""

import sys
sys.path.insert(0, 'cybercorp_stable')
from client import VSCodeController
import json

def save_content():
    controller = VSCodeController()
    
    if not controller.find_vscode_window():
        print("VSCode not found")
        return
    
    content = controller.get_window_content()
    if not content:
        print("No content")
        return
    
    # Process and clean content
    clean_content = {
        'window_title': content['window_title'],
        'is_active': content['is_active'],
        'text_contents': []
    }
    
    # Extract all texts
    for area in content['content_areas']:
        if area.get('texts'):
            for text in area['texts']:
                if text and len(text) > 5:
                    # Clean text
                    clean_text = ''.join(c for c in text if c.isprintable() or c in '\n\t')
                    if clean_text.strip():
                        clean_content['text_contents'].append({
                            'type': area['type'],
                            'name': area.get('name', ''),
                            'text': clean_text
                        })
    
    # Save to file
    with open('vscode_extracted_content.json', 'w', encoding='utf-8') as f:
        json.dump(clean_content, f, indent=2, ensure_ascii=False)
    
    print("Content saved to vscode_extracted_content.json")
    
    # Look for task content
    for item in clean_content['text_contents']:
        if 'Task:' in item['text'] or 'cybercorp' in item['text'].lower():
            print(f"\nFound relevant content in {item['type']}:")
            print(item['text'][:200])

if __name__ == "__main__":
    save_content()