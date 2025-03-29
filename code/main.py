from ai_agent import AiAgent
import ollama
import logging
import json
import os

# Configure logging
logging.basicConfig(filename='main.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s') # Corrected line

def check_ollama(config_filepath: str) -> bool:
    """Checks Ollama connection and the specified model."""
    try:
        with open(config_filepath, 'r') as f:
            config = json.load(f)
        model_name = config['pixy']['model_name']

        # Attempt a simple chat to test the connection
        test_response = ollama.chat(model=model_name, messages=[{"role": "user", "content": "test"}])
        logging.info(f"Successfully connected to Ollama model: {model_name}")
        return True

    except FileNotFoundError:
        logging.error(f"Configuration file '{config_filepath}' not found.")
        return False
    except json.JSONDecodeError:
        logging.error(f"Invalid JSON in '{config_filepath}'.")
        return False
    except Exception as e:
        logging.exception(f"Error connecting to Ollama model: {e}")
        return False

def load_config(config_filepath: str) -> dict:
    """Loads the configuration from the specified file."""
    try:
        with open(config_filepath, 'r') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        logging.critical(f"Configuration file '{config_filepath}' not found.")
        raise
    except json.JSONDecodeError:
        logging.critical(f"Invalid JSON in '{config_filepath}'.")
        raise

def initialize_agent(config_filepath: str, history_filepath: str) -> AiAgent:
    """Initializes the AiAgent."""
    try:
        agent = AiAgent(config_filepath, history_filepath)
        logging.info("AiAgent initialized successfully.")
        return agent
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.critical(f"Failed to initialize AiAgent: {e}")
        raise

def main():
    """Main function to run the Pixy AI agent."""
    logging.info("Starting Pixy AI Agent...")

    config_filepath = 'config/AI_config.json'
    history_filepath = 'history.json'

    # Ensure config directory exists
    config_dir = os.path.dirname(config_filepath)
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
        logging.warning(f"Config directory '{config_dir}' created. Please add AI_config.json.")
        print(f"Config directory '{config_dir}' created. Please add AI_config.json.")
        return

    # Ensure history file exists
    if not os.path.exists(history_filepath):
        with open(history_filepath, 'w') as f:
            json.dump([], f)  # Initialize with an empty list
        logging.info(f"History file '{history_filepath}' created.")

    # Check Ollama connection and model
    if not check_ollama(config_filepath):
        print("Ollama connection or model verification failed. Exiting.")
        logging.critical("Ollama connection or model verification failed.")
        return

    # Load configuration
    try:
        config = load_config(config_filepath)
    except (FileNotFoundError, json.JSONDecodeError):
        print("Failed to load configuration. Exiting.")
        return

    # Initialize the agent
    try:
        agent = initialize_agent(config_filepath, history_filepath)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print("Failed to initialize agent. Exiting.")
        return

    # Start the conversation
    try:
        # agent.chat(agent.system_prompt)  # Use system prompt from config
        logging.info("Conversation started.")

        while True: #* ====> main loop <======
            user_input = f"Suhas:{input('You: ')}"

            # Command check
            if user_input.lower() in ["/quit", "/exit", "/bye"]:
                logging.info("Exiting conversation.")
                break

            try:
                response = agent.chat(user_input)
                print("Pixy:", response)
            except Exception as e:
                print(f"An error occurred during chat or summarization: {e}")
                logging.error(f"Error during chat or summarization: {e}")

    except Exception as e:
        logging.exception(f"An unexpected error occurred: {e}")
        print(f"An unexpected error occurred: {e}")

    finally:
        logging.info("Pixy AI Agent finished.")

if __name__ == "__main__":
    main()
