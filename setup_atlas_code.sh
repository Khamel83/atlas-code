#!/bin/bash

# setup_atlas_code.sh: Automated setup script for Atlas Code on Raspberry Pi
# This script will:
# 1. Check for Python 3.9+ and pip
# 2. Create and activate a Python virtual environment
# 3. Install Atlas Code in editable mode
# 4. Install all development dependencies
# 5. Guide the user to set up their OpenRouter API Key
# 6. Provide instructions for the first run in YOLO mode

# Exit immediately if a command exits with a non-zero status.
set -e

echo "🚀 Starting Atlas Code setup..."

# --- 1. Check for Python 3.9+ and pip ---
echo "\n🔍 Checking for Python 3.9+ and pip..."
PYTHON_MIN_VERSION="3.9"

# Check for python3 and get its version
if command -v python3 &> /dev/null
then
    PYTHON_VERSION=$(python3 -c "import sys; print(f\"{\n.sys.version_info.major}.{\n.sys.version_info.minor}\")")
    if printf '%s\n' "$PYTHON_VERSION" "$PYTHON_MIN_VERSION" | sort -V -C
    then
        echo "✅ Python $PYTHON_VERSION found (>= $PYTHON_MIN_VERSION)"
    else
        echo "❌ Python $PYTHON_VERSION found, but requires >= $PYTHON_MIN_VERSION. Please update Python."
        exit 1
    fi
else
    echo "❌ python3 not found. Please install Python 3.9 or newer."
    exit 1
fi

# Check for pip3
if command -v pip3 &> /dev/null
then
    echo "✅ pip3 found."
else
    echo "❌ pip3 not found. Installing pip3..."
    sudo apt update
    sudo apt install python3-pip -y
    echo "✅ pip3 installed."
fi

# --- 2. Create and activate a Python virtual environment ---
echo "\nCreating and activating virtual environment..."
VENV_DIR="./.venv"
if [ -d "$VENV_DIR" ]; then
    echo "Virtual environment already exists. Reusing it."
else
    python3 -m venv "$VENV_DIR"
    echo "✅ Virtual environment created at $VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
echo "✅ Virtual environment activated."

# --- 3. Install Atlas Code in editable mode ---
echo "\nInstalling Atlas Code in editable mode..."
pip install -e .
echo "✅ Atlas Code installed in editable mode."

# --- 4. Install all development dependencies ---
echo "\nInstalling development dependencies..."
pip install -r requirements.txt
pip install -r requirements/requirements-dev.txt

# Install pre-commit hooks
if command -v pre-commit &> /dev/null
then
    echo "✅ pre-commit found. Installing git hooks..."
    pre-commit install
    echo "✅ Git pre-commit hooks installed."
else
    echo "⚠️ pre-commit not found. Skipping git hook installation."
    echo "   You can install it later: pip install pre-commit && pre-commit install"
fi

echo "✅ All dependencies installed."

# --- 5. Guide the user to set up their OpenRouter API Key ---
echo "\n--- OpenRouter API Key Setup ---"
echo "Atlas Code uses OpenRouter to access various LLMs. You'll need an API key."
echo "1. Go to https://openrouter.ai/ and sign up or log in."
echo "2. Navigate to your API keys section (usually under your profile or settings)."
echo "3. Generate a new API key and copy it. Keep this key secure!"
echo "\nNow, please enter your OpenRouter API Key:"
read -s OPENROUTER_API_KEY_INPUT

if [ -z "$OPENROUTER_API_KEY_INPUT" ]; then
    echo "⚠️ No API key entered. You will need to set it manually later."
    echo "   To set it for the current session: export OPENROUTER_API_KEY=\"YOUR_KEY\""
    echo "   To set it permanently: Add 'export OPENROUTER_API_KEY=\"YOUR_KEY\"' to your ~/.bashrc or ~/.zshrc"
else
    # Add to .env file in the project root for convenience (gitignored)
    echo "OPENROUTER_API_KEY=\"$OPENROUTER_API_KEY_INPUT\"" > .env
    echo "✅ API key saved to .env file (this file is gitignored)."
    echo "   It will be loaded automatically when you run Atlas Code from this directory."
fi

# --- 6. Provide instructions for the first run in YOLO mode ---
echo "\n--- Setup Complete! ---"
echo "Atlas Code is now set up and ready to use."
echo "\nTo start Atlas Code in YOLO mode (recommended for initial dogfooding):"
echo "1. Ensure your virtual environment is active: source $VENV_DIR/bin/activate"
echo "2. Run: atlas-code --yolo"
echo "\nEnjoy vibing with Atlas Code! 🚀"
