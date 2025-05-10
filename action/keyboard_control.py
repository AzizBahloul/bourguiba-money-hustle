import pyautogui
import time
import random
from loguru import logger

class KeyboardController:
    """Handles keyboard typing and shortcuts."""
    
    def __init__(self, human_like=True):
        self.human_like = human_like
    
    def type_text(self, text, interval=0.05):
        if not text:
            logger.warning("Empty text provided to type_text")
            return
        logger.debug(f"Typing text: {text[:20]}{'...' if len(text) > 20 else ''}")
        if self.human_like:
            for char in text:
                base_interval = interval * 1.5 if char in '.,!?;:' else interval
                adjusted_interval = base_interval * random.uniform(0.8, 1.2)
                pyautogui.write(char)
                time.sleep(adjusted_interval)
        else:
            pyautogui.write(text, interval=interval)
    
    def press_key(self, key):
        logger.debug(f"Pressing key: {key}")
        pyautogui.press(key)
    
    def hotkey(self, *keys):
        key_str = '+'.join(keys)
        logger.debug(f"Pressing hotkey: {key_str}")
        pyautogui.hotkey(*keys)
    
    def select_all(self):
        self.hotkey('ctrl', 'a')
    
    def copy(self):
        self.hotkey('ctrl', 'c')
    
    def paste(self):
        self.hotkey('ctrl', 'v')
    
    def cut(self):
        self.hotkey('ctrl', 'x')
    
    def undo(self):
        self.hotkey('ctrl', 'z')
    
    def delete(self):
        self.press_key('delete')
    
    def backspace(self, count=1):
        for _ in range(count):
            self.press_key('backspace')
            if count > 1 and self.human_like:
                time.sleep(random.uniform(0.05, 0.1))
