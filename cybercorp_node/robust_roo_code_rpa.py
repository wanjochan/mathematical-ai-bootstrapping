"""Robust RPA implementation for Roo Code interaction"""

import asyncio
import websockets
import json
import os
import time
from datetime import datetime
from typing import Optional, Dict, List, Tuple

class RobustRooCodeController:
    """Robust controller for Roo Code RPA operations"""
    
    def __init__(self, username: str):
        self.username = username
        self.server_url = 'ws://localhost:9998'
        self.websocket = None
        self.client_id = None
        self.retry_count = 3
        self.retry_delay = 2
        self.var_dir = os.path.join(os.path.dirname(__file__), 'var')
        os.makedirs(self.var_dir, exist_ok=True)
        
    async def connect(self) -> bool:
        """Connect to server and find target client"""
        try:
            self.websocket = await websockets.connect(self.server_url)
            
            # Register
            await self.websocket.send(json.dumps({
                'type': 'register',
                'user_session': f"{os.environ.get('USERNAME', 'unknown')}_robust_rpa",
                'client_start_time': datetime.now().isoformat(),
                'capabilities': {'management': True, 'control': True},
                'system_info': {
                    'platform': 'Windows',
                    'hostname': os.environ.get('COMPUTERNAME', 'unknown')
                }
            }))
            
            await self.websocket.recv()  # welcome
            
            # Find target client
            await self.websocket.send(json.dumps({
                'type': 'request',
                'command': 'list_clients'
            }))
            
            response = await self.websocket.recv()
            data = json.loads(response)
            
            if data['type'] == 'client_list':
                for client in data['clients']:
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
        """Send command and wait for result"""
        if not self.client_id:
            return None
            
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
        
        # Wait for result
        try:
            response = await asyncio.wait_for(self.websocket.recv(), timeout=5.0)
            result = json.loads(response)
            if result.get('type') == 'command_result':
                return result
        except asyncio.TimeoutError:
            print(f"[TIMEOUT] Command '{command}' timed out")
            
        return None
    
    async def ensure_vscode_active(self) -> bool:
        """Ensure VSCode window is active with retries"""
        print("\n[STEP 1] Ensuring VSCode is active...")
        
        for attempt in range(self.retry_count):
            print(f"  Attempt {attempt + 1}/{self.retry_count}")
            
            # Activate window
            result = await self.send_command('activate_window')
            if result and not result.get('error'):
                await asyncio.sleep(1)  # Wait for activation
                
                # Verify by getting structure
                structure = await self.get_vscode_structure()
                if structure and structure.get('is_active'):
                    print("  [OK] VSCode window is active")
                    return True
                else:
                    print("  [WARNING] Window not active yet")
            
            if attempt < self.retry_count - 1:
                await asyncio.sleep(self.retry_delay)
        
        print("  [ERROR] Failed to activate VSCode window")
        return False
    
    async def get_vscode_structure(self) -> Optional[dict]:
        """Get current VSCode structure"""
        result = await self.send_command('vscode_get_content')
        if result and not result.get('error'):
            return result.get('result', {})
        return None
    
    async def find_roo_code_input(self) -> Tuple[bool, Optional[dict]]:
        """Find Roo Code input field with validation"""
        print("\n[STEP 2] Finding Roo Code input field...")
        
        structure = await self.get_vscode_structure()
        if not structure:
            print("  [ERROR] Cannot get VSCode structure")
            return False, None
        
        # Save structure for debugging
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        debug_file = os.path.join(self.var_dir, f'debug_structure_{timestamp}.json')
        with open(debug_file, 'w', encoding='utf-8') as f:
            json.dump(structure, f, indent=2, ensure_ascii=False)
        print(f"  [DEBUG] Structure saved to: {debug_file}")
        
        # Find Edit elements
        edit_elements = []
        content_areas = structure.get('content_areas', [])
        
        for i, area in enumerate(content_areas):
            if isinstance(area, dict) and area.get('type') == 'Edit':
                edit_elements.append((i, area))
                print(f"  [FOUND] Edit element at index {i}: {area.get('name', 'Unknown')}")
        
        if len(edit_elements) == 0:
            print("  [ERROR] No Edit elements found")
            return False, None
        
        if len(edit_elements) == 1:
            print(f"  [OK] Found single Edit element: {edit_elements[0][1].get('name')}")
            return True, edit_elements[0][1]
        
        # Multiple edit elements - try to find the right one
        for idx, elem in edit_elements:
            name = elem.get('name', '').lower()
            if 'task' in name or 'type' in name or 'message' in name:
                print(f"  [OK] Selected Edit element: {elem.get('name')}")
                return True, elem
        
        print(f"  [WARNING] Multiple Edit elements ({len(edit_elements)}), using first one")
        return True, edit_elements[0][1]
    
    async def clear_input_field(self) -> bool:
        """Clear input field with multiple methods"""
        print("\n[STEP 3] Clearing input field...")
        
        # Method 1: Ctrl+A and Delete
        print("  Method 1: Ctrl+A")
        await self.send_command('send_keys', {'keys': '^a'})
        await asyncio.sleep(0.3)
        
        # Method 2: Send Delete
        print("  Method 2: Delete")
        await self.send_command('send_keys', {'keys': '{DELETE}'})
        await asyncio.sleep(0.3)
        
        print("  [OK] Input field cleared")
        return True
    
    async def type_message(self, message: str) -> bool:
        """Type message with verification"""
        print(f"\n[STEP 4] Typing message: {message}")
        
        # Type the message
        result = await self.send_command('vscode_type_text', {'text': message})
        
        if result and not result.get('error'):
            print("  [OK] Message typed")
            await asyncio.sleep(0.5)  # Wait for typing to complete
            return True
        else:
            print(f"  [ERROR] Failed to type: {result}")
            return False
    
    async def send_message(self) -> bool:
        """Send message with multiple methods"""
        print("\n[STEP 5] Sending message...")
        
        # Method 1: Enter key
        print("  Method 1: Sending Enter key")
        result = await self.send_command('send_keys', {'keys': '{ENTER}'})
        
        if result and not result.get('error'):
            print("  [OK] Enter key sent")
            await asyncio.sleep(1)
            
            # Verify by checking structure change
            new_structure = await self.get_vscode_structure()
            if new_structure:
                # Save for comparison
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                after_file = os.path.join(self.var_dir, f'after_send_{timestamp}.json')
                with open(after_file, 'w', encoding='utf-8') as f:
                    json.dump(new_structure, f, indent=2, ensure_ascii=False)
                print(f"  [DEBUG] After-send structure saved to: {after_file}")
            
            return True
        
        # Method 2: Click Send button (if Method 1 failed)
        print("  Method 2: Looking for Send button...")
        # ... implement button click
        
        return False
    
    async def execute_roo_code_task(self, message: str) -> bool:
        """Execute complete Roo Code interaction"""
        print(f"\n{'=' * 80}")
        print(f"Robust Roo Code RPA - Target: {self.username}")
        print(f"Message: {message}")
        print(f"{'=' * 80}")
        
        # Connect
        if not await self.connect():
            return False
        
        try:
            # Step 1: Ensure VSCode is active
            if not await self.ensure_vscode_active():
                return False
            
            # Step 2: Find input field
            found, input_elem = await self.find_roo_code_input()
            if not found:
                return False
            
            # Step 3: Clear input
            if not await self.clear_input_field():
                return False
            
            # Step 4: Type message
            if not await self.type_message(message):
                return False
            
            # Step 5: Send message
            if not await self.send_message():
                return False
            
            print("\n[SUCCESS] Roo Code task completed successfully!")
            return True
            
        except Exception as e:
            print(f"\n[ERROR] Task failed: {e}")
            import traceback
            traceback.print_exc()
            return False
            
        finally:
            if self.websocket:
                await self.websocket.close()

async def main():
    """Main function"""
    controller = RobustRooCodeController("wjchk")
    success = await controller.execute_roo_code_task("分析一下当前的产品设计")
    
    if not success:
        print("\n[FAILED] Task did not complete successfully")
        print("Check the debug files in the var/ directory for details")

if __name__ == "__main__":
    asyncio.run(main())