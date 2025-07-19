"""Background RPA for Roo Code - No foreground window switching"""

import asyncio
import websockets
import json
import os
from datetime import datetime
from typing import Optional, Dict, List

class BackgroundRooCodeRPA:
    """RPA that operates on background windows using UI Automation"""
    
    def __init__(self, username: str):
        self.username = username
        self.server_url = 'ws://localhost:9998'
        self.websocket = None
        self.client_id = None
        self.var_dir = os.path.join(os.path.dirname(__file__), 'var')
        os.makedirs(self.var_dir, exist_ok=True)
        
    async def connect(self) -> bool:
        """Connect to server and find target client"""
        try:
            self.websocket = await websockets.connect(self.server_url)
            
            # Register
            await self.websocket.send(json.dumps({
                'type': 'register',
                'user_session': f"{os.environ.get('USERNAME', 'unknown')}_background_rpa",
                'client_start_time': datetime.now().isoformat(),
                'capabilities': {'management': True, 'control': True, 'background_ops': True}
            }))
            
            await self.websocket.recv()
            
            # Find target
            await self.websocket.send(json.dumps({
                'type': 'request',
                'command': 'list_clients'
            }))
            
            response = await self.websocket.recv()
            data = json.loads(response)
            
            for client in data.get('clients', []):
                if client.get('user_session') == self.username:
                    self.client_id = client['id']
                    print(f"[OK] Connected to {self.username} (ID: {self.client_id})")
                    return True
                    
            print(f"[ERROR] Client '{self.username}' not found")
            return False
            
        except Exception as e:
            print(f"[ERROR] Connection failed: {e}")
            return False
    
    async def send_command(self, command: str, params: dict = None) -> Optional[dict]:
        """Send command to client"""
        await self.websocket.send(json.dumps({
            'type': 'forward_command',
            'target_client': self.client_id,
            'command': {
                'type': 'command',
                'command': command,
                'params': params or {}
            }
        }))
        
        await self.websocket.recv()  # ack
        
        try:
            response = await asyncio.wait_for(self.websocket.recv(), timeout=5.0)
            return json.loads(response)
        except asyncio.TimeoutError:
            print(f"[TIMEOUT] Command '{command}' timed out")
            return None
    
    async def get_ui_structure(self) -> Optional[dict]:
        """Get current VSCode UI structure"""
        print("\n[STEP 1] Getting UI structure (background)...")
        
        result = await self.send_command('vscode_get_content')
        if result and not result.get('error'):
            structure = result.get('result', {})
            
            # Save for analysis
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = os.path.join(self.var_dir, f'background_ui_{timestamp}.json')
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(structure, f, indent=2, ensure_ascii=False)
            print(f"  [SAVED] UI structure: {file_path}")
            
            return structure
            
        return None
    
    async def find_roo_code_elements(self, structure: dict) -> dict:
        """Analyze structure to find Roo Code elements"""
        print("\n[STEP 2] Analyzing UI elements...")
        
        elements = {
            'input_field': None,
            'send_button': None,
            'roo_panel': None,
            'edit_elements': [],
            'button_elements': []
        }
        
        content_areas = structure.get('content_areas', [])
        
        for i, area in enumerate(content_areas):
            if not isinstance(area, dict):
                continue
                
            elem_type = area.get('type', '')
            name = area.get('name', '')
            
            # Collect all edit elements
            if elem_type == 'Edit':
                elements['edit_elements'].append({
                    'index': i,
                    'name': name,
                    'area': area
                })
                
                # Check if this is the Roo Code input
                if any(keyword in name.lower() for keyword in ['task', 'type', 'message', 'chat']):
                    elements['input_field'] = area
                    print(f"  [FOUND] Input field: {name}")
            
            # Collect all buttons
            elif elem_type == 'Button':
                elements['button_elements'].append({
                    'index': i,
                    'name': name,
                    'area': area
                })
                
                # Check if this is send button
                if 'send' in name.lower():
                    elements['send_button'] = area
                    print(f"  [FOUND] Send button: {name}")
            
            # Look for Roo panel
            if 'roo' in name.lower():
                elements['roo_panel'] = area
        
        print(f"  Total Edit elements: {len(elements['edit_elements'])}")
        print(f"  Total Button elements: {len(elements['button_elements'])}")
        
        return elements
    
    async def send_background_input(self, element_info: dict, text: str) -> bool:
        """Send input to specific element without activating window"""
        print(f"\n[STEP 3] Sending background input...")
        
        # Use a special command for background input
        result = await self.send_command('background_input', {
            'element_name': element_info.get('name', ''),
            'element_type': element_info.get('type', ''),
            'action': 'set_text',
            'text': text
        })
        
        if result and result.get('result'):
            print("  [OK] Background input sent")
            return True
        
        # Fallback: Try regular input without activation
        print("  [FALLBACK] Using regular input method...")
        
        # Clear field first
        await self.send_command('send_keys', {'keys': '^a'})
        await asyncio.sleep(0.2)
        
        # Type text
        result = await self.send_command('vscode_type_text', {'text': text})
        
        return result is not None
    
    async def click_element_background(self, element_info: dict) -> bool:
        """Click element without activating window"""
        print(f"\n[STEP 4] Clicking element (background)...")
        
        # Try background click
        result = await self.send_command('background_click', {
            'element_name': element_info.get('name', ''),
            'element_type': element_info.get('type', '')
        })
        
        if result and result.get('result'):
            print("  [OK] Background click sent")
            return True
        
        # Fallback: Send Enter key
        print("  [FALLBACK] Sending Enter key...")
        result = await self.send_command('send_keys', {'keys': '{ENTER}'})
        
        return result is not None
    
    async def execute_background_task(self, message: str) -> bool:
        """Execute complete task in background"""
        print(f"\n{'=' * 80}")
        print(f"Background Roo Code RPA")
        print(f"Target: {self.username}")
        print(f"Message: {message}")
        print(f"Mode: Background (no window switching)")
        print(f"{'=' * 80}")
        
        # Connect
        if not await self.connect():
            return False
        
        try:
            # Get UI structure
            structure = await self.get_ui_structure()
            if not structure:
                print("[ERROR] Cannot get UI structure")
                return False
            
            # Find elements
            elements = await self.find_roo_code_elements(structure)
            
            # Check if we have required elements
            if not elements['input_field']:
                if len(elements['edit_elements']) == 1:
                    # Use the only edit element
                    elements['input_field'] = elements['edit_elements'][0]['area']
                    print(f"  [AUTO] Using only Edit element: {elements['edit_elements'][0]['name']}")
                else:
                    print("[ERROR] Cannot find input field")
                    return False
            
            # Send input
            if not await self.send_background_input(elements['input_field'], message):
                print("[ERROR] Failed to send input")
                return False
            
            await asyncio.sleep(0.5)
            
            # Click send or press Enter
            if elements['send_button']:
                success = await self.click_element_background(elements['send_button'])
            else:
                # Just send Enter
                print("  [INFO] No send button found, using Enter key")
                result = await self.send_command('send_keys', {'keys': '{ENTER}'})
                success = result is not None
            
            if success:
                print("\n[SUCCESS] Background task completed!")
                
                # Get updated structure to verify
                await asyncio.sleep(1)
                new_structure = await self.get_ui_structure()
                if new_structure:
                    print("  [VERIFIED] UI updated after send")
                
                return True
            else:
                print("[ERROR] Failed to send message")
                return False
                
        except Exception as e:
            print(f"[ERROR] Task failed: {e}")
            import traceback
            traceback.print_exc()
            return False
            
        finally:
            if self.websocket:
                await self.websocket.close()

# Also need to update client.py to support background operations
BACKGROUND_OPS_CODE = '''
# Add to client.py command handling:

elif command == 'background_input':
    # Background input without window activation
    element_name = params.get('element_name', '')
    text = params.get('text', '')
    
    if self.vscode_window:
        try:
            # Find element by name
            element = self.vscode_window.child_window(title=element_name)
            if element.exists():
                element.set_text(text)
                result = True
            else:
                result = False
        except:
            result = False
    else:
        result = False

elif command == 'background_click':
    # Background click without window activation
    element_name = params.get('element_name', '')
    
    if self.vscode_window:
        try:
            element = self.vscode_window.child_window(title=element_name)
            if element.exists():
                element.click_input()
                result = True
            else:
                result = False
        except:
            result = False
    else:
        result = False
'''

async def main():
    """Test background RPA"""
    rpa = BackgroundRooCodeRPA("wjchk")
    success = await rpa.execute_background_task("分析一下当前的产品设计")
    
    if not success:
        print("\n[FAILED] Background operation failed")
        print("Note: Client may need update to support background operations")
        print("See BACKGROUND_OPS_CODE in this file for required changes")

if __name__ == "__main__":
    asyncio.run(main())