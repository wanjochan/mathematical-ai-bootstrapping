"""Extract the latest response from Cursor IDE dialog"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
from cybercorp_node.utils.remote_control import RemoteController

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def extract_cursor_response():
    """Extract the latest response from Cursor IDE"""
    
    print("EXTRACTING CURSOR IDE RESPONSE")
    print("=" * 35)
    
    try:
        # Connect
        remote_controller = RemoteController()
        await remote_controller.connect("response_extractor")
        
        target_client = await remote_controller.find_client("wjc2022")
        if not target_client:
            print("❌ No target client found")
            return False
        
        print(f"✅ Connected to client: {target_client}")
        
        # Get Cursor window
        windows = await remote_controller.get_windows()
        cursor_window = None
        for window in windows:
            if 'cursor' in window.get('title', '').lower():
                cursor_window = window
                break
        
        if not cursor_window:
            print("❌ Cursor window not found")
            return False
        
        hwnd = cursor_window['hwnd']
        print(f"✅ Found Cursor window: {hwnd}")
        
        # Method 1: Try to select and copy the response area
        print(f"\n📋 Method 1: Extracting via clipboard selection")
        
        try:
            # Focus the window first
            await remote_controller.execute_command('win32_call', {
                'function': 'SetForegroundWindow',
                'args': [hwnd]
            })
            await asyncio.sleep(0.5)
            
            # Click in the response area (right side, middle area)
            window_info = await remote_controller.execute_command('get_window_info', {'hwnd': hwnd})
            if window_info and 'rect' in window_info:
                rect = window_info['rect']
                window_width = rect[2] - rect[0]
                window_height = rect[3] - rect[1]
            else:
                window_width = 1200
                window_height = 800
            
            # Click in the response area (right side, upper-middle area)
            response_x = int(window_width * 0.75)
            response_y = int(window_height * 0.4)
            
            print(f"   Clicking response area at ({response_x}, {response_y})")
            await remote_controller.execute_command('click', {
                'x': response_x,
                'y': response_y
            })
            await asyncio.sleep(0.5)
            
            # Select all content in the response area
            print("   Selecting all content...")
            await remote_controller.execute_command('send_keys', {'keys': '^a'})
            await asyncio.sleep(0.5)
            
            # Copy to clipboard
            print("   Copying to clipboard...")
            await remote_controller.execute_command('send_keys', {'keys': '^c'})
            await asyncio.sleep(0.8)
            
            # Get clipboard content
            clipboard_result = await remote_controller.execute_command('get_clipboard')
            if clipboard_result:
                print(f"   ✅ Extracted content via clipboard ({len(clipboard_result)} characters)")
                return clipboard_result
            else:
                print("   ❌ No content in clipboard")
        
        except Exception as e:
            print(f"   Clipboard method failed: {e}")
        
        # Method 2: Try OCR/screenshot approach
        print(f"\n🖼️ Method 2: Attempting screenshot analysis")
        
        try:
            # Take screenshot of the window
            result = await remote_controller.execute_command('capture_window', {'hwnd': hwnd})
            if result and result.get('success'):
                print("   ✅ Screenshot captured")
                
                # Try to analyze with vision system
                from cybercorp_node.utils.vision_integration import VisionWindowAnalyzer
                vision_analyzer = VisionWindowAnalyzer(remote_controller)
                
                analysis_result = await vision_analyzer.analyze_window(hwnd)
                if analysis_result and hasattr(analysis_result, 'text_content'):
                    print(f"   ✅ Text extracted via OCR ({len(analysis_result.text_content)} characters)")
                    return analysis_result.text_content
                else:
                    print("   ❌ OCR analysis failed")
            else:
                print("   ❌ Screenshot capture failed")
                
        except Exception as e:
            print(f"   Screenshot method failed: {e}")
        
        # Method 3: Try to find and read text controls
        print(f"\n🔍 Method 3: Reading text from UI controls")
        
        try:
            result = await remote_controller.execute_command('enum_child_windows', {'hwnd': hwnd})
            if result and 'children' in result:
                text_content = []
                
                for child in result['children']:
                    class_name = child.get('class_name', '').lower()
                    child_hwnd = child.get('hwnd')
                    
                    # Try to get text from various control types
                    if any(keyword in class_name for keyword in ['edit', 'static', 'text', 'rich']):
                        try:
                            text_result = await remote_controller.execute_command('win32_call', {
                                'function': 'GetWindowText',
                                'args': [child_hwnd]
                            })
                            
                            if text_result and len(str(text_result)) > 10:
                                text_content.append(f"Control {class_name}: {text_result}")
                                
                        except:
                            continue
                
                if text_content:
                    combined_text = "\n".join(text_content)
                    print(f"   ✅ Extracted text from {len(text_content)} controls")
                    return combined_text
                else:
                    print("   ❌ No readable text controls found")
            
        except Exception as e:
            print(f"   Control reading failed: {e}")
        
        print(f"\n❌ All extraction methods failed")
        return None
        
    except Exception as e:
        print(f"❌ Response extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def display_response(response_text):
    """Display the extracted response in a readable format"""
    
    if not response_text:
        print("\n❌ No response content extracted")
        return
    
    print(f"\n📄 CURSOR IDE RESPONSE CONTENT")
    print("=" * 50)
    
    # Clean up the text
    lines = response_text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if line and len(line) > 3:  # Filter out very short lines
            cleaned_lines.append(line)
    
    # Display the content
    if cleaned_lines:
        print(f"Content ({len(cleaned_lines)} lines):")
        print("-" * 30)
        
        for i, line in enumerate(cleaned_lines[:50]):  # Show first 50 lines
            print(f"{i+1:2d}. {line}")
        
        if len(cleaned_lines) > 50:
            print(f"... ({len(cleaned_lines) - 50} more lines)")
        
        # Look for script content
        script_indicators = ['#!/', 'import ', 'def ', 'if __name__', 'function', 'echo ', 'rm ', 'find ']
        script_lines = [line for line in cleaned_lines if any(indicator in line for indicator in script_indicators)]
        
        if script_lines:
            print(f"\n🔧 DETECTED SCRIPT CONTENT:")
            print("-" * 25)
            for line in script_lines[:20]:
                print(f"   {line}")
        
        # Look for backup-related content
        backup_keywords = ['backup', 'clean', 'delete', 'remove', 'temp', 'directory', 'file']
        backup_lines = [line for line in cleaned_lines if any(keyword in line.lower() for keyword in backup_keywords)]
        
        if backup_lines:
            print(f"\n🗂️ BACKUP-RELATED CONTENT:")
            print("-" * 25)
            for line in backup_lines[:15]:
                print(f"   {line}")
    
    else:
        print("Raw content:")
        print(response_text[:1000] + "..." if len(response_text) > 1000 else response_text)


if __name__ == "__main__":
    async def main():
        print("Extracting Cursor IDE response to see what it generated...")
        print("This will help verify our cleanup request was processed correctly.")
        print("")
        
        await asyncio.sleep(1)
        
        response = await extract_cursor_response()
        await display_response(response)
        
        if response:
            print(f"\n✅ Response extraction successful!")
            print(f"This shows that our adaptive interaction system")
            print(f"successfully communicated with Cursor IDE!")
        else:
            print(f"\n⚠️ Could not extract response automatically")
            print(f"Please manually check Cursor IDE for the backup cleanup response")
    
    asyncio.run(main())