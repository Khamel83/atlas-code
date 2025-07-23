# Atlas Code V5

**A self-contained, terminal-native, intelligent agentic coding assistant.**

Atlas Code V5 is a standalone coding assistant that runs entirely in your terminal. It uses a sophisticated semantic routing system to understand your requests and dispatch them to the most appropriate large language model via OpenRouter. The agent's logic is designed to be modular and extensible, inspired by the AgentOS framework.

## Core Architecture

- **Semantic Routing:** Intents are classified semantically to ensure the right model is used for the right task.
- **Dynamic Model Dispatch:** Models are dynamically selected from OpenRouter based on the task's requirements.
- **Terminal-First:** The entire user interface is within the terminal, providing a lightweight and efficient experience.
- **Modular Agent Logic:** The agent's execution logic is broken down into modular components, making it easy to extend and maintain.
- **Zero Runtime Dependencies:** Beyond OpenRouter and standard Python libraries, Atlas Code V5 requires no additional runtime dependencies.

## Getting Started

To run the Atlas Code V5 CLI, you will need to have Python installed. Once you have cloned the repository, you can run the agent from the root directory:

```bash
python -m atlas_core.launcher
```

## Project Roadmap

For a detailed overview of the project's future direction, please see the [V5 Comprehensive Roadmap](archive/V5-COMPREHENSIVE-ROADMAP.md).
