#!/usr/bin/env python

import os
import sys

def main():
    """The main entry point for the Atlas Code V5 agent."""
    # --- API Key Check (Task 2.1.1 & 2.1.2) ---
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: The OPENROUTER_API_KEY environment variable is not set.", file=sys.stderr)
        print("Please get a key from https://openrouter.ai/ and set the environment variable.", file=sys.stderr)
        sys.exit(1)

    # --- File Context (In-memory store) ---
    file_context = {}

    print("Welcome to Atlas Code V5!")
    print("Type /add <file_path> to add a file to context, or /exit to quit.")

    # --- Basic Interactive CLI (Task 2.2.1 & 2.2.2) ---
    while True:
        try:
            user_input = input("> ")
            if user_input.lower() in ["/exit", "/quit"]:
                break

            # --- File Context Management (Task 2.3.1, 2.3.2, 2.3.3) ---
            if user_input.startswith("/add "):
                file_path_str = user_input.split(" ", 1)[1].strip()
                try:
                    with open(file_path_str, "r", encoding="utf-8") as f:
                        file_context[file_path_str] = f.read()
                    print(f"Added '{file_path_str}' to context.")
                except FileNotFoundError:
                    print(f"Error: File not found at '{file_path_str}'", file=sys.stderr)
                except Exception as e:
                    print(f"Error reading file: {e}", file=sys.stderr)
                continue

            # Placeholder for future logic
            print(f"Received: {user_input}")

        except (KeyboardInterrupt, EOFError):
            break

    print("\nGoodbye!")

if __name__ == "__main__":
    main()
