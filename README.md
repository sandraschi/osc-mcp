# OSCMCP - Open Source Content Management Platform MCP Server

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A FastMCP 2.10 compliant MCP server for managing Open Source Content Management Platforms through a standardized interface.

## Features

- FastMCP 2.10 compliant API
- Asynchronous architecture using FastAPI
- Plugin system for extending functionality
- Comprehensive test suite
- DXT packaging support
- Docker container support

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### From Source

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/oscmcp.git
   cd oscmcp
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. Install the package in development mode with all dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

## Usage

### Starting the Server

```bash
# Start the server with default settings
oscmcp

# Start on a specific host and port
oscmcp --host 127.0.0.1 --port 8080

# Enable development mode with auto-reload
oscmcp --reload
```

### API Documentation

Once the server is running, you can access the following endpoints:

- `GET /health` - Health check endpoint
- `POST /mcp/execute` - Execute MCP commands
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation (ReDoc)

## Development

### Setting Up Development Environment

1. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

2. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=oscmcp --cov-report=term-missing

# Run a specific test file
pytest tests/test_module.py
```

### Code Style

This project uses:
- [Black](https://github.com/psf/black) for code formatting
- [isort](https://github.com/timothycrosley/isort) for import sorting
- [Flake8](https://flake8.py.org/) for linting

To automatically format and check your code:

```bash
# Format code with Black
black src tests

# Sort imports with isort
isort src tests

# Run linter
flake8 src tests
```

## DXT Packaging

This project supports DXT packaging for easy distribution and deployment.

### Creating a DXT Package

```bash
# Build the package
python -m build

# The package will be created in the dist/ directory
```

### Installing from DXT Package

```bash
pip install dist/oscmcp-*.whl
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please read our [contributing guidelines](CONTRIBUTING.md) to get started.

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - The web framework used
- [uvicorn](https://www.uvicorn.org/) - ASGI server
- [pydantic](https://pydantic-docs.helpmanual.io/) - Data validation and settings management
