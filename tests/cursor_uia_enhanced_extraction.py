"""Enhanced Cursor response extraction using UIA (UI Automation)"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
from cybercorp_node.utils.remote_control import RemoteController

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def extract_cursor_response_with_uia():
    """Extract Cursor response using UI Automation for better accuracy"""
    
    print("ENHANCED CURSOR RESPONSE EXTRACTION (UIA)")
    print("Using UI Automation for precise content extraction")
    print("=" * 50)
    
    try:
        # Connect
        remote_controller = RemoteController()
        await remote_controller.connect("uia_extractor")
        
        target_client = await remote_controller.find_client("wjc2022")
        if not target_client:
            print("❌ No target client found")
            return None
        
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
            return None
        
        hwnd = cursor_window['hwnd']
        print(f"✅ Found Cursor window: {hwnd}")
        
        # Method 1: UIA Tree Analysis
        print(f"\n🔍 Method 1: UI Automation Tree Analysis")
        try:
            # Get UIA tree for the window
            uia_result = await remote_controller.execute_command('get_uia_tree', {
                'hwnd': hwnd,
                'max_depth': 10
            })
            
            if uia_result and 'tree' in uia_result:
                print("   ✅ UIA tree retrieved")
                
                # Extract text from UIA elements
                text_content = []
                await extract_text_from_uia_tree(uia_result['tree'], text_content)
                
                if text_content:
                    combined_text = "\n".join(text_content)
                    print(f"   ✅ Extracted {len(text_content)} text elements via UIA")
                    return combined_text
                else:
                    print("   ❌ No text found in UIA tree")
            else:
                print("   ❌ Failed to get UIA tree")
                
        except Exception as e:
            print(f"   UIA tree method failed: {e}")
        
        # Method 2: UIA Pattern-based extraction
        print(f"\n📄 Method 2: UIA Text Pattern Extraction")
        try:
            # Find all text elements using UIA patterns
            text_elements = await remote_controller.execute_command('find_uia_elements', {
                'hwnd': hwnd,
                'control_type': 'Text',
                'include_descendants': True
            })
            
            if text_elements and 'elements' in text_elements:
                print(f"   Found {len(text_elements['elements'])} text elements")
                
                extracted_texts = []
                for elem in text_elements['elements']:
                    try:
                        # Get text value using TextPattern
                        text_result = await remote_controller.execute_command('get_uia_text', {
                            'element_id': elem.get('id'),
                            'use_text_pattern': True
                        })
                        
                        if text_result and text_result.get('text'):
                            text = text_result['text'].strip()
                            if len(text) > 10:  # Filter out short texts
                                extracted_texts.append(text)
                    except:
                        continue
                
                if extracted_texts:
                    print(f"   ✅ Extracted {len(extracted_texts)} meaningful texts")
                    return "\n".join(extracted_texts)
            
        except Exception as e:
            print(f"   UIA pattern method failed: {e}")
        
        # Method 3: Focused element extraction
        print(f"\n🎯 Method 3: Focused Element Extraction")
        try:
            # Get the focused element
            focused_result = await remote_controller.execute_command('get_focused_element', {
                'use_uia': True
            })
            
            if focused_result and focused_result.get('element'):
                elem = focused_result['element']
                print(f"   Found focused element: {elem.get('control_type', 'Unknown')}")
                
                # Try to get its parent container
                parent_result = await remote_controller.execute_command('get_uia_parent', {
                    'element_id': elem.get('id'),
                    'levels_up': 2  # Go up 2 levels to find container
                })
                
                if parent_result and parent_result.get('parent'):
                    # Get all text from parent container
                    container_text = await remote_controller.execute_command('get_uia_container_text', {
                        'element_id': parent_result['parent'].get('id')
                    })
                    
                    if container_text and container_text.get('text'):
                        print(f"   ✅ Extracted text from focused container")
                        return container_text['text']
            
        except Exception as e:
            print(f"   Focused element method failed: {e}")
        
        # Method 4: Accessibility API
        print(f"\n♿ Method 4: Accessibility API Extraction")
        try:
            # Use accessibility API to get readable content
            acc_result = await remote_controller.execute_command('get_accessible_text', {
                'hwnd': hwnd,
                'include_children': True,
                'text_roles': ['statictext', 'text', 'paragraph', 'heading']
            })
            
            if acc_result and acc_result.get('texts'):
                texts = acc_result['texts']
                filtered_texts = [t for t in texts if len(t) > 20]
                
                if filtered_texts:
                    print(f"   ✅ Extracted {len(filtered_texts)} texts via Accessibility API")
                    return "\n".join(filtered_texts)
            
        except Exception as e:
            print(f"   Accessibility API failed: {e}")
        
        # Method 5: Combined approach with smart filtering
        print(f"\n🔧 Method 5: Combined Smart Extraction")
        try:
            # Combine multiple methods and filter intelligently
            all_texts = await remote_controller.execute_command('extract_window_text_smart', {
                'hwnd': hwnd,
                'methods': ['uia', 'accessibility', 'win32'],
                'filter_rules': {
                    'min_length': 20,
                    'exclude_patterns': ['button', 'menu', 'toolbar'],
                    'include_patterns': ['message', 'response', 'text', 'content']
                }
            })
            
            if all_texts and all_texts.get('combined_text'):
                print(f"   ✅ Smart extraction successful")
                return all_texts['combined_text']
            
        except Exception as e:
            print(f"   Combined method failed: {e}")
        
        print(f"\n❌ All UIA extraction methods failed")
        return None
        
    except Exception as e:
        print(f"❌ UIA extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def extract_text_from_uia_tree(node, text_list, level=0):
    """Recursively extract text from UIA tree"""
    if not node:
        return
    
    # Extract text from current node
    if node.get('name'):
        text = node['name'].strip()
        if len(text) > 10 and not text.startswith('System.'):
            text_list.append(text)
    
    if node.get('value'):
        text = str(node['value']).strip()
        if len(text) > 10:
            text_list.append(text)
    
    # Process children
    children = node.get('children', [])
    for child in children:
        await extract_text_from_uia_tree(child, text_list, level + 1)


async def display_extracted_content(content):
    """Display extracted content in organized format"""
    if not content:
        print("\n❌ No content extracted")
        return
    
    print(f"\n📄 EXTRACTED CURSOR RESPONSE")
    print("=" * 50)
    
    lines = content.split('\n')
    
    # Group by potential message blocks
    messages = []
    current_message = []
    
    for line in lines:
        line = line.strip()
        if line:
            if any(keyword in line.lower() for keyword in ['agi', 'ai', '智能', '模型', 'gpt', 'claude']):
                if current_message:
                    messages.append('\n'.join(current_message))
                    current_message = []
                current_message.append(line)
            else:
                current_message.append(line)
    
    if current_message:
        messages.append('\n'.join(current_message))
    
    # Display messages
    for i, msg in enumerate(messages[:10]):  # Show first 10 messages
        print(f"\n💬 Message {i+1}:")
        print("-" * 30)
        preview = msg[:200] + "..." if len(msg) > 200 else msg
        print(preview)
    
    if len(messages) > 10:
        print(f"\n... and {len(messages) - 10} more messages")
    
    # Extract key AGI discussion points
    agi_points = []
    keywords = ['agi', 'artificial general intelligence', '通用人工智能', 'scaling', 'emergence', 
                'consciousness', '意识', 'reasoning', '推理', 'world model', '世界模型']
    
    for line in lines:
        if any(kw in line.lower() for kw in keywords):
            agi_points.append(line.strip())
    
    if agi_points:
        print(f"\n🧠 AGI Discussion Points Found:")
        print("-" * 30)
        for point in agi_points[:5]:
            print(f"• {point}")


async def continuous_extract_and_chat():
    """Extract response and continue chatting"""
    print("Starting continuous extraction and chat cycle...")
    
    # First extract current response
    content = await extract_cursor_response_with_uia()
    await display_extracted_content(content)
    
    if content:
        print(f"\n✅ UIA extraction successful!")
        print(f"📊 Extracted {len(content)} characters")
        print(f"🔄 Ready to continue conversation based on extracted content")
    else:
        print(f"\n⚠️ UIA extraction needs further optimization")
        print(f"💡 Consider using OCR or manual inspection")


if __name__ == "__main__":
    asyncio.run(continuous_extract_and_chat())