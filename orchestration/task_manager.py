class TaskManager:
    """Manages the list of tasks and their statuses."""
    
    def __init__(self):
        self.tasks = []
    
    def add_task(self, task_description):
        task = {"description": task_description, "status": "pending"}
        self.tasks.append(task)
        return task
    
    def update_task(self, task, status):
        task["status"] = status
    
    def get_pending_tasks(self):
        return [t for t in self.tasks if t["status"] == "pending"]
