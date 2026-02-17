#!/bin/bash
# Build script for Linux executable

set -e

echo "========================================"
echo "Building AI Usage Dashboard for Linux"
echo "========================================"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist

# Install dependencies if needed
echo "Installing dependencies..."
pip install -r requirements.txt pyinstaller==6.3.0

# Build with PyInstaller
echo "Building executable..."
pyinstaller build.spec --clean --noconfirm

# Create release package
echo "Creating release package..."
mkdir -p release/linux
cd dist

# Create tarball
tar -czvf "../release/linux/ai_usage_dash_linux.tar.gz" ai_usage_dash

# Create install script
cat > "../release/linux/install.sh" << 'EOF'
#!/bin/bash
# Installation script for AI Usage Dashboard

echo "Installing AI Usage Dashboard..."

# Create application directory
mkdir -p ~/.local/bin
mkdir -p ~/.local/share/applications
mkdir -p ~/.ai_usage_dash/logs

# Copy executable
cp ai_usage_dash ~/.local/bin/

# Make executable
chmod +x ~/.local/bin/ai_usage_dash

# Create desktop entry
cat > ~/.local/share/applications/ai-usage-dash.desktop << 'DESKTOP'
[Desktop Entry]
Name=AI Usage Dashboard
Comment=Track and visualize AI usage across providers
Exec=ai_usage_dash
Icon=utilities-system-monitor
Terminal=false
Type=Application
Categories=Utility;Development;
DESKTOP

echo "Installation complete!"
echo "Run 'ai_usage_dash' to start the application"
EOF

chmod +x "../release/linux/install.sh"

cd "$SCRIPT_DIR"

echo "========================================"
echo "Build complete!"
echo "Output: release/linux/"
echo "========================================"
