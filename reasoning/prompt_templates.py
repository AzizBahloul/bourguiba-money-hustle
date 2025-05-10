class PromptTemplates:
    """Collection of prompt templates for different agent tasks."""
    
    BASE_SYSTEM_PROMPT = """You are an AI agent that can control a computer to complete tasks. 
You see the screen through OCR text and UI element analysis.
Your goal is to help the user complete their task by breaking it down into precise, actionable steps.
Always think step-by-step. Provide clear reasoning for your actions.
Actions must be one of: CLICK X Y, TYPE "text", PRESS "key", WAIT DURATION_SECONDS, SCROLL "direction".
Coordinates are 0,0 top-left. Screen size is typically 1920x1080 but can vary.
"""

    TASK_DECOMPOSITION_PROMPT = """Given the user's request: "{task_description}"
Break this down into a sequence of smaller, distinct sub-tasks that need to be performed in order.
List each sub-task on a new line.
If the task is already simple and cannot be broken down further, return the original task description on a single line.
Example:
User request: "Open Chrome, go to google.com, and search for 'best AI tools'"
Sub-tasks:
Open Chrome
Navigate to google.com
Search for 'best AI tools'

User request: "Take a screenshot"
Sub-tasks:
Take a screenshot
"""

    SCREEN_ANALYSIS_PROMPT = """Analyze the current screen and describe:
1. What application is visible
2. Key UI elements visible (buttons, fields, menus)
3. What text content is visible
4. Where the user's attention should be focused

Description of current screen state:
{screen_text}

Think carefully about what this screen represents and what actions would be appropriate.
"""

    TASK_PLANNING_PROMPT = """I need to accomplish the following sub-task:
{sub_task_description}

The overall goal is:
{original_task_description}

Current screen analysis:
{screen_description}

Break this sub-task down into 1-5 precise, executable steps.
For each step, specify THE EXACT ACTION to take:
1. CLICK X Y (e.g., CLICK 100 250) - Determine X,Y from screen_description. If an app or element is not visible, your first steps should be to find and open it (e.g., click app menu, type app name, click app icon).
2. TYPE "text to type" (e.g., TYPE "hello world")
3. PRESS "key" (e.g., PRESS "enter", PRESS "ctrl+a", PRESS "super" for Windows/Cmd key)
4. WAIT D (e.g., WAIT 2.5) - Wait for D seconds.
5. SCROLL "direction" (e.g., SCROLL "down")

Provide a numbered list of actions. Each action MUST be on a new line.
Example:
1. CLICK 50 1050 (to open start menu)
2. WAIT 1
3. TYPE "notepad"
4. WAIT 1
5. PRESS "enter"
"""

    ACTION_DECISION_PROMPT = """Current sub-task: {current_step_description} (Part of overall task: {task_description})
Screen analysis: {screen_description}

What is the SINGLE EXACT next action to perform to achieve the sub-task?
Choose ONE action from:
1. CLICK X Y (e.g., CLICK 100 250) - Determine X,Y from screen_description. If a target is an icon or non-text element, estimate its center X,Y.
2. TYPE "text to type" (e.g., TYPE "hello world")
3. PRESS "key" (e.g., PRESS "enter", PRESS "tab", PRESS "ctrl+c", PRESS "super")
4. WAIT D (e.g., WAIT 2) - Wait for D seconds.
5. SCROLL "direction" (e.g., SCROLL "down")

Provide ONLY the action line, with no extra explanation.
If the sub-task seems complete based on the screen, you can output: TASK_COMPLETE
If you are stuck or cannot determine the next action, output: CANNOT_PROCEED
"""

    ERROR_HANDLING_PROMPT = """I encountered an issue while trying to complete the task.

Current task: {task_description}
Action attempted: {failed_action}
Current screen state: {screen_description}

What went wrong and what should I do next? Provide:
1. Analysis of what might have gone wrong
2. Alternative approach to try
3. Specific next action to take
"""

    @classmethod
    def get_screen_analysis_prompt(cls, screen_text):
        return cls.SCREEN_ANALYSIS_PROMPT.format(screen_text=screen_text)
    
    @classmethod
    def get_task_decomposition_prompt(cls, task_description):
        return cls.TASK_DECOMPOSITION_PROMPT.format(task_description=task_description)

    @classmethod
    def get_task_planning_prompt(cls, sub_task_description, original_task_description, screen_description):
        return cls.TASK_PLANNING_PROMPT.format(
            sub_task_description=sub_task_description,
            original_task_description=original_task_description,
            screen_description=screen_description
        )

    @classmethod
    def get_action_decision_prompt(cls, task_description, current_step_description, screen_description):
        return cls.ACTION_DECISION_PROMPT.format(
            task_description=task_description,
            current_step_description=current_step_description,
            screen_description=screen_description
        )
    
    @classmethod
    def get_error_handling_prompt(cls, task_description, failed_action, screen_description):
        return cls.ERROR_HANDLING_PROMPT.format(
            task_description=task_description,
            failed_action=failed_action,
            screen_description=screen_description
        )
