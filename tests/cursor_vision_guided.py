"""Vision-guided Cursor interaction"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from cybercorp_node.utils.remote_control import RemoteController
from cybercorp_node.utils.vision_integration import VisionWindowAnalyzer


async def vision_guided_cursor_interaction():
    """Use vision to analyze Cursor UI and interact intelligently"""
    
    print("🎯 视觉引导的Cursor交互")
    print("=" * 50)
    
    try:
        # Connect
        controller = RemoteController()
        await controller.connect("vision_cursor")
        
        target = await controller.find_client("wjc2022")
        if not target:
            return
            
        print(f"✅ 已连接: {target}")
        
        # Initialize vision analyzer
        vision = VisionWindowAnalyzer(controller)
        
        # Find Cursor window
        cursor_hwnd = 7670670
        print(f"\n📸 分析Cursor窗口 (HWND: {cursor_hwnd})")
        
        # Step 1: Capture and analyze window
        print("\n1. 截图并分析窗口UI结构...")
        
        # Capture window
        capture_result = await controller.execute_command('capture_window', {
            'hwnd': cursor_hwnd
        })
        
        if not capture_result or not capture_result.get('success'):
            print("❌ 截图失败，使用全屏截图")
            capture_result = await controller.execute_command('screenshot')
        
        # Analyze with vision
        print("2. 使用视觉AI分析UI元素...")
        
        analysis = await vision.analyze_window(cursor_hwnd)
        
        if analysis and hasattr(analysis, 'ui_elements'):
            print(f"✅ 找到 {len(analysis.ui_elements)} 个UI元素")
            
            # Find input areas
            input_areas = []
            buttons = []
            
            for elem in analysis.ui_elements:
                if elem.type in ['input', 'textbox', 'textarea', 'edit']:
                    input_areas.append({
                        'type': elem.type,
                        'bbox': elem.bbox,  # [x1, y1, x2, y2]
                        'confidence': elem.confidence
                    })
                    print(f"  - 输入框: {elem.bbox} (置信度: {elem.confidence:.2f})")
                elif elem.type in ['button', 'submit']:
                    buttons.append({
                        'text': elem.text,
                        'bbox': elem.bbox
                    })
                    print(f"  - 按钮: {elem.text} at {elem.bbox}")
            
            if input_areas:
                # Use the input area with highest confidence
                best_input = max(input_areas, key=lambda x: x['confidence'])
                bbox = best_input['bbox']
                
                # Calculate click position (center of bbox)
                x = (bbox[0] + bbox[2]) // 2
                y = (bbox[1] + bbox[3]) // 2
                
                print(f"\n3. 最佳输入位置: ({x}, {y})")
                print(f"   区域: {bbox}")
                print(f"   置信度: {best_input['confidence']:.2f}")
                
                # Now interact
                await interact_at_position(controller, cursor_hwnd, x, y)
            else:
                print("❌ 未找到输入框，尝试备用方法")
                await fallback_interaction(controller, cursor_hwnd, analysis)
        else:
            print("❌ 视觉分析失败，使用启发式方法")
            await heuristic_interaction(controller, cursor_hwnd)
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


async def interact_at_position(controller, hwnd, x, y):
    """Interact at the vision-detected position"""
    print(f"\n4. 在检测到的位置交互...")
    
    # Activate window
    await controller.execute_command('win32_call', {
        'function': 'SetForegroundWindow',
        'args': [hwnd]
    })
    await asyncio.sleep(0.5)
    
    # Messages for AGI discussion
    messages = [
        "你好！我想深入讨论AGI的技术路线。",
        "你认为当前大模型离AGI还有多远？",
        "Scaling law会一直有效吗？",
        "意识对AGI是必要的吗？",
        "多模态融合的关键挑战是什么？"
    ]
    
    print(f"\n发送{len(messages)}条消息：")
    
    for i, msg in enumerate(messages):
        print(f"\n消息{i+1}: {msg[:30]}...")
        
        # Click at detected position
        await controller.execute_command('click', {'x': x, 'y': y})
        await asyncio.sleep(0.3)
        
        # Clear
        await controller.execute_command('send_keys', {'keys': '^a'})
        await asyncio.sleep(0.1)
        await controller.execute_command('send_keys', {'keys': '{DELETE}'})
        await asyncio.sleep(0.2)
        
        # Type
        await controller.execute_command('send_keys', {'keys': msg})
        await asyncio.sleep(0.5)
        
        # Send
        await controller.execute_command('send_keys', {'keys': '{ENTER}'})
        print(f"✅ 已发送")
        
        # Wait for response
        await asyncio.sleep(5)
    
    print("\n✅ 视觉引导交互完成！")


async def fallback_interaction(controller, hwnd, analysis):
    """Fallback using other visual cues"""
    print("\n使用其他视觉线索...")
    
    # Look for text that might indicate input area
    if hasattr(analysis, 'text_regions'):
        for region in analysis.text_regions:
            text = region.text.lower()
            if any(keyword in text for keyword in ['type', 'message', 'chat', 'input']):
                # Click below this text
                x = (region.bbox[0] + region.bbox[2]) // 2
                y = region.bbox[3] + 20  # 20 pixels below
                
                print(f"在文本 '{region.text}' 下方点击: ({x}, {y})")
                await interact_at_position(controller, hwnd, x, y)
                return
    
    print("未找到合适的视觉线索")


async def heuristic_interaction(controller, hwnd):
    """Heuristic approach when vision fails"""
    print("\n使用启发式方法...")
    
    # Get window rect
    rect = await controller.execute_command('win32_call', {
        'function': 'GetWindowRect',
        'args': [hwnd]
    })
    
    if rect and len(rect) == 4:
        left, top, right, bottom = rect
        width = right - left
        height = bottom - top
        
        # Common input positions for chat apps
        x = left + int(width * 0.75)  # Right side
        y = top + int(height * 0.85)  # Bottom area
        
        print(f"启发式位置: ({x}, {y})")
        await interact_at_position(controller, hwnd, x, y)


if __name__ == "__main__":
    asyncio.run(vision_guided_cursor_interaction())