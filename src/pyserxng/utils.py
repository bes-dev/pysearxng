"""
Utility functions for SearXNG client.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

from .models import InstanceInfo, SearchResult


logger = logging.getLogger(__name__)


def export_instances_to_json(instances: List[InstanceInfo], filename: str) -> int:
    """Export instances list to JSON file."""
    try:
        data = [instance.dict() for instance in instances]
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"Exported {len(instances)} instances to {filename}")
        return len(instances)
        
    except Exception as e:
        logger.error(f"Failed to export instances: {e}")
        raise


def import_instances_from_json(filename: str) -> List[InstanceInfo]:
    """Import instances list from JSON file."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        instances = []
        for item in data:
            try:
                instance = InstanceInfo(**item)
                instances.append(instance)
            except Exception as e:
                logger.warning(f"Failed to parse instance data: {e}")
                continue
        
        logger.info(f"Imported {len(instances)} instances from {filename}")
        return instances
        
    except Exception as e:
        logger.error(f"Failed to import instances: {e}")
        raise


def export_search_results(results: List[SearchResult], filename: str, format: str = "json") -> None:
    """Export search results to file."""
    try:
        if format.lower() == "json":
            data = [result.dict() for result in results]
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        
        elif format.lower() == "csv":
            import csv
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                if results:
                    writer = csv.DictWriter(f, fieldnames=results[0].dict().keys())
                    writer.writeheader()
                    for result in results:
                        writer.writerow(result.dict())
        
        elif format.lower() == "txt":
            with open(filename, 'w', encoding='utf-8') as f:
                for i, result in enumerate(results, 1):
                    f.write(f"{i}. {result.title}\n")
                    f.write(f"   URL: {result.url}\n")
                    if result.content:
                        f.write(f"   Description: {result.content}\n")
                    f.write("\n")
        
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        logger.info(f"Exported {len(results)} results to {filename}")
        
    except Exception as e:
        logger.error(f"Failed to export results: {e}")
        raise


def validate_url(url: str) -> bool:
    """Validate if a URL is properly formatted."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations."""
    import re
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing whitespace and dots
    filename = filename.strip(' .')
    # Ensure it's not empty
    if not filename:
        filename = "unnamed"
    return filename


def format_bytes(bytes_value: int) -> str:
    """Format bytes value to human readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human readable string."""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:.0f}m {secs:.0f}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours:.0f}h {minutes:.0f}m"


def get_domain(url: str) -> str:
    """Extract domain from URL."""
    try:
        parsed = urlparse(url)
        return parsed.netloc
    except Exception:
        return url


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split a list into chunks of specified size."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def merge_search_results(results_lists: List[List[SearchResult]]) -> List[SearchResult]:
    """Merge multiple lists of search results, removing duplicates."""
    seen_urls = set()
    merged = []
    
    for results in results_lists:
        for result in results:
            url = str(result.url)
            if url not in seen_urls:
                seen_urls.add(url)
                merged.append(result)
    
    return merged


def filter_results_by_domain(results: List[SearchResult], allowed_domains: List[str]) -> List[SearchResult]:
    """Filter search results to only include specified domains."""
    filtered = []
    
    for result in results:
        domain = get_domain(str(result.url))
        if any(allowed_domain in domain for allowed_domain in allowed_domains):
            filtered.append(result)
    
    return filtered


def deduplicate_results(results: List[SearchResult]) -> List[SearchResult]:
    """Remove duplicate results based on URL."""
    seen_urls = set()
    deduplicated = []
    
    for result in results:
        url = str(result.url)
        if url not in seen_urls:
            seen_urls.add(url)
            deduplicated.append(result)
    
    return deduplicated


class SearchResultsAnalyzer:
    """Analyzer for search results."""
    
    @staticmethod
    def get_domain_distribution(results: List[SearchResult]) -> Dict[str, int]:
        """Get distribution of results by domain."""
        domain_counts = {}
        
        for result in results:
            domain = get_domain(str(result.url))
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
        
        return dict(sorted(domain_counts.items(), key=lambda x: x[1], reverse=True))
    
    @staticmethod
    def get_engine_distribution(results: List[SearchResult]) -> Dict[str, int]:
        """Get distribution of results by search engine."""
        engine_counts = {}
        
        for result in results:
            engine = result.engine or "unknown"
            engine_counts[engine] = engine_counts.get(engine, 0) + 1
        
        return dict(sorted(engine_counts.items(), key=lambda x: x[1], reverse=True))
    
    @staticmethod
    def analyze_content_length(results: List[SearchResult]) -> Dict[str, float]:
        """Analyze content length statistics."""
        lengths = [len(result.content) for result in results if result.content]
        
        if not lengths:
            return {"count": 0, "avg": 0, "min": 0, "max": 0}
        
        return {
            "count": len(lengths),
            "avg": sum(lengths) / len(lengths),
            "min": min(lengths),
            "max": max(lengths)
        }