# Atlas Code V2 🚀

**AI Pair Programming with Smart Model Routing**

Atlas Code V2 is a lightweight wrapper around [Aider](https://aider.chat) that adds intelligent model routing, budget awareness, and development standards integration.

## 🎯 Key Features

### Smart 4-Tier Model Routing
- **Silver**: Budget models for simple tasks (typos, basic scripts)
- **Gold**: Balanced models for regular development work  
- **Platinum**: Premium models for complex coding challenges
- **Diamond**: Flagship models for architecture and design

### OpenRouter Integration
- Unified access to multiple LLM providers through OpenRouter
- Automatic cost optimization within each tier
- Single API key for all models

### Agent OS Integration
- Development standards and coding guidelines
- Project-specific workflows and instructions
- Intelligent prompt enhancement with context
- **Source**: https://github.com/Khamel83/agent-os

### Simple Budget Management
- Daily spending limits and warnings
- Real-time cost estimation
- Usage tracking and reporting
- Budget-aware model recommendations

## 🚀 Quick Start

### Installation
```bash
# Clone Atlas Code V2
git clone https://github.com/Khamel83/atlas-code.git
cd atlas-code
git checkout atlas-code-v2

# Run setup
bash setup-v2.sh

# Add your OpenRouter API key to .env
echo "OPENAI_API_KEY=sk-or-v1-your-key-here" >> .env
```

### Basic Usage
```bash
# Simple task (auto-routes to appropriate tier)
./atlas-code "create a Python calculator"

# Force specific tier
./atlas-code --tier gold "implement user authentication"

# Include specific files
./atlas-code "add error handling" src/main.py src/utils.py

# Check available models
./atlas-code --models

# Initialize development standards
./atlas-code --init-agent-os
```

## 🏗️ Architecture

Atlas Code V2 uses a **wrapper architecture** that preserves vanilla Aider:

```
User Request → Model Router → OpenRouter → Aider → Code Changes
     ↓              ↓            ↓
Agent OS     Budget Check   Cost Tracking
```

### Benefits:
- ✅ Easy Aider upgrades (no deep modifications)
- ✅ Clean, maintainable codebase  
- ✅ Focused functionality (smart routing + budget awareness)
- ✅ Compatible with all Aider features

## 📊 Model Tiers

| Tier | Use Cases | Example Models | Cost Range |
|------|-----------|----------------|------------|
| **Silver** | Simple edits, typos, basic scripts | DeepSeek R1 Free, Claude Haiku | $0.00 - $0.25/1K |
| **Gold** | Regular development, debugging | DeepSeek Chat, Llama 3.1 70B | $0.14 - $0.59/1K |
| **Platinum** | Complex coding, refactoring | Claude 3.5 Sonnet, GPT-4o | $2.50 - $3.00/1K |
| **Diamond** | Architecture, system design | Claude 3.7 Sonnet, DeepSeek R1 | $2.19 - $15.00/1K |

## 🔧 Configuration

### Environment Variables
```bash
# Required: OpenRouter API key
OPENAI_API_KEY=sk-or-v1-your-key-here

# Optional: Default tier
ATLAS_DEFAULT_TIER=gold

# Optional: Daily budget limit
ATLAS_DAILY_BUDGET=5.00
```

### Agent OS Setup
```bash
# Initialize development standards
./atlas-code --init-agent-os

# Customize standards
edit agent_os/standards/python.md
edit agent_os/instructions/testing.md
```

## 💰 Budget Management

```bash
# Set daily limit
./atlas-code --set-budget 10.00

# Check budget status
./atlas-code --budget-status

# Skip budget check for a request
./atlas-code --no-budget-check "urgent fix needed"
```

## 🔄 Continuous Development

Atlas Code V2 includes workflow automation:

```bash
# Quick commit and push script
./quick-push.sh "feat: implement new feature"

# Automated development workflow
# (pushes every 30 minutes during development)
```

## 📖 Documentation

- [V1 vs V2 Comparison](./V1_VS_V2.md) - Architecture differences and feature comparison
- [Agent OS Integration](./AGENT_OS.md) - Development standards and workflow management
- [Original Aider Docs](https://aider.chat/docs/) - Full Aider capabilities

## 🎯 Use Cases

### Individual Developers
- Cost-conscious development with automatic model selection
- Consistent coding standards across projects
- Budget tracking for personal OpenRouter usage

### Small Teams
- Shared development standards via Agent OS
- Team budget management and cost tracking
- Consistent AI pair programming experience

### Learning & Experimentation
- Free tier models for learning (Silver tier)
- Gradual progression to more powerful models
- Budget controls to prevent unexpected costs

## 🔄 Migration from V1

Atlas Code V2 is a complete rewrite focused on simplicity. If you're using V1:

1. **Export configurations**: Model preferences, budget settings
2. **Install V2**: Clean wrapper architecture
3. **Set up Agent OS**: Migrate development standards  
4. **Configure OpenRouter**: Consolidate API access
5. **Test workflow**: Ensure core functionality works

See [V1_VS_V2.md](./V1_VS_V2.md) for detailed comparison.

## 🤝 Contributing

Atlas Code V2's simple architecture makes contributions easy:

1. Fork the repository
2. Create a feature branch
3. Make changes to ralex_core/ modules
4. Test with `./atlas-code --models`
5. Submit a pull request

## 📄 License

This project builds on [Aider](https://github.com/Aider-AI/aider) and follows the same open-source principles.

## 🙏 Acknowledgments

- **Aider Team**: For the excellent foundation
- **OpenRouter**: For unified LLM access
- **Agent OS**: For development standards framework

---

**Atlas Code V2**: Smart model routing + Simple budget awareness + Vanilla Aider = Powerful, maintainable AI pair programming