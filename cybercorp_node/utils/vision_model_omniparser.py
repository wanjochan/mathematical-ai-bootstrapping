"""OmniParser-based vision model for high-accuracy UI element detection"""

import os
import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
import logging
from dataclasses import dataclass
import torch
from PIL import Image

logger = logging.getLogger(__name__)

@dataclass
class UIElementOmni:
    """UI element detected by OmniParser"""
    element_type: str
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2)
    center: Tuple[int, int]
    confidence: float
    clickable: bool
    text: Optional[str] = None
    description: Optional[str] = None

class UIVisionModelOmniParser:
    """OmniParser-based vision model wrapper"""
    
    def __init__(self, model_path: str = None):
        self.model_path = model_path or "weights"
        self.detector = None
        self.captioner = None
        self._initialize_models()
        
    def _initialize_models(self):
        """Initialize OmniParser models"""
        try:
            # Check if we can import required modules
            try:
                from ultralytics import YOLO
                import torch
                from transformers import AutoProcessor, AutoModelForCausalLM
            except ImportError as e:
                logger.error(f"Missing dependencies: {e}")
                logger.info("Please install: pip install ultralytics transformers torch torchvision")
                raise
            
            # Load detection model (YOLOv8)
            detection_model_path = os.path.join(self.model_path, "icon_detect", "model.pt")
            if os.path.exists(detection_model_path):
                self.detector = YOLO(detection_model_path)
                logger.info(f"Loaded OmniParser detection model from {detection_model_path}")
            else:
                logger.warning(f"Detection model not found at {detection_model_path}")
                logger.info("Using YOLOv8n as fallback")
                self.detector = YOLO('yolov8n.pt')
            
            # Load caption model (Florence-2)
            caption_model_path = os.path.join(self.model_path, "icon_caption_florence")
            if os.path.exists(caption_model_path):
                self.processor = AutoProcessor.from_pretrained(caption_model_path, trust_remote_code=True)
                self.captioner = AutoModelForCausalLM.from_pretrained(
                    caption_model_path, 
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                    trust_remote_code=True
                )
                logger.info(f"Loaded OmniParser caption model from {caption_model_path}")
            else:
                logger.warning(f"Caption model not found at {caption_model_path}")
                self.processor = None
                self.captioner = None
                
        except Exception as e:
            logger.error(f"Failed to initialize OmniParser models: {e}")
            raise
    
    def detect_ui_elements(self, image: np.ndarray) -> List[UIElementOmni]:
        """Detect UI elements using OmniParser"""
        if image is None or image.size == 0:
            return []
        
        elements = []
        
        try:
            # Run YOLO detection
            results = self.detector(image)
            
            # Process each detection
            for result in results:
                if result.boxes is None:
                    continue
                    
                boxes = result.boxes
                for i in range(len(boxes)):
                    # Get bbox coordinates
                    x1, y1, x2, y2 = boxes.xyxy[i].tolist()
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                    
                    # Get confidence and class
                    conf = float(boxes.conf[i])
                    cls = int(boxes.cls[i])
                    
                    # Map class to element type
                    logger.debug(f"Detected class {cls}: {result.names.get(cls, 'unknown')}")
                    element_type = self._map_class_to_type(cls, result.names)
                    
                    # Create UI element
                    element = UIElementOmni(
                        element_type=element_type,
                        bbox=(x1, y1, x2, y2),
                        center=((x1 + x2) // 2, (y1 + y2) // 2),
                        confidence=conf,
                        clickable=self._is_clickable(element_type)
                    )
                    
                    # Get element description if captioner is available
                    if self.captioner and self.processor:
                        element.description = self._get_element_caption(image, (x1, y1, x2, y2))
                    
                    elements.append(element)
            
            logger.info(f"OmniParser detected {len(elements)} UI elements")
            
        except Exception as e:
            logger.error(f"Error in OmniParser detection: {e}")
            # Fallback to basic detection
            elements = self._fallback_detection(image)
        
        return elements
    
    def _map_class_to_type(self, cls: int, names: Dict) -> str:
        """Map YOLO class to UI element type"""
        # OmniParser specific mappings
        class_name = names.get(cls, 'unknown').lower()
        
        # Map to standard UI element types
        type_mapping = {
            'button': 'button',
            'icon': 'button',  # Icons are often clickable
            'text': 'text',
            'textbox': 'input',
            'input': 'input',
            'checkbox': 'checkbox',
            'radio': 'radio',
            'dropdown': 'dropdown',
            'combobox': 'dropdown',
            'link': 'link',
            'tab': 'tab',
            'menu': 'menu_item',
            'image': 'image',
            'video': 'video',
            'slider': 'slider',
            'switch': 'switch',
            'toggle': 'switch',
        }
        
        return type_mapping.get(class_name, class_name)
    
    def _is_clickable(self, element_type: str) -> bool:
        """Determine if element type is clickable"""
        clickable_types = {
            'button', 'input', 'checkbox', 'radio', 'dropdown',
            'link', 'tab', 'menu_item', 'switch', 'slider'
        }
        return element_type in clickable_types
    
    def _get_element_caption(self, image: np.ndarray, bbox: Tuple[int, int, int, int]) -> str:
        """Get caption/description for UI element using Florence-2"""
        try:
            x1, y1, x2, y2 = bbox
            # Crop element region
            element_img = image[y1:y2, x1:x2]
            
            if element_img.size == 0:
                return ""
            
            # Convert to PIL Image
            pil_img = Image.fromarray(cv2.cvtColor(element_img, cv2.COLOR_BGR2RGB))
            
            # Generate caption
            task_prompt = "<CAPTION>"
            inputs = self.processor(text=task_prompt, images=pil_img, return_tensors="pt")
            
            generated_ids = self.captioner.generate(
                input_ids=inputs["input_ids"],
                pixel_values=inputs["pixel_values"],
                max_new_tokens=1024,
                num_beams=3
            )
            
            generated_text = self.processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
            caption = self.processor.post_process_generation(generated_text, task=task_prompt)
            
            return caption.get("<CAPTION>", "")
            
        except Exception as e:
            logger.debug(f"Error generating caption: {e}")
            return ""
    
    def _fallback_detection(self, image: np.ndarray) -> List[UIElementOmni]:
        """Fallback detection using basic YOLO"""
        logger.warning("Using fallback detection method")
        elements = []
        
        # Use standard YOLOv8 for general object detection
        if self.detector:
            results = self.detector(image)
            for result in results:
                if result.boxes is None:
                    continue
                    
                boxes = result.boxes
                for i in range(len(boxes)):
                    x1, y1, x2, y2 = boxes.xyxy[i].tolist()
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                    conf = float(boxes.conf[i])
                    
                    # Basic element
                    element = UIElementOmni(
                        element_type='unknown',
                        bbox=(x1, y1, x2, y2),
                        center=((x1 + x2) // 2, (y1 + y2) // 2),
                        confidence=conf,
                        clickable=True
                    )
                    elements.append(element)
        
        return elements
    
    def visualize_detection(self, image: np.ndarray, elements: List[UIElementOmni]) -> np.ndarray:
        """Visualize detected elements on image"""
        vis_img = image.copy()
        
        for elem in elements:
            x1, y1, x2, y2 = elem.bbox
            color = (0, 255, 0) if elem.clickable else (255, 0, 0)
            
            # Draw bounding box
            cv2.rectangle(vis_img, (x1, y1), (x2, y2), color, 2)
            
            # Draw label
            label = f"{elem.element_type} ({elem.confidence:.2f})"
            if elem.description:
                label += f": {elem.description[:20]}..."
                
            cv2.putText(vis_img, label, (x1, y1-5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            
            # Draw center point
            cv2.circle(vis_img, elem.center, 3, color, -1)
        
        return vis_img