"""
Search result parsing for SearXNG responses.
"""

import re
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from .models import SearchResult


logger = logging.getLogger(__name__)


class SearchParser:
    """Parses search results from SearXNG responses."""
    
    @staticmethod
    def parse_json_response(data: Dict[str, Any]) -> List[SearchResult]:
        """Parse search results from JSON response."""
        results = []
        
        if 'results' not in data:
            logger.warning("No 'results' key in JSON response")
            return results
        
        for item in data['results']:
            try:
                result = SearchResult(
                    title=item.get('title', ''),
                    url=item.get('url', ''),
                    content=item.get('content', ''),
                    engine=item.get('engine'),
                    category=item.get('category'),
                    score=item.get('score'),
                    thumbnail=item.get('thumbnail'),
                    publishedDate=SearchParser._parse_date(item.get('publishedDate'))
                )
                results.append(result)
            except Exception as e:
                logger.warning(f"Failed to parse JSON result: {e}")
                continue
        
        return results
    
    @staticmethod
    def parse_html_response(html: str, base_url: str = "") -> List[SearchResult]:
        """Parse search results from HTML response."""
        results = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Try different selectors for SearXNG results
        selectors = [
            'article.result',
            '.result',
            '#results article',
            '#results .result',
            '.search_result',
            '#urls .g',  # Google-like layout
            'div[class*="result"]',
            'div.result',
            '.results article',
            '.results .result',
            'section.result',
            '[class*="result"]:not([class*="no-result"])',
            '.search-result',
            'div[id*="result"]'
        ]
        
        result_elements = []
        for selector in selectors:
            result_elements = soup.select(selector)
            if result_elements:
                logger.debug(f"Found {len(result_elements)} results with selector: {selector}")
                break
        
        if not result_elements:
            logger.warning("No result elements found, trying fallback parsing")
            # Let's also try to find any structured content that might be results
            fallback_results = SearchParser._fallback_parse(soup, base_url)
            if len(fallback_results) > 20:  # If we found too many, it's probably navigation
                return fallback_results[:10]  # Take first 10
            return fallback_results
        
        for element in result_elements:
            try:
                result = SearchParser._parse_result_element(element, base_url)
                if result:
                    results.append(result)
            except Exception as e:
                logger.warning(f"Failed to parse result element: {e}")
                continue
        
        return results
    
    @staticmethod
    def _parse_result_element(element, base_url: str) -> Optional[SearchResult]:
        """Parse a single result element."""
        # Find title
        title_selectors = ['h3', 'h2', 'h4', '.title', 'a']
        title_elem = None
        for selector in title_selectors:
            title_elem = element.select_one(selector)
            if title_elem:
                break
        
        if not title_elem:
            return None
        
        title = title_elem.get_text(strip=True)
        
        # Find URL
        url_elem = element.select_one('a[href]')
        if not url_elem:
            return None
        
        url = url_elem.get('href', '')
        
        # Make URL absolute if relative
        if url.startswith('/') and base_url:
            url = urljoin(base_url, url)
        
        # Skip invalid URLs
        if not url or not url.startswith(('http://', 'https://')):
            return None
        
        # Find content/description
        content_selectors = [
            '.content', 'p.content', '.description', 
            '.snippet', 'p', 'span.description'
        ]
        content = ""
        for selector in content_selectors:
            content_elem = element.select_one(selector)
            if content_elem:
                content = content_elem.get_text(strip=True)
                break
        
        # Find thumbnail
        thumbnail = None
        img_elem = element.select_one('img[src]')
        if img_elem:
            img_src = img_elem.get('src')
            if img_src and img_src.startswith(('http://', 'https://')):
                thumbnail = img_src
        
        # Extract engine info if available
        engine = None
        engine_elem = element.select_one('.engine, [data-engine]')
        if engine_elem:
            engine = engine_elem.get_text(strip=True) or engine_elem.get('data-engine')
        
        return SearchResult(
            title=title,
            url=url,
            content=content,
            engine=engine,
            thumbnail=thumbnail
        )
    
    @staticmethod
    def _fallback_parse(soup: BeautifulSoup, base_url: str) -> List[SearchResult]:
        """Fallback parsing when standard selectors don't work."""
        results = []
        
        # Look for any links that might be search results
        links = soup.find_all('a', href=True)
        
        seen_urls = set()
        for link in links[:20]:  # Limit to first 20 links
            href = link.get('href', '')
            
            # Make URL absolute
            if href.startswith('/') and base_url:
                href = urljoin(base_url, href)
            
            # Filter out non-result links
            if not href.startswith(('http://', 'https://')):
                continue
            
            # Skip internal links and common non-result patterns
            parsed_url = urlparse(href)
            if any(pattern in href.lower() for pattern in [
                'search', 'preferences', 'about', 'help', 'contact',
                'privacy', 'terms', 'login', 'register', 'stats',
                'github.com/searxng', 'github.com/return42', 'searx.space'
            ]):
                continue
            
            # Skip duplicate URLs
            if href in seen_urls:
                continue
            seen_urls.add(href)
            
            title = link.get_text(strip=True)
            if not title or len(title) < 3:
                title = href
            
            result = SearchResult(
                title=title,
                url=href,
                content=""
            )
            results.append(result)
        
        return results
    
    @staticmethod
    def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime object."""
        if not date_str:
            return None
        
        # Common date formats
        formats = [
            '%Y-%m-%d',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%d %H:%M:%S',
            '%d.%m.%Y',
            '%d/%m/%Y',
            '%m/%d/%Y'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # Try to extract year at least
        year_match = re.search(r'\b(20\d{2})\b', date_str)
        if year_match:
            try:
                year = int(year_match.group(1))
                return datetime(year, 1, 1)
            except ValueError:
                pass
        
        logger.debug(f"Failed to parse date: {date_str}")
        return None
    
    @staticmethod
    def extract_suggestions(data: Dict[str, Any]) -> List[str]:
        """Extract search suggestions from response."""
        suggestions = []
        
        if isinstance(data, dict):
            # JSON response
            if 'suggestions' in data:
                suggestions = data['suggestions']
            elif 'suggestion' in data:
                suggestions = [data['suggestion']]
        
        return [s for s in suggestions if isinstance(s, str) and s.strip()]
    
    @staticmethod
    def extract_engines_used(data: Dict[str, Any]) -> List[str]:
        """Extract list of engines used for the search."""
        engines = []
        
        if isinstance(data, dict) and 'results' in data:
            engine_set = set()
            for result in data['results']:
                if isinstance(result, dict) and 'engine' in result:
                    engine_set.add(result['engine'])
            engines = list(engine_set)
        
        return engines