"""
Enhanced Claude (Anthropic) provider with real API integration
"""

import logging
from typing import Dict, Any
from datetime import datetime, timedelta
from enhanced_api_client import EnhancedAPIClient

logger = logging.getLogger(__name__)


class ClaudeEnhanced(EnhancedAPIClient):
    """Enhanced Anthropic Claude API client with real usage endpoints"""
    
    def __init__(self, api_key: str):
        super().__init__(
            provider_name='claude',
            api_key=api_key,
            rate_limits={
                'per_minute': 50,  # Varies by tier
                'per_day': 1000    # Conservative default
            }
        )
        
        self.api_base = "https://api.anthropic.com/v1"
        self.headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
    
    def test_connection(self) -> Dict[str, Any]:
        """Test Claude API connection"""
        try:
            # Test with a minimal message request
            response = self.make_request(
                'POST',
                f"{self.api_base}/messages",
                headers=self.headers,
                data={
                    "model": "claude-3-haiku-20240307",
                    "max_tokens": 10,
                    "messages": [{"role": "user", "content": "Hi"}]
                },
                use_cache=False
            )
            
            return {
                'success': True,
                'provider': 'claude',
                'message': 'Connection successful',
                'model_used': response.get('model', 'unknown')
            }
            
        except Exception as e:
            return {
                'success': False,
                'provider': 'claude',
                'error': str(e)
            }
    
    def get_usage_data(self, period: str = 'daily') -> Dict[str, Any]:
        """
        Get Claude usage data from Admin API
        
        Note: Requires admin API key with proper permissions
        """
        try:
            # Calculate date range
            end_date = datetime.now()
            if period == 'hourly':
                start_date = end_date - timedelta(hours=1)
                bucket_width = '1h'
            elif period == 'daily':
                start_date = end_date - timedelta(days=1)
                bucket_width = '1d'
            elif period == 'weekly':
                start_date = end_date - timedelta(weeks=1)
                bucket_width = '1d'
            else:  # monthly
                start_date = end_date - timedelta(days=30)
                bucket_width = '1d'
            
            # Try to get usage data from Claude Admin API
            try:
                response = self.make_request(
                    'GET',
                    f"{self.api_base}/organizations/usage_report/messages",
                    headers=self.headers,
                    params={
                        'starting_at': start_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'ending_at': end_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'bucket_width': bucket_width
                    }
                )
                
                # Process real data
                return {
                    'provider': 'claude',
                    'period': period,
                    'data': {
                        'total_tokens': self._sum_field(response, 'input_tokens') + 
                                       self._sum_field(response, 'output_tokens'),
                        'input_tokens': self._sum_field(response, 'input_tokens'),
                        'output_tokens': self._sum_field(response, 'output_tokens'),
                        'total_requests': self._sum_field(response, 'requests'),
                        'total_cost': self._calculate_cost(response),
                        'models': self._extract_models(response),
                        'breakdown': response.get('data', [])
                    },
                    'rate_limits': {
                        'requests_per_minute': 50,
                        'input_tokens_per_minute': 100000,
                        'output_tokens_per_minute': 25000,
                        'requests_per_day': 1000
                    },
                    'status': 'success'
                }
                
            except Exception as api_error:
                logger.warning(f"Claude usage API not accessible: {api_error}")
                
                return {
                    'provider': 'claude',
                    'period': period,
                    'data': {
                        'total_tokens': 0,
                        'input_tokens': 0,
                        'output_tokens': 0,
                        'total_requests': 0,
                        'total_cost': 0,
                        'models': [],
                        'breakdown': [],
                        'note': 'Usage API requires admin API key. Visit console.anthropic.com for usage details.'
                    },
                    'rate_limits': {
                        'requests_per_minute': 50,
                        'input_tokens_per_minute': 100000,
                        'output_tokens_per_minute': 25000,
                        'requests_per_day': 1000
                    },
                    'status': 'limited',
                    'message': 'Usage API requires admin permissions'
                }
                
        except Exception as e:
            logger.error(f"Error getting Claude usage data: {e}")
            return {
                'provider': 'claude',
                'period': period,
                'status': 'error',
                'error': str(e)
            }
    
    def _sum_field(self, response: Dict, field: str) -> int:
        """Sum a field across all data points"""
        total = 0
        for item in response.get('data', []):
            total += item.get(field, 0)
        return total
    
    def _calculate_cost(self, response: Dict) -> float:
        """Calculate total cost (approximate based on standard pricing)"""
        # Standard Claude 3 pricing per 1M tokens
        INPUT_COST_PER_M = 0.25  # $0.25 per 1M input tokens
        OUTPUT_COST_PER_M = 1.25  # $1.25 per 1M output tokens
        
        input_tokens = self._sum_field(response, 'input_tokens')
        output_tokens = self._sum_field(response, 'output_tokens')
        
        cost = (input_tokens / 1_000_000 * INPUT_COST_PER_M + 
                output_tokens / 1_000_000 * OUTPUT_COST_PER_M)
        
        return round(cost, 4)
    
    def _extract_models(self, response: Dict) -> list:
        """Extract unique models used"""
        models = set()
        for item in response.get('data', []):
            if 'model' in item:
                models.add(item['model'])
        return list(models)
