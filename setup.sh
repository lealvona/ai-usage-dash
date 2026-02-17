#!/bin/bash
# Setup script for AI Usage Dashboard

echo "🤖 AI Usage Dashboard - Setup Script"
echo "===================================="

# Check Python version
echo "Checking Python version..."
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "✓ Python $python_version detected"

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo ""
echo "Creating directories..."
mkdir -p storage templates

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your API keys before running the application."
else
    echo ""
    echo "✓ .env file already exists"
fi

echo ""
echo "===================================="
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Run: python app.py"
echo "3. Open: http://localhost:5000"
echo ""
echo "Or run the demo: python demo/demo_usage.py"
