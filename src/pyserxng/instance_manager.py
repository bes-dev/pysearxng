"""
Instance management for SearXNG client.
"""

import json
import time
import random
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse

import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .models import InstanceInfo, InstanceStatus, InstanceStats
from .config import ClientConfig, get_cache_dir
from .exceptions import InstanceNotAvailableError, NetworkError


logger = logging.getLogger(__name__)


class InstanceManager:
    """Manages SearXNG instances discovery, caching, and selection."""
    
    def __init__(self, config: ClientConfig):
        self.config = config
        self.instances: List[InstanceInfo] = []
        self.instance_stats: Dict[str, InstanceStats] = {}
        self.cache_file = self._get_cache_file()
        self.last_update: Optional[datetime] = None
        
        # Load cached instances
        self._load_cache()
    
    def _get_cache_file(self) -> Path:
        """Get the cache file path."""
        if self.config.instances_cache_file:
            return Path(self.config.instances_cache_file)
        return get_cache_dir() / "instances.json"
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(requests.exceptions.RequestException)
    )
    def _fetch_instances_data(self) -> Dict[str, Any]:
        """Fetch instances data from searx.space."""
        try:
            response = requests.get(
                self.config.instances_url,
                timeout=self.config.default_timeout,
                headers={'User-Agent': self.config.user_agent}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch instances data: {e}")
            raise NetworkError(f"Failed to fetch instances data: {e}")
    
    def _parse_instance_data(self, url: str, data: Dict[str, Any]) -> InstanceInfo:
        """Parse instance data from API response."""
        try:
            instance_data = data.get('instance', {}) or {}
            timing_data = data.get('timing', {}) or {}
            tls_data = data.get('tls', {}) or {}
            csp_data = data.get('csp', {}) or {}
            html_data = data.get('html', {}) or {}
            network_data = data.get('network', {}) or {}
            
            # Clean numeric values
            uptime = data.get('uptime')
            if isinstance(uptime, dict):
                uptime = None
            
            search_time = timing_data.get('search')
            if isinstance(search_time, dict):
                search_time = None
            
            google_time = timing_data.get('google')
            if isinstance(google_time, dict):
                google_time = None
            
            initial_time = timing_data.get('initial')
            if isinstance(initial_time, dict):
                initial_time = None
            
            # Determine status - be more lenient about what we consider "online"
            status = InstanceStatus.ONLINE
            error_data = data.get('error')
            if error_data:
                # Only mark as error if it's a serious error, not just missing data
                if isinstance(error_data, dict) and error_data.get('type') in ['connection_error', 'timeout']:
                    status = InstanceStatus.ERROR
                elif isinstance(error_data, str) and 'error' in error_data.lower():
                    status = InstanceStatus.ERROR
            
            return InstanceInfo(
                url=url,
                version=instance_data.get('version'),
                tls_grade=tls_data.get('grade'),
                csp_grade=csp_data.get('grade'),
                html_grade=html_data.get('grade'),
                certificate=tls_data.get('certificate'),
                ipv6=network_data.get('ipv6'),
                country=network_data.get('country'),
                network=network_data.get('network_name'),
                search_time=search_time,
                google_time=google_time,
                initial_time=initial_time,
                uptime=uptime,
                comments=data.get('comments'),
                alternative_urls=data.get('alternative_urls', []),
                status=status,
                last_checked=datetime.now()
            )
        except Exception as e:
            logger.debug(f"Failed to parse instance data for {url}: {e}")
            # Still try to create a basic instance entry
            return InstanceInfo(url=url, status=InstanceStatus.ONLINE)
    
    def update_instances(self, force: bool = False) -> None:
        """Update instances list from remote source."""
        # Check if update is needed
        if not force and self.last_update:
            age = datetime.now() - self.last_update
            if age.total_seconds() < self.config.instances_cache_ttl:
                logger.debug("Instances cache is still fresh, skipping update")
                return
        
        logger.info("Updating instances list...")
        try:
            data = self._fetch_instances_data()
            
            if 'instances' not in data:
                raise ValueError("Invalid response format: missing 'instances' key")
            
            instances = []
            for url, instance_data in data['instances'].items():
                instance = self._parse_instance_data(url, instance_data)
                instances.append(instance)
            
            self.instances = instances
            self.last_update = datetime.now()
            self._save_cache()
            
            logger.info(f"Updated {len(self.instances)} instances")
            
        except Exception as e:
            logger.error(f"Failed to update instances: {e}")
            if not self.instances:
                raise InstanceNotAvailableError("No cached instances available")
    
    def _save_cache(self) -> None:
        """Save instances to cache file."""
        try:
            cache_data = {
                'last_update': self.last_update.isoformat() if self.last_update else None,
                'instances': [instance.dict() for instance in self.instances],
                'stats': {url: stats.dict() for url, stats in self.instance_stats.items()}
            }
            
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2, default=str)
            
            logger.debug(f"Saved cache to {self.cache_file}")
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")
    
    def _load_cache(self) -> None:
        """Load instances from cache file."""
        try:
            if not self.cache_file.exists():
                return
            
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)
            
            if 'last_update' in cache_data and cache_data['last_update']:
                self.last_update = datetime.fromisoformat(cache_data['last_update'])
            
            if 'instances' in cache_data:
                self.instances = [
                    InstanceInfo(**instance_data) 
                    for instance_data in cache_data['instances']
                ]
            
            if 'stats' in cache_data:
                self.instance_stats = {
                    url: InstanceStats(**stats_data)
                    for url, stats_data in cache_data['stats'].items()
                }
            
            logger.debug(f"Loaded {len(self.instances)} instances from cache")
            
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
            self.instances = []
            self.instance_stats = {}
    
    def filter_instances(
        self,
        include_tor: bool = None,
        min_uptime: float = None,
        max_response_time: float = None,
        countries: List[str] = None,
        exclude_countries: List[str] = None,
        tls_grades: List[str] = None,
        status: InstanceStatus = InstanceStatus.ONLINE
    ) -> List[InstanceInfo]:
        """Filter instances based on criteria."""
        filtered = []
        
        for instance in self.instances:
            # Status filter
            if instance.status != status:
                continue
            
            # Tor filter
            if include_tor is not None:
                if include_tor != instance.is_tor:
                    continue
            
            # Apply config defaults
            if include_tor is None and self.config.exclude_tor and instance.is_tor:
                continue
            
            # HTTPS filter - be more lenient during initial testing
            if self.config.prefer_https and not str(instance.url).startswith('https://'):
                # Allow HTTP for initial discovery, but deprioritize
                pass
            
            # Uptime filter - be more lenient, allow instances without uptime data
            uptime_threshold = min_uptime or self.config.min_uptime
            if uptime_threshold and instance.uptime is not None and instance.uptime < uptime_threshold:
                continue
            
            # Response time filter - be more lenient, allow instances without timing data
            time_threshold = max_response_time or self.config.max_response_time
            if time_threshold and instance.search_time is not None and instance.search_time > time_threshold:
                continue
            
            # Country filters
            if countries and instance.country not in countries:
                continue
            
            exclude_list = exclude_countries or self.config.excluded_countries or []
            if exclude_list and instance.country in exclude_list:
                continue
            
            # TLS grade filter
            if tls_grades and instance.tls_grade not in tls_grades:
                continue
            
            filtered.append(instance)
        
        return filtered
    
    def get_best_instances(
        self,
        limit: int = 10,
        sort_by: str = "uptime",
        **filter_kwargs
    ) -> List[InstanceInfo]:
        """Get best instances based on sorting criteria."""
        instances = self.filter_instances(**filter_kwargs)
        
        if sort_by == "uptime":
            instances.sort(
                key=lambda x: (x.uptime or 0, -(x.error_count or 0)),
                reverse=True
            )
        elif sort_by == "speed":
            instances.sort(
                key=lambda x: (x.search_time or float('inf'), x.error_count or 0)
            )
        elif sort_by == "random":
            random.shuffle(instances)
        elif sort_by == "success_rate":
            # Sort by success rate from stats
            instances.sort(
                key=lambda x: self.get_instance_stats(str(x.url)).success_rate,
                reverse=True
            )
        
        return instances[:limit]
    
    def get_instance_stats(self, url: str) -> InstanceStats:
        """Get statistics for an instance."""
        if url not in self.instance_stats:
            self.instance_stats[url] = InstanceStats()
        return self.instance_stats[url]
    
    def record_success(self, url: str, response_time: float) -> None:
        """Record a successful request to an instance."""
        stats = self.get_instance_stats(url)
        stats.total_requests += 1
        stats.successful_requests += 1
        stats.last_success = datetime.now()
        
        # Update average response time
        if stats.average_response_time == 0:
            stats.average_response_time = response_time
        else:
            # Simple moving average
            stats.average_response_time = (
                stats.average_response_time * 0.8 + response_time * 0.2
            )
    
    def record_failure(self, url: str, error: Exception) -> None:
        """Record a failed request to an instance."""
        stats = self.get_instance_stats(url)
        stats.total_requests += 1
        stats.failed_requests += 1
        stats.last_failure = datetime.now()
        
        # Update instance status if needed
        for instance in self.instances:
            if str(instance.url) == url:
                instance.error_count += 1
                if instance.error_count >= 3:
                    instance.status = InstanceStatus.ERROR
                break
    
    def get_random_instance(self, **filter_kwargs) -> Optional[InstanceInfo]:
        """Get a random instance matching criteria."""
        instances = self.filter_instances(**filter_kwargs)
        if not instances:
            return None
        return random.choice(instances)
    
    def ensure_instances_available(self) -> None:
        """Ensure we have instances available, updating if necessary."""
        if not self.instances:
            self.update_instances()
        
        if not self.instances:
            raise InstanceNotAvailableError("No SearXNG instances available")