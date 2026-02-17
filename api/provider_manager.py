from typing import Dict, Any, List, Optional
from providers import BaseProvider
from providers.openai_provider import OpenAIProvider
from providers.claude_provider import ClaudeProvider
from providers.minimax_provider import MiniMaxProvider
from providers.zai_provider import ZaiProvider
from providers.gemini_provider import GeminiProvider
import json
import os
import logging

logger = logging.getLogger(__name__)

class ProviderManager:
    """Manages provider instances and configuration"""

    def __init__(self, config_path: str = 'config/providers.json'):
        """
        Initialize provider manager

        Args:
            config_path: Path to providers configuration file
        """
        self.config_path = config_path
        self.providers: Dict[str, BaseProvider] = {}
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """
        Load provider configuration from JSON file

        Returns:
            Configuration dictionary
        """
        try:
            if not os.path.exists(self.config_path):
                logger.warning(f"Config file not found: {self.config_path}")
                return {}

            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}

    def load_providers(self, env_vars: Optional[Dict[str, str]] = None) -> None:
        """
        Load all enabled providers

        Args:
            env_vars: Dictionary of environment variable values
        """
        providers_config = self.config.get('providers', {})

        for provider_name, provider_config in providers_config.items():
            if not provider_config.get('enabled', False):
                continue

            api_key = env_vars.get(provider_name.upper() + '_API_KEY', '') if env_vars else ''

            try:
                provider = self._create_provider(provider_name, api_key, provider_config)
                self.providers[provider_name] = provider
            except Exception as e:
                logger.error(f"Failed to load provider {provider_name}: {e}")

    def _create_provider(self, provider_name: str, api_key: str, config: Dict[str, Any]) -> BaseProvider:
        """
        Create provider instance based on name

        Args:
            provider_name: Name of the provider
            api_key: API key for the provider
            config: Provider configuration

        Returns:
            Provider instance
        """
        provider_classes = {
            'openai': OpenAIProvider,
            'claude': ClaudeProvider,
            'minimax': MiniMaxProvider,
            'zai': ZaiProvider,
            'gemini': GeminiProvider
        }

        provider_class = provider_classes.get(provider_name)
        if not provider_class:
            raise ValueError(f"Unknown provider: {provider_name}")

        return provider_class(api_key, config)

    def get_provider(self, name: str) -> Optional[BaseProvider]:
        """
        Get a specific provider instance

        Args:
            name: Provider name

        Returns:
            Provider instance or None
        """
        return self.providers.get(name)

    def get_all_providers(self) -> List[BaseProvider]:
        """
        Get all loaded providers

        Returns:
            List of provider instances
        """
        return list(self.providers.values())

    def get_enabled_providers(self) -> List[BaseProvider]:
        """
        Get all enabled provider instances

        Returns:
            List of enabled provider instances
        """
        return [p for p in self.providers.values() if p.enabled]

    def get_usage_summary(self, period: str = 'daily') -> Dict[str, Any]:
        """
        Get usage summary across all providers

        Args:
            period: Time period

        Returns:
            Dictionary with usage summary
        """
        summary = {
            'period': period,
            'providers': {},
            'total': {
                'tokens': 0,
                'requests': 0,
                'cost': 0
            },
            'limits': {}
        }

        for provider_name, provider in self.providers.items():
            provider_data = provider.get_usage_data(period)
            summary['providers'][provider_name] = provider_data

            if 'usage' in provider_data:
                summary['total']['tokens'] += provider_data['usage'].get('tokens', 0)
                summary['total']['requests'] += provider_data['usage'].get('requests', 0)
                summary['total']['cost'] += provider_data.get('cost', 0)

            if 'limits' in provider_data:
                summary['limits'][provider_name] = provider_data['limits']

        return summary

    def get_alerts(self) -> List[str]:
        """
        Get alerts for providers approaching or exceeding limits

        Returns:
            List of alert messages
        """
        alerts = []

        for provider_name, provider in self.providers.items():
            current = provider.get_current_usage()
            limit = provider.rate_limits['day']
            usage = current.get('tokens', 0)

            if provider.check_rate_limit():
                status = provider.get_usage_status(usage, limit)

                if status == 'warning':
                    alerts.append(
                        f"{provider_name}: Usage is {usage/limit:.1%} of daily limit"
                    )
                elif status == 'critical':
                    alerts.append(
                        f"CRITICAL: {provider_name} at {usage/limit:.1%} of daily limit!"
                    )
                elif status == 'exceeded':
                    alerts.append(
                        f"ALERT: {provider_name} limit exceeded by {usage - limit} tokens!"
                    )

        return alerts
