"""
Enhanced OpenAI provider with real API integration
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from enhanced_api_client import EnhancedAPIClient

logger = logging.getLogger(__name__)


class OpenAIEnhanced(EnhancedAPIClient):
    """Enhanced OpenAI API client with real usage endpoints"""
    
    def __init__(self, api_key: str):
        super().__init__(
            provider_name='openai',
            api_key=api_key,
            rate_limits={
                'per_minute': 60,  # Varies by tier
                'per_day': 1000    # Conservative default
            }
        )
        
        self.api_base = "https://api.openai.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def test_connection(self) -> Dict[str, Any]:
        """Test OpenAI API connection"""
        try:
            # Get models list to test connection
            response = self.make_request(
                'GET',
                f"{self.api_base}/models",
                headers=self.headers
            )
            
            return {
                'success': True,
                'provider': 'openai',
                'message': 'Connection successful',
                'models_count': len(response.get('data', []))
            }
            
        except Exception as e:
            return {
                'success': False,
                'provider': 'openai',
                'error': str(e)
            }
    
    def get_usage_data(self, period: str = 'daily') -> Dict[str, Any]:
        """
        Get OpenAI usage data
        
        Note: OpenAI's usage API is limited. This implementation
        uses the available endpoints and provides realistic data structure.
        """
        try:
            # Calculate date range
            end_date = datetime.now()
            if period == 'hourly':
                start_date = end_date - timedelta(hours=1)
            elif period == 'daily':
                start_date = end_date - timedelta(days=1)
            elif period == 'weekly':
                start_date = end_date - timedelta(weeks=1)
            else:  # monthly
                start_date = end_date - timedelta(days=30)
            
            # Try to get usage data from OpenAI API
            # Note: This endpoint may require special access
            try:
                response = self.make_request(
                    'GET',
                    f"{self.api_base}/usage",
                    headers=self.headers,
                    params={
                        'start_date': start_date.strftime('%Y-%m-%d'),
                        'end_date': end_date.strftime('%Y-%m-%d')
                    }
                )
                
                # Process real data
                data = response.get('data', {})
                
                return {
                    'provider': 'openai',
                    'period': period,
                    'data': {
                        'total_tokens': data.get('total_tokens', 0),
                        'total_requests': data.get('total_requests', 0),
                        'total_cost': data.get('total_cost', 0),
                        'prompt_tokens': data.get('prompt_tokens', 0),
                        'completion_tokens': data.get('completion_tokens', 0),
                        'models': data.get('models', []),
                        'daily_breakdown': data.get('daily_breakdown', [])
                    },
                    'rate_limits': {
                        'requests_per_minute': 60,
                        'tokens_per_minute': 90000,
                        'requests_per_day': 10000
                    },
                    'status': 'success'
                }
                
            except Exception as api_error:
                # If usage API not available, return placeholder
                logger.warning(f"OpenAI usage API not accessible: {api_error}")
                
                return {
                    'provider': 'openai',
                    'period': period,
                    'data': {
                        'total_tokens': 0,
                        'total_requests': 0,
                        'total_cost': 0,
                        'prompt_tokens': 0,
                        'completion_tokens': 0,
                        'models': [],
                        'daily_breakdown': [],
                        'note': 'Usage API requires special access. Visit platform.openai.com/usage for details.'
                    },
                    'rate_limits': {
                        'requests_per_minute': 60,
                        'tokens_per_minute': 90000,
                        'requests_per_day': 10000
                    },
                    'status': 'limited',
                    'message': 'Usage API requires organization access'
                }
                
        except Exception as e:
            logger.error(f"Error getting OpenAI usage data: {e}")
            return {
                'provider': 'openai',
                'period': period,
                'status': 'error',
                'error': str(e)
            }
    
    def get_models(self) -> Dict[str, Any]:
        """Get available OpenAI models"""
        try:
            response = self.make_request(
                'GET',
                f"{self.api_base}/models",
                headers=self.headers
            )
            
            models = response.get('data', [])
            
            return {
                'success': True,
                'models': [
                    {
                        'id': model.get('id'),
                        'name': model.get('id'),
                        'owned_by': model.get('owned_by', 'openai')
                    }
                    for model in models
                ]
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
