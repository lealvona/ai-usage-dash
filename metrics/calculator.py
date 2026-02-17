from typing import Dict, Any, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class MetricsCalculator:
    """Calculates and aggregates usage metrics"""

    def __init__(self):
        self.metrics_cache = {}

    def calculate_period_usage(
        self,
        provider_data: Dict[str, Any],
        period: str = 'daily'
    ) -> Dict[str, Any]:
        """
        Calculate usage for a specific period

        Args:
            provider_data: Provider usage data
            period: Time period ('hourly', 'daily', 'weekly', 'monthly')

        Returns:
            Calculated metrics
        """
        if not provider_data or 'error' in provider_data:
            return {
                'period': period,
                'tokens': 0,
                'requests': 0,
                'cost': 0,
                'status': 'error'
            }

        usage = provider_data.get('usage', {})

        # Calculate percentage for each limit tier
        result = {
            'period': period,
            'tokens': usage.get('tokens', 0),
            'requests': usage.get('requests', 0),
            'cost': usage.get('cost', 0),
            'completion_tokens': usage.get('completion_tokens', 0),
            'prompt_tokens': usage.get('prompt_tokens', 0),
            'limits': provider_data.get('limits', {}),
            'status': self._determine_status(usage, provider_data)
        }

        # Add calculated metrics
        result.update(self._calculate_percentages(usage, provider_data))

        return result

    def _determine_status(self, usage: Dict[str, Any], provider_data: Dict[str, Any]) -> str:
        """
        Determine overall usage status

        Args:
            usage: Current usage data
            provider_data: Provider data with limits

        Returns:
            Status string
        """
        if 'error' in provider_data:
            return 'error'

        current = usage.get('tokens', 0)
        limits = provider_data.get('limits', {})

        day_limit = limits.get('day', 0)

        if current > day_limit:
            return 'exceeded'
        elif current > day_limit * 0.95:
            return 'critical'
        elif current > day_limit * 0.8:
            return 'warning'
        else:
            return 'ok'

    def _calculate_percentages(self, usage: Dict[str, Any], provider_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate various usage percentages

        Args:
            usage: Current usage data
            provider_data: Provider data with limits

        Returns:
            Dictionary with percentage calculations
        """
        limits = provider_data.get('limits', {})

        return {
            'daily_percentage': self._safe_percentage(
                usage.get('tokens', 0),
                limits.get('day', 1)
            ),
            'hourly_percentage': self._safe_percentage(
                usage.get('tokens', 0),
                limits.get('hour', 1)
            ),
            'daily_requests_percentage': self._safe_percentage(
                usage.get('requests', 0),
                limits.get('day', 1)
            ),
            'daily_cost_percentage': self._safe_percentage(
                usage.get('cost', 0),
                provider_data.get('daily_cost_limit', 1)
            )
        }

    def _safe_percentage(self, current: float, limit: float) -> float:
        """
        Safely calculate percentage with ceiling at 1.0

        Args:
            current: Current value
            limit: Limit value

        Returns:
            Percentage (0.0 to 1.0)
        """
        if limit == 0:
            return 0.0
        return min(current / limit, 1.0)

    def aggregate_provider_data(self, provider_summaries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate data from multiple providers

        Args:
            provider_summaries: List of provider summaries

        Returns:
            Aggregated metrics
        """
        if not provider_summaries:
            return {}

        aggregate = {
            'total_tokens': 0,
            'total_requests': 0,
            'total_cost': 0,
            'providers': {}
        }

        for summary in provider_summaries:
            provider_name = summary.get('provider', 'unknown')

            if 'error' in summary:
                aggregate['providers'][provider_name] = summary
                continue

            usage = summary.get('usage', {})

            aggregate['total_tokens'] += usage.get('tokens', 0)
            aggregate['total_requests'] += usage.get('requests', 0)
            aggregate['total_cost'] += usage.get('cost', 0)

            aggregate['providers'][provider_name] = summary

        return aggregate

    def calculate_trend_data(
        self,
        history_data: List[Dict[str, Any]],
        period: str = 'daily'
    ) -> Dict[str, Any]:
        """
        Calculate trend data from history

        Args:
            history_data: List of historical usage data
            period: Time period

        Returns:
            Trend metrics
        """
        if not history_data:
            return {'period': period, 'data': []}

        recent = history_data[-10:] if len(history_data) > 10 else history_data

        return {
            'period': period,
            'trend': self._calculate_trend(recent),
            'average': self._calculate_average(recent),
            'peak': self._calculate_peak(recent),
            'data': recent
        }

    def _calculate_trend(self, data: List[Dict[str, Any]]) -> str:
        """
        Calculate trend direction

        Args:
            data: Historical data

        Returns:
            Trend direction ('increasing', 'decreasing', 'stable')
        """
        if len(data) < 2:
            return 'stable'

        first = data[0]
        last = data[-1]

        current = first.get('tokens', 0)
        previous = last.get('tokens', 0)

        if previous > current:
            return 'increasing'
        elif previous < current:
            return 'decreasing'
        else:
            return 'stable'

    def _calculate_average(self, data: List[Dict[str, Any]]) -> float:
        """
        Calculate average usage

        Args:
            data: Historical data

        Returns:
            Average value
        """
        if not data:
            return 0.0

        total = sum(d.get('tokens', 0) for d in data)
        return total / len(data)

    def _calculate_peak(self, data: List[Dict[str, Any]]) -> float:
        """
        Calculate peak usage

        Args:
            data: Historical data

        Returns:
            Peak value
        """
        if not data:
            return 0.0

        return max(d.get('tokens', 0) for d in data)

    def format_cost(self, cost: float) -> str:
        """
        Format cost as string

        Args:
            cost: Cost value

        Returns:
            Formatted cost string
        """
        if cost >= 1000:
            return f"${cost/1000:.2f}k"
        return f"${cost:.2f}"

    def format_tokens(self, tokens: int) -> str:
        """
        Format token count as string

        Args:
            tokens: Token count

        Returns:
            Formatted token string
        """
        if tokens >= 1_000_000:
            return f"{tokens/1_000_000:.2f}M"
        elif tokens >= 1_000:
            return f"{tokens/1_000:.2f}K"
        return str(tokens)
