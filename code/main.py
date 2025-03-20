from ai_agent.ai_agent import AiAgent
import ollama
import logging ,json

logging.basicConfig(filename='main.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def check_ollama(config_filepath: str) -> bool:
    """Checks Ollama connection and the specified model."""
    try:
        with open(config_filepath, 'r') as f:
            config = json.load(f)
        model_name = config['pixy']['model_name']  # Extract model name from config

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
        logging.exception(f"Error connecting to Ollama model '{model_name}': {e}")
        return False

def main():
    logging.info("Starting main function")

    #* endearment verbals
    config_filepath = 'config/AI_config.json'
    history_filepath = 'history.json'
    
    #* validation
    if not check_ollama(config_filepath):
        print("Ollama connection or model verification failed. Exiting.")
        return

    try:
        agent = AiAgent(config_filepath,history_filepath) # make agent

    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.critical("Failed to load configuration: %s", e)
        return  # Exit if configuration loading fails
    

    try:
        agent.chat(agent.system_prompt) # Use system prompt from config

        while True:
            user_input = input("You: ")

            # command chick
            if user_input.lower() in ["/quit", "/exit", "/bye"]:
                break

            try:
                response = agent.chat(user_input)
                print("Pixy:", response)
                summary = agent.summarize_conversation()
                print("Conversation Summary:", summary)
            except Exception as e:
                print(f"An error occurred during chat or summarization: {e}")

    except Exception as e:
        logging.exception("An unexpected error occurred: %s", e)

if __name__ == "__main__":
    main()
