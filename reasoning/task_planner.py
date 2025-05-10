from .ollama_client import OllamaClient
from .prompt_templates import PromptTemplates
from loguru import logger

class TaskPlanner:
    """Plans complex tasks by breaking them down into actionable steps."""
    
    def __init__(self, model="mistral:7b", use_gpu=False):
        self.ollama = OllamaClient(model=model, use_gpu=use_gpu)
        self.templates = PromptTemplates
    
    def _decompose_task(self, task_description):
        logger.info(f"Decomposing task: {task_description}")
        system_prompt = self.templates.BASE_SYSTEM_PROMPT
        user_prompt = self.templates.get_task_decomposition_prompt(task_description)
        
        response = self.ollama.generate(
            prompt=user_prompt,
            system_message=system_prompt,
            temperature=0.1
        )
        sub_tasks = [task.strip() for task in response.strip().split('\n') if task.strip()]
        if not sub_tasks or (len(sub_tasks) == 1 and sub_tasks[0].lower() == task_description.lower()):
            logger.info("Task is simple, no decomposition needed.")
            return [task_description]
        logger.info(f"Decomposed into sub-tasks: {sub_tasks}")
        return sub_tasks

    def _plan_sub_task(self, sub_task_description, original_task_description, screen_description):
        logger.info(f"Planning sub-task: {sub_task_description}")
        system_prompt = self.templates.BASE_SYSTEM_PROMPT
        user_prompt = self.templates.get_task_planning_prompt(
            sub_task_description,
            original_task_description,
            screen_description
        )
        
        tokens = []
        # Stream tokens for quicker response
        logger.info(f"Streaming plan tokens for sub-task '{sub_task_description}' from Ollama...")
        for chunk in self.ollama.stream_generate(
            prompt=user_prompt,
            system_message=system_prompt,
            temperature=0.2 # Slightly lower temp for more deterministic planning
        ):
            tokens.append(chunk)
        
        response = "".join(tokens)
        steps = self._parse_steps(response)
        if not steps:
            logger.warning(f"Empty plan received for sub-task '{sub_task_description}'.")
        return steps

    def plan_task(self, task_description, screen_description):
        sub_tasks = self._decompose_task(task_description)
        
        all_plans = []
        current_sub_task_number = 1
        for sub_task in sub_tasks:
            logger.info(f"Processing sub-task {current_sub_task_number}/{len(sub_tasks)}: {sub_task}")
            sub_task_plan = self._plan_sub_task(sub_task, task_description, screen_description)
            if sub_task_plan:
                for step in sub_task_plan:
                    step['description'] = f"Sub-task '{sub_task}': {step['description']}"
                all_plans.extend(sub_task_plan)
            else:
                logger.warning(f"Could not generate plan for sub-task: {sub_task}. Skipping.")
            current_sub_task_number += 1

        if not all_plans:
            logger.warning("No steps generated for any sub-task. Using generic fallback.")
            from .fallback_plans import get_fallback_plan
            all_plans = get_fallback_plan(task_description, screen_description)
        
        # Re-number steps sequentially
        for i, step in enumerate(all_plans):
            step['number'] = i + 1
            
        return all_plans
    
    def _parse_steps(self, plan_text):
        lines = plan_text.strip().split('\n')
        steps = []
        current_step = {}
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line[0].isdigit() and "." in line[:3]:
                if current_step:
                    steps.append(current_step)
                step_num = int(line[0])
                step_text = line[line.index('.')+1:].strip()
                current_step = {
                    'number': step_num,
                    'description': step_text,
                    'details': []
                }
            elif current_step:
                current_step['details'].append(line)
        if current_step:
            steps.append(current_step)
        return steps
