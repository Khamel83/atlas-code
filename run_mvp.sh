#!/bin/bash

# This script automates the setup and execution of the Ralex MVP.

# Check for OPENROUTER_API_KEY
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "Error: The OPENROUTER_API_KEY environment variable is not set."
    echo "Please get a key from https://openrouter.ai/ and set the environment variable."
    exit 1
fi

# Install dependencies
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
else
    echo "Warning: requirements.txt not found. Skipping dependency installation."
fi

# Launch the agent
echo "Launching Ralex..."
python -m ralex_core.launcher
