"""Command forwarding utilities for CyberCorp Node system"""

import asyncio
from typing import Optional, Dict, Any, List, Tuple
from .cybercorp_client import CyberCorpClient


class CommandForwarder:
    """Handles command forwarding to target clients"""
    
    def __init__(self, client: CyberCorpClient):
        """Initialize CommandForwarder
        
        Args:
            client: Connected CyberCorpClient instance
        """
        self.client = client
        
    async def forward_command(self, target_client_id: str, command: str, 
                            params: Optional[Dict[str, Any]] = None, 
                            timeout: float = 5.0) -> Dict[str, Any]:
        """Forward command to target client and get result
        
        Args:
            target_client_id: ID of target client
            command: Command to execute
            params: Optional command parameters
            timeout: Response timeout in seconds
            
        Returns:
            Command result from target client
            
        Raises:
            asyncio.TimeoutError: If response times out
            Exception: If command fails
        """
        # Build forward command request
        forward_request = {
            'type': 'forward_command',
            'target_client': target_client_id,
            'command': {
                'type': 'command',
                'command': command
            }
        }
        
        if params:
            forward_request['command']['params'] = params
            
        # Send forward request
        await self.client.send_raw(forward_request)
        
        # Wait for acknowledgment
        ack = await self.client.receive_raw(timeout=timeout)
        
        if ack.get('type') == 'error':
            raise Exception(f"Forward command failed: {ack.get('error', 'Unknown error')}")
            
        # Wait for actual result
        try:
            response = await self.client.receive_raw(timeout=timeout)
            
            if response.get('type') == 'command_result':
                result = response.get('result', {})
                if isinstance(result, dict) and result.get('success') is False:
                    raise Exception(f"Command failed: {result.get('error', 'Unknown error')}")
                return result
            else:
                raise Exception(f"Unexpected response type: {response.get('type')}")
                
        except asyncio.TimeoutError:
            raise asyncio.TimeoutError(f"Timeout waiting for result of command '{command}'")
            
    async def batch_forward(self, target_client_id: str, 
                           commands: List[Tuple[str, Optional[Dict[str, Any]]]], 
                           stop_on_error: bool = False) -> List[Dict[str, Any]]:
        """Forward multiple commands in sequence
        
        Args:
            target_client_id: ID of target client
            commands: List of (command, params) tuples
            stop_on_error: Whether to stop on first error
            
        Returns:
            List of results for each command
        """
        results = []
        
        for command, params in commands:
            try:
                result = await self.forward_command(target_client_id, command, params)
                results.append({'success': True, 'command': command, 'result': result})
            except Exception as e:
                error_result = {'success': False, 'command': command, 'error': str(e)}
                results.append(error_result)
                
                if stop_on_error:
                    break
                    
        return results
        
    async def forward_with_retry(self, target_client_id: str, command: str,
                               params: Optional[Dict[str, Any]] = None,
                               max_retries: int = 3, 
                               retry_delay: float = 1.0) -> Dict[str, Any]:
        """Forward command with automatic retry on failure
        
        Args:
            target_client_id: ID of target client
            command: Command to execute
            params: Optional command parameters
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            
        Returns:
            Command result from target client
            
        Raises:
            Exception: If all retries fail
        """
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                return await self.forward_command(target_client_id, command, params)
            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    await asyncio.sleep(retry_delay)
                    
        raise Exception(f"Command '{command}' failed after {max_retries} retries: {last_error}")
        
    async def broadcast_command(self, client_ids: List[str], command: str,
                              params: Optional[Dict[str, Any]] = None,
                              timeout: float = 5.0) -> Dict[str, Dict[str, Any]]:
        """Broadcast command to multiple clients
        
        Args:
            client_ids: List of target client IDs
            command: Command to execute
            params: Optional command parameters
            timeout: Response timeout per client
            
        Returns:
            Dictionary mapping client_id to result
        """
        results = {}
        
        # Create tasks for parallel execution
        tasks = []
        for client_id in client_ids:
            task = self.forward_command(client_id, command, params, timeout)
            tasks.append((client_id, task))
            
        # Wait for all tasks to complete
        for client_id, task in tasks:
            try:
                result = await task
                results[client_id] = {'success': True, 'result': result}
            except Exception as e:
                results[client_id] = {'success': False, 'error': str(e)}
                
        return results
        
    async def forward_and_wait(self, target_client_id: str, command: str,
                             params: Optional[Dict[str, Any]] = None,
                             wait_condition: Optional[callable] = None,
                             max_wait: float = 30.0,
                             check_interval: float = 1.0) -> Dict[str, Any]:
        """Forward command and wait for a specific condition
        
        Args:
            target_client_id: ID of target client
            command: Command to execute
            params: Optional command parameters
            wait_condition: Function that takes result and returns True when satisfied
            max_wait: Maximum time to wait for condition
            check_interval: How often to check condition
            
        Returns:
            Final result that satisfies condition
            
        Raises:
            TimeoutError: If condition not met within max_wait
        """
        # Forward initial command
        initial_result = await self.forward_command(target_client_id, command, params)
        
        if wait_condition is None or wait_condition(initial_result):
            return initial_result
            
        # Wait for condition
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < max_wait:
            await asyncio.sleep(check_interval)
            
            # Re-check by forwarding command again
            result = await self.forward_command(target_client_id, command, params)
            
            if wait_condition(result):
                return result
                
        raise TimeoutError(f"Condition not met within {max_wait} seconds")