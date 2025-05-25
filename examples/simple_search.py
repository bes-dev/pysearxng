#!/usr/bin/env python3
"""
Simple search example for PySearXNG.
"""

import sys
from pathlib import Path

# Add the src directory to Python path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pyserxng import SearXNGClient


def main():
    """Simple search example."""
    # Initialize client
    client = SearXNGClient()
    
    # Perform search
    print("🔍 Searching for 'artificial intelligence'...")
    results = client.search("artificial intelligence")
    
    print(f"✅ Found {len(results.results)} results in {results.search_time:.2f}s")
    print(f"🌐 Using instance: {results.instance_url}")
    
    # Show first 3 results
    for i, result in enumerate(results.results[:3], 1):
        print(f"\n{i}. {result.title}")
        print(f"   🔗 {result.url}")
        if result.content:
            content = result.content[:80] + "..." if len(result.content) > 80 else result.content
            print(f"   📝 {content}")
    
    # Close client
    client.close()


if __name__ == "__main__":
    main()