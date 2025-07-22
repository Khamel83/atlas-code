# Atlas Code Setup for Raspberry Pi

## What is Atlas Code?
Atlas Code is an AI-powered coding assistant that helps you write, modify, and debug code using AI models like GPT-4, Claude, etc.

## Quick Setup (3 Steps)

### 1. Clone and Setup
```bash
git clone https://github.com/Khamel83/atlas-code.git
cd atlas-code
sudo apt install python3-full python3-venv
./setup.sh
```

### 2. Get Your API Key
- Go to [OpenRouter.ai](https://openrouter.ai)
- Sign up and get your API key (starts with `sk-or-v1-...`)

### 3. Configure and Run
```bash
# Edit the .env file to add your API key:
nano .env

# Then run Atlas Code:
./run.sh
```

## That's It! 🎉

### Usage Examples:
```bash
# Start Atlas Code
./run.sh

# Use with a specific model
./run.sh --model openrouter/anthropic/claude-3.5-sonnet

# Get help
./run.sh --help
```

### Inside Atlas Code:
```
> Create a Python calculator
> Fix the bug in calculator.py
> Add error handling to my code
> Explain what this function does
```

## Troubleshooting

**Import Error?** Make sure you ran `./setup.sh` first.

**API Key Error?** Check that your key is correctly set in `.env` file.

**Permission Error?** Run `chmod +x setup.sh run.sh`

## Models You Can Use
- `openrouter/anthropic/claude-3.5-sonnet` (recommended)
- `openrouter/openai/gpt-4`
- `openrouter/meta-llama/llama-3.1-8b-instruct` (cheaper)

---
*Happy coding with AI on your Raspberry Pi!* 🤖🥧