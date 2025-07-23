# Ralex V2 transforms AI-assisted coding from a manual, anxiety-inducing process into an automated, cost-effective, and reliable development workflow.

**AI Pair Programming on Raspberry Pi with Smart Model Routing**

Simple guide to get Atlas Code V2 running on your Raspberry Pi in under 10 minutes.

## 🎯 What You Get
- **Smart AI Coding**: Automatically selects the right AI model for your task
- **Budget Control**: Never accidentally spend too much on AI
- **Raspberry Pi Optimized**: Lightweight wrapper that works great on ARM
- **Continuous Backup**: Auto-saves your work to GitHub every 5 minutes

## ⚡ 5-Minute Setup

### 1. Prerequisites
```bash
# Update your Pi
sudo apt update && sudo apt upgrade -y

# Install Python 3.10+ (if not already installed)
sudo apt install python3 python3-pip python3-venv git -y

# Check Python version (needs 3.10+)
python3 --version
```

### 2. Get Atlas Code
```bash
# Clone the repository
git clone https://github.com/Khamel83/atlas-code.git
cd atlas-code

# Switch to V2 branch
git checkout atlas-code-v2

# Run the setup script
bash setup-v2.sh
```

### 3. Add Your OpenRouter API Key
```bash
# Get a free API key from https://openrouter.ai
# Edit the .env file
nano .env

# Add this line (replace with your actual key):
OPENAI_API_KEY=sk-or-v1-your-key-here
```

### 4. Test It Works
```bash
# Check available models
./atlas-code --models

# Try a simple task
./atlas-code "create a hello world Python script"
```

## 🚀 Common Raspberry Pi Tasks

### Python Development
```bash
# Simple scripts (uses free models)
./atlas-code "create a temperature sensor reader"

# More complex projects (automatically uses better models)
./atlas-code "create a web dashboard for IoT sensors"
```

### Hardware Projects
```bash
# GPIO code
./atlas-code "create LED blink code for GPIO pin 18"

# Sensor integration
./atlas-code "read data from DHT22 temperature sensor"
```

### Home Automation
```bash
# Smart home scripts
./atlas-code "create a motion sensor security system"

# IoT integration
./atlas-code "send sensor data to MQTT broker"
```

## 💰 Budget Tips for Pi Users

```bash
# Set a daily budget (great for learning)
./atlas-code --set-budget 2.00

# Check spending
./atlas-code --budget-status

# Use free models for learning
./atlas-code --tier silver "explain how GPIO works"
```

## 🔄 Continuous Development

### Auto-Backup Your Work
```bash
# Start auto-push in background (saves work every 5 minutes)
nohup ./auto-push.sh &

# Or use quick manual pushes
./quick-push.sh "working on sensor project"
```

### Development Workflow
```bash
# 1. Start your project
./atlas-code --init-agent-os

# 2. Work on code with AI assistance
./atlas-code "add error handling to sensor reading"

# 3. Quick save to GitHub
./quick-push.sh "added sensor error handling"

# 4. Continue iterating...
```

## 🛠️ Raspberry Pi Optimizations

### Memory Management
```bash
# If running low on memory, use lighter models
export ATLAS_DEFAULT_TIER=silver

# Or force specific models
./atlas-code --tier silver "simple task"
```

### Performance
```bash
# Check if virtual environment is active
source atlas-env-v2/bin/activate

# For faster startup, keep environment activated
echo "source $(pwd)/atlas-env-v2/bin/activate" >> ~/.bashrc
```

## 📝 Example Project: IoT Weather Station

```bash
# Initialize development standards
./atlas-code --init-agent-os

# Create the main application
./atlas-code "create a weather station that reads DHT22 sensor and logs to CSV"

# Add web interface
./atlas-code "add a Flask web interface to display weather data"

# Add MQTT publishing
./atlas-code "publish weather data to MQTT broker every 60 seconds"

# Save progress
./quick-push.sh "completed weather station v1"
```

## 🔧 Troubleshooting

### Common Pi Issues

**"Python version too old"**
```bash
# Install Python 3.10+ on older Pi OS
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install python3.10 python3.10-venv -y
```

**"pip install fails"**
```bash
# Update pip
python3 -m pip install --upgrade pip

# Install with user flag
pip3 install --user aider-chat
```

**"Permission denied"**
```bash
# Make scripts executable
chmod +x atlas-code quick-push.sh auto-push.sh
```

**"Git authentication fails"**
```bash
# Set up GitHub authentication
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Use token authentication for HTTPS
# Get token from GitHub → Settings → Developer Settings → Personal Access Tokens
```

### Performance Issues
- Use `silver` tier for simple tasks to save resources
- Close other applications when doing complex AI tasks
- Consider using SSH from another computer for heavy development

## 🎯 Next Steps

1. **Learn the Tiers**: Try different `--tier` options to understand cost vs capability
2. **Set Up Agent OS**: Customize `agent_os/` for your projects
3. **Automate Workflows**: Use the auto-push script for continuous backup
4. **Join Community**: Share your Pi projects and get help

## 📚 Quick Reference

```bash
# Essential commands
./atlas-code "your task"              # Smart auto-routing
./atlas-code --tier silver "task"     # Force budget model
./atlas-code --models                 # Show available models
./atlas-code --budget-status          # Check spending
./quick-push.sh "message"             # Save work to GitHub
./auto-push.sh                        # Auto-save every 5 min

# Configuration files
.env                    # API keys and settings
agent_os/               # Development standards
atlas-env-v2/           # Python virtual environment
```

---

**Ready to Code!** 🚀 Your Raspberry Pi is now a powerful AI pair programming station with automatic model selection, budget control, and continuous backup to GitHub!