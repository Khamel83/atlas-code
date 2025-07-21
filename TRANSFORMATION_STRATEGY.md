
# Atlas Code: Transformation Strategy

This document outlines the strategic plan for transforming the Aider codebase into Atlas Code, a cost-optimized, "one-shot" command-line tool for code generation.

## 1. Aider Architecture Map

This is an analysis of the key Aider components and their roles in the existing architecture.

*   **`aider/main.py`**: **CLI Entry Point & Main Loop.** This file parses command-line arguments and orchestrates the main user interaction loop. It will be modified to support a "one-shot" execution mode, allowing Atlas Code to be used in automated workflows.
*   **`aider/coders/base_coder.py`**: **Core Model Interaction.** This is the base class for all "coders" that interact with the LLM. It's the ideal location to implement cost tracking and budget enforcement, as all model requests pass through this module.
*   **`aider/models.py`**: **Model Selection.** This module is responsible for configuring and selecting the language model. It will be the central point for implementing the 4-tier model routing system.
*   **`aider/io.py`**: **User Input/Output.** This file handles all console input and output. It will be simplified to reduce verbosity in the "one-shot" mode, while preserving the necessary user interaction for the interactive mode.
*   **Git Integration**: Aider's git integration is a core strength and will be **preserved as-is**. All modifications will be designed to work seamlessly with the existing git workflow.

## 2. File-by-File Modification Plan

This section details the specific changes required in each file.

*   **`aider/main.py`**:
    *   Add a `--one-shot` command-line argument to enable single-command execution.
    *   Modify the main loop to exit after the first command when in "one-shot" mode.
    *   Add a `--silent` flag to suppress non-essential output.

*   **`aider/models.py`**:
    *   Implement a `ModelRouter` class to handle the 4-tier model selection logic.
    *   The router will select a model based on prompt analysis and/or user-specified tier.
    *   The tiers will be (for example): `cheap`, `regular`, `power`, `smart`.

*   **`aider/coders/base_coder.py`**:
    *   Add a `CostTracker` class to monitor token usage for each model call.
    *   Integrate the `CostTracker` into the `run` method to record costs.
    *   Implement a daily budget enforcement mechanism to prevent cost overruns.

*   **`aider/io.py`**:
    *   Modify printing functions to respect the `--silent` flag.

## 3. Transformation Task Queue

This is a list of ready-to-execute tasks for implementation.

```python
implementation_tasks = [
    {
        "task": "Add `--one-shot` and `--silent` arguments to aider/main.py",
        "complexity": 3,
        "estimated_cost": "$0.05",
        "files": ["aider/main.py"],
        "validation": "Verify that the tool exits after one command with `--one-shot`."
    },
    {
        "task": "Implement a 4-tier model router in aider/models.py",
        "complexity": 6,
        "estimated_cost": "$0.15",
        "files": ["aider/models.py"],
        "validation": "Test tier selection with different prompts and user flags."
    },
    {
        "task": "Integrate cost tracking into aider/coders/base_coder.py",
        "complexity": 4,
        "estimated_cost": "$0.08",
        "files": ["aider/coders/base_coder.py", "aider/main.py"],
        "validation": "Verify that model usage is tracked and costs are recorded."
    },
    {
        "task": "Implement daily budget enforcement in the CostTracker",
        "complexity": 5,
        "estimated_cost": "$0.10",
        "files": ["aider/coders/base_coder.py"],
        "validation": "Verify that the tool exits when the daily budget is exceeded."
    },
    {
        "task": "Add a file-based cost storage system",
        "complexity": 3,
        "estimated_cost": "$0.05",
        "files": ["aider/coders/base_coder.py"],
        "validation": "Check that costs are saved to and loaded from a file."
    }
]
```

## 4. Risk Assessment and Mitigation

*   **Risk**: Breaking existing Aider functionality.
    *   **Mitigation**: Maintain dual-mode support (interactive and one-shot). All new functionality will be behind feature flags initially.
*   **Risk**: Inaccurate cost tracking.
    *   **Mitigation**: Thoroughly test the `CostTracker` with different models and usage scenarios.
*   **Risk**: Complex merge conflicts with upstream Aider.
    *   **Mitigation**: Keep changes modular and well-documented to facilitate future merges.

