"""Analyze VSCode content structure in detail"""

import asyncio
import websockets
import json
import sys
import os
from datetime import datetime
from collections import defaultdict

async def analyze_vscode_content(username):
    """Get and analyze VSCode content structure"""
    
    server_url = 'ws://localhost:9998'
    
    try:
        websocket = await websockets.connect(server_url)
        
        # Register
        await websocket.send(json.dumps({
            'type': 'register',
            'user_session': f"{os.environ.get('USERNAME', 'unknown')}_analyzer",
            'client_start_time': datetime.now().isoformat(),
            'capabilities': {'management': True, 'control': True},
            'system_info': {
                'platform': 'Windows',
                'hostname': os.environ.get('COMPUTERNAME', 'unknown')
            }
        }))
        
        welcome = await websocket.recv()
        
        # Get client list
        await websocket.send(json.dumps({
            'type': 'request',
            'command': 'list_clients'
        }))
        
        response = await websocket.recv()
        data = json.loads(response)
        
        target_client_id = None
        if data['type'] == 'client_list':
            for client in data['clients']:
                if client.get('user_session') == username:
                    target_client_id = client['id']
                    break
        
        if not target_client_id:
            print(f"Client '{username}' not found")
            return
        
        # Send command
        await websocket.send(json.dumps({
            'type': 'forward_command',
            'target_client': target_client_id,
            'command': {
                'type': 'command',
                'command': 'vscode_get_content',
                'params': {}
            }
        }))
        
        await websocket.recv()  # ack
        
        # Wait for result
        while True:
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                result = json.loads(response)
                
                if result.get('type') == 'command_result' and result.get('from_client') == target_client_id:
                    if result.get('error'):
                        print(f"Error: {result['error']}")
                    else:
                        vscode_data = result.get('result', {})
                        analyze_structure(vscode_data)
                    break
                    
            except asyncio.TimeoutError:
                print("Timeout")
                break
        
        await websocket.close()
        
    except Exception as e:
        print(f"Error: {e}")

def analyze_structure(data):
    """Analyze VSCode window structure"""
    
    print("\nVSCode Window Analysis")
    print("=" * 80)
    
    # Basic info
    print(f"\nWindow Title: {data.get('window_title', 'Unknown')}")
    print(f"Active: {data.get('is_active', False)}")
    print(f"Rectangle: {data.get('rectangle', 'Unknown')}")
    
    # Analyze content areas
    content_areas = data.get('content_areas', [])
    print(f"\nTotal UI Elements: {len(content_areas)}")
    
    # Group by control type
    by_type = defaultdict(list)
    for area in content_areas:
        if isinstance(area, dict):
            control_type = area.get('control_type', 'Unknown')
            by_type[control_type].append(area)
    
    print("\nUI Elements by Type:")
    for ctrl_type, elements in sorted(by_type.items(), key=lambda x: -len(x[1])):
        print(f"  {ctrl_type}: {len(elements)}")
    
    # Find important elements
    print("\nImportant Elements Found:")
    
    # Look for editor
    editors = []
    tabs = []
    panels = []
    dialogs = []
    
    for area in content_areas:
        if isinstance(area, dict):
            name = area.get('name', '').lower()
            class_name = area.get('class_name', '').lower()
            control_type = area.get('control_type', '').lower()
            
            # Editor areas
            if 'editor' in name or 'monaco' in class_name:
                editors.append(area)
            
            # Tabs
            if 'tab' in control_type or 'tab' in name:
                tabs.append(area)
            
            # Panels
            if 'panel' in name or 'terminal' in name or 'output' in name:
                panels.append(area)
            
            # Dialogs (including Roo Code)
            if 'dialog' in control_type or 'roo' in name:
                dialogs.append(area)
    
    print(f"  Editors: {len(editors)}")
    print(f"  Tabs: {len(tabs)}")
    print(f"  Panels: {len(panels)}")
    print(f"  Dialogs: {len(dialogs)}")
    
    # Show editor content
    if editors:
        print("\nEditor Areas:")
        for i, editor in enumerate(editors[:3]):  # First 3
            print(f"  Editor {i+1}:")
            print(f"    Name: {editor.get('name', 'Unknown')}")
            print(f"    Class: {editor.get('class_name', 'Unknown')}")
            if 'rectangle' in editor:
                print(f"    Position: {editor['rectangle']}")
    
    # Show open tabs
    if tabs:
        print("\nOpen Tabs:")
        for tab in tabs[:10]:  # First 10
            name = tab.get('name', '')
            if name and not name.startswith('Tab') and len(name) > 2:
                print(f"  - {name}")
    
    # Look for Roo Code dialog
    print("\nSearching for Roo Code Dialog...")
    roo_elements = []
    for area in content_areas:
        if isinstance(area, dict):
            name = str(area.get('name', ''))
            if 'roo' in name.lower() or 'code' in name.lower():
                roo_elements.append(area)
    
    if roo_elements:
        print(f"Found {len(roo_elements)} potential Roo Code elements:")
        for elem in roo_elements[:5]:
            print(f"  - {elem.get('name', 'Unknown')} ({elem.get('control_type', 'Unknown')})")
    
    # Show sample of all text content
    print("\nText Content Found:")
    text_elements = []
    for area in content_areas:
        if isinstance(area, dict) and area.get('name'):
            name = str(area['name']).strip()
            if name and len(name) > 2 and not name.isdigit():
                text_elements.append(name)
    
    # Deduplicate and show
    unique_texts = list(set(text_elements))
    for text in unique_texts[:20]:  # First 20
        if len(text) < 100:  # Skip very long texts
            print(f"  - {text}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        username = "wjchk"
    else:
        username = sys.argv[1]
    
    asyncio.run(analyze_vscode_content(username))