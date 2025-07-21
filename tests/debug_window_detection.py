"""Debug window detection issue"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from cybercorp_node.utils.remote_control import RemoteController


async def debug_windows():
    """Debug why windows aren't being detected"""
    
    print("调试窗口检测问题")
    print("=" * 50)
    
    try:
        # Connect
        remote_controller = RemoteController()
        await remote_controller.connect("debug_windows")
        
        target_client = await remote_controller.find_client("wjc2022")
        if not target_client:
            print("❌ 未找到客户端")
            return
        
        print(f"✅ 已连接: {target_client}")
        
        # Method 1: Basic window list
        print("\n方法1: 基础窗口列表")
        try:
            windows = await remote_controller.get_windows()
            print(f"获取到 {len(windows)} 个窗口")
            
            # Show first 5 windows regardless of visibility
            for i, w in enumerate(windows[:10]):
                print(f"\n窗口 {i+1}:")
                print(f"  标题: {w.get('title', '(无)')}")
                print(f"  HWND: {w.get('hwnd', '(无)')}")
                print(f"  可见: {w.get('visible', '(未知)')}")
                print(f"  类名: {w.get('class_name', '(无)')}")
        except Exception as e:
            print(f"方法1错误: {e}")
        
        # Method 2: Direct Win32 enumeration
        print("\n方法2: Win32窗口枚举")
        try:
            result = await remote_controller.execute_command('enum_windows', {
                'include_invisible': False,
                'include_all': True
            })
            if result:
                print(f"Win32找到窗口: {result}")
        except Exception as e:
            print(f"方法2错误: {e}")
        
        # Method 3: Find specific window
        print("\n方法3: 查找特定窗口")
        search_terms = ['Cursor', 'cursor', 'Visual Studio Code', 'Code', 'AI']
        
        for term in search_terms:
            try:
                result = await remote_controller.execute_command('find_window', {
                    'title_contains': term
                })
                if result:
                    print(f"找到包含'{term}'的窗口: {result}")
            except Exception as e:
                print(f"搜索'{term}'失败: {e}")
        
        # Method 4: Get active window
        print("\n方法4: 获取当前活动窗口")
        try:
            result = await remote_controller.execute_command('get_active_window')
            if result:
                print(f"当前活动窗口: {result}")
        except Exception as e:
            print(f"获取活动窗口失败: {e}")
        
        print("\n" + "=" * 50)
        print("调试信息：")
        print("1. 如果看不到窗口，可能是权限问题")
        print("2. Cursor可能使用了特殊的窗口标题")
        print("3. 请手动告诉我Cursor窗口的确切标题")
        
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_windows())