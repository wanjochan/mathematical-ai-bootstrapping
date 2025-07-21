"""OCR backend for text extraction from images"""

import os
import sys
from typing import Optional, List, Dict, Any, Tuple, Union
from abc import ABC, abstractmethod
import numpy as np
from PIL import Image
import io
import base64


class OCREngine(ABC):
    """Abstract base class for OCR engines"""
    
    @abstractmethod
    def detect_text(self, image: Union[np.ndarray, Image.Image, str]) -> List[Dict[str, Any]]:
        """Detect text in image
        
        Args:
            image: Image as numpy array, PIL Image, or file path
            
        Returns:
            List of text detections with bounding boxes
        """
        pass
        
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this OCR engine is available"""
        pass
        

class WindowsOCREngine(OCREngine):
    """Windows native OCR API (Windows 10+)"""
    
    def __init__(self):
        self.available = self._check_availability()
        
    def _check_availability(self) -> bool:
        """Check if Windows OCR is available"""
        try:
            # Check Windows version
            if sys.platform != 'win32':
                return False
                
            # Try to import Windows Runtime
            import asyncio
            import winsdk.windows.media.ocr as ocr
            import winsdk.windows.graphics.imaging as imaging
            return True
        except ImportError:
            return False
            
    def is_available(self) -> bool:
        return self.available
        
    async def _detect_text_async(self, image_path: str) -> List[Dict[str, Any]]:
        """Async text detection using Windows OCR"""
        try:
            import winsdk.windows.storage as storage
            import winsdk.windows.media.ocr as ocr
            import winsdk.windows.graphics.imaging as imaging
            
            # Load image
            file = await storage.StorageFile.get_file_from_path_async(image_path)
            stream = await file.open_async(storage.FileAccessMode.READ)
            decoder = await imaging.BitmapDecoder.create_async(stream)
            bitmap = await decoder.get_software_bitmap_async()
            
            # Create OCR engine
            engine = ocr.OcrEngine.try_create_from_user_profile_languages()
            
            # Perform OCR
            result = await engine.recognize_async(bitmap)
            
            # Extract results
            detections = []
            for line in result.lines:
                words = []
                for word in line.words:
                    words.append({
                        'text': word.text,
                        'bbox': [
                            word.bounding_rect.x,
                            word.bounding_rect.y,
                            word.bounding_rect.x + word.bounding_rect.width,
                            word.bounding_rect.y + word.bounding_rect.height
                        ]
                    })
                    
                detections.append({
                    'text': line.text,
                    'words': words,
                    'bbox': self._get_line_bbox(words)
                })
                
            return detections
            
        except Exception as e:
            print(f"Windows OCR error: {e}")
            return []
            
    def _get_line_bbox(self, words: List[Dict]) -> List[int]:
        """Calculate bounding box for line from words"""
        if not words:
            return [0, 0, 0, 0]
            
        x1 = min(w['bbox'][0] for w in words)
        y1 = min(w['bbox'][1] for w in words)
        x2 = max(w['bbox'][2] for w in words)
        y2 = max(w['bbox'][3] for w in words)
        
        return [x1, y1, x2, y2]
        
    def detect_text(self, image: Union[np.ndarray, Image.Image, str]) -> List[Dict[str, Any]]:
        """Detect text using Windows OCR"""
        if not self.available:
            return []
            
        # Convert to file path
        if isinstance(image, np.ndarray):
            img = Image.fromarray(image)
            temp_path = "temp_ocr_image.png"
            img.save(temp_path)
        elif isinstance(image, Image.Image):
            temp_path = "temp_ocr_image.png"
            image.save(temp_path)
        else:
            temp_path = image
            
        # Run async OCR
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            results = loop.run_until_complete(self._detect_text_async(temp_path))
            return results
        finally:
            loop.close()
            # Clean up temp file
            if temp_path == "temp_ocr_image.png" and os.path.exists(temp_path):
                os.remove(temp_path)
                

class EasyOCREngine(OCREngine):
    """EasyOCR engine - supports 80+ languages"""
    
    def __init__(self, languages: List[str] = ['en', 'ch_sim']):
        self.languages = languages
        self.reader = None
        self.available = self._check_availability()
        
    def _check_availability(self) -> bool:
        """Check if EasyOCR is available"""
        try:
            import easyocr
            return True
        except ImportError:
            return False
            
    def is_available(self) -> bool:
        return self.available
        
    def _init_reader(self):
        """Initialize EasyOCR reader lazily"""
        if self.reader is None and self.available:
            try:
                import easyocr
                self.reader = easyocr.Reader(self.languages, gpu=True)
            except Exception:
                # Try CPU if GPU fails
                try:
                    import easyocr
                    self.reader = easyocr.Reader(self.languages, gpu=False)
                except Exception:
                    self.available = False
                    
    def detect_text(self, image: Union[np.ndarray, Image.Image, str]) -> List[Dict[str, Any]]:
        """Detect text using EasyOCR"""
        if not self.available:
            return []
            
        self._init_reader()
        if self.reader is None:
            return []
            
        # Convert image format
        if isinstance(image, Image.Image):
            image = np.array(image)
        elif isinstance(image, str):
            image = np.array(Image.open(image))
            
        try:
            # Perform OCR
            results = self.reader.readtext(image)
            
            # Format results
            detections = []
            for bbox, text, confidence in results:
                # Convert bbox format
                x_coords = [p[0] for p in bbox]
                y_coords = [p[1] for p in bbox]
                
                detections.append({
                    'text': text,
                    'confidence': confidence,
                    'bbox': [
                        min(x_coords),
                        min(y_coords),
                        max(x_coords),
                        max(y_coords)
                    ],
                    'polygon': bbox
                })
                
            return detections
            
        except Exception as e:
            print(f"EasyOCR error: {e}")
            return []
            

class TesseractEngine(OCREngine):
    """Tesseract OCR engine"""
    
    def __init__(self, lang: str = 'eng+chi_sim'):
        self.lang = lang
        self.available = self._check_availability()
        
    def _check_availability(self) -> bool:
        """Check if Tesseract is available"""
        try:
            import pytesseract
            # Try to get version
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False
            
    def is_available(self) -> bool:
        return self.available
        
    def detect_text(self, image: Union[np.ndarray, Image.Image, str]) -> List[Dict[str, Any]]:
        """Detect text using Tesseract"""
        if not self.available:
            return []
            
        try:
            import pytesseract
            
            # Convert image format
            if isinstance(image, np.ndarray):
                image = Image.fromarray(image)
            elif isinstance(image, str):
                image = Image.open(image)
                
            # Get detailed data
            data = pytesseract.image_to_data(
                image, 
                lang=self.lang,
                output_type=pytesseract.Output.DICT
            )
            
            # Format results
            detections = []
            n_boxes = len(data['level'])
            
            for i in range(n_boxes):
                if data['text'][i].strip():
                    detections.append({
                        'text': data['text'][i],
                        'confidence': data['conf'][i],
                        'bbox': [
                            data['left'][i],
                            data['top'][i],
                            data['left'][i] + data['width'][i],
                            data['top'][i] + data['height'][i]
                        ],
                        'level': data['level'][i]
                    })
                    
            return detections
            
        except Exception as e:
            print(f"Tesseract error: {e}")
            return []
            

class PaddleOCREngine(OCREngine):
    """PaddleOCR engine - optimized for Chinese"""
    
    def __init__(self):
        self.ocr = None
        self.available = self._check_availability()
        
    def _check_availability(self) -> bool:
        """Check if PaddleOCR is available"""
        try:
            from paddleocr import PaddleOCR
            return True
        except ImportError:
            return False
            
    def is_available(self) -> bool:
        return self.available
        
    def _init_ocr(self):
        """Initialize PaddleOCR lazily"""
        if self.ocr is None and self.available:
            try:
                from paddleocr import PaddleOCR
                self.ocr = PaddleOCR(
                    use_angle_cls=True,
                    lang='ch',
                    use_gpu=True,
                    show_log=False
                )
            except Exception:
                # Try CPU version
                try:
                    from paddleocr import PaddleOCR
                    self.ocr = PaddleOCR(
                        use_angle_cls=True,
                        lang='ch',
                        use_gpu=False,
                        show_log=False
                    )
                except Exception:
                    self.available = False
                    
    def detect_text(self, image: Union[np.ndarray, Image.Image, str]) -> List[Dict[str, Any]]:
        """Detect text using PaddleOCR"""
        if not self.available:
            return []
            
        self._init_ocr()
        if self.ocr is None:
            return []
            
        # Convert image format
        if isinstance(image, Image.Image):
            image = np.array(image)
        elif isinstance(image, str):
            # PaddleOCR can handle file paths directly
            pass
            
        try:
            # Perform OCR
            results = self.ocr.ocr(image, cls=True)
            
            # Format results
            detections = []
            if results and results[0]:
                for line in results[0]:
                    bbox, (text, confidence) = line
                    
                    # Convert bbox to standard format
                    x_coords = [p[0] for p in bbox]
                    y_coords = [p[1] for p in bbox]
                    
                    detections.append({
                        'text': text,
                        'confidence': confidence,
                        'bbox': [
                            min(x_coords),
                            min(y_coords),
                            max(x_coords),
                            max(y_coords)
                        ],
                        'polygon': bbox
                    })
                    
            return detections
            
        except Exception as e:
            print(f"PaddleOCR error: {e}")
            return []
            

class OCRBackend:
    """Unified OCR backend with multiple engine support"""
    
    def __init__(self):
        """Initialize OCR backend with available engines"""
        self.engines = {
            'windows': WindowsOCREngine(),
            'easyocr': EasyOCREngine(),
            'tesseract': TesseractEngine(),
            'paddleocr': PaddleOCREngine()
        }
        
        # Check which engines are available
        self.available_engines = {
            name: engine for name, engine in self.engines.items()
            if engine.is_available()
        }
        
        print(f"Available OCR engines: {list(self.available_engines.keys())}")
        
    def detect_text(self, image: Union[np.ndarray, Image.Image, str],
                   engine: Optional[str] = None,
                   merge_results: bool = False) -> List[Dict[str, Any]]:
        """Detect text using specified or best available engine
        
        Args:
            image: Input image
            engine: Specific engine to use (None for auto-select)
            merge_results: Merge results from multiple engines
            
        Returns:
            List of text detections
        """
        if not self.available_engines:
            print("No OCR engines available!")
            return []
            
        if engine:
            # Use specific engine
            if engine in self.available_engines:
                return self.available_engines[engine].detect_text(image)
            else:
                print(f"Engine '{engine}' not available")
                return []
                
        elif merge_results:
            # Merge results from all engines
            all_results = []
            for engine_name, engine_obj in self.available_engines.items():
                results = engine_obj.detect_text(image)
                for r in results:
                    r['engine'] = engine_name
                all_results.extend(results)
            return self._merge_detections(all_results)
            
        else:
            # Auto-select best available engine
            # Priority: Windows (fastest) > EasyOCR > PaddleOCR > Tesseract
            priority = ['windows', 'easyocr', 'paddleocr', 'tesseract']
            
            for engine_name in priority:
                if engine_name in self.available_engines:
                    return self.available_engines[engine_name].detect_text(image)
                    
        return []
        
    def _merge_detections(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge overlapping detections from multiple engines"""
        # Simple implementation - can be improved with NMS
        merged = []
        used = set()
        
        for i, det1 in enumerate(detections):
            if i in used:
                continue
                
            # Find overlapping detections
            overlapping = [det1]
            for j, det2 in enumerate(detections[i+1:], i+1):
                if j not in used and self._bbox_overlap(det1['bbox'], det2['bbox']) > 0.5:
                    overlapping.append(det2)
                    used.add(j)
                    
            # Merge overlapping detections
            if len(overlapping) > 1:
                merged_det = self._merge_detection_group(overlapping)
                merged.append(merged_det)
            else:
                merged.append(det1)
                
        return merged
        
    def _bbox_overlap(self, bbox1: List[float], bbox2: List[float]) -> float:
        """Calculate IoU overlap between two bounding boxes"""
        x1 = max(bbox1[0], bbox2[0])
        y1 = max(bbox1[1], bbox2[1])
        x2 = min(bbox1[2], bbox2[2])
        y2 = min(bbox1[3], bbox2[3])
        
        if x2 <= x1 or y2 <= y1:
            return 0.0
            
        intersection = (x2 - x1) * (y2 - y1)
        area1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
        area2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0.0
        
    def _merge_detection_group(self, detections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge a group of overlapping detections"""
        # Use detection with highest confidence
        best = max(detections, key=lambda d: d.get('confidence', 0))
        
        # Merge bounding boxes
        all_x = []
        all_y = []
        for det in detections:
            bbox = det['bbox']
            all_x.extend([bbox[0], bbox[2]])
            all_y.extend([bbox[1], bbox[3]])
            
        merged_bbox = [min(all_x), min(all_y), max(all_x), max(all_y)]
        
        # Add engines info
        engines = list(set(d.get('engine', 'unknown') for d in detections))
        
        return {
            'text': best['text'],
            'confidence': best.get('confidence', 0),
            'bbox': merged_bbox,
            'engines': engines,
            'num_detections': len(detections)
        }
        
    def benchmark(self, image: Union[np.ndarray, Image.Image, str]) -> Dict[str, Any]:
        """Benchmark all available engines
        
        Args:
            image: Test image
            
        Returns:
            Benchmark results
        """
        import time
        
        results = {}
        
        for engine_name, engine in self.available_engines.items():
            start_time = time.time()
            
            try:
                detections = engine.detect_text(image)
                elapsed = time.time() - start_time
                
                results[engine_name] = {
                    'success': True,
                    'time': elapsed,
                    'detections': len(detections),
                    'total_chars': sum(len(d['text']) for d in detections)
                }
            except Exception as e:
                results[engine_name] = {
                    'success': False,
                    'error': str(e)
                }
                
        return results