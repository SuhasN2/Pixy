import json
import ollama
from typing import Dict, List
import os
import logging
import sys
import general_tools

# Add the parent directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Configure logging
logging.basicConfig(filename='ai_agent.log', level=logging.INFO,format='%(asctime)s - %(levelname)s - %(message)s') # Corrected line


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

        self.call_general_info_tool()
        # logging.info("Chat completed successfully. User input: %s, AI response: %s", message, response)

        
        try:
            response = ollama.chat(
                model=self.model,
                messages=self.history,
                # Removed parameters argument here
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

            summary = ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": summary_prompt}],
                # Removed parameters argument here
            )
            answer = summary['message']['content']
            logging.info("Conversation summarized successfully. Summary: %s", answer)
            return answer
        except Exception as e:
            logging.exception("Error during summarization: %s", e)
            return f"Error during summarization: {e}"
        

    def call_general_info_tool(self):
        self.history.append({"role": "assistant", "content": "tool calling not implemented yet"})
        logging.info("not implemented yet field successfully.")
        return "not implemented yet"
        """
        Calls tools from the general_info section of the config.

        This function now handles tool calling more robustly, including:
        - Checking if tool calls are present in the response.
        - Handling multiple tool calls in a single response.
        - Correctly formatting tool outputs for the model.
        - Returning the final model response after tool execution.
        """


        general_info_config = self.config.get("general_info", {})
        model_parameters = general_info_config.get("model_parameters", self.model_parameters)
        system_prompt = general_info_config.get("system_prompt", None)
        tools = general_tools.available_functions

        messages = self.history.copy()
        if system_prompt:
            messages.insert(0, {"role": "system", "content": system_prompt})
            messages.append({"role": "system", "content": system_prompt})

        try:
            # Initial call to the model with tool definitions
            response = ollama.chat(model=self.model, options=model_parameters, messages=messages, tools=list(tools))

            # Check if there are any tool calls in the response
            if response.message.tool_calls is not None:
                logging.info(f"Tool calls detected: {response.message.tool_calls}")
                
                # Process each tool call
                for tool_call in response.message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments) # Load arguments as JSON

                    if tool_name in tools:
                        try:
                            # Execute the tool
                            tool_output = tools[tool_name]["callable"](**tool_args)
                            logging.info(f"Tool '{tool_name}' called successfully. Output: {tool_output}")

                            # Format the tool output for the model
                            tool_output_message = {
                                'role': 'tool',
                                'name': tool_name,
                                'content': str(tool_output)
                            }
                            self.history.append(tool_output_message)
                            messages.append(tool_output_message)

                        except Exception as e:
                            tool_output = f"Error calling tool '{tool_name}': {e}"
                            logging.error(f"Error calling tool '{tool_name}': {e}")
                            tool_output_message = {
                                'role': 'tool',
                                'name': tool_name,
                                'content': tool_output
                            }
                            self.history.append(tool_output_message)
                            messages.append(tool_output_message)
                    else:
                        tool_output = f"Tool '{tool_name}' not found."
                        logging.warning(f"Tool '{tool_name}' not found.")
                        tool_output_message = {
                            'role': 'tool',
                            'name': tool_name,
                            'content': tool_output
                        }
                        self.history.append(tool_output_message)
                        messages.append(tool_output_message)

                # Second call to the model with tool outputs
                second_response = ollama.chat(model=self.model, options=model_parameters, messages=messages)
                return second_response.message.content

            else:
                # No tool calls, return the original response
                self.history.append({"role": "system", "content": "No system calls were executed by the program."})
                return response.message.content

        except Exception as e:
            logging.exception(f"Error in call_general_info_tool: {e}")
            return f"Error: {e}"

if __name__ == "__main__":
    agent = AiAgent('config/AI_config.json', 'history.json')
