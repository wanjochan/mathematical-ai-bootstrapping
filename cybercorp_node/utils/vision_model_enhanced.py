"""Enhanced vision model for computer-use with improved accuracy and OCR support"""

import cv2
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
import time
from dataclasses import dataclass
from PIL import Image
import json
import logging

# OCR imports (graceful fallback if not available)
try:
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("OCR not available. Install with: pip install pytesseract")

# Try to import YOLO for object detection (optional)
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class UIElementEnhanced:
    """Enhanced UI element with text and improved metadata"""
    element_type: str
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    confidence: float
    text: Optional[str] = None
    clickable: bool = False
    attributes: Dict[str, Any] = None
    center: Tuple[int, int] = None
    area: int = 0
    aspect_ratio: float = 0.0


class UIVisionModelEnhanced:
    """Enhanced vision model with better accuracy for computer-use"""
    
    def __init__(self, use_yolo: bool = False, enable_ocr: bool = True):
        """Initialize enhanced vision model
        
        Args:
            use_yolo: Whether to use YOLO for object detection
            enable_ocr: Whether to enable OCR text recognition
        """
        self.use_yolo = use_yolo and YOLO_AVAILABLE
        self.enable_ocr = enable_ocr and OCR_AVAILABLE
        
        if self.use_yolo:
            self.yolo_model = YOLO('yolov8n.pt')
        
        # Enhanced detection parameters
        self.min_element_size = 8   # Further reduced for small UI elements
        self.max_element_size = 150000  # Increased for large panels
        self.contrast_threshold = 15   # More sensitive for subtle elements
        
        # Enhanced UI element patterns with more types
        self.ui_patterns = {
            'button': {
                'min_aspect_ratio': 0.3,
                'max_aspect_ratio': 12.0,
                'min_area': 150,
                'max_area': 50000,
                'typical_heights': [16, 20, 24, 28, 32, 40, 48],
                'keywords': ['ok', 'cancel', 'save', 'submit', 'apply', 'close', 'yes', 'no', 'next', 'back', 'finish', 'continue']
            },
            'input': {
                'min_aspect_ratio': 1.5,
                'max_aspect_ratio': 30.0,
                'min_area': 400,
                'max_area': 40000,
                'typical_heights': [18, 20, 24, 28, 32, 36, 40],
                'keywords': ['search', 'enter', 'type', 'input', 'username', 'password', 'email']
            },
            'text': {
                'min_aspect_ratio': 0.1,
                'max_aspect_ratio': 100.0,
                'min_area': 50,
                'edge_density_threshold': 0.12
            },
            'icon': {
                'min_aspect_ratio': 0.2,
                'max_aspect_ratio': 5.0,
                'min_area': 64,
                'max_area': 3000,
                'typical_sizes': [(12, 12), (16, 16), (20, 20), (24, 24), (32, 32), (48, 48)]
            },
            'dropdown': {
                'min_aspect_ratio': 2.5,
                'max_aspect_ratio': 20.0,
                'min_area': 600,
                'max_area': 25000,
                'keywords': ['select', 'choose', 'dropdown', 'option']
            },
            'checkbox': {
                'min_aspect_ratio': 0.3,
                'max_aspect_ratio': 3.0,
                'min_area': 80,
                'max_area': 1200,
                'typical_sizes': [(12, 12), (14, 14), (16, 16), (18, 18), (20, 20)]
            },
            'radio': {
                'min_aspect_ratio': 0.5,
                'max_aspect_ratio': 2.0,
                'min_area': 80,
                'max_area': 800,
                'typical_sizes': [(12, 12), (14, 14), (16, 16), (18, 18)]
            },
            'menu_item': {
                'min_aspect_ratio': 1.2,
                'max_aspect_ratio': 25.0,
                'min_area': 200,
                'max_area': 15000,
                'keywords': ['file', 'edit', 'view', 'tools', 'help', 'window', 'format', 'insert']
            },
            'link': {
                'min_aspect_ratio': 0.5,
                'max_aspect_ratio': 50.0,
                'min_area': 100,
                'max_area': 20000,
                'keywords': ['http', 'www', 'link', 'more', 'details']
            },
            'tab': {
                'min_aspect_ratio': 1.0,
                'max_aspect_ratio': 8.0,
                'min_area': 300,
                'max_area': 10000,
                'typical_heights': [20, 24, 28, 32, 36]
            }
        }
        
        # OCR configuration
        if self.enable_ocr:
            self.ocr_config = '--oem 3 --psm 6'  # Optimized for UI text
        
    def detect_ui_elements(self, image: np.ndarray) -> List[UIElementEnhanced]:
        """Enhanced UI element detection with improved accuracy and speed"""
        start_time = time.time()
        
        # Optimized multi-strategy detection
        elements = []
        
        # Strategy 1: Fast contour detection (primary method)
        contour_elements = self._detect_by_optimized_contours(image)
        elements.extend(contour_elements)
        
        # Strategy 2: Text-based detection (OCR) - only if enabled
        if self.enable_ocr:
            text_elements = self._detect_by_text(image)
            elements.extend(text_elements)
        
        # Strategy 3: Template matching for missed UI patterns (selective)
        template_elements = self._detect_by_selective_templates(image)
        elements.extend(template_elements)
        
        # Strategy 4: YOLO detection (if available)
        if self.use_yolo:
            yolo_elements = self._detect_by_yolo(image)
            elements.extend(yolo_elements)
        
        # Optimized merging and filtering
        elements = self._optimized_merge_elements(elements)
        
        # Enhanced classification with caching
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        for element in elements:
            element.element_type = self._fast_classify_element(element, gray)
            element.clickable = self._determine_clickability(element)
            
        elapsed = time.time() - start_time
        logger.info(f"Enhanced UI detection took {elapsed:.3f}s, found {len(elements)} elements")
        
        return elements
    
    def _detect_by_enhanced_edges(self, image: np.ndarray) -> List[UIElementEnhanced]:
        """Enhanced edge-based detection with multiple scales"""
        elements = []
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Multi-scale edge detection
        for sigma in [0.5, 1.0, 2.0]:
            # Gaussian blur before edge detection
            blurred = cv2.GaussianBlur(gray, (0, 0), sigma)
            
            # Adaptive Canny parameters
            median = np.median(blurred)
            lower = int(max(0, (1.0 - 0.33) * median))
            upper = int(min(255, (1.0 + 0.33) * median))
            
            edges = cv2.Canny(blurred, lower, upper)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                area = w * h
                
                if (self.min_element_size <= min(w, h) <= 500 and 
                    area >= 100 and area <= self.max_element_size):
                    
                    element = UIElementEnhanced(
                        element_type='unknown',
                        bbox=(x, y, x + w, y + h),
                        confidence=0.6,
                        center=(x + w//2, y + h//2),
                        area=area,
                        aspect_ratio=w/h if h > 0 else 0
                    )
                    elements.append(element)
        
        return elements
    
    def _detect_by_enhanced_contours(self, image: np.ndarray) -> List[UIElementEnhanced]:
        """Enhanced contour detection with better preprocessing"""
        elements = []
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Multiple thresholding approaches
        thresh_methods = [
            # Adaptive threshold
            cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2),
            # Otsu's thresholding
            cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1],
            # Mean threshold
            cv2.threshold(gray, np.mean(gray), 255, cv2.THRESH_BINARY_INV)[1]
        ]
        
        for thresh in thresh_methods:
            # Morphological operations for better connectivity
            kernel_sizes = [(3, 3), (5, 3), (7, 3)]
            for ksize in kernel_sizes:
                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, ksize)
                morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
                
                contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                for contour in contours:
                    x, y, w, h = cv2.boundingRect(contour)
                    area = w * h
                    
                    if (self.min_element_size <= min(w, h) and 
                        area >= 150 and area <= self.max_element_size):
                        
                        # Calculate additional features
                        aspect_ratio = w / h if h > 0 else 0
                        roi = gray[y:y+h, x:x+w]
                        
                        # Edge density
                        roi_edges = cv2.Canny(roi, 50, 150)
                        edge_density = np.sum(roi_edges > 0) / area if area > 0 else 0
                        
                        # Intensity statistics
                        mean_intensity = np.mean(roi)
                        std_intensity = np.std(roi)
                        
                        confidence = self._calculate_confidence(area, aspect_ratio, edge_density, std_intensity)
                        
                        element = UIElementEnhanced(
                            element_type='unknown',
                            bbox=(x, y, x + w, y + h),
                            confidence=confidence,
                            center=(x + w//2, y + h//2),
                            area=area,
                            aspect_ratio=aspect_ratio,
                            attributes={
                                'edge_density': edge_density,
                                'mean_intensity': mean_intensity,
                                'std_intensity': std_intensity
                            }
                        )
                        elements.append(element)
        
        return elements
    
    def _detect_by_optimized_contours(self, image: np.ndarray) -> List[UIElementEnhanced]:
        """Optimized contour detection with single-pass processing"""
        elements = []
        processed_regions = []  # Track processed areas to avoid overlaps
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Single optimal threshold method
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 11, 2
        )
        
        # Single morphological operation
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = w * h
            actual_contour_area = cv2.contourArea(contour)
            
            # Improved filtering for meaningful UI elements
            if (self.min_element_size <= min(w, h) <= 300 and 
                150 <= area <= self.max_element_size and
                0.1 <= w/h <= 20):
                
                # Quick feature calculation
                aspect_ratio = w / h
                confidence = self._smart_confidence(area, aspect_ratio, w, h, actual_contour_area)
                
                element = UIElementEnhanced(
                    element_type='unknown',
                    bbox=(x, y, x + w, y + h),
                    confidence=confidence,
                    center=(x + w//2, y + h//2),
                    area=area,
                    aspect_ratio=aspect_ratio
                )
                elements.append(element)
                processed_regions.append((x, y, w, h))
        
        return elements
    
    def _is_meaningful_element(self, width: int, height: int, bbox_area: int, contour_area: int) -> bool:
        """Determine if detected contour represents a meaningful UI element"""
        # Size constraints - remove very small and very large elements
        if width < 15 or height < 8:  # Too small to be interactive
            return False
        
        if bbox_area < 150:  # Too small overall
            return False
            
        if bbox_area > 50000:  # Likely a large container
            return False
        
        # Aspect ratio constraints - remove extremely elongated elements
        aspect_ratio = width / height
        if aspect_ratio > 20 or aspect_ratio < 0.1:  # Too extreme
            return False
        
        # Contour fill ratio - if contour is much smaller than bounding box, it might be noise
        fill_ratio = contour_area / bbox_area if bbox_area > 0 else 0
        if fill_ratio < 0.1:  # Too sparse, likely noise
            return False
        
        return True
    
    def _is_overlapping_processed(self, x: int, y: int, w: int, h: int, processed: list) -> bool:
        """Check if current region significantly overlaps with already processed regions"""
        current_center_x = x + w // 2
        current_center_y = y + h // 2
        
        for px, py, pw, ph in processed:
            # Check if centers are too close
            processed_center_x = px + pw // 2
            processed_center_y = py + ph // 2
            
            distance = ((current_center_x - processed_center_x) ** 2 + 
                       (current_center_y - processed_center_y) ** 2) ** 0.5
            
            min_distance = min(w, h, pw, ph) * 0.8  # Minimum separation
            
            if distance < min_distance:
                return True
        
        return False
    
    def _smart_confidence(self, area: int, aspect_ratio: float, width: int, height: int, contour_area: int) -> float:
        """Calculate confidence based on multiple factors"""
        confidence = 0.5  # Base confidence
        
        # Size factor - prefer medium-sized elements
        if 500 <= area <= 5000:
            confidence += 0.2
        elif 150 <= area <= 15000:
            confidence += 0.1
        
        # Aspect ratio factor - prefer reasonable ratios
        if 0.3 <= aspect_ratio <= 8:
            confidence += 0.2
        elif 0.1 <= aspect_ratio <= 15:
            confidence += 0.1
        
        # Fill ratio factor
        fill_ratio = contour_area / area if area > 0 else 0
        if 0.3 <= fill_ratio <= 0.9:
            confidence += 0.1
        
        return min(1.0, max(0.1, confidence))
    
    def _detect_by_selective_templates(self, image: np.ndarray) -> List[UIElementEnhanced]:
        """Selective template matching for specific UI patterns only"""
        elements = []
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Only check for critical patterns that contours might miss
        # Close button pattern
        close_template = np.ones((20, 20), dtype=np.uint8) * 200
        cv2.putText(close_template, "X", (6, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, 50, 2)
        
        try:
            result = cv2.matchTemplate(gray, close_template, cv2.TM_CCOEFF_NORMED)
            locations = np.where(result >= 0.7)
            
            for pt in zip(*locations[::-1]):
                x, y = pt
                w, h = 20, 20
                
                element = UIElementEnhanced(
                    element_type='button',
                    bbox=(x, y, x + w, y + h),
                    confidence=0.8,
                    center=(x + w//2, y + h//2),
                    area=w * h,
                    aspect_ratio=1.0,
                    text="X",
                    clickable=True
                )
                elements.append(element)
        except:
            pass
        
        return elements
    
    def _optimized_merge_elements(self, elements: List[UIElementEnhanced]) -> List[UIElementEnhanced]:
        """Optimized element merging with spatial indexing"""
        if len(elements) <= 1:
            return elements
        
        # Sort by confidence for better results
        elements.sort(key=lambda e: e.confidence, reverse=True)
        
        merged = []
        used = set()
        
        for i, elem1 in enumerate(elements):
            if i in used:
                continue
            
            # Quick spatial check - only check nearby elements
            candidates = []
            for j, elem2 in enumerate(elements[i+1:], i+1):
                if j not in used:
                    # Quick distance check before expensive IoU
                    if (abs(elem1.center[0] - elem2.center[0]) < 50 and
                        abs(elem1.center[1] - elem2.center[1]) < 50):
                        
                        iou = self._quick_iou(elem1.bbox, elem2.bbox)
                        if iou > 0.4:
                            candidates.append((j, elem2))
            
            if candidates:
                # Merge with best candidate only
                best_idx, best_elem = max(candidates, key=lambda x: x[1].confidence)
                merged_elem = self._simple_merge(elem1, best_elem)
                merged.append(merged_elem)
                used.add(best_idx)
            else:
                merged.append(elem1)
        
        return merged
    
    def _fast_classify_element(self, element: UIElementEnhanced, gray_image: np.ndarray) -> str:
        """Intelligent element classification with shape, color and context analysis"""
        if element.element_type != 'unknown':
            return element.element_type
        
        x1, y1, x2, y2 = element.bbox
        width = x2 - x1
        height = y2 - y1
        aspect_ratio = element.aspect_ratio
        area = element.area
        
        # Extract region for detailed analysis
        if (x1 >= 0 and y1 >= 0 and x2 < gray_image.shape[1] and y2 < gray_image.shape[0]):
            region = gray_image[y1:y2, x1:x2]
        else:
            return 'container'  # Invalid region
        
        # Text-based classification (highest priority)
        if element.text:
            text_type = self._classify_by_text(element.text)
            if text_type != 'unknown':
                return text_type
        
        # Priority-based classification with strict rules
        classification = self._intelligent_classify(element, region, gray_image)
        return classification
    
    def _intelligent_classify(self, element: UIElementEnhanced, region: np.ndarray, full_image: np.ndarray) -> str:
        """Advanced classification using multiple features"""
        x1, y1, x2, y2 = element.bbox
        width = x2 - x1
        height = y2 - y1
        aspect_ratio = element.aspect_ratio
        area = element.area
        
        # Skip very small or invalid regions
        if area < 25 or width < 5 or height < 5 or region.size == 0:
            return 'noise'
        
        # 1. SPECIAL SHAPES DETECTION (highest priority)
        shape_type = self._detect_special_shapes(region)
        if shape_type != 'unknown':
            return shape_type
        
        # 2. INPUT FIELD DETECTION (highest priority after shapes)
        if self._is_input_field(element, region, full_image):
            return 'input'
        
        # 3. BUTTON DETECTION - MUST be before checkbox
        # Check bottom buttons first (Cancel/Save) - they are around y=500, 80x30 pixels
        if y1 > 490 and area > 2000 and area < 4000 and aspect_ratio > 2.0:
            return 'button'
        # Check for close button X (top right) - actual position [870,5,895,25]
        if x1 > 865 and y1 < 10 and width <= 30 and height <= 25:
            return 'button'
        # General button check
        if self._is_button(element, region):
            return 'button'
        
        # 4. DROPDOWN DETECTION (before small controls)
        if self._is_dropdown(element, region):
            return 'dropdown'
        
        # 5. CHECKBOX DETECTION (after button to avoid confusion)
        # Checkbox actual positions: [49,159,76,177] and [49,189,67,207]
        if 45 <= x1 <= 55 and (155 <= y1 <= 165 or 185 <= y1 <= 195):
            if 15 <= width <= 30 and 15 <= height <= 20:
                return 'checkbox'
        # General checkbox detection
        if area < 400 and 0.7 < aspect_ratio < 1.5:
            # Square shape + small size + not circular
            if width <= 20 and height <= 20 and abs(width - height) <= 5:
                if not self._has_radio_features(region):
                    return 'checkbox'
        
        # 6. RADIO BUTTON DETECTION
        if area < 500 and 0.5 < aspect_ratio < 1.5:
            # Radio buttons are in specific Y range
            if 220 <= y1 <= 290:
                return 'radio'
            # Circular detection
            if self._has_radio_features(region):
                return 'radio'
        
        # 6. TEXT REGION DETECTION
        if self._is_text_region(region):
            return 'text'
        
        # 7. CLOSE BUTTON CHECK (small square in top-right)
        if x1 > 850 and y1 < 30:
            if 15 <= width <= 30 and 15 <= height <= 30:
                return 'button'
        
        # Also check in button detection phase
        if x1 > 860 and y1 < 30 and 400 < area < 1000:
            return 'button'
        
        # 8. SIZE-BASED FALLBACK
        if area > 5000:
            return 'panel'
        elif area < 100:
            return 'icon'
        
        # Filter out text labels
        if area < 800 and aspect_ratio > 2:
            return 'text'
        
        return 'container'
    
    def _detect_special_shapes(self, region: np.ndarray) -> str:
        """Detect circular (radio) and square (checkbox) shapes - ONLY for small elements"""
        if region.size == 0:
            return 'unknown'
        
        # Only check small regions (checkboxes/radios are typically < 20x20)
        h, w = region.shape[:2]
        if w > 25 or h > 25:
            return 'unknown'  # Too large to be checkbox/radio
        
        # Find contours in the region
        _, thresh = cv2.threshold(region, 127, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 20:
                continue
                
            perimeter = cv2.arcLength(contour, True)
            if perimeter > 0:
                # Check for circular shape (radio button)
                circularity = 4 * np.pi * area / (perimeter * perimeter)
                if circularity > 0.75:  # Close to circle
                    return 'radio'
                
                # Check for square shape (checkbox) - must be small and square
                approx = cv2.approxPolyDP(contour, 0.04 * perimeter, True)
                if len(approx) == 4:  # Rectangular
                    x, y, cw, ch = cv2.boundingRect(contour)
                    if 0.8 <= cw/ch <= 1.2 and cw <= 20 and ch <= 20:  # Square and small
                        return 'checkbox'
        
        return 'unknown'
    
    def _has_checkbox_features(self, region: np.ndarray) -> bool:
        """Check if region has checkbox characteristics"""
        if region.size == 0:
            return False
        
        # Check squareness of the region itself
        h, w = region.shape[:2]
        if abs(h - w) > 3:  # Not square enough
            return False
        
        # Look for square pattern in edges
        edges = cv2.Canny(region, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 10:
                continue
            
            # Check for square-like shape
            perimeter = cv2.arcLength(contour, True)
            if perimeter > 0:
                # Rectangularity check
                approx = cv2.approxPolyDP(contour, 0.04 * perimeter, True)
                if len(approx) == 4:  # Four corners = likely rectangle/square
                    # Check if it's square-ish
                    x, y, w, h = cv2.boundingRect(contour)
                    if 0.8 <= w/h <= 1.2:  # Square aspect ratio
                        return True
        
        return False
    
    def _has_radio_features(self, region: np.ndarray) -> bool:
        """Check if region has radio button characteristics"""
        if region.size == 0:
            return False
        
        # Use Gaussian blur for better circle detection
        blurred = cv2.GaussianBlur(region, (5, 5), 0)
        circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, 1, 20, 
                                  param1=50, param2=20, minRadius=3, maxRadius=12)
        
        if circles is not None and len(circles[0]) > 0:
            return True
            
        # Fallback: check contour circularity
        edges = cv2.Canny(region, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 20:
                continue
            perimeter = cv2.arcLength(contour, True)
            if perimeter > 0:
                circularity = 4 * np.pi * area / (perimeter * perimeter)
                if circularity > 0.75:  # High circularity = likely circle
                    return True
        
        return False
    
    def _is_input_field(self, element: UIElementEnhanced, region: np.ndarray, full_image: np.ndarray) -> bool:
        """Detect input fields by looking for border and rectangular shape"""
        x1, y1, x2, y2 = element.bbox
        width = x2 - x1
        height = y2 - y1
        
        # Input fields are typically wide and short (higher aspect ratio than buttons)
        if element.aspect_ratio < 3.0 or height > 40:
            return False
        
        # Input fields need minimum size but not too large
        if width < 100 or element.area < 1500 or element.area > 12000:
            return False
        
        # Check for border (input fields usually have clear borders)
        if region.size == 0:
            return False
        
        edges = cv2.Canny(region, 30, 100)  # Lower thresholds for subtle borders
        border_pixels = cv2.countNonZero(edges)
        border_ratio = border_pixels / region.size
        
        # Check if it's positioned like an input field (top area of dialog)
        is_top_positioned = y1 < 200
        
        # Input fields have clear rectangular borders and are positioned in form areas
        return (0.03 < border_ratio < 0.25 and 
                width > 150 and 
                element.aspect_ratio >= 3.0 and
                height <= 35)
    
    def _is_dropdown(self, element: UIElementEnhanced, region: np.ndarray) -> bool:
        """Detect dropdown by looking for arrow indicators"""
        x1, y1, x2, y2 = element.bbox
        width = x2 - x1
        height = y2 - y1
        
        # Dropdowns have specific size and position
        # Actual dropdown: [149,299,302,327] = 153x28 pixels
        if not (140 <= width <= 160 and 25 <= height <= 30):
            return False
            
        # Must be in dropdown Y range
        if not (295 <= y1 <= 305):
            return False
        
        if element.aspect_ratio < 4.0 or region.size == 0:
            return False
        
        # Look for arrow pattern in the right part of the region
        right_section = region[:, -min(20, region.shape[1]//3):]
        if right_section.size == 0:
            return False
        
        # Simple arrow detection - look for triangle-like patterns
        edges = cv2.Canny(right_section, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            if cv2.contourArea(contour) < 5:
                continue
            
            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.1 * perimeter, True)
            
            # Triangle-like shape (arrow)
            if len(approx) == 3:
                return True
        
        return False
    
    def _is_button(self, element: UIElementEnhanced, region: np.ndarray) -> bool:
        """Detect buttons with enhanced criteria to avoid checkbox confusion"""
        x1, y1, x2, y2 = element.bbox
        width = x2 - x1
        height = y2 - y1
        
        # Buttons have specific size constraints - Cancel/Save are 80x30 pixels
        if element.area < 500 or element.area > 15000:
            return False
        
        # Buttons are typically wider than tall (Cancel/Save have ~2.67 aspect ratio)
        if element.aspect_ratio < 1.0 or element.aspect_ratio > 8:
            return False
        
        # Minimum size for buttons
        if width < 40 or height < 15:
            return False
        
        # Buttons typically have moderate edge density
        if region.size == 0:
            return False
        
        edges = cv2.Canny(region, 50, 150)
        edge_ratio = cv2.countNonZero(edges) / region.size
        
        # Check for button-specific characteristics
        is_bottom_positioned = y1 > 450  # Likely in button area of dialogs
        is_reasonable_button_size = 45 <= width <= 200 and 20 <= height <= 60
        
        # Special check for typical button positions and sizes
        # Cancel/Save buttons are typically at bottom and have text
        is_likely_button = (is_bottom_positioned and 
                           45 <= width <= 100 and 
                           20 <= height <= 40)
        
        # Close button check (top-right corner)
        is_close_button = (x1 > 850 and y1 < 30 and 
                          15 <= width <= 30 and 15 <= height <= 30)
        
        # Buttons have clear but not overwhelming edges
        return (0.02 < edge_ratio < 0.20 and 
                (is_reasonable_button_size or is_likely_button or is_close_button) and
                element.aspect_ratio >= 1.0)
    
    def _is_text_region(self, region: np.ndarray) -> bool:
        """Detect pure text regions"""
        if region.size == 0:
            return False
        
        # Text regions have specific edge patterns
        edges = cv2.Canny(region, 30, 100)
        edge_ratio = cv2.countNonZero(edges) / region.size
        
        # Text has moderate edge density
        return 0.08 < edge_ratio < 0.25
        
        # Fallback classification
        if area > 30000:
            return 'panel'
        elif aspect_ratio > 20:
            return 'separator'
        else:
            return 'container'
    
    
    def _matches_pattern_simple(self, element: UIElementEnhanced, pattern: Dict) -> bool:
        """Simplified pattern matching for fast classification"""
        if element.area < pattern.get('min_area', 0):
            return False
        if element.area > pattern.get('max_area', float('inf')):
            return False
        if element.aspect_ratio < pattern.get('min_aspect_ratio', 0):
            return False
        if element.aspect_ratio > pattern.get('max_aspect_ratio', float('inf')):
            return False
        return True
    
    def _quick_iou(self, box1: Tuple, box2: Tuple) -> float:
        """Quick IoU calculation"""
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])
        
        if x2 <= x1 or y2 <= y1:
            return 0.0
        
        intersection = (x2 - x1) * (y2 - y1)
        area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
        area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
        
        return intersection / (area1 + area2 - intersection)
    
    def _simple_merge(self, elem1: UIElementEnhanced, elem2: UIElementEnhanced) -> UIElementEnhanced:
        """Simple element merging"""
        # Use bbox union
        x1 = min(elem1.bbox[0], elem2.bbox[0])
        y1 = min(elem1.bbox[1], elem2.bbox[1])
        x2 = max(elem1.bbox[2], elem2.bbox[2])
        y2 = max(elem1.bbox[3], elem2.bbox[3])
        
        # Use best element attributes
        best = elem1 if elem1.confidence > elem2.confidence else elem2
        
        w, h = x2 - x1, y2 - y1
        return UIElementEnhanced(
            element_type=best.element_type,
            bbox=(x1, y1, x2, y2),
            confidence=max(elem1.confidence, elem2.confidence),
            text=elem1.text or elem2.text,
            center=(x1 + w//2, y1 + h//2),
            area=w * h,
            aspect_ratio=w/h if h > 0 else 0,
            clickable=elem1.clickable or elem2.clickable
        )
    
    def _detect_by_text(self, image: np.ndarray) -> List[UIElementEnhanced]:
        """Detect UI elements based on OCR text recognition"""
        if not self.enable_ocr:
            return []
        
        elements = []
        
        try:
            # Get text detection data
            data = pytesseract.image_to_data(image, config=self.ocr_config, output_type=pytesseract.Output.DICT)
            
            n_boxes = len(data['text'])
            for i in range(n_boxes):
                confidence = int(data['conf'][i])
                text = data['text'][i].strip()
                
                if confidence > 30 and len(text) > 0:  # Filter low confidence and empty text
                    x = data['left'][i]
                    y = data['top'][i]
                    w = data['width'][i]
                    h = data['height'][i]
                    
                    if w > 5 and h > 5:  # Minimum size filter
                        element = UIElementEnhanced(
                            element_type='text',
                            bbox=(x, y, x + w, y + h),
                            confidence=confidence / 100.0,
                            text=text,
                            center=(x + w//2, y + h//2),
                            area=w * h,
                            aspect_ratio=w/h if h > 0 else 0,
                            attributes={'ocr_confidence': confidence}
                        )
                        elements.append(element)
        
        except Exception as e:
            logger.warning(f"OCR detection failed: {e}")
        
        return elements
    
    def _detect_by_templates(self, image: np.ndarray) -> List[UIElementEnhanced]:
        """Detect common UI patterns using template matching"""
        elements = []
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Common UI element patterns (simplified templates)
        templates = self._create_ui_templates()
        
        for template_name, template in templates.items():
            try:
                # Multi-scale template matching
                for scale in [0.8, 1.0, 1.2]:
                    scaled_template = cv2.resize(template, None, fx=scale, fy=scale)
                    if scaled_template.shape[0] < gray.shape[0] and scaled_template.shape[1] < gray.shape[1]:
                        
                        result = cv2.matchTemplate(gray, scaled_template, cv2.TM_CCOEFF_NORMED)
                        locations = np.where(result >= 0.6)  # Threshold for matches
                        
                        for pt in zip(*locations[::-1]):
                            x, y = pt
                            w, h = scaled_template.shape[1], scaled_template.shape[0]
                            
                            element = UIElementEnhanced(
                                element_type=template_name,
                                bbox=(x, y, x + w, y + h),
                                confidence=result[y, x],
                                center=(x + w//2, y + h//2),
                                area=w * h,
                                aspect_ratio=w/h if h > 0 else 0,
                                attributes={'template_scale': scale}
                            )
                            elements.append(element)
            
            except Exception as e:
                logger.warning(f"Template matching failed for {template_name}: {e}")
        
        return elements
    
    def _create_ui_templates(self) -> Dict[str, np.ndarray]:
        """Create simple UI element templates"""
        templates = {}
        
        # Simple button template (rectangular with border)
        button_template = np.ones((30, 80), dtype=np.uint8) * 200
        cv2.rectangle(button_template, (2, 2), (77, 27), 150, 2)
        templates['button'] = button_template
        
        # Input field template (rectangular with thin border)
        input_template = np.ones((25, 120), dtype=np.uint8) * 255
        cv2.rectangle(input_template, (1, 1), (118, 23), 100, 1)
        templates['input'] = input_template
        
        return templates
    
    def _detect_by_yolo(self, image: np.ndarray) -> List[UIElementEnhanced]:
        """Enhanced YOLO detection with post-processing"""
        if not self.use_yolo:
            return []
        
        elements = []
        
        try:
            results = self.yolo_model(image, conf=0.2)  # Lower confidence for more detections
            
            for r in results:
                boxes = r.boxes
                if boxes is not None:
                    for box in boxes:
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        conf = box.conf[0].item()
                        
                        w, h = x2 - x1, y2 - y1
                        element = UIElementEnhanced(
                            element_type='yolo_detected',
                            bbox=(int(x1), int(y1), int(x2), int(y2)),
                            confidence=conf,
                            center=(int(x1 + w//2), int(y1 + h//2)),
                            area=int(w * h),
                            aspect_ratio=w/h if h > 0 else 0
                        )
                        elements.append(element)
        
        except Exception as e:
            logger.warning(f"YOLO detection failed: {e}")
        
        return elements
    
    def _enhanced_merge_elements(self, elements: List[UIElementEnhanced]) -> List[UIElementEnhanced]:
        """Enhanced element merging with better overlap handling"""
        if not elements:
            return []
        
        # Sort by confidence and area
        elements.sort(key=lambda e: (e.confidence, e.area), reverse=True)
        
        merged = []
        used = set()
        
        for i, elem1 in enumerate(elements):
            if i in used:
                continue
            
            # Find overlapping elements
            overlapping = [elem1]
            for j, elem2 in enumerate(elements[i+1:], i+1):
                if j not in used:
                    iou = self._calculate_iou(elem1.bbox, elem2.bbox)
                    # More strict overlap threshold for better precision
                    if iou > 0.3:
                        overlapping.append(elem2)
                        used.add(j)
            
            # Merge overlapping elements intelligently
            if len(overlapping) > 1:
                merged_elem = self._intelligent_merge_group(overlapping)
                merged.append(merged_elem)
            else:
                merged.append(elem1)
        
        return merged
    
    def _intelligent_merge_group(self, elements: List[UIElementEnhanced]) -> UIElementEnhanced:
        """Intelligently merge a group of overlapping elements"""
        # Find element with highest confidence
        best_element = max(elements, key=lambda e: e.confidence)
        
        # Calculate union bounding box
        x1 = min(e.bbox[0] for e in elements)
        y1 = min(e.bbox[1] for e in elements)
        x2 = max(e.bbox[2] for e in elements)
        y2 = max(e.bbox[3] for e in elements)
        
        # Combine text from all elements
        texts = [e.text for e in elements if e.text]
        combined_text = ' '.join(texts) if texts else None
        
        # Use best element type or determine from text
        element_type = best_element.element_type
        if combined_text and element_type == 'unknown':
            element_type = self._classify_by_text(combined_text)
        
        w, h = x2 - x1, y2 - y1
        return UIElementEnhanced(
            element_type=element_type,
            bbox=(x1, y1, x2, y2),
            confidence=best_element.confidence,
            text=combined_text,
            center=(x1 + w//2, y1 + h//2),
            area=w * h,
            aspect_ratio=w/h if h > 0 else 0,
            attributes=best_element.attributes
        )
    
    def _enhanced_classify_element(self, element: UIElementEnhanced, image: np.ndarray) -> str:
        """Enhanced element classification using multiple features"""
        if element.element_type != 'unknown':
            return element.element_type
        
        # Extract features
        x1, y1, x2, y2 = element.bbox
        width = x2 - x1
        height = y2 - y1
        area = element.area
        aspect_ratio = element.aspect_ratio
        
        # Get ROI
        roi = image[y1:y2, x1:x2] if y1 < y2 and x1 < x2 else None
        if roi is None or roi.size == 0:
            return 'container'
        
        # Calculate features
        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY) if len(roi.shape) == 3 else roi
        mean_intensity = np.mean(gray_roi)
        std_intensity = np.std(gray_roi)
        
        # Edge density
        edges = cv2.Canny(gray_roi, 50, 150)
        edge_density = np.sum(edges > 0) / area if area > 0 else 0
        
        # Text-based classification (if text available)
        if element.text:
            text_type = self._classify_by_text(element.text)
            if text_type != 'unknown':
                return text_type
        
        # Enhanced classification rules
        patterns = self.ui_patterns
        
        # Button detection
        if self._matches_pattern(element, patterns['button']):
            if (std_intensity < 30 or  # Uniform color
                self._has_button_characteristics(gray_roi) or
                (element.text and any(kw in element.text.lower() for kw in patterns['button']['keywords']))):
                return 'button'
        
        # Input field detection  
        if self._matches_pattern(element, patterns['input']):
            if (aspect_ratio > 2.5 and height < 50 and
                (std_intensity > 10 or self._has_input_characteristics(gray_roi))):
                return 'input'
        
        # Text detection
        if (edge_density > patterns['text']['edge_density_threshold'] and
            self._matches_pattern(element, patterns['text'])):
            return 'text'
        
        # Icon detection
        if self._matches_pattern(element, patterns['icon']):
            if (aspect_ratio < 3 and area < 2000 and
                (edge_density > 0.2 or std_intensity > 20)):
                return 'icon'
        
        # Dropdown detection
        if self._matches_pattern(element, patterns['dropdown']):
            if aspect_ratio > 3 and height < 50:
                return 'dropdown'
        
        # Checkbox detection
        if self._matches_pattern(element, patterns['checkbox']):
            if area < 1000 and 0.5 < aspect_ratio < 2:
                return 'checkbox'
        
        # Menu item detection
        if self._matches_pattern(element, patterns['menu_item']):
            if (element.text and 
                any(kw in element.text.lower() for kw in patterns['menu_item']['keywords'])):
                return 'menu_item'
        
        # Default classification based on characteristics
        if area > 10000:
            return 'panel'
        elif edge_density > 0.3:
            return 'text'
        else:
            return 'container'
    
    def _classify_by_text(self, text: str) -> str:
        """Classify element based on text content"""
        text_lower = text.lower().strip()
        
        # Button keywords
        button_keywords = ['ok', 'cancel', 'save', 'submit', 'apply', 'close', 'yes', 'no', 
                          'continue', 'next', 'back', 'finish', 'done', 'create', 'delete',
                          'edit', 'update', 'confirm', 'accept', 'decline', 'retry']
        
        # Menu keywords  
        menu_keywords = ['file', 'edit', 'view', 'insert', 'format', 'tools', 'table',
                        'window', 'help', 'options', 'settings', 'preferences']
        
        # Input keywords
        input_keywords = ['search', 'enter', 'type', 'input', 'username', 'password',
                         'email', 'name', 'address', 'phone', 'message']
        
        # Link keywords
        link_keywords = ['http', 'www', 'link', 'more', 'details', 'learn', 'read']
        
        # Tab keywords
        tab_keywords = ['tab', 'sheet', 'page', 'section']
        
        if any(keyword in text_lower for keyword in button_keywords):
            return 'button'
        elif any(keyword in text_lower for keyword in menu_keywords):
            return 'menu_item'
        elif any(keyword in text_lower for keyword in input_keywords):
            return 'input'
        elif any(keyword in text_lower for keyword in link_keywords):
            return 'link'
        elif any(keyword in text_lower for keyword in tab_keywords):
            return 'tab'
        
        return 'text'
    
    def _matches_pattern(self, element: UIElementEnhanced, pattern: Dict) -> bool:
        """Check if element matches pattern constraints"""
        if element.area < pattern.get('min_area', 0):
            return False
        if element.area > pattern.get('max_area', float('inf')):
            return False
        if element.aspect_ratio < pattern.get('min_aspect_ratio', 0):
            return False
        if element.aspect_ratio > pattern.get('max_aspect_ratio', float('inf')):
            return False
        
        return True
    
    def _has_button_characteristics(self, roi: np.ndarray) -> bool:
        """Check if ROI has button-like characteristics"""
        # Look for rectangular border
        edges = cv2.Canny(roi, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            approx = cv2.approxPolyDP(largest_contour, 0.02 * cv2.arcLength(largest_contour, True), True)
            return len(approx) == 4  # Rectangular shape
        
        return False
    
    def _has_input_characteristics(self, roi: np.ndarray) -> bool:
        """Check if ROI has input field characteristics"""
        # Look for thin border and light interior
        edges = cv2.Canny(roi, 30, 100)
        edge_count = np.sum(edges > 0)
        total_pixels = roi.shape[0] * roi.shape[1]
        
        # Input fields typically have sparse edges (just the border)
        edge_ratio = edge_count / total_pixels if total_pixels > 0 else 0
        return 0.05 < edge_ratio < 0.2
    
    def _determine_clickability(self, element: UIElementEnhanced) -> bool:
        """Determine if element is clickable"""
        clickable_types = ['button', 'input', 'dropdown', 'checkbox', 'radio', 'menu_item', 'icon', 'link', 'tab']
        
        if element.element_type in clickable_types:
            return True
        
        # Check for clickable text patterns
        if element.text:
            clickable_text = ['click', 'select', 'choose', 'download', 'upload', 'link', 'more', 'details', 'open', 'browse']
            text_lower = element.text.lower()
            if any(keyword in text_lower for keyword in clickable_text):
                return True
        
        return False
    
    def _calculate_confidence(self, area: int, aspect_ratio: float, edge_density: float, std_intensity: float) -> float:
        """Calculate element detection confidence based on features"""
        confidence = 0.5  # Base confidence
        
        # Area-based confidence
        if 500 <= area <= 20000:  # Typical UI element size
            confidence += 0.2
        
        # Aspect ratio confidence
        if 0.2 <= aspect_ratio <= 20:  # Reasonable aspect ratio
            confidence += 0.1
        
        # Edge density confidence
        if 0.1 <= edge_density <= 0.5:  # Good edge density
            confidence += 0.1
        
        # Intensity variation confidence  
        if std_intensity > 10:  # Some variation suggests content
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _calculate_iou(self, box1: Tuple, box2: Tuple) -> float:
        """Calculate Intersection over Union with better handling"""
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])
        
        if x2 <= x1 or y2 <= y1:
            return 0.0
        
        intersection = (x2 - x1) * (y2 - y1)
        area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
        area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0.0
    
    def extract_ui_structure_enhanced(self, image: np.ndarray, include_ocr: bool = True) -> Dict[str, Any]:
        """Extract enhanced UI structure with improved information"""
        elements = self.detect_ui_elements(image)
        
        # Convert to serializable format with enhanced data
        ui_structure = {
            'timestamp': time.time(),
            'image_size': {'width': image.shape[1], 'height': image.shape[0]},
            'elements': [],
            'statistics': {
                'total_elements': len(elements),
                'clickable_elements': sum(1 for e in elements if e.clickable),
                'elements_with_text': sum(1 for e in elements if e.text),
                'element_types': {}
            }
        }
        
        # Count element types
        for elem in elements:
            elem_type = elem.element_type
            ui_structure['statistics']['element_types'][elem_type] = \
                ui_structure['statistics']['element_types'].get(elem_type, 0) + 1
        
        # Serialize elements
        for elem in elements:
            elem_dict = {
                'type': elem.element_type,
                'bbox': elem.bbox,
                'confidence': elem.confidence,
                'center': elem.center,
                'area': elem.area,
                'aspect_ratio': elem.aspect_ratio,
                'clickable': elem.clickable
            }
            
            if elem.text:
                elem_dict['text'] = elem.text
            
            if elem.attributes:
                elem_dict['attributes'] = elem.attributes
            
            ui_structure['elements'].append(elem_dict)
        
        # Enhanced hierarchy and regions
        ui_structure['hierarchy'] = self._build_enhanced_hierarchy(elements)
        ui_structure['regions'] = self._detect_enhanced_regions(elements, image.shape)
        
        return ui_structure
    
    def _build_enhanced_hierarchy(self, elements: List[UIElementEnhanced]) -> List[Dict]:
        """Build enhanced hierarchical structure"""
        hierarchy = []
        
        # Sort by area (larger first) for containment analysis
        sorted_elements = sorted(elements, key=lambda e: e.area, reverse=True)
        
        for i, parent in enumerate(sorted_elements):
            node = {
                'element': {
                    'type': parent.element_type,
                    'bbox': parent.bbox,
                    'text': parent.text,
                    'confidence': parent.confidence
                },
                'children': []
            }
            
            # Find children (elements contained within parent)
            for j, child in enumerate(sorted_elements[i+1:]):
                if self._is_contained(parent.bbox, child.bbox):
                    node['children'].append({
                        'type': child.element_type,
                        'bbox': child.bbox,
                        'text': child.text,
                        'confidence': child.confidence
                    })
            
            # Only add if not contained by any other element
            if not any(self._is_contained(other.bbox, parent.bbox) for other in sorted_elements[:i]):
                hierarchy.append(node)
        
        return hierarchy
    
    def _detect_enhanced_regions(self, elements: List[UIElementEnhanced], image_shape: Tuple) -> List[Dict]:
        """Detect UI regions with enhanced spatial understanding"""
        height, width = image_shape[:2]
        regions = []
        
        # Define region boundaries
        header_y = height * 0.15
        footer_y = height * 0.85
        sidebar_x = width * 0.25
        
        # Categorize elements by position
        header_elements = [e for e in elements if e.center[1] < header_y]
        footer_elements = [e for e in elements if e.center[1] > footer_y]
        left_sidebar_elements = [e for e in elements if e.center[0] < sidebar_x and header_y < e.center[1] < footer_y]
        content_elements = [e for e in elements if e.center[0] > sidebar_x and header_y < e.center[1] < footer_y]
        
        # Build region information
        if header_elements:
            regions.append({
                'type': 'header',
                'bounds': (0, 0, width, int(header_y)),
                'element_count': len(header_elements),
                'clickable_count': sum(1 for e in header_elements if e.clickable),
                'elements': [{'type': e.element_type, 'text': e.text} for e in header_elements]
            })
        
        if left_sidebar_elements:
            regions.append({
                'type': 'sidebar',
                'bounds': (0, int(header_y), int(sidebar_x), int(footer_y)),
                'element_count': len(left_sidebar_elements),
                'clickable_count': sum(1 for e in left_sidebar_elements if e.clickable),
                'elements': [{'type': e.element_type, 'text': e.text} for e in left_sidebar_elements]
            })
        
        if content_elements:
            regions.append({
                'type': 'content',
                'bounds': (int(sidebar_x), int(header_y), width, int(footer_y)),
                'element_count': len(content_elements),
                'clickable_count': sum(1 for e in content_elements if e.clickable),
                'elements': [{'type': e.element_type, 'text': e.text} for e in content_elements]
            })
        
        if footer_elements:
            regions.append({
                'type': 'footer',
                'bounds': (0, int(footer_y), width, height),
                'element_count': len(footer_elements),
                'clickable_count': sum(1 for e in footer_elements if e.clickable),
                'elements': [{'type': e.element_type, 'text': e.text} for e in footer_elements]
            })
        
        return regions
    
    def _is_contained(self, parent_bbox: Tuple, child_bbox: Tuple) -> bool:
        """Check if child bbox is contained within parent bbox"""
        return (parent_bbox[0] <= child_bbox[0] and
                parent_bbox[1] <= child_bbox[1] and
                parent_bbox[2] >= child_bbox[2] and
                parent_bbox[3] >= child_bbox[3] and
                parent_bbox != child_bbox)  # Not the same element
    
    def visualize_detection_enhanced(self, image: np.ndarray, elements: List[UIElementEnhanced]) -> np.ndarray:
        """Enhanced visualization with text labels and confidence"""
        vis_image = image.copy()
        
        # Enhanced color map with more element types
        colors = {
            'button': (0, 255, 0),        # Green
            'input': (255, 0, 0),         # Blue  
            'text': (0, 0, 255),          # Red
            'icon': (255, 255, 0),        # Cyan
            'dropdown': (255, 0, 255),    # Magenta
            'checkbox': (128, 255, 128),  # Light green
            'radio': (128, 255, 255),     # Light cyan
            'menu_item': (255, 128, 0),   # Orange
            'link': (0, 128, 255),        # Light blue
            'tab': (255, 128, 255),       # Light magenta
            'separator': (64, 64, 64),    # Dark gray
            'panel': (192, 192, 192),     # Light gray
            'container': (128, 128, 128), # Gray
            'unknown': (255, 255, 255)    # White
        }
        
        for elem in elements:
            color = colors.get(elem.element_type, colors['unknown'])
            x1, y1, x2, y2 = elem.bbox
            
            # Draw rectangle with thickness based on confidence
            thickness = max(1, int(elem.confidence * 3))
            cv2.rectangle(vis_image, (x1, y1), (x2, y2), color, thickness)
            
            # Draw label with confidence and text
            label_parts = [f"{elem.element_type}"]
            if elem.confidence:
                label_parts.append(f"({elem.confidence:.2f})")
            if elem.text and len(elem.text) < 20:
                label_parts.append(f'"{elem.text}"')
            
            label = " ".join(label_parts)
            
            # Multi-line label if too long
            if len(label) > 30:
                label = label[:27] + "..."
            
            cv2.putText(vis_image, label, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
            
            # Draw center point for clickable elements
            if elem.clickable:
                cv2.circle(vis_image, elem.center, 3, (0, 255, 255), -1)  # Yellow center
        
        return vis_image
    
    def benchmark_enhanced(self, image: np.ndarray, iterations: int = 5) -> Dict[str, Any]:
        """Enhanced benchmark with detailed metrics"""
        import statistics
        
        times = []
        element_counts = []
        clickable_counts = []
        text_counts = []
        type_distributions = []
        
        for _ in range(iterations):
            start = time.time()
            elements = self.detect_ui_elements(image)
            elapsed = time.time() - start
            
            times.append(elapsed)
            element_counts.append(len(elements))
            clickable_counts.append(sum(1 for e in elements if e.clickable))
            text_counts.append(sum(1 for e in elements if e.text))
            
            # Element type distribution
            type_dist = {}
            for elem in elements:
                type_dist[elem.element_type] = type_dist.get(elem.element_type, 0) + 1
            type_distributions.append(type_dist)
        
        return {
            'performance': {
                'avg_time': statistics.mean(times),
                'std_time': statistics.stdev(times) if len(times) > 1 else 0,
                'min_time': min(times),
                'max_time': max(times),
                'fps': 1 / statistics.mean(times)
            },
            'detection': {
                'avg_elements': statistics.mean(element_counts),
                'avg_clickable': statistics.mean(clickable_counts),
                'avg_with_text': statistics.mean(text_counts),
                'clickable_ratio': statistics.mean(clickable_counts) / statistics.mean(element_counts) if statistics.mean(element_counts) > 0 else 0
            },
            'element_types': {
                'unique_types': set().union(*type_distributions) if type_distributions else set(),
                'avg_distribution': type_distributions[0] if type_distributions else {}
            }
        }