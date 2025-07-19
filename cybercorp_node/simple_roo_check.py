"""Simple check of Roo Code response"""

import asyncio
import websockets
import json
import os
from datetime import datetime

async def check_roo_simple():
    """Simple check of current VSCode state"""
    
    server_url = 'ws://localhost:9998'
    
    try:
        websocket = await websockets.connect(server_url)
        
        # Register
        await websocket.send(json.dumps({
            'type': 'register',
            'user_session': 'simple_checker',
            'capabilities': {'management': True}
        }))
        
        await websocket.recv()
        
        # Find wjchk client
        await websocket.send(json.dumps({
            'type': 'request',
            'command': 'list_clients'
        }))
        
        response = await websocket.recv()
        data = json.loads(response)
        
        client_id = None
        for client in data.get('clients', []):
            if client.get('user_session') == 'wjchk':
                client_id = client['id']
                break
        
        if not client_id:
            print("wjchk client not found")
            return
        
        print(f"Found wjchk client: {client_id}")
        
        # Get VSCode content
        print("\nGetting VSCode content...")
        
        await websocket.send(json.dumps({
            'type': 'forward_command',
            'target_client': client_id,
            'command': {
                'type': 'command',
                'command': 'vscode_get_content'
            }
        }))
        
        await websocket.recv()  # ack
        
        # Get result
        response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
        result = json.loads(response)
        
        if result.get('type') == 'command_result':
            vscode_data = result.get('result', {})
            
            # Save full data
            var_dir = os.path.join(os.path.dirname(__file__), 'var')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = os.path.join(var_dir, f'roo_check_{timestamp}.json')
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(vscode_data, f, indent=2, ensure_ascii=False)
            
            print(f"Full data saved to: {filepath}")
            
            # Extract key information
            print("\n=== VSCode Window Status ===")
            print(f"Title: {vscode_data.get('window_title', 'Unknown')}")
            print(f"Active: {vscode_data.get('is_active', False)}")
            
            # Look for our message and responses
            print("\n=== Text Content Analysis ===")
            
            content_areas = vscode_data.get('content_areas', [])
            
            # Collect all text
            all_texts = []
            for area in content_areas:
                if isinstance(area, dict):
                    # Handle different text formats
                    texts = area.get('texts', [])
                    if isinstance(texts, list):
                        for text in texts:
                            if isinstance(text, str):
                                all_texts.append(text)
                    
                    # Also check 'name' field
                    name = area.get('name', '')
                    if name:
                        all_texts.append(name)
            
            # Look for our task
            task_found = False
            for text in all_texts:
                if '分析一下当前的产品设计' in text:
                    task_found = True
                    print(f"\n[TASK FOUND] Our question is in the UI")
                    break
            
            # Look for response indicators
            print("\n=== Potential Responses ===")
            response_keywords = ['产品', '设计', '分析', '功能', '架构', '系统', '模块', '用户']
            
            potential_responses = []
            for text in all_texts:
                if len(text) > 50:  # Substantial text
                    matches = sum(1 for kw in response_keywords if kw in text)
                    if matches >= 2 and '分析一下当前的产品设计' not in text:
                        potential_responses.append(text)
            
            if potential_responses:
                print(f"\nFound {len(potential_responses)} potential response(s):")
                for i, resp in enumerate(potential_responses[:3], 1):
                    print(f"\n[Response {i}]")
                    print(resp[:500] + '...' if len(resp) > 500 else resp)
            else:
                print("\nNo clear response found yet.")
                print("Possible reasons:")
                print("- Roo is still processing")
                print("- Response is in a different format")
                print("- Response might be visual (need screenshot)")
            
            # Show sample of all texts
            print("\n=== Sample of All Text Elements ===")
            unique_texts = list(set(t for t in all_texts if len(t) > 20))[:10]
            for i, text in enumerate(unique_texts, 1):
                print(f"{i}. {text[:100]}...")
        
        await websocket.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_roo_simple())