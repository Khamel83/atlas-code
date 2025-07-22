#!/bin/bash

# Simple script to run Atlas Code
source atlas-env/bin/activate

# Load environment variables from .env file
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Check if API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "Please set OPENAI_API_KEY in .env file"
    echo "For OpenRouter, use your OpenRouter key as OPENAI_API_KEY"
    exit 1
fi

python -m aider "$@"