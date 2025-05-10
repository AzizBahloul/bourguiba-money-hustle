from .screen_capture import ScreenCapture
from .ocr_processor import OCRProcessor
from .element_detector import ElementDetector
import concurrent.futures
from loguru import logger

class ScreenAnalyzer:
    """High-level screen analysis that combines different perception techniques."""
    
    def __init__(self, tesseract_path=None):
        self.screen_capture = ScreenCapture()
        self.ocr = OCRProcessor(tesseract_path)
        self.detector = ElementDetector()
        self._cached_analysis = None  # Store the latest analysis
        # Create thread pool executor for parallel processing
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
    
    def analyze_current_screen(self, force_new=False):
        """Analyze the current screen, with option to use cached analysis"""
        if not force_new and self._cached_analysis is not None:
            return self._cached_analysis
        
        screenshot = self.screen_capture.capture_full_screen()
        np_screenshot = self.screen_capture.to_numpy(screenshot)
        
        # Run OCR and button detection in parallel
        futures = {
            'text': self.executor.submit(self.ocr.extract_text, screenshot),
            'text_elements': self.executor.submit(self.ocr.extract_text_with_positions, screenshot),
            'buttons': self.executor.submit(self.detector.detect_buttons, np_screenshot)
        }
        
        # Gather results
        text = futures['text'].result()
        text_elements = futures['text_elements'].result()
        buttons = futures['buttons'].result()
        
        analysis = {
            'text_elements': text_elements,
            'ui_elements': {
                'buttons': buttons,
            },
            'raw_text': text,
            'screenshot': screenshot
        }
        # Cache the analysis
        self._cached_analysis = analysis
        return analysis
    
    def find_element_by_text(self, text, case_sensitive=False, partial_match=False):
        analysis = self.analyze_current_screen()  # Use cached analysis if available
        matching_elements = []
        for elem in analysis['text_elements']:
            elem_text = elem['text']
            search_text = text
            
            if not case_sensitive:
                elem_text = elem_text.lower()
                search_text = search_text.lower()
                
            if partial_match:
                if search_text in elem_text or elem_text in search_text:
                    # Calculate center coordinates before adding to matches
                    center_elem = elem.copy()
                    center_elem['center_x'] = elem['x'] + elem['width'] // 2
                    center_elem['center_y'] = elem['y'] + elem['height'] // 2
                    matching_elements.append(center_elem)
            else:
                if search_text in elem_text:
                    # Calculate center coordinates before adding to matches
                    center_elem = elem.copy()
                    center_elem['center_x'] = elem['x'] + elem['width'] // 2
                    center_elem['center_y'] = elem['y'] + elem['height'] // 2
                    matching_elements.append(center_elem)
                    
        return matching_elements
    
    def clear_cache(self):
        """Clear the cached analysis"""
        self._cached_analysis = None
        
    def shutdown(self):
        """Properly clean up resources"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
