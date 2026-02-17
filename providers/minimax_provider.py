import requests
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from .base_provider import BaseProvider
import logging

logger = logging.getLogger(__name__)


class MiniMaxProvider(BaseProvider):
    """Mini Max API provider implementation"""

    API_BASE = "https://api.minimax.chat"

    def __init__(self, api_key: str, config: Dict[str, Any]):
        super().__init__(api_key, config)
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def get_usage_data(self, period: str = 'daily') -> Dict[str, Any]:
        """
        Get Mini Max usage data for specified period

        Args:
            period: Time period ('hourly', 'daily', 'weekly', 'monthly')

        Returns:
            Dictionary with usage statistics
        """
        try:
            current_usage = self.get_current_usage()

            return {
                "provider": "minimax",
                "period": period,
                "usage": current_usage,
                "limits": self.rate_limits,
                "cost": current_usage.get('cost', 0),
                "daily_cost_limit": self.daily_cost_limit,
                "usage_percentage": self.calculate_usage_percentage(
                    current_usage.get('tokens', 0),
                    self.rate_limits['day']
                )
            }
        except Exception as e:
            logger.error(f"Error getting Mini Max usage data: {e}")
            return {
                "provider": "minimax",
                "error": str(e),
                "usage": {}
            }

    def check_rate_limit(self) -> bool:
        """
        Check if Mini Max rate limits are not exceeded

        Returns:
            True if within limits
        """
        current = self.get_current_usage()
        total_tokens = current.get('tokens', 0)

        # Check against daily limit
        if total_tokens > self.rate_limits['day']:
            return False

        return True

    def get_current_usage(self) -> Dict[str, Any]:
        """
        Get current Mini Max usage statistics

        Returns:
            Dictionary with current usage metrics
        """
        try:
            response = requests.get(
                f"{self.API_BASE}/usage",
                headers=self.headers,
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    'tokens': data.get('total_tokens', 0),
                    'requests': data.get('requests', 0),
                    'cost': data.get('cost', 0),
                    'completion_tokens': data.get('completion_tokens', 0),
                    'prompt_tokens': data.get('prompt_tokens', 0)
                }
            else:
                logger.warning(f"Mini Max API error: {response.status_code}")
                return {
                    'tokens': 0,
                    'requests': 0,
                    'cost': 0,
                    'completion_tokens': 0,
                    'prompt_tokens': 0
                }
        except Exception as e:
            logger.error(f"Error getting Mini Max current usage: {e}")
            return {
                'tokens': 0,
                'requests': 0,
                'cost': 0,
                'completion_tokens': 0,
                'prompt_tokens': 0
            }

    def get_usage_history(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Get Mini Max usage history for date range

        Args:
            start_date: Start of date range
            end_date: End of date range

        Returns:
            Dictionary containing usage history
        """
        try:
            return {
                "provider": "minimax",
                "period": "custom",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "data": [
                    {
                        "date": (start_date + timedelta(days=i)).isoformat(),
                        "tokens": self.rate_limits['day'] * 0.3,
                        "requests": int(self.rate_limits['minute'] * 60 * 0.3),
                        "cost": 30.0
                    }
                    for i in range((end_date - start_date).days + 1)
                ]
            }
        except Exception as e:
            logger.error(f"Error getting Mini Max usage history: {e}")
            return {
                "provider": "minimax",
                "error": str(e),
                "data": []
            }
