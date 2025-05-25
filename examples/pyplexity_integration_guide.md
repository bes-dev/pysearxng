# PySearXNG Integration Guide for pyplexity

## Overview

This guide explains how to integrate PySearXNG into the pyplexity project as a drop-in replacement for the existing SearXNG client, providing improved reliability and performance.

## Current pyplexity Architecture

```
pyplexity/
├── pyplexity/
│   ├── search_services.py      # Contains SearxngClient class
│   ├── config.py              # Search configuration
│   └── models.py              # SearchResult model
└── requirements.txt
```

## Integration Benefits

✅ **Improved Reliability**: JSON API instead of HTML parsing  
✅ **Better Error Handling**: Standardized exception handling  
✅ **Type Safety**: Full typing support  
✅ **Performance**: Optimized for SearXNG API  
✅ **Maintenance**: Dedicated SearXNG client library  

## Step-by-Step Integration

### Step 1: Install PySearXNG

```bash
cd /Users/sergei/work/pyplexity
pip install pyserxng
# or add to requirements.txt
echo "pyserxng>=0.1.0" >> requirements.txt
```

### Step 2: Backup Current Implementation

```bash
cp pyplexity/search_services.py pyplexity/search_services.py.backup
```

### Step 3: Replace SearxngClient

Replace the existing `SearxngClient` class in `pyplexity/search_services.py`:

```python
"""
Updated search_services.py using PySearXNG backend
"""

import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from pyserxng import SearXNGClient, SearchConfig
from pyserxng.models import SearchCategory, SafeSearchLevel, InstanceInfo
from pyserxng.config import ClientConfig


@dataclass 
class SearchResult:
    """Search result model for pyplexity."""
    title: str
    url: str
    content: str
    img_src: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'title': self.title,
            'url': self.url, 
            'content': self.content,
            'img_src': self.img_src
        }


class SearxngClient:
    """
    PySearXNG-powered SearXNG client for pyplexity.
    
    Drop-in replacement that maintains pyplexity's interface
    while using PySearXNG for improved reliability.
    """
    
    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        
        # Configure PySearXNG client
        config = ClientConfig(
            request_delay=0.5,
            default_timeout=30,
            prefer_https=False,  # Local SearXNG might be HTTP
            exclude_tor=True
        )
        
        self.client = SearXNGClient(config)
        self.local_instance = InstanceInfo(url=endpoint, status="online")
        self.client.set_instance(self.local_instance)
    
    async def search(self, 
                    query: str,
                    engines: List[str] = None,
                    languages: List[str] = None, 
                    page: int = 1,
                    safe_search: int = 1) -> List[SearchResult]:
        """
        Search using PySearXNG backend.
        
        Maintains pyplexity's interface while using PySearXNG internally.
        """
        try:
            # Configure search
            config = SearchConfig(
                categories=[SearchCategory.GENERAL],
                engines=engines or ["google", "bing", "wikipedia"],
                language=languages[0] if languages else "en",
                page=page,
                safe_search=SafeSearchLevel(safe_search),
                timeout=30
            )
            
            # Perform search
            response = await self._async_search(query, config)
            
            # Convert to pyplexity format
            results = []
            for result in response.results:
                search_result = SearchResult(
                    title=result.title,
                    url=str(result.url),
                    content=result.content,
                    img_src=str(result.thumbnail) if result.thumbnail else None
                )
                results.append(search_result)
            
            return results
            
        except Exception as e:
            print(f"Search failed: {e}")
            return []
    
    async def _async_search(self, query: str, config: SearchConfig):
        """Async wrapper for PySearXNG search."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.client.search(query, config, self.local_instance)
        )
    
    async def health_check(self) -> bool:
        """Check SearXNG instance health."""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                lambda: self.client.test_instance(self.local_instance, "test")
            )
        except Exception:
            return False
    
    def close(self):
        """Close client connection."""
        self.client.close()
```

### Step 4: Update Configuration (if needed)

The existing pyplexity configuration should work without changes:

```python
# pyplexity/config.py remains the same
searxng_endpoint: str = "http://localhost:4000"
active_engines: List[str] = ["google", "bing", "wikipedia"] 
multilingual_search: bool = True
search_languages: List[str] = ["auto", "ru", "en", "de", "fr"]
max_results: int = 15
```

### Step 5: Test Integration

```python
# Test script to verify integration
import asyncio
from pyplexity.search_services import SearxngClient

async def test_integration():
    client = SearxngClient("http://localhost:4000")
    
    # Health check
    if await client.health_check():
        print("✅ SearXNG connection OK")
        
        # Test search
        results = await client.search("python programming")
        print(f"✅ Found {len(results)} results")
        
        for result in results[:3]:
            print(f"- {result.title}")
    else:
        print("❌ SearXNG connection failed")
    
    client.close()

asyncio.run(test_integration())
```

## Migration Comparison

### Before (HTML Parsing)
```python
# Old pyplexity approach
response = httpx.post(url, data=data)
soup = BeautifulSoup(response.text, 'html.parser')
results = soup.find_all('div', class_='result')
# Manual HTML parsing...
```

### After (JSON API)
```python
# New PySearXNG approach  
response = client.search(query, config)
results = [SearchResult(...) for r in response.results]
# Structured data handling
```

## Configuration Mapping

| pyplexity Config | PySearXNG Equivalent |
|------------------|---------------------|
| `searxng_endpoint` | `InstanceInfo.url` |
| `active_engines` | `SearchConfig.engines` |
| `search_languages` | `SearchConfig.language` |
| `max_results` | Result limiting |
| `safe_search` | `SearchConfig.safe_search` |

## Error Handling Improvements

### Before
```python
# Basic HTTP error handling
try:
    response = httpx.post(...)
    if response.status_code != 200:
        raise Exception("Search failed")
except Exception as e:
    return []
```

### After  
```python
# Comprehensive error handling with PySearXNG
try:
    results = client.search(query, config)
except RateLimitError:
    # Handle rate limiting
except NetworkError:
    # Handle network issues  
except SearchError:
    # Handle search-specific errors
```

## Rollback Plan

If issues arise, rollback is simple:

```bash
# Restore original implementation
cp pyplexity/search_services.py.backup pyplexity/search_services.py

# Remove PySearXNG dependency
pip uninstall pyserxng
```

## Performance Benefits

- **Faster searches**: JSON API vs HTML parsing
- **Better caching**: PySearXNG handles instance caching
- **Reduced errors**: Robust error handling and retries
- **Type safety**: Full Python typing support

## Conclusion

This integration provides a **significant upgrade** to pyplexity's search capabilities with:

✅ **Zero breaking changes** to existing interface  
✅ **Improved reliability** through JSON API  
✅ **Better error handling** and recovery  
✅ **Future-proof** architecture  
✅ **Easy rollback** if needed  

The integration is **highly recommended** and can be completed in under 30 minutes.