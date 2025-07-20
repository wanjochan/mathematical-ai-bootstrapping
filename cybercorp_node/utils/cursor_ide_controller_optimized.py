"""Optimized Cursor IDE controller using Vision + Win32 API"""

import asyncio
import time
import logging
import hashlib
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class OptimizedCursorDialogElements:
    """Optimized Cursor IDE dialog UI elements with Win32 handles"""
    input_box: Optional[Dict] = None
    input_hwnd: Optional[int] = None  # Direct Win32 handle for input
    send_button: Optional[Dict] = None
    send_hwnd: Optional[int] = None   # Direct Win32 handle for button
    response_area: Optional[Dict] = None
    window_hwnd: Optional[int] = None
    detection_confidence: float = 0.0
    detection_method: str = "unknown"


class OptimizedCursorIDEController:
    """Optimized controller using Vision + Win32 API for maximum speed and reliability"""
    
    def __init__(self, controller):
        self.controller = controller
        self.vision_analyzer = None  # Will be set if available
        self.cursor_window = None
        self.dialog_elements = None
        self.position_memory = {}  # Simplified memory for successful positions
        
    async def initialize_vision(self):
        """Initialize vision analyzer if available"""
        try:
            from .vision_integration import VisionWindowAnalyzer
            self.vision_analyzer = VisionWindowAnalyzer(self.controller)
            logger.info("Vision analyzer initialized")
        except Exception as e:
            logger.warning(f"Vision analyzer not available: {e}")
    
    async def find_cursor_window(self) -> Optional[int]:
        """Find Cursor IDE window using enhanced detection"""
        logger.info("Finding Cursor IDE window...")
        
        windows = await self.controller.get_windows()
        
        cursor_candidates = []
        for window in windows:
            title = window.get('title', '').lower()
            if 'cursor' in title:
                cursor_candidates.append(window)
                logger.info(f"Found Cursor candidate: {window['title']}")
        
        if not cursor_candidates:
            logger.error("No Cursor IDE window found")
            return None
        
        # Select best candidate (prefer visible/active ones)
        self.cursor_window = cursor_candidates[0]
        for candidate in cursor_candidates:
            if candidate.get('is_active') or candidate.get('visible'):
                self.cursor_window = candidate
                break
        
        hwnd = self.cursor_window['hwnd']
        logger.info(f"Selected Cursor window: {self.cursor_window['title']} (HWND: {hwnd})")
        
        # Try to activate window
        await self._activate_window(hwnd)
        
        return hwnd
    
    async def _activate_window(self, hwnd: int):
        """Activate window using multiple Win32 methods"""
        try:
            # Method 1: ShowWindow
            await self.controller.execute_command('win32_call', {
                'function': 'ShowWindow',
                'args': [hwnd, 9]  # SW_RESTORE
            })
            
            await self.controller.execute_command('win32_call', {
                'function': 'ShowWindow', 
                'args': [hwnd, 5]  # SW_SHOW
            })
            
            # Method 2: SetForegroundWindow
            await self.controller.execute_command('win32_call', {
                'function': 'SetForegroundWindow',
                'args': [hwnd]
            })
            
            # Method 3: SetActiveWindow
            await self.controller.execute_command('win32_call', {
                'function': 'SetActiveWindow',
                'args': [hwnd]
            })
            
            logger.info("Window activation completed")
            await asyncio.sleep(1)  # Give window time to activate
            
        except Exception as e:
            logger.warning(f"Window activation failed: {e}")
    
    async def detect_dialog_elements_optimized(self, hwnd: int) -> OptimizedCursorDialogElements:
        """Optimized detection using Vision + Win32 child enumeration"""
        logger.info("Starting optimized dialog element detection...")
        
        elements = OptimizedCursorDialogElements(window_hwnd=hwnd)
        
        # Method 1: Try vision-based detection first (most accurate)
        if self.vision_analyzer:
            try:
                logger.info("Attempting vision-based detection...")
                vision_result = await self.vision_analyzer.analyze_window(hwnd, save_visualization=True)
                
                if vision_result and vision_result.elements:
                    # Process vision results
                    input_candidates = []
                    button_candidates = []
                    
                    for element in vision_result.elements:
                        if element['type'] == 'input':
                            score = self._score_input_element(element)
                            input_candidates.append((element, score))
                        elif element['type'] == 'button':
                            button_candidates.append(element)
                    
                    # Select best input candidate
                    if input_candidates:
                        best_input = max(input_candidates, key=lambda x: x[1])
                        if best_input[1] > 0.3:
                            elements.input_box = best_input[0]
                            elements.detection_confidence = best_input[1]
                            elements.detection_method = "vision"
                            logger.info(f"Vision detected input box with confidence {best_input[1]:.2f}")
                    
                    # Select send button
                    if elements.input_box and button_candidates:
                        elements.send_button = self._find_nearest_button(elements.input_box, button_candidates)
                        if elements.send_button:
                            logger.info("Vision detected send button")
                
            except Exception as e:
                logger.warning(f"Vision detection failed: {e}")
        
        # Method 2: Win32 child window enumeration (as backup or complement)
        try:
            logger.info("Performing Win32 child window enumeration...")
            result = await self.controller.execute_command('enum_child_windows', {'hwnd': hwnd})
            
            if result and 'children' in result:
                # Find edit controls and map them to vision-detected positions
                edit_controls = []
                for child in result['children']:
                    class_name = child.get('class_name', '').lower()
                    child_hwnd = child.get('hwnd')
                    
                    if child_hwnd and ('edit' in class_name or 'input' in class_name or 'text' in class_name):
                        edit_controls.append(child)
                        logger.debug(f"Found Win32 edit control: {class_name} (HWND: {child_hwnd})")
                
                # Map vision detection to Win32 handles
                if elements.input_box and edit_controls:
                    # Find the edit control closest to vision-detected position
                    input_center = elements.input_box['center']
                    elements.input_hwnd = self._find_closest_edit_control(input_center, edit_controls)
                    if elements.input_hwnd:
                        logger.info(f"Mapped vision input to Win32 handle: {elements.input_hwnd}")
                
                # If no vision detection, use edit controls directly
                elif edit_controls and not elements.input_box:
                    # Use the largest/most likely edit control
                    elements.input_hwnd = edit_controls[0]['hwnd']
                    elements.detection_method = "win32_fallback"
                    logger.info(f"Using Win32 fallback edit control: {elements.input_hwnd}")
                
        except Exception as e:
            logger.warning(f"Win32 child enumeration failed: {e}")
        
        # Method 3: Heuristic positioning (last resort)
        if not elements.input_box and not elements.input_hwnd:
            logger.info("Using heuristic positioning as last resort...")
            elements = self._create_heuristic_elements(hwnd)
            elements.detection_method = "heuristic"
        
        logger.info(f"Detection complete: method={elements.detection_method}, "
                   f"input_box={bool(elements.input_box)}, input_hwnd={elements.input_hwnd}, "
                   f"confidence={elements.detection_confidence:.2f}")
        
        self.dialog_elements = elements
        return elements
    
    async def send_prompt_optimized(self, prompt: str) -> bool:
        """Optimized prompt sending using the best available method"""
        logger.info(f"Sending prompt using optimized method: {prompt[:50]}...")
        
        if not self.dialog_elements:
            hwnd = await self.find_cursor_window()
            if not hwnd:
                return False
            await self.detect_dialog_elements_optimized(hwnd)
        
        # Method 1: Direct Win32 to detected edit control (fastest and most reliable)
        if self.dialog_elements.input_hwnd:
            logger.info(f"Using direct Win32 method to HWND {self.dialog_elements.input_hwnd}")
            success = await self._send_via_win32_direct(self.dialog_elements.input_hwnd, prompt)
            if success:
                logger.info("✓ Win32 direct method successful")
                return True
        
        # Method 2: Position-based clicking + Win32 character sending
        if self.dialog_elements.input_box:
            logger.info("Using position-based + Win32 character method")
            success = await self._send_via_position_win32(self.dialog_elements.input_box, prompt)
            if success:
                logger.info("✓ Position + Win32 method successful")
                return True
        
        # Method 3: Fallback to basic Win32 posting
        logger.info("Using Win32 posting fallback method")
        success = await self._send_via_win32_posting(self.dialog_elements.window_hwnd, prompt)
        if success:
            logger.info("✓ Win32 posting fallback successful")
            return True
        
        logger.error("All optimized methods failed")
        return False
    
    async def _send_via_win32_direct(self, edit_hwnd: int, prompt: str) -> bool:
        """Send text directly to edit control using Win32 API"""
        try:
            # Clear existing text
            await self.controller.execute_command('win32_call', {
                'function': 'SendMessage',
                'args': [edit_hwnd, 0x000C, 0, ""]  # WM_SETTEXT
            })
            
            # Set new text
            result = await self.controller.execute_command('win32_call', {
                'function': 'SendMessage',
                'args': [edit_hwnd, 0x000C, 0, prompt]  # WM_SETTEXT
            })
            
            # Verify text was set
            verify_result = await self.controller.execute_command('win32_call', {
                'function': 'GetWindowText',
                'args': [edit_hwnd]
            })
            
            if verify_result:
                logger.debug(f"Text verification successful (length: {len(str(verify_result))})")
                
                # Send Enter key to submit
                await self.controller.execute_command('win32_call', {
                    'function': 'SendMessage',
                    'args': [edit_hwnd, 0x0100, 0x0D, 0]  # WM_KEYDOWN VK_RETURN
                })
                await self.controller.execute_command('win32_call', {
                    'function': 'SendMessage', 
                    'args': [edit_hwnd, 0x0101, 0x0D, 0]  # WM_KEYUP VK_RETURN
                })
                
                return True
            else:
                logger.warning("Text verification failed")
                return False
                
        except Exception as e:
            logger.error(f"Win32 direct method failed: {e}")
            return False
    
    async def _send_via_position_win32(self, input_element: Dict, prompt: str) -> bool:
        """Send text using position-based clicking + Win32 character posting"""
        try:
            center = input_element['center']
            
            # Click to focus
            await self.controller.click(center[0], center[1])
            await asyncio.sleep(0.5)
            
            # Clear existing content using Win32 keys
            await self._send_win32_key_combo([0x11, 0x41])  # Ctrl+A
            await asyncio.sleep(0.1)
            await self._send_win32_key(0x2E)  # Delete
            await asyncio.sleep(0.2)
            
            # Send text character by character
            hwnd = self.dialog_elements.window_hwnd
            for char in prompt:
                char_code = ord(char)
                await self.controller.execute_command('win32_call', {
                    'function': 'PostMessage',
                    'args': [hwnd, 0x0102, char_code, 0]  # WM_CHAR
                })
                await asyncio.sleep(0.005)  # Small delay
            
            # Send Enter
            await self._send_win32_key(0x0D)  # VK_RETURN
            
            return True
            
        except Exception as e:
            logger.error(f"Position + Win32 method failed: {e}")
            return False
    
    async def _send_via_win32_posting(self, hwnd: int, prompt: str) -> bool:
        """Fallback method using Win32 message posting"""
        try:
            # Focus window first
            await self.controller.execute_command('win32_call', {
                'function': 'SetFocus',
                'args': [hwnd]
            })
            
            # Send text (limited length for reliability)
            text_to_send = prompt[:200] if len(prompt) > 200 else prompt
            
            for char in text_to_send:
                char_code = ord(char)
                await self.controller.execute_command('win32_call', {
                    'function': 'PostMessage',
                    'args': [hwnd, 0x0102, char_code, 0]  # WM_CHAR
                })
                await asyncio.sleep(0.01)
            
            # Send Enter
            await self.controller.execute_command('win32_call', {
                'function': 'PostMessage',
                'args': [hwnd, 0x0100, 0x0D, 0]  # WM_KEYDOWN VK_RETURN
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Win32 posting fallback failed: {e}")
            return False
    
    async def _send_win32_key(self, vk_code: int):
        """Send a single key using Win32 keybd_event"""
        await self.controller.execute_command('win32_call', {
            'function': 'keybd_event',
            'args': [vk_code, 0, 0, 0]  # Key down
        })
        await self.controller.execute_command('win32_call', {
            'function': 'keybd_event',
            'args': [vk_code, 0, 2, 0]  # Key up
        })
    
    async def _send_win32_key_combo(self, vk_codes: List[int]):
        """Send key combination using Win32 keybd_event"""
        # Press all keys down
        for vk_code in vk_codes:
            await self.controller.execute_command('win32_call', {
                'function': 'keybd_event',
                'args': [vk_code, 0, 0, 0]  # Key down
            })
        
        # Release all keys up (in reverse order)
        for vk_code in reversed(vk_codes):
            await self.controller.execute_command('win32_call', {
                'function': 'keybd_event',
                'args': [vk_code, 0, 2, 0]  # Key up
            })
    
    def _score_input_element(self, element: Dict) -> float:
        """Score input element based on characteristics"""
        bbox = element['bbox']
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        
        score = 0.0
        
        # Size scoring
        if 300 <= width <= 800:
            score += 0.4
        elif width > 200:
            score += 0.2
        
        if 25 <= height <= 60:
            score += 0.3
        elif height > 15:
            score += 0.1
        
        # Position scoring (prefer bottom area)
        center_y = (bbox[1] + bbox[3]) / 2
        if center_y > 400:  # Assume bottom area
            score += 0.3
        
        return score
    
    def _find_nearest_button(self, input_element: Dict, buttons: List[Dict]) -> Optional[Dict]:
        """Find button nearest to input element"""
        input_center = input_element['center']
        min_distance = float('inf')
        nearest_button = None
        
        for button in buttons:
            button_center = button['center']
            distance = ((button_center[0] - input_center[0]) ** 2 + 
                       (button_center[1] - input_center[1]) ** 2) ** 0.5
            
            if distance < min_distance and distance < 100:  # Within reasonable range
                min_distance = distance
                nearest_button = button
        
        return nearest_button
    
    def _find_closest_edit_control(self, vision_center: Tuple[int, int], edit_controls: List[Dict]) -> Optional[int]:
        """Find Win32 edit control closest to vision-detected position"""
        min_distance = float('inf')
        closest_hwnd = None
        
        for edit_ctrl in edit_controls:
            # We'd need to get position of edit control, for now use first one
            # In real implementation, we'd use GetWindowRect to get positions
            closest_hwnd = edit_ctrl['hwnd']
            break  # Use first edit control for now
        
        return closest_hwnd
    
    def _create_heuristic_elements(self, hwnd: int) -> OptimizedCursorDialogElements:
        """Create heuristic elements as last resort"""
        elements = OptimizedCursorDialogElements(window_hwnd=hwnd)
        
        # Create a fallback input box position (bottom center of window)
        elements.input_box = {
            'type': 'input',
            'bbox': [200, 650, 800, 690],
            'center': [500, 670],
            'confidence': 0.1,
            'source': 'heuristic'
        }
        
        elements.detection_confidence = 0.1
        return elements