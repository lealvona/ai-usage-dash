import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from flask import Flask, render_template, jsonify, request
import logging
from dotenv import load_dotenv

from api.provider_manager import ProviderManager
from metrics.calculator import MetricsCalculator
from storage.usage_storage import UsageStorage

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Initialize components
provider_manager = ProviderManager()
metrics_calculator = MetricsCalculator()
usage_storage = UsageStorage()

# Load providers on startup
provider_manager.load_providers(dict(os.environ))


@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')


@app.route('/api/usage')
def get_usage():
    """
    Get usage summary for all providers

    Query parameters:
    - period: Time period (hourly, daily, weekly, monthly)

    Returns:
        JSON with usage summary
    """
    try:
        period = request.args.get('period', 'daily')
        period = period.lower() if period else 'daily'

        enabled_providers = provider_manager.get_enabled_providers()

        if not enabled_providers:
            return jsonify({
                'error': 'No providers configured',
                'providers': [],
                'total': {}
            })

        provider_summaries = []
        for provider in enabled_providers:
            usage_data = provider.get_usage_data(period)
            calculated = metrics_calculator.calculate_period_usage(usage_data, period)
            provider_summaries.append(calculated)

        summary = metrics_calculator.aggregate_provider_data(provider_summaries)

        return jsonify({
            'period': period,
            'providers': summary.get('providers', {}),
            'total': summary.get('total', {}),
            'alerts': provider_manager.get_alerts()
        })

    except Exception as e:
        logging.error(f"Error getting usage: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/providers')
def get_providers():
    """
    Get list of all providers with status

    Returns:
        JSON with provider list and status
    """
    try:
        providers = []
        enabled_providers = provider_manager.get_enabled_providers()

        for provider in enabled_providers:
            current_usage = provider.get_current_usage()
            limits = provider.rate_limits

            status = provider.get_usage_status(
                current_usage.get('tokens', 0),
                limits['day']
            )

            providers.append({
                'name': provider.name,
                'default_model': provider.default_model,
                'status': status,
                'current_usage': current_usage,
                'limits': limits,
                'daily_cost_limit': provider.daily_cost_limit
            })

        return jsonify({
            'providers': providers,
            'total_enabled': len(providers)
        })

    except Exception as e:
        logging.error(f"Error getting providers: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/alerts')
def get_alerts():
    """
    Get current alerts for all providers

    Returns:
        JSON with alert messages
    """
    try:
        alerts = provider_manager.get_alerts()
        return jsonify({'alerts': alerts})

    except Exception as e:
        logging.error(f"Error getting alerts: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/history/<provider>')
def get_provider_history(provider):
    """
    Get usage history for a specific provider

    Args:
        provider: Provider name

    Query parameters:
    - days: Number of days to retrieve

    Returns:
        JSON with history data
    """
    try:
        days = int(request.args.get('days', 7))
        start_date: Optional[datetime] = None
        end_date: Optional[datetime] = None

        if days > 0:
            start_date = datetime.now() - timedelta(days=days)
            end_date = datetime.now()

        provider_instance = provider_manager.get_provider(provider)

        if not provider_instance:
            return jsonify({'error': 'Provider not found'}), 404

        history_data = provider_instance.get_usage_history(start_date, end_date)

        # Calculate metrics for history
        calculated_history = []
        for entry in history_data.get('data', []):
            calculated = metrics_calculator.calculate_period_usage(
                {'usage': entry, 'limits': provider_instance.rate_limits},
                'daily'
            )
            calculated_history.append(calculated)

        return jsonify({
            'provider': provider,
            'period': history_data.get('period', 'custom'),
            'data': calculated_history
        })

    except Exception as e:
        logging.error(f"Error getting provider history: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/config', methods=['GET', 'POST'])
def manage_config():
    """
    Get or update provider configuration

    GET: Return current configuration
    POST: Update configuration

    Returns:
        JSON with configuration
    """
    try:
        if request.method == 'POST':
            config_data = request.get_json()

            # Save configuration
            with open('config/providers.json', 'w') as f:
                json.dump(config_data, f, indent=2)

            # Reload providers
            provider_manager.config = config_data
            provider_manager.load_providers(os.environ)

            return jsonify({'status': 'success', 'message': 'Configuration updated'})

        else:
            return jsonify(provider_manager.config)

    except Exception as e:
        logging.error(f"Error managing config: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/test-connection', methods=['POST'])
def test_connection():
    """
    Test connection to a provider

    Request body:
    - provider: Provider name
    - api_key: API key to test

    Returns:
        JSON with connection status
    """
    try:
        data = request.get_json()
        provider_name = data.get('provider')
        api_key = data.get('api_key') or None

        if not provider_name:
            return jsonify({'error': 'Provider name required'}), 400

        provider_instance = provider_manager.get_provider(provider_name)

        if not provider_instance:
            return jsonify({'error': 'Provider not found'}), 404

        # Update API key for testing
        old_key = provider_instance.api_key
        provider_instance.api_key = api_key or old_key

        # Test connection
        current_usage = provider_instance.get_current_usage()

        return jsonify({
            'status': 'success',
            'connected': True,
            'usage': current_usage,
            'key_valid': provider_instance.validate_api_key()
        })

    except Exception as e:
        logging.error(f"Error testing connection: {e}")
        return jsonify({'error': str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    app.run(
        debug=os.getenv('DEBUG', 'true').lower() == 'true',
        host='0.0.0.0',
        port=5000
    )
