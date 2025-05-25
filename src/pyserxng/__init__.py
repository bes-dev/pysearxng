"""
PySearXNG - Python SearXNG Client Library

A Python library for interacting with SearXNG search instances.
"""

from .client import SearXNGClient
from .local_client import LocalSearXNGClient
from .models import SearchResult, InstanceInfo, SearchConfig
from .exceptions import SearXNGError, InstanceNotAvailableError, SearchError
from .instance_manager import InstanceManager

__version__ = "0.1.0"
__all__ = [
    "SearXNGClient",
    "LocalSearXNGClient",
    "SearchResult", 
    "InstanceInfo",
    "SearchConfig",
    "SearXNGError",
    "InstanceNotAvailableError", 
    "SearchError",
    "InstanceManager",
]