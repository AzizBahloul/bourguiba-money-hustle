import re
import platform
from loguru import logger

def extract_task_components(task_description):
    """Extract the main components from a task description"""
    task_lower = task_description.lower()
    
    # Common task patterns
    patterns = {
        'open_app': r'(?:open|launch|start|run)\s+([a-zA-Z0-9\s\-_\.]+)',
        'search_for': r'(?:search for|find|look for|google|search)\s+([a-zA-Z0-9\s\-_\.]+)',
        'navigate_to': r'(?:go to|navigate to|visit|open)\s+(?:website|page|url|site)?\s*(?:https?://)?([a-zA-Z0-9\s\-_\.]+\.[a-z]{2,}[a-zA-Z0-9\s\-_\./]*)',
        'type_text': r'(?:type|input|enter|write)\s+(?:the text|text|)?\s*["\']?([^"\']+)["\']?',
        'click_on': r'(?:click|press|select|choose)\s+(?:on|the)?["\']?([^"\']+)["\']?',
        'take_screenshot': r'(?:take|capture|grab)[a\s]+(?:screenshot|screen shot|screen capture|snapshot)',
        'create_file': r'(?:create|make|new)[a\s]+(?:file|document|doc)(?:\s+named|called)?\s+["\']?([^"\']+)["\']?',
    }
    
    # Extract components
    components = {}
    for component, pattern in patterns.items():
        match = re.search(pattern, task_lower)
        if match:
            components[component] = match.group(1).strip()
    
    # Detect if this is a compound task (multiple actions)
    actions = []
    
    # Split by "and", "then", "after that" to find multiple actions
    action_phrases = re.split(r'\s+(?:and|then|after that|afterwards|next)\s+', task_lower)
    
    if len(action_phrases) > 1:
        components['compound_task'] = True
        components['action_phrases'] = action_phrases
    
    logger.info(f"Extracted task components: {components}")
    return components

def get_fallback_plan(task_description, screen_description):
    """Generate a generic and adaptive fallback plan for any task"""
    
    # Extract components from the task description
    components = extract_task_components(task_description)
    steps = []
    
    # 1. Check for "open app" tasks
    if 'open_app' in components:
        app_name = components['open_app']
        logger.info(f"Detected 'open app' task for: {app_name}")
        
        # Combine with other actions if it's a compound task
        if 'search_for' in components and ('browser' in app_name or 'chrome' in app_name or 'firefox' in app_name):
            search_term = components['search_for']
            steps.extend([
                {
                    'number': 1,
                    'description': f'Launch {app_name}',
                    'details': [f'LAUNCH "{app_name}"']
                },
                {
                    'number': 2,
                    'description': 'Wait for browser to load',
                    'details': ['WAIT 3']
                },
                {
                    'number': 3,
                    'description': f'Type search term: {search_term}',
                    'details': [f'TYPE "{search_term}"']
                },
                {
                    'number': 4,
                    'description': 'Press Enter to search',
                    'details': ['PRESS "enter"', 'WAIT 1']
                }
            ])
        else:
            # Generic app launch
            steps.extend([
                {
                    'number': 1,
                    'description': f'Launch {app_name}',
                    'details': [f'LAUNCH "{app_name}"']
                },
                {
                    'number': 2,
                    'description': f'Wait for {app_name} to load',
                    'details': ['WAIT 2']
                }
            ])
    
    # 2. Check for search tasks without a specific app
    elif 'search_for' in components and not steps:
        search_term = components['search_for']
        logger.info(f"Detected search task for: {search_term}")
        steps.extend([
            {
                'number': 1,
                'description': 'Launch web browser',
                'details': ['LAUNCH_CHROME']
            },
            {
                'number': 2,
                'description': 'Wait for browser to load',
                'details': ['WAIT 3']
            },
            {
                'number': 3,
                'description': f'Type search term: {search_term}',
                'details': [f'TYPE "{search_term}"']
            },
            {
                'number': 4,
                'description': 'Press Enter to search',
                'details': ['PRESS "enter"', 'WAIT 1']
            }
        ])
    
    # 3. Check for navigation tasks
    elif 'navigate_to' in components and not steps:
        website = components['navigate_to']
        logger.info(f"Detected navigation task to: {website}")
        
        # Add https:// if not present and not containing www.
        if not website.startswith('www.') and not website.startswith('http'):
            website = f"www.{website}"
            
        steps.extend([
            {
                'number': 1,
                'description': 'Launch web browser',
                'details': ['LAUNCH_CHROME']
            },
            {
                'number': 2,
                'description': 'Wait for browser to load',
                'details': ['WAIT 3']
            },
            {
                'number': 3,
                'description': f'Type URL: {website}',
                'details': [f'TYPE "{website}"']
            },
            {
                'number': 4,
                'description': 'Press Enter to navigate',
                'details': ['PRESS "enter"', 'WAIT 1']
            }
        ])
        
    # 4. Check for typing tasks
    elif 'type_text' in components and not steps:
        text = components['type_text']
        logger.info(f"Detected typing task: {text}")
        steps.extend([
            {
                'number': 1,
                'description': f'Type text: {text[:20]}{"..." if len(text) > 20 else ""}',
                'details': [f'TYPE "{text}"']
            }
        ])
    
    # 5. Check for click tasks
    elif 'click_on' in components and not steps:
        element = components['click_on']
        logger.info(f"Detected click task on: {element}")
        steps.extend([
            {
                'number': 1,
                'description': f'Find and click on: {element}',
                'details': [f'CLICK_ELEMENT "{element}"']
            }
        ])
    
    # 6. Handle screenshot tasks
    elif 'take_screenshot' in components and not steps:
        logger.info("Detected screenshot task")
        steps.extend([
            {
                'number': 1,
                'description': 'Take screenshot',
                'details': ['SCREENSHOT']
            }
        ])
    
    # 7. Default generic task handler if no specific pattern was matched
    if not steps:
        # Look for potential app or action names in the task
        words = task_description.lower().split()
        common_apps = ['chrome', 'firefox', 'safari', 'edge', 'word', 'excel', 
                     'powerpoint', 'outlook', 'notepad', 'calculator', 'terminal', 
                     'code', 'vscode', 'spotify', 'discord', 'slack', 'explorer', 'settings']
        
        # Try to find an app name in the task
        app_name = None
        for app in common_apps:
            if app in words:
                app_name = app
                break
        
        # If found an app, assume it's a launch task
        if app_name:
            logger.info(f"Detected potential app in general task: {app_name}")
            steps.extend([
                {
                    'number': 1,
                    'description': f'Launch {app_name}',
                    'details': [f'LAUNCH "{app_name}"']
                },
                {
                    'number': 2,
                    'description': f'Wait for {app_name} to load',
                    'details': ['WAIT 2']
                }
            ])
        else:
            # Truly generic fallback: try to find something to click based on the task words
            logger.info("Using fully generic fallback plan")
            
            # Remove common words
            stop_words = ['the', 'a', 'an', 'and', 'or', 'but', 'if', 'then', 'else', 'when', 'at', 'from', 'by', 'for', 'with', 'about', 'to']
            important_words = [word for word in words if word not in stop_words and len(word) > 2]
            
            # Create click steps for any potentially meaningful terms
            if important_words:
                steps.append({
                    'number': 1,
                    'description': f'Look for elements matching task description',
                    'details': [f'CLICK_ELEMENT "{word}"' for word in important_words[:3]]
                })
            else:
                # Last resort: just try clicking on something that looks clickable
                steps.append({
                    'number': 1,
                    'description': 'Look for clickable elements',
                    'details': ['CLICK_ELEMENT "button"', 'CLICK_ELEMENT "menu"', 'CLICK_ELEMENT "icon"']
                })
    
    return steps
