import agent   # Assuming your agent class is in agent.py
import tools  # Assuming your tools are in tools.py


def display_help():
    """Displays available commands."""
    print("Available commands:")
    print("/exit - Exit the program")
    print("/help - Display this help message")

if __name__ == "__main__":
    config_file = "pixy_config.json"
    ai = agent.load_agent_from_json(config_file)

    if ai:
        display_help()
        while True:
            user_input = input("input: ")
            user_input_lower = user_input.lower()

            if user_input_lower == "/exit":
                break
            elif user_input_lower == "/help":
                display_help()
            else:
                print("pixy:" + ai.run("user name: suhas \n"+ user_input))