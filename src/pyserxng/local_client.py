"""
Local SearXNG client for working with local instances.
"""

from typing import Optional, List
from .client import SearXNGClient
from .models import InstanceInfo, SearchConfig, SearchResponse
from .config import ClientConfig


class LocalSearXNGClient:
    """Simplified client for local SearXNG instances."""
    
    def __init__(self, local_url: str = "http://localhost:8888", **config_kwargs):
        """
        Initialize local SearXNG client.
        
        Args:
            local_url: URL of the local SearXNG instance
            **config_kwargs: Additional configuration options
        """
        # Default config optimized for local usage
        default_config = {
            'request_delay': 0,      # No delay needed for local
            'default_timeout': 30,   # Longer timeout
            'max_retries': 1,        # Fewer retries
            'exclude_tor': True,     # Not relevant for local
            'prefer_https': False,   # Local might be HTTP
        }
        default_config.update(config_kwargs)
        
        config = ClientConfig(**default_config)
        self.client = SearXNGClient(config)
        
        # Set up local instance
        self.local_instance = InstanceInfo(url=local_url, status="online")
        self.client.set_instance(self.local_instance)
        
        self.local_url = local_url
    
    def search(self, query: str, config: Optional[SearchConfig] = None) -> SearchResponse:
        """Search using the local instance."""
        return self.client.search(query, config, self.local_instance)
    
    def search_images(self, query: str, config: Optional[SearchConfig] = None) -> SearchResponse:
        """Search for images using the local instance."""
        return self.client.search_images(query, config)
    
    def search_videos(self, query: str, config: Optional[SearchConfig] = None) -> SearchResponse:
        """Search for videos using the local instance."""
        return self.client.search_videos(query, config)
    
    def search_news(self, query: str, config: Optional[SearchConfig] = None) -> SearchResponse:
        """Search for news using the local instance."""
        return self.client.search_news(query, config)
    
    def test_connection(self) -> bool:
        """Test if the local instance is accessible."""
        return self.client.test_instance(self.local_instance)
    
    def get_instance_info(self) -> InstanceInfo:
        """Get information about the local instance."""
        return self.local_instance
    
    def close(self):
        """Close the client."""
        self.client.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()