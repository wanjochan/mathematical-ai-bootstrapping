"""YOLO-based vision model for UI element detection"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass 
class UIElementYOLO:
    """UI element detected by YOLO"""
    element_type: str
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2)
    center: Tuple[int, int]
    confidence: float
    clickable: bool
    text: Optional[str] = None

class UIVisionModelYOLO:
    """YOLO-based vision model using pretrained models"""
    
    def __init__(self):
        self.model = None
        self._initialize_model()
        
    def _initialize_model(self):
        """Initialize YOLO model"""
        try:
            from ultralytics import YOLO
            
            # Try to use a UI-specific model if available
            # Otherwise fallback to general object detection
            self.model = YOLO('yolov8n.pt')  # Nano model for speed
            logger.info("Initialized YOLOv8 model")
            
        except ImportError:
            logger.error("Ultralytics not installed. Run: pip install ultralytics")
            raise
    
    def detect_ui_elements(self, image: np.ndarray) -> List[UIElementYOLO]:
        """Detect UI elements using YOLO with custom post-processing"""
        if image is None or image.size == 0:
            return []
        
        # Run YOLO detection with low confidence threshold
        results = self.model(image, conf=0.25, iou=0.45)
        
        # Combine YOLO detections with traditional CV for UI elements
        yolo_elements = self._process_yolo_results(results, image)
        cv_elements = self._detect_ui_specific_elements(image)
        
        # Merge and deduplicate
        all_elements = self._merge_detections(yolo_elements, cv_elements)
        
        return all_elements
    
    def _process_yolo_results(self, results, image: np.ndarray) -> List[UIElementYOLO]:
        """Process YOLO results and map to UI elements"""
        elements = []
        
        for result in results:
            if result.boxes is None:
                continue
                
            boxes = result.boxes
            for i in range(len(boxes)):
                x1, y1, x2, y2 = boxes.xyxy[i].tolist()
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                
                conf = float(boxes.conf[i])
                cls = int(boxes.cls[i])
                
                # Try to map YOLO class to UI element
                element_type = self._infer_ui_type(x1, y1, x2, y2, image)
                
                element = UIElementYOLO(
                    element_type=element_type,
                    bbox=(x1, y1, x2, y2),
                    center=((x1 + x2) // 2, (y1 + y2) // 2),
                    confidence=conf,
                    clickable=self._is_clickable(element_type)
                )
                elements.append(element)
        
        return elements
    
    def _detect_ui_specific_elements(self, image: np.ndarray) -> List[UIElementYOLO]:
        """Detect UI-specific elements using traditional CV"""
        elements = []
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detect buttons
        buttons = self._detect_buttons(image, gray)
        elements.extend(buttons)
        
        # Detect input fields
        inputs = self._detect_input_fields(image, gray)
        elements.extend(inputs)
        
        # Detect checkboxes and radio buttons
        controls = self._detect_small_controls(image, gray)
        elements.extend(controls)
        
        # Detect dropdowns
        dropdowns = self._detect_dropdowns(image, gray)
        elements.extend(dropdowns)
        
        return elements
    
    def _detect_buttons(self, image: np.ndarray, gray: np.ndarray) -> List[UIElementYOLO]:
        """Detect button-like elements"""
        buttons = []
        
        # Find rectangular regions with specific characteristics
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = w * h
            
            # Button criteria
            if (1000 < area < 10000 and 
                1.5 < w/h < 6 and 
                20 < h < 60):
                
                # Check if it looks like a button (color analysis)
                roi = image[y:y+h, x:x+w]
                if self._is_button_like(roi):
                    element = UIElementYOLO(
                        element_type='button',
                        bbox=(x, y, x+w, y+h),
                        center=(x+w//2, y+h//2),
                        confidence=0.8,
                        clickable=True
                    )
                    buttons.append(element)
        
        return buttons
    
    def _detect_input_fields(self, image: np.ndarray, gray: np.ndarray) -> List[UIElementYOLO]:
        """Detect input field elements"""
        inputs = []
        
        # Look for wide, rectangular regions with light background
        edges = cv2.Canny(gray, 30, 100)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Input field criteria
            if (w > 150 and 20 < h < 40 and w/h > 4):
                roi = image[y:y+h, x:x+w]
                mean_color = cv2.mean(roi)[:3]
                
                # Check if it has light background (likely input field)
                if all(c > 200 for c in mean_color):
                    element = UIElementYOLO(
                        element_type='input',
                        bbox=(x, y, x+w, y+h),
                        center=(x+w//2, y+h//2),
                        confidence=0.7,
                        clickable=True
                    )
                    inputs.append(element)
        
        return inputs
    
    def _detect_small_controls(self, image: np.ndarray, gray: np.ndarray) -> List[UIElementYOLO]:
        """Detect checkboxes and radio buttons"""
        controls = []
        
        # Find small square/circular regions
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = cv2.contourArea(contour)
            
            # Small control criteria
            if (100 < area < 500 and 0.7 < w/h < 1.3 and w < 25):
                # Check circularity for radio vs checkbox
                perimeter = cv2.arcLength(contour, True)
                if perimeter > 0:
                    circularity = 4 * np.pi * area / (perimeter * perimeter)
                    
                    element_type = 'radio' if circularity > 0.7 else 'checkbox'
                    
                    element = UIElementYOLO(
                        element_type=element_type,
                        bbox=(x, y, x+w, y+h),
                        center=(x+w//2, y+h//2),
                        confidence=0.7,
                        clickable=True
                    )
                    controls.append(element)
        
        return controls
    
    def _detect_dropdowns(self, image: np.ndarray, gray: np.ndarray) -> List[UIElementYOLO]:
        """Detect dropdown elements"""
        dropdowns = []
        
        # Look for regions with dropdown arrow pattern
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Dropdown criteria
            if (100 < w < 300 and 20 < h < 40 and 3 < w/h < 8):
                # Check for arrow in right portion
                roi = gray[y:y+h, x+int(w*0.8):x+w]
                if roi.size > 0 and self._has_dropdown_arrow(roi):
                    element = UIElementYOLO(
                        element_type='dropdown',
                        bbox=(x, y, x+w, y+h),
                        center=(x+w//2, y+h//2),
                        confidence=0.7,
                        clickable=True
                    )
                    dropdowns.append(element)
        
        return dropdowns
    
    def _is_button_like(self, roi: np.ndarray) -> bool:
        """Check if region looks like a button"""
        if roi.size == 0:
            return False
            
        # Check color uniformity and contrast
        mean = cv2.mean(roi)[:3]
        std = cv2.meanStdDev(roi)[1][:3]
        
        # Buttons typically have uniform color
        return all(s < 50 for s in std)
    
    def _has_dropdown_arrow(self, roi: np.ndarray) -> bool:
        """Check if region contains dropdown arrow"""
        if roi.size == 0:
            return False
            
        # Simple arrow detection
        edges = cv2.Canny(roi, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 10, minLineLength=5, maxLineGap=3)
        
        return lines is not None and len(lines) >= 2
    
    def _infer_ui_type(self, x1: int, y1: int, x2: int, y2: int, image: np.ndarray) -> str:
        """Infer UI element type based on position and appearance"""
        width = x2 - x1
        height = y2 - y1
        aspect_ratio = width / height
        area = width * height
        
        # Position-based inference
        img_height, img_width = image.shape[:2]
        
        # Close button (top-right)
        if x1 > img_width * 0.9 and y1 < img_height * 0.1 and area < 1000:
            return 'button'
        
        # Bottom buttons
        if y1 > img_height * 0.8 and 1000 < area < 5000:
            return 'button'
        
        # Input fields (wide and short)
        if aspect_ratio > 4 and height < 40:
            return 'input'
        
        # Small square elements
        if area < 500 and 0.7 < aspect_ratio < 1.3:
            return 'checkbox'
        
        return 'unknown'
    
    def _is_clickable(self, element_type: str) -> bool:
        """Determine if element is clickable"""
        clickable_types = {'button', 'input', 'checkbox', 'radio', 'dropdown', 'link'}
        return element_type in clickable_types
    
    def _merge_detections(self, yolo_elements: List, cv_elements: List) -> List[UIElementYOLO]:
        """Merge and deduplicate detections from different sources"""
        all_elements = yolo_elements + cv_elements
        
        # Remove duplicates based on IoU
        filtered = []
        for i, elem1 in enumerate(all_elements):
            is_duplicate = False
            for j, elem2 in enumerate(filtered):
                if self._calculate_iou(elem1.bbox, elem2.bbox) > 0.5:
                    # Keep the one with higher confidence
                    if elem1.confidence > elem2.confidence:
                        filtered[j] = elem1
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                filtered.append(elem1)
        
        return filtered
    
    def _calculate_iou(self, box1: Tuple, box2: Tuple) -> float:
        """Calculate Intersection over Union"""
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])
        
        if x2 < x1 or y2 < y1:
            return 0.0
        
        intersection = (x2 - x1) * (y2 - y1)
        area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
        area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0