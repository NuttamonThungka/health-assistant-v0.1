#!/bin/bash

# Agnos Health Assistant Launcher
# Simple script to run the Streamlit application

echo "╔═══════════════════════════════════════════════╗"
echo "║     🏥 Agnos Health Assistant v0.1            ║"
echo "╚═══════════════════════════════════════════════╝"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "⚠️  No virtual environment found!"
    echo "   Please run setup first: ./setup.sh"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "   Creating from template..."
    cp .env.example .env
    echo "   Please edit .env and add your OpenAI API key"
    echo "   Run: nano .env"
    exit 1
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Verify dependencies
python -c "import streamlit" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Installing missing dependencies..."
    pip install -r requirements.txt
fi

# Run the application normally
echo ""
echo "🚀 Starting Agnos Health Assistant..."
echo "   Opening browser at http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the server"
echo "----------------------------------------"

# Run streamlit normally (venv is already activated)
streamlit run streamlit_app/Agnos_Health_Chatbot.py