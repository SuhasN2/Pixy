import datetime
import requests
import json,os, re

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

WEATHER_CACHE = {}
WEATHER_CACHE_EXPIRY_HOURS = 1

def get_weather(city: str = "Bangalore"):
    """
    Gets current weather in a specified city, using a single function with 1-hour caching and error handling.

    Args:
        city: The name of the city to get weather for. Defaults to "Bangalore".
        trigger: A trigger to initiate weather retrieval (not used, but required by tool definition).

    Returns:
        A dictionary containing weather information, an error message string, or None if no function is needed.
    """
    location = city  # Use the provided city name
    cache_key = f"weather_{location}"

    cached_data = WEATHER_CACHE.get(cache_key)

    if cached_data:
        last_cache_time, weather_info = cached_data
        time_difference = datetime.datetime.now() - last_cache_time
        if time_difference < datetime.timedelta(hours=WEATHER_CACHE_EXPIRY_HOURS):
            print(f"Using cached weather data for {location} (within 1 hour)...")
            return weather_info  # Return cached data if less than 1 hour old

    print(f"Fetching fresh weather data from API for {location}...")
    api_key = None
    try:
        with open('code/nv.json', 'r') as f:
            nv_config = json.load(f)
            api_key = nv_config.get("YOUR_OPENWEATHER_API_KEY")
            print(f"API Key from code/nv.json: {api_key}")
            if not api_key:
                return {"error": "API key not found in code/nv.json. Check 'YOUR_OPENWEATHER_API_KEY' key in file."}
    except FileNotFoundError:
        return {"error": "Error: code/nv.json file not found. Ensure code/nv.json exists in directory."}
    except json.JSONDecodeError:
        return {"error": "Error: Invalid JSON format in code/nv.json. Check code/nv.json is valid JSON."}

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
            WEATHER_CACHE[cache_key] = (datetime.datetime.now(), weather_info)  # Update cache
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

def get_current_time(location=None):
    """
    Returns the current time for a given city or time zone.

    Args:
        location (str): The name of a city or a time zone string.

    Returns:
        str: The current time in the specified location, or an error message.
    """

    city_timezones = {
            "New York": "America/New_York",
            "Los Angeles": "America/Los_Angeles",
            "Chicago": "America/Chicago",
            "Delhi": "Asia/Kolkata",
            "Mumbai": "Asia/Kolkata",
            "Bangalore": "Asia/Kolkata",
            "Chennai": "Asia/Kolkata",
            "Hyderabad": "Asia/Kolkata",
            "Kolkata": "Asia/Kolkata",
            "Pune": "Asia/Kolkata",
            "Ahmedabad": "Asia/Kolkata",
            "Jaipur": "Asia/Kolkata",
            "Lucknow": "Asia/Kolkata",
            "Surat": "Asia/Kolkata",
            "Beijing": "Asia/Shanghai",
            "Shanghai": "Asia/Shanghai",
            "Guangzhou": "Asia/Shanghai",
            "Shenzhen": "Asia/Shanghai",
            "Tianjin": "Asia/Shanghai",
            "London": "Europe/London",
            "Paris": "Europe/Paris",
            "Berlin": "Europe/Berlin",
            "Rome": "Europe/Rome",
            "Madrid": "Europe/Madrid",
            "Amsterdam": "Europe/Amsterdam",
            "Stockholm": "Europe/Stockholm",
            "Tokyo": "Asia/Tokyo",
        }

    try:
        if location:
            if location in city_timezones:
                time_zone = city_timezones[location]
            else:
                time_zone = location
        else:
          time_zone = datetime.datetime.now().astimezone().tzinfo
          if time_zone is None:
            return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        tz = pytz.timezone(time_zone)
        current_time = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        return current_time

    except pytz.exceptions.UnknownTimeZoneError: #! what is pytz
        return "Error: Invalid time zone."
    except Exception as e:
        return f"An unexpected error occured: {e}"
    
def get_news_articles_from_json_key(keywords, json_file_path='code/nv.json', top_results=5, search_days=10):
    """
    Fetches news articles based on keywords using the News API.
    API key is imported from a JSON file.
    Dynamically updates the 'from' date to search within a specified day range.
    Returns a maximum of the top specified number of results.

    Args:
        keywords (str or list): Keywords to search for in news articles.
                                 If a list is provided, it will be joined into a string.
        json_file_path (str, optional): Path to the JSON file containing API keys.
                                        Defaults to 'code/nv.json' in the same directory.
        top_results (int, optional): Maximum number of top results to return. Defaults to 5.
        search_days (int, optional): Number of days to search back from today for news articles. Defaults to 10 days.

    Returns:
        dict: A dictionary containing news articles from the News API, or an error message.
              Returns an empty dictionary if no articles are found.
    """

    search_days = int(search_days)
    base_url = 'https://newsapi.org/v2/everything?'
    # Dynamically set the date to 'search_days' ago from today
    today_date = datetime.date.today()
    date_from = (today_date - datetime.timedelta(days=search_days)).strftime('%Y-%m-%d')
    sort_by = 'popularity' # Using sortBy from the user's example
    api_key = None

    if not isinstance(top_results, int) or top_results <= 0:
        return {'error': "Invalid value for 'top_results'. Must be a positive integer."}
    if not isinstance(search_days, int) or search_days <= 0:
        return {'error': "Invalid value for 'search_days'. Must be a positive integer."}


    try:
        # Construct the absolute path to the JSON file
        script_dir = os.path.dirname(os.path.abspath(__file__))  # Directory of the current script
        json_path = os.path.join(script_dir, json_file_path)

        with open(json_path, 'r') as f:
            keys_data = json.load(f)
            api_key = keys_data.get('YOUR_NEWSAPI_API_KEY')

        if not api_key:
            return {'error': "API key not found in JSON file or 'YOUR_NEWSAPI_API_KEY' key is missing."}

    except FileNotFoundError:
        return {'error': f"JSON file not found at path: {json_path}"}
    except json.JSONDecodeError:
        return {'error': f"Error decoding JSON from file: {json_path}. Please ensure it's valid JSON."}
    except Exception as e: # Catch other potential exceptions during file reading
        return {'error': f"An unexpected error occurred while reading the JSON file: {e}"}


    if isinstance(keywords, list):
        search_query = " ".join(keywords) # Join list of keywords into a string
    else:
        search_query = keywords # Use string keywords directly

    url = f'{base_url}q={search_query}&from={date_from}&sortBy={sort_by}&apiKey={api_key}'

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        news_data = response.json()

        if news_data.get('status') == 'ok' and news_data.get('articles'):
            articles = news_data['articles']
            top_articles = articles[:top_results] # Limit to top results
            news_data['articles'] = top_articles # Update the articles in the dictionary
            return news_data # Returns the entire JSON response as a dictionary, now with limited articles
        elif news_data.get('status') == 'ok' and not news_data.get('articles'):
            return {} # Return empty dictionary if no articles are found but the request was successful
        else:
            return {'error': f"API request failed: {news_data.get('message', 'Unknown error')}"} # Error from API

    except requests.exceptions.RequestException as e:
        return {'error': f"Request Exception: {e}"} # Handle network errors, timeouts, etc.


def get_top_headlines(country='us', json_file_path='code/nv.json'):
    """
    Fetches top headlines from the News API for a specific country.
    API key is imported from a JSON file.

    Args:
        country (str, optional): The 2-letter ISO 3166-1 country code for headlines.
                                 Defaults to 'us' (United States).
        json_file_path (str, optional): Path to the JSON file containing API keys.
                                        Defaults to 'code/nv.json' in the same directory.

    Returns:
        dict: A dictionary containing top headlines from the News API, or an error message.
              Returns an empty dictionary if no headlines are found.
    """
    base_url = 'https://newsapi.org/v2/top-headlines?'
    api_key = None

    if not country:
        return {'error': "Country code must be provided."} # Ensure country code is provided

    try:
        # Construct the absolute path to the JSON file
        script_dir = os.path.dirname(os.path.abspath(__file__))  # Directory of the current script
        json_path = os.path.join(script_dir, json_file_path)

        with open(json_path, 'r') as f:
            keys_data = json.load(f)
            api_key = keys_data.get('YOUR_NEWSAPI_API_KEY')

        if not api_key:
            return {'error': "API key not found in JSON file or 'YOUR_NEWSAPI_API_KEY' key is missing."}

    except FileNotFoundError:
        return {'error': f"JSON file not found at path: {json_path}"}
    except json.JSONDecodeError:
        return {'error': f"Error decoding JSON from file: {json_path}. Please ensure it's valid JSON."}
    except Exception as e: # Catch other potential exceptions during file reading
        return {'error': f"An unexpected error occurred while reading the JSON file: {e}"}


    url = f'{base_url}country={country}&apiKey={api_key}'

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        news_data = response.json()

        if news_data.get('status') == 'ok' and news_data.get('articles'):
            return news_data # Returns the entire JSON response as a dictionary
        elif news_data.get('status') == 'ok' and not news_data.get('articles'):
            return {} # Return empty dictionary if no headlines are found but the request was successful
        else:
            return {'error': f"API request failed: {news_data.get('message', 'Unknown error')}"} # Error from API

    except requests.exceptions.RequestException as e:
        return {'error': f"Request Exception: {e}"} # Handle network errors, timeouts, etc.

def calculate(expression):
    """
    Calculates the result of a mathematical expression according to BODMAS.

    Args:
        expression: The mathematical expression as a string.

    Returns:
        The calculated result as a string, or an error message string.
    """

    def evaluate_expression(expr):
        """
        Evaluates a simplified expression (without parentheses or exponents).
        """
        try:
            tokens = re.findall(r"[\d.]+|\*\*|\*|/|\+|-", expr) # added ** for exponents
            stack = []
            operators = []

            def apply_operator():
                if operators:
                    operator = operators.pop()
                    operand2 = stack.pop()
                    operand1 = stack.pop()
                    if operator == "+":
                        result = operand1 + operand2
                    elif operator == "-":
                        result = operand1 - operand2
                    elif operator == "*":
                        result = operand1 * operand2
                    elif operator == "/":
                        if operand2 == 0:
                            return "Error: Division by zero"
                        result = operand1 / operand2
                    elif operator == "**": # added exponent handling
                        result = operand1 ** operand2
                    stack.append(result)

            precedence = {"**": 3, "*": 2, "/": 2, "+": 1, "-": 1}

            for token in tokens:
                if token in "+-*/**":
                    while operators and precedence.get(operators[-1], 0) >= precedence[token]:
                        error = apply_operator()
                        if error:
                           return error
                    operators.append(token)
                else:
                    stack.append(float(token))

            while operators:
                error = apply_operator()
                if error:
                    return error

            if len(stack) != 1:
                return "Error: Invalid expression"
            return stack[0]

        except ValueError:
            return "Error: Invalid expression"

    def handle_parentheses(expr):
        """
        Handles parentheses within the expression.
        """
        while "(" in expr:
            start = expr.rfind("(")
            end = expr.find(")", start)
            if end == -1:
                return "Error: Unmatched parentheses"
            sub_expr = expr[start + 1:end]
            sub_result = calculate(sub_expr)
            if sub_result.startswith("Error"):
                return sub_result
            expr = expr[:start] + str(sub_result) + expr[end + 1:]
        return expr

    try:
        expr = handle_parentheses(expression)
        result = evaluate_expression(expr)
        return str(result)
    except Exception:
        return "Error: Invalid expression"

CACHE_FILE = "anidb_cache.json"

def load_cache():
    """Loads anime data from the cache file."""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_cache(cache):
    """Saves anime data to the cache file."""
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=4)


tools = {
    "get_weather": {
        "function": {
            "name": "get_weather",
            "description": "Get the current weather conditions in a specified city.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "The name of the city to get weather conditions for. Defaults to Bangalore."
                    }
                },
                "required": []
            }
        },
        "enabled": True,
        "callable": get_weather  # Directly reference the function
    },
    "get_current_time": {
        "function": {
            "name": "get_current_time",
            "description": "Get the current time.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        },
        "enabled": True,
        "callable": get_current_time
    },
    "none_function": {
        "function": {
            "name": "none_function",
            "description": "This function does nothing and returns None. Use when no other function is needed.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        },
        "enabled": True,
        "callable": none_function
    },
    "store_user_information": {
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
        },
        "enabled": True,
        "callable": store_user_information
    },
    "store_contact": {
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
        },
        "enabled": True,
        "callable": store_contact
    },
    "update_contact_information": {
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
        },
        "enabled": True,
        "callable": update_contact_information
    },
    "get_news_articles_from_json_key": {
        "function": {
            "name": "get_news_articles_from_json_key",
            "description": "Use this function to get news articles based on keywords. You can provide keywords as a single string or a list of strings. The function will search for articles related to these keywords using the News API.  The API key is securely imported from a JSON file named 'code/nv.json' in the same directory as the script. This function returns a maximum of the top specified number of most popular news articles related to the keywords within a specified date range, defaulting to the last 10 days. This is useful when the user is asking for news about a specific topic or event and wants to see the most popular articles from recent days.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keywords": {
                        "type": "string",
                        "description": "Keywords to search for in news articles.  Provide a single keyword or a list of keywords. For lists, each keyword should be a separate string."
                    },
                    "search_days": {
                        "type": "integer",
                        "description": "Number of days to search back from today for news articles. Defaults to 10 if not specified. Must be a positive integer."
                    }
                },
                "required": ["keywords"]
            }
        },
        "enabled": True,
        "callable": get_news_articles_from_json_key
    },
    "get_top_headlines": {
        "function": {
            "name": "get_top_headlines",
            "description": "Use this function to get the top headlines from the News API for a specific country.  You need to specify the 2-letter ISO country code (e.g., 'us' for United States, 'in' for India). The API key is securely imported from a JSON file named 'nv.json' in the same directory as the script. This is helpful when the user wants to know the general top news headlines for a particular country.",
            "parameters": {
                "type": "object",
                "properties": {
                    "country": {
                        "type": "string",
                        "description": "The 2-letter ISO 3166-1 country code for top headlines (e.g., 'us', 'gb', 'in', 'ca')."
                    }
                },
                "required": ["country"]
            }
        },
        "enabled": True,
        "callable": get_top_headlines
    },
    "calculate": {
            "function": {
                "name": "calculate",
                "description": "Calculates the result of a mathematical expression according to BODMAS (Brackets, Orders, Division, Multiplication, Addition, Subtraction). Supports basic arithmetic operations (+, -, *, /), parentheses, and exponents (**).", # Added a comma here.
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "The mathematical expression to calculate as a string. For example: '2 * (3 + 4) / 7', '2 + 3 * 4 - 1', '2 ** 3 + 1'."
                        }
                    },
                    "required": ["expression"]
                }
            },
            "enabled": True,
            "callable": calculate
    },
    "get_current_time_location":{
        "function":{
            "name": "get_current_time",
            "description": "Get the current time in a specified city or timezone.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The name of the city or timezone to get the current time for. If no location is provided, the current time in the user's local timezone will be returned."
                    }
                },
                "required": []
            }
        },
        "enabled": True,
        "callable": get_current_time
    }
}