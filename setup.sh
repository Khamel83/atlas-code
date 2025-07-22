#!/bin/bash

echo "Setting up Atlas Code on Raspberry Pi..."

# Check if virtual environment exists
if [ ! -d "atlas-env" ]; then
    echo "Creating virtual environment..."
    python3 -m venv atlas-env
fi

echo "Activating virtual environment..."
source atlas-env/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Setup complete!"
echo ""
echo "To use Atlas Code:"
echo "1. Run: source atlas-env/bin/activate"
echo "2. Set your API key: export OPENAI_API_KEY='your-key-here'"
echo "3. Run: python -m aider"
echo ""
echo "Or just run: ./run.sh"