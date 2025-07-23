# Ralex - MVP Development Plan

This document outlines the detailed, task-by-task plan to develop the Minimum Viable Product (MVP) for Atlas Code V5. The goal is to create a functional, well-documented, and stable foundation that clearly demonstrates the project's core value proposition.

The plan is designed to be executed by an AI assistant, with each task being atomic and resulting in a single commit.

---

## Phase 1: Foundational Documentation & Project Identity

**Goal:** To create crystal-clear documentation that defines what V5 is, why it's useful, and how it works at a high level. This phase is critical for setting the project's direction.

### Epic 1.1: Solidify the `README.md`

The `README.md` is the front door to the project. It must be clear, concise, and compelling.

- [ ] **Task 1.1.1:** Overhaul the main title and introduction in `README.md` to crisply define Atlas Code V5 as a "terminal-native, agentic coding assistant."
- [ ] **Task 1.1.2:** Create a new section titled "Why Use Atlas Code?" in `README.md`. This section will detail the three core value propositions:
    -   **Cost-Effective:** Explain the budget-aware, dynamic model routing.
    -   **Control & Privacy:** Emphasize the local-first architecture.
    -   **Flexibility:** Describe the model-agnostic approach via OpenRouter.
- [ ] **Task 1.1.3:** Create a new section titled "Core Concepts" in `README.md`. This section will briefly explain:
    -   The **Semantic Router**: How it analyzes user intent.
    -   The **Dynamic Dispatcher**: How it selects the best model for the job.
    -   The **Agentic Engine**: How it interacts with the file system to carry out tasks.
- [ ] **Task 1.1.4:** Add a placeholder "Getting Started" section to `README.md` that we will fill in during Phase 3.
- [ ] **Task 1.1.5:** Commit the updated `README.md` with the message: `docs: Overhaul README with core concepts and value proposition`.

### Epic 1.2: Establish Contributor Guidelines

To ensure consistency, we need a basic set of guidelines.

- [ ] **Task 1.2.1:** Create a new file named `CONTRIBUTING.md`.
- [ ] **Task 1.2.2:** Add a section explaining the development philosophy: one change, one commit.
- [ ] **Task 1.2.3:** Add a placeholder section for "Running Tests."
- [ ] **Task 1.2.4:** Commit the new file with the message: `docs: Create initial CONTRIBUTING.md`.

---

## Phase 2: Core Engine Implementation (MVP)

**Goal:** To build the absolute minimum set of features required to make the agent functional and demonstrate its core loop.

### Epic 2.1: Configuration and API Key Management

The agent needs to be configured with an API key to function.

- [ ] **Task 2.1.1:** Modify `atlas_core/launcher.py` (or the appropriate configuration file) to securely read the `OPENROUTER_API_KEY` from the system's environment variables.
- [ ] **Task 2.1.2:** Implement robust error handling. If the API key is not found, the application should print a user-friendly error message and exit gracefully.
- [ ] **Task 2.1.3:** Commit the changes with the message: `feat(core): Implement API key handling from environment variable`.

### Epic 2.2: Basic Interactive CLI

The user needs a way to interact with the agent.

- [ ] **Task 2.2.1:** In `atlas_core/launcher.py`, implement a simple, persistent REPL (Read-Eval-Print Loop) that continuously prompts the user for input.
- [ ] **Task 2.2.2:** Implement a special command, `/exit` or `/quit`, that cleanly terminates the application.
- [ ] **Task 2.2.3:** Commit the changes with the message: `feat(cli): Implement basic interactive REPL for user input`.

### Epic 2.3: File Context Management

The agent needs to be aware of the files it's supposed to work on.

- [ ] **Task 2.3.1:** Implement a command `/add <file_path>` that allows the user to add a file to the agent's working context.
- [ ] **Task 2.3.2:** The agent should read the content of the specified file and store it in memory for the current session.
- [ ] **Task 2.3.3:** Upon successful addition, the agent should confirm with a message like "Added `file.py` to context."
- [ ] **Task 2.3.4:** Commit the changes with the message: `feat(agent): Implement /add command to load file context`.

### Epic 2.4: First LLM Integration (Hardcoded Model)

This is the first end-to-end test of the core logic.

- [ ] **Task 2.4.1:** Integrate the `atlas_core/openrouter_client.py` with the main CLI loop.
- [ ] **Task 2.4.2:** When the user enters a prompt (that is not a special command), concatenate the prompt with the content of all added files and send it to a hardcoded, low-cost model on OpenRouter (e.g., `mistralai/mistral-7b-instruct-v0.2`).
- [ ] **Task 2.4.3:** Stream the LLM's response back to the user's terminal in real-time.
- [ ] **Task 2.4.4:** Commit the changes with the message: `feat(llm): Implement first end-to-end LLM call`.

### Epic 2.5: Basic File-Writing Capability

The agent must be able to act on its suggestions.

- [ ] **Task 2.5.1:** Define a simple, unambiguous format for the LLM to specify file modifications (e.g., a fenced code block with a file path).
- [ ] **Task 2.5.2:** In the CLI, parse the LLM response to detect this format.
- [ ] **Task 2.5.3:** When a modification is detected, present the proposed change to the user (e.g., show a diff) and ask for confirmation: "Apply changes to `file.py`? [y/N]".
- [ ] **Task 2.5.4:** If the user confirms, overwrite the file with the new content.
- [ ] **Task 2.5.5:** Commit the changes with the message: `feat(agent): Implement file writing with user confirmation`.

---

## Phase 3: User Experience & Onboarding

**Goal:** To make the MVP easy for a new user to install, configure, and run.

### Epic 3.1: Finalize the "Getting Started" Guide

Now that the core features are built, we can write the user manual.

- [ ] **Task 3.1.1:** Update the "Getting Started" section in `README.md` with a complete, step-by-step guide.
- [ ] **Task 3.1.2:** The guide must include:
    -   How to clone the repository.
    -   How to set the `OPENROUTER_API_KEY` environment variable.
    -   How to install dependencies (from the new `requirements.txt`).
    -   A full, copy-pasteable example of a common workflow (`python -m atlas_core.launcher`, `/add file.py`, "refactor this function", `y`).
- [ ] **Task 3.1.3:** Commit the changes with the message: `docs: Complete Getting Started guide in README`.

### Epic 3.2: Dependency Management

- [ ] **Task 3.2.1:** Consolidate all essential runtime dependencies into a single, clean `requirements.txt` file at the project root.
- [ ] **Task 3.2.2:** Remove or archive any old `requirements-*.txt` files that are no longer relevant to the V5 MVP.
- [ ] **Task 3.2.3:** Commit the changes with the message: `chore: Consolidate dependencies into a single requirements.txt`.

---

## Phase 4: Validation & Release Preparation

**Goal:** To package the MVP for easy testing and mark a stable release point.

### Epic 4.1: Create a Test Script

- [ ] **Task 4.1.1:** Create a shell script named `run_mvp.sh` that automates the setup and execution process for a new user.
- [ ] **Task 4.1.2:** The script should check if the `OPENROUTER_API_KEY` is set, run `pip install -r requirements.txt`, and then launch the agent.
- [ ] **Task 4.1.3:** Commit the script with the message: `feat(dev): Add run_mvp.sh for easy testing`.

### Epic 4.2: Tag the MVP Release

- [ ] **Task 4.2.1:** Once all previous tasks are completed and verified, create a lightweight git tag for the MVP release.
- [ ] **Task 4.2.2:** Execute the command: `git tag v5.0.0-mvp`.
- [ ] **Task 4.2.3:** Push the tag to the remote repository with `git push origin v5.0.0-mvp`.
- [ ] **Task 4.2.4:** The final commit message for this phase will be: `chore: Tag v5.0.0-mvp release`.
