import json
import ollama
import os
import re
from datetime import datetime
import hashlib  # For generating unique IDs

class BaseAgent:
    def __init__(self, name, system_prompt, history_filepath=None, memory_filepath=None, user_data_filepath=None, temperature=0.7, **kwargs): # Added temperature parameter
        self.name = name
        self.system_prompt = system_prompt
        self.history_filepath = history_filepath
        self.memory_filepath = memory_filepath
        self.user_data_filepath = user_data_filepath
        self.settings = kwargs
        self.history = self._load_history() if history_filepath else []
        self.memory = self._load_memory() if memory_filepath else {}
        self.user_data = self._load_user_data() if user_data_filepath else {}
        self.temperature = temperature  # Store the default temperature

    def _load_user_data(self):
        if not os.path.exists(self.user_data_filepath):
            return {}
        try:
            with open(self.user_data_filepath, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_user_data(self):
        if self.user_data_filepath:
            try:
                with open(self.user_data_filepath, 'w') as f:
                    json.dump(self.user_data, f, indent=4)
            except Exception as e:
                print(f"Error saving user data: {e}")

    def _get_user_template(self, user_id):
        if user_id not in self.user_data:
            self.user_data[user_id] = {"memories": {}, "topics": {}}
            self._save_user_data()
        return self.user_data[user_id]

    def _store_memory_structured(self, user_id, entity, relation, value, metadata, model_name, embedding):
        """Stores information in a structured JSON format with embeddings."""
        user_template = self._get_user_template(user_id)
        timestamp = datetime.now().isoformat()
        unique_id = hashlib.md5(f"{entity}{relation}{value}{timestamp}".encode()).hexdigest()

        memory_item = {
            "entity": entity,
            "relation": relation,
            "value": value,
            "metadata": metadata,
            "timestamp": timestamp,
            "embedding": embedding  # Store the embedding
        }

        topic = metadata.get("topic", "general")
        if topic not in user_template["topics"]:
            user_template["topics"][topic] = {}
        user_template["topics"][topic][unique_id] = memory_item
        if "time" not in user_template["memories"]:
            user_template["memories"]["time"] = {}
        user_template["memories"]["time"][timestamp] = memory_item

        self._save_user_data()

    def _store_memory_tool(self, key, value):
        """Tool function to store memory."""
        self.store_memory(key, value)
        return "Memory stored."

    def _recall_memory_tool(self, key):
        """Tool function to recall memory."""
        if key in self.memory:
            return self.memory[key]
        else:
            return "Memory not found."
    def _load_history(self):
        if not os.path.exists(self.history_filepath):
            return []
        try:
            with open(self.history_filepath, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_history(self):
        if self.history_filepath:
            try:
                with open(self.history_filepath, 'w') as f:
                    json.dump(self.history, f, indent=4)
            except Exception as e:
                print(f"Error saving history: {e}")

    def _load_memory(self):
        if not os.path.exists(self.memory_filepath):
            return {}
        try:
            with open(self.memory_filepath, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_memory(self):
        if self.memory_filepath:
            try:
                with open(self.memory_filepath, 'w') as f:
                    json.dump(self.memory, f, indent=4)
            except Exception as e:
                print(f"Error saving memory: {e}")

    def _validate_memory_format(self, memory_data):
        """Validates the memory format."""
        if not isinstance(memory_data, dict):
            return False
        if not all(key in memory_data for key in ["entity", "relation", "value", "metadata"]):
            return False
        if not isinstance(memory_data["metadata"], dict):
            return False
        return True

    def store_memory(self, key, value):
        self.memory[key] = value
        self._save_memory()
        
    def run(self, model_name, user_message, user_id="default", temperature=None):
        user_template = self._get_user_template(user_id)
        full_prompt = f"{self.system_prompt}\n"
        for msg in self.history:
            full_prompt += f"{msg['role']}: {msg['content']}\n"
        full_prompt += f"user: {user_message}\n"
        full_prompt += f"Current Memory: {json.dumps(user_template['topics'], indent=4)}\n"
        full_prompt += "When storing information, use the following JSON format ONLY, and nothing else: {\"memory\": {\"entity\": \"entity_name\", \"relation\": \"relation_type\", \"value\": \"value\", \"metadata\": {\"source\": \"source_name\", \"timestamp\": \"timestamp_value\", \"topic\": \"topic_name\", \"entities\": [\"entity1\", \"entity2\"], \"relevance\": 0.8}}}. Use MEMORY_STORE: <JSON_START>{{\"memory\": {{...}}}}<JSON_END>. To recall, use MEMORY_RECALL:<JSON_START>{\"key\": \"key_value\"}<JSON_END>. Do not add any extra text or examples. If <JSON_START> or <JSON_END> is missing, try to locate the json data between the first and last curly braces. If the json is invalid return an error message."

        current_temperature = temperature if temperature is not None else self.temperature

        try:
            response = ollama.chat(model=model_name, messages=[
                {
                    'role': 'user',
                    'content': full_prompt,
                },
            ], options={"temperature": current_temperature})
            agent_response = response['message']['content']

            if "MEMORY_STORE:" in agent_response:
                try:
                    json_match = re.search(r"MEMORY_STORE:\s*(\{.*?\})(?:\s*MEMORY_RECALL:|\s*$)", agent_response, re.DOTALL)
                    if json_match:
                        memory_data_str = json_match.group(1).strip()
                        memory_dict = json.loads(memory_data_str)
                        memory_data = memory_dict.get("memory")
                        if self._validate_memory_format(memory_data):
                            embedding_prompt = f"Generate an embedding for the following: Entity: {memory_data['entity']}, Relation: {memory_data['relation']}, Value: {memory_data['value']}"
                            embedding_response = ollama.chat(model=model_name, messages=[{'role': 'user', 'content': embedding_prompt}], options={"temperature": 0})
                            embedding = embedding_response['message']['content']

                            self._store_memory_structured(user_id, memory_data["entity"], memory_data["relation"], memory_data["value"], memory_data["metadata"], model_name, embedding)
                        else:
                            print(f"Invalid memory format: {memory_data}")
                    else:
                        raise ValueError("JSON data not found")
                except (ValueError, json.JSONDecodeError) as e:
                    print(f"Error processing MEMORY_STORE: {e}, response: {agent_response}")

            if "MEMORY_RECALL:" in agent_response:
                try:
                    json_match = re.search(r"MEMORY_RECALL:\s*(\{.*?\})", agent_response, re.DOTALL)
                    if json_match:
                        recall_data_str = json_match.group(1).strip()
                        recall_dict = json.loads(recall_data_str)
                        if "key" in recall_dict:
                            key = recall_dict["key"]
                            recalled_value = self._recall_memory_tool(key)
                            agent_response = agent_response.replace(json_match.group(0), recalled_value)
                    else:
                        raise ValueError("JSON data not found")
                except (ValueError, json.JSONDecodeError) as e:
                    print(f"Error processing MEMORY_RECALL: {e}, response: {agent_response}")

            self.history.append({'role': 'user', 'content': user_message})
            self.history.append({'role': 'assistant', 'content': agent_response})
            self._save_history()
            return agent_response
        except ollama.ResponseError as e:
            print(f"Error from Ollama: {e}")
            return "An error occurred while processing your request."

    def summarize_oldest_messages(self, model_name, limit):
        if len(self.history) <= limit:
            return
        oldest_messages = self.history[:len(self.history) - limit]
        remaining_messages = self.history[len(self.history) - limit:]
        summary_prompt = ("Summarize the following conversation, focusing on the key concepts and important points.\n" "If the conversation is very long, please provide a concise summary of the main ideas, instead of trying to include everything.\n")
        for msg in oldest_messages:
            summary_prompt += f"{msg['role']}: {msg['content']}\n"
        try:
            response = ollama.chat(model=model_name, messages=[
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

# Example Usage:
# agent_config.json
# {
#   "name": "IntelligentMemoryBot",
#   "system_prompt": "You are an intelligent AI. You should remember important things. If something is important, use MEMORY_STORE: {\"key\": \"value\"} to store it.",
#   "history_filepath": "intelligent_memory_bot_history.json",
#   "memory_filepath": "intelligent_memory_bot_memory.json",
#   "temperature": 0.7
# }

agent = load_agent_from_json("pixy_config.json")

if agent:
    model_name = "llama3.1:8b-instruct-q4_0"
    agent.run(model_name, "I went to the store and bought milk and eggs. I also saw a blue car.", "user1") # Added user_id
    agent.run(model_name, "My name is John.", "user1") # Added user_id
    agent.run(model_name, "What is my name?", "user1") # Added user_id
    agent.run(model_name, "I went to the museum and saw a dinosaur", "user2") # Added user_id
    agent.run(model_name, "what did I see?", "user2") # Added user_id
    print(agent.user_data)
else:
    print("Failed to load agent.")