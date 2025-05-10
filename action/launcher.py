import platform
import os
import subprocess
import time
import re
import shutil
from loguru import logger

class AppLauncher:
    """Platform-specific application launcher with robust app detection"""
    
    # Common app command variations
    APP_COMMANDS = {
        'vscode': ['code', 'vscode', 'visual-studio-code', 'visual studio code', 'vs code'],
        'chrome': ['google-chrome', 'google-chrome-stable', 'chrome', 'chromium-browser', 'chromium'],
        'firefox': ['firefox', 'mozilla-firefox'],
        'terminal': ['gnome-terminal', 'konsole', 'terminal', 'xterm', 'cmd.exe', 'terminal.app'],
        'calculator': ['gnome-calculator', 'kcalc', 'calc', 'calculator'],
        'notepad': ['gedit', 'kate', 'notepad', 'notepad.exe', 'notepad++', 'notepad-plus-plus'],
        'file manager': ['nautilus', 'dolphin', 'thunar', 'explorer.exe', 'finder'],
        'spotify': ['spotify'],
        'discord': ['discord'],
        'slack': ['slack'],
        'zoom': ['zoom'],
        'skype': ['skype'],
        'vlc': ['vlc'],
        'microsoft word': ['microsoft-word', 'word', 'winword', 'libreoffice --writer'],
        'microsoft excel': ['microsoft-excel', 'excel', 'libreoffice --calc'],
        'microsoft powerpoint': ['microsoft-powerpoint', 'powerpoint', 'libreoffice --impress'],
        'paint': ['mspaint', 'pinta', 'krita', 'gimp'],
        'settings': ['gnome-control-center', 'systemsettings5', 'control panel']
    }
    
    def __init__(self):
        self.platform = platform.system().lower()
        self.display_server = os.environ.get('XDG_SESSION_TYPE', 'unknown') if self.platform == 'linux' else None
        logger.info(f"AppLauncher initialized for {self.platform} platform")
        
        # Try to detect installed applications
        self.available_commands = self._detect_available_commands()
        
    def _detect_available_commands(self):
        """Detect which commands are available on the system"""
        available = {}
        
        for app, commands in self.APP_COMMANDS.items():
            for cmd in commands:
                # Check if the command exists in PATH
                if shutil.which(cmd.split()[0]):
                    if app not in available:
                        available[app] = []
                    available[app].append(cmd)
                    logger.debug(f"Found command for {app}: {cmd}")
        
        logger.info(f"Detected {len(available)} available applications")
        return available
    
    def _normalize_app_name(self, app_name):
        """Normalize application name for better matching"""
        app_name = app_name.lower().strip()
        app_name = re.sub(r'\s+', ' ', app_name)  # Normalize whitespace
        
        # Try direct matches first
        for app, commands in self.APP_COMMANDS.items():
            if app == app_name:
                return app
            
            # Check for command variations
            for cmd in commands:
                if cmd == app_name or cmd.replace('-', ' ') == app_name:
                    return app
        
        # Try partial matches
        for app, commands in self.APP_COMMANDS.items():
            if app in app_name or app_name in app:
                return app
                
            # Check command variations for partial matches
            for cmd in commands:
                cmd_norm = cmd.replace('-', ' ')
                if cmd in app_name or app_name in cmd or cmd_norm in app_name or app_name in cmd_norm:
                    return app
        
        # No match found, return original
        return app_name
    
    def _get_launch_commands(self, app_name):
        """Get possible launch commands for an application"""
        # Normalize app name
        normalized = self._normalize_app_name(app_name)
        
        # Check if we have direct commands for this app
        if normalized in self.available_commands:
            return self.available_commands[normalized]
        
        # If not found in available commands, try the APP_COMMANDS list
        if normalized in self.APP_COMMANDS:
            return self.APP_COMMANDS[normalized]
            
        # Special case for VSCode
        if any(term in normalized for term in ['code', 'vscode', 'vs code', 'visual studio']):
            return self.APP_COMMANDS.get('vscode', ['code', 'vscode'])
            
        # Last resort: try the app name itself
        return [app_name]
        
    def launch_app(self, app_name):
        """Launch any application by name with fallbacks"""
        if not app_name or len(app_name.strip()) == 0:
            logger.error("Empty app name provided")
            return False
            
        logger.info(f"Attempting to launch application: {app_name}")
        
        # Special cases
        if 'chrome' in app_name.lower() or 'browser' in app_name.lower() and 'google' in app_name.lower():
            return self.launch_chrome()
            
        # Get all possible commands for this app
        commands = self._get_launch_commands(app_name)
        logger.info(f"Found {len(commands)} possible commands for {app_name}: {commands}")
        
        # Try each command
        for cmd in commands:
            try:
                logger.info(f"Trying to launch with command: {cmd}")
                
                if self.platform == 'windows':
                    process = subprocess.Popen(f"start {cmd}", shell=True)
                elif self.platform == 'darwin':  # macOS
                    process = subprocess.Popen(['open', '-a', cmd])
                else:  # Linux
                    if " " in cmd:
                        process = subprocess.Popen(cmd, shell=True)
                    else:
                        process = subprocess.Popen([cmd])
                        
                logger.info(f"Launched {app_name} with command: {cmd}")
                time.sleep(1)  # Brief pause to allow app to start
                return True
                
            except Exception as e:
                logger.warning(f"Failed to launch {app_name} with command {cmd}: {e}")
                
        # If we get here, all commands failed
        logger.error(f"Failed to launch {app_name} after trying all commands")
        return False
        
    def launch_chrome(self):
        """Launch Google Chrome browser with platform-specific commands"""
        logger.info(f"Attempting to launch Chrome on {self.platform}")
        
        success = False
        
        # Try specific command for Chrome
        if 'chrome' in self.available_commands:
            for cmd in self.available_commands['chrome']:
                try:
                    logger.info(f"Launching Chrome with detected command: {cmd}")
                    if " " in cmd:
                        subprocess.Popen(f"{cmd} https://www.google.com", shell=True)
                    else:
                        subprocess.Popen([cmd, "https://www.google.com"])
                    success = True
                    time.sleep(2)
                    break
                except Exception as e:
                    logger.warning(f"Failed to launch Chrome with {cmd}: {e}")
                    
        # If that didn't work, try platform-specific methods
        if not success:
            try:
                if self.platform == 'linux':
                    commands = [
                        ['google-chrome', 'https://www.google.com'],
                        ['google-chrome-stable', 'https://www.google.com'],
                        ['chromium-browser', 'https://www.google.com'],
                        ['chromium', 'https://www.google.com'],
                        ['firefox', 'https://www.google.com'],  # Fallback to Firefox
                        ['xdg-open', 'https://www.google.com']  # Last resort
                    ]
                    
                    for cmd in commands:
                        try:
                            subprocess.Popen(cmd)
                            success = True
                            time.sleep(2)
                            break
                        except Exception as e:
                            logger.warning(f"Failed with command {cmd}: {e}")
                            
                elif self.platform == 'darwin':
                    subprocess.Popen(['open', '-a', 'Google Chrome', 'https://www.google.com'])
                    success = True
                    time.sleep(2)
                    
                elif self.platform == 'windows':
                    subprocess.Popen(['start', 'chrome', 'https://www.google.com'], shell=True)
                    success = True
                    time.sleep(2)
            except Exception as e:
                logger.warning(f"Failed with platform-specific Chrome launch: {e}")
                
        # Last resort: system command
        if not success:
            try:
                if self.platform == 'windows':
                    os.system('start https://www.google.com')
                elif self.platform == 'darwin':
                    os.system('open https://www.google.com')
                else:
                    os.system('xdg-open https://www.google.com')
                logger.info("Launched default browser with Google URL")
                success = True
                time.sleep(2)
            except Exception as e:
                logger.error(f"All Chrome launch methods failed: {e}")
                
        return success
