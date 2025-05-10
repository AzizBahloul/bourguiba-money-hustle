# bourguiba-money-hustle

This project demonstrates an AI agent system that uses computer vision,
LLM reasoning, and computer control to automate complex tasks.

## Overview

The system is organized into the following components:
- **Perception:** Captures and processes the screen (via OCR and UI element detection).
- **Reasoning:** Uses prompt templates and a LLM (e.g., Ollama) to plan and decide actions.
- **Action:** Executes tasks using simulated mouse and keyboard inputs.
- **Memory:** Maintains context and logs actions.
- **Orchestration:** Ties all modules together for complete task automation.

## Installation

1. Create and activate a Python virtual environment.
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
   On Windows:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```
2. Install dependencies listed in `requirements.txt`.
   ```bash
   pip install -r requirements.txt
   ```
3. Configure your environment (see `orchestration/config_manager.py`).

## Project Structure

```
/bourguiba-money-hustle
├── perception/
├── reasoning/
├── action/
├── memory/
├── orchestration/
├── LICENSE
└── README.md 
```

## Troubleshooting

### Mouse and Keyboard Control Issues

If the agent reports that it's taking actions but you don't see mouse movements:

#### On Linux:
- Make sure you have X11 access permissions: `xhost +local:` 
- For Wayland, make sure you have appropriate permissions
- Install xdotool as a backup: `sudo apt install xdotool`

#### On macOS:
- Grant Accessibility permissions to Terminal/your IDE in System Preferences
- You may need to grant Screen Recording permission as well

#### On Windows:
- Run the script as administrator
- Check if any security software is blocking Python from controlling input devices

## Usage

To run the system:

```bash
cd /home/siaziz/Desktop/bourguiba-money-hustle
source venv/bin/activate   # or `venv\Scripts\activate` on Windows
python main.py
```

You will be prompted to enter your task description at the console. The agent will then execute it.