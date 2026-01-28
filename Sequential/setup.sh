#!/bin/bash

# ============================================
# AI Research Assistant - Quick Setup Script
# ============================================
# This script automates the setup process for the AI Research Assistant

echo "============================================"
echo "🚀 AI Research Assistant - Quick Setup"
echo "============================================"
echo ""

# Check Python installation
echo "📋 Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    echo "❌ Python not found! Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | grep -oP '\d+\.\d+')
echo "✅ Found Python $PYTHON_VERSION"
echo ""

# Create virtual environment
echo "📦 Creating virtual environment..."
$PYTHON_CMD -m venv venv
echo "✅ Virtual environment created"
echo ""

# Activate virtual environment
echo "🔧 Activating virtual environment..."
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi
echo "✅ Virtual environment activated"
echo ""

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip --quiet
echo "✅ pip upgraded"
echo ""

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# Check for .env file
echo "🔍 Checking for .env file..."
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOL
# Google API Key - Get yours at: https://aistudio.google.com/app/apikey
GOOGLE_API_KEY=your_google_api_key_here

# Optional: Google Custom Search (DuckDuckGo is used by default)
# GOOGLE_CSE_ID=your_custom_search_engine_id
# GOOGLE_CSE_API_KEY=your_custom_search_api_key
EOL
    echo "✅ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file and add your Google API Key!"
    echo "   Get your key from: https://aistudio.google.com/app/apikey"
else
    echo "✅ .env file already exists"
fi
echo ""

# Setup complete
echo "============================================"
echo "✅ Setup Complete!"
echo "============================================"
echo ""
echo "📝 Next Steps:"
echo "   1. Edit .env file and add your GOOGLE_API_KEY"
echo "   2. Run: python main.py"
echo "   3. Open: http://localhost:8000"
echo ""
echo "💡 Need help? Check README.md for detailed instructions"
echo ""
