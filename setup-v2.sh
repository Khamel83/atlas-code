#!/bin/bash

# Atlas Code V2 Setup Script
# Simple setup for the wrapper architecture

echo "🚀 Setting up Atlas Code V2..."

# Check Python version
python_version=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
required_version="3.10"

if ! printf '%s\n' "$required_version" "$python_version" | sort -V -C; then
    echo "❌ Python $python_version found, but requires >= $required_version"
    echo "Please update Python or use a compatible environment"
    exit 1
fi

echo "✅ Python $python_version found"

# Create virtual environment if it doesn't exist
if [ ! -d "atlas-env-v2" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv atlas-env-v2
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source atlas-env-v2/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements-v2.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file..."
    cat > .env << 'EOF'
# Atlas Code V2 Configuration
# Add your OpenRouter API key here:
# OPENAI_API_KEY=sk-or-v1-your-key-here

# Optional: Set default model tier
# ATLAS_DEFAULT_TIER=gold

# Optional: Set daily budget limit
# ATLAS_DAILY_BUDGET=5.00
EOF
    echo "📝 Created .env file - please add your OpenRouter API key"
else
    echo "✅ .env file already exists"
fi

# Test installation
echo "🧪 Testing installation..."
if ./atlas-code --models > /dev/null 2>&1; then
    echo "✅ Atlas Code V2 installed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Add your OpenRouter API key to .env file:"
    echo "   nano .env"
    echo ""
    echo "2. Try Atlas Code:"
    echo "   ./atlas-code 'create a hello world script'"
    echo ""
    echo "3. Initialize Agent OS (optional):"
    echo "   ./atlas-code --init-agent-os"
    echo "   # Agent OS: https://github.com/Khamel83/agent-os"
    echo ""
    echo "4. Check available models:"
    echo "   ./atlas-code --models"
else
    echo "❌ Installation test failed"
    echo "Check that all dependencies installed correctly"
    exit 1
fi