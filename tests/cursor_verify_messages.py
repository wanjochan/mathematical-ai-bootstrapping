"""Verify if messages are actually being sent to Cursor IDE"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
from cybercorp_node.utils.remote_control import RemoteController

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def verify_cursor_interaction():
    """Verify and debug message sending to Cursor"""
    
    print("CURSOR消息发送验证")
    print("=" * 40)
    
    try:
        # Connect
        remote_controller = RemoteController()
        await remote_controller.connect("verify_test")
        
        target_client = await remote_controller.find_client("wjc2022")
        if not target_client:
            print("❌ 未找到目标客户端")
            return False
        
        print(f"✅ 已连接到客户端: {target_client}")
        
        # Find Cursor window
        windows = await remote_controller.get_windows()
        cursor_window = None
        for window in windows:
            if 'cursor' in window.get('title', '').lower():
                cursor_window = window
                break
        
        if not cursor_window:
            print("❌ 未找到Cursor窗口")
            return False
        
        hwnd = cursor_window['hwnd']
        print(f"✅ 找到Cursor窗口: {hwnd}")
        
        # Step 1: Take screenshot before
        print("\n📸 步骤1: 截图对话框当前状态")
        try:
            screenshot1 = await remote_controller.execute_command('capture_window', {'hwnd': hwnd})
            print("   ✅ 截图成功（操作前）")
        except Exception as e:
            print(f"   ❌ 截图失败: {e}")
        
        # Step 2: Try different methods to send a test message
        print("\n🔍 步骤2: 尝试不同方法发送测试消息")
        
        test_message = "测试消息：验证是否能成功发送到Cursor"
        
        # Method 1: Direct click and type
        print("\n方法1: 直接点击和输入")
        try:
            # Get window info
            window_info = await remote_controller.execute_command('get_window_info', {'hwnd': hwnd})
            if window_info and 'rect' in window_info:
                rect = window_info['rect']
                window_width = rect[2] - rect[0]
                window_height = rect[3] - rect[1]
                print(f"   窗口尺寸: {window_width}x{window_height}")
            else:
                window_width = 1200
                window_height = 800
            
            # Try multiple click positions
            positions = [
                ("右下角输入区", int(window_width * 0.75), int(window_height * 0.85)),
                ("右中部区域", int(window_width * 0.75), int(window_height * 0.6)),
                ("中下部区域", int(window_width * 0.5), int(window_height * 0.8)),
                ("右上角区域", int(window_width * 0.75), int(window_height * 0.25)),
            ]
            
            for desc, x, y in positions:
                print(f"\n   尝试位置: {desc} ({x}, {y})")
                
                # Click
                await remote_controller.execute_command('click', {'x': x, 'y': y})
                await asyncio.sleep(0.5)
                
                # Check if we can type
                await remote_controller.execute_command('send_keys', {'keys': '^a'})
                await asyncio.sleep(0.1)
                await remote_controller.execute_command('send_keys', {'keys': test_message})
                await asyncio.sleep(0.5)
                
                # Take screenshot to verify
                try:
                    screenshot2 = await remote_controller.execute_command('capture_window', {'hwnd': hwnd})
                    print("      ✅ 已输入文字，截图保存")
                except:
                    pass
                
                # Don't send yet, just verify text appears
                print("      ⏸️ 暂不发送，仅验证文字是否出现")
                
                # Clear for next test
                await remote_controller.execute_command('send_keys', {'keys': '^a'})
                await asyncio.sleep(0.1)
                await remote_controller.execute_command('send_keys', {'keys': '{DELETE}'})
                await asyncio.sleep(0.3)
                
        except Exception as e:
            print(f"   方法1失败: {e}")
        
        # Method 2: Check child windows
        print("\n方法2: 检查子窗口")
        try:
            result = await remote_controller.execute_command('enum_child_windows', {'hwnd': hwnd})
            if result and 'children' in result:
                print(f"   找到 {len(result['children'])} 个子窗口")
                
                # Look for edit controls
                edit_controls = []
                for child in result['children']:
                    class_name = child.get('class_name', '').lower()
                    if 'edit' in class_name or 'input' in class_name or 'text' in class_name:
                        edit_controls.append(child)
                        print(f"   - {class_name} (HWND: {child['hwnd']})")
                
                if edit_controls:
                    print(f"   找到 {len(edit_controls)} 个可能的输入控件")
            else:
                print("   未找到子窗口")
                
        except Exception as e:
            print(f"   方法2失败: {e}")
        
        # Step 3: Manual verification
        print("\n👁️ 步骤3: 手动验证")
        print("请手动检查Cursor IDE:")
        print("1. 是否看到了测试文字出现？")
        print("2. 输入框在哪个位置？")
        print("3. 对话框是否处于活跃状态？")
        
        print("\n❓ 可能的问题:")
        print("- Cursor使用了特殊的UI框架")
        print("- 输入框位置动态变化")
        print("- 需要特定的激活步骤")
        print("- 窗口焦点问题")
        
        return True
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    print("开始验证Cursor消息发送问题")
    print("这将帮助诊断为什么消息没有出现在对话框中")
    print("")
    
    await asyncio.sleep(1)
    
    success = await verify_cursor_interaction()
    
    if success:
        print("\n" + "=" * 50)
        print("验证完成")
        print("请告诉我你在Cursor中看到了什么")
        print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())