"""List all windows to see what's available"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
from cybercorp_node.utils.remote_control import RemoteController

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def list_all_windows():
    """List all available windows"""
    
    print("🪟 Window List Test")
    print("=" * 30)
    
    try:
        # Connect to remote control
        remote_controller = RemoteController()
        await remote_controller.connect("window_lister")
        
        # Find target client
        target_client = await remote_controller.find_client("wjc2022")
        if not target_client:
            print("❌ No target client found")
            return
        
        print(f"✅ Connected to client: {target_client}")
        
        # Get all windows
        print("\n📋 All Windows:")
        windows = await remote_controller.get_windows()
        
        print(f"Found {len(windows)} windows:")
        
        cursor_candidates = []
        for i, window in enumerate(windows):
            title = window.get('title', '')
            hwnd = window.get('hwnd', 0)
            visible = window.get('visible', False)
            
            print(f"{i+1:2d}. {title:50} (HWND: {hwnd}) {'[VISIBLE]' if visible else '[HIDDEN]'}")
            
            # Look for Cursor-related windows
            if 'cursor' in title.lower():
                cursor_candidates.append(window)
        
        print(f"\n🎯 Cursor IDE Candidates:")
        if cursor_candidates:
            for window in cursor_candidates:
                print(f"   - {window['title']} (HWND: {window['hwnd']})")
        else:
            print("   No Cursor IDE windows found")
            print("   Please ensure Cursor IDE is running and not minimized")
        
        # Show some example windows that might be IDE-related
        print(f"\n🔍 Possible IDE Windows:")
        ide_keywords = ['code', 'visual', 'editor', 'ide', 'dev']
        for window in windows:
            title_lower = window.get('title', '').lower()
            if any(keyword in title_lower for keyword in ide_keywords):
                print(f"   - {window['title']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(list_all_windows())