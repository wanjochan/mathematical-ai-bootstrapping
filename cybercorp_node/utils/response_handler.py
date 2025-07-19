"""Response handling utilities for standardized error handling"""

import asyncio
import traceback
from typing import Any, Dict, Optional, Union, Callable
from datetime import datetime


class ResponseHandler:
    """Standardized response and error handling utilities"""
    
    @staticmethod
    def create_success_response(data: Any, message: Optional[str] = None) -> Dict[str, Any]:
        """Create standardized success response
        
        Args:
            data: Response data
            message: Optional success message
            
        Returns:
            Standardized success response
        """
        response = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        
        if message:
            response['message'] = message
            
        return response
        
    @staticmethod
    def create_error_response(error: Union[str, Exception], 
                            context: Optional[str] = None,
                            details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create standardized error response
        
        Args:
            error: Error message or exception
            context: Context where error occurred
            details: Additional error details
            
        Returns:
            Standardized error response
        """
        response = {
            'success': False,
            'timestamp': datetime.now().isoformat(),
            'error': str(error)
        }
        
        if context:
            response['context'] = context
            
        if details:
            response['details'] = details
            
        if isinstance(error, Exception):
            response['error_type'] = type(error).__name__
            
        return response
        
    @staticmethod
    def handle_timeout(command: str, timeout: float, 
                      details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Standard timeout handling
        
        Args:
            command: Command that timed out
            timeout: Timeout duration
            details: Additional details
            
        Returns:
            Timeout error response
        """
        return ResponseHandler.create_error_response(
            f"Command '{command}' timed out after {timeout} seconds",
            context="timeout",
            details=details
        )
        
    @staticmethod
    def handle_error(error: Exception, context: str,
                    include_traceback: bool = False) -> Dict[str, Any]:
        """Standard error handling with optional traceback
        
        Args:
            error: Exception to handle
            context: Context where error occurred
            include_traceback: Whether to include full traceback
            
        Returns:
            Error response with details
        """
        details = {}
        
        if include_traceback:
            details['traceback'] = traceback.format_exc()
            
        return ResponseHandler.create_error_response(
            error,
            context=context,
            details=details
        )
        
    @staticmethod
    def validate_response(response: Any, expected_type: str,
                        required_fields: Optional[list] = None) -> Dict[str, Any]:
        """Validate response format and required fields
        
        Args:
            response: Response to validate
            expected_type: Expected response type
            required_fields: List of required field names
            
        Returns:
            Validation result with success status and any errors
        """
        validation = {
            'valid': True,
            'errors': []
        }
        
        # Check response is a dictionary
        if not isinstance(response, dict):
            validation['valid'] = False
            validation['errors'].append(f"Response is not a dictionary, got {type(response).__name__}")
            return validation
            
        # Check response type
        if response.get('type') != expected_type:
            validation['valid'] = False
            validation['errors'].append(
                f"Expected type '{expected_type}', got '{response.get('type', 'None')}'"
            )
            
        # Check required fields
        if required_fields:
            for field in required_fields:
                if field not in response:
                    validation['valid'] = False
                    validation['errors'].append(f"Missing required field: {field}")
                    
        return validation
        
    @staticmethod
    async def with_retry(operation: Callable, max_retries: int = 3,
                        retry_delay: float = 1.0,
                        exponential_backoff: bool = True,
                        on_retry: Optional[Callable] = None) -> Any:
        """Execute operation with automatic retry on failure
        
        Args:
            operation: Async callable to execute
            max_retries: Maximum retry attempts
            retry_delay: Initial delay between retries
            exponential_backoff: Whether to use exponential backoff
            on_retry: Optional callback for each retry
            
        Returns:
            Result from successful operation
            
        Raises:
            Last exception if all retries fail
        """
        last_error = None
        delay = retry_delay
        
        for attempt in range(max_retries + 1):
            try:
                return await operation()
            except Exception as e:
                last_error = e
                
                if attempt < max_retries:
                    if on_retry:
                        await on_retry(attempt + 1, e)
                        
                    await asyncio.sleep(delay)
                    
                    if exponential_backoff:
                        delay *= 2
                        
        raise last_error
        
    @staticmethod
    def format_error_message(error: Exception, include_type: bool = True,
                           max_length: Optional[int] = None) -> str:
        """Format error message for display
        
        Args:
            error: Exception to format
            include_type: Whether to include error type
            max_length: Maximum message length
            
        Returns:
            Formatted error message
        """
        if include_type:
            message = f"{type(error).__name__}: {str(error)}"
        else:
            message = str(error)
            
        if max_length and len(message) > max_length:
            message = message[:max_length-3] + "..."
            
        return message
        
    @staticmethod
    def merge_responses(*responses: Dict[str, Any]) -> Dict[str, Any]:
        """Merge multiple responses into one
        
        Args:
            *responses: Response dictionaries to merge
            
        Returns:
            Merged response with combined data
        """
        merged = {
            'success': all(r.get('success', False) for r in responses),
            'timestamp': datetime.now().isoformat(),
            'results': []
        }
        
        for i, response in enumerate(responses):
            result = {
                'index': i,
                'success': response.get('success', False)
            }
            
            if 'data' in response:
                result['data'] = response['data']
            if 'error' in response:
                result['error'] = response['error']
                
            merged['results'].append(result)
            
        return merged
        
    @staticmethod
    def extract_data(response: Dict[str, Any], path: str, 
                    default: Any = None) -> Any:
        """Extract data from nested response structure
        
        Args:
            response: Response dictionary
            path: Dot-separated path to data (e.g., 'data.user.name')
            default: Default value if path not found
            
        Returns:
            Extracted data or default value
        """
        current = response
        
        for key in path.split('.'):
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
                
        return current