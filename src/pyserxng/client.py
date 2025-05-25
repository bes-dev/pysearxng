"""
Main SearXNG client class.
"""

import time
import logging
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin

import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .models import SearchResult, SearchResponse, SearchConfig, InstanceInfo
from .config import ClientConfig, load_config
from .instance_manager import InstanceManager
from .search_parser import SearchParser
from .exceptions import (
    SearXNGError, SearchError, RateLimitError, 
    NetworkError, InstanceNotAvailableError
)


logger = logging.getLogger(__name__)


class SearXNGClient:
    """Main client for interacting with SearXNG instances."""
    
    def __init__(self, config: Optional[ClientConfig] = None):
        """Initialize the SearXNG client."""
        self.config = config or load_config()
        self.instance_manager = InstanceManager(self.config)
        self.session = self._create_session()
        self.current_instance: Optional[InstanceInfo] = None
        
        # Setup logging
        self._setup_logging()
        
        # Ensure we have instances available
        self.instance_manager.ensure_instances_available()
    
    def _create_session(self) -> requests.Session:
        """Create a configured requests session."""
        session = requests.Session()
        
        # Set default headers
        session.headers.update({
            'User-Agent': self.config.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate' if self.config.enable_compression else 'identity',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Add custom headers
        session.headers.update(self.config.additional_headers)
        
        # Configure connection pooling
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=self.config.connection_pool_size,
            pool_maxsize=self.config.connection_pool_size
        )
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        return session
    
    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        log_level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        logger.setLevel(log_level)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        if self.config.log_file:
            file_handler = logging.FileHandler(self.config.log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
    
    def update_instances(self, force: bool = False) -> None:
        """Update the list of available instances."""
        self.instance_manager.update_instances(force=force)
    
    def get_instances(self, **filter_kwargs) -> List[InstanceInfo]:
        """Get list of available instances with optional filtering."""
        return self.instance_manager.filter_instances(**filter_kwargs)
    
    def get_best_instances(self, limit: int = 10, **kwargs) -> List[InstanceInfo]:
        """Get the best instances based on criteria."""
        return self.instance_manager.get_best_instances(limit=limit, **kwargs)
    
    def set_instance(self, instance: InstanceInfo) -> None:
        """Set a specific instance to use for searches."""
        self.current_instance = instance
        logger.info(f"Set current instance to: {instance.url}")
    
    def _select_instance(self) -> InstanceInfo:
        """Select an instance for search."""
        if self.current_instance:
            return self.current_instance
        
        # Get best instances and select one
        instances = self.instance_manager.get_best_instances(limit=5, sort_by="success_rate")
        if not instances:
            raise InstanceNotAvailableError("No suitable instances available")
        
        # Use weighted random selection based on success rate
        instance = instances[0]  # For now, just use the best one
        logger.debug(f"Selected instance: {instance.url}")
        return instance
    
    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((requests.exceptions.Timeout, requests.exceptions.ConnectionError))
    )
    def _make_search_request(
        self, 
        instance: InstanceInfo, 
        query: str, 
        config: SearchConfig
    ) -> requests.Response:
        """Make a search request to an instance."""
        # Add delay to avoid rate limiting
        if self.config.request_delay > 0:
            time.sleep(self.config.request_delay)
        
        # Prepare URL and parameters
        base_url = str(instance.url).rstrip('/')
        search_url = f"{base_url}/search"
        
        # Use simplified parameters like the working script
        params = {
            'q': query,
            'categories': ','.join(config.categories),
            'language': config.language,
        }
        
        # Only add optional parameters if they differ from defaults
        if config.page > 1:
            params['pageno'] = config.page
            
        # Only add safesearch if it's not the default
        safe_search_val = config.safe_search.value if hasattr(config.safe_search, 'value') else config.safe_search
        if safe_search_val != 1:  # 1 is moderate/default
            params['safesearch'] = safe_search_val
        
        # Add optional parameters
        if config.engines:
            params['engines'] = ','.join(config.engines)
        
        if config.time_range:
            params['time_range'] = config.time_range.value
        
        logger.debug(f"Making search request to {search_url} with params: {params}")
        
        try:
            response = self.session.get(
                search_url,
                params=params,
                timeout=config.timeout
            )
            
            # Handle rate limiting
            if response.status_code == 429:
                logger.warning(f"Rate limited by {instance.url}")
                raise RateLimitError(f"Rate limited by {instance.url}")
            
            # Handle forbidden access
            if response.status_code == 403:
                logger.warning(f"Access forbidden by {instance.url}")
                raise NetworkError(f"Access forbidden by {instance.url}")
            
            # Try alternative endpoint if 404
            if response.status_code == 404:
                search_url = f"{base_url}/"
                response = self.session.get(
                    search_url,
                    params=params,
                    timeout=config.timeout
                )
            
            response.raise_for_status()
            return response
            
        except requests.exceptions.Timeout:
            raise NetworkError(f"Timeout connecting to {instance.url}")
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Request failed for {instance.url}: {e}")
    
    def search(
        self, 
        query: str, 
        config: Optional[SearchConfig] = None,
        instance: Optional[InstanceInfo] = None
    ) -> SearchResponse:
        """Perform a search query."""
        if not query.strip():
            raise SearchError("Query cannot be empty")
        
        search_config = config or SearchConfig()
        target_instance = instance or self._select_instance()
        
        start_time = time.time()
        
        try:
            response = self._make_search_request(target_instance, query, search_config)
            response_time = time.time() - start_time
            
            # Try to parse as JSON first
            results = []
            suggestions = []
            engines_used = []
            
            try:
                json_data = response.json()
                results = SearchParser.parse_json_response(json_data)
                suggestions = SearchParser.extract_suggestions(json_data)
                engines_used = SearchParser.extract_engines_used(json_data)
                logger.debug("Successfully parsed JSON response")
            except ValueError:
                # Fallback to HTML parsing
                results = SearchParser.parse_html_response(
                    response.text, 
                    str(target_instance.url)
                )
                logger.debug("Parsed HTML response as fallback")
            
            # Record success
            self.instance_manager.record_success(str(target_instance.url), response_time)
            
            search_response = SearchResponse(
                query=query,
                results=results,
                number_of_results=len(results),
                instance_url=target_instance.url,
                search_time=response_time,
                categories_used=search_config.categories,
                engines_used=engines_used,
                suggestions=suggestions
            )
            
            logger.info(
                f"Search completed: {len(results)} results in {response_time:.2f}s "
                f"from {target_instance.url}"
            )
            
            return search_response
            
        except Exception as e:
            # Record failure
            self.instance_manager.record_failure(str(target_instance.url), e)
            
            if isinstance(e, (RateLimitError, NetworkError)):
                # Try with a different instance
                if not instance:  # Only retry if we selected the instance
                    logger.warning(f"Retrying with different instance due to: {e}")
                    other_instances = self.instance_manager.get_best_instances(
                        limit=3, 
                        sort_by="success_rate"
                    )
                    for other_instance in other_instances:
                        if other_instance.url != target_instance.url:
                            try:
                                return self.search(query, search_config, other_instance)
                            except Exception:
                                continue
            
            raise SearchError(f"Search failed: {e}")
    
    def search_images(
        self, 
        query: str, 
        config: Optional[SearchConfig] = None
    ) -> SearchResponse:
        """Search for images."""
        search_config = config or SearchConfig()
        search_config.categories = ['images']
        return self.search(query, search_config)
    
    def search_videos(
        self, 
        query: str, 
        config: Optional[SearchConfig] = None
    ) -> SearchResponse:
        """Search for videos."""
        search_config = config or SearchConfig()
        search_config.categories = ['videos']
        return self.search(query, search_config)
    
    def search_news(
        self, 
        query: str, 
        config: Optional[SearchConfig] = None
    ) -> SearchResponse:
        """Search for news."""
        search_config = config or SearchConfig()
        search_config.categories = ['news']
        return self.search(query, search_config)
    
    def get_suggestions(self, query: str) -> List[str]:
        """Get search suggestions for a query."""
        try:
            # Use a simple search with minimal results to get suggestions
            config = SearchConfig(categories=['general'])
            response = self.search(query, config)
            return response.suggestions
        except Exception as e:
            logger.warning(f"Failed to get suggestions: {e}")
            return []
    
    def test_instance(self, instance: InstanceInfo, test_query: str = "test") -> bool:
        """Test if an instance is working."""
        try:
            config = SearchConfig(timeout=10)
            response = self.search(test_query, config, instance)
            return len(response.results) > 0
        except Exception as e:
            logger.debug(f"Instance test failed for {instance.url}: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics."""
        total_instances = len(self.instance_manager.instances)
        working_instances = len(self.instance_manager.filter_instances())
        
        stats = {
            'total_instances': total_instances,
            'working_instances': working_instances,
            'current_instance': str(self.current_instance.url) if self.current_instance else None,
            'instance_stats': {
                url: stats.dict() 
                for url, stats in self.instance_manager.instance_stats.items()
            }
        }
        
        return stats
    
    def close(self) -> None:
        """Close the client and cleanup resources."""
        self.session.close()
        logger.info("SearXNG client closed")