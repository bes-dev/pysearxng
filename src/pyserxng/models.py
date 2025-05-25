"""
Data models for SearXNG client library.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl, validator


class TLSGrade(str, Enum):
    """TLS security grades."""
    A_PLUS = "A+"
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    F = "F"


class InstanceStatus(str, Enum):
    """Instance status enumeration."""
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"
    RATE_LIMITED = "rate_limited"


class SearchCategory(str, Enum):
    """Search categories supported by SearXNG."""
    GENERAL = "general"
    IMAGES = "images"
    VIDEOS = "videos"
    NEWS = "news"
    MAP = "map"
    MUSIC = "music"
    IT = "it"
    SCIENCE = "science"
    FILES = "files"
    SOCIAL_MEDIA = "social media"


class SafeSearchLevel(int, Enum):
    """Safe search levels."""
    OFF = 0
    MODERATE = 1
    STRICT = 2


class TimeRange(str, Enum):
    """Time range filters for search."""
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


class InstanceInfo(BaseModel):
    """Information about a SearXNG instance."""
    url: HttpUrl
    version: Optional[str] = None
    tls_grade: Optional[TLSGrade] = None
    csp_grade: Optional[str] = None
    html_grade: Optional[str] = None
    certificate: Optional[str] = None
    ipv6: Optional[bool] = None
    country: Optional[str] = None
    network: Optional[str] = None
    search_time: Optional[float] = None
    google_time: Optional[float] = None
    initial_time: Optional[float] = None
    uptime: Optional[float] = None
    comments: Optional[str] = None
    alternative_urls: List[str] = Field(default_factory=list)
    is_tor: bool = False
    status: InstanceStatus = InstanceStatus.ONLINE
    last_checked: Optional[datetime] = None
    error_count: int = 0
    
    class Config:
        use_enum_values = True
    
    @validator('certificate', pre=True)
    def parse_certificate(cls, v):
        if isinstance(v, dict):
            # Extract common name from certificate dict
            if 'issuer' in v and isinstance(v['issuer'], dict):
                return v['issuer'].get('commonName', 'Unknown')
            return 'Certificate data available'
        return v
    
    @validator('comments', pre=True)
    def parse_comments(cls, v):
        if isinstance(v, list):
            return ', '.join(str(item) for item in v) if v else None
        return v
    
    @validator('is_tor', pre=True, always=True)
    def detect_tor(cls, v, values):
        if 'url' in values and values['url']:
            return str(values['url']).endswith('.onion')
        return v


class SearchConfig(BaseModel):
    """Configuration for search requests."""
    categories: List[SearchCategory] = Field(default=[SearchCategory.GENERAL])
    engines: Optional[List[str]] = None
    language: str = "en"
    page: int = Field(default=1, ge=1)
    time_range: Optional[TimeRange] = None
    safe_search: SafeSearchLevel = SafeSearchLevel.MODERATE
    timeout: int = Field(default=15, ge=1, le=60)
    
    class Config:
        use_enum_values = True


class SearchResult(BaseModel):
    """A single search result."""
    title: str
    url: HttpUrl
    content: str = ""
    engine: Optional[str] = None
    category: Optional[str] = None
    score: Optional[float] = None
    thumbnail: Optional[HttpUrl] = None
    publishedDate: Optional[datetime] = None
    
    class Config:
        use_enum_values = True


class SearchResponse(BaseModel):
    """Response from a search operation."""
    query: str
    results: List[SearchResult]
    number_of_results: int
    instance_url: HttpUrl
    search_time: float
    categories_used: List[str]
    engines_used: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    
    class Config:
        use_enum_values = True


class InstanceStats(BaseModel):
    """Statistics for an instance."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100