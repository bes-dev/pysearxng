#!/usr/bin/env python3
"""
PySearXNG adapter for pyplexity integration.

This adapter provides a drop-in replacement for pyplexity's SearxngClient
while using PySearXNG as the backend for improved reliability and performance.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import asyncio
from dataclasses import dataclass

# Add the src directory to Python path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pyserxng import SearXNGClient, SearchConfig
from pyserxng.models import SearchCategory, SafeSearchLevel, InstanceInfo
from pyserxng.config import ClientConfig


@dataclass
class SearchResult:
    """Search result compatible with pyplexity's SearchResult format."""
    title: str
    url: str
    content: str
    img_src: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'title': self.title,
            'url': self.url,
            'content': self.content,
            'img_src': self.img_src
        }


class PyplexitySearchAdapter:
    """
    Adapter that provides pyplexity-compatible interface using PySearXNG backend.
    
    This is a drop-in replacement for pyplexity's SearxngClient that:
    - Maintains the same API interface
    - Uses PySearXNG for improved reliability
    - Supports all pyplexity features (multi-language, engines, etc.)
    """
    
    def __init__(self, 
                 endpoint: str = "http://localhost:4000",
                 active_engines: List[str] = None,
                 search_languages: List[str] = None,
                 max_results: int = 15):
        """
        Initialize the adapter.
        
        Args:
            endpoint: SearXNG instance URL
            active_engines: List of search engines to use
            search_languages: List of languages for search
            max_results: Maximum number of results per search
        """
        self.endpoint = endpoint
        self.active_engines = active_engines or ["google", "bing", "wikipedia"]
        self.search_languages = search_languages or ["auto", "ru", "en", "de", "fr"]
        self.max_results = max_results
        
        # Configure PySearXNG client
        config = ClientConfig(
            request_delay=0.5,  # Reasonable delay for local instance
            default_timeout=30,
            prefer_https=False,  # Local might be HTTP
            exclude_tor=True
        )
        
        self.client = SearXNGClient(config)
        
        # Set up local instance
        self.local_instance = InstanceInfo(url=endpoint, status="online")
        self.client.set_instance(self.local_instance)
    
    async def search(self, 
                    query: str, 
                    engines: List[str] = None, 
                    languages: List[str] = None,
                    page: int = 1,
                    safe_search: int = 1) -> List[SearchResult]:
        """
        Perform search with pyplexity-compatible interface.
        
        Args:
            query: Search query
            engines: List of engines to use (overrides default)
            languages: List of languages to search (overrides default)
            page: Page number
            safe_search: Safe search level (0, 1, 2)
        
        Returns:
            List of SearchResult objects compatible with pyplexity
        """
        # Use provided engines or default
        search_engines = engines or self.active_engines
        
        # Use provided languages or default  
        search_langs = languages or self.search_languages
        
        # Convert safe_search to PySearXNG format
        safe_search_level = SafeSearchLevel(safe_search)
        
        results = []
        
        # Search across languages (pyplexity does this)
        for lang in search_langs:
            try:
                # Configure search
                config = SearchConfig(
                    categories=[SearchCategory.GENERAL],
                    engines=search_engines,
                    language=lang if lang != "auto" else "en",
                    page=page,
                    safe_search=safe_search_level,
                    timeout=30
                )
                
                # Perform search using PySearXNG
                response = await self._async_search(query, config)
                
                # Convert results to pyplexity format
                for result in response.results:
                    search_result = SearchResult(
                        title=result.title,
                        url=str(result.url),
                        content=result.content,
                        img_src=str(result.thumbnail) if result.thumbnail else None
                    )
                    results.append(search_result)
                
                # Limit results
                if len(results) >= self.max_results:
                    break
                    
            except Exception as e:
                print(f"Search failed for language {lang}: {e}")
                continue
        
        # Deduplicate results (pyplexity feature)
        return self._deduplicate_results(results[:self.max_results])
    
    async def _async_search(self, query: str, config: SearchConfig):
        """Async wrapper for PySearXNG search."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            lambda: self.client.search(query, config, self.local_instance)
        )
    
    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Remove duplicate results based on URL."""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            if result.url not in seen_urls:
                seen_urls.add(result.url)
                unique_results.append(result)
        
        return unique_results
    
    async def health_check(self) -> bool:
        """
        Check if SearXNG instance is healthy.
        Compatible with pyplexity's health check interface.
        """
        try:
            return await self._async_health_check()
        except Exception:
            return False
    
    async def _async_health_check(self) -> bool:
        """Async health check using PySearXNG."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.client.test_instance(self.local_instance, "test")
        )
    
    def close(self):
        """Close the client connection."""
        self.client.close()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        self.close()


# Alias for direct replacement
SearxngClient = PyplexitySearchAdapter


async def demo_pyplexity_compatibility():
    """Demonstrate pyplexity compatibility."""
    print("🔄 Demonstrating pyplexity compatibility...")
    
    # Initialize adapter (same as pyplexity's SearxngClient)
    searxng = SearxngClient(
        endpoint="http://localhost:8888",  # Adjust to your SearXNG instance
        active_engines=["google", "bing"],
        search_languages=["en", "ru"],
        max_results=10
    )
    
    try:
        # Health check (pyplexity feature)
        print("🏥 Checking SearXNG health...")
        is_healthy = await searxng.health_check()
        if not is_healthy:
            print("❌ SearXNG instance not available")
            return
        
        print("✅ SearXNG is healthy")
        
        # Perform search (pyplexity interface)
        print("🔍 Searching for 'artificial intelligence'...")
        results = await searxng.search(
            query="artificial intelligence",
            engines=["google", "bing"], 
            languages=["en"],
            page=1,
            safe_search=1
        )
        
        print(f"📊 Found {len(results)} results")
        
        # Display results (pyplexity format)
        for i, result in enumerate(results[:3], 1):
            print(f"\n{i}. {result.title}")
            print(f"   🔗 {result.url}")
            if result.content:
                content = result.content[:100] + "..." if len(result.content) > 100 else result.content
                print(f"   📝 {content}")
        
        # Convert to dict format (pyplexity uses this)
        results_dict = [r.to_dict() for r in results]
        print(f"\n📋 Results converted to dict format: {len(results_dict)} items")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        searxng.close()


async def main():
    """Main demo function."""
    print("=== PySearXNG Adapter for pyplexity ===\n")
    
    await demo_pyplexity_compatibility()
    
    print(f"\n✅ Integration complete!")
    print("💡 To use in pyplexity:")
    print("   1. Replace import in search_services.py")
    print("   2. from pyplexity_adapter import SearxngClient")
    print("   3. Keep all existing pyplexity configuration")


if __name__ == "__main__":
    asyncio.run(main())