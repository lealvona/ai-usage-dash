"""
Main GUI Application for AI Usage Dashboard
Uses PyWebView for cross-platform desktop GUI
"""

import os
import sys
import json
import logging
import threading
import time
import argparse
from typing import Dict, Any, Optional
from datetime import datetime
from flask import Flask, render_template, jsonify, request, send_from_directory

# Setup path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from encryption_manager import EncryptedStorage
from enhanced_providers import (
    OpenAIEnhanced,
    ClaudeEnhanced,
    GeminiEnhanced,
    MiniMaxEnhanced,
    ZaiEnhanced,
)


def setup_logging(log_dir: str = None, debug: bool = False) -> logging.Logger:
    """
    Setup platform-specific logging configuration

    Args:
        log_dir: Directory for log files
        debug: Enable debug logging

    Returns:
        Configured logger
    """
    # Determine log directory
    if log_dir is None:
        if sys.platform == "win32":
            log_dir = os.path.join(
                os.environ.get("APPDATA", os.path.expanduser("~")),
                "AIUsageDash",
                "logs",
            )
        else:
            log_dir = os.path.expanduser("~/.ai_usage_dash/logs")

    os.makedirs(log_dir, exist_ok=True)

    # Log file path
    log_file = os.path.join(log_dir, "ai_usage_dash.log")

    # Configure logging
    log_level = logging.DEBUG if debug else logging.INFO

    # Create formatters
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_formatter = logging.Formatter("%(levelname)s: %(message)s")

    # Setup handlers
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # File handler (always log to file)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # Console handler (only if not in daemon mode)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized. Log file: {log_file}")
    logger.info(f"Platform: {sys.platform}, Python: {sys.version}")

    return logger


# Get the base directory (handle PyInstaller)
def get_base_dir() -> str:
    """Get the base directory for the application"""
    if getattr(sys, "frozen", False):
        # Running as executable
        return os.path.dirname(sys.executable)
    else:
        # Running as script
        return os.path.dirname(os.path.abspath(__file__))


# Initialize Flask app
BASE_DIR = get_base_dir()

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "gui_templates"),
    static_folder=os.path.join(BASE_DIR, "gui_static"),
    static_url_path="/static",
)

# Global state
storage = EncryptedStorage()
providers: Dict[str, Any] = {}
update_thread = None
stop_updates = False
current_period = "daily"
logger = None


def initialize_providers():
    """Initialize provider clients from stored API keys"""
    global providers

    api_keys = storage.load_api_keys()
    if not api_keys:
        logger.info("No API keys found")
        return

    provider_classes = {
        "openai": OpenAIEnhanced,
        "claude": ClaudeEnhanced,
        "gemini": GeminiEnhanced,
        "minimax": MiniMaxEnhanced,
        "zai": ZaiEnhanced,
    }

    providers = {}
    for provider_name, api_key in api_keys.items():
        if provider_name in provider_classes and api_key:
            try:
                providers[provider_name] = provider_classes[provider_name](api_key)
                logger.info(f"Initialized {provider_name} provider")
            except Exception as e:
                logger.error(f"Failed to initialize {provider_name}: {e}")


# API Routes
@app.route("/")
def index():
    """Main dashboard page"""
    return render_template("index.html")


@app.route("/api/status")
def get_status():
    """Get application status"""
    return jsonify(
        {
            "initialized": storage.is_initialized,
            "providers": list(providers.keys()),
            "update_interval": 300,  # 5 minutes
        }
    )


@app.route("/api/initialize", methods=["POST"])
def initialize_storage():
    """Initialize encrypted storage with password"""
    try:
        data = request.get_json()
        password = data.get("password")

        if not password:
            return jsonify({"error": "Password required"}), 400

        if storage.initialize(password):
            initialize_providers()
            return jsonify(
                {
                    "success": True,
                    "message": "Storage initialized successfully",
                    "providers": list(providers.keys()),
                }
            )
        else:
            return jsonify({"error": "Failed to initialize storage"}), 500

    except Exception as e:
        logger.error(f"Error initializing storage: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/providers")
def get_providers():
    """Get list of all providers with status"""
    all_providers = ["openai", "claude", "gemini", "minimax", "zai"]

    provider_status = []
    for provider_name in all_providers:
        has_key = storage.has_api_key(provider_name)
        is_active = provider_name in providers

        provider_status.append(
            {
                "name": provider_name,
                "display_name": provider_name.upper()
                if provider_name != "claude"
                else "Claude",
                "has_key": has_key,
                "is_active": is_active,
                "status": "active"
                if is_active
                else ("configured" if has_key else "not_configured"),
            }
        )

    return jsonify({"providers": provider_status, "active_count": len(providers)})


@app.route("/api/keys", methods=["GET"])
def list_keys():
    """List providers with configured keys (without revealing keys)"""
    try:
        providers_with_keys = storage.list_providers()
        return jsonify(
            {"providers": providers_with_keys, "count": len(providers_with_keys)}
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/keys/<provider>", methods=["POST"])
def set_api_key(provider):
    """Set API key for a Provider"""
    try:
        data = request.get_json()
        api_key = data.get("api_key")

        if not api_key:
            return jsonify({"error": "API key required"}), 400

        if storage.update_api_key(provider, api_key):
            # Reinitialize providers
            initialize_providers()

            return jsonify(
                {
                    "success": True,
                    "message": f"{provider} API key saved",
                    "provider": provider,
                }
            )
        else:
            return jsonify({"error": "Failed to save API key"}), 500

    except Exception as e:
        logger.error(f"Error setting API key: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/keys/<provider>", methods=["DELETE"])
def delete_api_key(provider):
    """Delete API key for a provider"""
    try:
        if storage.delete_api_key(provider):
            # Remove from active providers
            if provider in providers:
                del providers[provider]

            return jsonify({"success": True, "message": f"{provider} API key deleted"})
        else:
            return jsonify({"error": "Failed to delete API key"}), 500

    except Exception as e:
        logger.error(f"Error deleting API key: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/usage")
def get_usage():
    """Get usage data for all active providers"""
    global current_period

    try:
        period = request.args.get("period", current_period)
        current_period = period

        usage_data = {}

        for provider_name, provider_client in providers.items():
            try:
                data = provider_client.get_usage_data(period)
                usage_data[provider_name] = data
            except Exception as e:
                usage_data[provider_name] = {
                    "provider": provider_name,
                    "status": "error",
                    "error": str(e),
                }

        return jsonify(
            {
                "period": period,
                "providers": usage_data,
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error getting usage data: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/test/<provider>", methods=["POST"])
def test_provider(provider):
    """Test connection to a provider"""
    try:
        if provider not in providers:
            return jsonify({"error": "Provider not configured"}), 400

        result = providers[provider].test_connection()
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error testing provider: {e}")
        return jsonify({"success": False, "provider": provider, "error": str(e)}), 500


@app.route("/api/refresh", methods=["POST"])
def refresh_data():
    """Force refresh of all provider data"""
    try:
        # Clear caches
        for provider_client in providers.values():
            provider_client.clear_cache()

        return jsonify(
            {"success": True, "message": "Cache cleared, data will be refreshed"}
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def background_updater():
    """Background thread to update data periodically"""
    global stop_updates

    while not stop_updates:
        try:
            time.sleep(300)  # Update every 5 minutes

            if providers and not stop_updates:
                logger.info("Background update: refreshing data...")
                for provider_client in providers.values():
                    provider_client.clear_cache()

        except Exception as e:
            logger.error(f"Error in background updater: {e}")


def start_flask():
    """Start Flask server"""
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)


def release_console():
    """Release console control on Windows"""
    if sys.platform == "win32":
        # Detach from console on Windows
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32
            kernel32.FreeConsole()
        except Exception:
            pass


def main(
    daemon: bool = False,
    debug: bool = False,
    log_dir: str = None,
    browser: bool = False,
):
    """Main entry point

    Args:
        daemon: Run in daemon mode (release console control)
        debug: Enable debug logging
        log_dir: Custom log directory
        browser: Run in browser mode (no pywebview window)
    """
    global logger, update_thread

    # Setup logging first
    logger = setup_logging(log_dir=log_dir, debug=debug)

    logger.info("=" * 50)
    logger.info("Starting AI Usage Dashboard")
    logger.info("=" * 50)

    # Handle daemon mode
    if daemon:
        logger.info("Running in daemon mode - releasing console control")
        release_console()

    if browser:
        # Browser mode: run Flask in foreground, open browser
        import webbrowser

        # Start background updater
        update_thread = threading.Thread(target=background_updater, daemon=True)
        update_thread.start()

        # Open browser after a short delay
        def open_browser():
            time.sleep(1.5)
            webbrowser.open("http://127.0.0.1:5000")

        threading.Thread(target=open_browser, daemon=True).start()

        logger.info("Starting in browser mode at http://127.0.0.1:5000")
        logger.info("Press Ctrl+C to stop.")

        try:
            app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
        except KeyboardInterrupt:
            pass
    else:
        # Desktop mode: Flask in background, pywebview in foreground
        flask_thread = threading.Thread(target=start_flask, daemon=True)
        flask_thread.start()

        # Wait for Flask to start
        time.sleep(1)
        logger.info("Flask server started on http://127.0.0.1:5000")

        # Start background updater
        update_thread = threading.Thread(target=background_updater, daemon=True)
        update_thread.start()
        logger.info("Background updater started")

        # Import pywebview lazily so the module loads even when it's not installed
        try:
            import webview
        except ImportError:
            logger.error(
                "pywebview is not installed. Install with: uv pip install pywebview"
            )
            logger.error("Falling back to browser mode.")
            main(browser=True, debug=debug, log_dir=log_dir)
            return

        # Create webview window
        window = webview.create_window(
            "AI Usage Dashboard",
            "http://127.0.0.1:5000",
            width=1400,
            height=900,
            resizable=True,
            min_size=(1024, 768),
        )

        # Start webview
        logger.info("Opening GUI window...")
        webview.start(debug=debug)

    # Cleanup
    global stop_updates
    stop_updates = True
    logger.info("Application closed")


def _parse_and_run(**overrides):
    """Shared CLI argument parser used by all entry points."""
    parser = argparse.ArgumentParser(description="AI Usage Dashboard")
    parser.add_argument(
        "--daemon",
        "-d",
        action="store_true",
        help="Run in daemon mode (release console control)",
    )
    parser.add_argument(
        "--browser",
        "-b",
        action="store_true",
        help="Run in browser mode (no desktop window)",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument(
        "--log-dir", type=str, default=None, help="Custom log directory"
    )

    args = parser.parse_args()
    kwargs = {
        "daemon": args.daemon,
        "debug": args.debug,
        "log_dir": args.log_dir,
        "browser": args.browser,
    }
    kwargs.update(overrides)
    main(**kwargs)


# ── Entry points for pyproject.toml [project.scripts] / [project.gui-scripts] ──


def cli_main():
    """Default entry point - tries desktop GUI, falls back to browser."""
    _parse_and_run()


def cli_browser():
    """Browser-only entry point (no pywebview required)."""
    _parse_and_run(browser=True)


def cli_gui():
    """Desktop GUI entry point (requires pywebview)."""
    _parse_and_run(daemon=True)


if __name__ == "__main__":
    cli_main()
