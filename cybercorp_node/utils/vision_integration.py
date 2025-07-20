"""Vision integration module for window content analysis"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
import numpy as np
import cv2
from datetime import datetime
from pathlib import Path

from .vision_model import UIVisionModel, UIElement
from .window_cache import WindowCache
from .remote_control import RemoteController

logger = logging.getLogger(__name__)


@dataclass
class WindowAnalysisResult:
    """Structured data for window analysis results"""
    window_title: str
    window_hwnd: int
    timestamp: float
    elements: List[Dict[str, Any]]
    layout_structure: Dict[str, Any]
    content_summary: Dict[str, Any]
    interaction_points: List[Dict[str, Any]]
    

class VisionWindowAnalyzer:
    """Analyze window content using vision model"""
    
    def __init__(self, controller: RemoteController = None):
        self.controller = controller
        self.vision_model = UIVisionModel(use_yolo=False)  # Start with lightweight mode
        self.analysis_cache = {}  # Cache analysis results
        self.cache_ttl = 60  # Cache time-to-live in seconds
        
    async def analyze_window(self, hwnd: int, save_visualization: bool = False) -> WindowAnalysisResult:
        """Analyze window content and return structured data
        
        Args:
            hwnd: Window handle
            save_visualization: Whether to save visualization image
            
        Returns:
            WindowAnalysisResult with structured data
        """
        logger.info(f"Starting window analysis for hwnd: {hwnd}")
        
        # Check cache first
        cache_key = f"{hwnd}_{int(time.time() / self.cache_ttl)}"
        if cache_key in self.analysis_cache:
            logger.info("Returning cached analysis result")
            return self.analysis_cache[cache_key]
        
        # Take screenshot directly to memory
        image = await self._capture_window_to_memory(hwnd)
        if image is None:
            logger.error(f"Failed to capture window {hwnd}")
            return None
            
        # Run vision analysis
        ui_structure = self.vision_model.extract_ui_structure(image, include_ocr=False)
        
        # Build analysis result
        result = self._build_analysis_result(hwnd, ui_structure, image)
        
        # Save visualization if requested
        if save_visualization:
            vis_path = self._save_visualization(image, ui_structure['elements'], hwnd)
            logger.info(f"Saved visualization: {vis_path}")
            
        # Cache result
        self.analysis_cache[cache_key] = result
        
        # Clean up old cache entries
        self._cleanup_cache()
        
        return result
        
    async def analyze_active_window(self) -> Optional[WindowAnalysisResult]:
        """Analyze the currently active window"""
        if not self.controller:
            logger.error("No controller set for active window analysis")
            return None
            
        # Get active window
        windows = await self.controller.get_windows()
        active_window = None
        
        for window in windows:
            if window.get('is_active'):
                active_window = window
                break
                
        if not active_window:
            logger.warning("No active window found")
            return None
            
        return await self.analyze_window(active_window['hwnd'])
        
    async def find_clickable_elements(self, hwnd: int) -> List[Dict[str, Any]]:
        """Find all clickable elements in a window
        
        Returns:
            List of clickable elements with coordinates
        """
        result = await self.analyze_window(hwnd)
        if not result:
            return []
            
        clickable = []
        for element in result.elements:
            if element['type'] in ['button', 'input', 'menu_item']:
                clickable.append({
                    'type': element['type'],
                    'center': element['center'],
                    'bbox': element['bbox'],
                    'confidence': element['confidence']
                })
                
        return clickable
        
    async def find_text_regions(self, hwnd: int) -> List[Dict[str, Any]]:
        """Find all text regions in a window
        
        Returns:
            List of text regions with coordinates
        """
        result = await self.analyze_window(hwnd)
        if not result:
            return []
            
        text_regions = []
        for element in result.elements:
            if element['type'] in ['text', 'input']:
                text_regions.append({
                    'type': element['type'],
                    'bbox': element['bbox'],
                    'center': element['center']
                })
                
        return text_regions
        
    async def get_window_layout(self, hwnd: int) -> Dict[str, Any]:
        """Get structured layout information for a window
        
        Returns:
            Dictionary with layout structure
        """
        result = await self.analyze_window(hwnd)
        if not result:
            return {}
            
        return result.layout_structure
        
    async def _capture_window_to_memory(self, hwnd: int) -> Optional[np.ndarray]:
        """Capture window screenshot directly to memory (no file saving)"""
        if not self.controller:
            logger.error("No controller set for screenshot")
            return None
        
        try:
            # Try to get screenshot as numpy array directly if controller supports it
            if hasattr(self.controller, 'screenshot_to_memory'):
                return await self.controller.screenshot_to_memory(hwnd)
            
            # Fallback: capture to temp file and load to memory
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                temp_filename = tmp_file.name
            
            screenshot_path = await self.controller.screenshot(hwnd, temp_filename)
            if screenshot_path and os.path.exists(temp_filename):
                image = cv2.imread(temp_filename)
                os.unlink(temp_filename)  # Clean up temp file
                return image
            else:
                if os.path.exists(temp_filename):
                    os.unlink(temp_filename)
                return None
                
        except Exception as e:
            logger.error(f"Failed to capture window {hwnd} to memory: {e}")
            return None
    
    async def _capture_window(self, hwnd: int) -> Optional[str]:
        """Capture window screenshot (legacy method - saves file)"""
        if not self.controller:
            logger.error("No controller set for screenshot")
            return None
            
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"vision_capture_{hwnd}_{timestamp}.png"
        
        return await self.controller.screenshot(hwnd, filename)
        
    def _build_analysis_result(self, hwnd: int, ui_structure: Dict[str, Any], 
                              image: np.ndarray) -> WindowAnalysisResult:
        """Build structured analysis result"""
        # Get window info
        window_title = "Unknown"
        if self.controller and hasattr(self.controller, 'window_cache'):
            window_info = self.controller.window_cache.get_window_by_hwnd(hwnd)
            if window_info:
                window_title = window_info.get('title', 'Unknown')
                
        # Extract interaction points
        interaction_points = []
        for element in ui_structure['elements']:
            if element['type'] in ['button', 'input', 'menu_item']:
                interaction_points.append({
                    'type': element['type'],
                    'location': element['center'],
                    'bbox': element['bbox'],
                    'priority': 'high' if element['type'] == 'button' else 'medium'
                })
                
        # Build content summary
        content_summary = {
            'total_elements': len(ui_structure['elements']),
            'element_types': self._count_element_types(ui_structure['elements']),
            'has_text_input': any(e['type'] == 'input' for e in ui_structure['elements']),
            'has_buttons': any(e['type'] == 'button' for e in ui_structure['elements']),
            'layout_type': self._detect_layout_type(ui_structure)
        }
        
        # Build layout structure
        layout_structure = {
            'hierarchy': ui_structure.get('hierarchy', []),
            'regions': self._detect_regions(ui_structure['elements'], image.shape),
            'dominant_orientation': self._detect_orientation(ui_structure['elements'])
        }
        
        return WindowAnalysisResult(
            window_title=window_title,
            window_hwnd=hwnd,
            timestamp=time.time(),
            elements=ui_structure['elements'],
            layout_structure=layout_structure,
            content_summary=content_summary,
            interaction_points=interaction_points
        )
        
    def _count_element_types(self, elements: List[Dict]) -> Dict[str, int]:
        """Count elements by type"""
        counts = {}
        for elem in elements:
            elem_type = elem['type']
            counts[elem_type] = counts.get(elem_type, 0) + 1
        return counts
        
    def _detect_layout_type(self, ui_structure: Dict) -> str:
        """Detect the general layout type"""
        elements = ui_structure['elements']
        if not elements:
            return 'empty'
            
        # Simple heuristics for layout detection
        button_count = sum(1 for e in elements if e['type'] == 'button')
        input_count = sum(1 for e in elements if e['type'] == 'input')
        panel_count = sum(1 for e in elements if e['type'] == 'panel')
        
        if input_count > 3 and button_count >= 1:
            return 'form'
        elif button_count > 5:
            return 'toolbar'
        elif panel_count > 3:
            return 'dashboard'
        else:
            return 'general'
            
    def _detect_regions(self, elements: List[Dict], image_shape: Tuple) -> List[Dict]:
        """Detect UI regions (header, sidebar, content, etc.)"""
        height, width = image_shape[:2]
        regions = []
        
        # Simple region detection based on element positions
        top_elements = [e for e in elements if e['center'][1] < height * 0.2]
        left_elements = [e for e in elements if e['center'][0] < width * 0.2]
        bottom_elements = [e for e in elements if e['center'][1] > height * 0.8]
        
        if top_elements:
            regions.append({
                'type': 'header',
                'element_count': len(top_elements),
                'bounds': (0, 0, width, int(height * 0.2))
            })
            
        if left_elements:
            regions.append({
                'type': 'sidebar',
                'element_count': len(left_elements),
                'bounds': (0, 0, int(width * 0.2), height)
            })
            
        if bottom_elements:
            regions.append({
                'type': 'footer',
                'element_count': len(bottom_elements),
                'bounds': (0, int(height * 0.8), width, height)
            })
            
        return regions
        
    def _detect_orientation(self, elements: List[Dict]) -> str:
        """Detect dominant orientation of UI elements"""
        if not elements:
            return 'unknown'
            
        # Calculate average aspect ratio
        aspect_ratios = []
        for elem in elements:
            bbox = elem['bbox']
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
            if height > 0:
                aspect_ratios.append(width / height)
                
        if not aspect_ratios:
            return 'unknown'
            
        avg_ratio = sum(aspect_ratios) / len(aspect_ratios)
        
        if avg_ratio > 2.0:
            return 'horizontal'
        elif avg_ratio < 0.5:
            return 'vertical'
        else:
            return 'mixed'
            
    def _save_visualization(self, image: np.ndarray, elements: List[Dict], 
                           hwnd: int) -> str:
        """Save visualization of detected elements"""
        # Convert elements to UIElement objects for visualization
        ui_elements = []
        for elem in elements:
            ui_elem = UIElement(
                element_type=elem['type'],
                bbox=tuple(elem['bbox']),
                confidence=elem['confidence']
            )
            ui_elements.append(ui_elem)
            
        # Create visualization
        vis_image = self.vision_model.visualize_detection(image, ui_elements)
        
        # Save image
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"vision_analysis_{hwnd}_{timestamp}.png"
        cv2.imwrite(filename, vis_image)
        
        return filename
        
    def _cleanup_cache(self):
        """Remove old cache entries"""
        current_time = time.time()
        keys_to_remove = []
        
        for key in self.analysis_cache:
            # Extract timestamp from cache key
            try:
                hwnd, timestamp = key.split('_')
                if current_time - float(timestamp) * self.cache_ttl > self.cache_ttl * 2:
                    keys_to_remove.append(key)
            except:
                keys_to_remove.append(key)
                
        for key in keys_to_remove:
            self.analysis_cache.pop(key, None)
            
    def export_analysis(self, result: WindowAnalysisResult, format: str = 'json') -> str:
        """Export analysis result in specified format
        
        Args:
            result: Analysis result
            format: Export format ('json', 'yaml', 'summary')
            
        Returns:
            Formatted string
        """
        if format == 'json':
            return json.dumps(asdict(result), indent=2)
        elif format == 'summary':
            return self._format_summary(result)
        else:
            return str(result)
            
    def _format_summary(self, result: WindowAnalysisResult) -> str:
        """Format analysis result as human-readable summary"""
        summary = f"""
Window Analysis Summary
======================
Title: {result.window_title}
HWND: {result.window_hwnd}
Time: {datetime.fromtimestamp(result.timestamp).strftime('%Y-%m-%d %H:%M:%S')}

Content Summary:
- Total Elements: {result.content_summary['total_elements']}
- Element Types: {', '.join(f"{k}: {v}" for k, v in result.content_summary['element_types'].items())}
- Layout Type: {result.content_summary['layout_type']}
- Has Text Input: {result.content_summary['has_text_input']}
- Has Buttons: {result.content_summary['has_buttons']}

Interaction Points: {len(result.interaction_points)}
"""
        
        for i, point in enumerate(result.interaction_points[:5]):  # Show first 5
            summary += f"  {i+1}. {point['type']} at ({point['location'][0]}, {point['location'][1]})\n"
            
        if len(result.interaction_points) > 5:
            summary += f"  ... and {len(result.interaction_points) - 5} more\n"
            
        return summary


# Convenience functions
async def analyze_window_quick(hwnd: int, controller: RemoteController) -> Dict[str, Any]:
    """Quick window analysis function"""
    analyzer = VisionWindowAnalyzer(controller)
    result = await analyzer.analyze_window(hwnd)
    return asdict(result) if result else None


async def find_ui_element(hwnd: int, element_type: str, controller: RemoteController) -> Optional[Dict[str, Any]]:
    """Find specific UI element in window"""
    analyzer = VisionWindowAnalyzer(controller)
    elements = await analyzer.find_clickable_elements(hwnd)
    
    for elem in elements:
        if elem['type'] == element_type:
            return elem
            
    return None