## Phase 7: Advanced CLI Interface

**Goal:** To build a more robust and user-friendly command-line interface, moving beyond the simple REPL.

### Epic 7.1: Command-Line Argument Parsing

The agent should accept commands and arguments directly from the command line.

- [ ] **Task 7.1.1:** Modify `atlas_core/launcher.py` to use `argparse` for command-line argument parsing.
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
- [ ] **Task 7.3.2:** Add a `--version` argument that displays the current version of Atlas Code V5.
- [ ] **Task 7.3.3:** Commit the changes with the message: `feat(cli): Add help and version arguments`.