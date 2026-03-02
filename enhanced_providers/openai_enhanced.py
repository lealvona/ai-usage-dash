"""
Enhanced OpenAI provider with real Admin Usage API integration.

Requires an Admin API key (sk-admin-...) for usage/costs endpoints.
Regular API keys (sk-...) can only test connection via /v1/models.
"""

import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enhanced_api_client import EnhancedAPIClient

logger = logging.getLogger(__name__)

# Approximate per-token pricing (USD) by model family.
# Used as fallback when the Costs API is unavailable.
MODEL_PRICING = {
    'gpt-4o': {'input': 2.50 / 1_000_000, 'output': 10.00 / 1_000_000},
    'gpt-4o-mini': {'input': 0.15 / 1_000_000, 'output': 0.60 / 1_000_000},
    'gpt-4-turbo': {'input': 10.00 / 1_000_000, 'output': 30.00 / 1_000_000},
    'gpt-4': {'input': 30.00 / 1_000_000, 'output': 60.00 / 1_000_000},
    'gpt-3.5-turbo': {'input': 0.50 / 1_000_000, 'output': 1.50 / 1_000_000},
    'o1': {'input': 15.00 / 1_000_000, 'output': 60.00 / 1_000_000},
    'o1-mini': {'input': 3.00 / 1_000_000, 'output': 12.00 / 1_000_000},
    'o3-mini': {'input': 1.10 / 1_000_000, 'output': 4.40 / 1_000_000},
}

DEFAULT_PRICING = {'input': 5.00 / 1_000_000, 'output': 15.00 / 1_000_000}


class OpenAIEnhanced(EnhancedAPIClient):
    """OpenAI API client using the Admin Usage & Costs API."""

    def __init__(self, api_key: str):
        super().__init__(
            provider_name='openai',
            api_key=api_key,
            rate_limits={
                'per_minute': 60,
                'per_day': 1000
            }
        )

        self.api_base = "https://api.openai.com/v1"
        self.is_admin_key = api_key.startswith('sk-admin-')
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    # ------------------------------------------------------------------
    # Connection test
    # ------------------------------------------------------------------

    def test_connection(self) -> Dict[str, Any]:
        """Test OpenAI API connection.

        Admin keys are tested against the usage endpoint.
        Regular keys fall back to /v1/models.
        """
        try:
            if self.is_admin_key:
                # Quick probe: fetch 1 minute of usage data
                start = int(time.time()) - 120
                response = self.make_request(
                    'GET',
                    f"{self.api_base}/organization/usage/completions",
                    headers=self.headers,
                    params={'start_time': start, 'bucket_width': '1m', 'limit': 1},
                    use_cache=False,
                )
                return {
                    'success': True,
                    'provider': 'openai',
                    'message': 'Admin key verified – Usage API accessible',
                    'key_type': 'admin',
                }
            else:
                response = self.make_request(
                    'GET',
                    f"{self.api_base}/models",
                    headers=self.headers,
                    use_cache=False,
                )
                return {
                    'success': True,
                    'provider': 'openai',
                    'message': 'Connection successful (regular key – no usage data)',
                    'key_type': 'regular',
                    'models_count': len(response.get('data', [])),
                }
        except Exception as e:
            return {
                'success': False,
                'provider': 'openai',
                'error': str(e),
            }

    # ------------------------------------------------------------------
    # Usage data
    # ------------------------------------------------------------------

    def get_usage_data(self, period: str = 'daily') -> Dict[str, Any]:
        """Fetch usage data from the OpenAI Admin Usage API.

        Endpoint: GET /v1/organization/usage/completions
        Requires an admin key (sk-admin-...).
        """
        if not self.is_admin_key:
            return self._no_admin_key_response(period)

        try:
            now = int(time.time())
            start_time, bucket_width = self._period_to_params(period, now)

            # --- Completions usage (paginated) ---
            usage_buckets = self._fetch_all_pages(
                f"{self.api_base}/organization/usage/completions",
                {'start_time': start_time, 'bucket_width': bucket_width, 'limit': 7},
            )

            # --- Costs (paginated) ---
            costs_buckets = self._fetch_all_pages(
                f"{self.api_base}/organization/costs",
                {'start_time': start_time, 'bucket_width': '1d', 'limit': 7},
            )

            # Aggregate usage
            total_input = 0
            total_output = 0
            total_requests = 0
            models_seen: set = set()
            breakdown: List[Dict] = []

            for bucket in usage_buckets:
                bucket_input = 0
                bucket_output = 0
                bucket_reqs = 0
                for result in bucket.get('results', []):
                    inp = result.get('input_tokens', 0)
                    out = result.get('output_tokens', 0)
                    reqs = result.get('num_model_requests', 0)
                    bucket_input += inp
                    bucket_output += out
                    bucket_reqs += reqs
                    model = result.get('model', '')
                    if model:
                        models_seen.add(model)

                total_input += bucket_input
                total_output += bucket_output
                total_requests += bucket_reqs

                breakdown.append({
                    'start_time': bucket.get('start_time'),
                    'end_time': bucket.get('end_time'),
                    'input_tokens': bucket_input,
                    'output_tokens': bucket_output,
                    'requests': bucket_reqs,
                })

            total_tokens = total_input + total_output

            # Aggregate costs
            total_cost = self._aggregate_costs(costs_buckets)

            # If costs endpoint returned 0, estimate from tokens
            if total_cost == 0 and total_tokens > 0:
                total_cost = self._estimate_cost(total_input, total_output, models_seen)

            return {
                'provider': 'openai',
                'period': period,
                'data': {
                    'total_tokens': total_tokens,
                    'input_tokens': total_input,
                    'output_tokens': total_output,
                    'total_requests': total_requests,
                    'total_cost': round(total_cost, 4),
                    'models': sorted(models_seen),
                    'daily_breakdown': breakdown,
                },
                'rate_limits': {
                    'requests_per_minute': 60,
                    'tokens_per_minute': 90000,
                    'requests_per_day': 10000,
                },
                'status': 'success',
            }

        except Exception as e:
            logger.error(f"Error getting OpenAI usage data: {e}")
            return {
                'provider': 'openai',
                'period': period,
                'status': 'error',
                'error': str(e),
            }

    # ------------------------------------------------------------------
    # Models list
    # ------------------------------------------------------------------

    def get_models(self) -> Dict[str, Any]:
        """Get available OpenAI models (works with any key type)."""
        try:
            response = self.make_request(
                'GET',
                f"{self.api_base}/models",
                headers=self.headers,
            )
            models = response.get('data', [])
            return {
                'success': True,
                'models': [
                    {
                        'id': m.get('id'),
                        'name': m.get('id'),
                        'owned_by': m.get('owned_by', 'openai'),
                    }
                    for m in models
                ],
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _period_to_params(period: str, now: int):
        """Convert a period label to (start_time, bucket_width)."""
        if period == 'hourly':
            return now - 3600, '1m'
        elif period == 'daily':
            return now - 86400, '1h'
        elif period == 'weekly':
            return now - 7 * 86400, '1d'
        else:  # monthly
            return now - 30 * 86400, '1d'

    def _fetch_all_pages(self, url: str, params: Dict) -> List[Dict]:
        """Handle cursor-based pagination for Usage/Costs endpoints."""
        all_data: List[Dict] = []
        page_params = dict(params)
        page_cursor: Optional[str] = None

        for _ in range(20):  # safety cap
            if page_cursor:
                page_params['page'] = page_cursor

            response = self.make_request(
                'GET', url, headers=self.headers, params=page_params,
            )

            all_data.extend(response.get('data', []))

            if response.get('has_more'):
                page_cursor = response.get('next_page')
                if not page_cursor:
                    break
            else:
                break

        return all_data

    @staticmethod
    def _aggregate_costs(costs_buckets: List[Dict]) -> float:
        """Sum amount values from Costs API buckets.

        The Costs API returns amount.value as a string in USD (not cents).
        """
        total_usd = 0.0
        for bucket in costs_buckets:
            for result in bucket.get('results', []):
                amount = result.get('amount', {})
                try:
                    total_usd += float(amount.get('value', 0))
                except (ValueError, TypeError):
                    pass
        return total_usd

    @staticmethod
    def _estimate_cost(input_tokens: int, output_tokens: int,
                       models: set) -> float:
        """Rough cost estimate when Costs API returns nothing."""
        # Pick the best matching pricing entry
        pricing = DEFAULT_PRICING
        for model_id in models:
            for prefix, p in MODEL_PRICING.items():
                if model_id.startswith(prefix):
                    pricing = p
                    break

        cost = (input_tokens * pricing['input'] +
                output_tokens * pricing['output'])
        return round(cost, 4)

    @staticmethod
    def _no_admin_key_response(period: str) -> Dict[str, Any]:
        """Return a helpful message when a regular key is used."""
        return {
            'provider': 'openai',
            'period': period,
            'data': {
                'total_tokens': 0,
                'input_tokens': 0,
                'output_tokens': 0,
                'total_requests': 0,
                'total_cost': 0,
                'models': [],
                'daily_breakdown': [],
                'note': ('Usage data requires an Admin API key (sk-admin-...). '
                         'Create one at platform.openai.com > Settings > Admin API Keys.'),
            },
            'rate_limits': {
                'requests_per_minute': 60,
                'tokens_per_minute': 90000,
                'requests_per_day': 10000,
            },
            'status': 'limited',
            'message': 'Admin API key required for usage data',
        }
