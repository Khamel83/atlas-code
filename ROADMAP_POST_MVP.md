# Ralex - Post-MVP Development Roadmap

This document outlines the next phase of development for Ralex, building upon the completed MVP. The goal is to incrementally implement the advanced features envisioned in the original roadmap, starting with the most critical components.

Each phase is designed to deliver a significant, verifiable enhancement to the agent's capabilities.

---

## Phase 1: Configuration and Intent-Based Routing

**Goal:** To move beyond a hardcoded model and implement a basic, configuration-driven routing system. This is the first step towards intelligent model dispatch.

### Epic 1.1: Externalize Configuration

The agent's behavior should be driven by external configuration files, not hardcoded values.

- [ ] **Task 1.1.1:** Create a `config` directory at the project root.
- [ ] **Task 1.1.2:** Create `config/settings.json` to hold general application settings (e.g., default model, temperature).
- [ ] **Task 1.1.3:** Create `config/model_tiers.json` to define different tiers of models (e.g., `cheap`, `standard`, `premium`) and their associated costs.
- [ ] **Task 1.1.4:** Create `config/intent_routes.json` to map user intents (e.g., `generate`, `edit`, `debug`) to specific model tiers.
- [ ] **Task 1.1.5:** Modify the application to load these configuration files at startup.
- [ ] **Task 1.1.6:** Commit the changes with the message: `feat(config): Externalize configuration into JSON files`.

### Epic 1.2: Simple Intent-Based Routing

Based on the user's prompt, the agent should select a model tier from the configuration.

- [ ] **Task 1.2.1:** Implement a simple keyword-based intent classifier. For example, if the prompt contains "fix" or "debug", classify the intent as `debug`.
- [ ] **Task 1.2.2:** Based on the classified intent, use the `intent_routes.json` to select a model tier.
- [ ] **Task 1.2.3:** From the selected tier, choose the first available model in `model_tiers.json`.
- [ ] **Task 1.2.4:** Use this dynamically selected model for the OpenRouter API call, instead of the hardcoded one.
- [ ] **Task 1.2.5:** Commit the changes with the message: `feat(router): Implement simple intent-based model routing`.

---

## Phase 2: Enhanced User Experience & Safety

**Goal:** To make the agent more interactive, informative, and safe to use.

### Epic 2.1: Pre-Execution Dry Run

Before making an API call, the agent should inform the user of its plan.

- [ ] **Task 2.1.1:** After classifying the intent and selecting a model, print a summary to the user (e.g., "Intent: `debug`, Model: `anthropic/claude-3.5-sonnet`").
- [ ] **Task 2.1.2:** Ask the user for confirmation before proceeding with the API call.
- [ ] **Task 2.1.3:** Commit the changes with the message: `feat(cli): Implement pre-execution dry run and confirmation`.

### Epic 2.2: Unified Diff Preview

Instead of printing the entire new file content, show a diff of the proposed changes.

- [ ] **Task 2.2.1:** After receiving the LLM response, generate a unified diff between the original file content and the proposed new content.
- [ ] **Task 2.2.2:** Display the colorized diff to the user for review.

- [ ] **Task 2.2.3:** Commit the changes with the message: `feat(agent): Display unified diff for file modifications`.

---

## Phase 3: Advanced Agentic Capabilities

**Goal:** To introduce more sophisticated agentic behaviors, such as multi-file operations and context management.

### Epic 3.1: Multi-File Context

The agent should be able to reason about multiple files at once.

- [ ] **Task 3.1.1:** The `/add` command should support adding multiple files at once (e.g., `/add file1.py file2.py`).
- [ ] **Task 3.1.2:** The agent should be able to receive and apply modifications for multiple files in a single response.
- [ ] **Task 3.1.3:** Commit the changes with the message: `feat(agent): Enable multi-file context and modifications`.

### Epic 3.2: Session Memory

The agent should remember the conversation history within a single session.

- [ ] **Task 3.2.1:** Store the history of user prompts and assistant responses in a session-specific list.
- [ ] **Task 3.2.2:** On each new request, include the recent conversation history in the messages sent to the LLM.
- [ ] **Task 3.2.3:** Commit the changes with the message: `feat(agent): Implement in-session conversation memory`.

---

## Phase 4: Semantic Search & Intelligence

**Goal:** To move beyond simple keyword matching and implement a true semantic understanding of the user's intent.

### Epic 4.1: Semantic Intent Classification

- [ ] **Task 4.1.1:** Integrate the `sentence-transformers` library.
- [ ] **Task 4.1.2:** Create a set of example prompts for each intent and pre-compute their embeddings.
- [ ] **Task 4.1.3:** When a new user prompt is received, compute its embedding and find the closest matching intent via vector similarity.
- [ ] **Task 4.1.4:** Use this semantically classified intent to drive the model routing.
- [ ] **Task 4.1.5:** Commit the changes with the message: `feat(router): Implement semantic intent classification`.

---

## Phase 5: Advanced Budget Optimizer

**Goal:** To implement real-time cost control with intelligent downgrades and spending analytics.

### Epic 5.1: Basic Budget Tracking and Persistence

The agent needs to track usage and persist it across sessions.

- [ ] **Task 5.1.1:** Create `ralex_core/budget_optimizer.py` with a `BudgetOptimizer` class.
- [ ] **Task 5.1.2:** Implement a method `record_usage(model, tokens_sent, tokens_received, cost)` in `BudgetOptimizer` that saves usage data to a simple JSON file (e.g., `data/usage_log.jsonl`).
- [ ] **Task 5.1.3:** Implement a method `get_total_spent()` in `BudgetOptimizer` that reads and sums costs from the usage log.
- [ ] **Task 5.1.4:** Integrate `BudgetOptimizer` into `ralex_core/launcher.py` to record usage after each successful LLM call.
- [ ] **Task 5.1.5:** Commit the changes with the message: `feat(budget): Implement basic budget tracking and persistence`.

### Epic 5.2: Budget Limits and Warnings

The agent should warn the user when approaching or exceeding budget limits.

- [ ] **Task 5.2.1:** Add a `daily_limit` setting to `config/settings.json`.
- [ ] **Task 5.2.2:** Implement a method `check_budget_status()` in `BudgetOptimizer` that compares current spending against the `daily_limit` and returns a status (e.g., `safe`, `warning`, `exceeded`).
- [ ] **Task 5.2.3:** Modify `ralex_core/launcher.py` to call `check_budget_status()` before making an LLM call and display a warning if necessary.
- [ ] **Task 5.2.4:** If the budget is exceeded, prompt the user for confirmation to proceed.
- [ ] **Task 5.2.5:** Commit the changes with the message: `feat(budget): Add budget limits and warnings`.

---

## Phase 6: Direct Code Executor

**Goal:** To enable the agent to generate and execute code directly within a safe environment.

### Epic 6.1: Basic Code Execution Framework

The agent needs a way to execute code snippets.

- [ ] **Task 6.1.1:** Create `ralex_core/code_executor.py` with a `CodeExecutor` class.
- [ ] **Task 6.1.2:** Implement a method `execute_python_code(code: str) -> dict` in `CodeExecutor` that runs Python code using `subprocess` and captures stdout/stderr.
- [ ] **Task 6.1.3:** Modify `ralex_core/launcher.py` to allow the LLM to output code blocks that can be executed by the `CodeExecutor`. This will involve defining a new LLM output format (e.g., ````python\nprint("hello")\n````) and parsing it.
- [ ] **Task 6.1.4:** Integrate `CodeExecutor` into `ralex_core/launcher.py` to execute these code blocks after user confirmation.
- [ ] **Task 6.1.5:** Commit the changes with the message: `feat(executor): Implement basic Python code execution framework`.

### Epic 6.2: Safe Execution Environment

Ensure code execution is safe and does not harm the host system.

- [ ] **Task 6.2.1:** Modify `execute_python_code` to run code in a temporary directory to prevent unintended file system modifications.
- [ ] **Task 6.2.2:** Implement a timeout for code execution to prevent infinite loops.
- [ ] **Task 6.2.3:** Add basic sandboxing (e.g., restricting imports, though full sandboxing is complex and might be a later phase). For MVP, focus on temporary directory and timeout.
- [ ] **Task 6.2.4:** Commit the changes with the message: `feat(executor): Add basic sandboxing and timeout for code execution`.

### Epic 6.3: Code Execution Feedback

Provide clear feedback on code execution results.

- [ ] **Task 6.3.1:** Display the stdout and stderr from code execution to the user.
- [ ] **Task 6.3.2:** Indicate whether the execution was successful or failed.
- [ ] **Task 6.3.3:** Commit the changes with the message: `feat(executor): Provide execution feedback to user`.

---

## Phase 7: Advanced CLI Interface

**Goal:** To build a more robust and user-friendly command-line interface, moving beyond the simple REPL.

### Epic 7.1: Command-Line Argument Parsing

The agent should accept commands and arguments directly from the command line.

- [ ] **Task 7.1.1:** Modify `ralex_core/launcher.py` to use `argparse` for command-line argument parsing.
- [ ] **Task 7.1.2:** Define top-level commands for `run` (to start the interactive REPL) and `execute` (to run a single task non-interactively).
- [ ] **Task 7.1.3:** For the `execute` command, define arguments for `intent`, `prompt`, and `files`.
- [ ] **Task 7.1.4:** Adjust the `main` function to handle both interactive and non-interactive modes based on parsed arguments.
- [ ] **Task 7.1.5:** Commit the changes with the message: `feat(cli): Implement argparse for command-line operations`.

### Epic 7.2: Non-Interactive Execution

Allow users to run a single task directly from the command line without entering the REPL.

- [ ] **Task 7.2.1:** In non-interactive mode, execute the LLM call and file modifications/code execution based on the provided command-line arguments.
- [ ] **Task 7.2.2:** Print the results (e.g., success/failure, diffs, execution output) and exit.
- [ ] **Task 7.2.3:** Commit the changes with the message: `feat(cli): Enable non-interactive task execution`.

### Epic 7.3: Basic Help and Version Information

Provide standard CLI help and version information.

- [ ] **Task 7.3.1:** Add a `--help` argument that displays usage information for all commands and arguments.
- [ ] **Task 7.3.2:** Add a `--version` argument that displays the current version of Ralex.
- [ ] **Task 7.3.3:** Commit the changes with the message: `feat(cli): Add help and version arguments`.
