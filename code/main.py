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

def load_json_config(config_filepath, history_filepath):
    """
    Loads JSON configuration and initializes an agent.

    Args:
        config_filepath (str): The path to the configuration file.
        history_filepath (str): The path to the history file.

    Returns:
        bool: True if the process completes without errors, False otherwise.
    """
    try:
        config_dir = os.path.dirname(config_filepath)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
            logging.warning(f"Config directory '{config_dir}' created. Please add AI_config.json.")
            print(f"Config directory '{config_dir}' created. Please add AI_config.json.")
            return False  # Indicate an error as the user needs to add the config file

        # Ensure history file exists
        if not os.path.exists(history_filepath):
            with open(history_filepath, 'w') as f:
                json.dump([], f)  # Initialize with an empty list
            logging.info(f"History file '{history_filepath}' created.")

        # Assuming check_ollama, load_config, and initialize_agent are defined elsewhere
        # If these raise exceptions, they will be caught in the outer try-except block

        # Check Ollama connection and model
        if not check_ollama(config_filepath):
            print("Ollama connection or model ve/rification failed. Exiting.")
            logging.critical("Ollama connection or model verification failed.")
            return False

        return True

    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading configuration or history file: {e}")
        logging.error(f"Error loading configuration or history file: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        logging.error(f"An unexpected error occurred: {e}")
        return False    
    
def get_multiline_input(prompt="Enter text (Shift+Enter for new line, Enter to finish):"): # to do fix
    """
    Reads lines from standard input. Shift+Enter creates a new line in the input,
    and pressing Enter on an empty line will stop the input.

    Args:
        prompt (str, optional): A message displayed once before reading begins.
                                   Defaults to "Enter text (Shift+Enter for new line, Enter to finish):".

    Returns:
        str: A single string containing all the input lines entered,
             with each original line separated by a newline character.
    """
    print(prompt, end="")
    lines = []
    while True:
        try:
            line = input()
            if line == "/-": #* Make it little better.
                break  # Empty line, stop reading
            lines.append(line)
        except EOFError:
            # Handle potential EOFError if input is redirected
            break
        except KeyboardInterrupt:
            # Handle Ctrl+C
            break

    return "\n".join(lines)

def main():
    """Main function to run the Pixy AI agent."""
    logging.info("Starting Pixy AI Agent...")

    config_filepath = 'config/AI_config.json'
    history_filepath = 'history.json'

    if load_json_config(config_filepath, history_filepath):
        # Load configuration 
        config = load_config(config_filepath) # TODO --------------
        # Initialize the agent
        agent = initialize_agent(config_filepath, history_filepath)
    
        # Start the conversation
        try:
            # agent.chat(agent.system_prompt)  # Use system prompt from config
            logging.info("Conversation started.")

            while True: #* ====> main loop <======
                user_input = f"Suhas:{get_multiline_input('You: ')}"

                # Command check
                if user_input.lower() in ["suhas:/quit", "suhas:/exit", "suhas:/bye"]:
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
    else:
        pass
if __name__ == "__main__":
    main()
