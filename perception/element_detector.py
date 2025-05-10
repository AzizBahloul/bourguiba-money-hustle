import cv2
import numpy as np

class ElementDetector:
    """Detect UI elements like buttons, checkboxes, text fields, etc."""
    
    def detect_buttons(self, image):
        if not isinstance(image, np.ndarray):
            image = np.array(image)
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        buttons = []
        for contour in contours:
            if cv2.contourArea(contour) > 1000:
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = float(w) / h
                if 0.5 <= aspect_ratio <= 5:
                    buttons.append({
                        'x': x,
                        'y': y,
                        'width': w,
                        'height': h,
                        'center_x': x + w // 2,
                        'center_y': y + h // 2,
                        'type': 'button'
                    })
        return buttons
    
    def detect_text_fields(self, image):
        # TODO: Implement text field detection algorithm.
        return []
