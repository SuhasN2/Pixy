import json
import ollama
import os
import re
from datetime import datetime
import hashlib

class BaseAgent:
    def __init__(self, name, model_name, system_prompt, history_filepath, memory_filepath, user_data_filepath, temperature=0.7, **kwargs):
        self.name = name
        self.model_name = model_name
        self.system_prompt = system_prompt

        self.history_filepath = history_filepath
        self.history = self._load_history()

        self.memory_filepath = memory_filepath
        self.memory = self._load_memory()

        self.user_data_filepath = user_data_filepath
        self.user_data = self._load_user_data()

        self.settings = kwargs

        self.temperature = temperature

    # history loading and saving
    def _load_history(self):
        if not os.path.exists(self.history_filepath):
            print("History file not found, creating empty history file.")
            self._create_empty_file(self.history_filepath)
            return []
        try:
            with open(self.history_filepath, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            print("History file could not be read. Returning empty history.")
            return []

    def _save_history(self):
        if self.history_filepath:
            try:
                with open(self.history_filepath, 'w') as f:
                    json.dump(self.history, f, indent=4)
            except Exception as e:
                print(f"Error saving history: {e}")
        else:
            print("History file path not provided")

    # memory loading and saving
    def _load_memory(self):
        if not os.path.exists(self.memory_filepath):
            print("Memory file not found, creating empty memory file.")
            self._create_empty_file(self.memory_filepath)
            return {}
        try:
            with open(self.memory_filepath, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            print("Memory file could not be read. Returning empty memory.")
            return {}

    def _save_memory(self):
        if self.memory_filepath:
            try:
                with open(self.memory_filepath, 'w') as f:
                    json.dump(self.memory, f, indent=4)
            except Exception as e:
                print(f"Error saving memory: {e}")
        else:
            print("Memory file path not provided")

    # User data loading and saving
    def _load_user_data(self):
        if not os.path.exists(self.user_data_filepath):
            print("User data file not found, creating empty user data file.")
            self._create_empty_file(self.user_data_filepath)
            return {}
        try:
            with open(self.user_data_filepath, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            print("User data file could not be read. Returning empty user data.")
            return {}

    def _save_user_data(self):
        if self.user_data_filepath:
            try:
                with open(self.user_data_filepath, 'w') as f:
                    json.dump(self.user_data, f, indent=4)
            except Exception as e:
                print(f"Error saving user data: {e}")
        else:
            print("User data file path not provided")

    def _create_empty_file(self, filepath):
        try:
            with open(filepath, 'w') as f:
                if filepath == self.history_filepath:
                    json.dump([], f) # create an empty list for history
                else:
                    json.dump({}, f) # create an empty dict for memory and user data
        except Exception as e:
            print(f"Error creating empty file {filepath}: {e}")

    def _get_user_memories(self, user_id):
        if user_id not in self.user_data:
            self.user_data[user_id] = {"memories": {}}
            self._save_user_data()
        return self.user_data[user_id]["memories"]
    
    #* ---------------------------ollama tools-------------------------------
    def _generate_memory_data(self, memory):
        # Simply return the memory string
        return memory    
    def _store_memory_structured(self, user_id, memory_string):
        memories = self._get_user_memories(user_id)
        timestamp = datetime.now().isoformat()
        unique_id = hashlib.md5(f"{memory_string}{timestamp}".encode()).hexdigest()
        memories[unique_id] = {
            "memory": memory_string,
            "timestamp": timestamp,
        }
        self._save_user_data()

    def store_memory(self, user_id, memory_content):
        memory_string = self._generate_memory_data(memory_content)
        if memory_string:
            self._store_memory_structured(user_id, memory_string)
            return "Memory stored."
        else:
            return "Failed to store memory."

    def run(self, user_message, user_id="default", temperature=None):
        full_prompt = f"{self.system_prompt}\n"
        for msg in self.history:
            full_prompt += f"{msg['role']}: {msg['content']}\n"
        full_prompt += f"user: {user_message}\n"

        current_temperature = temperature if temperature is not None else self.temperature

        open("temp.txt","w").write(full_prompt)

        try: #! WTF Y
            response = ollama.chat(model=self.model_name, messages=[
                {
                    'role': 'user',
                    'content': full_prompt,
                },
            ], options={"temperature": current_temperature}, tools=[{
                "type": "function",
                "function": {
                    "name": "store_memory",
                    "description": "Stores a memory.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "memory_content": {
                                "type": "string",
                                "description": "The memory content to store."
                            }
                        },
                        "required": ["memory_content"]
                    }
                }
            }])
            agent_response = response['message']['content']

            if response.get('message', {}).get('tool_calls'):
                for tool_call in response['message']['tool_calls']:

                    if tool_call['function']['name'] == 'store_memory':
                        arguments = tool_call['function']['arguments']
                        if 'memory_content' in arguments:
                            self.store_memory(user_id, arguments['memory_content'])
                        else:
                            print(f"Error: 'memory_content' key missing in tool call arguments: {arguments}")

            if "MEMORY_STORE" in user_message: # ok 
                memory_string = self._generate_memory_data(user_message)
                if memory_string:
                    self._store_memory_structured(user_id, memory_string)

            """if "MEMORY_RECALL:" in agent_response: # !the F
                json_match = re.search(r"MEMORY_RECALL:\s*(\{.*?\}\s*?)(?:MEMORY_STORE:|\s*$)", agent_response, re.DOTALL)
                if json_match:
                    recall_data_str = json_match.group(1).strip()
                    recall_dict = json.loads(recall_data_str)
                    if "key" in recall_dict:
                        key = recall_dict["key"]
                        recalled_value = self._recall_memory_tool(user_id, key)
                        agent_response = agent_response.replace(json_match.group(0), recalled_value)
                    else:
                        print("MEMORY_RECALL: key not found")
                else:
                    raise ValueError("MEMORY_RECALL: JSON data not found")"""
            
            response = response

            self.history.append({'role': 'user', 'content': user_message})
            self.history.append({'role': 'assistant', 'content': str(response["message"]["content"])})
            self._save_history()
            return agent_response
        except ollama.ResponseError as e:
            print(f"Error from Ollama: {e}")
            return "An error occurred while processing your request."

    def summarize_oldest_messages(self, limit):
        if len(self.history) <= limit:
            return
        oldest_messages = self.history[:len(self.history) - limit]
        remaining_messages = self.history[len(self.history) - limit:]
        summary_prompt = ("Summarize the following conversation, focusing on the key concepts and important points.\n" "If the conversation is very long, please provide a concise summary of the main ideas, instead of trying to include everything.\n")
        for msg in oldest_messages:
            summary_prompt += f"{msg['role']}: {msg['content']}\n"
        try:
            response = ollama.chat(model=self.model_name, messages=[
                {
                    'role': 'user',
                    'content': summary_prompt,
                },
            ])
            summary = response['message']['content']
            self.history = [{'role': 'system', 'content': f"Summary of key points: {summary}"}] + remaining_messages
            self._save_history()
        except ollama.ResponseError as e:
            print(f"Error summarizing: {e}")
def load_agent_from_json(filepath):
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            return BaseAgent(**data)
    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {filepath}")
        return None
    except TypeError as e:
        print(f"Error: Type error when creating agent: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occured: {e}")
        return None
    
agent = load_agent_from_json("pixy_config.json")

if agent:
    agent.run("I went to the store and bought milk and eggs. I also saw a blue car.", "user1") # Added user_id
    agent.run("My name is John.", "user1") # Added user_id
    agent.run("What is my name?", "user1") # Added user_id
    agent.run("I went to the museum and saw a dinosaur", "user2") # Added user_id
    agent.run("what did I see?", "user2") # Added user_id
    print(agent.user_data)
else:
    print("Failed to load agent.")


agent.summarize_oldest_messages(5)
agent._save_history()
