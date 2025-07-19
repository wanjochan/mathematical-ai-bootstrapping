"""Quick test script for new features"""

import asyncio
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.cybercorp_client import CyberCorpClient
from utils.client_manager import ClientManager
from utils.command_forwarder import CommandForwarder
from utils.data_persistence import DataPersistence


async def test_new_features():
    """Test the new features added to CyberCorp Node"""
    
    print("CyberCorp Node - New Features Test")
    print("=" * 60)
    
    # Initialize client
    client = CyberCorpClient(client_type="test", port=9998)
    
    try:
        # Connect
        print("\n1. Connecting to server...")
        await client.connect()
        print("✓ Connected successfully")
        
        # Initialize helpers
        client_manager = ClientManager(client)
        forwarder = CommandForwarder(client)
        persistence = DataPersistence()
        
        # Find target client
        print("\n2. Finding target client...")
        target_username = input("Enter target username (e.g., wjchk): ").strip()
        
        target_client = await client_manager.find_client_by_username(target_username)
        if not target_client:
            print(f"✗ Client '{target_username}' not found")
            return
            
        client_id = target_client['id']
        print(f"✓ Found client: {client_id}")
        
        # Test menu
        while True:
            print("\n" + "=" * 60)
            print("Select test to run:")
            print("1. Test mouse drag")
            print("2. Test OCR")
            print("3. Test Win32 API")
            print("4. Test all")
            print("0. Exit")
            
            choice = input("\nEnter choice: ").strip()
            
            if choice == "0":
                break
                
            elif choice == "1":
                # Test mouse drag
                print("\n--- Testing Mouse Drag ---")
                print("This will perform a drag operation in 3 seconds...")
                await asyncio.sleep(3)
                
                result = await forwarder.forward_command(
                    client_id, 
                    'mouse_drag',
                    {
                        'start_x': 200,
                        'start_y': 300,
                        'end_x': 600,
                        'end_y': 300,
                        'duration': 2.0,
                        'humanize': True
                    }
                )
                
                print(f"Result: {'Success' if result else 'Failed'}")
                
            elif choice == "2":
                # Test OCR
                print("\n--- Testing OCR ---")
                
                # Test screen OCR
                print("Capturing screen region for OCR...")
                result = await forwarder.forward_command(
                    client_id,
                    'ocr_screen',
                    {
                        'x': 100,
                        'y': 100,
                        'width': 600,
                        'height': 400
                    }
                )
                
                if result.get('success'):
                    print(f"✓ OCR completed")
                    print(f"Available engines: {result.get('available_engines', [])}")
                    print(f"Found {len(result.get('detections', []))} text regions")
                    
                    # Show first few detections
                    for i, det in enumerate(result.get('detections', [])[:3]):
                        print(f"  [{i+1}] '{det['text']}' (conf: {det.get('confidence', 'N/A')})")
                        
                    # Save results
                    filepath = persistence.save_json(result, "ocr_test")
                    print(f"\nFull results saved to: {filepath}")
                else:
                    print(f"✗ OCR failed: {result.get('error', 'Unknown error')}")
                    
            elif choice == "3":
                # Test Win32 API
                print("\n--- Testing Win32 API ---")
                
                # Find a window
                window_name = input("Enter window name to find (partial match): ").strip()
                
                result = await forwarder.forward_command(
                    client_id,
                    'win32_find_window',
                    {'window_name': window_name}
                )
                
                if result.get('success'):
                    info = result.get('info', {})
                    print(f"✓ Found window:")
                    print(f"  Title: {info.get('title')}")
                    print(f"  HWND: {info.get('hwnd')}")
                    print(f"  Size: {info.get('width')}x{info.get('height')}")
                    print(f"  Process ID: {info.get('process_id')}")
                    
                    # Test OCR on this window
                    if input("\nPerform OCR on this window? (y/n): ").lower() == 'y':
                        ocr_result = await forwarder.forward_command(
                            client_id,
                            'ocr_window',
                            {'hwnd': info.get('hwnd')}
                        )
                        
                        if ocr_result.get('success'):
                            print(f"✓ Window OCR completed")
                            print(f"Found {len(ocr_result.get('detections', []))} text regions")
                        else:
                            print(f"✗ Window OCR failed: {ocr_result.get('error')}")
                else:
                    print(f"✗ Window not found")
                    
            elif choice == "4":
                # Test all
                print("\n--- Running All Tests ---")
                
                # Quick test of each feature
                tests = [
                    ("Mouse drag", 'mouse_drag', {
                        'start_x': 200, 'start_y': 200,
                        'end_x': 400, 'end_y': 200,
                        'duration': 1.0
                    }),
                    ("OCR screen", 'ocr_screen', {
                        'x': 0, 'y': 0,
                        'width': 500, 'height': 300
                    }),
                    ("Win32 keys", 'win32_send_keys', {
                        'keys': '{F5}',
                        'delay': 0.1
                    })
                ]
                
                for test_name, command, params in tests:
                    print(f"\nTesting {test_name}...")
                    try:
                        result = await forwarder.forward_command(
                            client_id, command, params, timeout=10.0
                        )
                        
                        if isinstance(result, dict) and result.get('success'):
                            print(f"✓ {test_name}: Success")
                        elif result:
                            print(f"✓ {test_name}: Completed")
                        else:
                            print(f"✗ {test_name}: Failed")
                    except Exception as e:
                        print(f"✗ {test_name}: Error - {e}")
                        
                print("\n✓ All tests completed")
                
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Disconnect
        print("\nDisconnecting...")
        await client.disconnect()
        

async def main():
    """Main function"""
    print("This script tests the new features added to CyberCorp Node:")
    print("- Mouse drag (for captcha scenarios)")
    print("- OCR (text recognition)")
    print("- Win32 API (advanced window control)")
    print("\nMake sure the server is running and target client is connected.")
    
    await test_new_features()
    

if __name__ == "__main__":
    asyncio.run(main())