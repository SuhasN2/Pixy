def get_multiline_input(prompt="Enter text (Shift+Enter for new line, Enter to finish):"):
    """
    Reads lines from standard input. Shift+Enter creates a new line in the input,
    and pressing Enter on an empty line will stop the input.

    Args:
        prompt (str, optional): A message displayed once before reading begins.
                                   Defaults to "Enter text (Shift+Enter for new line, Enter to finish):".

    Returns:
        str: A single string containing all the input lines entered,
             with each original line separated by a newline character.
    """
    print(prompt, end="")
    lines = []
    while True:
        try:
            line = input()
            if not line:
                break  # Empty line, stop reading
            lines.append(line)
        except EOFError:
            # Handle potential EOFError if input is redirected
            break
        except KeyboardInterrupt:
            # Handle Ctrl+C
            break
    return "\n".join(lines)

print(get_multiline_input(":"))