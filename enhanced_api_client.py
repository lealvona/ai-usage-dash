"""
Enhanced API client with rate limiting, error handling, and retry logic
"""

import time
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from functools import wraps
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter with exponential backoff"""
    
    def __init__(self, calls_per_minute: int = 60, calls_per_day: int = 1000):
        """
        Initialize rate limiter
        
        Args:
            calls_per_minute: Maximum calls per minute
            calls_per_day: Maximum calls per day
        """
        self.calls_per_minute = calls_per_minute
        self.calls_per_day = calls_per_day
        self.minute_calls = []
        self.day_calls = []
        
    def can_call(self) -> bool:
        """Check if we can make a call without exceeding rate limits"""
        now = datetime.now()
        
        # Clean old calls
        self.minute_calls = [t for t in self.minute_calls 
                           if now - t < timedelta(minutes=1)]
        self.day_calls = [t for t in self.day_calls 
                         if now - t < timedelta(days=1)]
        
        # Check limits
        if len(self.minute_calls) >= self.calls_per_minute:
            return False
        if len(self.day_calls) >= self.calls_per_day:
            return False
            
        return True
    
    def record_call(self):
        """Record that a call was made"""
        now = datetime.now()
        self.minute_calls.append(now)
        self.day_calls.append(now)
    
    def wait_time(self) -> float:
        """Get time to wait before next call"""
        if not self.minute_calls:
            return 0
        
        now = datetime.now()
        oldest_minute_call = self.minute_calls[0] if self.minute_calls else now
        
        # Wait until oldest call is more than a minute old
        wait_seconds = 60 - (now - oldest_minute_call).total_seconds()
        return max(0, wait_seconds)


def with_retry(max_retries: int = 3, backoff_factor: float = 2.0, 
               timeout: int = 30):
    """
    Decorator for retrying API calls with exponential backoff
    
    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Multiplier for backoff time
        timeout: Request timeout in seconds
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    # Add timeout to kwargs if not present
                    if 'timeout' not in kwargs:
                        kwargs['timeout'] = timeout
                    
                    result = func(*args, **kwargs)
                    return result
                    
                except (Timeout, ConnectionError) as e:
                    last_exception = e
                    wait_time = backoff_factor ** attempt
                    
                    logger.warning(
                        f"API call failed (attempt {attempt + 1}/{max_retries}): {e}. "
                        f"Retrying in {wait_time}s..."
                    )
                    
                    if attempt < max_retries - 1:
                        time.sleep(wait_time)
                        
                except RequestException as e:
                    # Don't retry on non-network errors
                    logger.error(f"API call failed with non-retryable error: {e}")
                    raise
            
            # All retries exhausted
            logger.error(f"All {max_retries} retry attempts exhausted")
            if last_exception:
                raise last_exception
            raise Exception("API call failed after all retries")
            
        return wrapper
    return decorator


class EnhancedAPIClient:
    """
    Enhanced API client with rate limiting, error handling, and caching
    """
    
    def __init__(self, provider_name: str, api_key: str, 
                 rate_limits: Dict[str, int]):
        """
        Initialize enhanced API client
        
        Args:
            provider_name: Name of the provider
            api_key: API key for the provider
            rate_limits: Dictionary with rate limit configuration
        """
        self.provider_name = provider_name
        self.api_key = api_key
        self.session = requests.Session()
        
        # Rate limiter
        self.rate_limiter = RateLimiter(
            calls_per_minute=rate_limits.get('per_minute', 60),
            calls_per_day=rate_limits.get('per_day', 1000)
        )
        
        # Cache
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        
    def _get_cache_key(self, endpoint: str, params: Optional[Dict] = None) -> str:
        """Generate cache key"""
        import hashlib
        key_data = f"{self.provider_name}:{endpoint}:{str(params)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_cached(self, cache_key: str) -> Optional[Dict]:
        """Get cached response if valid"""
        if cache_key in self.cache:
            data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return data
        return None
    
    def _set_cache(self, cache_key: str, data: Dict):
        """Cache response"""
        self.cache[cache_key] = (data, time.time())
    
    @with_retry(max_retries=3, backoff_factor=2.0, timeout=30)
    def make_request(self, method: str, url: str, 
                     headers: Optional[Dict] = None, 
                     params: Optional[Dict] = None,
                     data: Optional[Dict] = None,
                     use_cache: bool = True) -> Dict[str, Any]:
        """
        Make rate-limited API request with caching and error handling
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: API endpoint URL
            headers: Request headers
            params: Query parameters
            data: Request body data
            use_cache: Whether to use caching
            
        Returns:
            API response as dictionary
            
        Raises:
            Exception: If request fails after retries
        """
        # Generate cache key
        cache_key = self._get_cache_key(url, params)
        
        # Check cache
        if use_cache and method == 'GET':
            cached = self._get_cached(cache_key)
            if cached:
                logger.debug(f"Using cached response for {url}")
                return cached
        
        # Check rate limit
        if not self.rate_limiter.can_call():
            wait_time = self.rate_limiter.wait_time()
            logger.warning(f"Rate limit reached, waiting {wait_time:.1f}s")
            time.sleep(wait_time)
        
        # Make request
        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=data
            )
            
            # Record call
            self.rate_limiter.record_call()
            
            # Handle HTTP errors
            if response.status_code == 429:
                # Rate limit exceeded
                retry_after = int(response.headers.get('Retry-After', 60))
                logger.warning(f"Rate limit exceeded, waiting {retry_after}s")
                time.sleep(retry_after)
                # Retry once after waiting
                response = self.session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=data
                )
            
            response.raise_for_status()
            
            # Parse response
            result = response.json()
            
            # Cache successful GET requests
            if use_cache and method == 'GET':
                self._set_cache(cache_key, result)
            
            return result
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error for {self.provider_name}: {e}")
            
            # Try to get error details from response
            try:
                error_data = e.response.json()
                error_msg = error_data.get('error', {}).get('message', str(e))
            except:
                error_msg = str(e)
            
            raise Exception(f"API error ({e.response.status_code}): {error_msg}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for {self.provider_name}: {e}")
            raise Exception(f"Network error: {str(e)}")
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test API connection
        
        Returns:
            Dictionary with connection status and details
        """
        raise NotImplementedError("Subclasses must implement test_connection")
    
    def get_usage_data(self, period: str = 'daily') -> Dict[str, Any]:
        """
        Get usage data for specified period
        
        Args:
            period: Time period (hourly, daily, weekly, monthly)
            
        Returns:
            Usage data dictionary
        """
        raise NotImplementedError("Subclasses must implement get_usage_data")
    
    def clear_cache(self):
        """Clear all cached data"""
        self.cache.clear()
        logger.info(f"Cache cleared for {self.provider_name}")
