import time
import argparse
from orchestration.config_manager import ConfigManager
from orchestration.agent_core import AgentCore
from loguru import logger

def main():
    # Set up argument parser for command line options
    parser = argparse.ArgumentParser(description='GUI Automation Agent')
    parser.add_argument('--model', '-m', type=str, help='Ollama model to use')
    parser.add_argument('--list-models', '-l', action='store_true', help='List recommended models')
    parser.add_argument('--task', '-t', type=str, help='Task to execute')
    args = parser.parse_args()

    # Load configuration from config.json in the project root
    config_manager = ConfigManager(config_path="config.json")
    config = config_manager.load_config()
    
    # Show model recommendations if requested
    if args.list_models:
        print("Recommended models for this application:")
        for model in config_manager.recommended_models:
            print(f" - {model}")
        return
    
    # Override model if specified in command line
    if args.model:
        logger.info(f"Using Ollama model specified via command line: {args.model}")
        config["ollama_model"] = args.model
    else:
        logger.info(f"Using Ollama model from config: {config['ollama_model']}")
    
    # Initialize and start the agent
    agent = AgentCore(config)
    agent.start()
    
    # Either use the task from command line or prompt user
    task_description = args.task or input("Enter your task: ")
    print(f"Submitting task: {task_description}")
    agent.execute_task(task_description)
    
    # Keep the program running until interrupted
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        agent.stop()
        print("Agent stopped.")

if __name__ == "__main__":
    main()
