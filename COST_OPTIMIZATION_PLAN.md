
# Atlas Code: Cost Optimization Plan

This document details the strategy for optimizing the operational cost of Atlas Code by implementing a 4-tier model selection system, budget enforcement, and usage analytics.

## 1. 4-Tier Model Selection Algorithm

The core of the cost optimization plan is a 4-tier model selection system. This system will automatically choose the most cost-effective model for a given task. The `ModelRouter` in `aider/models.py` will implement this logic.

*   **Tier 1: `cheap` (e.g., Haiku, GPT-3.5-Turbo)**
    *   **Trigger**: Simple, well-defined tasks; small code changes; analysis of small files.
    *   **Logic**: Default tier for most commands. Selected when the prompt is short and the file context is small.

*   **Tier 2: `regular` (e.g., Claude Sonnet, GPT-4-Turbo)**
    *   **Trigger**: More complex tasks; refactoring; generating new functions or classes.
    *   **Logic**: Selected when the prompt is longer, more complex, or the user explicitly requests it (`--model regular`).

*   **Tier 3: `power` (e.g., Claude Opus, GPT-4)**
    *   **Trigger**: High-stakes tasks; architectural changes; complex bug fixes.
    *   **Logic**: Selected when the user explicitly requests it (`--model power`). Used for tasks requiring deep reasoning.

*   **Tier 4: `smart` (Automated Selection)**
    *   **Trigger**: User does not specify a model.
    *   **Logic**: The `ModelRouter` will analyze the prompt and the context files to automatically select the most appropriate tier. This will involve a simple heuristic based on prompt length, file size, and keywords.

## 2. Budget Enforcement Implementation

To prevent runaway costs, a budget enforcement mechanism will be integrated into the `CostTracker` in `aider/coders/base_coder.py`.

*   **Daily Budget**: A user-configurable daily budget (e.g., `$1.00`) will be stored in a configuration file.
*   **Cost Calculation**: The `CostTracker` will calculate the cost of each model call based on the model's price per token.
*   **Enforcement**: Before each model call, the `CostTracker` will check if the call would exceed the daily budget. If so, it will abort the command and inform the user.
*   **Storage**: The daily accumulated cost will be stored in a simple file (e.g., `.atlas-code-costs.json`) in the user's home directory.

## 3. Usage Tracking and Analytics

To enable continuous improvement, the `CostTracker` will also log usage data.

*   **Data Points**: For each command, the following will be logged:
    *   Timestamp
    *   Model used
    *   Tokens used (input and output)
    *   Estimated cost
    *   Command run
*   **Storage**: This data will be stored in a local SQLite database for easy analysis.
*   **Analysis**: A separate script will be provided to analyze this data, allowing users to understand their usage patterns and identify opportunities for further cost savings.

## 4. Performance Optimization Targets

*   **Reduce Token Usage**: The `ModelRouter` will be designed to minimize token usage by intelligently selecting context files and truncating long prompts.
*   **Caching**: Implement a caching mechanism to avoid re-running the model on identical prompts.
*   **User Education**: The tool will provide feedback to the user on how to write more effective (and cheaper) prompts.
