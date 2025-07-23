#!/usr/bin/env python

import os
import sys
import re
import json

from .openrouter_client import OpenRouterClient

def parse_file_modifications(response_text):
    """Parses the LLM response to find file modification blocks."""
    pattern = r"```([a-zA-Z0-9_\./-]+)\n([\s\S]*?)\n```"
    matches = re.findall(pattern, response_text)
    modifications = {file_path: content for file_path, content in matches}
    return modifications

def load_config(file_path):
    """Loads a JSON configuration file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file not found at {file_path}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in configuration file at {file_path}", file=sys.stderr)
        sys.exit(1)

def main():
    """The main entry point for the Atlas Code V5 agent."""
    # --- API Key Check (Task 2.1.1 & 2.1.2) ---
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: The OPENROUTER_API_KEY environment variable is not set.", file=sys.stderr)
        print("Please get a key from https://openrouter.ai/ and set the environment variable.", file=sys.stderr)
        sys.exit(1)

    # --- Load Configuration Files (Task 1.1.5) ---
    config_dir = os.path.join(os.path.dirname(__file__), "..", "config")
    settings = load_config(os.path.join(config_dir, "settings.json"))
    model_tiers = load_config(os.path.join(config_dir, "model_tiers.json"))
    intent_routes = load_config(os.path.join(config_dir, "intent_routes.json"))

    # --- Initialize OpenRouter Client ---
    client = OpenRouterClient(api_key, model_tiers)

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

            # --- LLM Integration (Task 2.4.1, 2.4.2, 2.4.3) ---
            if not file_context:
                print("Please add at least one file to the context with /add <file_path>", file=sys.stderr)
                continue

            # Prepare the messages for the LLM
            messages = []
            context_str = "\n".join([f"--- {path} ---\n{content}" for path, content in file_context.items()])
            system_prompt = (
                f"You are an expert programmer. The user has provided the following file(s) as context:\n\n{context_str}\n\n"
                "When you provide code to modify a file, you MUST use the following format, including the file path:\n"
                "```path/to/your/file.py\n"
                "# Your code here\n"
                "```\n"
                "You can provide multiple blocks for multiple files."
            )
            messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": user_input})

            # Hardcoded model for the MVP (will be replaced by routing)
            model = settings["default_model"]

            print(f"\nAssistant (using {model}):", end="", flush=True)
            full_response = ""
            for chunk in client.send_request(model, messages):
                print(chunk, end="", flush=True)
                full_response += chunk
            print("\n")

            # --- File Writing (Task 2.5.1, 2.5.2, 2.5.3, 2.5.4) ---
            modifications = parse_file_modifications(full_response)
            if modifications:
                print("The assistant proposed the following changes:")
                for file_path, content in modifications.items():
                    print(f"\n--- Changes for {file_path} ---")
                    # For simplicity, we print the whole new content. A diff would be better.
                    print(content)
                    print("---------------------------")
                
                confirm = input("Apply these changes? [y/N] ").lower()
                if confirm in ["y", "yes"]:
                    for file_path, content in modifications.items():
                        try:
                            with open(file_path, "w", encoding="utf-8") as f:
                                f.write(content)
                            print(f"Applied changes to {file_path}")
                        except Exception as e:
                            print(f"Error writing to file {file_path}: {e}", file=sys.stderr)
                    # Update the in-memory context as well
                    file_context.update(modifications)

        except (KeyboardInterrupt, EOFError):
            break

    print("\nGoodbye!")

if __name__ == "__main__":
    main()
