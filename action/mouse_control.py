import pyautogui
import time
import random
import os
import platform
import subprocess
from loguru import logger

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.3  # Increased from 0.1 for more reliability

class MouseController:
    """Handles mouse movements and clicks."""
    
    def __init__(self, human_like=True):
        self.human_like = human_like
        try:
            self.screen_width, self.screen_height = pyautogui.size()
            logger.info(f"Screen size: {self.screen_width}x{self.screen_height}")
            
            # Check if we can control the mouse
            self._check_permissions()
        except Exception as e:
            logger.error(f"Error initializing mouse controller: {e}")
            self.screen_width, self.screen_height = 1920, 1080  # Default fallback
    
    def _check_permissions(self):
        """Check if we have permission to control mouse/keyboard"""
        system = platform.system()
        if system == "Linux":
            # Check X11 or Wayland
            display_server = os.environ.get("XDG_SESSION_TYPE", "unknown")
            logger.info(f"Running on Linux with {display_server} display server")
            if display_server == "wayland":
                logger.warning("Wayland detected - mouse control might be limited")
            
            # Check for X11 permissions
            try:
                current_pos = pyautogui.position()
                logger.info(f"Current mouse position: {current_pos}")
            except Exception as e:
                logger.error(f"Cannot access mouse position: {e}")
                raise Exception(f"Mouse control not available: {e}")
    
    def move_to(self, x, y, duration=0.5):
        """Move mouse to specified coordinates"""
        try:
            x = max(0, min(x, self.screen_width - 1))
            y = max(0, min(y, self.screen_height - 1))
            
            # Log current position first
            current_x, current_y = pyautogui.position()
            logger.debug(f"Moving mouse from ({current_x}, {current_y}) to ({x}, {y})")
            
            # More human-like movement
            if self.human_like:
                # Add a small wiggle for more natural movement
                x_jitter = random.uniform(-2, 2)
                y_jitter = random.uniform(-2, 2)
                duration_jitter = random.uniform(-0.1, 0.1)
                adjusted_duration = max(0.3, duration + duration_jitter)  # Min 0.3 sec
                
                # Move in two steps for more natural trajectory
                mid_x = current_x + (x - current_x) * 0.6 + random.uniform(-10, 10)
                mid_y = current_y + (y - current_y) * 0.6 + random.uniform(-10, 10)
                
                # Keep midpoint within screen bounds
                mid_x = max(0, min(mid_x, self.screen_width - 1))
                mid_y = max(0, min(mid_y, self.screen_height - 1))
                
                # Execute two-step movement
                pyautogui.moveTo(mid_x, mid_y, duration=adjusted_duration/2)
                pyautogui.moveTo(x + x_jitter, y + y_jitter, duration=adjusted_duration/2)
            else:
                pyautogui.moveTo(x, y, duration=duration)
                
            # Verify position after move
            final_x, final_y = pyautogui.position()
            logger.debug(f"Mouse moved to ({final_x}, {final_y})")
            
            # Small pause after movement
            time.sleep(0.2)
            return True
        except Exception as e:
            logger.error(f"Failed to move mouse: {e}")
            return False
    
    def click(self, x=None, y=None, button='left', clicks=1):
        """Click at the specified coordinates"""
        try:
            if x is not None and y is not None:
                if not self.move_to(x, y):
                    logger.error("Click failed because mouse movement failed")
                    return False
            
            # Now click
            for i in range(clicks):
                logger.debug(f"Clicking mouse button: {button} (click {i+1}/{clicks})")
                pyautogui.click(button=button)
                if clicks > 1 and self.human_like:
                    time.sleep(random.uniform(0.08, 0.15))
            
            logger.debug(f"{button.capitalize()} clicked at position {pyautogui.position()}")
            
            # Small pause after clicking to ensure the click registers
            time.sleep(0.3)
            return True
        except Exception as e:
            logger.error(f"Failed to click mouse: {e}")
            # Try alternative click method on Linux if normal click fails
            if platform.system() == "Linux":
                try:
                    logger.info("Attempting alternative click method...")
                    if x is not None and y is not None:
                        cmd = f"xdotool mousemove {int(x)} {int(y)} click {1 if button=='left' else 3}"
                        subprocess.run(cmd, shell=True)
                        logger.info(f"Alternative click executed: {cmd}")
                        return True
                except Exception as e2:
                    logger.error(f"Alternative click method failed: {e2}")
            return False
    
    def double_click(self, x=None, y=None):
        self.click(x, y, clicks=2)
    
    def right_click(self, x=None, y=None):
        self.click(x, y, button='right')
    
    def drag_to(self, x1, y1, x2, y2, duration=1.0):
        self.move_to(x1, y1)
        pyautogui.dragTo(x2, y2, duration=duration, button='left')
        logger.debug(f"Dragged from ({x1}, {y1}) to ({x2}, {y2})")
    
    def scroll(self, direction='down', clicks=3):
        amount = clicks * 100
        if direction.lower() == 'up':
            pyautogui.scroll(amount)
        else:
            pyautogui.scroll(-amount)
        logger.debug(f"Scrolled {direction} {clicks} clicks")
