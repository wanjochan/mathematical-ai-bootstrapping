"""Cursor IDE controller for automated interactions"""

import asyncio
import time
import logging
import cv2
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from .vision_integration import VisionWindowAnalyzer
from .remote_control import RemoteController

logger = logging.getLogger(__name__)


@dataclass
class CursorDialogElements:
    """Cursor IDE dialog UI elements"""
    input_box: Optional[Dict] = None
    send_button: Optional[Dict] = None
    response_area: Optional[Dict] = None
    window_hwnd: Optional[int] = None
    detection_confidence: float = 0.0
    last_successful_positions: Optional[Dict] = None


@dataclass 
class AdaptivePositionMemory:
    """Memory for adaptive positioning"""
    successful_input_positions: List[Tuple[int, int]] = None
    successful_send_positions: List[Tuple[int, int]] = None
    window_layout_hash: Optional[str] = None
    success_count: int = 0
    failure_count: int = 0
    
    def __post_init__(self):
        if self.successful_input_positions is None:
            self.successful_input_positions = []
        if self.successful_send_positions is None:
            self.successful_send_positions = []


class CursorIDEController:
    """Controller for Cursor IDE AI assistant interactions"""
    
    def __init__(self, controller: RemoteController):
        self.controller = controller
        self.vision_analyzer = VisionWindowAnalyzer(controller)
        self.cursor_window = None
        self.dialog_elements = None
        self.position_memory = AdaptivePositionMemory()
        self.adaptive_learning_enabled = True
        
    async def find_cursor_window(self) -> Optional[int]:
        """Find Cursor IDE window"""
        logger.info("Searching for Cursor IDE window...")
        
        windows = await self.controller.get_windows()
        
        # Look for Cursor IDE window (including hidden ones)
        cursor_candidates = []
        for window in windows:
            title = window.get('title', '').lower()
            if 'cursor' in title:
                cursor_candidates.append(window)
                logger.info(f"Found Cursor candidate: {window['title']} (visible: {window.get('visible', False)})")
        
        if not cursor_candidates:
            logger.error("No Cursor IDE window found")
            return None
        
        # Use the first candidate or the active one
        for candidate in cursor_candidates:
            if candidate.get('is_active'):
                self.cursor_window = candidate
                break
        
        if not self.cursor_window:
            self.cursor_window = cursor_candidates[0]
        
        logger.info(f"Selected Cursor window: {self.cursor_window['title']}")
        
        # Try to activate the window if it's hidden
        if not self.cursor_window.get('visible', True):
            logger.info("Window is hidden, attempting to activate...")
            try:
                await self.controller.execute_command('activate_window', {'hwnd': self.cursor_window['hwnd']})
                logger.info("Window activation command sent")
            except Exception as e:
                logger.warning(f"Failed to activate window: {e}")
        
        return self.cursor_window['hwnd']
    
    async def detect_dialog_elements(self, hwnd: int = None) -> CursorDialogElements:
        """Detect UI elements in Cursor IDE dialog with enhanced precision and adaptive learning"""
        if hwnd is None:
            hwnd = await self.find_cursor_window()
            if not hwnd:
                return CursorDialogElements()
        
        logger.info("Analyzing Cursor IDE dialog elements with adaptive detection...")
        
        # Use adaptive detection method
        elements = await self._adaptive_detect_elements(hwnd)
        
        # Legacy fallback for response area detection
        if not elements.response_area:
            result = await self.vision_analyzer.analyze_window(hwnd, save_visualization=True)
            if result:
                text_regions = []
                for element in result.elements:
                    if element['type'] in ['text', 'panel'] and element['bbox']:
                        width = element['bbox'][2] - element['bbox'][0]
                        height = element['bbox'][3] - element['bbox'][1]
                        area = width * height
                        
                        # Large text area likely to be response area
                        if area > 10000:
                            text_regions.append(element)
                
                if text_regions:
                    # Choose the largest text region as response area
                    elements.response_area = max(text_regions, key=lambda x: 
                        (x['bbox'][2] - x['bbox'][0]) * (x['bbox'][3] - x['bbox'][1]))
                    logger.info(f"Found response area at {elements.response_area['center']}")
        
        self.dialog_elements = elements
        logger.info(f"Dialog analysis complete: input={bool(elements.input_box)}, "
                   f"button={bool(elements.send_button)}, response={bool(elements.response_area)}, "
                   f"confidence={elements.detection_confidence:.2f}")
        
        return elements
    
    async def send_prompt(self, prompt: str, timeout: int = 30) -> bool:
        """Send a prompt to Cursor IDE AI assistant with validation
        
        Args:
            prompt: Text to send
            timeout: Maximum time to wait for operations
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Sending prompt to Cursor IDE: {prompt[:50]}...")
        
        # Ensure we have dialog elements
        if not self.dialog_elements:
            hwnd = await self.find_cursor_window()
            if not hwnd:
                return False
            await self.detect_dialog_elements(hwnd)
        
        if not self.dialog_elements.input_box:
            logger.error("No input box found in Cursor IDE")
            return False
        
        # Try multiple input methods with validation
        success = False
        
        # Method 1: Standard keyboard input
        try:
            success = await self._send_prompt_keyboard(prompt)
            if success:
                logger.info("Prompt sent successfully via keyboard")
                # Learn from successful interaction
                input_pos = tuple(self.dialog_elements.input_box['center'])
                send_pos = tuple(self.dialog_elements.send_button['center']) if self.dialog_elements.send_button else None
                self._learn_from_success(input_pos, send_pos)
                return True
        except Exception as e:
            logger.warning(f"Keyboard input failed: {e}")
        
        # Method 2: Clipboard input (fallback)
        try:
            success = await self._send_prompt_clipboard(prompt)
            if success:
                logger.info("Prompt sent successfully via clipboard")
                # Learn from successful interaction
                input_pos = tuple(self.dialog_elements.input_box['center'])
                send_pos = tuple(self.dialog_elements.send_button['center']) if self.dialog_elements.send_button else None
                self._learn_from_success(input_pos, send_pos)
                return True
        except Exception as e:
            logger.warning(f"Clipboard input failed: {e}")
        
        # Learn from failure
        self._learn_from_failure()
        logger.error("All input methods failed")
        return False
    
    async def _send_prompt_keyboard(self, prompt: str) -> bool:
        """Send prompt using Win32 API for more reliable input"""
        hwnd = self.dialog_elements.window_hwnd
        
        # Method 1: Try to find and use edit controls directly
        try:
            # Enumerate child windows to find input controls
            result = await self.controller.execute_command('enum_child_windows', {'hwnd': hwnd})
            
            edit_controls = []
            for child in result.get('children', []):
                class_name = child.get('class_name', '').lower()
                if 'edit' in class_name or 'input' in class_name or 'text' in class_name:
                    edit_controls.append(child)
            
            # Try SendMessage to edit controls
            for edit_ctrl in edit_controls:
                edit_hwnd = edit_ctrl['hwnd']
                logger.debug(f"Trying Win32 SendMessage to edit control {edit_hwnd}")
                
                try:
                    # Clear existing text first
                    await self.controller.execute_command('win32_call', {
                        'function': 'SendMessage',
                        'args': [edit_hwnd, 0x000C, 0, ""]  # WM_SETTEXT with empty string
                    })
                    
                    # Set new text
                    result = await self.controller.execute_command('win32_call', {
                        'function': 'SendMessage', 
                        'args': [edit_hwnd, 0x000C, 0, prompt]  # WM_SETTEXT
                    })
                    
                    if result:
                        logger.info(f"Successfully set text via Win32 SendMessage")
                        # Validate input was successful
                        if await self._validate_input_win32(edit_hwnd, prompt):
                            return await self._trigger_send_win32(edit_hwnd)
                        
                except Exception as e:
                    logger.debug(f"SendMessage to edit control {edit_hwnd} failed: {e}")
                    continue
                    
        except Exception as e:
            logger.warning(f"Win32 edit control method failed: {e}")
        
        # Method 2: Fallback to position-based clicking + Win32 character sending
        try:
            input_center = self.dialog_elements.input_box['center']
            
            # Click on input box to focus
            await self.controller.click(input_center[0], input_center[1])
            await asyncio.sleep(0.5)
            
            # Clear existing content using Win32
            await self.controller.execute_command('win32_call', {
                'function': 'keybd_event',
                'args': [0x11, 0, 0, 0]  # Ctrl down
            })
            await self.controller.execute_command('win32_call', {
                'function': 'keybd_event', 
                'args': [0x41, 0, 0, 0]  # A down (Ctrl+A)
            })
            await self.controller.execute_command('win32_call', {
                'function': 'keybd_event',
                'args': [0x41, 0, 2, 0]  # A up
            })
            await self.controller.execute_command('win32_call', {
                'function': 'keybd_event',
                'args': [0x11, 0, 2, 0]  # Ctrl up
            })
            
            await asyncio.sleep(0.2)
            
            # Send Delete key
            await self.controller.execute_command('win32_call', {
                'function': 'keybd_event',
                'args': [0x2E, 0, 0, 0]  # Delete down
            })
            await self.controller.execute_command('win32_call', {
                'function': 'keybd_event',
                'args': [0x2E, 0, 2, 0]  # Delete up
            })
            
            await asyncio.sleep(0.3)
            
            # Send text character by character using Win32
            for char in prompt:
                char_code = ord(char)
                await self.controller.execute_command('win32_call', {
                    'function': 'PostMessage',
                    'args': [hwnd, 0x0102, char_code, 0]  # WM_CHAR
                })
                await asyncio.sleep(0.01)  # Small delay between characters
            
            logger.info("Text sent via Win32 PostMessage")
            
            # Validate input was successful
            if not await self._validate_input(prompt):
                logger.warning("Input validation failed for Win32 method")
                return False
            
            # Send the prompt
            return await self._trigger_send()
            
        except Exception as e:
            logger.error(f"Win32 fallback method failed: {e}")
            return False
    
    async def _send_prompt_clipboard(self, prompt: str) -> bool:
        """Send prompt using clipboard method with validation"""
        input_center = self.dialog_elements.input_box['center']
        
        # Click on input box to focus
        await self.controller.click(input_center[0], input_center[1])
        await asyncio.sleep(0.5)
        
        # Clear existing text
        await self.controller.send_keys("^a")
        await asyncio.sleep(0.2)
        await self.controller.send_keys("{DELETE}")
        await asyncio.sleep(0.3)
        
        # Set clipboard and paste
        if hasattr(self.controller, 'set_clipboard'):
            await self.controller.set_clipboard(prompt)
            await asyncio.sleep(0.2)
            await self.controller.send_keys("^v")
            await asyncio.sleep(0.5)
            
            # Validate input was successful
            if not await self._validate_input(prompt):
                logger.warning("Input validation failed for clipboard method")
                return False
            
            # Send the prompt
            return await self._trigger_send()
        else:
            logger.warning("Controller doesn't support clipboard operations")
            return False
    
    async def _validate_input(self, expected_text: str) -> bool:
        """Validate that text was successfully input"""
        try:
            # Method 1: Select all and copy to check content
            await self.controller.send_keys("^a")
            await asyncio.sleep(0.2)
            await self.controller.send_keys("^c")
            await asyncio.sleep(0.3)
            
            if hasattr(self.controller, 'get_clipboard'):
                actual_text = await self.controller.get_clipboard()
                if actual_text and actual_text.strip() == expected_text.strip():
                    logger.debug("Input validation successful")
                    return True
                else:
                    logger.warning(f"Text mismatch - expected: {expected_text[:30]}, got: {actual_text[:30] if actual_text else 'None'}")
                    return False
            else:
                # Method 2: Visual validation using screenshot analysis
                return await self._validate_input_visual(expected_text)
                
        except Exception as e:
            logger.warning(f"Input validation error: {e}")
            return False
    
    async def _validate_input_visual(self, expected_text: str) -> bool:
        """Validate input using visual analysis"""
        try:
            # Take screenshot of input area
            hwnd = self.dialog_elements.window_hwnd
            result = await self.vision_analyzer.analyze_window(hwnd)
            
            if result and hasattr(result, 'text_content'):
                # Simple heuristic: check if some keywords from expected text appear
                keywords = expected_text.lower().split()[:3]  # First 3 words
                detected_text = result.text_content.lower()
                
                matches = sum(1 for word in keywords if word in detected_text)
                if matches >= min(2, len(keywords)):  # At least 2 words or all if less than 2
                    logger.debug("Visual input validation successful")
                    return True
            
            logger.warning("Visual input validation failed")
            return False
            
        except Exception as e:
            logger.warning(f"Visual validation error: {e}")
            return False
    
    async def _trigger_send(self) -> bool:
        """Trigger sending the prompt"""
        try:
            # Click send button if available
            if self.dialog_elements.send_button:
                send_center = self.dialog_elements.send_button['center']
                await self.controller.click(send_center[0], send_center[1])
                logger.debug("Send button clicked")
            else:
                # Try Enter key as fallback
                await self.controller.send_keys("{ENTER}")
                logger.debug("Enter key sent as fallback")
            
            await asyncio.sleep(0.5)
            return True
            
        except Exception as e:
            logger.error(f"Failed to trigger send: {e}")
            return False
    
    async def _validate_input_win32(self, edit_hwnd: int, expected_text: str) -> bool:
        """Validate input using Win32 GetWindowText"""
        try:
            # Get text from edit control using Win32 API
            result = await self.controller.execute_command('win32_call', {
                'function': 'GetWindowText',
                'args': [edit_hwnd]
            })
            
            actual_text = result.get('text', '') if isinstance(result, dict) else str(result)
            
            if actual_text and actual_text.strip() == expected_text.strip():
                logger.debug("Win32 input validation successful")
                return True
            else:
                logger.warning(f"Win32 text mismatch - expected: {expected_text[:30]}, got: {actual_text[:30] if actual_text else 'None'}")
                return False
                
        except Exception as e:
            logger.warning(f"Win32 input validation error: {e}")
            return False
    
    async def _trigger_send_win32(self, edit_hwnd: int) -> bool:
        """Trigger sending using Win32 API"""
        try:
            # Method 1: Send Enter key to edit control
            await self.controller.execute_command('win32_call', {
                'function': 'SendMessage',
                'args': [edit_hwnd, 0x0100, 0x0D, 0]  # WM_KEYDOWN, VK_RETURN
            })
            await self.controller.execute_command('win32_call', {
                'function': 'SendMessage',
                'args': [edit_hwnd, 0x0101, 0x0D, 0]  # WM_KEYUP, VK_RETURN
            })
            
            logger.debug("Win32 Enter key sent to edit control")
            await asyncio.sleep(0.5)
            return True
            
        except Exception as e:
            logger.error(f"Failed to trigger send via Win32: {e}")
            return False
    
    async def wait_for_response(self, timeout: int = 60) -> bool:
        """Wait for Cursor IDE to complete response
        
        Args:
            timeout: Maximum time to wait
            
        Returns:
            True if response seems complete, False if timeout
        """
        logger.info("Waiting for Cursor IDE response...")
        
        start_time = time.time()
        last_check_time = 0
        stable_count = 0
        required_stable_count = 3  # Number of stable checks needed
        
        while time.time() - start_time < timeout:
            current_time = time.time()
            
            # Check every 2 seconds
            if current_time - last_check_time < 2:
                await asyncio.sleep(0.5)
                continue
            
            last_check_time = current_time
            
            # Take screenshot to check for activity indicators
            hwnd = self.dialog_elements.window_hwnd
            if hwnd:
                try:
                    # Look for typing indicators or busy states
                    result = await self.vision_analyzer.analyze_window(hwnd)
                    if result:
                        # Simple heuristic: if we see consistent UI, response is likely done
                        stable_count += 1
                        if stable_count >= required_stable_count:
                            logger.info("Response appears complete")
                            return True
                except Exception as e:
                    logger.warning(f"Error checking response status: {e}")
            
            await asyncio.sleep(1)
        
        logger.warning(f"Timeout waiting for response after {timeout}s")
        return False
    
    async def get_response_text(self) -> Optional[str]:
        """Get the response text from Cursor IDE
        
        Returns:
            Response text if available, None otherwise
        """
        logger.info("Extracting response text from Cursor IDE...")
        
        if not self.dialog_elements or not self.dialog_elements.response_area:
            logger.warning("No response area identified")
            return None
        
        try:
            # Select all text in response area and copy
            response_center = self.dialog_elements.response_area['center']
            
            # Click in response area
            await self.controller.click(response_center[0], response_center[1])
            await asyncio.sleep(0.5)
            
            # Select all and copy
            await self.controller.send_keys("^a")
            await asyncio.sleep(0.3)
            await self.controller.send_keys("^c")
            await asyncio.sleep(0.5)
            
            # Get clipboard content
            if hasattr(self.controller, 'get_clipboard'):
                text = await self.controller.get_clipboard()
                logger.info(f"Extracted response text: {len(text) if text else 0} characters")
                return text
            else:
                logger.warning("Controller doesn't support clipboard access")
                return None
                
        except Exception as e:
            logger.error(f"Failed to extract response text: {e}")
            return None
    
    async def send_and_get_response(self, prompt: str, timeout: int = 90) -> Optional[str]:
        """Send prompt and get response in one operation
        
        Args:
            prompt: Text to send
            timeout: Maximum time to wait for complete operation
            
        Returns:
            Response text if successful, None otherwise
        """
        logger.info(f"Starting full interaction with prompt: {prompt[:50]}...")
        
        # Send prompt
        if not await self.send_prompt(prompt):
            return None
        
        # Wait for response
        if not await self.wait_for_response(timeout):
            logger.warning("Response may be incomplete due to timeout")
        
        # Get response text
        response = await self.get_response_text()
        
        if response:
            logger.info(f"Full interaction completed, response length: {len(response)}")
        else:
            logger.error("Failed to get response text")
        
        return response
    
    async def refresh_dialog_elements(self) -> bool:
        """Refresh the detected dialog elements"""
        if not self.cursor_window:
            hwnd = await self.find_cursor_window()
            if not hwnd:
                return False
        else:
            hwnd = self.cursor_window['hwnd']
        
        elements = await self.detect_dialog_elements(hwnd)
        return bool(elements.input_box and elements.send_button)
    
    def _score_input_candidate(self, element: Dict, window_bounds: Optional[Tuple[int, int, int, int]]) -> float:
        """Score an input element candidate based on Cursor IDE characteristics"""
        bbox = element['bbox']
        center = element['center']
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        
        score = 0.0
        
        # Size scoring - Cursor chat input is typically wide but not too tall
        if 300 <= width <= 800:
            score += 0.4
        elif width > 200:
            score += 0.2
        
        if 25 <= height <= 60:
            score += 0.3
        elif height > 15:
            score += 0.1
        
        # Position scoring - input usually in bottom third of window
        if window_bounds:
            window_height = window_bounds[3] - window_bounds[1]
            relative_y = (center[1] - window_bounds[1]) / window_height
            if relative_y > 0.7:  # Bottom 30% of window
                score += 0.3
            elif relative_y > 0.5:  # Bottom 50% of window  
                score += 0.1
        
        return score
    
    def _detect_cursor_specific_elements(self, result) -> List[Tuple[Dict, float]]:
        """Detect Cursor IDE specific UI patterns"""
        candidates = []
        
        # Look for elements with Cursor-specific characteristics
        for element in result.elements:
            if element['type'] in ['text', 'panel']:
                bbox = element['bbox']
                width = bbox[2] - bbox[0]
                height = bbox[3] - bbox[1]
                
                # Look for "Plan, search, build anything" placeholder pattern
                if 400 <= width <= 900 and 30 <= height <= 80:
                    # Create a synthetic input element based on this region
                    synthetic_input = {
                        'type': 'input',
                        'bbox': bbox,
                        'center': element['center'],
                        'confidence': 0.7,
                        'source': 'cursor_specific'
                    }
                    candidates.append((synthetic_input, 0.6))
        
        return candidates
    
    def _create_fallback_input_element(self, window_bounds: Optional[Tuple[int, int, int, int]]) -> Dict:
        """Create fallback input element using heuristic positioning"""
        if window_bounds:
            x1, y1, x2, y2 = window_bounds
            window_width = x2 - x1
            window_height = y2 - y1
            
            # Position input box in bottom area (75% width, 15% from bottom)
            input_width = int(window_width * 0.75)
            input_height = 40
            input_x = x1 + (window_width - input_width) // 2
            input_y = y2 - int(window_height * 0.15)
            
            return {
                'type': 'input',
                'bbox': [input_x, input_y, input_x + input_width, input_y + input_height],
                'center': [input_x + input_width // 2, input_y + input_height // 2],
                'confidence': 0.3,
                'source': 'fallback_heuristic'
            }
        else:
            # Default fallback position
            return {
                'type': 'input',
                'bbox': [100, 600, 700, 640],
                'center': [400, 620],
                'confidence': 0.1,
                'source': 'default_fallback'
            }
    
    def _create_fallback_send_element(self, input_element: Dict, window_bounds: Optional[Tuple[int, int, int, int]]) -> Dict:
        """Create fallback send button element near input box"""
        input_bbox = input_element['bbox']
        
        # Position send button to the right of input box
        button_x = input_bbox[2] + 10
        button_y = input_bbox[1] + 5
        button_width = 60
        button_height = 30
        
        return {
            'type': 'button',
            'bbox': [button_x, button_y, button_x + button_width, button_y + button_height],
            'center': [button_x + button_width // 2, button_y + button_height // 2],
            'confidence': 0.2,
            'source': 'fallback_near_input'
        }
    
    def _calculate_window_layout_hash(self, result) -> str:
        """Calculate a hash representing the current window layout"""
        import hashlib
        
        # Create a signature based on major UI elements positions
        signature_data = []
        
        if hasattr(result, 'window_bounds') and result.window_bounds:
            signature_data.append(f"window:{result.window_bounds}")
        
        # Add element positions (simplified)
        for element in result.elements[:10]:  # First 10 elements only
            elem_type = element.get('type', 'unknown')
            bbox = element.get('bbox', [0,0,0,0])
            signature_data.append(f"{elem_type}:{bbox[0]//50},{bbox[1]//50}")  # Quantized positions
        
        signature_str = "|".join(signature_data)
        return hashlib.md5(signature_str.encode()).hexdigest()[:8]
    
    def _learn_from_success(self, input_position: Tuple[int, int], send_position: Optional[Tuple[int, int]] = None):
        """Learn from successful interactions"""
        if not self.adaptive_learning_enabled:
            return
        
        self.position_memory.success_count += 1
        
        # Add successful positions to memory
        if input_position not in self.position_memory.successful_input_positions:
            self.position_memory.successful_input_positions.append(input_position)
            # Keep only last 10 successful positions
            if len(self.position_memory.successful_input_positions) > 10:
                self.position_memory.successful_input_positions.pop(0)
        
        if send_position and send_position not in self.position_memory.successful_send_positions:
            self.position_memory.successful_send_positions.append(send_position)
            if len(self.position_memory.successful_send_positions) > 10:
                self.position_memory.successful_send_positions.pop(0)
        
        logger.debug(f"Learned from success: input={input_position}, send={send_position}")
    
    def _learn_from_failure(self):
        """Learn from failed interactions"""
        if not self.adaptive_learning_enabled:
            return
        
        self.position_memory.failure_count += 1
        logger.debug(f"Recorded failure. Total failures: {self.position_memory.failure_count}")
    
    def _get_adaptive_input_candidates(self, window_bounds: Optional[Tuple[int, int, int, int]]) -> List[Tuple[Dict, float]]:
        """Generate input candidates based on learned positions"""
        candidates = []
        
        # Use successful positions from memory
        for pos in self.position_memory.successful_input_positions:
            # Create synthetic element based on successful position
            synthetic_input = {
                'type': 'input',
                'bbox': [pos[0] - 100, pos[1] - 20, pos[0] + 100, pos[1] + 20],
                'center': pos,
                'confidence': 0.8,
                'source': 'adaptive_memory'
            }
            score = 0.8  # High confidence for learned positions
            candidates.append((synthetic_input, score))
        
        return candidates
    
    async def _adaptive_detect_elements(self, hwnd: int) -> CursorDialogElements:
        """Enhanced detection with adaptive learning"""
        # Get current window analysis
        result = await self.vision_analyzer.analyze_window(hwnd, save_visualization=True)
        if not result:
            return CursorDialogElements(window_hwnd=hwnd)
        
        # Check if window layout has changed
        current_layout_hash = self._calculate_window_layout_hash(result)
        layout_changed = (self.position_memory.window_layout_hash != current_layout_hash)
        
        if layout_changed:
            logger.info(f"Window layout changed: {self.position_memory.window_layout_hash} -> {current_layout_hash}")
            self.position_memory.window_layout_hash = current_layout_hash
        
        elements = CursorDialogElements(window_hwnd=hwnd)
        window_bounds = result.window_bounds if hasattr(result, 'window_bounds') else None
        
        # Combine multiple detection strategies
        input_candidates = []
        
        # Strategy 1: Standard detection
        for element in result.elements:
            if element['type'] == 'input':
                score = self._score_input_candidate(element, window_bounds)
                input_candidates.append((element, score))
        
        # Strategy 2: Cursor-specific patterns
        cursor_specific = self._detect_cursor_specific_elements(result)
        input_candidates.extend(cursor_specific)
        
        # Strategy 3: Adaptive candidates (learned positions)
        if not layout_changed:  # Only use learned positions if layout hasn't changed
            adaptive_candidates = self._get_adaptive_input_candidates(window_bounds)
            input_candidates.extend(adaptive_candidates)
        
        # Select best candidate
        if input_candidates:
            best_input = max(input_candidates, key=lambda x: x[1])
            if best_input[1] > 0.2:  # Lower threshold to be more adaptive
                elements.input_box = best_input[0]
                elements.detection_confidence = best_input[1]
                logger.info(f"Selected input box with confidence {best_input[1]:.2f} from {best_input[0].get('source', 'unknown')}")
        
        # Fallback if no good candidate found
        if not elements.input_box:
            elements.input_box = self._create_fallback_input_element(window_bounds)
            elements.detection_confidence = 0.1
        
        # Send button detection (simplified for now)
        if elements.input_box:
            elements.send_button = self._create_fallback_send_element(elements.input_box, window_bounds)
        
        return elements