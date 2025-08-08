#!/bin/bash

# Setup script for Agnos Health Assistant
# This script sets up the virtual environment and installs all dependencies

echo "╔═══════════════════════════════════════════════╗"
echo "║     🏥 Agnos Health Assistant Setup            ║"
echo "╚═══════════════════════════════════════════════╝"
echo ""

# Check Python version
echo "🔍 Checking Python version..."
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD=python3.11
elif command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    if [ "$PYTHON_VERSION" = "3.11" ]; then
        PYTHON_CMD=python3
    else
        echo "⚠️  Python 3.11 is required. Current version: $(python3 --version)"
        echo "   Please install Python 3.11 first."
        exit 1
    fi
else
    echo "❌ Python 3 not found. Please install Python 3.11."
    exit 1
fi

echo "✅ Using $($PYTHON_CMD --version)"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    $PYTHON_CMD -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "📦 Upgrading pip..."
pip install --upgrade pip --quiet

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo ""
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your OpenAI API key"
    echo "   Run: nano .env"
fi

# Create necessary directories
echo ""
echo "📁 Creating necessary directories..."
mkdir -p data/vector_store
mkdir -p data/metadata
mkdir -p logs

echo ""
echo "╔═══════════════════════════════════════════════╗"
echo "║           ✅ Setup Complete!                   ║"
echo "╚═══════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "1. Add your OpenAI API key to .env file:"
echo "   nano .env"
echo ""
echo "2. Run the application:"
echo "   source venv/bin/activate"
echo "   streamlit run streamlit_app/Agnos_Health_Chatbot.py"
echo ""
echo "Or simply use:"
echo "   ./run.sh"
echo ""