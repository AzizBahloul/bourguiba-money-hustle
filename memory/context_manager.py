import time
import json
from collections import deque
from loguru import logger

class ContextManager:
    """Manages context for task execution."""
    
    def __init__(self, max_history=20):
        self.current_task = None
        self.task_status = "idle"
        self.start_time = None
        self.end_time = None
        self.screen_history = deque(maxlen=max_history)
        self.action_history = deque(maxlen=max_history)
        self.current_plan = []
        self.current_step_index = -1
        self.task_context = {}
    
    def start_task(self, task_description):
        self.current_task = task_description
        self.task_status = "in_progress"
        self.start_time = time.time()
        self.end_time = None
        self.current_plan = []
        self.current_step_index = -1
        self.task_context = {}
        self.screen_history.clear()
        self.action_history.clear()
        logger.info(f"Started task: {task_description}")
    
    def set_plan(self, plan):
        self.current_plan = plan
        self.current_step_index = 0 if plan else -1
        logger.info(f"Set plan with {len(plan)} steps")
    
    def next_step(self):
        if self.current_step_index < len(self.current_plan) - 1:
            self.current_step_index += 1
            return self.current_plan[self.current_step_index]
        else:
            return None
    
    def get_current_step(self):
        if 0 <= self.current_step_index < len(self.current_plan):
            return self.current_plan[self.current_step_index]
        else:
            return None
    
    def add_screen(self, screenshot, analysis):
        timestamp = time.time()
        self.screen_history.append({
            'timestamp': timestamp,
            'screenshot': screenshot,
            'analysis': analysis
        })
    
    def add_action(self, action, success, result):
        timestamp = time.time()
        self.action_history.append({
            'timestamp': timestamp,
            'action': action,
            'success': success,
            'result': result
        })
    
    def get_recent_screens(self, count=1):
        return list(self.screen_history)[-count:]
    
    def get_recent_actions(self, count=5):
        return list(self.action_history)[-count:]
    
    def set_task_completed(self):
        self.task_status = "completed"
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        logger.info(f"Task completed in {duration:.2f} seconds")
    
    def set_task_failed(self, reason):
        self.task_status = "failed"
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        logger.error(f"Task failed after {duration:.2f} seconds. Reason: {reason}")
    
    def get_task_summary(self):
        if not self.current_task:
            return {"status": "No task in progress"}
        summary = {
            "task": self.current_task,
            "status": self.task_status
        }
        if self.start_time:
            if self.end_time:
                duration = self.end_time - self.start_time
                summary["duration"] = f"{duration:.2f} seconds"
            else:
                duration = time.time() - self.start_time
                summary["elapsed"] = f"{duration:.2f} seconds"
        if self.action_history:
            total_actions = len(self.action_history)
            successful_actions = sum(1 for a in self.action_history if a['success'])
            summary["actions"] = {
                "total": total_actions,
                "successful": successful_actions,
                "failed": total_actions - successful_actions
            }
        if self.current_plan:
            summary["plan"] = {
                "total_steps": len(self.current_plan),
                "completed_steps": self.current_step_index + 1 if self.current_step_index >= 0 else 0,
                "current_step": self.current_step_index + 1 if self.current_step_index >= 0 else None
            }
        return summary
    
    def save_to_file(self, filename):
        serializable = {
            "task": self.current_task,
            "status": self.task_status,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "plan": self.current_plan,
            "current_step": self.current_step_index,
            "task_context": self.task_context,
            "actions": [
                {
                    "timestamp": a["timestamp"],
                    "action": a["action"],
                    "success": a["success"],
                    "result": a["result"]
                } for a in self.action_history
            ]
        }
        try:
            with open(filename, 'w') as f:
                json.dump(serializable, f, indent=2)
            logger.info(f"Context saved to {filename}")
            return True
        except Exception as e:
            logger.error(f"Error saving context: {str(e)}")
            return False
