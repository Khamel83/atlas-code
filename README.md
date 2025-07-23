# Ralex: Your Terminal-Native AI Coding Assistant

**An intelligent, cost-effective, and privacy-focused agent that lives in your terminal.**

Ralex is a standalone coding assistant that runs entirely in your terminal. It uses a sophisticated semantic routing system to understand your requests and dispatch them to the most appropriate large language model via OpenRouter. The agent's logic is designed to be modular and extensible, inspired by the AgentOS framework.

## Why Use Ralex?

- **🧠 Cost-Effective Intelligence:** Ralex dynamically routes your requests to the best-suited and most affordable language model. Get the power of top-tier models like Claude 3.5 Sonnet for complex tasks, while using smaller, faster models for simple queries, saving you significant API costs.
- **💻 Unparalleled Control & Privacy:** Your code stays on your machine. Ralex is a terminal-native tool, not a cloud service. It interacts directly with your local files, and only the necessary code snippets are sent to the LLM you've configured.
- **🔌 Ultimate Flexibility:** Powered by OpenRouter, Ralex is model-agnostic. You are never locked into a single provider. Seamlessly switch between models from OpenAI, Anthropic, Google, or open-source alternatives to fit your budget and needs.

## Core Concepts

- **The Semantic Router:** At its heart, Ralex analyzes your natural language instructions to understand your *intent*. It then uses this understanding to choose the most effective and efficient way to accomplish the task.
- **The Dynamic Dispatcher:** Based on the router's decision, the dispatcher selects the best language model for the job from a tiered list of options, balancing performance with cost.
- **The Agentic Engine:** This is the workhorse. The engine manages the file context, orchestrates the calls to the LLM, and applies the approved changes directly to your local files.

## Getting Started

Here is how you can get the Ralex MVP up and running in a few simple steps.

### 1. Clone the Repository

First, clone the project to your local machine:

```bash
git clone https://github.com/Khamel83/ralex.git
cd ralex
```

### 2. Set Your API Key

Ralex uses the OpenRouter service to connect to various language models. You will need an OpenRouter API key.

1.  Go to [https://openrouter.ai/](https://openrouter.ai/) to get your free API key.
2.  Set it as an environment variable in your terminal:

```bash
export OPENROUTER_API_KEY="YOUR_KEY_HERE"
```

### 3. Install Dependencies

The project has a few Python dependencies. Install them using pip:

```bash
pip install -r requirements.txt
```

### 4. Run the Agent

Now you are ready to launch the agent:

```bash
python -m ralex_core.launcher
```

### 5. Example Workflow

Here is a quick example of how to use the agent to refactor a simple Python file.

1.  **Create a file** named `my_script.py` with the following content:

    ```python
    def hello():
        print("hello world")
    ```

2.  **Start the agent** (if you haven't already):

    ```bash
    python -m ralex_core.launcher
    ```

3.  **Add the file** to the agent's context:

    ```
    > /add my_script.py
    ```

4.  **Make a request** to the agent:

    ```
    > Add a docstring to the function in my_script.py
    ```

5.  The agent will stream a response and propose a change. **Confirm the change** by typing `y`.

That's it! The agent will have modified your file.

## Project Roadmap

For a detailed overview of the project's future direction, please see the [MVP Development Plan](MVP_PLAN.md).
