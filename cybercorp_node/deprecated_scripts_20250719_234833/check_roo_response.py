"""Check Roo Code's response to our task"""

import asyncio
import websockets
import json
import os
from datetime import datetime
import difflib

class RooResponseChecker:
    """Check how Roo Code processed the task"""
    
    def __init__(self, username: str):
        self.username = username
        self.server_url = 'ws://localhost:9998'
        self.websocket = None
        self.client_id = None
        self.var_dir = os.path.join(os.path.dirname(__file__), 'var')
        
    async def connect(self) -> bool:
        """Connect to server"""
        try:
            self.websocket = await websockets.connect(self.server_url)
            
            await self.websocket.send(json.dumps({
                'type': 'register',
                'user_session': f"{os.environ.get('USERNAME', 'unknown')}_response_checker",
                'client_start_time': datetime.now().isoformat(),
                'capabilities': {'management': True, 'control': True}
            }))
            
            await self.websocket.recv()
            
            # Find target client
            await self.websocket.send(json.dumps({
                'type': 'request',
                'command': 'list_clients'
            }))
            
            response = await self.websocket.recv()
            data = json.loads(response)
            
            for client in data.get('clients', []):
                if client.get('user_session') == self.username:
                    self.client_id = client['id']
                    return True
                    
            return False
            
        except Exception as e:
            print(f"Connection error: {e}")
            return False
    
    async def get_current_ui(self) -> dict:
        """Get current UI structure"""
        await self.websocket.send(json.dumps({
            'type': 'forward_command',
            'target_client': self.client_id,
            'command': {
                'type': 'command',
                'command': 'vscode_get_content'
            }
        }))
        
        await self.websocket.recv()
        
        try:
            response = await asyncio.wait_for(self.websocket.recv(), timeout=5.0)
            result = json.loads(response)
            if result.get('type') == 'command_result':
                return result.get('result', {})
        except:
            pass
            
        return {}
    
    async def analyze_roo_response(self):
        """Analyze Roo's response to the task"""
        print(f"\nChecking Roo Code Response for user: {self.username}")
        print("=" * 80)
        
        if not await self.connect():
            print("Failed to connect")
            return
        
        try:
            # Get current UI
            current_ui = await self.get_current_ui()
            if not current_ui:
                print("Failed to get UI")
                return
            
            # Save current state
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            current_file = os.path.join(self.var_dir, f'roo_response_{timestamp}.json')
            with open(current_file, 'w', encoding='utf-8') as f:
                json.dump(current_ui, f, indent=2, ensure_ascii=False)
            print(f"Current UI saved: {current_file}")
            
            # Extract text content
            print("\n[1] Analyzing UI Content")
            print("-" * 60)
            
            all_texts = []
            content_areas = current_ui.get('content_areas', [])
            
            # Look for response indicators
            response_found = False
            task_elements = []
            chat_elements = []
            
            for area in content_areas:
                if isinstance(area, dict):
                    texts = area.get('texts', [])
                    name = area.get('name', '')
                    elem_type = area.get('type', '')
                    
                    # Collect all text
                    for text in texts:
                        if isinstance(text, str) and len(text.strip()) > 0:
                            all_texts.append(text)
                        elif isinstance(text, list):
                            # Handle nested lists
                            for t in text:
                                if isinstance(t, str) and len(t.strip()) > 0:
                                    all_texts.append(t)
                    
                    # Look for task/chat related elements
                    if any(keyword in name.lower() for keyword in ['task', 'chat', 'message', 'response', 'roo']):
                        task_elements.append({
                            'name': name,
                            'type': elem_type,
                            'texts': texts
                        })
                    
                    # Look for our original message
                    if any('分析一下当前的产品设计' in str(t) for t in texts):
                        response_found = True
                        print(f"  [FOUND] Our task in element: {name}")
                    
                    # Look for response patterns
                    for text in texts:
                        text_lower = str(text).lower()
                        if any(keyword in text_lower for keyword in ['产品', '设计', '分析', '功能', '架构']):
                            if '分析一下当前的产品设计' not in text:  # Not our input
                                chat_elements.append({
                                    'element': name,
                                    'text': text[:200] + '...' if len(text) > 200 else text
                                })
            
            # Display findings
            print(f"\n[2] Task Elements Found: {len(task_elements)}")
            for elem in task_elements[:5]:  # First 5
                print(f"  - {elem['name']} ({elem['type']})")
                if elem['texts']:
                    print(f"    Sample text: {elem['texts'][0][:100]}...")
            
            print(f"\n[3] Potential Response Elements: {len(chat_elements)}")
            for elem in chat_elements[:5]:  # First 5
                print(f"  - From: {elem['element']}")
                print(f"    Text: {elem['text']}")
            
            # Compare with previous state
            print("\n[4] Comparing with Previous State")
            print("-" * 60)
            
            # Find previous UI files
            ui_files = [f for f in os.listdir(self.var_dir) if f.startswith('background_ui_') or f.startswith('roo_response_')]
            ui_files.sort()
            
            if len(ui_files) >= 2:
                # Compare with previous
                prev_file = os.path.join(self.var_dir, ui_files[-2])
                with open(prev_file, 'r', encoding='utf-8') as f:
                    prev_ui = json.load(f)
                
                prev_texts = []
                for area in prev_ui.get('content_areas', []):
                    if isinstance(area, dict):
                        prev_texts.extend(area.get('texts', []))
                
                # Find new texts
                new_texts = [t for t in all_texts if t not in prev_texts]
                
                print(f"  Previous file: {ui_files[-2]}")
                print(f"  New text elements: {len(new_texts)}")
                
                if new_texts:
                    print("\n  New content detected:")
                    for i, text in enumerate(new_texts[:10], 1):  # First 10
                        if len(text) > 20:  # Significant text
                            print(f"    [{i}] {text[:150]}...")
            
            # Look for Roo's response patterns
            print("\n[5] Roo Response Analysis")
            print("-" * 60)
            
            response_indicators = [
                "根据", "分析", "产品设计", "功能", "架构", "模块",
                "Based on", "analysis", "product", "design", "architecture"
            ]
            
            likely_responses = []
            for text in all_texts:
                if len(text) > 50:  # Substantial text
                    score = sum(1 for indicator in response_indicators if indicator in text)
                    if score >= 2:  # Multiple indicators
                        likely_responses.append((score, text))
            
            if likely_responses:
                likely_responses.sort(reverse=True, key=lambda x: x[0])
                print("  Likely Roo responses found:")
                for score, text in likely_responses[:3]:  # Top 3
                    print(f"\n  Score {score}: {text[:300]}...")
            else:
                print("  No clear response detected yet.")
                print("  Roo might still be processing or response might be in a different format.")
            
            # Summary
            print("\n[6] Summary")
            print("-" * 60)
            print(f"  Task sent: 分析一下当前的产品设计")
            print(f"  Task found in UI: {'Yes' if response_found else 'No'}")
            print(f"  New content detected: {'Yes' if new_texts else 'No'}")
            print(f"  Likely response found: {'Yes' if likely_responses else 'No'}")
            
            if not likely_responses:
                print("\n  Suggestions:")
                print("  - Roo might still be processing the request")
                print("  - Response might be in a different UI element")
                print("  - Try taking a screenshot to see visual response")
                
        finally:
            if self.websocket:
                await self.websocket.close()

async def main():
    """Check Roo's response"""
    checker = RooResponseChecker("wjchk")
    await checker.analyze_roo_response()

if __name__ == "__main__":
    asyncio.run(main())