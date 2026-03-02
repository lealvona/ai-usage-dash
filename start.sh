#!/usr/bin/env bash
set -e

echo "============================================"
echo "  AI Usage Dashboard"
echo "============================================"
echo

# Absolute project root
PROJECT_DIR="/c/Users/lvona/src/ai-usage-dash"

# Check for uv
if ! command -v uv &>/dev/null; then
    echo "ERROR: uv not found. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Parse arguments
MODE="gui"
EXTRA_ARGS=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --browser|-b) MODE="browser"; shift ;;
        --debug)      EXTRA_ARGS="$EXTRA_ARGS --debug"; shift ;;
        *)            shift ;;
    esac
done

# Start in chosen mode
if [ "$MODE" = "browser" ]; then
    echo "Starting in browser mode..."
    echo "Dashboard: http://127.0.0.1:5000"
    echo "Press Ctrl+C to stop."
    echo
    uv run --project "$PROJECT_DIR" ai-dash-browser $EXTRA_ARGS
else
    echo "Starting desktop app..."
    echo
    uv run --project "$PROJECT_DIR" ai-dash --daemon $EXTRA_ARGS || {
        echo
        echo "Desktop mode failed - falling back to browser mode..."
        echo
        uv run --project "$PROJECT_DIR" ai-dash-browser $EXTRA_ARGS
    }
fi
