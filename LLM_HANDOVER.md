# LLM Session Handover

This document summarizes the progress and context of the current development session, intended for seamless handover to another LLM.

**Generated:** 2025-07-21 (Manual Update)
**Current Project Root:** `/home/RPI3/atlas-code/`
**Current Git Branch:** `temp/openrouter-client`

**Last 5 Commits (most recent first):**
*   `70810abc - feat: add LLM handover mechanism and session summary`
*   `7bdcaf3e - feat: add YOLO mode with dspy; --lazy as alias`
*   `61c6a3e7 - feat: Add --llm and --prompt flags to loop.py`
*   `b62743b3 - feat: Add openrouter_client.py for OpenRouter API interaction`
*   `f38200c5 - copy`

## LLM Operational Guidelines

### Context Management Rules

1.  **Auto-Summarize**  
    - Every 5 messages (or after each completed subtask), generate a 1–2-sentence summary of all prior content.  
    - Store that in the handover state and drop the detailed history.

2.  **Token Monitoring & Handover**  
    - Before each new prompt, estimate token usage.  
    - If ≥ 70% of the model’s window is used, automatically run:
      ```
      /handover "auto-summary"
      ```
      then clear chat and restore only the summary.

3.  **Tiered Model Routing**  
    - For planning/analysis steps, use top-tier model.  
    - For drafting/code edits, switch to medium-tier.  
    - For repetitive or low-complexity tasks, use `--yolo` with Flash-Lite.

4.  **“Plan → Execute” Workflow**  
    - Always begin with `/plan` to break work into 3–7 steps.  
    - Checkpoint the plan via `/handover "plan"` then clear history.  
    - Process each step in its own mini-session, restoring only the plan and that step’s context.

5.  **Prune & Restore**  
    - Never carry more than the last summary + current step context.  
    - Use `/restore` to load just those when starting a new session.

> _By baking these rules into your system prompt, Atlas Code will handle context compression, token monitoring, and model-tier switching automatically on every run._

### Model Tiering Definitions

To ensure consistent understanding and routing of LLM tasks, the following model tiering system is adopted across Atlas Code:

*   **Silver / Low Tier:** Suitable for repetitive, low-complexity tasks, or initial drafting where speed and cost-efficiency are paramount. Configured by `MODEL_TIER_EXECUTION` in `.env`.
*   **Gold / Mid Tier:** Ideal for general drafting, code edits, and tasks requiring a balance of capability and efficiency. Configured by `MODEL_TIER_DRAFTING` in `.env`.
*   **Platinum / Top Tier:** Reserved for planning, complex analysis, and critical code generation where high accuracy and reasoning are essential. Configured by `MODEL_TIER_PLANNING` in `.env`.
*   **Diamond / Flagship Tier:** The highest tier, for the most demanding tasks, advanced reasoning, and flagship model capabilities. (Currently not directly configurable via `.env`, but can be used by setting `MODEL_TIER_PLANNING` to a flagship model).

### Budget Management

Atlas Code incorporates a budget management system to help control LLM API costs. Key configurations are set in the `.env` file:

*   `DAILY_BUDGET`: Your daily spending limit in USD.
*   `NOTIFY_THRESHOLDS`: Comma-separated percentages (e.g., `0.8,0.95`) at which you will be notified of your spending.
*   `CUTOFF_TIME`: A 24-hour time (e.g., `17:00`) after which Atlas Code may automatically switch to a more cost-effective model tier if the budget is nearing its limit.

## Summary of Work Completed in this Session:

1.  **Systematic Handover Process Implementation:**
    *   **HandoverManager (`aider/handover_manager.py`):** Core infrastructure for capturing complete session state, including model configuration, file context, conversation history, and performance metrics.
    *   **HandoverDocumentGenerator (`aider/handover_generator.py`):** Automated generation of comprehensive handover documents with structured state information.
    *   **State Serialization:** JSON-based session state capture with validation checksums and integrity checking.

2.  **Previous OpenRouter Integration:**
    *   **OpenRouter API Client (`aider/openrouter_client.py`):** Module for OpenRouter API interactions with environment variable configuration.
    *   **`loop.py` Updates:** Added `--llm` and `--prompt` flags for direct LLM interaction and YOLO mode (`--yolo`/`--lazy`) with dspy instruction expansion.

3.  **Handover Infrastructure Features:**
    *   **Automated State Capture:** Complete session serialization including model configs, file context, git status, and conversation summaries.
    *   **Validation Framework:** State integrity checking with checksums and accessibility validation.
    *   **Document Generation:** Automated LLM_HANDOVER.md generation with structured context information.

4.  **Budget and Tiering System Implementation:**
    *   **`aider/cost_estimator.py`:** Module for estimating LLM API costs.
    *   **`aider/tier_router.py`:** Module for routing LLM calls to appropriate model tiers based on task and budget.
    *   **`aider/budget_manager.py`:** Module for tracking daily spending, managing notifications, and enforcing budget cutoffs.
    *   **Integration into `loop.py` and `aider/coders/base_coder.py`:** LLM calls now incorporate budget checks and tier routing.
    *   **Integration into `aider/production_validator.py`:** Projected cost checks added to production readiness validation.
    *   **CLI Flags:** Added `--budget`, `--notify-thresholds`, `--cutoff-time`, and `--no-auto-switch` for overriding budget settings.

**Pending Tasks / Next Steps:**

**High Priority:**
*   Unit tests for new modules (`cost_estimator`, `tier_router`, `budget_manager`).
*   Integration tests for various budget scenarios (under threshold, hit notify, exceed budget, auto-downgrade).
*   Model-tier switching tests.
*   Handover snapshot/restore tests.
*   E2E tests covering full deliverable run.

**Medium Priority:**
*   Integrate budget checks into `repo_map` operations (deferred to last).

**Instructions for the Next LLM:**

*   **Handover System Usage:** The new handover infrastructure allows automatic session state capture and restoration:
    ```python
    from aider.handover_manager import HandoverManager
    from aider.handover_generator import HandoverDocumentGenerator
    
    # Capture current state
    manager = HandoverManager()
    state = manager.capture_current_state(coder, reason="manual", trigger="user_request")
    
    # Generate handover document
    generator = HandoverDocumentGenerator(manager)
    document = generator.generate_full_handover_document(coder)
    ```

*   **State Files:** Check for `.aider.handover.state.json` for complete session state and `.aider.handover.history.jsonl` for handover history.
*   **Existing Features:** Continue building upon OpenRouter integration (`aider/openrouter_client.py`) and YOLO mode functionality in `loop.py`.
*   **Integration Tasks:** Focus on integrating handover hooks into the BaseCoderClass and command system for seamless state transitions.

**Handover System Status:**
*   ✅ Core HandoverManager infrastructure complete
*   ✅ Automated document generation complete  
*   ✅ Integration with existing coder classes complete
*   ✅ Production readiness validation framework complete
*   ✅ Command-level handover triggers implemented
*   ✅ SwitchCoder system enhanced for state transfer
*   ✅ JSON schema validation implemented
*   ✅ Budget and Tiering System implemented and integrated

**New Commands Available:**
*   `/handover [reason]` - Manually trigger handover process
*   `/restore [state_file]` - Restore session from handover state  
*   `/production [export format]` - Validate production readiness
*   `/budget-status` - Display current budget usage and status
*   `/budget-approve` - Approve a budget increase if prompted