"""
Pytest configuration and fixtures.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock

from pyserxng.config import ClientConfig
from pyserxng.models import InstanceInfo, InstanceStatus


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def test_config(temp_dir):
    """Create test configuration."""
    return ClientConfig(
        instances_cache_file=str(temp_dir / "test_instances.json"),
        instances_cache_ttl=3600,
        default_timeout=10,
        request_delay=0,
        log_level="DEBUG"
    )


@pytest.fixture
def sample_instances():
    """Create sample instances for testing."""
    return [
        InstanceInfo(
            url="https://searx1.example.com",
            status=InstanceStatus.ONLINE,
            uptime=99.5,
            search_time=0.5,
            tls_grade="A+",
            country="US"
        ),
        InstanceInfo(
            url="https://searx2.example.com",
            status=InstanceStatus.ONLINE,
            uptime=95.0,
            search_time=1.2,
            tls_grade="A",
            country="DE"
        ),
        InstanceInfo(
            url="http://searx3onion.onion",
            status=InstanceStatus.ONLINE,
            uptime=90.0,
            search_time=2.0,
            is_tor=True
        ),
        InstanceInfo(
            url="https://searx4.example.com",
            status=InstanceStatus.ERROR,
            uptime=85.0,
            search_time=3.0
        )
    ]


@pytest.fixture
def mock_requests_session():
    """Create a mock requests session."""
    session = Mock()
    session.headers = {}
    return session