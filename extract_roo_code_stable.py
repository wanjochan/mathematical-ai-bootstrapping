"""Extract detailed Roo Code content using CyberCorp Stable"""

import sys
sys.path.insert(0, 'cybercorp_stable')
from client import VSCodeController
import json

def extract_roo_code_details():
    print("Extracting Roo Code Dialog Content with CyberCorp Stable")
    print("=" * 60)
    
    controller = VSCodeController()
    
    # Find VSCode
    if not controller.find_vscode_window():
        print("[FAIL] VSCode window not found")
        return
    
    print("[OK] Found VSCode window")
    
    # Get content
    content = controller.get_window_content()
    if not content:
        print("[FAIL] Could not get window content")
        return
    
    print(f"[OK] Window: {content['window_title']}")
    print(f"[OK] Total content areas: {len(content['content_areas'])}")
    
    # Extract all Roo Code related content
    roo_code_contents = []
    all_texts = []
    
    for area in content['content_areas']:
        # Collect all texts
        for text in area.get('texts', []):
            if text and len(text) > 10:
                all_texts.append(text)
        
        # Look for Roo Code specific content
        if ('Roo Code' in area.get('name', '') or 
            any('Roo Code' in t for t in area.get('texts', [])) or
            area.get('type') in ['Document', 'Edit', 'Text']):
            
            roo_code_contents.append({
                'type': area['type'],
                'name': area['name'],
                'texts': area.get('texts', [])
            })
    
    # Look for task content in all texts
    print("\n[SEARCHING] Looking for task content...")
    task_found = False
    
    for text in all_texts:
        if 'Task:' in text or 'mathematical-ai-bootstrapping' in text:
            print(f"\n[FOUND] Task-related content:")
            print("-" * 60)
            try:
                print(text[:500] + "..." if len(text) > 500 else text)
            except UnicodeEncodeError:
                # Handle encoding issues
                safe_text = text.encode('utf-8', errors='ignore').decode('utf-8')
                print(safe_text[:500] + "..." if len(safe_text) > 500 else safe_text)
            task_found = True
        elif any(keyword in text.lower() for keyword in ['architect', 'cybercorp', 'analysis', 'component']):
            print(f"\n[FOUND] Related content:")
            try:
                print(text[:200] + "..." if len(text) > 200 else text)
            except UnicodeEncodeError:
                safe_text = text.encode('utf-8', errors='ignore').decode('utf-8')
                print(safe_text[:200] + "..." if len(safe_text) > 200 else safe_text)
    
    if not task_found:
        # Try to find in the window text itself
        print("\n[INFO] Checking window text content...")
        
        # Save all content for analysis
        with open('vscode_content_stable.json', 'w', encoding='utf-8') as f:
            json.dump({
                'window': content['window_title'],
                'is_active': content['is_active'],
                'content_areas': roo_code_contents,
                'all_texts': all_texts
            }, f, indent=2, ensure_ascii=False)
        
        print("[OK] Content saved to vscode_content_stable.json")
        
        # Display some sample texts
        print("\n[INFO] Sample texts found:")
        for i, text in enumerate(all_texts[:10]):
            if len(text) > 20:
                print(f"{i+1}. {text[:80]}...")
    
    # Test window activation and typing
    print("\n[TEST] Testing window control...")
    if controller.activate_window():
        print("[OK] Window activated")
    else:
        print("[FAIL] Could not activate window")
    
    print("\n[DONE] Extraction completed")

if __name__ == "__main__":
    extract_roo_code_details()