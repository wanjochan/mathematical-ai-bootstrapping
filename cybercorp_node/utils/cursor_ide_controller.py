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


class CursorIDEController:
    """Controller for Cursor IDE AI assistant interactions"""
    
    def __init__(self, controller: RemoteController):
        self.controller = controller
        self.vision_analyzer = VisionWindowAnalyzer(controller)
        self.cursor_window = None
        self.dialog_elements = None
        
    async def find_cursor_window(self) -> Optional[int]:
        """Find Cursor IDE window"""
        logger.info("Searching for Cursor IDE window...")
        
        windows = await self.controller.get_windows()
        
        # Look for Cursor IDE window
        cursor_candidates = []
        for window in windows:
            title = window.get('title', '').lower()
            if ('cursor' in title and 
                ('code' in title or 'ide' in title or '.py' in title or '.js' in title)):
                cursor_candidates.append(window)
                logger.info(f"Found Cursor candidate: {window['title']}")
        
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
        return self.cursor_window['hwnd']
    
    async def detect_dialog_elements(self, hwnd: int = None) -> CursorDialogElements:
        """Detect UI elements in Cursor IDE dialog"""
        if hwnd is None:
            hwnd = await self.find_cursor_window()
            if not hwnd:
                return CursorDialogElements()
        
        logger.info("Analyzing Cursor IDE dialog elements...")
        
        # Analyze window with vision system
        result = await self.vision_analyzer.analyze_window(hwnd, save_visualization=True)
        if not result:
            logger.error("Failed to analyze Cursor window")
            return CursorDialogElements()
        
        elements = CursorDialogElements(window_hwnd=hwnd)
        
        # Find different types of elements
        for element in result.elements:
            elem_type = element['type']
            center = element['center']
            bbox = element['bbox']
            
            # Identify input box (typically wide and in the bottom area)
            if elem_type == 'input':
                width = bbox[2] - bbox[0]
                height = bbox[3] - bbox[1]
                y_position = center[1]
                
                # Large input box likely to be the main chat input
                if width > 200 and height > 20:
                    if not elements.input_box or y_position > elements.input_box['center'][1]:
                        elements.input_box = element
                        logger.info(f"Found input box at {center}")
            
            # Identify send button (usually near input box)
            elif elem_type == 'button':
                if elements.input_box:
                    input_center = elements.input_box['center']
                    # Button should be close to input box
                    distance = abs(center[1] - input_center[1])
                    if distance < 50:  # Within 50 pixels vertically
                        elements.send_button = element
                        logger.info(f"Found send button at {center}")
                else:
                    # If no input box yet, keep any button as potential send button
                    elements.send_button = element
        
        # Find response area (large text region above input)
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
                   f"button={bool(elements.send_button)}, response={bool(elements.response_area)}")
        
        return elements
    
    async def send_prompt(self, prompt: str, timeout: int = 30) -> bool:
        """Send a prompt to Cursor IDE AI assistant
        
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
        
        try:
            # Click on input box to focus
            input_center = self.dialog_elements.input_box['center']
            await self.controller.click(input_center[0], input_center[1])
            await asyncio.sleep(0.5)  # Wait for focus
            
            # Clear existing text (Ctrl+A, Delete)
            await self.controller.send_keys("^a")
            await asyncio.sleep(0.2)
            await self.controller.send_keys("{DELETE}")
            await asyncio.sleep(0.2)
            
            # Type the prompt
            await self.controller.send_keys(prompt)
            await asyncio.sleep(0.5)
            
            # Click send button if available
            if self.dialog_elements.send_button:
                send_center = self.dialog_elements.send_button['center']
                await self.controller.click(send_center[0], send_center[1])
                logger.info("Send button clicked")
            else:
                # Try Enter key as fallback
                await self.controller.send_keys("{ENTER}")
                logger.info("Enter key sent as fallback")
            
            logger.info("Prompt sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send prompt: {e}")
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