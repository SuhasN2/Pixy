import ollama

def manage_ollama_conversation(model="pixy"):
    """Manages a conversation with Ollama, controlling history."""
    conversation_history = []  # Initialize your history

    while True:
        user_input = input("You: ")

        if user_input.lower() == "/exit" or user_input.lower() == "/bye":
            break

        if user_input.lower() == "/reset":
            conversation_history = []
            print("Conversation history reset.")
            continue

        conversation_history.append({"role": "user", "content": user_input})

        try:
            response = ollama.chat(
                model=model,
                messages=conversation_history, #send the entire history to the model.
            )
            assistant_response = response["message"]["content"]
            print(f"Ollama: {assistant_response}")
            conversation_history.append({"role": "assistant", "content": assistant_response})

            # Example: Sliding window (keep last 3 interactions)
            if len(conversation_history) > 6:
                conversation_history = conversation_history[-6:]

        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    manage_ollama_conversation()  