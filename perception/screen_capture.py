import mss
import numpy as np
from PIL import Image, ImageGrab

class ScreenCapture:
    def __init__(self):
        self.sct = mss.mss()
    
    def capture_full_screen(self):
        """Capture the entire screen."""
        try:
            monitor = self.sct.monitors[0]
            screenshot = self.sct.grab(monitor)
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        except AttributeError:
            # Fallback if mss fails due to display issues
            img = ImageGrab.grab()
        return img
    
    def capture_region(self, x, y, width, height):
        """Capture a specific region of the screen."""
        try:
            region = {"top": y, "left": x, "width": width, "height": height}
            screenshot = self.sct.grab(region)
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        except AttributeError:
            # Fallback: crop a full-screen grab
            full = ImageGrab.grab()
            img = full.crop((x, y, x + width, y + height))
        return img
    
    def to_numpy(self, image):
        """Convert PIL image to numpy array for OpenCV processing."""
        return np.array(image)
