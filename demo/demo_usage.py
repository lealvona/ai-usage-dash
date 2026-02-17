"""
Demonstration of AI Usage Dashboard functionality

This file demonstrates the various features of the AI Usage Dashboard,
including provider management, usage tracking, and visualization.
"""

import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our dashboard components
from api.provider_manager import ProviderManager
from metrics.calculator import MetricsCalculator
from storage.usage_storage import UsageStorage

metrics_calculator = MetricsCalculator()


def demo_basic_usage():
    """Basic usage demonstration"""
    print("=" * 60)
    print("AI USAGE DASHBOARD - DEMONSTRATION")
    print("=" * 60)

    print("\n1. Setting up provider manager...")

    # Initialize manager with config
    provider_manager = ProviderManager()
    metrics_calculator = MetricsCalculator()
    usage_storage = UsageStorage()

    print("✓ Provider manager initialized")

    print("\n2. Loading providers from configuration...")

    # Load providers (use your actual API keys)
    provider_manager.load_providers(dict(os.environ))

    enabled_providers = provider_manager.get_enabled_providers()
    print(f"✓ Loaded {len(enabled_providers)} enabled providers")

    if enabled_providers:
        print("\n3. Provider Details:")
        for provider in enabled_providers:
            print(f"  - {provider.name}: {provider.default_model}")
            print(f"    Rate limits: {provider.rate_limits['minute']}/min, "
                  f"{provider.rate_limits['hour']}/hr, "
                  f"{provider.rate_limits['day']}/day")

    print("\n4. Current Usage Statistics:")

    for provider in enabled_providers:
        current_usage = provider.get_current_usage()
        print(f"\n  {provider.name}:")
        print(f"    Tokens used: {current_usage.get('tokens', 0):,}")
        print(f"    Requests: {current_usage.get('requests', 0):,}")
        print(f"    Cost: {current_usage.get('cost', 0):.2f}")

    print("\n5. Usage Data by Period:")

    for period in ['hourly', 'daily', 'weekly', 'monthly']:
        print(f"\n  {period.upper()}:")
        summary = provider_manager.get_usage_summary(period)

        total = summary['total']
        print(f"    Total tokens: {total['tokens']:,}")
        print(f"    Total requests: {total['requests']:,}")
        print(f"    Total cost: {total['cost']:.2f}")

    print("\n6. Alerts and Warnings:")

    alerts = provider_manager.get_alerts()
    if alerts:
        print(f"  ⚠️  {len(alerts)} alert(s) detected:")
        for alert in alerts:
            print(f"    - {alert}")
    else:
        print("  ✓ No alerts (all usage is within limits)")

    print("\n" + "=" * 60)


def demo_metrics_calculation():
    """Demonstrate metrics calculation"""
    print("\n" + "=" * 60)
    print("METRICS CALCULATION DEMONSTRATION")
    print("=" * 60)

    metrics_calculator = MetricsCalculator()

    # Example usage data
    example_usage = {
        'tokens': 75000,
        'requests': 2500,
        'cost': 12.50,
        'completion_tokens': 50000,
        'prompt_tokens': 25000
    }

    example_limits = {
        'minute': 60,
        'hour': 2000,
        'day': 100000
    }

    print("\n1. Calculating usage percentages:")

    percentages = metrics_calculator._calculate_percentages(
        example_usage,
        {'limits': example_limits, 'daily_cost_limit': 50.0}
    )

    print(f"  Daily token usage: {percentages['daily_percentage']:.1%}")
    print(f"  Hourly token usage: {percentages['hourly_percentage']:.1%}")
    print(f"  Daily request usage: {percentages['daily_requests_percentage']:.1%}")
    print(f"  Daily cost usage: {percentages['daily_cost_percentage']:.1%}")

    print("\n2. Formatting utilities:")

    print(f"  Tokens formatted: {metrics_calculator.format_tokens(125000)}")
    print(f"  Cost formatted: {metrics_calculator.format_cost(15.75)}")

    print("\n3. Usage status determination:")

    for usage_level, limit in [(75000, 100000), (18000, 100000), (98000, 100000)]:
        status = metrics_calculator._determine_status(
            {'tokens': usage_level, 'limits': {'day': limit}},
            {}
        )
        print(f"  {usage_level}/{limit} tokens: {status}")

    print("\n" + "=" * 60)


def demo_history_analysis():
    """Demonstrate historical analysis"""
    print("\n" + "=" * 60)
    print("HISTORICAL ANALYSIS DEMONSTRATION")
    print("=" * 60)

    # Mock historical data
    mock_history = [
        {'tokens': 50000, 'requests': 1500, 'cost': 8.0},
        {'tokens': 60000, 'requests': 1800, 'cost': 10.0},
        {'tokens': 55000, 'requests': 1600, 'cost': 9.0},
        {'tokens': 70000, 'requests': 2000, 'cost': 12.0},
        {'tokens': 65000, 'requests': 1900, 'cost': 11.0},
    ]

    print("\n1. Historical data analysis:")

    trend = metrics_calculator._calculate_trend(mock_history)
    average = metrics_calculator._calculate_average(mock_history)
    peak = metrics_calculator._calculate_peak(mock_history)

    print(f"  Trend: {trend}")
    print(f"  Average tokens: {average:,.0f}")
    print(f"  Peak tokens: {peak:,.0f}")

    print("\n2. Trend interpretation:")

    if trend == 'increasing':
        print("  → Usage is increasing over time")
    elif trend == 'decreasing':
        print("  → Usage is decreasing over time")
    else:
        print("  → Usage is stable")

    print("\n" + "=" * 60)


def demo_provider_configuration():
    """Demonstrate provider configuration"""
    print("\n" + "=" * 60)
    print("PROVIDER CONFIGURATION DEMONSTRATION")
    print("=" * 60)

    # Load configuration
    with open('config/providers.json', 'r') as f:
        config = json.load(f)

    print("\n1. Current configuration:")
    print(json.dumps(config, indent=2))

    print("\n2. Available providers:")
    for name, settings in config['providers'].items():
        print(f"  - {name}:")
        print(f"    Enabled: {settings.get('enabled', False)}")
        print(f"    Default model: {settings.get('default_model', 'N/A')}")
        print(f"    Rate limits: {settings.get('rate_limit_per_minute', 0)}/min")

    print("\n3. Adding a new provider:")

    # Example of how to add a new provider
    new_provider = {
        "my_new_provider": {
            "name": "My New Provider",
            "enabled": False,
            "default_model": "model-v2",
            "rate_limit_per_minute": 100,
            "rate_limit_per_hour": 4000,
            "rate_limit_per_day": 200000,
            "daily_cost_limit": 100.0
        }
    }

    print("  You can add providers by updating config/providers.json")
    print("  Or use the API endpoint: POST /api/config")

    print("\n" + "=" * 60)


def demo_storage_operations():
    """Demonstrate storage operations"""
    print("\n" + "=" * 60)
    print("STORAGE OPERATIONS DEMONSTRATION")
    print("=" * 60)

    usage_storage = UsageStorage()

    print("\n1. Storing usage data:")

    sample_usage = {
        'provider': 'openai',
        'period': 'daily',
        'usage': {
            'tokens': 45000,
            'requests': 1500,
            'cost': 7.50
        },
        'stored_at': datetime.now().isoformat()
    }

    usage_storage.store_usage_data(sample_usage['provider'], sample_usage['period'], sample_usage['usage'])
    print("  ✓ Usage data stored")

    print("\n2. Retrieving stored data:")

    retrieved = usage_storage.get_usage_data(sample_usage['provider'], sample_usage['period'])
    print(f"  Provider: {retrieved['data'].get('tokens', 0)} tokens")

    print("\n3. Getting history:")

    history = usage_storage.get_history(limit=5)
    print(f"  History entries: {len(history)}")

    print("\n4. Provider-specific history:")

    provider_history = usage_storage.get_provider_history(sample_usage['provider'])
    print(f"  {sample_usage['provider']} history entries: {len(provider_history)}")

    print("\n5. Storage file location:")
    print(f"  {usage_storage.storage_path}")

    print("\n" + "=" * 60)


def main():
    """Run all demonstrations"""

    print("\n" + "=" * 60)
    print("AI USAGE DASHBOARD - COMPLETE DEMONSTRATION")
    print("=" * 60)

    # Check if environment variables are set
    api_keys = {
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'ANTHROPIC_API_KEY': os.getenv('ANTHROPIC_API_KEY'),
        'MINIMAX_API_KEY': os.getenv('MINIMAX_API_KEY'),
        'ZAI_API_KEY': os.getenv('ZAI_API_KEY'),
        'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY')
    }

    print("\n1. Environment Configuration:")
    for key, value in api_keys.items():
        if value:
            print(f"  ✓ {key}: Configured")
        else:
            print(f"  ⚠️  {key}: Not set")

    # Run demonstrations
    demo_basic_usage()
    demo_metrics_calculation()
    demo_history_analysis()
    demo_provider_configuration()
    demo_storage_operations()

    print("\n" + "=" * 60)
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)

    print("\nTo run the dashboard:")
    print("  python app.py")

    print("\nOr with Flask development server:")
    print("  FLASK_APP=app.py FLASK_ENV=development python -m flask run")

    print("\n" + "=" * 60)


if __name__ == '__main__':
    main()
