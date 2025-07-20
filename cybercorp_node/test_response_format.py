"""
Test unified response format
"""

import asyncio
import json
import websockets
import logging
import argparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('TestResponseFormat')

def validate_response(response):
    """Validate response follows unified format"""
    issues = []
    
    # Check required fields
    if 'success' not in response:
        issues.append("Missing 'success' field")
    elif not isinstance(response['success'], bool):
        issues.append("'success' field must be boolean")
    
    if 'timestamp' not in response:
        issues.append("Missing 'timestamp' field")
    
    if 'error' not in response:
        issues.append("Missing 'error' field")
    
    # Check error structure
    if not response.get('success') and response.get('error'):
        if not isinstance(response['error'], dict):
            issues.append("'error' field must be dict for failed responses")
        elif 'message' not in response['error']:
            issues.append("Error must contain 'message' field")
    
    # Check data field for successful responses
    if response.get('success') and response.get('error') is not None:
        issues.append("Successful response should have 'error' as None")
    
    return issues

async def test_response_format(host='localhost', port=9998):
    """Test unified response format for various commands"""
    url = f'ws://{host}:{port}'
    
    try:
        # Connect as admin
        ws = await websockets.connect(url)
        
        # Register
        await ws.send(json.dumps({
            'type': 'register',
            'user_session': 'admin',
            'client_start_time': '2024',
            'capabilities': {'management': True}
        }))
        
        response = await ws.recv()
        logger.info(f"Registration: {response}")
        
        # Get client list
        await ws.send(json.dumps({'type': 'request', 'command': 'list_clients'}))
        response = await ws.recv()
        data = json.loads(response)
        
        clients = data.get('clients', [])
        
        if not clients:
            logger.warning("No clients found")
            return
        
        # Test commands with different response types
        test_commands = [
            # Window operations
            ('get_windows', {}),
            ('activate_window', {}),
            ('get_window_content', {}),
            
            # System info
            ('get_system_info', {}),
            ('get_processes', {}),
            
            # Screenshot
            ('take_screenshot', {}),
            
            # Health monitoring
            ('health_status', {}),
            
            # Logging
            ('get_log_stats', {}),
            ('get_logs', {'count': 10, 'level': 'INFO'}),
            ('set_log_level', {'level': 'DEBUG'}),
            
            # Hot reload
            ('hot_reload', {'action': 'status'}),
            
            # Error cases
            ('unknown_command', {}),  # Should return error
            ('send_keys', {}),  # Missing 'keys' parameter
        ]
        
        # Test each client
        for client in clients[:1]:  # Test first client only
            client_id = client['id']
            logger.info(f"\nTesting response format on client: {client_id}")
            
            results = []
            
            for command, params in test_commands:
                logger.info(f"\nTesting command: {command}")
                
                await ws.send(json.dumps({
                    'type': 'forward_command',
                    'target_client': client_id,
                    'command': {
                        'type': 'command',
                        'command': command,
                        'params': params
                    }
                }))
                
                await ws.recv()  # ack
                
                try:
                    result = await asyncio.wait_for(ws.recv(), timeout=10.0)
                    data = json.loads(result)
                    
                    if data.get('type') == 'command_result':
                        response = data.get('result', {})
                        
                        # Validate response format
                        issues = validate_response(response)
                        
                        if issues:
                            logger.error(f"✗ {command}: Format issues: {issues}")
                            results.append((command, False, issues))
                        else:
                            success = response.get('success', False)
                            if success:
                                logger.info(f"✓ {command}: Valid format (success)")
                                if 'message' in response:
                                    logger.info(f"  Message: {response['message']}")
                            else:
                                logger.info(f"✓ {command}: Valid format (error)")
                                if response.get('error'):
                                    logger.info(f"  Error: {response['error'].get('message')}")
                                    if 'code' in response['error']:
                                        logger.info(f"  Code: {response['error']['code']}")
                            
                            results.append((command, True, None))
                            
                            # Log sample data
                            if response.get('data'):
                                data_str = json.dumps(response['data'])
                                if len(data_str) > 100:
                                    data_str = data_str[:100] + '...'
                                logger.info(f"  Data: {data_str}")
                        
                except asyncio.TimeoutError:
                    logger.error(f"✗ {command}: Timeout")
                    results.append((command, False, ['Timeout']))
                
                # Small delay between commands
                await asyncio.sleep(0.5)
            
            # Summary
            logger.info("\n" + "="*50)
            logger.info("SUMMARY")
            logger.info("="*50)
            
            passed = sum(1 for _, success, _ in results if success)
            total = len(results)
            
            logger.info(f"Total commands tested: {total}")
            logger.info(f"Passed: {passed}")
            logger.info(f"Failed: {total - passed}")
            logger.info(f"Success rate: {passed/total*100:.1f}%")
            
            if passed < total:
                logger.info("\nFailed commands:")
                for cmd, success, issues in results:
                    if not success:
                        logger.info(f"  - {cmd}: {issues}")
        
        await ws.close()
        
    except Exception as e:
        logger.error(f"Test error: {e}")

def main():
    parser = argparse.ArgumentParser(description='Test unified response format')
    parser.add_argument('--host', default='localhost', help='Server host')
    parser.add_argument('--port', type=int, default=9998, help='Server port')
    
    args = parser.parse_args()
    
    logger.info("Testing unified response format...")
    logger.info("This will verify all commands return consistent response structure.\n")
    
    asyncio.run(test_response_format(args.host, args.port))

if __name__ == '__main__':
    main()