import ollama

def run_agent(model, system_prompt, history, user_message):
    """Runs an agent with a given prompt, history, and message."""
    full_prompt = f"{system_prompt}\n"
    for msg in history:
        full_prompt += f"{msg['role']}: {msg['content']}\n"
    full_prompt += f"user: {user_message}"

    response = ollama.chat(model=model, messages=[
        {
            'role': 'user',
            'content': full_prompt,
        },
    ])

    agent_response = response['message']['content']
    history.append({'role': 'user', 'content': user_message})
    history.append({'role': 'assistant', 'content': agent_response})
    return agent_response, history

# Model to use
model_name = 'dolphin3'  # or 'mistral', etc.

# Agent 1 (e.g., a helpful assistant)
agent1_system_prompt = "You are a helpful and friendly assistant."
agent1_history = []

# Agent 2 (e.g., a creative writer)
agent2_system_prompt = "You are a creative writer, skilled in crafting stories."
agent2_history = []

# Example conversation flow
user_input = "Hello!"

# Agent 1 responds
agent1_response, agent1_history = run_agent(model_name, agent1_system_prompt, agent1_history, user_input)
print(f"Agent 1: {agent1_response}")

# Agent 2 responds to a related query
agent2_response, agent2_history = run_agent(model_name, agent2_system_prompt, agent2_history, "Write a short story about a person who finds a magical item.")
print(f"Agent 2: {agent2_response}")

# Agent 1 responds to Agent 2's story, for example.
agent1_response, agent1_history = run_agent(model_name, agent1_system_prompt, agent1_history, "That sounds interesting! Can you give me a summary?")
print(f"Agent 1: {agent1_response}")

print(agent1_history)
print()
print(agent2_history)