"""Client discovery and management utilities"""

from typing import Optional, List, Dict, Any
from .cybercorp_client import CyberCorpClient


class ClientManager:
    """Manages client discovery and information retrieval"""
    
    def __init__(self, client: CyberCorpClient):
        """Initialize ClientManager
        
        Args:
            client: Connected CyberCorpClient instance
        """
        self.client = client
        
    async def list_clients(self) -> List[Dict[str, Any]]:
        """Get list of all connected clients
        
        Returns:
            List of client information dictionaries
            
        Raises:
            Exception: If request fails
        """
        response = await self.client.send_request('request', 'list_clients')
        
        if response.get('success'):
            return response.get('clients', [])
        else:
            raise Exception(f"Failed to list clients: {response.get('error', 'Unknown error')}")
            
    async def find_client_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Find specific client by username
        
        Args:
            username: Username to search for
            
        Returns:
            Client information if found, None otherwise
        """
        clients = await self.list_clients()
        
        for client in clients:
            # Check both user_session and username fields
            if (client.get('user_session') == username or 
                client.get('user_session', '').startswith(f"{username}_")):
                return client
                
        return None
        
    async def find_client_id_by_username(self, username: str) -> Optional[str]:
        """Find client ID by username
        
        Args:
            username: Username to search for
            
        Returns:
            Client ID if found, None otherwise
        """
        client = await self.find_client_by_username(username)
        return client['id'] if client else None
        
    async def get_client_capabilities(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get capabilities of specific client
        
        Args:
            client_id: Client ID
            
        Returns:
            Client capabilities if found, None otherwise
        """
        clients = await self.list_clients()
        
        for client in clients:
            if client.get('id') == client_id:
                return client.get('capabilities', {})
                
        return None
        
    async def wait_for_client(self, username: str, timeout: float = 30.0, 
                            check_interval: float = 1.0) -> Optional[Dict[str, Any]]:
        """Wait for a specific client to connect
        
        Args:
            username: Username to wait for
            timeout: Maximum time to wait in seconds
            check_interval: How often to check in seconds
            
        Returns:
            Client information if found within timeout, None otherwise
        """
        import asyncio
        
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            client = await self.find_client_by_username(username)
            if client:
                return client
                
            await asyncio.sleep(check_interval)
            
        return None
        
    async def get_client_count(self) -> int:
        """Get total number of connected clients
        
        Returns:
            Number of connected clients
        """
        clients = await self.list_clients()
        return len(clients)
        
    async def get_clients_by_capability(self, capability: str) -> List[Dict[str, Any]]:
        """Get all clients with a specific capability
        
        Args:
            capability: Capability name to filter by
            
        Returns:
            List of clients with the specified capability
        """
        clients = await self.list_clients()
        
        matching_clients = []
        for client in clients:
            capabilities = client.get('capabilities', {})
            if capabilities.get(capability):
                matching_clients.append(client)
                
        return matching_clients
        
    async def get_client_status(self, client_id: str) -> Optional[str]:
        """Get status of specific client
        
        Args:
            client_id: Client ID
            
        Returns:
            Client status if found, None otherwise
        """
        clients = await self.list_clients()
        
        for client in clients:
            if client.get('id') == client_id:
                return client.get('status', 'unknown')
                
        return None
        
    def format_client_info(self, client: Dict[str, Any]) -> str:
        """Format client information for display
        
        Args:
            client: Client information dictionary
            
        Returns:
            Formatted string representation
        """
        lines = []
        lines.append(f"Client ID: {client.get('id', 'Unknown')}")
        lines.append(f"  User Session: {client.get('user_session', 'Unknown')}")
        lines.append(f"  Status: {client.get('status', 'Unknown')}")
        lines.append(f"  Connected At: {client.get('connected_at', 'Unknown')}")
        
        capabilities = client.get('capabilities', {})
        if capabilities:
            lines.append("  Capabilities:")
            for cap, enabled in capabilities.items():
                if enabled:
                    lines.append(f"    - {cap}")
                    
        system_info = client.get('system_info', {})
        if system_info:
            lines.append("  System Info:")
            lines.append(f"    Platform: {system_info.get('platform', 'Unknown')}")
            lines.append(f"    Node: {system_info.get('node', 'Unknown')}")
            
        return '\n'.join(lines)