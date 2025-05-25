#!/usr/bin/env python3
"""
Simple example using LocalSearXNGClient.
"""

import sys
from pathlib import Path

# Add the src directory to Python path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pyserxng import LocalSearXNGClient


def main():
    """Simple local search example."""
    
    # Method 1: Using context manager (recommended)
    print("🏠 Method 1: Using context manager")
    with LocalSearXNGClient("http://localhost:8888") as client:
        # Test connection
        if not client.test_connection():
            print("❌ Cannot connect to local SearXNG instance")
            print("💡 Make sure SearXNG is running on http://localhost:8888")
            return
        
        print("✅ Connected to local SearXNG instance")
        
        # Perform search
        results = client.search("python programming")
        print(f"🔍 Found {len(results.results)} results")
        
        # Show first result
        if results.results:
            result = results.results[0]
            print(f"📄 First result: {result.title}")
            print(f"🔗 {result.url}")
    
    print("\n" + "-"*50 + "\n")
    
    # Method 2: Manual management
    print("🏠 Method 2: Manual client management")
    client = LocalSearXNGClient("http://localhost:8888")
    
    try:
        # Search for images
        image_results = client.search_images("cats")
        print(f"🖼️  Found {len(image_results.results)} images")
        
        # Search for news
        news_results = client.search_news("technology")
        print(f"📰 Found {len(news_results.results)} news articles")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        client.close()
    
    print("\n✅ Done!")


if __name__ == "__main__":
    main()