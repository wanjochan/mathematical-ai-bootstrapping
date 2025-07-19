"""Analyze RPA operation failures and design robust solutions"""

import json
import os
from datetime import datetime

def analyze_vscode_structure():
    """Analyze the VSCode structure to understand why RPA failed"""
    
    var_dir = os.path.join(os.path.dirname(__file__), 'var')
    
    # Find the latest VSCode structure file
    structure_files = [f for f in os.listdir(var_dir) if f.startswith('vscode_structure_')]
    if not structure_files:
        print("No VSCode structure files found")
        return None
    
    latest_file = sorted(structure_files)[-1]
    filepath = os.path.join(var_dir, latest_file)
    
    print(f"Analyzing: {latest_file}")
    print("=" * 80)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Analysis results
    analysis = {
        'window_state': data.get('is_active', False),
        'total_elements': len(data.get('content_areas', [])),
        'edit_elements': [],
        'button_elements': [],
        'roo_elements': [],
        'potential_issues': []
    }
    
    # Analyze elements
    content_areas = data.get('content_areas', [])
    for area in content_areas:
        if isinstance(area, dict):
            elem_type = area.get('type', '').lower()
            name = area.get('name', '').lower()
            
            # Categorize elements
            if elem_type == 'edit':
                analysis['edit_elements'].append({
                    'name': area.get('name'),
                    'type': area.get('type'),
                    'texts': area.get('texts', [])
                })
            
            if elem_type == 'button':
                analysis['button_elements'].append({
                    'name': area.get('name'),
                    'type': area.get('type')
                })
            
            if 'roo' in name or 'code' in name:
                analysis['roo_elements'].append({
                    'name': area.get('name'),
                    'type': area.get('type')
                })
    
    # Identify potential issues
    if not analysis['window_state']:
        analysis['potential_issues'].append("VSCode window is not active")
    
    if len(analysis['edit_elements']) == 0:
        analysis['potential_issues'].append("No Edit elements found - input field not detected")
    elif len(analysis['edit_elements']) > 1:
        analysis['potential_issues'].append(f"Multiple Edit elements found ({len(analysis['edit_elements'])}) - ambiguous target")
    
    send_buttons = [b for b in analysis['button_elements'] if 'send' in b['name'].lower()]
    if len(send_buttons) == 0:
        analysis['potential_issues'].append("No Send button found")
    
    # Check for Roo Code dialog state
    roo_dialog_open = any('roo code' in elem['name'].lower() for elem in analysis['roo_elements'])
    if not roo_dialog_open:
        analysis['potential_issues'].append("Roo Code dialog might not be open")
    
    return analysis

def design_robust_strategy():
    """Design a robust RPA strategy based on analysis"""
    
    strategy = {
        'pre_checks': [
            'Verify VSCode window exists',
            'Check if VSCode is responsive',
            'Ensure Roo Code extension is loaded',
            'Verify Roo Code panel is visible'
        ],
        'element_location': [
            'Use multiple selectors (name, type, position)',
            'Implement fuzzy matching for element names',
            'Use relative positioning from known elements',
            'Cache element positions for faster access'
        ],
        'input_strategy': [
            'Click on input field before typing',
            'Use multiple clear methods (Ctrl+A, triple-click)',
            'Verify field is empty before typing',
            'Type in chunks with verification'
        ],
        'send_strategy': [
            'Try multiple send methods (Enter, button click, Ctrl+Enter)',
            'Verify message appears in chat history',
            'Check for loading indicators',
            'Implement timeout and retry logic'
        ],
        'verification': [
            'Screenshot before and after',
            'Check UI element states',
            'Monitor for error messages',
            'Validate response appears'
        ]
    }
    
    return strategy

def generate_robust_rpa_code():
    """Generate improved RPA code template"""
    
    template = '''"""Robust RPA for VSCode Roo Code interaction"""

import asyncio
import time
from typing import Optional, Dict, List

class RobustRooCodeRPA:
    def __init__(self, client_id: str, websocket):
        self.client_id = client_id
        self.websocket = websocket
        self.retry_count = 3
        self.retry_delay = 2
    
    async def ensure_vscode_ready(self) -> bool:
        """Ensure VSCode is ready for interaction"""
        
        # Step 1: Activate window
        for attempt in range(self.retry_count):
            success = await self.activate_window()
            if success:
                await asyncio.sleep(1)  # Wait for activation
                
                # Verify activation by getting window state
                state = await self.get_window_state()
                if state.get('is_active'):
                    return True
            
            await asyncio.sleep(self.retry_delay)
        
        return False
    
    async def find_roo_code_input(self) -> Optional[Dict]:
        """Find the Roo Code input field with multiple strategies"""
        
        structure = await self.get_vscode_structure()
        if not structure:
            return None
        
        # Strategy 1: Find by exact type and name
        for elem in structure.get('content_areas', []):
            if elem.get('type') == 'Edit' and 'type your task' in elem.get('name', '').lower():
                return elem
        
        # Strategy 2: Find any Edit element near Roo elements
        edit_elements = [e for e in structure.get('content_areas', []) if e.get('type') == 'Edit']
        roo_elements = [e for e in structure.get('content_areas', []) if 'roo' in e.get('name', '').lower()]
        
        if len(edit_elements) == 1:
            return edit_elements[0]
        
        # Strategy 3: Use UI Automation to find by pattern
        # ... more strategies
        
        return None
    
    async def clear_and_type(self, text: str) -> bool:
        """Clear input field and type text with verification"""
        
        # Method 1: Click and select all
        await self.send_keys('^a')  # Ctrl+A
        await asyncio.sleep(0.2)
        
        # Method 2: Triple click
        # await self.triple_click_input()
        
        # Type text
        success = await self.type_text(text)
        if not success:
            return False
        
        # Verify text was typed
        await asyncio.sleep(0.5)
        # ... verification logic
        
        return True
    
    async def send_message(self) -> bool:
        """Send message with multiple methods"""
        
        # Method 1: Enter key
        success = await self.send_keys('{ENTER}')
        if success:
            return await self.verify_message_sent()
        
        # Method 2: Click send button
        # ... button click logic
        
        # Method 3: Ctrl+Enter
        # ... alternative send
        
        return False
    
    async def verify_message_sent(self) -> bool:
        """Verify the message was sent successfully"""
        
        await asyncio.sleep(1)
        
        # Check for changes in UI
        # Check for loading indicators
        # Check for response
        
        return True

# Usage
async def robust_send_to_roo(username: str, message: str):
    """Main function with full error handling"""
    
    rpa = RobustRooCodeRPA(client_id, websocket)
    
    # Pre-flight checks
    if not await rpa.ensure_vscode_ready():
        raise Exception("VSCode not ready")
    
    # Find input
    input_elem = await rpa.find_roo_code_input()
    if not input_elem:
        raise Exception("Cannot find Roo Code input")
    
    # Type and send
    if not await rpa.clear_and_type(message):
        raise Exception("Failed to type message")
    
    if not await rpa.send_message():
        raise Exception("Failed to send message")
    
    return True
'''
    
    return template

if __name__ == "__main__":
    print("RPA Failure Analysis")
    print("=" * 80)
    
    # Analyze current state
    analysis = analyze_vscode_structure()
    
    if analysis:
        print("\nCurrent State Analysis:")
        print(f"- Window Active: {analysis['window_state']}")
        print(f"- Total Elements: {analysis['total_elements']}")
        print(f"- Edit Elements: {len(analysis['edit_elements'])}")
        print(f"- Button Elements: {len(analysis['button_elements'])}")
        print(f"- Roo Elements: {len(analysis['roo_elements'])}")
        
        if analysis['potential_issues']:
            print("\nPotential Issues:")
            for issue in analysis['potential_issues']:
                print(f"  [WARNING] {issue}")
        
        print("\nEdit Elements Found:")
        for elem in analysis['edit_elements']:
            print(f"  - {elem['name']} ({elem['type']})")
            if elem['texts']:
                print(f"    Texts: {elem['texts']}")
    
    # Show robust strategy
    print("\n" + "=" * 80)
    print("Robust RPA Strategy")
    print("=" * 80)
    
    strategy = design_robust_strategy()
    for category, items in strategy.items():
        print(f"\n{category.upper()}:")
        for item in items:
            print(f"  [OK] {item}")
    
    # Save template
    var_dir = os.path.join(os.path.dirname(__file__), 'var')
    os.makedirs(var_dir, exist_ok=True)
    
    template_file = os.path.join(var_dir, 'robust_rpa_template.py')
    with open(template_file, 'w', encoding='utf-8') as f:
        f.write(generate_robust_rpa_code())
    
    print(f"\nRobust RPA template saved to: {template_file}")