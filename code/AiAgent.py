import ollama
import json
import os
import tools
class AiAgent:
    def __init__(self,name,model_name, system_prompt, history_filepath, memory_filepath, user_data_filepath,tool_calling_model = None, temperature=0.7,**kwargs):
        self.name = name
        self.model_name = model_name

        if tool_calling_model == None: 
            self.tool_calling_model = model_name 
        else:
            self.tool_calling_model = tool_calling_model

        self.system_prompt = system_prompt

        self.history_filepath = history_filepath
        self.history = self._load_history()

        self.memory_filepath = memory_filepath
        self.memory = self._load_memory()

        self.user_data_filepath = user_data_filepath
        self.user_data = self._load_user_data()

        self.settings = kwargs

        self.temperature = temperature

    # history loading and saving-----------------------------------
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
    # memory loading and saving----------------------------------------
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

    # User data loading and saving ---------------------------------
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
                elif filepath == self.memory_filepath:
                    json.dump([], f)#  
                else:
                    json.dump({}, f) # create an empty dict for memory and user data
        except Exception as e:
            print(f"Error creating empty file {filepath}: {e}")

    def generate_prompt(self,user_query):
        full_prompt = ""
        full_prompt += f"{user_query}"
        return full_prompt

    def tool_calling(self):
        messages = self.history.copy()
        messages.append({'role': 'system', 'content': """You are the **Tool Selector AI**.
        Your role is to analyze user requests and determine if a tool is needed to answer them. If a tool is necessary, you must select the most appropriate tool from the available tools and generate a valid tool call.

        **Your Goal:** To accurately identify when a tool is required and to create a correct tool call that the second AI can use to get the information needed to answer the user's question.

        **Tool Access:** You have access to a set of tools. You do not need to know the specifics of each tool in this prompt, but you understand that you can use them to access information and perform actions.

        **Your Task Breakdown:**

        1. **Analyze User Request:** Carefully read and understand the user's request. Identify the core question or need.
        2. **Tool Necessity Check:** Determine if answering the user's request would be significantly improved or only possible by using a tool. Consider:
            * **Information Need:** Does the request require real-time data, specific information from external sources, or actions beyond general knowledge?
            * **Tool Capabilities:** Consider if any of the tools you have access to are designed to address this type of information need or action.
        3. **Tool Selection (If Necessary):** If a tool is needed, choose the most appropriate tool(s) from the available set. Select the tool(s) that are best suited to directly address the user's request.
        4. **Tool Call Generation:** Once you've selected a tool, generate a valid tool call. This involves:
            * Identifying the correct function name for the chosen tool.
            * Determining the necessary arguments/parameters for the function based on the user's request.
            * Formatting the tool call correctly so that it can be executed by the system.
        5. **Output Tool Call(s) OR Indicate No Tool Needed:**
            * **If tool(s) are selected:** Output *only* the tool call(s). Do not attempt to answer the user's question yourself. Your output should be the structured tool call(s) ready for execution.
            * **If no tool is needed:** Output a clear signal that no tool is required. This could be a simple message like "No tool needed." or a specific code like `\"tool_calls\": \"None\"`.

        **Important Considerations:**

        * **Focus on Tool Selection and Calling:** Your *only* responsibility is tool selection and call generation. Do not attempt to formulate a final answer to the user.
        * **Multiple Tool Calls:** You can make multiple tool calls if necessary, especially when storing multiple pieces of information. For example, if the user provides several facts, you can call the `store_user_information` function multiple times.
        * **Accuracy in Tool Calls:** Ensure your tool calls are valid and contain all necessary and correctly formatted arguments. Incorrect tool calls will prevent the second AI from getting the information it needs.
        * **Efficiency:** Select the most direct and efficient tool(s) for the task. Avoid unnecessary tool calls.
        * **Assume Second AI Handles Response:** You do not need to worry about how the final response to the user will be generated. The second AI will handle that using the output from the tool you call.

        Your output will be used by a second AI to generate the final response to the user. Make sure your tool selection and tool calls are accurate and helpful for that second AI to complete the task."""})
        response: ollama.ChatResponse = ollama.chat(model=self.tool_calling_model, options={"temperature": 0.1}, messages=self.history, tools=tools.tools_list)
        if response.message.tool_calls:
            if response.message.tool_calls != "None":
                # There may be multiple tool calls in the response
                for tool in response.message.tool_calls:
                    # Ensure the function is available, and then call it
                    if function_to_call := tools.available_functions.get(tool.function.name):
                        print('Calling function:', tool.function.name)
                        print('Arguments:', tool.function.arguments)
                        output = function_to_call(**tool.function.arguments)
                        print('Function output:', output)
                        # Add the function response to messages for the model to use
                        self.history.append({'role': 'tool', 'content': str(output), 'name': tool.function.name})

                    else:
                        print('Function', tool.function.name, 'not found')

        else:
            print('No tool calls returned from model')

    def run(self,user_message):
        
        self.history.append({'role': 'user', 'content': self.generate_prompt(user_message)})

        self.tool_calling()

        response = ollama.chat(model=self.model_name, messages=self.history,)
        
        agent_response = response['message']['content']

        
        self.history.append({'role': 'assistant', 'content': agent_response})

        self._save_history()

        return agent_response
def load_agent_from_json(filepath):
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            return AiAgent(**data)
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
    
if __name__ == "__main__":
    agent = load_agent_from_json("pixy_config.json")
    while True:
        user_input = input("input: ")
        if user_input.lower() == "/exit":
            break
        print("pixy:" + agent.run("user name: suhas \n"+ user_input))
