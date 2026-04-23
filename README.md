# Codex Application Server

A robust Python library for building and interacting with codex-based application servers.

## Overview

The Codex Application Server provides a comprehensive framework for building scalable, production-ready applications with built-in support for:
- RESTful API endpoints
- Async and sync client implementations
- Error handling and retry mechanisms
- Notification registry system
- Generated API clients for versioned APIs

## Installation

```bash
pip install codex-app-server
```

Or install from source:

```bash
pip install -e .
```

## Quick Start

### Basic Usage

```python
from codex_app_server import Client

# Initialize client
client = Client(api_key="your-api-key")

# Make API calls
response = client.api.v2.get_endpoint()
print(response.data)
```

### Async Usage

```python
import asyncio
from codex_app_server import AsyncClient

async def main():
    async_client = AsyncClient(api_key="your-api-key")
    response = await async_client.api.v2.get_endpoint()
    print(response.data)

asyncio.run(main())
```

## Features

- **API Versioning**: Support for v2 API endpoints with generated clients
- **Robust Error Handling**: Comprehensive error classes and handling strategies
- **Retry Logic**: Built-in retry mechanisms for network resilience
- **Notification System**: Registry for handling various notification types
- **Type Safety**: Full type hints and py.typed marker for IDE support

## Directory Structure

```
codex_app_server/
├── __init__.py          # Package initialization
├── _inputs.py          # Input validation and processing
├── _run.py             # Core execution logic
├── api.py              # API interface definitions
├── async_client.py     # Async client implementation
├── client.py           # Sync client implementation
├── errors.py           # Custom error classes
├── models.py           # Data models and schemas
├── retry.py            # Retry strategy implementation
├── py.typed            # Type checking marker
└── generated/
    ├── __init__.py     # Generated code initialization
    ├── notification_registry.py  # Notification system
    └── v2_all.py       # v2 API endpoint definitions
```

## Development

### Setting up the development environment

```bash
# Clone the repository
git clone <repository-url>
cd codex-app-server

# Create virtual environment
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate

# Install in development mode
pip install -e .

# Install development dependencies
pip install -r requirements-dev.txt
```

### Running tests

```bash
pytest tests/
```

## Contributing

Contributions are welcome! Please see our [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

For questions or support, please open an issue on GitHub or contact the maintainers.