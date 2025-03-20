import json

class tool:
    def __init__(self,name: str,func: callable,tool_def: str,enabled = True):
        self.name = name
        self.func = func
        self.tool_def = tool_def
        self.enabled = enabled

    def get_tool_def(self):
        if self.enabled:
            return self.tool_def
        else:
            pass

    def run_func(self, *args, **kwargs):
        if self.enabled:
            return self.func(*args, **kwargs)
        else:
            raise Exception(f"Tool '{self.name}' is disabled.")

def load_tools_from_json(filepath):
    """Loads tool definitions from a JSON file and creates tool objects."""
    tools = []
    try:
        with open(filepath, 'r') as f:
            tool_data = json.load(f)

        for name, details in tool_data.items():
            func_name = details["function"]["name"]
            # Simulate function retrieval (replace with your actual function retrieval logic)
            try:
                # This is a placeholder. In a real application, you would retrieve the actual function
                # based on the function name (e.g., using globals(), or by importing modules).
                func = lambda x: print(f"Mock function '{func_name}' called with: {x}")
            except NameError:
                print(f"Warning: Function '{func_name}' not found. Tool '{name}' will have a placeholder function.")
                func = lambda x: print(f"Warning: Function '{func_name}' not found. Tool '{name}' was called with: {x}")

            tool_def_json = {name: details["function"]}
            tool_def_str = json.dumps(tool_def_json) #Use json.dumps for proper json formatting.

            tools.append(tool(name=name, func=func, tool_def=tool_def_str))

        return tools

    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.")
        return []
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in '{filepath}'.")
        return []
    