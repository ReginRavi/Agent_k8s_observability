#!/bin/bash

# K8s Observability Agent - Quick Startup Script
# This script helps you get started quickly

echo "=========================================="
echo "K8s Observability Agent - Quick Start"
echo "=========================================="
echo ""

# Step 1: Check prerequisites
echo "📋 Step 1: Checking prerequisites..."
echo ""

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.9+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✅ Python version: $PYTHON_VERSION"

# Step 2: Setup virtual environment
echo ""
echo "🔧 Step 2: Setting up virtual environment..."
echo ""

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate
echo "✅ Virtual environment activated"

# Step 3: Install dependencies
echo ""
echo "📦 Step 3: Installing dependencies..."
echo ""

pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "✅ Dependencies installed"

# Step 4: Check configuration
echo ""
echo "⚙️  Step 4: Checking configuration..."
echo ""

if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and set your GEMINI_API_KEY"
    echo "   nano .env"
    echo ""
    read -p "Press Enter after you've set your API key..."
fi

# Verify API key is set
if grep -q "your-gemini-api-key-here" .env; then
    echo "❌ Please set your GEMINI_API_KEY in .env file"
    echo "   Current: GEMINI_API_KEY=your-gemini-api-key-here"
    echo ""
    echo "Get your API key from: https://makersuite.google.com/app/apikey"
    exit 1
fi

echo "✅ Configuration file exists"

# Step 5: Run comprehensive service validation
echo ""
echo "🔍 Step 5: Validating all services..."
echo ""

python3 scripts/validate_services.py

VALIDATION_STATUS=$?

if [ $VALIDATION_STATUS -eq 1 ]; then
    # Critical services are down
    echo ""
    echo "❌ Critical services are unavailable. Cannot start the agent."
    echo ""
    echo "Please fix the issues above or run:"
    echo "  python3 scripts/fix_connections.py  # For cluster services"
    echo ""
    exit 1
elif [ $VALIDATION_STATUS -eq 2 ]; then
    # Optional services are down but critical are ok
    echo ""
    echo "⚠️  Some services are unavailable but critical ones are healthy."
    echo ""
    read -p "Do you want to continue with limited functionality? (Y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        exit 1
    fi
fi

echo "✅ Service validation passed!"

# Step 6: Start the agent
echo ""
echo "=========================================="
echo "🚀 Ready to start the agent!"
echo "=========================================="
echo ""
echo "The agent will start on http://localhost:8000"
echo ""
echo "You can:"
echo "  - View API docs: http://localhost:8000/docs"
echo "  - Check health: http://localhost:8000/health"
echo "  - Ask questions: POST to http://localhost:8000/chat"
echo ""
echo "Press Ctrl+C to stop the agent"
echo ""
read -p "Start the agent now? (Y/n) " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    echo ""
    echo "Starting agent..."
    echo ""
    python3 -m app.main
else
    echo ""
    echo "To start manually, run:"
    echo "  source venv/bin/activate"
    echo "  python3 -m app.main"
fi
