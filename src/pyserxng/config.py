"""
Configuration management for SearXNG client.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class ClientConfig(BaseModel):
    """Configuration for SearXNG client."""
    
    # Instance discovery
    instances_url: str = "https://searx.space/data/instances.json"
    instances_cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")
    instances_cache_file: Optional[str] = None
    
    # Request settings
    default_timeout: int = Field(default=15, ge=1, le=60)
    max_retries: int = Field(default=3, ge=1, le=10)
    retry_delay: float = Field(default=2.0, ge=0.1, le=10.0)
    request_delay: float = Field(default=1.0, ge=0.0, le=5.0)
    
    # User agent and headers
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    additional_headers: Dict[str, str] = Field(default_factory=dict)
    
    # Instance selection
    prefer_https: bool = True
    exclude_tor: bool = True
    min_uptime: Optional[float] = None
    max_response_time: Optional[float] = None
    preferred_countries: Optional[list] = None
    excluded_countries: Optional[list] = None
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    # Performance
    connection_pool_size: int = Field(default=10, ge=1, le=100)
    enable_compression: bool = True
    
    class Config:
        env_prefix = "SEARXNG_"


def load_config(config_file: Optional[str] = None) -> ClientConfig:
    """Load configuration from file and environment variables."""
    config_data = {}
    
    # Load from file if provided
    if config_file and Path(config_file).exists():
        with open(config_file, 'r') as f:
            config_data = json.load(f)
    
    # Load from default config file
    default_config_file = Path.home() / ".pyserxng" / "config.json"
    if not config_file and default_config_file.exists():
        with open(default_config_file, 'r') as f:
            file_config = json.load(f)
            config_data.update(file_config)
    
    # Override with environment variables
    env_config = {}
    for key, value in os.environ.items():
        if key.startswith("SEARXNG_"):
            config_key = key[8:].lower()  # Remove SEARXNG_ prefix
            env_config[config_key] = value
    
    config_data.update(env_config)
    
    return ClientConfig(**config_data)


def save_config(config: ClientConfig, config_file: Optional[str] = None) -> None:
    """Save configuration to file."""
    if not config_file:
        config_dir = Path.home() / ".pyserxng"
        config_dir.mkdir(exist_ok=True)
        config_file = config_dir / "config.json"
    
    config_path = Path(config_file)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w') as f:
        json.dump(config.dict(), f, indent=2)


def get_cache_dir() -> Path:
    """Get the cache directory for the client."""
    cache_dir = Path.home() / ".cache" / "pyserxng"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir