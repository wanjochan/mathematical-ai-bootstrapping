"""List ALL visible windows with detailed info"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from cybercorp_node.utils.remote_control import RemoteController


async def list_all_visible_windows():
    """Show all visible windows to find Cursor"""
    
    print("列出所有可见窗口")
    print("=" * 60)
    
    try:
        # Connect
        remote_controller = RemoteController()
        await remote_controller.connect("list_windows")
        
        target_client = await remote_controller.find_client("wjc2022")
        if not target_client:
            print("❌ 未找到客户端")
            return
        
        print(f"✅ 已连接: {target_client}\n")
        
        # Get all windows
        windows = await remote_controller.get_windows()
        
        # Filter and show visible windows
        visible_windows = [w for w in windows if w.get('visible', False)]
        
        print(f"找到 {len(visible_windows)} 个可见窗口：\n")
        
        for i, window in enumerate(visible_windows):
            title = window.get('title', '(无标题)')
            hwnd = window.get('hwnd', 0)
            
            # Skip empty titles
            if not title or title.strip() == '':
                continue
                
            print(f"{i+1}. 窗口标题: {title}")
            print(f"   HWND: {hwnd}")
            
            # Check window type
            title_lower = title.lower()
            if 'cursor' in title_lower:
                print(f"   ⭐ 可能是 Cursor IDE!")
            elif 'code' in title_lower:
                print(f"   📝 可能是 VS Code")
            elif 'chrome' in title_lower or 'edge' in title_lower:
                print(f"   🌐 浏览器")
            elif any(x in title_lower for x in ['cmd', 'powershell', 'terminal']):
                print(f"   💻 终端")
                
            print()
        
        # Ask user
        print("\n" + "=" * 60)
        print("请告诉我：")
        print("1. 你的Cursor IDE窗口标题是什么？")
        print("2. 是否在上面的列表中看到了Cursor？")
        print("3. 如果没有，Cursor窗口可能的标题是什么？")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(list_all_visible_windows())