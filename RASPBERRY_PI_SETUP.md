# Atlas Code Setup for Raspberry Pi

## What is Atlas Code?
Atlas Code is an AI-powered coding assistant that helps you write, modify, and debug code using AI models like GPT-4, Claude, etc. Based on the popular Aider project, it provides budget-aware pair programming in your terminal.

## System Requirements
- **OS**: Raspberry Pi OS (Debian 12 "Bookworm") or newer
- **Python**: 3.10+ (3.11.2+ recommended)
- **Memory**: 2GB RAM minimum, 4GB+ recommended
- **Storage**: 2GB free space for dependencies

## Quick Setup (3 Steps)

### 1. Clone and Setup
```bash
# Install prerequisites
sudo apt update
sudo apt install python3-full python3-venv git -y

# Clone the repository
git clone https://github.com/Khamel83/atlas-code.git
cd atlas-code

# Run the setup script
chmod +x setup.sh setup_atlas_code.sh
./setup.sh
```

### 2. Get Your OpenRouter API Key
- Go to [OpenRouter.ai](https://openrouter.ai)
- Sign up for a free account (gets you $1 in credits)
- Navigate to "Keys" in your account settings
- Create a new API key (starts with `sk-or-v1-...`)
- Copy the key securely

### 3. Configure and Run
```bash
# The setup creates a .env file automatically
# Edit it to add your API key:
nano .env

# Add this line (replace with your actual key):
# OPENAI_API_KEY=sk-or-v1-your-key-here

# Test the installation:
./run.sh --version

# Start Atlas Code:
./run.sh
```

## That's It! 🎉

### Usage Examples:
```bash
# Start Atlas Code with default model
./run.sh

# Use with a specific tier model
./run.sh --model openrouter/deepseek/deepseek-chat

# List available models
./run.sh --list-models claude

# Get help
./run.sh --help

# Start with files to edit
./run.sh myproject.py README.md
```

### Inside Atlas Code:
```
> Create a Python calculator
> Fix the bug in calculator.py  
> Add error handling to my code
> Explain what this function does
> /help - Show available commands
> /exit - Exit Atlas Code
```

## Advanced Setup (setup_atlas_code.sh)

For development work, use the advanced setup script:

```bash
./setup_atlas_code.sh
```

This script:
- Creates a `.venv` virtual environment
- Installs development dependencies
- Sets up pre-commit hooks
- Guides you through API key setup interactively

## Troubleshooting

### Common Issues

**Permission Error on Scripts?**
```bash
chmod +x setup.sh setup_atlas_code.sh run.sh
```

**Missing API Key Error?**
```bash
# Check if .env file exists and has your key
cat .env
# Should show: OPENAI_API_KEY=sk-or-v1-...
```

**Import or Module Errors?**
```bash
# Make sure you ran setup first
./setup.sh
# Check virtual environment
source atlas-env/bin/activate
python -c "import aider; print('OK')"
```

**Python Version Too Old?**
```bash
python3 --version  # Should be 3.10+
# If too old, upgrade your Raspberry Pi OS
```

**Memory Issues on Pi Zero/1GB models?**
- Use Silver Tier models: `openrouter/anthropic/claude-3-haiku` or `openrouter/deepseek/deepseek-r1:free`
- Limit file scope with `./run.sh specific_file.py`
- Close other applications to free memory

### Getting Help

**Check System Status:**
```bash
# Test all components
./run.sh --version
./run.sh --list-models gpt
```

**For support:**
- Check the [Aider documentation](https://aider.chat/docs/)
- Open issues on [GitHub](https://github.com/Khamel83/atlas-code/issues)

## Atlas Code 4-Tier Model System

Atlas Code uses a simple 4-tier system with OpenRouter models:

### 🥈 Silver Tier (Budget) - Perfect for Pi 2GB models:
- `openrouter/deepseek/deepseek-r1:free` - Free but rate limited
- `openrouter/anthropic/claude-3-haiku` - Fast and cheap ($0.25/1M tokens)
- `openrouter/openai/gpt-4o-mini` - Good for simple tasks

### 🥇 Gold Tier (Balanced) - Best value for most work:
- `openrouter/deepseek/deepseek-chat` - Excellent value ($0.14/1M tokens)
- `openrouter/meta-llama/llama-3.1-70b-instruct` - Strong performance

### 💎 Platinum Tier (Premium) - Serious coding work:
- `openrouter/anthropic/claude-3.5-sonnet` - Best coding performance ($3/1M tokens)
- `openrouter/openai/gpt-4o` - Strong overall performance ($2.50/1M tokens)

### 💠 Diamond Tier (Flagship) - Complex projects:
- `openrouter/anthropic/claude-3.7-sonnet` - Latest Claude ($15/1M tokens)
- `openrouter/deepseek/deepseek-r1` - Advanced reasoning ($2.19/1M tokens)

### Using the Tier System:
```bash
# Start with Silver Tier for learning
./run.sh --model openrouter/anthropic/claude-3-haiku

# Move to Gold Tier for regular work
./run.sh --model openrouter/deepseek/deepseek-chat

# Use Platinum Tier for important projects
./run.sh --model openrouter/anthropic/claude-3.5-sonnet

# Set default tier in .env:
echo "AIDER_MODEL=openrouter/deepseek/deepseek-chat" >> .env
```

## Performance Tips

1. **Start with specific files** rather than entire projects
2. **Use lighter models** for simple tasks
3. **Close other applications** to free memory
4. **Use `--map-tokens 1024`** to reduce memory usage
5. **Enable swap** if you have SD card space:
   ```bash
   sudo dphys-swapfile swapoff
   sudo nano /etc/dphys-swapfile  # Set CONF_SWAPSIZE=1024
   sudo dphys-swapfile setup
   sudo dphys-swapfile swapon
   ```

## What's Next?

Once Atlas Code is running:
1. Try the tutorial: `./run.sh --help`
2. Read the [usage documentation](https://aider.chat/docs/usage.html)
3. Explore different models and find your favorite
4. Join the [Discord community](https://discord.gg/Tv2uQnR)

---
*Happy AI-powered coding on your Raspberry Pi!* 🤖🥧