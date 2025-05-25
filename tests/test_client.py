"""
Tests for PySearXNG client.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
from datetime import datetime

from pyserxng import SearXNGClient, SearchConfig, SearchResult
from pyserxng.config import ClientConfig
from pyserxng.models import InstanceInfo, InstanceStatus
from pyserxng.exceptions import SearchError, InstanceNotAvailableError


class TestSearXNGClient:
    """Test cases for SearXNGClient."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return ClientConfig(
            instances_cache_ttl=3600,
            default_timeout=10,
            request_delay=0,  # No delay in tests
            log_level="DEBUG"
        )
    
    @pytest.fixture
    def mock_instance(self):
        """Create mock instance."""
        return InstanceInfo(
            url="https://test.searx.example.com",
            status=InstanceStatus.ONLINE,
            uptime=99.5,
            search_time=0.5
        )
    
    @pytest.fixture
    def client(self, config):
        """Create test client."""
        with patch('pyserxng.client.InstanceManager') as mock_manager:
            mock_manager.return_value.instances = []
            mock_manager.return_value.ensure_instances_available.return_value = None
            return SearXNGClient(config)
    
    def test_client_initialization(self, config):
        """Test client initialization."""
        with patch('pyserxng.client.InstanceManager'):
            client = SearXNGClient(config)
            assert client.config == config
            assert client.session is not None
    
    def test_search_empty_query(self, client):
        """Test search with empty query."""
        with pytest.raises(SearchError, match="Query cannot be empty"):
            client.search("")
    
    @patch('pyserxng.client.SearchParser')
    def test_successful_search(self, mock_parser, client, mock_instance):
        """Test successful search."""
        # Setup mocks
        mock_response = Mock()
        mock_response.json.return_value = {
            'results': [
                {
                    'title': 'Test Result',
                    'url': 'https://example.com',
                    'content': 'Test content'
                }
            ]
        }
        mock_response.status_code = 200
        
        client.session.get = Mock(return_value=mock_response)
        client.instance_manager.get_best_instances = Mock(return_value=[mock_instance])
        
        mock_parser.parse_json_response.return_value = [
            SearchResult(
                title="Test Result",
                url="https://example.com",
                content="Test content"
            )
        ]
        mock_parser.extract_suggestions.return_value = []
        mock_parser.extract_engines_used.return_value = []
        
        # Execute search
        result = client.search("test query")
        
        # Verify results
        assert result.query == "test query"
        assert len(result.results) == 1
        assert result.results[0].title == "Test Result"
        assert result.instance_url == mock_instance.url
    
    def test_search_with_config(self, client, mock_instance):
        """Test search with custom configuration."""
        config = SearchConfig(
            categories=['images'],
            language='es',
            page=2,
            timeout=20
        )
        
        client.instance_manager.get_best_instances = Mock(return_value=[mock_instance])
        client._make_search_request = Mock(return_value=Mock(
            json=Mock(return_value={'results': []}),
            text=""
        ))
        
        with patch('pyserxng.client.SearchParser'):
            client.search("test", config)
        
        # Verify the request was made with correct parameters
        client._make_search_request.assert_called_once()
        args = client._make_search_request.call_args
        assert args[0][2].categories == ['images']
        assert args[0][2].language == 'es'
        assert args[0][2].page == 2
    
    def test_search_rate_limited(self, client, mock_instance):
        """Test handling of rate limiting."""
        mock_response = Mock()
        mock_response.status_code = 429
        
        client.session.get = Mock(return_value=mock_response)
        client.instance_manager.get_best_instances = Mock(return_value=[mock_instance])
        
        with pytest.raises(SearchError):
            client.search("test query")
    
    def test_search_with_fallback_instance(self, client):
        """Test search with fallback to another instance."""
        instance1 = InstanceInfo(url="https://test1.example.com")
        instance2 = InstanceInfo(url="https://test2.example.com")
        
        # First instance fails, second succeeds
        def mock_get(*args, **kwargs):
            if 'test1' in args[0]:
                response = Mock()
                response.status_code = 429
                return response
            else:
                response = Mock()
                response.json.return_value = {'results': []}
                response.status_code = 200
                return response
        
        client.session.get = Mock(side_effect=mock_get)
        client.instance_manager.get_best_instances = Mock(return_value=[instance1, instance2])
        
        with patch('pyserxng.client.SearchParser'):
            result = client.search("test query")
            assert result.instance_url == instance2.url
    
    def test_no_instances_available(self, client):
        """Test behavior when no instances are available."""
        client.instance_manager.get_best_instances = Mock(return_value=[])
        
        with pytest.raises(InstanceNotAvailableError):
            client.search("test query")
    
    def test_search_images(self, client, mock_instance):
        """Test image search."""
        client.instance_manager.get_best_instances = Mock(return_value=[mock_instance])
        client._make_search_request = Mock(return_value=Mock(
            json=Mock(return_value={'results': []}),
            text=""
        ))
        
        with patch('pyserxng.client.SearchParser'):
            client.search_images("cats")
        
        # Verify categories were set to images
        args = client._make_search_request.call_args
        assert args[0][2].categories == ['images']
    
    def test_search_videos(self, client, mock_instance):
        """Test video search."""
        client.instance_manager.get_best_instances = Mock(return_value=[mock_instance])
        client._make_search_request = Mock(return_value=Mock(
            json=Mock(return_value={'results': []}),
            text=""
        ))
        
        with patch('pyserxng.client.SearchParser'):
            client.search_videos("funny cats")
        
        # Verify categories were set to videos
        args = client._make_search_request.call_args
        assert args[0][2].categories == ['videos']
    
    def test_search_news(self, client, mock_instance):
        """Test news search."""
        client.instance_manager.get_best_instances = Mock(return_value=[mock_instance])
        client._make_search_request = Mock(return_value=Mock(
            json=Mock(return_value={'results': []}),
            text=""
        ))
        
        with patch('pyserxng.client.SearchParser'):
            client.search_news("latest technology")
        
        # Verify categories were set to news
        args = client._make_search_request.call_args
        assert args[0][2].categories == ['news']
    
    def test_set_instance(self, client, mock_instance):
        """Test setting a specific instance."""
        client.set_instance(mock_instance)
        assert client.current_instance == mock_instance
    
    def test_test_instance(self, client, mock_instance):
        """Test instance testing."""
        client.instance_manager.get_best_instances = Mock(return_value=[mock_instance])
        client._make_search_request = Mock(return_value=Mock(
            json=Mock(return_value={'results': [{'title': 'test', 'url': 'http://example.com'}]}),
            text=""
        ))
        
        with patch('pyserxng.client.SearchParser') as mock_parser:
            mock_parser.parse_json_response.return_value = [
                SearchResult(title="test", url="http://example.com")
            ]
            result = client.test_instance(mock_instance)
            assert result is True
    
    def test_get_stats(self, client):
        """Test getting client statistics."""
        client.instance_manager.instances = [Mock(), Mock()]
        client.instance_manager.filter_instances = Mock(return_value=[Mock()])
        client.instance_manager.instance_stats = {}
        
        stats = client.get_stats()
        
        assert stats['total_instances'] == 2
        assert stats['working_instances'] == 1
        assert 'instance_stats' in stats
    
    def test_close_client(self, client):
        """Test closing the client."""
        client.session.close = Mock()
        client.close()
        client.session.close.assert_called_once()