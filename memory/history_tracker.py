import time
import json
import os
from datetime import datetime
from loguru import logger

class HistoryTracker:
    """Tracks and logs agent activity over time."""
    
    def __init__(self, log_dir="logs"):
        self.log_dir = log_dir
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_log = []
        os.makedirs(log_dir, exist_ok=True)
        self.start_session()
    
    def start_session(self):
        self.session_start_time = time.time()
        self.session_log = []
        self.log_event("session_start", {
            "session_id": self.session_id,
            "timestamp": self.session_start_time
        })
        logger.info(f"Started session {self.session_id}")
    
    def end_session(self):
        self.session_end_time = time.time()
        duration = self.session_end_time - self.session_start_time
        self.log_event("session_end", {
            "session_id": self.session_id,
            "timestamp": self.session_end_time,
            "duration": duration
        })
        self.save_session_log()
        logger.info(f"Ended session {self.session_id} (duration: {duration:.2f}s)")
    
    def log_event(self, event_type, data=None):
        timestamp = time.time()
        event = {
            "type": event_type,
            "timestamp": timestamp,
            "datetime": datetime.fromtimestamp(timestamp).isoformat()
        }
        if data:
            event["data"] = data
        self.session_log.append(event)
    
    def log_task(self, task_description):
        self.log_event("task_start", {
            "description": task_description
        })
    
    def log_task_completion(self, success, details=None):
        self.log_event("task_end", {
            "success": success,
            "details": details
        })
    
    def log_action(self, action, result):
        self.log_event("action", {
            "action": action,
            "result": result
        })
    
    def log_error(self, error_type, details):
        self.log_event("error", {
            "error_type": error_type,
            "details": details
        })
    
    def log_observation(self, observation_type, details):
        self.log_event("observation", {
            "observation_type": observation_type,
            "details": details
        })
    
    def save_session_log(self):
        filename = os.path.join(self.log_dir, f"session_{self.session_id}.json")
        try:
            with open(filename, 'w') as f:
                json.dump(self.session_log, f, indent=2)
            logger.info(f"Session log saved to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error saving session log: {str(e)}")
            return None
    
    def get_session_stats(self):
        event_counts = {}
        for event in self.session_log:
            event_type = event["type"]
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        action_events = [e for e in self.session_log if e["type"] == "action"]
        successful_actions = sum(1 for e in action_events if e.get("data", {}).get("result", {}).get("success", False))
        action_success_rate = successful_actions / len(action_events) if action_events else 0
        stats = {
            "session_id": self.session_id,
            "event_counts": event_counts,
            "action_success_rate": action_success_rate,
            "total_events": len(self.session_log)
        }
        if hasattr(self, "session_start_time"):
            duration = time.time() - self.session_start_time
            stats["duration"] = duration
        return stats
