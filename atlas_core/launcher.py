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

    print("Welcome to Atlas Code V5!")
    print("Type your request, or /exit to quit.")

    # --- Basic Interactive CLI (Task 2.2.1 & 2.2.2) ---
    while True:
        try:
            user_input = input("> ")
            if user_input.lower() in ["/exit", "/quit"]:
                break
            # Placeholder for future logic
            print(f"Received: {user_input}")

        except (KeyboardInterrupt, EOFError):
            break

    print("\nGoodbye!")

if __name__ == "__main__":
    main()
