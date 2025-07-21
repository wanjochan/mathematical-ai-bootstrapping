"""Smart Cursor interaction using Vision + UIA + intelligent decision"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
from cybercorp_node.utils.remote_control import RemoteController
from cybercorp_node.utils.vision_integration import VisionWindowAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SmartCursorController:
    """Intelligent Cursor controller using Vision + UIA"""
    
    def __init__(self, remote_controller):
        self.controller = remote_controller
        self.vision_analyzer = VisionWindowAnalyzer(remote_controller)
        
    async def find_and_interact(self):
        """Smart interaction with Cursor using multiple data sources"""
        
        print("🧠 智能Cursor交互系统")
        print("=" * 50)
        
        # Step 1: Find Cursor window
        cursor_hwnd = await self.find_cursor_window()
        if not cursor_hwnd:
            print("❌ 未找到Cursor窗口")
            return False
            
        print(f"✅ 找到Cursor窗口: {cursor_hwnd}")
        
        # Step 2: Visual analysis
        print("\n📸 步骤1: 视觉分析窗口")
        visual_data = await self.analyze_window_visually(cursor_hwnd)
        
        # Step 3: UIA analysis
        print("\n🔍 步骤2: UIA结构分析")
        uia_data = await self.analyze_window_uia(cursor_hwnd)
        
        # Step 4: Combine data and make intelligent decision
        print("\n🤔 步骤3: 智能决策")
        input_location = await self.determine_input_location(visual_data, uia_data)
        
        if not input_location:
            print("❌ 无法确定输入位置")
            return False
            
        # Step 5: Execute interaction
        print("\n🎯 步骤4: 执行交互")
        success = await self.execute_interaction(cursor_hwnd, input_location)
        
        return success
        
    async def find_cursor_window(self):
        """Find Cursor window intelligently"""
        windows = await self.controller.get_windows()
        
        # Score windows based on multiple criteria
        cursor_candidates = []
        
        for window in windows:
            title = window.get('title', '').lower()
            score = 0
            
            # Title matching
            if 'cursor' in title and 'visual studio code' not in title:
                score += 10
            elif 'cursor' in title:
                score += 5
                
            # Window characteristics
            if window.get('visible'):
                score += 2
                
            # Add to candidates if score > 0
            if score > 0:
                cursor_candidates.append((window['hwnd'], score, window['title']))
                
        # Sort by score and return best match
        if cursor_candidates:
            cursor_candidates.sort(key=lambda x: x[1], reverse=True)
            return cursor_candidates[0][0]
            
        return None
        
    async def analyze_window_visually(self, hwnd):
        """Use vision to analyze window layout"""
        try:
            # Capture window
            result = await self.controller.execute_command('capture_window', {'hwnd': hwnd})
            if not result or not result.get('success'):
                print("   ❌ 截图失败")
                return None
                
            print("   ✅ 截图成功")
            
            # Analyze with vision
            analysis = await self.vision_analyzer.analyze_window(hwnd)
            
            if analysis:
                print("   ✅ 视觉分析完成")
                
                # Extract UI elements
                ui_elements = {
                    'input_areas': [],
                    'buttons': [],
                    'text_areas': []
                }
                
                # Process vision results
                if hasattr(analysis, 'ui_elements'):
                    for elem in analysis.ui_elements:
                        if elem.type in ['input', 'textbox', 'textarea']:
                            ui_elements['input_areas'].append({
                                'bbox': elem.bbox,
                                'confidence': elem.confidence
                            })
                        elif elem.type in ['button', 'submit']:
                            ui_elements['buttons'].append({
                                'bbox': elem.bbox,
                                'text': elem.text
                            })
                            
                print(f"   找到输入区域: {len(ui_elements['input_areas'])}")
                print(f"   找到按钮: {len(ui_elements['buttons'])}")
                
                return ui_elements
                
        except Exception as e:
            print(f"   视觉分析错误: {e}")
            
        return None
        
    async def analyze_window_uia(self, hwnd):
        """Use UIA to analyze window structure"""
        try:
            # Get UIA tree
            uia_result = await self.controller.execute_command('get_uia_tree', {
                'hwnd': hwnd,
                'max_depth': 5
            })
            
            if not uia_result:
                # Fallback to child enumeration
                result = await self.controller.execute_command('enum_child_windows', {'hwnd': hwnd})
                if result and 'children' in result:
                    print(f"   ✅ 找到 {len(result['children'])} 个子窗口")
                    
                    # Find interactive elements
                    interactive_elements = []
                    for child in result['children']:
                        class_name = child.get('class_name', '').lower()
                        if any(keyword in class_name for keyword in ['edit', 'input', 'text']):
                            interactive_elements.append({
                                'hwnd': child['hwnd'],
                                'class': class_name,
                                'type': 'input'
                            })
                            
                    print(f"   找到可交互元素: {len(interactive_elements)}")
                    return {'elements': interactive_elements}
                    
            else:
                print("   ✅ UIA树获取成功")
                # Process UIA tree
                return self.process_uia_tree(uia_result)
                
        except Exception as e:
            print(f"   UIA分析错误: {e}")
            
        return None
        
    def process_uia_tree(self, uia_tree):
        """Process UIA tree to find interactive elements"""
        elements = []
        
        def traverse(node):
            if not node:
                return
                
            # Check if this is an input element
            control_type = node.get('control_type', '').lower()
            if any(t in control_type for t in ['edit', 'text', 'input']):
                elements.append({
                    'id': node.get('id'),
                    'type': control_type,
                    'name': node.get('name'),
                    'value': node.get('value')
                })
                
            # Traverse children
            for child in node.get('children', []):
                traverse(child)
                
        traverse(uia_tree.get('tree', {}))
        return {'elements': elements}
        
    async def determine_input_location(self, visual_data, uia_data):
        """Intelligently determine where to input text"""
        print("\n   分析数据并决策...")
        
        # Priority 1: Visual input areas
        if visual_data and visual_data.get('input_areas'):
            best_input = max(visual_data['input_areas'], 
                           key=lambda x: x['confidence'])
            bbox = best_input['bbox']
            
            # Convert bbox to click position (center)
            x = (bbox[0] + bbox[2]) // 2
            y = (bbox[1] + bbox[3]) // 2
            
            print(f"   ✅ 视觉识别输入位置: ({x}, {y})")
            return {'method': 'visual', 'x': x, 'y': y}
            
        # Priority 2: UIA elements
        if uia_data and uia_data.get('elements'):
            for elem in uia_data['elements']:
                if elem.get('hwnd'):
                    print(f"   ✅ UIA找到输入控件: {elem['hwnd']}")
                    return {'method': 'uia', 'hwnd': elem['hwnd']}
                    
        # Priority 3: Heuristic positions
        print("   ⚠️ 使用启发式位置")
        # Common positions for chat input in Cursor
        return {
            'method': 'heuristic',
            'positions': [
                {'desc': '右下角', 'x_ratio': 0.75, 'y_ratio': 0.85},
                {'desc': '底部中央', 'x_ratio': 0.5, 'y_ratio': 0.9},
                {'desc': '右侧中部', 'x_ratio': 0.75, 'y_ratio': 0.6}
            ]
        }
        
    async def execute_interaction(self, cursor_hwnd, location):
        """Execute the interaction based on determined location"""
        
        messages = [
            "你好！我想跟你深入讨论AGI的技术路线。",
            "你认为当前的Transformer架构还能走多远？",
            "智能涌现是真实现象还是我们的错觉？",
            "AGI需要具备意识吗？",
            "多模态能力对AGI有多重要？"
        ]
        
        success_count = 0
        
        for i, message in enumerate(messages):
            print(f"\n💬 发送消息 {i+1}: {message[:30]}...")
            
            if location['method'] == 'visual':
                # Click at visual position
                success = await self.send_at_position(cursor_hwnd, location['x'], location['y'], message)
                
            elif location['method'] == 'uia':
                # Use UIA hwnd
                success = await self.send_to_hwnd(location['hwnd'], message)
                
            elif location['method'] == 'heuristic':
                # Try multiple positions
                success = await self.try_heuristic_positions(cursor_hwnd, location['positions'], message)
                
            if success:
                success_count += 1
                print(f"   ✅ 消息 {i+1} 发送成功")
                await asyncio.sleep(5)  # Wait for response
            else:
                print(f"   ❌ 消息 {i+1} 发送失败")
                
        print(f"\n🎯 成功发送 {success_count}/{len(messages)} 条消息")
        return success_count > 0
        
    async def send_at_position(self, hwnd, x, y, message):
        """Send message at specific position"""
        try:
            # Activate window
            await self.controller.execute_command('win32_call', {
                'function': 'SetForegroundWindow',
                'args': [hwnd]
            })
            await asyncio.sleep(0.5)
            
            # Click position
            await self.controller.execute_command('click', {'x': x, 'y': y})
            await asyncio.sleep(0.3)
            
            # Clear and type
            await self.controller.execute_command('send_keys', {'keys': '^a'})
            await asyncio.sleep(0.1)
            await self.controller.execute_command('send_keys', {'keys': '{DELETE}'})
            await asyncio.sleep(0.2)
            await self.controller.execute_command('send_keys', {'keys': message})
            await asyncio.sleep(0.5)
            
            # Send
            await self.controller.execute_command('send_keys', {'keys': '{ENTER}'})
            return True
            
        except Exception as e:
            logger.error(f"Position send error: {e}")
            return False
            
    async def send_to_hwnd(self, hwnd, message):
        """Send message to specific hwnd using Win32"""
        try:
            # Clear
            await self.controller.execute_command('win32_call', {
                'function': 'SendMessage',
                'args': [hwnd, 0x000C, 0, ""]  # WM_SETTEXT
            })
            
            # Set text
            await self.controller.execute_command('win32_call', {
                'function': 'SendMessage',
                'args': [hwnd, 0x000C, 0, message]
            })
            
            # Send Enter
            await self.controller.execute_command('win32_call', {
                'function': 'SendMessage',
                'args': [hwnd, 0x0100, 0x0D, 0]  # WM_KEYDOWN Enter
            })
            
            return True
            
        except Exception as e:
            logger.error(f"HWND send error: {e}")
            return False
            
    async def try_heuristic_positions(self, hwnd, positions, message):
        """Try multiple heuristic positions"""
        # Get window size
        try:
            window_info = await self.controller.execute_command('get_window_info', {'hwnd': hwnd})
            if window_info and 'rect' in window_info:
                rect = window_info['rect']
                width = rect[2] - rect[0]
                height = rect[3] - rect[1]
            else:
                width = 1200
                height = 800
                
            # Try each position
            for pos in positions:
                x = int(width * pos['x_ratio'])
                y = int(height * pos['y_ratio'])
                print(f"   尝试{pos['desc']}位置 ({x}, {y})")
                
                if await self.send_at_position(hwnd, x, y, message):
                    return True
                    
        except Exception as e:
            logger.error(f"Heuristic error: {e}")
            
        return False


async def main():
    """Main function"""
    print("智能Cursor交互测试")
    print("使用视觉识别 + UIA + 智能决策")
    print("")
    
    try:
        # Connect
        remote_controller = RemoteController()
        await remote_controller.connect("smart_cursor")
        
        target_client = await remote_controller.find_client("wjc2022")
        if not target_client:
            print("❌ 未找到客户端")
            return
            
        print(f"✅ 已连接: {target_client}\n")
        
        # Create smart controller
        smart_controller = SmartCursorController(remote_controller)
        
        # Run interaction
        success = await smart_controller.find_and_interact()
        
        if success:
            print("\n" + "=" * 50)
            print("🎉 智能交互成功！")
            print("系统成功：")
            print("• 使用视觉识别定位UI元素")
            print("• 结合UIA获取结构信息")
            print("• 智能决策最佳交互方式")
            print("• 成功发送多轮对话消息")
            print("=" * 50)
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())