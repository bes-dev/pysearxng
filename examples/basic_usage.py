#!/usr/bin/env python3
"""
Basic usage example for PySearXNG client library.
"""

import sys
from pathlib import Path

# Add the src directory to Python path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pyserxng import SearXNGClient, SearchConfig
from pyserxng.models import SearchCategory, SafeSearchLevel, TimeRange
from pyserxng.utils import export_search_results


def main():
    """Demonstrate basic usage of the SearXNG client."""
    
    # Initialize the client
    print("🔍 Initializing PySearXNG client...")
    client = SearXNGClient()
    
    # Update instances list
    print("📡 Updating instances list...")
    client.update_instances()
    
    # Get available instances - try different approaches
    print("🔍 Looking for instances...")
    
    # First try with lenient filtering
    instances = client.get_instances(include_tor=False)
    print(f"📋 Total instances found: {len(instances)}")
    
    # Filter to get working ones
    working_instances = [inst for inst in instances if inst.status == "online"]
    print(f"✅ Online instances: {len(working_instances)}")
    
    # Get best ones
    best_instances = client.get_best_instances(limit=5)
    print(f"⭐ Best instances: {len(best_instances)}")
    
    if best_instances:
        print("Top instances:")
        for i, instance in enumerate(best_instances, 1):
            uptime = f"{instance.uptime:.1f}%" if instance.uptime else "N/A"
            country = instance.country or "Unknown"
            print(f"  {i}. {instance.url} (Uptime: {uptime}, Country: {country})")
        instances = best_instances
    elif working_instances:
        print("Using working instances:")
        instances = working_instances[:5]
        for i, instance in enumerate(instances, 1):
            print(f"  {i}. {instance.url}")
    else:
        print("❌ No instances available. Exiting.")
        return
    
    # Perform a basic search
    print("\n🔍 Performing basic search...")
    try:
        results = client.search("Python programming")
        print(f"📊 Found {len(results.results)} results in {results.search_time:.2f}s")
        print(f"🌐 Using instance: {results.instance_url}")
        
        # Display first 5 results
        print("\n📋 Top 5 results:")
        for i, result in enumerate(results.results[:5], 1):
            print(f"\n{i}. {result.title}")
            print(f"   🔗 {result.url}")
            if result.content:
                content = result.content[:100] + "..." if len(result.content) > 100 else result.content
                print(f"   📝 {content}")
            if result.engine:
                print(f"   🔧 Engine: {result.engine}")
    
    except Exception as e:
        print(f"❌ Search failed: {e}")
        return
    
    # Search with custom configuration
    print("\n🔍 Performing image search...")
    try:
        config = SearchConfig(
            categories=[SearchCategory.IMAGES],
            safe_search=SafeSearchLevel.MODERATE,
            language="en"
        )
        
        image_results = client.search("cute cats", config)
        print(f"🖼️  Found {len(image_results.results)} image results")
        
        # Show first few image results
        for i, result in enumerate(image_results.results[:3], 1):
            print(f"  {i}. {result.title} - {result.url}")
            if result.thumbnail:
                print(f"     🖼️  Thumbnail: {result.thumbnail}")
    
    except Exception as e:
        print(f"❌ Image search failed: {e}")
    
    # Search news
    print("\n🔍 Performing news search...")
    try:
        news_results = client.search_news("artificial intelligence")
        print(f"📰 Found {len(news_results.results)} news results")
        
        for i, result in enumerate(news_results.results[:3], 1):
            print(f"  {i}. {result.title}")
            print(f"     🔗 {result.url}")
    
    except Exception as e:
        print(f"❌ News search failed: {e}")
    
    # Test specific instance
    print("\n🧪 Testing specific instance...")
    if instances:
        test_instance = instances[0]
        is_working = client.test_instance(test_instance, "test query")
        print(f"🏥 Instance {test_instance.url} is {'working' if is_working else 'not working'}")
    
    # Get and display statistics
    print("\n📈 Client statistics:")
    stats = client.get_stats()
    print(f"  📊 Total instances: {stats['total_instances']}")
    print(f"  ✅ Working instances: {stats['working_instances']}")
    if stats['current_instance']:
        print(f"  🎯 Current instance: {stats['current_instance']}")
    
    # Export results to file
    if 'results' in locals() and results.results:
        print("\n💾 Exporting results...")
        try:
            export_search_results(results.results, "search_results.json", "json")
            export_search_results(results.results, "search_results.txt", "txt")
            print("✅ Results exported to search_results.json and search_results.txt")
        except Exception as e:
            print(f"❌ Export failed: {e}")
    
    # Get suggestions
    print("\n💡 Getting search suggestions...")
    try:
        suggestions = client.get_suggestions("machine learn")
        if suggestions:
            print(f"🔍 Suggestions for 'machine learn': {', '.join(suggestions[:5])}")
        else:
            print("🔍 No suggestions available")
    except Exception as e:
        print(f"❌ Failed to get suggestions: {e}")
    
    # Close the client
    client.close()
    print("\n✅ Done!")


if __name__ == "__main__":
    main()