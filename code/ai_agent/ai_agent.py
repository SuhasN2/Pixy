import json
import ollama
from typing import Dict, List
import os
import logging
import sys

# Add the parent directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import tool_calling.general_tools

print("************")
print(tool_calling.general_tools.available_functions)


# Configure logging
logging.basicConfig(filename='ai_agent.log', level=logging.INFO,format='%(asctime)s - %(levelname)s - %(message)s')


class AiAgent:
    def __init__(self, config_filepath: str, history_filepath: str):
        # load config
        self.config = self.load_config(config_filepath)

        self.pixy_config = self.config.get("pixy", {})
        self.model = self.pixy_config.get("model_name", "llama3.1:8b")
        self.system_prompt = self.pixy_config.get("system_prompt", "")
        self.model_parameters = self.pixy_config.get("model_parameters", {})
        # load history
        self.history_filepath = history_filepath
        self.history: List[Dict[str, str]] = self.load_history()

    def load_config(self, config_filepath: str) -> Dict:
        try:
            with open(config_filepath, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logging.exception(f"Error: Configuration file '{config_filepath}' not found.")
            raise  # Re-raise the exception to be handled by the caller
        except json.JSONDecodeError as e:
            logging.exception(f"Error: Invalid JSON in '{config_filepath}': {e}")
            raise  # Re-raise the exception

    def load_history(self) -> List[Dict[str, str]]:
        if os.path.exists(self.history_filepath):
            try:
                with open(self.history_filepath, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                logging.warning(f"Error decoding history.json: {e}. Starting with empty history.")
                return []  # Return empty list instead of raising exception for history
        return []

    def save_history(self):
        try:
            with open(self.history_filepath, 'w') as f:
                json.dump(self.history, f, indent=4)
            logging.info("Conversation history saved to %s", self.history_filepath)
        except Exception as e:
            logging.exception("Error saving history to history.json: %s", e)

    def chat(self, message: str) -> str:
        self.history.append({"role": "user", "content": message})
        try:
            response = ollama.chat(
                model=self.model,
                messages=self.history,
                parameters=self.model_parameters
            )
            answer = response['message']['content']
            self.history.append({"role": "assistant", "content": answer})
            self.save_history()
            logging.info("Chat completed successfully. User input: %s, AI response: %s", message, answer)
            return answer
        except Exception as e:
            logging.exception("Error during chat: %s", e)
            return f"Error during chat: {e}"
        
    def summarize_conversation(self) -> str:
        if not self.history:
            return "No conversation history."
        try:
            summary_prompt = "Summarize this conversation history: " + "\n".join(
                [f"{entry['role']}: {entry['content']}" for entry in self.history]
            )
            
            # Get summarization parameters from config, default to model parameters if not found
            summarization_config = self.config.get("summarization", {})
            summarization_parameters = summarization_config.get("model_parameters", self.model_parameters)

            summary = ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": summary_prompt}],
                parameters=summarization_parameters
            )
            answer = summary['message']['content']
            logging.info("Conversation summarized successfully. Summary: %s", answer)
            return answer
        except Exception as e:
            logging.exception("Error during summarization: %s", e)
            return f"Error during summarization: {e}"
        
    
    def handle_tool_calls(self, response, tools):
        """Handles tool calls from a chat response, excluding disabled tools."""
        if response.message.tool_calls:
            available_functions = {tool_obj.name: tool_obj.func for tool_obj in tools if tool_obj.enabled} #only enabled tools.
            for tool_call in response.message.tool_calls:
                if function_to_call := available_functions.get(tool_call.function.name):
                    print('Calling function:', tool_call.function.name)
                    print('Arguments:', tool_call.function.arguments)
                    try:
                        output = function_to_call(**json.loads(tool_call.function.arguments))
                        print('Function output:', output)
                    except Exception as e:
                        print(f"Error calling function {tool_call.function.name}: {e}")
                        return None
                else:
                    print('Function', tool_call.function.name, 'not found or disabled.')
                    return None  # Or handle the error as needed

            self.history.append(response.message)
            self.history.append({'role': 'tool', 'content': str(output), 'name': tool_call.function.name})
            return output
        else:
            print('No tool calls returned from model')
            return None
        
    def call_general_info_tool(self):
        """Calls a tool from the general_info section of the config."""
        general_info_config = self.config.get("general_info", {})
        model_parameters = general_info_config.get("model_parameters", self.model_parameters)
        system_prompt = general_info_config.get("system_prompt", "")
        #functions_dict = general_info_config.get("functions", {}) #get the tool dict from the config.
        tools = tool_calling.general_tools.available_functions #load tools from the dictionary.
        tool_list_for_chat = [json.loads(tool_obj.tool_def)[tool_obj.name] for tool_obj in tools if tool_obj.enabled] #create the tool list for the chat API.

        messages = self.history.copy()

        if system_prompt:
          messages.append({'role': 'system', 'content': system_prompt})

        try:
            response: ollama.ChatResponse = ollama.chat(model=self.model, options=model_parameters, messages=messages, tools=tool_list_for_chat)

            if self.handle_tool_calls(response, tools):
                return True
            else:
                return False

        except Exception as e:
            print(f"Error calling Ollama chat API: {e}")
            return False
        
    def call_database_handler_tool(self, tool_name: str, **kwargs):
        """Calls a tool from the database_handler section of the config."""
        database_config = self.config.get("database_handler", {})
        model_parameters = database_config.get("model_parameters", self.model_parameters)
        system_prompt = database_config.get("system_prompt", "")
        functions = database_config.get("functions", {})

        # Add error handling for missing functions
        if tool_name not in functions:
            logging.error(f"Tool '{tool_name}' not found in database_handler config.")
            return None

        try:
            result = functions[tool_name](**kwargs)
            self.history.append({"role": "tool", "name": tool_name, "arguments": kwargs, "result": result})
            return result
        except Exception as e:
            logging.exception(f"Error executing tool '{tool_name}': {e}")
            self.history.append({"role": "tool", "name": tool_name, "arguments": kwargs, "error": str(e)})
            return None
