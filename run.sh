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
    echo "   Creating virtual environment with Python 3.11..."
    python3.11 -m venv venv
    echo "   Installing dependencies..."
    ./venv/bin/pip install --upgrade pip
    ./venv/bin/pip install -r requirements.txt
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "   Creating from template..."
    cp .env.example .env
    echo "   Please edit .env and add your OpenAI API key"
    exit 1
fi

# Check if dependencies are installed
./venv/bin/python -c "import streamlit" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Installing dependencies..."
    ./venv/bin/pip install -r requirements.txt
fi

# Run the application using venv Python directly
echo ""
echo "🚀 Starting Agnos Health Assistant..."
echo "   Opening browser at http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the server"
echo "----------------------------------------"

# Use venv's streamlit directly to avoid system Python issues
./venv/bin/streamlit run streamlit_app/Agnos_Health_Chatbot.py