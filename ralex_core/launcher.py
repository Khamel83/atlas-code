#!/usr/bin/env python

import os
import sys
import re
import json
import difflib
import argparse

from ralex_core.openrouter_client import OpenRouterClient
from ralex_core.semantic_classifier import SemanticClassifier
from ralex_core.budget_optimizer import BudgetOptimizer
from ralex_core.code_executor import CodeExecutor

def parse_file_modifications(response_text):
    """Parses the LLM response to find file modification blocks."""
    pattern = r"```([a-zA-Z0-9_\./-]+)\n([\s\S]*?)\n```"
    matches = re.findall(pattern, response_text)
    modifications = {file_path: content for file_path, content in matches}
    return modifications

def parse_code_blocks(response_text):
    """Parses the LLM response to find executable code blocks."""
    pattern = r"```(python|bash|sh)\n([\s\S]*?)\n```"
    matches = re.findall(pattern, response_text)
    code_blocks = []
    for lang, code in matches:
        code_blocks.append({"language": lang, "code": code})
    return code_blocks

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

def classify_intent(user_input):
    """Classifies user input into a predefined intent based on keywords."""
    user_input_lower = user_input.lower()
    if "debug" in user_input_lower or "fix" in user_input_lower or "error" in user_input_lower:
        return "debug"
    elif "generate" in user_input_lower or "create" in user_input_lower or "build" in user_input_lower:
        return "generate"
    elif "edit" in user_input_lower or "modify" in user_input_lower or "change" in user_input_lower:
        return "edit"
    elif "review" in user_input_lower or "analyze" in user_input_lower or "suggest" in user_input_lower:
        return "review"
    elif "optimize" in user_input_lower or "performance" in user_input_lower or "faster" in user_input_lower:
        return "optimize"
    elif "format" in user_input_lower or "style" in user_input_lower or "lint" in user_input_lower:
        return "format"
    elif "explain" in user_input_lower or "document" in user_input_lower or "how to" in user_input_lower:
        return "explain"
    else:
        return "default"

def run_interactive_mode(settings, model_tiers, intent_routes, client, semantic_classifier, budget_optimizer):
    """Runs the interactive CLI mode."""
    file_context = {}
    conversation_history = []
    code_executor = CodeExecutor()

    print("Welcome to Ralex!")
    print("Type /add <file_path> to add a file to context, or /exit to quit.")

    while True:
        try:
            user_input = input("> ")
            if user_input.lower() in ["/exit", "/quit"]:
                break

            # --- File Context Management (Task 2.3.1, 2.3.2, 2.3.3) ---
            if user_input.startswith("/add "):
                file_paths_str = user_input.split(" ", 1)[1].strip()
                for file_path_str in file_paths_str.split(): # Split by space to handle multiple files
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
            messages.extend(conversation_history) # Add previous conversation
            messages.append({"role": "user", "content": user_input})

            # --- Intent Classification and Model Selection (Task 1.2.1, 1.2.2, 1.2.3, 1.2.4) ---
            # First, try semantic classification
            semantic_intent, confidence = semantic_classifier.classify(user_input)
            if confidence > 0.7: # Use semantic if confident enough
                intent = semantic_intent
            else:
                # Fallback to keyword-based classification
                intent = classify_intent(user_input)

            tier = intent_routes.get(intent, "default")
            
            selected_model = None
            if tier in model_tiers["tiers"] and model_tiers["tiers"][tier]:
                selected_model = model_tiers["tiers"][tier][0]["name"]
            
            if not selected_model:
                print(f"Error: No model found for tier '{tier}'. Please check your model_tiers.json and intent_routes.json.", file=sys.stderr)
                continue

            # --- Pre-execution Dry Run and Confirmation (Task 2.1.1 & 2.1.2) ---
            print(f"\nProposed Action: Intent '{intent}' using model '{selected_model}' (tier: {tier})")
            
            # --- Budget Check (Task 5.2.3 & 5.2.4) ---
            budget_status = budget_optimizer.check_budget_status()
            if budget_status["status"] == "warning":
                print(f"\n⚠️  Budget Warning: You have spent ${budget_status["spent_today"]:.2f} today out of your ${budget_status["daily_limit"]:.2f} daily limit ({budget_status["percentage_used"]:.2f}% used).")
            elif budget_status["status"] == "exceeded":
                print(f"\n🚨 Budget Exceeded: You have spent ${budget_status["spent_today"]:.2f} today out of your ${budget_status["daily_limit"]:.2f} daily limit ({budget_status["percentage_used"]:.2f}% used).")
                confirm = input("You have exceeded your daily budget. Proceed anyway? [y/N] ").lower()
                if confirm != 'y':
                    print("Action cancelled due to budget.")
                    continue

            confirm = input("Proceed with this action? [Y/n] ").lower()
            if confirm == 'n':
                print("Action cancelled.")
                continue

            print(f"\nAssistant (using {selected_model}, intent: {intent}, tier: {tier}):", end="", flush=True)
            full_response = ""
            for chunk in client.send_request(selected_model, messages):
                print(chunk, end="", flush=True)
                full_response += chunk
            print("\n")

            # --- Code Execution (Task 6.1.3 & 6.1.4) ---
            code_blocks = parse_code_blocks(full_response)
            if code_blocks:
                print("The assistant proposed the following code to execute:")
                for i, block in enumerate(code_blocks):
                    print(f"\n--- Code Block {i+1} ({block["language"]}) ---")
                    print(block["code"])
                    print("---------------------------")
                
                confirm_exec = input("Execute this code? [y/N] ").lower()
                if confirm_exec in ["y", "yes"]:
                    for block in code_blocks:
                        if block["language"] == "python":
                            print(f"\nExecuting Python code...")
                            exec_result = code_executor.execute_python_code(block["code"])
                            if exec_result["success"]:
                                print("Execution successful.")
                                if exec_result["stdout"]:
                                    print("Stdout:\n" + exec_result["stdout"])
                                if exec_result["stderr"]:
                                    print("Stderr:\n" + exec_result["stderr"])
                            else:
                                print("Execution failed.")
                                if exec_result["stdout"]:
                                    print("Stdout:\n" + exec_result["stdout"])
                                if exec_result["stderr"]:
                                    print("Stderr:\n" + exec_result["stderr"])
                        else:
                            print(f"Execution of {block["language"]} code is not yet supported.")

            # Update conversation history (Task 3.2.1)
            conversation_history.append({"role": "user", "content": user_input})
            conversation_history.append({"role": "assistant", "content": full_response})

            # Record usage (Task 5.1.4)
            # For simplicity, estimating tokens based on response length. Real implementation would use tokenizers.
            estimated_tokens_sent = len(str(messages).split()) # Very rough estimate
            estimated_tokens_received = len(full_response.split()) # Very rough estimate
            cost_per_token = 0.0 # Placeholder, will get from model_tiers later
            for t in model_tiers["tiers"][tier]:
                if t["name"] == selected_model:
                    cost_per_token = t["cost_per_token"]
                    break
            estimated_cost = (estimated_tokens_sent + estimated_tokens_received) * cost_per_token
            budget_optimizer.record_usage(selected_model, estimated_tokens_sent, estimated_tokens_received, estimated_cost)

            # --- File Writing with Diff Preview (Task 2.2.1, 2.2.2, 2.5.1, 2.5.2, 2.5.3, 2.5.4) ---
            modifications = parse_file_modifications(full_response)
            if modifications:
                print("The assistant proposed the following changes:")
                for file_path, new_content in modifications.items():
                    original_content = ""
                    if os.path.exists(file_path):
                        with open(file_path, "r", encoding="utf-8") as f:
                            original_content = f.read()

                    diff = difflib.unified_diff(
                        original_content.splitlines(keepends=True),
                        new_content.splitlines(keepends=True),
                        fromfile=file_path + " (original)",
                        tofile=file_path + " (proposed)"
                    )
                    print(f"\n--- Diff for {file_path} ---")
                    for line in diff:
                        if line.startswith('+'):
                            print(f"\033[92m{line}\033[0m", end="") # Green
                        elif line.startswith('-'):
                            print(f"\033[91m{line}\033[0m", end="") # Red
                        elif line.startswith('@'):
                            print(f"\033[94m{line}\033[0m", end="") # Blue
                        else:
                            print(line, end="")
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

def run_non_interactive_mode(args, settings, model_tiers, intent_routes, client, semantic_classifier, budget_optimizer):
    """Runs the non-interactive CLI mode."""
    file_context = {}
    code_executor = CodeExecutor()

    # Load files into context if provided
    if args.files:
        for file_path_str in args.files:
            try:
                with open(file_path_str, "r", encoding="utf-8") as f:
                    file_context[file_path_str] = f.read()
                print(f"Added '{file_path_str}' to context.")
            except FileNotFoundError:
                print(f"Error: File not found at '{file_path_str}'", file=sys.stderr)
                sys.exit(1)
            except Exception as e:
                print(f"Error reading file: {e}", file=sys.stderr)
                sys.exit(1)

    if not file_context and not args.intent == "generate": # For generate, file context might not be needed initially
        print("Error: Please add at least one file to the context with --files or use the 'generate' intent.", file=sys.stderr)
        sys.exit(1)

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
    messages.append({"role": "user", "content": args.prompt})

    # --- Intent Classification and Model Selection ---
    semantic_intent, confidence = semantic_classifier.classify(args.prompt)
    if confidence > 0.7:
        intent = semantic_intent
    else:
        intent = classify_intent(args.prompt)

    tier = intent_routes.get(intent, "default")
    selected_model = None
    if tier in model_tiers["tiers"] and model_tiers["tiers"][tier]:
        selected_model = model_tiers["tiers"][tier][0]["name"]

    if not selected_model:
        print(f"Error: No model found for tier '{tier}'. Please check your model_tiers.json and intent_routes.json.", file=sys.stderr)
        sys.exit(1)

    print(f"\nProposed Action: Intent '{intent}' using model '{selected_model}' (tier: {tier})")
    
    # --- Budget Check ---
    budget_status = budget_optimizer.check_budget_status()
    if budget_status["status"] == "warning":
        print(f"\n⚠️  Budget Warning: You have spent ${budget_status["spent_today"]:.2f} today out of your ${budget_status["daily_limit"]:.2f} daily limit ({budget_status["percentage_used"]:.2f}% used).")
    elif budget_status["status"] == "exceeded":
        print(f"\n🚨 Budget Exceeded: You have spent ${budget_status["spent_today"]:.2f} today out of your ${budget_status["daily_limit"]:.2f} daily limit ({budget_status["percentage_used"]:.2f}% used).")
        # In non-interactive mode, we don't prompt, just warn and exit if not forced
        if not args.force_budget:
            print("Action cancelled due to budget. Use --force-budget to override.", file=sys.stderr)
            sys.exit(1)

    print(f"\nAssistant (using {selected_model}, intent: {intent}, tier: {tier}):", end="", flush=True)
    full_response = ""
    for chunk in client.send_request(selected_model, messages):
        print(chunk, end="", flush=True)
        full_response += chunk
    print("\n")

    # --- Code Execution ---
    code_blocks = parse_code_blocks(full_response)
    if code_blocks:
        print("The assistant proposed the following code to execute:")
        for i, block in enumerate(code_blocks):
            print(f"\n--- Code Block {i+1} ({block["language"]}) ---")
            print(block["code"])
            print("---------------------------")
        
        confirm_exec = input("Execute this code? [y/N] ").lower()
        if confirm_exec in ["y", "yes"]:
            for block in code_blocks:
                if block["language"] == "python":
                    print(f"\nExecuting Python code...")
                    exec_result = code_executor.execute_python_code(block["code"])
                    if exec_result["success"]:
                        print("Execution successful.")
                        if exec_result["stdout"]:
                            print("Stdout:\n" + exec_result["stdout"])
                        if exec_result["stderr"]:
                            print("Stderr:\n" + exec_result["stderr"])
                    else:
                        print("Execution failed.")
                        if exec_result["stdout"]:
                            print("Stdout:\n" + exec_result["stdout"])
                        if exec_result["stderr"]:
                            print("Stderr:\n" + exec_result["stderr"])
                else:
                    print(f"Execution of {block["language"]} code is not yet supported.")

    # Record usage
    estimated_tokens_sent = len(str(messages).split()) # Very rough estimate
    estimated_tokens_received = len(full_response.split()) # Very rough estimate
    cost_per_token = 0.0 # Placeholder, will get from model_tiers later
    for t in model_tiers["tiers"][tier]:
        if t["name"] == selected_model:
            cost_per_token = t["cost_per_token"]
            break
    estimated_cost = (estimated_tokens_sent + estimated_tokens_received) * cost_per_token
    budget_optimizer.record_usage(selected_model, estimated_tokens_sent, estimated_tokens_received, estimated_cost)

    # --- File Writing with Diff Preview ---
    modifications = parse_file_modifications(full_response)
    if modifications:
        print("The assistant proposed the following changes:")
        for file_path, new_content in modifications.items():
            original_content = ""
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    original_content = f.read()

            diff = difflib.unified_diff(
                original_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=file_path + " (original)",
                tofile=file_path + " (proposed)"
            )
            print(f"\n--- Diff for {file_path} ---")
            for line in diff:
                if line.startswith('+'):
                    print(f"\033[92m{line}\033[0m", end="") # Green
                elif line.startswith('-'):
                    print(f"\033[91m{line}\033[0m", end="") # Red
                elif line.startswith('@'):
                    print(f"\033[94m{line}\033[0m", end="") # Blue
                else:
                    print(line, end="")
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