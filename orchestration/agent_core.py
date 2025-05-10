import time
import threading
from queue import Queue
import atexit
import concurrent.futures
import psutil
import os
from loguru import logger
import pyautogui

from perception.screen_analyzer import ScreenAnalyzer
from reasoning.ollama_client import OllamaClient
from reasoning.task_planner import TaskPlanner
from reasoning.decision_maker import DecisionMaker
from action.action_executor import ActionExecutor
from memory.context_manager import ContextManager
from memory.history_tracker import HistoryTracker

class AgentCore:
    """Core agent orchestration system that ties all components together."""
    
    def __init__(self, config):
        self.config = config
        self._init_components()
        self.is_running = False
        self.is_paused = False
        self.task_queue = Queue()
        # Add thread pool for parallel tasks
        cpu_count = psutil.cpu_count(logical=False) or 2  # Physical cores or fallback to 2
        self.thread_pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=max(2, cpu_count - 1),  # Leave one core free for system
            thread_name_prefix="agent_worker"
        )
        # Register shutdown handler
        atexit.register(self._cleanup_resources)
        logger.info(f"Agent core initialized with {cpu_count} CPUs")
    
    def _init_components(self):
        ollama_model = self.config.get("ollama_model", "mistral:7b")
        human_like   = self.config.get("human_like", True)
        tesseract_path = self.config.get("tesseract_path")
        use_gpu      = self.config.get("use_gpu", False)

        self.perception    = ScreenAnalyzer(tesseract_path)
        self.ollama        = OllamaClient(model=ollama_model, use_gpu=use_gpu)
        self.planner       = TaskPlanner(model=ollama_model, use_gpu=use_gpu)
        self.decision_maker= DecisionMaker(model=ollama_model, use_gpu=use_gpu)
        self.action_executor = ActionExecutor(human_like=human_like)
        self.context       = ContextManager()
        self.history       = HistoryTracker()
        logger.info(f"Components initialized with model {ollama_model}")
    
    def _cleanup_resources(self):
        """Clean up resources when process exits"""
        logger.info("Cleaning up resources...")
        if hasattr(self, 'perception'):
            if hasattr(self.perception, 'shutdown'):
                self.perception.shutdown()
        
        if hasattr(self, 'action_executor'):
            if hasattr(self.action_executor, 'shutdown'):
                self.action_executor.shutdown()
                
        if hasattr(self, 'thread_pool'):
            self.thread_pool.shutdown(wait=False)
            
        logger.info("Resource cleanup completed")
    
    def start(self):
        if self.is_running:
            logger.warning("Agent is already running")
            return False
        self.is_running = True
        self.is_paused = False
        self.agent_thread = threading.Thread(target=self._agent_loop)
        self.agent_thread.daemon = True
        self.agent_thread.start()
        logger.info("Agent started")
        return True
    
    def stop(self):
        if not self.is_running:
            logger.warning("Agent is not running")
            return False
        self.is_running = False
        if hasattr(self, 'agent_thread') and self.agent_thread.is_alive():
            self.agent_thread.join(timeout=2.0)
        self._cleanup_resources()
        logger.info("Agent stopped")
        return True
    
    def pause(self):
        self.is_paused = True
        logger.info("Agent paused")
        return True
    
    def resume(self):
        self.is_paused = False
        logger.info("Agent resumed")
        return True
    
    def execute_task(self, task_description):
        if not self.is_running:
            logger.error("Cannot execute task - agent is not running")
            return None
        self.task_queue.put(task_description)
        self.context.start_task(task_description)
        self.history.log_task(task_description)
        logger.info(f"Task submitted: {task_description}")
        return self.history.session_id
    
    def execute_parallel_tasks(self, task_descriptions):
        """Execute multiple tasks in parallel"""
        if not self.is_running:
            logger.error("Cannot execute tasks - agent is not running")
            return None
            
        futures = []
        for task in task_descriptions:
            self.context.start_task(task)
            self.history.log_task(task)
            futures.append(self.thread_pool.submit(self._process_task, task))
            
        return futures
    
    def _process_task(self, task_description):
        """Process a single task (for parallel execution)"""
        try:
            logger.info(f"Processing task: {task_description}")
            self.current_task = task_description
            success = self._process_current_task()
            self.history.log_task_completion(success)
            if success:
                self.context.set_task_completed()
            else:
                self.context.set_task_failed("Task execution failed")
            return success
        except Exception as e:
            logger.error(f"Error processing task: {str(e)}")
            return False
        finally:
            self.current_task = None
    
    def _agent_loop(self):
        try:
            logger.info("Agent loop started")
            while self.is_running:
                if self.is_paused:
                    time.sleep(0.5)
                    continue
                if self.task_queue.empty():
                    time.sleep(0.5)
                    continue
                self.current_task = self.task_queue.get()
                success = self._process_current_task()
                self.current_task = None
                self.history.log_task_completion(success)
                if success:
                    self.context.set_task_completed()
                else:
                    self.context.set_task_failed("Task execution failed")
                time.sleep(0.1)
        except Exception as e:
            logger.error(f"Error in agent loop: {str(e)}")
            self.is_running = False
        finally:
            logger.info("Agent loop terminated")
    
    def _process_current_task(self):
        try:
            logger.info("Step 1: Capturing and analyzing screen")
            # Clear any previous cached analysis
            self.perception.clear_cache()
            # Get a fresh analysis for planning
            analysis = self.perception.analyze_current_screen(force_new=True)
            self.context.add_screen(analysis['screenshot'], analysis)
            
            # No need to save _initial_analysis since we're now using caching

            logger.info("Step 2: Planning task")
            plan = self.planner.plan_task(self.current_task, analysis['raw_text'])
            logger.info(f"Step 2 done: received plan with {len(plan)} steps")
            if not plan:
                logger.error("Empty plan received – aborting task execution")
                return False
            self.context.set_plan(plan)
            return self._execute_plan()
        except Exception as e:
            logger.error(f"Error processing task: {str(e)}")
            return False
    
    def _execute_plan(self):
        plan = self.context.current_plan
        if not plan:
            logger.error("No plan to execute")
            return False

        total_steps = len(plan)
        logger.info(f"Executing plan with {total_steps} steps")
        plan_start = time.time()

        # Keep track of elements we've already clicked
        clicked_elements = set()

        for idx, step in enumerate(plan, start=1):
            # Log step start
            logger.info(f"Starting step {idx}/{total_steps}: {step['description']}")
            step_start = time.time()

            # Check for pause/stop
            if not self.is_running or self.is_paused:
                logger.info("Plan execution interrupted")
                return False

            # Fallback for steps with direct details
            details = step.get('details', [])
            if details:
                logger.info(f"Fallback step {step['number']}: executing direct commands")
                step_succeeded = False
                
                for detail in details:
                    # Handle WAIT commands
                    if detail.upper().startswith("WAIT"):
                        try:
                            duration = float(detail.split()[1]) if len(detail.split()) > 1 else 2
                        except (ValueError, IndexError):
                            duration = 2
                        
                        logger.info(f"Waiting for {duration} seconds")
                        time.sleep(duration)
                        # Mark this step as successful since we successfully waited
                        step_succeeded = True
                        continue
                    
                    elif detail.upper().startswith("CLICK "):
                        # Direct coordinates for clicking
                        try:
                            parts = detail.upper().split()
                            x, y = int(parts[1]), int(parts[2])
                            logger.info(f"Clicking at coordinates ({x}, {y})")
                            
                            # Execute click with verification
                            success = self.action_executor.mouse.move_to(x, y)
                            if not success:
                                logger.error(f"Failed to move to ({x}, {y})")
                                continue
                                
                            # Verify position before clicking
                            current_x, current_y = pyautogui.position()
                            logger.info(f"Current position before clicking: ({current_x}, {current_y})")
                            
                            success = self.action_executor.mouse.click(current_x, current_y)
                            if success:
                                logger.info(f"Successfully clicked at ({current_x}, {current_y})")
                                step_succeeded = True
                            else:
                                logger.error(f"Failed to click at ({current_x}, {current_y})")
                            continue
                        except Exception as e:
                            logger.error(f"Error executing direct click: {e}")
                            continue
                    
                    # Standard action parsing for other commands
                    action = self.decision_maker._parse_action(detail)
                    success, result = self.action_executor.execute_action(action)
                    self.context.add_action(action, success, result)
                    if success:
                        step_succeeded = True
                
                # If all attempts failed but this isn't the last step, continue to the next step
                if not step_succeeded and idx < len(plan):
                    logger.warning(f"Step {idx} failed but continuing with next step")
                    continue
                
                # If all attempts in the last step failed, report task failure
                if not step_succeeded and idx == len(plan):
                    logger.error(f"All fallback attempts failed in final step")
                    return False
                
                continue  # Move to next step
            
            # Use cached analysis for the first step and refresh for subsequent steps
            if idx > 1:
                # Only refresh the screen analysis for steps after the first
                self.perception.clear_cache()
            
            analysis = self.perception.analyze_current_screen()
            self.context.add_screen(analysis['screenshot'], analysis)
            
            action = self.decision_maker.decide_next_action(
                self.current_task,
                step['description'],
                analysis['raw_text']
            )

            # Execute action
            success, result = self.action_executor.execute_action(action)
            step_duration = time.time() - step_start
            logger.info(f"Step {idx}/{total_steps} {'succeeded' if success else 'failed'} in {step_duration:.2f}s: {result}")

            # Record history
            self.context.add_action(action, success, result)
            self.history.log_action(action, {"success": success, "result": result})

            # Handle failure
            if not success:
                error_handling_result = self.decision_maker.handle_error(
                    self.current_task,
                    action,
                    analysis['raw_text']
                )
                logger.info(f"Error handling suggestion: {error_handling_result}")
                if "RETRY" in error_handling_result.upper():
                    self.context.current_step_index = max(0, idx - 2)
                    continue
                else:
                    logger.error("Aborting plan due to unrecoverable error")
                    total_duration = time.time() - plan_start
                    logger.info(f"Plan aborted after {idx}/{total_steps} steps in {total_duration:.2f}s")
                    return False

            # After executing an action, clear the cached analysis
            # as the screen will change for the next step
            self.perception.clear_cache()

            # Brief pause before next step
            time.sleep(0.5)

        total_duration = time.time() - plan_start
        logger.info(f"Plan executed successfully in {total_duration:.2f}s")
        return True
    
    def get_status(self):
        status = {
            "running": self.is_running,
            "paused": self.is_paused,
            "task": self.current_task,
            "task_status": self.context.task_status if hasattr(self.context, 'task_status') else None
        }
        return status
