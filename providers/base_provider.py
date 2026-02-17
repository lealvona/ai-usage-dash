from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BaseProvider(ABC):
    """Abstract base class for AI providers"""

    def __init__(self, api_key: str, config: Dict[str, Any]):
        """
        Initialize provider with API key and configuration

        Args:
            api_key: Provider's API key
            config: Provider-specific configuration
        """
        self.api_key = api_key
        self.config = config
        self.name = config.get('name', 'Unknown')
        self.enabled = config.get('enabled', False)
        self.default_model = config.get('default_model', 'unknown')

        # Rate limits from config
        self.rate_limits = {
            'minute': config.get('rate_limit_per_minute', 60),
            'hour': config.get('rate_limit_per_hour', 2000),
            'day': config.get('rate_limit_per_day', 100000)
        }

        self.daily_cost_limit = config.get('daily_cost_limit', 100.0)

    @abstractmethod
    def get_usage_data(self, period: str = 'daily') -> Dict[str, Any]:
        """
        Get usage data for the specified period

        Args:
            period: Time period ('hourly', 'daily', 'weekly', 'monthly')

        Returns:
            Dictionary containing usage statistics
        """
        pass

    @abstractmethod
    def check_rate_limit(self) -> bool:
        """
        Check if we're within rate limits

        Returns:
            True if within limits, False otherwise
        """
        pass

    @abstractmethod
    def get_current_usage(self) -> Dict[str, Any]:
        """
        Get current usage statistics

        Returns:
            Dictionary with current usage metrics
        """
        pass

    @abstractmethod
    def get_usage_history(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Get usage history for a date range

        Args:
            start_date: Start of date range
            end_date: End of date range

        Returns:
            Dictionary containing usage history
        """
        pass

    def calculate_usage_percentage(self, current: float, limit: float) -> float:
        """
        Calculate usage percentage with safety ceiling

        Args:
            current: Current usage value
            limit: Limit value

        Returns:
            Usage percentage (0.0 to 1.0)
        """
        if limit == 0:
            return 0.0
        return min(current / limit, 1.0)

    def get_usage_status(self, usage: float, limit: float) -> str:
        """
        Determine usage status

        Args:
            usage: Current usage
            limit: Limit value

        Returns:
            Status string: 'ok', 'warning', 'critical', or 'exceeded'
        """
        percentage = self.calculate_usage_percentage(usage, limit)

        if percentage > 1.0:
            return 'exceeded'
        elif percentage >= 0.95:
            return 'critical'
        elif percentage >= 0.8:
            return 'warning'
        else:
            return 'ok'

    def validate_api_key(self) -> bool:
        """
        Validate API key format

        Returns:
            True if API key is valid
        """
        return bool(self.api_key and self.api_key != 'your_key_here')
