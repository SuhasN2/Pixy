import requests, json, datetime, re, os, pytz
import logging
# from tool_calling import tool

# Configure logging (add this if you haven't already)
logging.basicConfig(filename='general_tools.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s') # Corrected line

CONFIG_FILEPATH = 'config/AI_config.json'  # Path to your config file
WEATHER_CACHE = {}
WEATHER_CACHE_EXPIRY_HOURS = 1


def load_api_keys(config_filepath: str):
    """Loads API keys from the specified JSON configuration file."""
    try:
        with open(config_filepath, 'r') as f:
            config = json.load(f)
            general_info_config = config.get("general_info", {})
            api_keys = general_info_config.get("api_keys", {})
            return api_keys
    except FileNotFoundError:
        logging.exception(f"Error: Configuration file '{config_filepath}' not found.")
        return {}  # Return empty dict if file not found
    except json.JSONDecodeError as e:
        logging.exception(f"Error: Invalid JSON in '{config_filepath}': {e}")
        return {}  # Return empty dict if JSON is invalid
    except KeyError as e:
        logging.exception(f"Error: Missing key in '{config_filepath}': {e}")
        return {}  # Return empty dict if key is missing


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
        with open('config/nv.json', 'r') as f:
            nv_config = json.load(f)
            api_key = nv_config.get("YOUR_OPENWEATHER_API_KEY")
            print(f"API Key from config/nv.json: {api_key}")
            if not api_key:
                return {"error": "API key not found in config/nv.json. Check 'YOUR_OPENWEATHER_API_KEY' key in file."}
    except FileNotFoundError:
        return {"error": "Error: config/nv.json file not found. Ensure config/nv.json exists in directory."}
    except json.JSONDecodeError:
        return {"error": "Error: Invalid JSON format in config/nv.json. Check config/nv.json is valid JSON."}

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
    
def get_news_articles_from_json_key(keywords, json_file_path='config/nv.json', top_results=5, search_days=10):
    """
    Fetches news articles based on keywords using the News API.
    API key is imported from a JSON file.
    Dynamically updates the 'from' date to search within a specified day range.
    Returns a maximum of the top specified number of results.

    Args:
        keywords (str or list): Keywords to search for in news articles.
                                 If a list is provided, it will be joined into a string.
        json_file_path (str, optional): Path to the JSON file containing API keys.
                                        Defaults to 'config/nv.json' in the same directory.
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
        with open(json_file_path, 'r') as f:
            keys_data = json.load(f)
            api_key = keys_data.get('YOUR_NEWSAPI_API_KEY')

        if not api_key:
            return {'error': "API key not found in JSON file or 'YOUR_NEWSAPI_API_KEY' key is missing."}

    except FileNotFoundError:
        return {'error': f"JSON file not found at path: {json_file_path}"}
    except json.JSONDecodeError:
        return {'error': f"Error decoding JSON from file: {json_file_path}. Please ensure it's valid JSON."}
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


def get_top_headlines(country='us', json_file_path='config/nv.json'):
    """
    Fetches top headlines from the News API for a specific country.
    API key is imported from a JSON file.

    Args:
        country (str, optional): The 2-letter ISO 3166-1 country code for headlines.
                                 Defaults to 'us' (United States).
        json_file_path (str, optional): Path to the JSON file containing API keys.
                                        Defaults to 'config/nv.json' in the same directory.

    Returns:
        dict: A dictionary containing top headlines from the News API, or an error message.
              Returns an empty dictionary if no headlines are found.
    """
    base_url = 'https://newsapi.org/v2/top-headlines?'
    api_key = None

    if not country:
        return {'error': "Country code must be provided."} # Ensure country code is provided

    try:

        with open(json_file_path, 'r') as f:
            keys_data = json.load(f)
            api_key = keys_data.get('YOUR_NEWSAPI_API_KEY')

        if not api_key:
            return {'error': "API key not found in JSON file or 'YOUR_NEWSAPI_API_KEY' key is missing."}

    except FileNotFoundError:
        return {'error': f"JSON file not found at path: {json_file_path}"}
    except json.JSONDecodeError:
        return {'error': f"Error decoding JSON from file: {json_file_path}. Please ensure it's valid JSON."}
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

def get_time():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
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

def test():
    print("#"*64)
    print("="*30,"#"*8,"-"*30)
    print( 100,"=", calculate("(125 + 75)/2"))
    print("="*30,"#"*8,"-"*30)
    print( get_top_headlines(country='us') )
    print("="*30,"#"*8,"-"*30)
    print( get_news_articles_from_json_key("code"))
    print("="*30,"#"*8,"-"*30)
    print( get_current_time(location="Bangalore"))
    print("="*30,"#"*8,"-"*30)
    print( get_weather())
    print("="*30,"#"*8,"-"*30)
    print("#"*64)

tools_config = {
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
            "name": "get_time",
            "description": "Get the current time.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        },
        "enabled": True,
        "callable": get_time
    },
    "get_news_articles_from_json_key": {
        "function": {
            "name": "get_news_articles_from_json_key",
            "description": "Use this function to get news articles based on keywords. You can provide keywords as a single string or a list of strings. The function will search for articles related to these keywords using the News API.  The API key is securely imported from a JSON file named 'config/nv.json' in the same directory as the script. This function returns a maximum of the top specified number of most popular news articles related to the keywords within a specified date range, defaulting to the last 10 days. This is useful when the user is asking for news about a specific topic or event and wants to see the most popular articles from recent days.",
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

def get_enabled_tools(tools_config):
    """
    Generates a new dictionary containing only the enabled tools from the tools_config.

    Args:
        tools_config (dict): The original dictionary containing tool configurations.

    Returns:
        dict: A new dictionary with only the enabled tools.
    """
    enabled_tools = {}
    for tool_name, tool_data in tools_config.items():
        if tool_data["enabled"]:
            enabled_tools[tool_name] = tool_data
    return enabled_tools

# Generate the new dictionary with only enabled tools
available_functions = get_enabled_tools(tools_config)

if __name__ == "__main__":
    test()
    print (available_functions)
