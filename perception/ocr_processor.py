import pytesseract
import cv2
import numpy as np
from PIL import Image

class OCRProcessor:
    def __init__(self, tesseract_path=None):
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
    
    def extract_text(self, image):
        if isinstance(image, np.ndarray):
            image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        text = pytesseract.image_to_string(image)
        return text
    
    def extract_text_with_positions(self, image):
        if isinstance(image, np.ndarray):
            image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        results = []
        n_boxes = len(data['text'])
        for i in range(n_boxes):
            if int(data['conf'][i]) > 60:
                text = data['text'][i]
                if text.strip():
                    results.append({
                        'text': text,
                        'x': data['left'][i],
                        'y': data['top'][i],
                        'width': data['width'][i],
                        'height': data['height'][i],
                        'confidence': data['conf'][i]
                    })
        return results
