
# Atlas Code: Dogfooding Workflow

This document describes the process for using Atlas Code to improve its own codebase. This "dogfooding" workflow is designed to accelerate development, optimize costs, and ensure the tool is practical for real-world use.

## 1. Bootstrap Installation Process

The first step is to get a minimal, functional version of Atlas Code running. This version will have basic one-shot capabilities and cost tracking.

```bash
# Stage 1: Initial Setup (Manual)
# Ensure you have a clean, editable installation
python -m venv .venv
source .venv/bin/activate
pip install -e .

# Stage 2: Get minimal Atlas Code working
# Use the most basic model to add initial cost tracking
atlas-code --model cheap --one-shot "in `aider/coders/base_coder.py`, add a print statement to the `run` method to show the model name and number of tokens."

# Stage 3: Verify the bootstrap
# Run a simple command and check for the new output
atlas-code --model cheap --one-shot "What is your name?"
```

## 2. Self-Improvement Prompt Library

Once the bootstrap version is working, use these prompts to have Atlas Code implement its own features. Start with simple, targeted tasks and gradually move to more complex ones.

### Tier 1: Simple, Safe Modifications

*   `atlas-code "Refactor the cost tracking print statement to be a formatted log message."`
*   `atlas-code "In `aider/main.py`, change the default greeting message."`
*   `atlas-code "Add a new command-line argument `--version` that prints the current version."`

### Tier 2: Core Feature Implementation

*   `atlas-code "Implement the tier escalation logic in the `ModelRouter` in `aider/models.py`."`
*   `atlas-code "Optimize the CLI interface for one-shot execution by reducing non-essential output."`
*   `atlas-code "Add a check for a `.atlas-code-config.yml` file to load default settings."`

### Tier 3: Advanced/Risky Modifications (Use with caution)

*   `atlas-code --yolo "Refactor the entire configuration system to use environment variables."`
*   `atlas-code --yolo "Analyze the `sendchat` module and propose a more efficient implementation."`
*   `atlas-code --yolo "Rewrite the main loop in `aider/main.py` to be more modular."`

## 3. Safety Checks and Rollback Procedures

Self-modification is powerful but can be risky. Follow these procedures to minimize problems.

*   **Git is Your Safety Net**: Aider's core strength is its git integration. Atlas Code will inherit this. **Always commit your changes** before running a self-modification command.

    ```bash
    # Before every self-modification command:
    git add .
    git commit -m "Ready to attempt self-modification"
    ```

*   **Use `--diff` for Review**: Before applying any change, use the `--diff` flag to see what Atlas Code is proposing.

    ```bash
    atlas-code --diff "Implement the `--version` flag."
    ```

*   **Rollback Strategy**: If a self-modification breaks the codebase, use git to revert the changes.

    ```bash
    # If the last command broke something:
    git reset --hard HEAD
    ```

## 4. Development Acceleration Techniques

*   **Chain Commands**: Use shell scripting to chain multiple Atlas Code commands together for complex workflows.
*   **Automated Testing**: After each significant self-modification, run the project's test suite to ensure no regressions were introduced.
*   **Analyze, then Implement**: Use Atlas Code to analyze a file (`--one-shot "analyze `path/to/file.py` and describe its purpose"`) before asking it to make changes.
