"""Check all windows to find the correct Cursor IDE"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from cybercorp_node.utils.remote_control import RemoteController


async def check_all_windows():
    """List all windows to identify the correct Cursor IDE"""
    
    print("检查所有窗口列表")
    print("=" * 50)
    
    try:
        # Connect
        remote_controller = RemoteController()
        await remote_controller.connect("window_check")
        
        target_client = await remote_controller.find_client("wjc2022")
        if not target_client:
            print("❌ 未找到客户端")
            return
        
        print(f"✅ 已连接: {target_client}")
        
        # Get all windows
        windows = await remote_controller.get_windows()
        
        print(f"\n找到 {len(windows)} 个窗口：")
        print("-" * 50)
        
        # Separate by type
        cursor_windows = []
        vscode_windows = []
        other_editors = []
        
        for i, window in enumerate(windows):
            title = window.get('title', '')
            hwnd = window.get('hwnd', '')
            visible = window.get('visible', False)
            
            # Detailed check
            title_lower = title.lower()
            
            if visible:  # Only show visible windows
                print(f"\n窗口 {i+1}:")
                print(f"  标题: {title}")
                print(f"  HWND: {hwnd}")
                print(f"  可见: {visible}")
                
                # Categorize
                if 'cursor' in title_lower and 'visual studio code' not in title_lower:
                    cursor_windows.append(window)
                    print(f"  类型: 🎯 CURSOR IDE")
                elif 'visual studio code' in title_lower or 'vscode' in title_lower:
                    vscode_windows.append(window)
                    print(f"  类型: 📝 VS Code")
                elif any(editor in title_lower for editor in ['sublime', 'notepad', 'editor', 'ide']):
                    other_editors.append(window)
                    print(f"  类型: 📄 其他编辑器")
        
        # Summary
        print("\n" + "=" * 50)
        print("窗口分类汇总：")
        print(f"🎯 Cursor IDE 窗口: {len(cursor_windows)} 个")
        for win in cursor_windows:
            print(f"   - {win['title']} (HWND: {win['hwnd']})")
        
        print(f"\n📝 VS Code 窗口: {len(vscode_windows)} 个")
        for win in vscode_windows:
            print(f"   - {win['title']} (HWND: {win['hwnd']})")
        
        print(f"\n📄 其他编辑器: {len(other_editors)} 个")
        for win in other_editors:
            print(f"   - {win['title']} (HWND: {win['hwnd']})")
        
        # Find the real Cursor
        print("\n" + "=" * 50)
        if cursor_windows:
            print("✅ 找到真正的Cursor IDE窗口！")
            print(f"应该使用 HWND: {cursor_windows[0]['hwnd']}")
        else:
            print("❌ 没有找到Cursor IDE窗口")
            print("可能的原因：")
            print("1. Cursor窗口标题不包含'Cursor'")
            print("2. Cursor未运行")
            print("3. Cursor被最小化")
            
            # Check for windows with AI-related titles
            print("\n查找可能的AI编辑器窗口...")
            for window in windows:
                if window.get('visible'):
                    title_lower = window['title'].lower()
                    if any(keyword in title_lower for keyword in ['ai', 'chat', 'assistant', 'copilot']):
                        print(f"   可能相关: {window['title']} (HWND: {window['hwnd']})")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(check_all_windows())