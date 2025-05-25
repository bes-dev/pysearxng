# PySearXNG

A comprehensive Python library for interacting with SearXNG search instances.

## Features

- 🔍 **Easy search functionality** - Simple API for performing searches
- 🌐 **Instance management** - Automatic discovery and management of public SearXNG instances
- ⚡ **Intelligent failover** - Automatically switches to working instances
- 📊 **Statistics tracking** - Monitor instance performance and success rates
- 🛡️ **Rate limiting handling** - Built-in protection against rate limits
- 🔧 **Highly configurable** - Extensive configuration options
- 📦 **Multiple export formats** - JSON, CSV, and TXT export support
- 🧪 **Comprehensive testing** - Full test suite included

## Installation

```bash
# Install the library
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"
```

## Quick Start

### Using Public Instances

```python
from pyserxng import SearXNGClient, SearchConfig
from pyserxng.models import SearchCategory

# Initialize the client (uses public instances)
client = SearXNGClient()

# Perform a basic search
results = client.search("Python programming")

print(f"Found {len(results.results)} results")
for result in results.results[:5]:
    print(f"- {result.title}: {result.url}")

# Search for images
image_results = client.search_images("cute cats")

# Search for news
news_results = client.search_news("artificial intelligence")

# Custom search configuration
config = SearchConfig(
    categories=[SearchCategory.GENERAL],
    language="en",
    safe_search=SafeSearchLevel.MODERATE,
    page=1
)
custom_results = client.search("machine learning", config)
```

### Using Local SearXNG Instance

```python
from pyserxng import LocalSearXNGClient

# Method 1: Simple usage with context manager
with LocalSearXNGClient("http://localhost:8888") as client:
    if client.test_connection():
        results = client.search("python tutorial")
        print(f"Found {len(results.results)} results")

# Method 2: Manual management
client = LocalSearXNGClient("http://localhost:8888")
try:
    results = client.search("machine learning")
    image_results = client.search_images("nature")
finally:
    client.close()

# Method 3: Using regular client with specific instance
from pyserxng import SearXNGClient
from pyserxng.models import InstanceInfo

client = SearXNGClient()
local_instance = InstanceInfo(url="http://localhost:8888")
results = client.search("AI research", instance=local_instance)
```

## Configuration

### Environment Variables

You can configure the client using environment variables:

```bash
export SEARXNG_DEFAULT_TIMEOUT=15
export SEARXNG_REQUEST_DELAY=1.0
export SEARXNG_EXCLUDE_TOR=true
export SEARXNG_LOG_LEVEL=INFO
```

### Configuration File

Create a configuration file at `~/.pyserxng/config.json`:

```json
{
  "default_timeout": 15,
  "request_delay": 1.0,
  "exclude_tor": true,
  "log_level": "INFO",
  "preferred_countries": ["US", "DE", "FR"],
  "min_uptime": 95.0
}
```

### Programmatic Configuration

```python
from pyserxng.config import ClientConfig

config = ClientConfig(
    default_timeout=20,
    request_delay=2.0,
    exclude_tor=True,
    min_uptime=95.0
)

client = SearXNGClient(config)
```

## Advanced Usage

### Instance Management

```python
# Update instances list
client.update_instances(force=True)

# Get best instances
best_instances = client.get_best_instances(
    limit=10,
    sort_by="uptime",
    min_uptime=95.0,
    exclude_countries=["CN", "RU"]
)

# Set specific instance
client.set_instance(best_instances[0])

# Test an instance
is_working = client.test_instance(instance, "test query")
```

### Search Configuration

```python
from pyserxng.models import SearchCategory, SafeSearchLevel, TimeRange

config = SearchConfig(
    categories=[SearchCategory.GENERAL, SearchCategory.SCIENCE],
    engines=["google", "bing", "duckduckgo"],
    language="en",
    page=1,
    time_range=TimeRange.MONTH,
    safe_search=SafeSearchLevel.STRICT,
    timeout=30
)

results = client.search("quantum computing", config)
```

### Export Results

```python
from pyserxng.utils import export_search_results

# Export to different formats
export_search_results(results.results, "results.json", "json")
export_search_results(results.results, "results.csv", "csv")
export_search_results(results.results, "results.txt", "txt")
```

### Statistics and Monitoring

```python
# Get client statistics
stats = client.get_stats()
print(f"Total instances: {stats['total_instances']}")
print(f"Working instances: {stats['working_instances']}")

# Instance-specific statistics
for url, instance_stats in stats['instance_stats'].items():
    print(f"{url}: {instance_stats.success_rate:.1f}% success rate")
```

## API Reference

### SearXNGClient

Main client class for interacting with SearXNG instances.

#### Methods

- `search(query, config=None, instance=None)` - Perform a search
- `search_images(query, config=None)` - Search for images
- `search_videos(query, config=None)` - Search for videos  
- `search_news(query, config=None)` - Search for news
- `get_suggestions(query)` - Get search suggestions
- `update_instances(force=False)` - Update instances list
- `get_instances(**filter_kwargs)` - Get filtered instances
- `get_best_instances(limit=10, **kwargs)` - Get best instances
- `set_instance(instance)` - Set specific instance
- `test_instance(instance, test_query="test")` - Test instance
- `get_stats()` - Get client statistics
- `close()` - Close client and cleanup

### Models

#### SearchResult
- `title: str` - Result title
- `url: HttpUrl` - Result URL
- `content: str` - Result description
- `engine: Optional[str]` - Search engine used
- `thumbnail: Optional[HttpUrl]` - Thumbnail image URL

#### InstanceInfo
- `url: HttpUrl` - Instance URL
- `status: InstanceStatus` - Instance status
- `uptime: Optional[float]` - Uptime percentage
- `country: Optional[str]` - Country code
- `tls_grade: Optional[str]` - TLS security grade

#### SearchConfig
- `categories: List[SearchCategory]` - Search categories
- `language: str` - Search language
- `page: int` - Page number
- `timeout: int` - Request timeout
- `safe_search: SafeSearchLevel` - Safe search level

## Examples

See the `examples/` directory for complete usage examples:

- `basic_usage.py` - Basic search functionality
- `advanced_config.py` - Advanced configuration options
- `batch_search.py` - Batch searching multiple queries
- `custom_instance.py` - Using custom instances

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone <repository-url>
cd searxng-client

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_client.py
```

### Code Quality

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for your changes
5. Ensure all tests pass (`pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [SearXNG](https://github.com/searxng/searxng) - The awesome metasearch engine
- [searx.space](https://searx.space) - Public instance directory
- All contributors and maintainers of public SearXNG instances

## Troubleshooting

### Common Issues

**No instances available:**
- Run `client.update_instances(force=True)` to refresh the instance list
- Check your internet connection
- Verify the instances API is accessible

**Rate limiting errors:**
- Increase `request_delay` in configuration
- Use fewer concurrent requests
- Try different instances

**Timeout errors:**
- Increase `default_timeout` in configuration
- Check instance availability
- Use instances geographically closer to you

**Search returns no results:**
- Try different search terms
- Check if the instance supports your search category
- Verify the instance is working with `test_instance()`

### Debug Mode

Enable debug logging to troubleshoot issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or set in configuration
config = ClientConfig(log_level="DEBUG")
```