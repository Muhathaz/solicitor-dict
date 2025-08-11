"""
SRA API Client for UK Solicitors Data Processing

Handles communication with the SRA (Solicitors Regulation Authority) API
to retrieve organization and solicitor data.
"""

import time
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path
import json

try:
    from ..utils import get_logger, ConfigLoader
except ImportError:
    from utils import get_logger, ConfigLoader

logger = get_logger(__name__)


class RateLimiter:
    """Rate limiter for API requests"""
    
    def __init__(self, requests_per_period: int, period_minutes: int, delay_between_requests: float = 0.5):
        self.requests_per_period = requests_per_period
        self.period_seconds = period_minutes * 60
        self.delay_between_requests = delay_between_requests
        self.request_timestamps: List[float] = []
        
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        now = time.time()
        
        # Remove old timestamps outside the rate limit period
        cutoff = now - self.period_seconds
        self.request_timestamps = [ts for ts in self.request_timestamps if ts > cutoff]
        
        # Check if we need to wait
        if len(self.request_timestamps) >= self.requests_per_period:
            sleep_time = self.period_seconds - (now - self.request_timestamps[0]) + 1
            if sleep_time > 0:
                logger.info(f"Rate limit reached. Waiting {sleep_time:.1f} seconds...")
                time.sleep(sleep_time)
        
        # Wait minimum delay between requests
        if self.request_timestamps and (now - self.request_timestamps[-1]) < self.delay_between_requests:
            sleep_time = self.delay_between_requests - (now - self.request_timestamps[-1])
            time.sleep(sleep_time)
        
        # Record this request
        self.request_timestamps.append(time.time())


class SRAAPIClient:
    """Client for interacting with the SRA API"""
    
    def __init__(self, config_loader: Optional[ConfigLoader] = None):
        self.config = config_loader or ConfigLoader()
        self._load_config()
        self._setup_rate_limiter()
        self._setup_session()
        
    def _load_config(self):
        """Load SRA API configuration"""
        sra_config = self.config.get_setting('data_sources.sra_api', {})
        
        self.base_url = sra_config.get('base_url', 'https://sra-prod-apim.azure-api.net')
        self.api_key = sra_config.get('api_key', '')
        self.endpoints = sra_config.get('endpoints', {})
        self.timeout = sra_config.get('timeout', 30)
        self.max_retries = sra_config.get('max_retries', 3)
        self.retry_delay = sra_config.get('retry_delay', 2.0)
        
        if not self.api_key:
            raise ValueError("SRA API key not found in configuration")
            
        logger.info(f"SRA API client initialized with base URL: {self.base_url}")
    
    def _setup_rate_limiter(self):
        """Setup rate limiting"""
        rate_config = self.config.get_setting('data_sources.sra_api.rate_limit', {})
        
        requests_per_period = rate_config.get('requests_per_period', 600)
        period_minutes = rate_config.get('period_minutes', 5)
        delay_between_requests = rate_config.get('delay_between_requests', 0.5)
        
        self.rate_limiter = RateLimiter(
            requests_per_period=requests_per_period,
            period_minutes=period_minutes,
            delay_between_requests=delay_between_requests
        )
        
        logger.info(f"Rate limiter configured: {requests_per_period} requests per {period_minutes} minutes")
    
    def _setup_session(self):
        """Setup HTTP session with headers"""
        self.session = requests.Session()
        self.session.headers.update({
            'Ocp-Apim-Subscription-Key': self.api_key,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'UK-Solicitors-Directory/1.0'
        })
    
    def _make_request(self, endpoint: str, method: str = 'GET', **kwargs) -> Dict[str, Any]:
        """Make HTTP request with rate limiting and retry logic"""
        url = f"{self.base_url.rstrip('/')}{endpoint}"
        
        for attempt in range(self.max_retries + 1):
            try:
                # Apply rate limiting
                self.rate_limiter.wait_if_needed()
                
                # Make request
                logger.debug(f"Making {method} request to {url} (attempt {attempt + 1})")
                
                response = self.session.request(
                    method=method,
                    url=url,
                    timeout=self.timeout,
                    **kwargs
                )
                
                # Handle different response codes
                if response.status_code == 200:
                    data = response.json()
                    logger.debug(f"Request successful: {len(str(data))} characters received")
                    return data
                    
                elif response.status_code == 429:  # Rate limited
                    retry_after = int(response.headers.get('Retry-After', self.retry_delay))
                    logger.warning(f"Rate limited by server. Waiting {retry_after} seconds...")
                    time.sleep(retry_after)
                    continue
                    
                elif response.status_code == 401:
                    raise ValueError("Invalid API key or authentication failed")
                    
                elif response.status_code == 403:
                    raise ValueError("Access forbidden - check API key permissions")
                    
                else:
                    logger.warning(f"HTTP {response.status_code}: {response.text}")
                    response.raise_for_status()
                    
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries:
                    logger.error(f"Request failed after {self.max_retries + 1} attempts: {e}")
                    raise
                
                wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                logger.warning(f"Request failed (attempt {attempt + 1}): {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
        
        raise Exception("Maximum retries exceeded")
    
    def get_all_organizations(self) -> Dict[str, Any]:
        """Retrieve all organizations from SRA API"""
        endpoint = self.endpoints.get('organizations', '/datashare/api/V1/organisation/GetAll')
        
        logger.info("Requesting all organizations from SRA API...")
        start_time = time.time()
        
        try:
            data = self._make_request(endpoint)
            
            duration = time.time() - start_time
            org_count = data.get('Count', 0)
            orgs_received = len(data.get('Organisations', []))
            
            logger.info(f"Successfully retrieved {orgs_received} organizations "
                       f"(total count: {org_count}) in {duration:.2f}s")
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to retrieve organizations: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test API connection and authentication"""
        try:
            logger.info("Testing SRA API connection...")
            data = self.get_all_organizations()
            
            # Validate response structure
            if not isinstance(data, dict):
                logger.error("Invalid response format - expected dictionary")
                return False
                
            if 'Count' not in data or 'Organisations' not in data:
                logger.error("Invalid response structure - missing Count or Organisations")
                return False
            
            count = data.get('Count', 0)
            orgs = data.get('Organisations', [])
            
            logger.info(f"Connection test successful: {len(orgs)} organizations available (total: {count})")
            return True
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def get_api_info(self) -> Dict[str, Any]:
        """Get API information and statistics"""
        return {
            'base_url': self.base_url,
            'endpoints': self.endpoints,
            'rate_limit': {
                'requests_per_period': self.rate_limiter.requests_per_period,
                'period_seconds': self.rate_limiter.period_seconds,
                'delay_between_requests': self.rate_limiter.delay_between_requests
            },
            'timeout': self.timeout,
            'max_retries': self.max_retries,
            'retry_delay': self.retry_delay
        }
    
    def close(self):
        """Close the HTTP session"""
        if hasattr(self, 'session'):
            self.session.close()
            logger.debug("HTTP session closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class SRAAPIError(Exception):
    """Custom exception for SRA API errors"""
    pass


class SRARateLimitError(SRAAPIError):
    """Exception for rate limit errors"""
    pass


class SRAAuthenticationError(SRAAPIError):
    """Exception for authentication errors"""
    pass