"""Example script demonstrating vision integration capabilities"""

import asyncio
import logging
from utils.remote_control import RemoteController

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demo_vision_capabilities():
    """Demonstrate various vision-based automation capabilities"""
    
    print("CyberCorp Vision Integration Demo")
    print("=" * 40)
    
    # Connect to server
    controller = RemoteController()
    await controller.connect('vision_demo')
    
    try:
        # Find a client
        client_id = await controller.find_client('main')
        if not client_id:
            print("No 'main' client found. Please start a client first.")
            return
            
        print(f"Connected to client: {client_id}")
        
        # Get all windows
        windows = await controller.get_windows()
        print(f"Found {len(windows)} windows")
        
        if not windows:
            print("No windows available for testing")
            return
            
        # Select a test window (first available)
        test_window = windows[0]
        hwnd = test_window['hwnd']
        title = test_window.get('title', 'Unknown')
        
        print(f"\nTesting with window: {title} (HWND: {hwnd})")
        print("-" * 50)
        
        # Demo 1: Basic window analysis
        print("1. Analyzing window with vision...")
        analysis = await controller.analyze_window_vision(hwnd, save_visualization=True)
        
        if analysis:
            print(f"   - Found {len(analysis['elements'])} UI elements")
            print(f"   - Layout type: {analysis['content_summary']['layout_type']}")
            print(f"   - Has buttons: {analysis['content_summary']['has_buttons']}")
            print(f"   - Has inputs: {analysis['content_summary']['has_text_input']}")
            print(f"   - Interaction points: {len(analysis['interaction_points'])}")
        else:
            print("   - Analysis failed")
            
        # Demo 2: Find clickable elements
        print("\n2. Finding clickable elements...")
        clickable = await controller.find_clickable_elements_vision(hwnd)
        
        if clickable:
            print(f"   Found {len(clickable)} clickable elements:")
            for i, elem in enumerate(clickable[:5]):  # Show first 5
                print(f"     {i+1}. {elem['type']} at ({elem['center'][0]}, {elem['center'][1]})")
                
            # Demo 3: Smart click (demonstrate capability but don't actually click)
            print(f"\n3. Smart click demonstration (finding buttons)...")
            buttons = [e for e in clickable if e['type'] == 'button']
            if buttons:
                button = buttons[0]
                print(f"   Would click button at: ({button['center'][0]}, {button['center'][1]})")
                # Uncomment next line to actually click:
                # success = await controller.smart_click(hwnd, 'button')
                # print(f"   Click success: {success}")
            else:
                print("   No buttons found for smart click demo")
        else:
            print("   No clickable elements found")
            
        # Demo 4: Get window summary
        print("\n4. Getting window content summary...")
        summary = await controller.get_window_summary_vision(hwnd)
        if summary:
            print("   Window Summary:")
            for line in summary.split('\n')[:10]:  # Show first 10 lines
                if line.strip():
                    print(f"   {line}")
        else:
            print("   Failed to get summary")
            
        # Demo 5: Test with multiple windows (if available)
        if len(windows) > 1:
            print(f"\n5. Quick analysis of all {len(windows)} windows...")
            for i, window in enumerate(windows[:3]):  # Test first 3
                w_hwnd = window['hwnd']
                w_title = window.get('title', f'Window {i+1}')
                
                print(f"   Analyzing: {w_title[:50]}...")
                analysis = await controller.analyze_window_vision(w_hwnd)
                if analysis:
                    elem_count = len(analysis['elements'])
                    layout_type = analysis['content_summary']['layout_type']
                    print(f"     -> {elem_count} elements, {layout_type} layout")
                else:
                    print("     -> Analysis failed")
                    
        print("\n" + "=" * 40)
        print("Vision integration demo completed!")
        print("\nKey capabilities demonstrated:")
        print("- Window content analysis and element detection")
        print("- Structured data extraction from UI")
        print("- Smart element finding and interaction")
        print("- Visual debugging with saved screenshots")
        print("- Multi-window batch processing")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await controller.close()


async def interactive_vision_demo():
    """Interactive demo allowing user to select specific features"""
    
    print("Interactive Vision Demo")
    print("=" * 30)
    
    controller = RemoteController()
    await controller.connect('interactive_vision')
    
    try:
        # Find client
        client_id = await controller.find_client('main')
        if not client_id:
            print("No 'main' client found.")
            return
            
        # Get windows
        windows = await controller.get_windows()
        if not windows:
            print("No windows available.")
            return
            
        # Let user select window
        print(f"\nAvailable windows:")
        for i, window in enumerate(windows):
            title = window.get('title', f'Window {i+1}')[:60]
            print(f"  {i+1}. {title}")
            
        try:
            choice = int(input(f"\nSelect window (1-{len(windows)}): ")) - 1
            if choice < 0 or choice >= len(windows):
                print("Invalid choice")
                return
        except ValueError:
            print("Invalid input")
            return
            
        selected_window = windows[choice]
        hwnd = selected_window['hwnd']
        title = selected_window.get('title', 'Unknown')
        
        print(f"\nSelected: {title}")
        
        while True:
            print("\nAvailable actions:")
            print("1. Analyze window")
            print("2. Find clickable elements")
            print("3. Get window summary")
            print("4. Smart click button")
            print("5. Find input fields")
            print("6. Exit")
            
            try:
                action = input("Choose action (1-6): ").strip()
                
                if action == '1':
                    print("Analyzing window...")
                    analysis = await controller.analyze_window_vision(hwnd, save_visualization=True)
                    if analysis:
                        print(f"Analysis complete! Found {len(analysis['elements'])} elements")
                        print(f"Layout: {analysis['content_summary']['layout_type']}")
                    else:
                        print("Analysis failed")
                        
                elif action == '2':
                    print("Finding clickable elements...")
                    clickable = await controller.find_clickable_elements_vision(hwnd)
                    print(f"Found {len(clickable)} clickable elements:")
                    for i, elem in enumerate(clickable):
                        print(f"  {i+1}. {elem['type']} at ({elem['center'][0]}, {elem['center'][1]})")
                        
                elif action == '3':
                    print("Getting window summary...")
                    summary = await controller.get_window_summary_vision(hwnd)
                    if summary:
                        print(summary)
                    else:
                        print("Failed to get summary")
                        
                elif action == '4':
                    print("Looking for buttons to click...")
                    clickable = await controller.find_clickable_elements_vision(hwnd)
                    buttons = [e for e in clickable if e['type'] == 'button']
                    
                    if buttons:
                        print(f"Found {len(buttons)} buttons:")
                        for i, btn in enumerate(buttons):
                            print(f"  {i+1}. Button at ({btn['center'][0]}, {btn['center'][1]})")
                            
                        try:
                            btn_choice = int(input(f"Which button to click (1-{len(buttons)}, 0 to cancel)? "))
                            if btn_choice > 0 and btn_choice <= len(buttons):
                                confirm = input("Really click? This will interact with the window! (y/N): ")
                                if confirm.lower() == 'y':
                                    success = await controller.smart_click(hwnd, 'button')
                                    print(f"Click result: {success}")
                                else:
                                    print("Cancelled")
                        except ValueError:
                            print("Invalid choice")
                    else:
                        print("No buttons found")
                        
                elif action == '5':
                    print("Finding input fields...")
                    analyzer = controller._get_vision_analyzer()
                    if analyzer:
                        text_regions = await analyzer.find_text_regions(hwnd)
                        inputs = [r for r in text_regions if r['type'] == 'input']
                        print(f"Found {len(inputs)} input fields:")
                        for i, inp in enumerate(inputs):
                            print(f"  {i+1}. Input at ({inp['center'][0]}, {inp['center'][1]})")
                    else:
                        print("Vision analyzer not available")
                        
                elif action == '6':
                    break
                    
                else:
                    print("Invalid choice")
                    
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"Error: {e}")
                
    finally:
        await controller.close()


async def main():
    """Main function"""
    print("CyberCorp Vision Integration Examples")
    print("====================================")
    print()
    print("This script demonstrates the vision-based window content analysis")
    print("and automation capabilities of CyberCorp.")
    print()
    
    choice = input("Choose demo type:\n1. Automated demo\n2. Interactive demo\nChoice (1/2): ").strip()
    
    if choice == '1':
        await demo_vision_capabilities()
    elif choice == '2':
        await interactive_vision_demo()
    else:
        print("Invalid choice")


if __name__ == "__main__":
    asyncio.run(main())