#!/usr/bin/env python3
"""
Example of using PySearXNG with a local SearXNG instance.
"""

import sys
from pathlib import Path

# Add the src directory to Python path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pyserxng import SearXNGClient, SearchConfig
from pyserxng.models import InstanceInfo, SearchCategory
from pyserxng.config import ClientConfig


def main():
    """Demonstrate usage with local SearXNG instance."""
    
    # Configuration for local usage
    config = ClientConfig(
        default_timeout=30,  # Longer timeout for local instance
        request_delay=0,     # No delay needed for local instance
        exclude_tor=True,
        log_level="INFO"
    )
    
    # Initialize client with config
    client = SearXNGClient(config)
    
    # Define local instance (adjust URL as needed)
    local_instance = InstanceInfo(
        url="http://localhost:8888",  # Default SearXNG port
        status="online"
    )
    
    print(f"🏠 Using local SearXNG instance: {local_instance.url}")
    
    # Test if local instance is accessible
    print("🧪 Testing local instance connectivity...")
    is_working = client.test_instance(local_instance, "test")
    
    if not is_working:
        print("❌ Local instance is not accessible!")
        print("💡 Make sure SearXNG is running on http://localhost:8888")
        print("💡 Or update the URL in this script to match your setup")
        return
    
    print("✅ Local instance is working!")
    
    # Set as current instance
    client.set_instance(local_instance)
    
    # Perform various searches
    print("\n🔍 Performing searches on local instance...")
    
    try:
        # Basic search
        print("\n1. Basic search:")
        results = client.search("python tutorial")
        print(f"   📊 Found {len(results.results)} results in {results.search_time:.2f}s")
        
        for i, result in enumerate(results.results[:3], 1):
            print(f"   {i}. {result.title}")
            print(f"      🔗 {result.url}")
        
        # Image search
        print("\n2. Image search:")
        image_results = client.search_images("nature photography")
        print(f"   🖼️  Found {len(image_results.results)} images")
        
        # News search
        print("\n3. News search:")
        news_results = client.search_news("technology")
        print(f"   📰 Found {len(news_results.results)} news articles")
        
        # Custom search configuration
        print("\n4. Custom search with specific engines:")
        custom_config = SearchConfig(
            categories=[SearchCategory.GENERAL],
            engines=["google", "bing"],  # Specify engines if configured
            language="en"
        )
        
        custom_results = client.search("artificial intelligence", custom_config)
        print(f"   🎯 Found {len(custom_results.results)} results with custom config")
        if custom_results.engines_used:
            print(f"   🔧 Engines used: {', '.join(custom_results.engines_used)}")
        
    except Exception as e:
        print(f"❌ Search failed: {e}")
    
    # Get client statistics
    print("\n📈 Client statistics:")
    stats = client.get_stats()
    print(f"   🎯 Current instance: {stats['current_instance']}")
    
    # Close client
    client.close()
    print("\n✅ Done!")


def quick_local_search(query: str, local_url: str = "http://localhost:8888"):
    """Quick function for local searches."""
    client = SearXNGClient()
    local_instance = InstanceInfo(url=local_url)
    
    try:
        results = client.search(query, instance=local_instance)
        print(f"🔍 Local search for '{query}':")
        print(f"✅ Found {len(results.results)} results")
        
        for i, result in enumerate(results.results[:5], 1):
            print(f"{i}. {result.title}")
            print(f"   {result.url}")
        
        return results
    except Exception as e:
        print(f"❌ Local search failed: {e}")
        return None
    finally:
        client.close()


if __name__ == "__main__":
    print("=== Local SearXNG Instance Example ===\n")
    
    # Run main example
    main()
    
    print("\n" + "="*50)
    print("=== Quick Local Search Example ===\n")
    
    # Quick search example
    quick_local_search("docker tutorial")