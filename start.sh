#!/bin/bash

# Health Assistant Startup Script
# This script ensures proper virtual environment activation and runs the app

echo "╔═══════════════════════════════════════════════╗"
echo "║     🏥 Agnos Health Assistant Launcher         ║"
echo "╚═══════════════════════════════════════════════╝"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "   Please run setup first: ./setup.sh"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "   Please run: cp .env.example .env"
    echo "   Then edit .env and add your OpenAI API key"
    exit 1
fi

echo "🔄 Activating virtual environment..."

# Unset any Python aliases that might interfere
unset -f python
unalias python 2>/dev/null || true

# Activate virtual environment
source venv/bin/activate

# Verify activation
echo "✅ Virtual environment activated"
echo "   Python: $(which python)"
echo "   Streamlit: $(which streamlit)"

# Check if we have the right Python
if [[ "$(which python)" != *"/venv/bin/python" ]]; then
    echo "⚠️  Warning: Python path doesn't include venv"
    echo "   Using explicit venv Python..."
    PYTHON_CMD="./venv/bin/python"
    STREAMLIT_CMD="./venv/bin/streamlit"
else
    PYTHON_CMD="python"
    STREAMLIT_CMD="streamlit"
fi

# Test imports
echo ""
echo "🔍 Testing dependencies..."
$PYTHON_CMD -c "import streamlit, dotenv, openai, langchain; print('✅ All core dependencies available')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Missing dependencies. Installing..."
    ./venv/bin/pip install -r requirements.txt
fi

# Start the application
echo ""
echo "🚀 Starting Agnos Health Assistant..."
echo "   Application will open at: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the server"
echo "────────────────────────────────────────────────"

# Run with explicit venv path to avoid any conflicts
exec ./venv/bin/streamlit run streamlit_app/Agnos_Health_Chatbot.py