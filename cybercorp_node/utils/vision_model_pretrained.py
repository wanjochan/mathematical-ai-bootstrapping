"""Pre-trained YOLO model for UI element detection with high accuracy"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class UIElementPretrained:
    """UI element detected by pre-trained model"""
    element_type: str
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2)
    center: Tuple[int, int]
    confidence: float
    clickable: bool
    text: Optional[str] = None

class UIVisionModelPretrained:
    """Pre-trained YOLO model for UI detection"""
    
    def __init__(self):
        self.model = None
        self._initialize_model()
        
    def _initialize_model(self):
        """Initialize pre-trained UI detection model"""
        try:
            # Try ultralyticsplus first
            try:
                from ultralyticsplus import YOLO as YOLO_PLUS
                use_plus = True
            except ImportError:
                logger.warning("ultralyticsplus not installed, using standard ultralytics")
                from ultralytics import YOLO as YOLO_PLUS
                use_plus = False
            
            if use_plus:
                # Try different pre-trained models
                models_to_try = [
                    'foduucom/web-form-ui-field-detection',  # Web form elements
                    'keremberke/yolov8n-table-extraction',    # Table elements
                    'mshamrai/yolov8x-visdrone',              # General detection
                ]
                
                for model_name in models_to_try:
                    try:
                        logger.info(f"Trying to load model: {model_name}")
                        self.model = YOLO_PLUS(model_name)
                        self.model_name = model_name
                        logger.info(f"Successfully loaded: {model_name}")
                        break
                    except Exception as e:
                        logger.warning(f"Failed to load {model_name}: {e}")
                        continue
            
            if self.model is None:
                # Fallback to base YOLOv8
                logger.warning("Using fallback: enhanced CV detection")
                # We'll use our enhanced CV model directly
                self.model = None
                self.model_name = 'enhanced_cv'
                
        except Exception as e:
            logger.error(f"Model initialization error: {e}")
            self.model = None
            self.model_name = 'enhanced_cv'
    
    def detect_ui_elements(self, image: np.ndarray) -> List[UIElementPretrained]:
        """Detect UI elements using pre-trained model"""
        if image is None or image.size == 0:
            return []
        
        elements = []
        
        # If no model loaded, use fallback directly
        if self.model is None or self.model_name == 'enhanced_cv':
            return self._fallback_cv_detection(image)
        
        try:
            # Run detection
            results = self.model.predict(image)
            
            # Process results
            for result in results:
                if result.boxes is None:
                    continue
                    
                boxes = result.boxes
                for i in range(len(boxes)):
                    x1, y1, x2, y2 = boxes.xyxy[i].tolist()
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                    
                    conf = float(boxes.conf[i])
                    cls = int(boxes.cls[i])
                    
                    # Get class name
                    class_name = result.names.get(cls, 'unknown').lower()
                    
                    # Map to standard UI element type
                    element_type = self._map_class_to_standard_type(class_name)
                    
                    element = UIElementPretrained(
                        element_type=element_type,
                        bbox=(x1, y1, x2, y2),
                        center=((x1 + x2) // 2, (y1 + y2) // 2),
                        confidence=conf,
                        clickable=self._is_clickable(element_type)
                    )
                    elements.append(element)
            
            # If using web-form model, apply additional heuristics
            if 'web-form' in self.model_name:
                elements = self._enhance_web_form_detection(image, elements)
            
        except Exception as e:
            logger.error(f"Error in detection: {e}")
            # Fallback to enhanced CV detection
            elements = self._fallback_cv_detection(image)
        
        return elements
    
    def _map_class_to_standard_type(self, class_name: str) -> str:
        """Map detected class to standard UI element type"""
        # Comprehensive mapping
        mapping = {
            # Form elements
            'button': 'button',
            'btn': 'button',
            'submit': 'button',
            'name': 'input',
            'email': 'input',
            'password': 'input',
            'number': 'input',
            'text': 'input',
            'textbox': 'input',
            'edittext': 'input',
            'input': 'input',
            'radio': 'radio',
            'radio button': 'radio',
            'radio bullet': 'radio',
            'checkbox': 'checkbox',
            'check': 'checkbox',
            'dropdown': 'dropdown',
            'select': 'dropdown',
            'combobox': 'dropdown',
            'spinner': 'dropdown',
            # UI elements
            'icon': 'icon',
            'image': 'image',
            'link': 'link',
            'tab': 'tab',
            'switch': 'switch',
            'toggle': 'switch',
            'slider': 'slider',
            'label': 'label',
            'text': 'label',
        }
        
        return mapping.get(class_name, class_name)
    
    def _is_clickable(self, element_type: str) -> bool:
        """Determine if element is clickable"""
        clickable_types = {
            'button', 'input', 'checkbox', 'radio', 'dropdown',
            'link', 'tab', 'switch', 'slider', 'icon'
        }
        return element_type in clickable_types
    
    def _enhance_web_form_detection(self, image: np.ndarray, elements: List) -> List[UIElementPretrained]:
        """Enhance detection for web form elements"""
        # Add missing UI elements using CV
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Find checkboxes and radio buttons that might be missed
        existing_bboxes = [elem.bbox for elem in elements]
        
        # Detect small square/circular regions
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Skip if overlaps with existing detection
            if self._overlaps_existing(x, y, w, h, existing_bboxes):
                continue
            
            # Small square/circle detection
            if 10 < w < 30 and 10 < h < 30 and 0.7 < w/h < 1.3:
                area = cv2.contourArea(contour)
                perimeter = cv2.arcLength(contour, True)
                if perimeter > 0:
                    circularity = 4 * np.pi * area / (perimeter * perimeter)
                    
                    element_type = 'radio' if circularity > 0.7 else 'checkbox'
                    
                    element = UIElementPretrained(
                        element_type=element_type,
                        bbox=(x, y, x+w, y+h),
                        center=(x+w//2, y+h//2),
                        confidence=0.7,
                        clickable=True
                    )
                    elements.append(element)
        
        return elements
    
    def _overlaps_existing(self, x: int, y: int, w: int, h: int, existing_bboxes: List) -> bool:
        """Check if bbox overlaps with existing detections"""
        for x1, y1, x2, y2 in existing_bboxes:
            # Check overlap
            if not (x + w < x1 or x > x2 or y + h < y1 or y > y2):
                return True
        return False
    
    def _fallback_cv_detection(self, image: np.ndarray) -> List[UIElementPretrained]:
        """Fallback to enhanced CV detection"""
        logger.info("Using fallback CV detection")
        # Import and use our enhanced vision model
        try:
            from cybercorp_node.utils.vision_model_enhanced import UIVisionModelEnhanced
            enhanced_model = UIVisionModelEnhanced()
            enhanced_elements = enhanced_model.detect_ui_elements(image)
            
            # Convert to our format
            elements = []
            for elem in enhanced_elements:
                element = UIElementPretrained(
                    element_type=elem.element_type,
                    bbox=elem.bbox,
                    center=elem.center,
                    confidence=elem.confidence,
                    clickable=elem.clickable,
                    text=elem.text
                )
                elements.append(element)
            
            return elements
        except Exception as e:
            logger.error(f"Fallback CV detection failed: {e}")
            return []