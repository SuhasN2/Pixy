import datetime
import requests
import json,os

WEATHER_CACHE = {}  # In-memory cache (can be replaced with file-based cache for persistence)
WEATHER_CACHE_EXPIRY_HOURS = 1  # Cache validity duration in hours
WEATHER_CACHE_FILE = "weather_cache.json" # Optional: File to persist cache

def store_user_information(data: str, metadata: dict = None) -> str:
    """Stores user information in the knowledge base."""
    try:
        if metadata is None:
            metadata = {}

        metadata["timestamp"] = datetime.datetime.now().isoformat()
        if "keywords" not in metadata:
            metadata["keywords"] = []
        if "source" not in metadata:
            metadata["source"] = "user"
        if "username" not in metadata:
            metadata["username"] = None
        if "mood" not in metadata:
            metadata["mood"] = None
        if "importance" not in metadata: # Added importance here.
            metadata["importance"] = None

        memory = {}
        if os.path.exists("memory.json"):
            with open("memory.json", "r") as f:
                try:
                    memory = json.load(f)
                except json.JSONDecodeError:
                    memory = {}

        memory[metadata["timestamp"]] = {"data": data, "metadata": metadata}

        with open("memory.json", "w") as f:
            json.dump(memory, f, indent=4)

        return "User information stored successfully."
    except Exception as e:
        return f"Error storing user information: {e}"

mood_list = [
    "happy", "sad", "angry", "neutral", "excited", "calm", "anxious", "frustrated",
    "surprised", "disappointed", "grateful", "hopeful", "confused", "curious",
    "bored", "relaxed", "stressed", "optimistic", "pessimistic", "proud", "ashamed",
    "loving", "lonely", "nostalgic", "jealous", "guilty", "enthusiastic", "indifferent",
    "amused", "irritated", "terrified", "relieved", "impressed", "disgusted",
    "envious", "sympathetic", "apathetic", "content", "melancholy", "ecstatic",
    "miserable", "furious", "serene", "apprehensive", "vexed", "astonished",
    "crestfallen", "thankful", "anticipating", "perplexed", "inquisitive",
    "listless", "tranquil", "uptight", "upbeat", "downcast", "smug", "remorseful",
    "affectionate", "forsaken", "yearning", "covetous", "contrite", "zealous",
    "unconcerned", "tickled", "nettled", "petrified", "soothed", "awestruck",
    "repulsed", "resentful", "compassionate", "unmoved"
]

def store_contact(contact_name: str, information: str, relation: str, other_data: dict = None) -> str:
    """
    Stores contact information in the knowledge base.

    Args:
        contact_name (str): The name of the contact.
        information (str): General information about the contact.
        relation (str): The user's relationship with the contact.
        other_data (dict, optional): Additional data about the contact.

    Returns:
        str: A confirmation message.
    """
    try:
        memory = {}
        if os.path.exists("memory.json"):
            with open("memory.json", "r") as f:
                try:
                    memory = json.load(f)
                except json.JSONDecodeError:
                    memory = {}

        if "contacts" not in memory:
            memory["contacts"] = {}

        memory["contacts"][contact_name] = {
            "information": information,
            "relation": relation,
            "other_data": other_data or {}
        }

        with open("memory.json", "w") as f:
            json.dump(memory, f, indent=4)

        return f"Contact '{contact_name}' stored successfully."
    except Exception as e:
        return f"Error storing contact: {e}"

def update_contact_information(contact_name: str, information: str = None, relation: str = None, other_data: dict = None, steps: int = None, status: str = None, night_change: str = None) -> str:
    """
    Updates contact information in the knowledge base.

    Args:
        contact_name (str): The name of the contact to update.
        information (str, optional): Updated general information about the contact.
        relation (str, optional): Updated relationship with the contact.
        other_data (dict, optional): Updated additional data.
        steps (int, optional): Updated steps information.
        status (str, optional): Updated status information.
        night_change (str, optional): Updated night change information.

    Returns:
        str: A confirmation message.
    """
    try:
        memory = {}
        if os.path.exists("memory.json"):
            with open("memory.json", "r") as f:
                try:
                    memory = json.load(f)
                except json.JSONDecodeError:
                    memory = {}

        if "contacts" not in memory or contact_name not in memory["contacts"]:
            return f"Contact '{contact_name}' not found."

        contact_data = memory["contacts"][contact_name]

        if information is not None:
            contact_data["information"] = information
        if relation is not None:
            contact_data["relation"] = relation
        if other_data is not None:
            if "other_data" not in contact_data:
                contact_data["other_data"] = {}
            contact_data["other_data"].update(other_data) #Append instead of overwrite.
        if steps is not None:
            if "other_data" not in contact_data:
                contact_data["other_data"] = {}
            contact_data["other_data"]["steps"] = steps
        if status is not None:
            if "other_data" not in contact_data:
                contact_data["other_data"] = {}
            contact_data["other_data"]["status"] = status
        if night_change is not None:
            if "other_data" not in contact_data:
                contact_data["other_data"] = {}
            contact_data["other_data"]["night_change"] = night_change

        memory["contacts"][contact_name] = contact_data

        with open("memory.json", "w") as f:
            json.dump(memory, f, indent=4)

        return f"Contact '{contact_name}' updated successfully."

    except Exception as e:
        return f"Error updating contact: {e}"
def none_function():
    """
    This function does nothing and returns None.
    """
    return None

def get_weather_in_bangalore(trigger: str = "None"): # Renamed to match tool name
    """
    Gets current weather in Bengaluru, India, using a single function with 1-hour caching and error handling.

    Args:
        trigger: A trigger to initiate weather retrieval (not used, but required by tool definition).

    Returns:
        A dictionary containing weather information, an error message string, or None if no function is needed.
    """
    location = "Bengaluru"  # Or "Bengaluru JP Nagar, India" - adjust as needed
    cache_key = f"weather_{location}"

    cached_data = WEATHER_CACHE.get(cache_key)

    if cached_data:
        last_cache_time, weather_info = cached_data
        time_difference = datetime.datetime.now() - last_cache_time
        if time_difference < datetime.timedelta(hours=WEATHER_CACHE_EXPIRY_HOURS):
            print("Using cached weather data for Bengaluru (within 1 hour)...")
            return weather_info  # Return cached data if less than 1 hour old


    print("Fetching fresh weather data from API for Bengaluru...")
    api_key = None
    try:
        with open('nv.json', 'r') as f:
            nv_config = json.load(f)
            api_key = nv_config.get("YOUR_OPENWEATHER_API_KEY")
            print(f"API Key from nv.json: {api_key}")
            if not api_key:
                return {"error": "API key not found in nv.json. Check 'YOUR_OPENWEATHER_API_KEY' key in file."}
    except FileNotFoundError:
        return {"error": "Error: nv.json file not found. Ensure nv.json exists in directory."}
    except json.JSONDecodeError:
        return {"error": "Error: Invalid JSON format in nv.json. Check nv.json is valid JSON."}

    if not api_key:
        return {"error": "API key was not loaded."}

    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    complete_url = base_url + "appid=" + api_key + "&q=" + location
    print(f"Request URL: {complete_url}")

    try:
        response = requests.get(complete_url)
        response.raise_for_status()

        if response.status_code == 200:
            data = response.json()
            weather_info = {
                "main": data['weather'][0]['main'],
                "description": data['weather'][0]['description'],
                "temperature_celsius": data['main']['temp'] - 273.15,
                "humidity": data['main']['humidity'],
                "wind_speed": data['wind']['speed']
            }
            WEATHER_CACHE[cache_key] = (datetime.datetime.now(), weather_info) # Update cache
            return weather_info
        else:
            return {"error": f"API error. Status code: {response.status_code}"}

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return {"error": f"Weather data not found for location: {location}. Status 404"}
        elif e.response.status_code == 429:
            return {"error": "Weather service busy (Rate Limit). Try again in a few minutes."}
        else:
            return {"error": f"HTTP error: {e}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Network error: {e}"}

def get_current_time():
    """
    Get the current time.

    Returns:
        The current time as a string.
    """
    now = datetime.datetime.now()
    current_time = now.strftime("%Y-%m-%d %H:%M:%S") # Format the time
    return f"Current time: {current_time}"

def evaluate_expression(expression):
    """
    Evaluates a Python code expression given as a string.

    Args:
        expression (str): The Python expression to evaluate.

    Returns:
        The result of the evaluation, or an error message if evaluation fails.
    """
    try:
        result = eval(expression)
        return result
    except Exception as e:
        return f"Error: {e}"

tools_list = [
    {
        "type": "function",
        "function": {
            "name": "get_weather_in_bangalore",
            "description": "Get the current weather conditions in Bengaluru JP Nagar, India.",
            "parameters": {
                "type": "object",
                "properties": {
                    "trigger": {
                        "type": "string",
                        "description": "A trigger to initiate weather retrieval. This parameter is not used, but is required to call the function."
                    }
                },
                "required": ["trigger"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current time.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "none_function",
            "description": "This function does nothing and returns None. Use when no other function is needed.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "evaluate_expression",
            "description": "Evaluates a Python code expression given as a string, including mathematical expressions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The Python expression to evaluate."
                    }
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "store_user_information",
            "description": "Stores general user information in the knowledge base. This function is used to store data with associated metadata. The data can be any string, and the metadata provides context, such as type, source, keywords, mood, username, and importance.",
            "parameters": {
                "type": "object",
                "properties": {
                    "data": {
                        "type": "string",
                        "description": "The user information to store."
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Metadata associated with the data.",
                        "properties": {
                            "type": {"type": "string", "description": "The type of information (e.g., preference, fact, note)."},
                            "source": {"type": "string", "description": "The source of the information (obsidian_vault, web_search, user)."},
                            "keywords": {"type": "array", "items": {"type": "string"}, "description": "Keywords related to the data."},
                            "username": {"type": "string", "description": "The username that the data belongs to, or a friend's name."},
                            "mood": {"type": "string", "description": "The user's mood. Select from: happy, sad, angry, neutral, excited, calm, anxious, frustrated, surprised, disappointed, grateful, hopeful, confused, curious, bored, relaxed, stressed, optimistic, pessimistic, proud, ashamed, loving, lonely, nostalgic, jealous, guilty, enthusiastic, indifferent, amused, irritated, terrified, relieved, impressed, disgusted, envious, sympathetic, apathetic, content, melancholy, ecstatic, miserable, furious, serene, apprehensive, vexed, astonished, crestfallen, thankful, anticipating, perplexed, inquisitive, listless, tranquil, uptight, upbeat, downcast, smug, remorseful, affectionate, forsaken, yearning, covetous, contrite, zealous, unconcerned, tickled, nettled, petrified, soothed, awestruck, repulsed, resentful, compassionate, unmoved"},
                            "importance": {"type": "string", "description": "The importance of the information. (e.g. High, Medium, Low)"}
                        }
                    },
                },
                "required": ["data"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "store_contact",
            "description": "Stores contact information in the knowledge base. This function is specifically for adding new contacts, including their name, general information, relationship to the user, and any other relevant data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "contact_name": {"type": "string", "description": "The name of the contact."},
                    "information": {"type": "string", "description": "General information about the contact."},
                    "relation": {"type": "string", "description": "The user's relationship with the contact."},
                    "other_data": {"type": "object", "description": "Additional data about the contact.", "properties": {}}
                },
                "required": ["contact_name", "information", "relation"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_contact_information",
            "description": "Updates existing contact information in the knowledge base. This function allows for modifications to a contact's general information, relationship, and any other stored data, including steps, status, and night change.",
            "parameters": {
                "type": "object",
                "properties": {
                    "contact_name": {"type": "string", "description": "The name of the contact to update."},
                    "information": {"type": "string", "description": "Updated general information about the contact."},
                    "relation": {"type": "string", "description": "Updated relationship with the contact."},
                    "other_data": {"type": "object", "description": "Updated or additional data about the contact. The new data will be appended to the existing data.", "properties":{}},
                    "steps": {"type": "integer", "description": "Updated steps information."},
                    "status": {"type": "string", "description": "Updated status information."},
                    "night_change": {"type": "string", "description": "Updated night change information."},
                },
                "required": ["contact_name"]
            }
        }
    }
]

available_functions = {
    'get_current_time': get_current_time,
    'none_function': none_function,
    'get_weather_in_bangalore': get_weather_in_bangalore,
    'evaluate_expression': evaluate_expression,
    'store_user_information': store_user_information,
    'store_contact': store_contact,
    'update_contact_information': update_contact_information,
}


