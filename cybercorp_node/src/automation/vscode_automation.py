"""VSCode automation utilities using command forwarding"""

from typing import Optional, Dict, Any, List
from .command_forwarder import CommandForwarder
from .vscode_ui_analyzer import VSCodeUIAnalyzer


class VSCodeAutomation:
    """Automates VSCode interactions through forwarded commands"""
    
    def __init__(self, command_forwarder: CommandForwarder):
        """Initialize VSCodeAutomation
        
        Args:
            command_forwarder: CommandForwarder instance for sending commands
        """
        self.forwarder = command_forwarder
        self.ui_analyzer = VSCodeUIAnalyzer()
        
    async def activate_window(self, client_id: str, timeout: float = 5.0) -> bool:
        """Activate VSCode window
        
        Args:
            client_id: Target client ID
            timeout: Command timeout
            
        Returns:
            True if successful
        """
        try:
            result = await self.forwarder.forward_command(
                client_id, 'activate_window', timeout=timeout
            )
            return result.get('success', False)
        except Exception:
            return False
            
    async def type_text(self, client_id: str, text: str, 
                       delay: float = 0.01) -> Dict[str, Any]:
        """Type text in VSCode
        
        Args:
            client_id: Target client ID
            text: Text to type
            delay: Delay between keystrokes
            
        Returns:
            Command result
        """
        params = {'text': text, 'delay': delay}
        return await self.forwarder.forward_command(
            client_id, 'vscode_type_text', params
        )
        
    async def send_keys(self, client_id: str, keys: str) -> Dict[str, Any]:
        """Send keyboard shortcuts/keys
        
        Args:
            client_id: Target client ID
            keys: Keys to send (e.g., 'ctrl+s', 'enter')
            
        Returns:
            Command result
        """
        params = {'keys': keys}
        return await self.forwarder.forward_command(
            client_id, 'send_keys', params
        )
        
    async def get_content(self, client_id: str) -> Dict[str, Any]:
        """Get VSCode window content/structure
        
        Args:
            client_id: Target client ID
            
        Returns:
            VSCode content structure
        """
        return await self.forwarder.forward_command(
            client_id, 'vscode_get_content'
        )
        
    async def background_input(self, client_id: str, element_name: str, 
                             text: str) -> Dict[str, Any]:
        """Input text in background without activating window
        
        Args:
            client_id: Target client ID
            element_name: Name/identifier of input element
            text: Text to input
            
        Returns:
            Command result
        """
        params = {
            'element_name': element_name,
            'text': text
        }
        return await self.forwarder.forward_command(
            client_id, 'background_input', params
        )
        
    async def background_click(self, client_id: str, 
                             element_name: str) -> Dict[str, Any]:
        """Click element in background without activating window
        
        Args:
            client_id: Target client ID
            element_name: Name/identifier of element to click
            
        Returns:
            Command result
        """
        params = {'element_name': element_name}
        return await self.forwarder.forward_command(
            client_id, 'background_click', params
        )
        
    async def take_screenshot(self, client_id: str, 
                            save_path: Optional[str] = None) -> Dict[str, Any]:
        """Take screenshot of VSCode window
        
        Args:
            client_id: Target client ID
            save_path: Optional path to save screenshot
            
        Returns:
            Command result with screenshot path
        """
        params = {}
        if save_path:
            params['save_path'] = save_path
            
        return await self.forwarder.forward_command(
            client_id, 'take_screenshot', params
        )
        
    async def find_and_click(self, client_id: str, element_text: str,
                           use_background: bool = True) -> Dict[str, Any]:
        """Find element by text and click it
        
        Args:
            client_id: Target client ID
            element_text: Text to search for
            use_background: Use background click if True
            
        Returns:
            Command result
        """
        # Get current content
        content = await self.get_content(client_id)
        
        # Find element
        elements = self.ui_analyzer.find_elements_by_name(content, element_text)
        
        if not elements:
            return {'success': False, 'error': f"Element '{element_text}' not found"}
            
        # Click first matching element
        element = elements[0]
        element_name = element.get('name', '')
        
        if use_background:
            return await self.background_click(client_id, element_name)
        else:
            # Use regular click with activation
            await self.activate_window(client_id)
            params = {'element_name': element_name}
            return await self.forwarder.forward_command(
                client_id, 'click_element', params
            )
            
    async def get_roo_code_state(self, client_id: str) -> Dict[str, Any]:
        """Get current Roo Code state
        
        Args:
            client_id: Target client ID
            
        Returns:
            Dictionary with Roo Code state information
        """
        content = await self.get_content(client_id)
        
        # Analyze Roo Code elements
        roo_elements = self.ui_analyzer.find_roo_code_elements(content)
        conversation = self.ui_analyzer.find_roo_conversation(content)
        
        state = {
            'has_roo_code': any(v is not None for v in roo_elements.values()),
            'elements': roo_elements,
            'conversation': conversation,
            'window_active': content.get('is_active', False)
        }
        
        return state
        
    async def send_to_roo_code(self, client_id: str, message: str,
                             use_background: bool = True) -> Dict[str, Any]:
        """Send message to Roo Code
        
        Args:
            client_id: Target client ID
            message: Message to send
            use_background: Use background operations if True
            
        Returns:
            Command result
        """
        # Get current state
        state = await self.get_roo_code_state(client_id)
        
        if not state['has_roo_code']:
            return {'success': False, 'error': 'Roo Code not found'}
            
        # Find input box
        input_element = state['elements'].get('input_box')
        send_button = state['elements'].get('send_button')
        
        if not input_element or not send_button:
            return {'success': False, 'error': 'Roo Code input elements not found'}
            
        results = []
        
        # Input text
        if use_background:
            result = await self.background_input(
                client_id, 
                input_element.get('name', ''),
                message
            )
            results.append(('input', result))
        else:
            await self.activate_window(client_id)
            result = await self.type_text(client_id, message)
            results.append(('input', result))
            
        # Click send
        if use_background:
            result = await self.background_click(
                client_id,
                send_button.get('name', '')
            )
            results.append(('send', result))
        else:
            result = await self.send_keys(client_id, 'enter')
            results.append(('send', result))
            
        # Check if all operations succeeded
        all_success = all(r[1].get('success', False) for r in results)
        
        return {
            'success': all_success,
            'operations': results
        }
        
    async def wait_for_element(self, client_id: str, element_name: str,
                             timeout: float = 30.0, 
                             check_interval: float = 1.0) -> bool:
        """Wait for element to appear
        
        Args:
            client_id: Target client ID
            element_name: Element name to wait for
            timeout: Maximum wait time
            check_interval: How often to check
            
        Returns:
            True if element found within timeout
        """
        import asyncio
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            try:
                content = await self.get_content(client_id)
                elements = self.ui_analyzer.find_elements_by_name(content, element_name)
                
                if elements:
                    return True
                    
            except Exception:
                pass
                
            await asyncio.sleep(check_interval)
            
        return False