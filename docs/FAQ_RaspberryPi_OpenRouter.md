# Atlas Code FAQ: Raspberry Pi & OpenRouter

## Table of Contents
- [Setup Questions](#setup-questions)
- [API Key & Authentication](#api-key--authentication)
- [Performance & Memory](#performance--memory)
- [Model Selection](#model-selection)
- [Troubleshooting](#troubleshooting)
- [Cost Management](#cost-management)

## Setup Questions

### Q: What Raspberry Pi models are supported?
**A:** Atlas Code works on:
- ✅ **Raspberry Pi 4** (4GB/8GB) - Recommended
- ✅ **Raspberry Pi 5** - Best performance
- ⚠️ **Raspberry Pi 4** (2GB) - Works with lightweight models
- ❌ **Raspberry Pi Zero/3B** - Not recommended (insufficient memory)

### Q: Can I run this on Raspberry Pi OS Lite?
**A:** Yes! Install the missing packages:
```bash
sudo apt update
sudo apt install python3-full python3-venv git nano -y
```

### Q: Do I need to compile anything?
**A:** No! Everything installs via pip using pre-compiled wheels from piwheels.org, optimized for ARM processors.

### Q: How much storage space do I need?
**A:** Approximately:
- **Base installation**: ~1.5GB
- **Virtual environment**: ~500MB
- **Model cache**: ~100MB
- **Total recommended**: 3GB+ free space

## API Key & Authentication

### Q: Is OpenRouter free?
**A:** OpenRouter offers:
- **Free tier**: $1 in credits when you sign up
- **Pay-as-you-go**: Starting at $0.002/1K tokens
- **No monthly fees**: Only pay for what you use

### Q: How do I get an OpenRouter API key?
**A:** 
1. Go to [openrouter.ai](https://openrouter.ai)
2. Sign up with email or GitHub
3. Navigate to "Keys" in your account
4. Click "Create Key"
5. Copy the key (starts with `sk-or-v1-`)

### Q: Where do I put my API key?
**A:** In the `.env` file:
```bash
nano .env
# Add this line:
OPENAI_API_KEY=sk-or-v1-your-actual-key-here
```

### Q: Can I use multiple API keys?
**A:** Yes! You can set different providers:
```bash
# In .env file:
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-claude-key  
OPENROUTER_API_KEY=sk-or-v1-your-openrouter-key
```

### Q: My API key isn't working
**A:** Check these steps:
1. **Verify the key format**: Should start with `sk-or-v1-`
2. **Check .env file**: `cat .env` should show your key
3. **Restart Atlas Code**: `./run.sh --version`
4. **Check OpenRouter balance**: Visit your OpenRouter dashboard

## Performance & Memory

### Q: Atlas Code is slow on my Pi 4 2GB
**A:** Try these optimizations:
```bash
# Use Silver Tier models for faster response
./run.sh --model openrouter/anthropic/claude-3-haiku

# Or try the free DeepSeek model
./run.sh --model openrouter/deepseek/deepseek-r1:free

# Reduce memory usage
./run.sh --map-tokens 1024 --max-chat-history-tokens 4000

# Work with specific files only
./run.sh myfile.py
```

### Q: How can I monitor memory usage?
**A:** Use these commands:
```bash
# Check memory before starting
free -h

# Monitor during use
htop  # Install with: sudo apt install htop
```

### Q: Should I enable swap on my Pi?
**A:** For 2GB models, yes:
```bash
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile  # Set CONF_SWAPSIZE=1024
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

### Q: Can I run Atlas Code remotely?
**A:** Yes! SSH with X11 forwarding:
```bash
ssh -X pi@your-pi-ip
# Then run Atlas Code normally
```

## Model Selection

### Q: Which model should I use on Raspberry Pi?
**A:** Atlas Code uses a 4-tier system with OpenRouter models:

**🥈 Silver Tier (Budget):**
- `openrouter/deepseek/deepseek-r1:free` - Free but rate limited
- `openrouter/anthropic/claude-3-haiku` - Fast and cheap ($0.25/1M tokens)
- `openrouter/openai/gpt-4o-mini` - Good for simple tasks

**🥇 Gold Tier (Balanced):**
- `openrouter/deepseek/deepseek-chat` - Excellent value ($0.14/1M tokens)
- `openrouter/meta-llama/llama-3.1-70b-instruct` - Strong performance

**💎 Platinum Tier (Premium):**
- `openrouter/anthropic/claude-3.5-sonnet` - Best coding performance ($3/1M tokens)
- `openrouter/openai/gpt-4o` - Strong overall performance ($2.50/1M tokens)

**💠 Diamond Tier (Flagship):**
- `openrouter/anthropic/claude-3.7-sonnet` - Latest Claude ($15/1M tokens)
- `openrouter/deepseek/deepseek-r1` - Advanced reasoning ($2.19/1M tokens)

### Q: How do I list all available models?
**A:** 
```bash
./run.sh --list-models          # All models
./run.sh --list-models claude   # Only Claude models
./run.sh --list-models gpt      # Only GPT models
```

### Q: How do I use the tier system?
**A:** 
```bash
# Silver Tier - Start here for learning
./run.sh --model openrouter/anthropic/claude-3-haiku

# Gold Tier - Best value for regular work  
./run.sh --model openrouter/deepseek/deepseek-chat

# Platinum Tier - Premium coding performance
./run.sh --model openrouter/anthropic/claude-3.5-sonnet

# Diamond Tier - Flagship models for complex tasks
./run.sh --model openrouter/anthropic/claude-3.7-sonnet

# Set default tier in .env:
echo "AIDER_MODEL=openrouter/deepseek/deepseek-chat" >> .env
```

### Q: Can I change models mid-conversation?
**A:** Not directly, but you can:
1. Save your work: `/exit`
2. Restart with new model: `./run.sh --model new-model`
3. Continue with same files

### Q: What's the difference between OpenRouter and direct API access?
**A:** **OpenRouter advantages:**
- Access to multiple providers through one API key
- Often cheaper pricing
- No need for multiple accounts
- Rate limiting protection

## Troubleshooting

### Q: I get "command not found" errors
**A:** Make scripts executable:
```bash
chmod +x setup.sh setup_atlas_code.sh run.sh
```

### Q: Python import errors
**A:** Ensure virtual environment is activated:
```bash
source atlas-env/bin/activate
python -c "import aider; print('Import successful')"
```

### Q: "No module named 'aider'" error
**A:** Reinstall dependencies:
```bash
./setup.sh
# Or manually:
source atlas-env/bin/activate
pip install -r requirements.txt
```

### Q: Atlas Code hangs or freezes
**A:** Common causes:
1. **Memory exhaustion**: Use lighter model or add swap
2. **Network issues**: Check internet connection
3. **API rate limiting**: Wait a few minutes and retry

### Q: Git errors in Atlas Code
**A:** Ensure git is configured:
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### Q: "TypeError: argument of type 'NoneType'" error
**A:** This is a known issue with `--show-repo-map`. Use these alternatives:
```bash
./run.sh --version          # Test basic functionality
./run.sh --list-models      # Test API connectivity  
./run.sh myfile.py          # Start with specific files
```

## Cost Management

### Q: How much does it cost to use Atlas Code?
**A:** **Typical costs with OpenRouter:**
- **Small script editing**: $0.01-0.05 per session
- **Medium project work**: $0.10-0.50 per session  
- **Large refactoring**: $1-5 per session

**Cost factors:**
- Model choice (Haiku < Sonnet < GPT-4)
- Project size (more files = higher costs)
- Conversation length

### Q: How can I monitor costs?
**A:** 
1. **OpenRouter dashboard**: Shows real-time usage
2. **Atlas Code budget features**: Set daily limits
3. **Model comparison**: Use `--list-models` to see pricing

### Q: How do I set spending limits?
**A:** Use Atlas Code's budget system:
```bash
# Set daily budget to $2
./run.sh --budget 2.00

# Get notifications at 50% and 80%
./run.sh --budget 2.00 --notify-thresholds 0.5 0.8

# Set budget reset time (UTC)
./run.sh --budget 2.00 --cutoff-time 00:00
```

### Q: What happens if I hit my budget limit?
**A:** Atlas Code will:
1. Show a warning when approaching limits
2. Prompt for approval to continue
3. Optionally switch to cheaper models
4. Stop operations if budget is exceeded

### Q: Can I use free/local models?
**A:** Currently Atlas Code is optimized for cloud APIs, but you can:
1. Use the cheapest OpenRouter models
2. Set strict budgets to control costs
3. Consider running local models with Ollama (advanced setup)

## Advanced Usage

### Q: Can I customize the setup scripts?
**A:** Yes! The scripts are bash and can be modified:
- `setup.sh` - Simple setup
- `setup_atlas_code.sh` - Advanced setup with dev tools
- `run.sh` - Runtime wrapper

### Q: How do I update Atlas Code?
**A:** 
```bash
git pull origin main
./setup.sh  # Reinstall dependencies if needed
```

### Q: Can I contribute to Atlas Code?
**A:** Absolutely! This is based on the open-source Aider project. Check:
- [Main Aider repository](https://github.com/Aider-AI/aider)
- [This Atlas Code fork](https://github.com/Khamel83/atlas-code)

### Q: How do I report bugs?
**A:** 
1. **For setup issues**: Open issue on the Atlas Code repository
2. **For core functionality**: Report to the main Aider project
3. **Include**: OS version, Python version, error messages, steps to reproduce

---

## Still Need Help?

- 📖 [Read the documentation](https://aider.chat/docs/)
- 💬 [Join the Discord](https://discord.gg/Tv2uQnR)
- 🐛 [Report issues](https://github.com/Khamel83/atlas-code/issues)
- 📧 [Contact support](mailto:support@example.com)

---
*Last updated: January 2025*
