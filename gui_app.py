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
from typing import Dict, Any, Optional
from datetime import datetime
from flask import Flask, render_template, jsonify, request, send_from_directory
import webview

# Setup path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from encryption_manager import EncryptedStorage
from enhanced_providers import (
    OpenAIEnhanced,
    ClaudeEnhanced,
    GeminiEnhanced,
    MiniMaxEnhanced,
    ZaiEnhanced
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_usage_dash.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Get the base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Initialize Flask app
app = Flask(__name__, 
            template_folder=os.path.join(BASE_DIR, 'gui_templates'),
            static_folder=os.path.join(BASE_DIR, 'gui_static'))

# Global state
storage = EncryptedStorage()
providers: Dict[str, Any] = {}
update_thread = None
stop_updates = False
current_period = 'daily'


def initialize_providers():
    """Initialize provider clients from stored API keys"""
    global providers
    
    api_keys = storage.load_api_keys()
    if not api_keys:
        logger.info("No API keys found")
        return
    
    provider_classes = {
        'openai': OpenAIEnhanced,
        'claude': ClaudeEnhanced,
        'gemini': GeminiEnhanced,
        'minimax': MiniMaxEnhanced,
        'zai': ZaiEnhanced
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
@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')


@app.route('/api/status')
def get_status():
    """Get application status"""
    return jsonify({
        'initialized': storage.is_initialized,
        'providers': list(providers.keys()),
        'update_interval': 300  # 5 minutes
    })


@app.route('/api/initialize', methods=['POST'])
def initialize_storage():
    """Initialize encrypted storage with password"""
    try:
        data = request.get_json()
        password = data.get('password')
        
        if not password:
            return jsonify({'error': 'Password required'}), 400
        
        if storage.initialize(password):
            initialize_providers()
            return jsonify({
                'success': True,
                'message': 'Storage initialized successfully',
                'providers': list(providers.keys())
            })
        else:
            return jsonify({'error': 'Failed to initialize storage'}), 500
            
    except Exception as e:
        logger.error(f"Error initializing storage: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/providers')
def get_providers():
    """Get list of all providers with status"""
    all_providers = ['openai', 'claude', 'gemini', 'minimax', 'zai']
    
    provider_status = []
    for provider_name in all_providers:
        has_key = storage.has_api_key(provider_name)
        is_active = provider_name in providers
        
        provider_status.append({
            'name': provider_name,
            'display_name': provider_name.upper() if provider_name != 'claude' else 'Claude',
            'has_key': has_key,
            'is_active': is_active,
            'status': 'active' if is_active else ('configured' if has_key else 'not_configured')
        })
    
    return jsonify({
        'providers': provider_status,
        'active_count': len(providers)
    })


@app.route('/api/keys', methods=['GET'])
def list_keys():
    """List providers with configured keys (without revealing keys)"""
    try:
        providers_with_keys = storage.list_providers()
        return jsonify({
            'providers': providers_with_keys,
            'count': len(providers_with_keys)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/keys/<provider>', methods=['POST'])
def set_api_key(provider):
    """Set API key for a provider"""
    try:
        data = request.get_json()
        api_key = data.get('api_key')
        
        if not api_key:
            return jsonify({'error': 'API key required'}), 400
        
        if storage.update_api_key(provider, api_key):
            # Reinitialize providers
            initialize_providers()
            
            return jsonify({
                'success': True,
                'message': f'{provider} API key saved',
                'provider': provider
            })
        else:
            return jsonify({'error': 'Failed to save API key'}), 500
            
    except Exception as e:
        logger.error(f"Error setting API key: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/keys/<provider>', methods=['DELETE'])
def delete_api_key(provider):
    """Delete API key for a provider"""
    try:
        if storage.delete_api_key(provider):
            # Remove from active providers
            if provider in providers:
                del providers[provider]
            
            return jsonify({
                'success': True,
                'message': f'{provider} API key deleted'
            })
        else:
            return jsonify({'error': 'Failed to delete API key'}), 500
            
    except Exception as e:
        logger.error(f"Error deleting API key: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/usage')
def get_usage():
    """Get usage data for all active providers"""
    global current_period
    
    try:
        period = request.args.get('period', current_period)
        current_period = period
        
        usage_data = {}
        
        for provider_name, provider_client in providers.items():
            try:
                data = provider_client.get_usage_data(period)
                usage_data[provider_name] = data
            except Exception as e:
                usage_data[provider_name] = {
                    'provider': provider_name,
                    'status': 'error',
                    'error': str(e)
                }
        
        return jsonify({
            'period': period,
            'providers': usage_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting usage data: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/test/<provider>', methods=['POST'])
def test_provider(provider):
    """Test connection to a provider"""
    try:
        if provider not in providers:
            return jsonify({'error': 'Provider not configured'}), 400
        
        result = providers[provider].test_connection()
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error testing provider: {e}")
        return jsonify({
            'success': False,
            'provider': provider,
            'error': str(e)
        }), 500


@app.route('/api/refresh', methods=['POST'])
def refresh_data():
    """Force refresh of all provider data"""
    try:
        # Clear caches
        for provider_client in providers.values():
            provider_client.clear_cache()
        
        return jsonify({
            'success': True,
            'message': 'Cache cleared, data will be refreshed'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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
    app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)


def main():
    """Main entry point"""
    global update_thread
    
    logger.info("Starting AI Usage Dashboard GUI...")
    
    # Start Flask in background thread
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()
    
    # Wait for Flask to start
    time.sleep(1)
    
    # Start background updater
    update_thread = threading.Thread(target=background_updater, daemon=True)
    update_thread.start()
    
    # Create webview window
    window = webview.create_window(
        'AI Usage Dashboard',
        'http://127.0.0.1:5000',
        width=1400,
        height=900,
        resizable=True,
        min_size=(1024, 768)
    )
    
    # Start webview
    webview.start(debug=False)
    
    # Cleanup
    global stop_updates
    stop_updates = True
    logger.info("Application closed")


if __name__ == '__main__':
    main()
