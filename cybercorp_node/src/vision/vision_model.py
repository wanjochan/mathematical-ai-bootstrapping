"""Vision model for UI understanding - lightweight implementation"""

import cv2
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
import time
from dataclasses import dataclass
from PIL import Image
import json

# Try to import YOLO for object detection (optional)
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("YOLO not available. Install with: pip install ultralytics")


@dataclass
class UIElement:
    """Represents a detected UI element"""
    element_type: str
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    confidence: float
    text: Optional[str] = None
    clickable: bool = False
    attributes: Dict[str, Any] = None


class UIVisionModel:
    """Lightweight vision model for UI understanding"""
    
    def __init__(self, use_yolo: bool = False):
        """Initialize vision model
        
        Args:
            use_yolo: Whether to use YOLO for object detection
        """
        self.use_yolo = use_yolo and YOLO_AVAILABLE
        
        if self.use_yolo:
            # Load YOLO model (you can train a custom one for UI elements)
            self.yolo_model = YOLO('yolov8n.pt')  # nano model for speed
        
        # Element detection parameters
        self.min_element_size = 20  # minimum size in pixels
        self.contrast_threshold = 30
        
        # UI element patterns (can be extended)
        self.ui_patterns = {
            'button': {
                'min_aspect_ratio': 1.5,
                'max_aspect_ratio': 8.0,
                'min_area': 500,
                'typical_heights': [20, 30, 40, 50]
            },
            'input': {
                'min_aspect_ratio': 3.0,
                'max_aspect_ratio': 20.0,
                'min_area': 800,
                'typical_heights': [25, 30, 35, 40]
            },
            'menu': {
                'min_aspect_ratio': 0.1,
                'max_aspect_ratio': 1.0,
                'min_area': 200
            }
        }
        
    def detect_ui_elements(self, image: np.ndarray) -> List[UIElement]:
        """Detect UI elements in image using lightweight computer vision
        
        Args:
            image: Input image as numpy array (BGR format)
            
        Returns:
            List of detected UI elements
        """
        start_time = time.time()
        
        # Convert to grayscale for processing
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detect elements using multiple strategies
        elements = []
        
        # Strategy 1: Edge-based detection
        edge_elements = self._detect_by_edges(gray)
        elements.extend(edge_elements)
        
        # Strategy 2: Contour-based detection
        contour_elements = self._detect_by_contours(gray)
        elements.extend(contour_elements)
        
        # Strategy 3: YOLO detection (if available)
        if self.use_yolo:
            yolo_elements = self._detect_by_yolo(image)
            elements.extend(yolo_elements)
        
        # Remove duplicates and merge overlapping elements
        elements = self._merge_elements(elements)
        
        # Classify elements
        for element in elements:
            element.element_type = self._classify_element(element, gray)
            
        elapsed = time.time() - start_time
        print(f"UI detection took {elapsed:.3f}s, found {len(elements)} elements")
        
        return elements
        
    def _detect_by_edges(self, gray: np.ndarray) -> List[UIElement]:
        """Detect UI elements using edge detection"""
        elements = []
        
        # Apply Canny edge detection
        edges = cv2.Canny(gray, 50, 150)
        
        # Find contours from edges
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            # Get bounding box
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter by size
            if w < self.min_element_size or h < self.min_element_size:
                continue
                
            # Create UI element
            element = UIElement(
                element_type='unknown',
                bbox=(x, y, x + w, y + h),
                confidence=0.5
            )
            elements.append(element)
            
        return elements
        
    def _detect_by_contours(self, gray: np.ndarray) -> List[UIElement]:
        """Detect UI elements using adaptive thresholding and contours"""
        elements = []
        
        # Adaptive threshold to handle varying lighting
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 11, 2
        )
        
        # Morphological operations to connect components
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 3))
        morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            # Get bounding box
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter by size and aspect ratio
            if w < self.min_element_size or h < self.min_element_size:
                continue
                
            aspect_ratio = w / h
            if aspect_ratio < 0.1 or aspect_ratio > 50:
                continue
                
            # Check if it's a filled rectangle (likely a button or input)
            roi = gray[y:y+h, x:x+w]
            mean_val = np.mean(roi)
            std_val = np.std(roi)
            
            # Low std suggests uniform color (button/input)
            confidence = 0.7 if std_val < 30 else 0.5
            
            element = UIElement(
                element_type='unknown',
                bbox=(x, y, x + w, y + h),
                confidence=confidence
            )
            elements.append(element)
            
        return elements
        
    def _detect_by_yolo(self, image: np.ndarray) -> List[UIElement]:
        """Detect UI elements using YOLO (if available)"""
        if not self.use_yolo:
            return []
            
        elements = []
        
        try:
            # Run YOLO detection
            results = self.yolo_model(image, conf=0.25)
            
            for r in results:
                boxes = r.boxes
                if boxes is not None:
                    for box in boxes:
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        conf = box.conf[0].item()
                        
                        element = UIElement(
                            element_type='yolo_detected',
                            bbox=(int(x1), int(y1), int(x2), int(y2)),
                            confidence=conf
                        )
                        elements.append(element)
                        
        except Exception as e:
            print(f"YOLO detection error: {e}")
            
        return elements
        
    def _merge_elements(self, elements: List[UIElement]) -> List[UIElement]:
        """Merge overlapping elements"""
        if not elements:
            return []
            
        # Sort by area (larger first)
        elements.sort(key=lambda e: (e.bbox[2] - e.bbox[0]) * (e.bbox[3] - e.bbox[1]), reverse=True)
        
        merged = []
        used = set()
        
        for i, elem1 in enumerate(elements):
            if i in used:
                continue
                
            # Check for overlaps with other elements
            overlapping = [elem1]
            for j, elem2 in enumerate(elements[i+1:], i+1):
                if j not in used and self._iou(elem1.bbox, elem2.bbox) > 0.5:
                    overlapping.append(elem2)
                    used.add(j)
                    
            # Merge overlapping elements
            if len(overlapping) > 1:
                merged_elem = self._merge_group(overlapping)
                merged.append(merged_elem)
            else:
                merged.append(elem1)
                
        return merged
        
    def _iou(self, box1: Tuple, box2: Tuple) -> float:
        """Calculate Intersection over Union"""
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
        
    def _merge_group(self, elements: List[UIElement]) -> UIElement:
        """Merge a group of overlapping elements"""
        # Take bounding box union
        x1 = min(e.bbox[0] for e in elements)
        y1 = min(e.bbox[1] for e in elements)
        x2 = max(e.bbox[2] for e in elements)
        y2 = max(e.bbox[3] for e in elements)
        
        # Average confidence
        confidence = sum(e.confidence for e in elements) / len(elements)
        
        return UIElement(
            element_type='merged',
            bbox=(x1, y1, x2, y2),
            confidence=confidence
        )
        
    def _classify_element(self, element: UIElement, gray_image: np.ndarray) -> str:
        """Classify UI element type based on visual features"""
        x1, y1, x2, y2 = element.bbox
        width = x2 - x1
        height = y2 - y1
        area = width * height
        aspect_ratio = width / height
        
        # Extract ROI
        roi = gray_image[y1:y2, x1:x2]
        
        # Calculate features
        mean_intensity = np.mean(roi)
        std_intensity = np.std(roi)
        
        # Edge density (indicates text or icons)
        edges = cv2.Canny(roi, 50, 150)
        edge_density = np.sum(edges > 0) / area
        
        # Classification rules (can be improved with ML)
        if aspect_ratio > 3 and height < 50 and std_intensity < 20:
            return 'input'
        elif aspect_ratio > 1.5 and aspect_ratio < 8 and std_intensity < 30:
            return 'button'
        elif edge_density > 0.3:
            return 'text'
        elif aspect_ratio < 1.5 and area > 10000:
            return 'panel'
        elif height < 30 and width > 100:
            return 'menu_item'
        else:
            return 'container'
            
    def extract_ui_structure(self, image: np.ndarray, 
                           include_ocr: bool = True) -> Dict[str, Any]:
        """Extract complete UI structure from image
        
        Args:
            image: Input image
            include_ocr: Whether to include OCR results
            
        Returns:
            Dictionary with UI structure
        """
        # Detect UI elements
        elements = self.detect_ui_elements(image)
        
        # Convert to serializable format
        ui_structure = {
            'timestamp': time.time(),
            'image_size': {'width': image.shape[1], 'height': image.shape[0]},
            'elements': []
        }
        
        for elem in elements:
            elem_dict = {
                'type': elem.element_type,
                'bbox': elem.bbox,
                'confidence': elem.confidence,
                'center': ((elem.bbox[0] + elem.bbox[2]) // 2, 
                          (elem.bbox[1] + elem.bbox[3]) // 2)
            }
            
            # Add text if OCR is enabled
            if include_ocr and elem.text:
                elem_dict['text'] = elem.text
                
            ui_structure['elements'].append(elem_dict)
            
        # Build element hierarchy (optional)
        ui_structure['hierarchy'] = self._build_hierarchy(elements)
        
        return ui_structure
        
    def _build_hierarchy(self, elements: List[UIElement]) -> List[Dict]:
        """Build hierarchical structure of UI elements"""
        # Simple containment-based hierarchy
        hierarchy = []
        
        # Sort by area (larger first)
        sorted_elements = sorted(
            elements, 
            key=lambda e: (e.bbox[2] - e.bbox[0]) * (e.bbox[3] - e.bbox[1]), 
            reverse=True
        )
        
        for i, parent in enumerate(sorted_elements):
            node = {
                'element': {
                    'type': parent.element_type,
                    'bbox': parent.bbox
                },
                'children': []
            }
            
            # Find children (elements contained within)
            for j, child in enumerate(sorted_elements[i+1:]):
                if self._contains(parent.bbox, child.bbox):
                    node['children'].append({
                        'type': child.element_type,
                        'bbox': child.bbox
                    })
                    
            if not any(self._contains(other.bbox, parent.bbox) 
                      for other in sorted_elements[:i]):
                # Top-level element
                hierarchy.append(node)
                
        return hierarchy
        
    def _contains(self, parent_bbox: Tuple, child_bbox: Tuple) -> bool:
        """Check if parent bbox contains child bbox"""
        return (parent_bbox[0] <= child_bbox[0] and
                parent_bbox[1] <= child_bbox[1] and
                parent_bbox[2] >= child_bbox[2] and
                parent_bbox[3] >= child_bbox[3])
                
    def visualize_detection(self, image: np.ndarray, 
                          elements: List[UIElement]) -> np.ndarray:
        """Visualize detected elements on image
        
        Args:
            image: Original image
            elements: Detected elements
            
        Returns:
            Image with visualizations
        """
        vis_image = image.copy()
        
        # Color map for different element types
        colors = {
            'button': (0, 255, 0),      # Green
            'input': (255, 0, 0),       # Blue
            'text': (0, 0, 255),        # Red
            'panel': (255, 255, 0),     # Cyan
            'menu_item': (255, 0, 255), # Magenta
            'container': (128, 128, 128), # Gray
            'unknown': (255, 255, 255)  # White
        }
        
        for elem in elements:
            color = colors.get(elem.element_type, colors['unknown'])
            x1, y1, x2, y2 = elem.bbox
            
            # Draw rectangle
            cv2.rectangle(vis_image, (x1, y1), (x2, y2), color, 2)
            
            # Draw label
            label = f"{elem.element_type} ({elem.confidence:.2f})"
            cv2.putText(vis_image, label, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                       
            # Draw center point
            center = ((x1 + x2) // 2, (y1 + y2) // 2)
            cv2.circle(vis_image, center, 3, color, -1)
            
        return vis_image
        
    def benchmark(self, image: np.ndarray, iterations: int = 10) -> Dict[str, float]:
        """Benchmark model performance
        
        Args:
            image: Test image
            iterations: Number of iterations
            
        Returns:
            Performance metrics
        """
        import statistics
        
        times = []
        element_counts = []
        
        for _ in range(iterations):
            start = time.time()
            elements = self.detect_ui_elements(image)
            elapsed = time.time() - start
            
            times.append(elapsed)
            element_counts.append(len(elements))
            
        return {
            'avg_time': statistics.mean(times),
            'std_time': statistics.stdev(times) if len(times) > 1 else 0,
            'min_time': min(times),
            'max_time': max(times),
            'fps': 1 / statistics.mean(times),
            'avg_elements': statistics.mean(element_counts)
        }