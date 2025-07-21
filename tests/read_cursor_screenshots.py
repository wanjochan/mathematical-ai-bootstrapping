"""Read and analyze the screenshots taken"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from cybercorp_node.utils.remote_control import RemoteController


async def read_screenshots():
    """Read the screenshots to see what actually happened"""
    
    print("读取截图分析实际情况")
    print("=" * 50)
    
    try:
        # Connect
        remote_controller = RemoteController()
        await remote_controller.connect("read_screenshots")
        
        target_client = await remote_controller.find_client("wjc2022")
        if not target_client:
            return
            
        print(f"✅ 已连接: {target_client}")
        
        # List screenshot files
        print("\n查找截图文件：")
        try:
            # Get current directory files
            result = await remote_controller.execute_command('list_files', {
                'path': '.',
                'pattern': 'cursor*.png'
            })
            
            if result and 'files' in result:
                print(f"找到 {len(result['files'])} 个截图文件")
                for f in result['files']:
                    print(f"  - {f}")
            else:
                # Try alternative method
                ls_result = await remote_controller.execute_command('run_command', {
                    'command': 'dir cursor*.png'
                })
                if ls_result:
                    print(f"截图文件: {ls_result}")
                    
        except Exception as e:
            print(f"列举文件错误: {e}")
        
        # Read a specific screenshot if exists
        print("\n尝试读取截图内容：")
        screenshot_paths = [
            'cursor_test_右下.png',
            'cursor_test_右中.png', 
            'cursor_test_中下.png',
            'cursor_test_右上.png',
            'cursor_state_7670670.png'
        ]
        
        for path in screenshot_paths:
            try:
                # Check if file exists
                exists = await remote_controller.execute_command('file_exists', {'path': path})
                if exists:
                    print(f"\n读取 {path}:")
                    
                    # Get file info
                    info = await remote_controller.execute_command('file_info', {'path': path})
                    if info:
                        print(f"  大小: {info.get('size', '未知')} bytes")
                        print(f"  修改时间: {info.get('modified', '未知')}")
                    
                    # Try to analyze with vision
                    analysis = await remote_controller.execute_command('analyze_image', {
                        'path': path,
                        'prompt': '这是什么应用程序的截图？能看到输入框或对话内容吗？'
                    })
                    
                    if analysis:
                        print(f"  分析结果: {analysis}")
                        
            except Exception as e:
                print(f"  读取{path}失败: {e}")
        
        # Alternative: Get desktop screenshot
        print("\n获取当前桌面截图：")
        try:
            desktop = await remote_controller.execute_command('screenshot', {
                'full_screen': True,
                'save_to': 'desktop_current.png'
            })
            if desktop:
                print("✅ 桌面截图已保存")
                
                # Find Cursor window in desktop
                windows = await remote_controller.execute_command('get_visible_windows')
                if windows:
                    print("\n当前可见窗口：")
                    for w in windows[:5]:
                        print(f"  - {w.get('title', '未知')} ({w.get('process', '')})")
                        
        except Exception as e:
            print(f"桌面截图失败: {e}")
        
        print("\n" + "=" * 50)
        print("分析建议：")
        print("1. 截图文件可能保存在受控端而非控制端")
        print("2. 可能需要使用文件传输功能获取截图")
        print("3. 或者直接在受控端查看生成的PNG文件")
        
    except Exception as e:
        print(f"❌ 错误: {e}")


if __name__ == "__main__":
    asyncio.run(read_screenshots())