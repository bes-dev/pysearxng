"""
Custom exceptions for SearXNG client library.
"""


class SearXNGError(Exception):
    """Base exception for SearXNG client library."""
    pass


class InstanceNotAvailableError(SearXNGError):
    """Raised when no SearXNG instances are available."""
    pass


class SearchError(SearXNGError):
    """Raised when a search operation fails."""
    pass


class RateLimitError(SearXNGError):
    """Raised when rate limit is exceeded."""
    pass


class ConfigurationError(SearXNGError):
    """Raised when there's a configuration error."""
    pass


class NetworkError(SearXNGError):
    """Raised when there's a network-related error."""
    pass