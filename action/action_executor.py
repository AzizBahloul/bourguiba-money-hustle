from .mouse_control import MouseController
from .keyboard_control import KeyboardController
from .launcher import AppLauncher
import subprocess
import time
import concurrent.futures
import pyautogui
from queue import Queue
import threading
from loguru import logger

class ActionExecutor:
    """High-level action execution combining mouse and keyboard controls."""
    
    def __init__(self, human_like=True, max_workers=3):
        self.mouse = MouseController(human_like)
        self.keyboard = KeyboardController(human_like)
        self.launcher = AppLauncher()  # Add the launcher
        # Create thread pool for non-blocking action execution
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self.pending_actions = Queue()
        self.action_results = {}
        self.action_counter = 0
        self.lock = threading.RLock()
    
    def execute_action(self, action):
        action_type = action.get('type', '').lower()
        try:
            if action_type == 'click':
                x, y = action.get('x'), action.get('y')
                self.mouse.click(x, y)
                return True, f"Clicked at ({x}, {y})"
            elif action_type == 'type':
                text = action.get('text', '')
                self.keyboard.type_text(text)
                return True, f"Typed text: {text[:20]}{'...' if len(text) > 20 else ''}"
            elif action_type == 'press':
                key = action.get('key', '')
                if '+' in key:
                    keys = [k.strip() for k in key.split('+')]
                    self.keyboard.hotkey(*keys)
                    return True, f"Pressed hotkey: {key}"
                else:
                    self.keyboard.press_key(key)
                    return True, f"Pressed key: {key}"
            elif action_type == 'wait':
                duration = action.get('duration', 2)
                logger.info(f"Waiting for {duration} seconds")
                time.sleep(duration)
                return True, f"Waited for {duration} seconds"
            elif action_type == 'scroll':
                direction = action.get('direction', 'down')
                clicks = action.get('clicks', 3)
                self.mouse.scroll(direction, clicks)
                return True, f"Scrolled {direction} {clicks} clicks"
            elif action_type == 'double_click':
                x, y = action.get('x'), action.get('y')
                self.mouse.double_click(x, y)
                return True, f"Double-clicked at ({x}, {y})"
            elif action_type == 'right_click':
                x, y = action.get('x'), action.get('y')
                self.mouse.right_click(x, y)
                return True, f"Right-clicked at ({x}, {y})"
            elif action_type == 'drag':
                x1, y1 = action.get('start_x'), action.get('start_y')
                x2, y2 = action.get('end_x'), action.get('end_y')
                self.mouse.drag_to(x1, y1, x2, y2)
                return True, f"Dragged from ({x1}, {y1}) to ({x2}, {y2})"
            elif action_type == 'run':
                cmd = action.get('cmd')
                subprocess.Popen(cmd, shell=True)
                return True, f"Ran command: {cmd}"
            elif action_type == 'launch':
                app_name = action.get('app', '')
                success = self.launcher.launch_app(app_name)
                return success, f"Launched app: {app_name}" if success else f"Failed to launch: {app_name}"
            elif action_type == 'launch_chrome':
                success = self.launcher.launch_chrome()
                return success, "Launched Chrome" if success else "Failed to launch Chrome"
            elif action_type == 'screenshot':
                from datetime import datetime
                import os
                
                # Create a directory for screenshots if it doesn't exist
                screenshots_dir = "screenshots"
                os.makedirs(screenshots_dir, exist_ok=True)
                
                # Generate filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = os.path.join(screenshots_dir, f"screenshot_{timestamp}.png")
                
                # Take the screenshot
                screenshot = self.mouse.screen_capture.capture_screen() if hasattr(self.mouse, 'screen_capture') else pyautogui.screenshot()
                screenshot.save(filename)
                
                return True, f"Saved screenshot to {filename}"
            else:
                logger.warning(f"Unknown action type: {action_type}")
                return False, f"Unknown action type: {action_type}"
        except Exception as e:
            logger.error(f"Error executing action {action_type}: {str(e)}")
            return False, f"Error: {str(e)}"
    
    def execute_action_async(self, action):
        """Execute an action asynchronously and return a future"""
        with self.lock:
            action_id = self.action_counter
            self.action_counter += 1
            
        future = self.executor.submit(self.execute_action, action)
        self.action_results[action_id] = future
        return action_id, future
    
    def get_action_result(self, action_id):
        """Get the result of an asynchronous action"""
        if action_id in self.action_results:
            future = self.action_results[action_id]
            if future.done():
                result = future.result()
                # Clean up completed actions
                del self.action_results[action_id]
                return True, result
            return False, None
        return False, "Action ID not found"
    
    def execute_sequence(self, actions, delay_between=0.5, parallel=False):
        """Execute a sequence of actions, optionally in parallel"""
        if not parallel:
            # Original sequential execution
            results = []
            for i, action in enumerate(actions):
                logger.info(f"Executing action {i+1}/{len(actions)}: {action}")
                success, output = self.execute_action(action)
                results.append((success, output))
                if not success:
                    logger.error(f"Action sequence aborted at step {i+1} due to failure")
                    break
                if i < len(actions) - 1:
                    time.sleep(delay_between)
            return results
        else:
            # New parallel execution
            futures = []
            for action in actions:
                futures.append(self.executor.submit(self.execute_action, action))
                time.sleep(delay_between)  # Small delay to prevent race conditions
            
            return [future.result() for future in concurrent.futures.as_completed(futures)]
    
    def shutdown(self):
        """Clean up resources properly"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
