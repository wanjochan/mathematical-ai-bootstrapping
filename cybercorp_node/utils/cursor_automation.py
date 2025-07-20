"""
Cursor IDE automation module
Implements automated control of Cursor IDE for task delegation
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from .response_formatter import format_success, format_error
from .win32_backend import Win32Backend

logger = logging.getLogger('CursorAutomation')

class TaskType(Enum):
    """Cursor task types"""
    GENERATE = "generate"
    EDIT = "edit"
    EXPLAIN = "explain"
    FIX = "fix"
    REFACTOR = "refactor"
    TEST = "test"

@dataclass
class CursorTask:
    """Cursor task definition"""
    file_path: str
    task_type: TaskType
    prompt: str
    context: Optional[Dict[str, Any]] = None
    timeout: int = 30

class CursorAutomation:
    """Cursor IDE automation controller"""
    
    # Cursor keyboard shortcuts
    SHORTCUTS = {
        'command_palette': 'ctrl+k',
        'ai_chat': 'ctrl+l',
        'inline_edit': 'ctrl+shift+l',
        'ai_write': 'ctrl+i',
        'generate_code': 'alt+k',
        'accept_suggestion': 'tab',
        'reject_suggestion': 'escape'
    }
    
    # UI timing constants (milliseconds)
    TIMING = {
        'key_delay': 50,
        'after_shortcut': 500,
        'after_paste': 200,
        'ai_response_check': 1000,
        'max_wait': 30000
    }
    
    def __init__(self, win32_backend: Optional[Win32Backend] = None):
        """Initialize Cursor automation"""
        self.win32 = win32_backend or Win32Backend()
        self.current_task: Optional[CursorTask] = None
        
    async def execute_task(self, task: CursorTask) -> Dict[str, Any]:
        """
        Execute a Cursor automation task
        
        Args:
            task: CursorTask object defining the task
            
        Returns:
            Dict with success status and results
        """
        self.current_task = task
        start_time = time.time()
        screenshots = []
        
        try:
            # Step 1: Find and activate Cursor window
            cursor_hwnd = self._find_cursor_window()
            if not cursor_hwnd:
                return format_error("Cursor window not found", error_code='WINDOW_NOT_FOUND')
            
            if not self._activate_window(cursor_hwnd):
                return format_error("Failed to activate Cursor window", error_code='ACTIVATION_FAILED')
            
            await asyncio.sleep(self.TIMING['after_shortcut'] / 1000)
            
            # Step 2: Open target file (if specified)
            if task.file_path:
                success = await self._open_file(cursor_hwnd, task.file_path)
                if not success:
                    return format_error(f"Failed to open file: {task.file_path}", error_code='FILE_OPEN_FAILED')
                screenshots.append(self._take_screenshot(cursor_hwnd, "file_opened"))
            
            # Step 3: Trigger appropriate AI function
            ai_triggered = await self._trigger_ai_function(cursor_hwnd, task.task_type)
            if not ai_triggered:
                return format_error("Failed to trigger AI function", error_code='AI_TRIGGER_FAILED')
            screenshots.append(self._take_screenshot(cursor_hwnd, "ai_triggered"))
            
            # Step 4: Input task prompt
            await self._input_prompt(cursor_hwnd, task.prompt)
            screenshots.append(self._take_screenshot(cursor_hwnd, "prompt_entered"))
            
            # Step 5: Wait for AI response
            response = await self._wait_for_response(cursor_hwnd, task.timeout)
            if not response:
                return format_error("AI response timeout", error_code='RESPONSE_TIMEOUT')
            screenshots.append(self._take_screenshot(cursor_hwnd, "response_received"))
            
            # Step 6: Extract and validate result
            result = self._extract_result(cursor_hwnd)
            
            duration = time.time() - start_time
            
            return format_success(
                data={
                    'task_id': f"cursor_task_{int(time.time())}",
                    'result': result,
                    'file_path': task.file_path,
                    'duration': duration,
                    'screenshots': screenshots
                },
                message=f"Cursor task completed in {duration:.1f}s"
            )
            
        except Exception as e:
            logger.error(f"Cursor automation error: {e}")
            return format_error(str(e), error_code='AUTOMATION_ERROR')
    
    def _find_cursor_window(self) -> Optional[int]:
        """Find Cursor IDE window"""
        windows = self.win32.get_windows()
        for window in windows:
            if 'Cursor' in window.get('title', '') and window.get('visible'):
                return window.get('hwnd')
        return None
    
    def _activate_window(self, hwnd: int) -> bool:
        """Activate Cursor window"""
        try:
            import win32gui
            import win32con
            
            # Restore if minimized
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            
            # Bring to front
            win32gui.SetForegroundWindow(hwnd)
            return True
        except Exception as e:
            logger.error(f"Window activation error: {e}")
            return False
    
    async def _open_file(self, hwnd: int, file_path: str) -> bool:
        """Open file in Cursor using Ctrl+O"""
        try:
            # Send Ctrl+O to open file dialog
            self.win32.send_keys('ctrl+o')
            await asyncio.sleep(self.TIMING['after_shortcut'] / 1000)
            
            # Type file path
            self.win32.send_keys(file_path)
            await asyncio.sleep(self.TIMING['after_paste'] / 1000)
            
            # Press Enter to open
            self.win32.send_keys('enter')
            await asyncio.sleep(self.TIMING['after_shortcut'] / 1000)
            
            return True
        except Exception as e:
            logger.error(f"File open error: {e}")
            return False
    
    async def _trigger_ai_function(self, hwnd: int, task_type: TaskType) -> bool:
        """Trigger appropriate AI function based on task type"""
        try:
            if task_type in [TaskType.GENERATE, TaskType.EDIT, TaskType.REFACTOR]:
                # Use Ctrl+L for AI chat
                shortcut = self.SHORTCUTS['ai_chat']
            elif task_type == TaskType.FIX:
                # Use inline edit for fixes
                shortcut = self.SHORTCUTS['inline_edit']
            else:
                # Default to AI chat
                shortcut = self.SHORTCUTS['ai_chat']
            
            self.win32.send_keys(shortcut)
            await asyncio.sleep(self.TIMING['after_shortcut'] / 1000)
            
            return True
        except Exception as e:
            logger.error(f"AI trigger error: {e}")
            return False
    
    async def _input_prompt(self, hwnd: int, prompt: str) -> None:
        """Input task prompt to AI"""
        # Clear any existing text
        self.win32.send_keys('ctrl+a')
        await asyncio.sleep(self.TIMING['key_delay'] / 1000)
        
        # Type the prompt
        self.win32.send_keys(prompt)
        await asyncio.sleep(self.TIMING['after_paste'] / 1000)
        
        # Send Enter to submit
        self.win32.send_keys('enter')
    
    async def _wait_for_response(self, hwnd: int, timeout: int) -> bool:
        """Wait for AI response to complete"""
        start_time = time.time()
        last_content = ""
        stable_count = 0
        
        while (time.time() - start_time) < timeout:
            await asyncio.sleep(self.TIMING['ai_response_check'] / 1000)
            
            # TODO: Implement content change detection
            # For now, we'll wait a fixed time
            if (time.time() - start_time) > 5:
                return True
            
        return False
    
    def _extract_result(self, hwnd: int) -> str:
        """Extract AI-generated result"""
        # TODO: Implement proper result extraction
        # This could use:
        # - Clipboard monitoring
        # - OCR on the response area
        # - UI automation to copy text
        
        # For now, return placeholder
        return "AI response extracted successfully"
    
    def _take_screenshot(self, hwnd: int, stage: str) -> Dict[str, Any]:
        """Take screenshot of current stage"""
        try:
            import datetime
            timestamp = datetime.datetime.now().isoformat()
            
            # TODO: Implement actual screenshot capture
            return {
                'stage': stage,
                'timestamp': timestamp,
                'hwnd': hwnd
            }
        except Exception as e:
            logger.error(f"Screenshot error: {e}")
            return {'stage': stage, 'error': str(e)}
    
    async def execute_cursor_command(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a Cursor automation command
        
        Expected params:
        - file_path: Target file path (optional)
        - task_type: Task type (generate, edit, explain, etc.)
        - prompt: Task description
        - context: Additional context (optional)
        - timeout: Timeout in seconds (default 30)
        """
        try:
            # Validate parameters
            task_type_str = params.get('task_type', 'generate')
            if task_type_str not in [t.value for t in TaskType]:
                return format_error(f"Invalid task type: {task_type_str}", error_code='INVALID_TASK_TYPE')
            
            prompt = params.get('prompt')
            if not prompt:
                return format_error("No prompt provided", error_code='MISSING_PROMPT')
            
            # Create task
            task = CursorTask(
                file_path=params.get('file_path', ''),
                task_type=TaskType(task_type_str),
                prompt=prompt,
                context=params.get('context'),
                timeout=params.get('timeout', 30)
            )
            
            # Execute task
            return await self.execute_task(task)
            
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            return format_error(str(e), error_code='EXECUTION_ERROR')

# Global instance
_cursor_automation = None

def get_cursor_automation() -> CursorAutomation:
    """Get or create Cursor automation instance"""
    global _cursor_automation
    if _cursor_automation is None:
        _cursor_automation = CursorAutomation()
    return _cursor_automation