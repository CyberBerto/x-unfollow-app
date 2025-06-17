#!/bin/bash

# Claude Token Tracker Setup Script
echo "Setting up Claude Token Tracker..."

# Create virtual environment
python3 -m venv venv

# Activate virtual environment (different for different shells)
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Install dependencies
pip install anthropic

echo "Setup complete!"
echo ""
echo "To use:"
echo "1. Set your API key: export ANTHROPIC_API_KEY='your-key-here'"
echo "2. Run: python claude_tracker.py"
echo ""
echo "Or activate the environment manually:"
echo "source venv/bin/activate  # Mac/Linux"
echo "venv\\Scripts\\activate     # Windows"