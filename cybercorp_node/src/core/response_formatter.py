"""
Unified response formatter for consistent client responses
"""

import json
import time
from datetime import datetime
from typing import Any, Dict, Optional, Union
import traceback
import logging

logger = logging.getLogger(__name__)


class ResponseFormatter:
    """Formats all client responses in a consistent structure"""
    
    @staticmethod
    def success(data: Any = None, message: str = None, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Format a successful response
        
        Args:
            data: The actual response data
            message: Optional success message
            metadata: Optional metadata (execution time, etc.)
            
        Returns:
            Formatted response dictionary
        """
        response = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'error': None
        }
        
        if data is not None:
            response['data'] = data
            
        if message:
            response['message'] = message
            
        if metadata:
            response['metadata'] = metadata
            
        return response
    
    @staticmethod
    def error(error: Union[str, Exception], error_code: str = None, 
              details: Dict[str, Any] = None, traceback_info: bool = True) -> Dict[str, Any]:
        """
        Format an error response
        
        Args:
            error: Error message or exception
            error_code: Optional error code for categorization
            details: Additional error details
            traceback_info: Whether to include traceback for exceptions
            
        Returns:
            Formatted error response dictionary
        """
        response = {
            'success': False,
            'timestamp': datetime.now().isoformat(),
            'data': None
        }
        
        # Handle exception objects
        if isinstance(error, Exception):
            error_message = str(error)
            error_type = type(error).__name__
            
            if traceback_info:
                tb = traceback.format_exc()
                response['traceback'] = tb
                
            response['error'] = {
                'message': error_message,
                'type': error_type
            }
        else:
            response['error'] = {
                'message': str(error),
                'type': 'Error'
            }
            
        if error_code:
            response['error']['code'] = error_code
            
        if details:
            response['error']['details'] = details
            
        return response
    
    @staticmethod
    def command_result(command: str, result: Any, execution_time: float, 
                      command_id: str = None, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Format a command execution result
        
        Args:
            command: The command that was executed
            result: The command result
            execution_time: Time taken to execute (seconds)
            command_id: Optional command ID
            params: Optional command parameters
            
        Returns:
            Formatted command result
        """
        # Determine if command was successful based on result
        if isinstance(result, dict) and 'error' in result:
            # Result contains an error
            return ResponseFormatter.error(
                result['error'],
                error_code='COMMAND_FAILED',
                details={
                    'command': command,
                    'command_id': command_id,
                    'execution_time': execution_time,
                    'params': params
                }
            )
        
        # Successful command
        metadata = {
            'command': command,
            'execution_time': execution_time
        }
        
        if command_id:
            metadata['command_id'] = command_id
            
        if params:
            metadata['params'] = params
            
        return ResponseFormatter.success(
            data=result,
            metadata=metadata
        )
    
    @staticmethod
    def validate_response(response: Dict[str, Any]) -> bool:
        """
        Validate that a response follows the standard format
        
        Args:
            response: Response dictionary to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['success', 'timestamp', 'error']
        
        # Check required fields
        for field in required_fields:
            if field not in response:
                logger.warning(f"Response missing required field: {field}")
                return False
                
        # Check field types
        if not isinstance(response['success'], bool):
            logger.warning("Response 'success' field must be boolean")
            return False
            
        # If error response, check error structure
        if not response['success'] and response['error']:
            if not isinstance(response['error'], dict):
                logger.warning("Error response must have dict 'error' field")
                return False
            if 'message' not in response['error']:
                logger.warning("Error response must have 'message' field")
                return False
                
        return True
    
    @staticmethod
    def normalize_legacy_response(legacy_response: Any, command: str = None) -> Dict[str, Any]:
        """
        Convert legacy response formats to unified format
        
        Args:
            legacy_response: Response in old format
            command: Optional command name for context
            
        Returns:
            Normalized response in unified format
        """
        # Handle None responses
        if legacy_response is None:
            return ResponseFormatter.error(
                "Command returned no response",
                error_code='NO_RESPONSE'
            )
        
        # Handle boolean responses
        if isinstance(legacy_response, bool):
            return ResponseFormatter.success(
                data={'result': legacy_response},
                message=f"Command {'succeeded' if legacy_response else 'failed'}"
            )
        
        # Handle dict responses with success field
        if isinstance(legacy_response, dict):
            if 'success' in legacy_response:
                # Already has success field, normalize it
                success = legacy_response.pop('success')
                if success:
                    return ResponseFormatter.success(data=legacy_response)
                else:
                    error_msg = legacy_response.pop('error', 'Unknown error')
                    return ResponseFormatter.error(error_msg, details=legacy_response)
            
            # Dict without success field - assume success
            return ResponseFormatter.success(data=legacy_response)
        
        # Handle list responses
        if isinstance(legacy_response, list):
            return ResponseFormatter.success(
                data={'items': legacy_response, 'count': len(legacy_response)}
            )
        
        # Handle string responses
        if isinstance(legacy_response, str):
            return ResponseFormatter.success(
                data={'message': legacy_response}
            )
        
        # Default - wrap in data field
        return ResponseFormatter.success(data=legacy_response)


# Convenience functions
def format_success(*args, **kwargs):
    """Convenience function for ResponseFormatter.success"""
    return ResponseFormatter.success(*args, **kwargs)

def format_error(*args, **kwargs):
    """Convenience function for ResponseFormatter.error"""
    return ResponseFormatter.error(*args, **kwargs)

def format_command_result(*args, **kwargs):
    """Convenience function for ResponseFormatter.command_result"""
    return ResponseFormatter.command_result(*args, **kwargs)