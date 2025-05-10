from .ollama_client import OllamaClient
from .prompt_templates import PromptTemplates

class DecisionMaker:
    """Makes decisions about what action to take based on screen state."""
    
    def __init__(self, model="mistral:7b", use_gpu=False):
        self.ollama = OllamaClient(model=model, use_gpu=use_gpu)
        self.templates = PromptTemplates
    
    def decide_next_action(self, task_description, current_step, screen_description):
        system_prompt = self.templates.BASE_SYSTEM_PROMPT
        user_prompt = self.templates.get_action_decision_prompt(
            task_description=task_description,
            current_step=current_step,
            screen_description=screen_description
        )
        response = self.ollama.generate(
            prompt=user_prompt,
            system_message=system_prompt,
            temperature=0.2
        )
        action = self._parse_action(response.strip())
        return action
    
    def handle_error(self, task_description, failed_action, screen_description):
        system_prompt = self.templates.BASE_SYSTEM_PROMPT
        user_prompt = self.templates.get_error_handling_prompt(
            task_description=task_description,
            failed_action=failed_action,
            screen_description=screen_description
        )
        response = self.ollama.generate(
            prompt=user_prompt,
            system_message=system_prompt,
            temperature=0.4
        )
        return response
    
    def _parse_action(self, action_text):
        action = action_text.strip().upper()
        if action.startswith("CLICK"):
            parts = action.split()
            if len(parts) >= 3:
                try:
                    x, y = int(parts[1]), int(parts[2])
                    return {"type": "click", "x": x, "y": y}
                except ValueError:
                    pass
        elif action.startswith("TYPE"):
            text_match = action[4:].strip()
            if text_match.startswith('"') and text_match.endswith('"'):
                text = text_match[1:-1]
                return {"type": "type", "text": text}
            else:
                return {"type": "type", "text": text_match}
        elif action.startswith("PRESS"):
            key_match = action[5:].strip()
            if key_match.startswith('"') and key_match.endswith('"'):
                key = key_match[1:-1].lower()   # force lowercase
            else:
                key = key_match.lower()
            return {"type": "press", "key": key}
        elif action.startswith("WAIT"):
            # Extract duration if provided, otherwise default to 2 seconds
            try:
                duration = float(action.split()[1]) if len(action.split()) > 1 else 2
            except (ValueError, IndexError):
                duration = 2
            return {"type": "wait", "duration": duration}
        elif action.startswith("SCROLL"):
            direction = "down"
            if "UP" in action:
                direction = "up"
            return {"type": "scroll", "direction": direction}
        elif action.startswith("RUN"):
            cmd = action[3:].strip()
            if cmd.startswith('"') and cmd.endswith('"'):
                cmd = cmd[1:-1]
            return {"type": "run", "cmd": cmd}
        elif action.startswith("LAUNCH"):
            app = action[6:].strip()
            if app.startswith('"') and app.endswith('"'):
                app = app[1:-1]
            if 'CHROME' in app.upper():
                return {"type": "launch_chrome"}
            else:
                return {"type": "launch", "app": app}
        return {"type": "unknown", "raw": action_text}
