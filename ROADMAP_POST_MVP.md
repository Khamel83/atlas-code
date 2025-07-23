# Atlas Code V5 - Post-MVP Development Roadmap

This document outlines the next phase of development for Atlas Code V5, building upon the completed MVP. The goal is to incrementally implement the advanced features envisioned in the original roadmap, starting with the most critical components.

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
