#!/usr/bin/env python3
"""
SDK Validation Demo Package

This is a sample package structure that demonstrates how to organize
a Python package for successful SDK validation.
"""

import tempfile
from pathlib import Path


def create_demo_package(output_dir: str = None) -> str:
    """
    Create a demonstration package with proper structure for SDK validation.

    Args:
        output_dir: Directory to create the package in. If None, uses temp directory.

    Returns:
        Path to the created package directory.
    """
    if output_dir is None:
        output_dir = tempfile.mkdtemp()

    package_dir = Path(output_dir) / "awesome-sdk-demo"
    package_dir.mkdir(exist_ok=True)

    # Create package structure
    _create_readme(package_dir)
    _create_license(package_dir)
    _create_setup_py(package_dir)
    _create_pyproject_toml(package_dir)
    _create_requirements(package_dir)
    _create_source_code(package_dir)
    _create_tests(package_dir)
    _create_documentation(package_dir)
    _create_ci_config(package_dir)
    _create_build_config(package_dir)
    _create_changelog(package_dir)
    _create_security_config(package_dir)

    print(f"✅ Demo package created at: {package_dir}")
    return str(package_dir)


def _create_readme(package_dir: Path):
    """Create comprehensive README.md."""
    readme_content = """# Awesome SDK Demo

[![CI](https://github.com/example/awesome-sdk-demo/workflows/CI/badge.svg)](https://github.com/example/awesome-sdk-demo/actions)
[![PyPI version](https://badge.fury.io/py/awesome-sdk-demo.svg)](https://badge.fury.io/py/awesome-sdk-demo)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

A demonstration SDK package showing best practices for package structure, validation, and publishing.

## Features

- 🚀 Clean, well-structured API
- 📚 Comprehensive documentation
- ✅ Full test coverage
- 🔒 Security-first design
- 🏗️ CI/CD ready
- 📦 Easy installation

## Installation

```bash
pip install awesome-sdk-demo
```

## Quick Start

```python
from awesome_sdk_demo import AwesomeClient

# Initialize the client
client = AwesomeClient(api_key="your-api-key")

# Make a request
result = client.get_data(query="example")
print(result)
```

## Documentation

Full documentation is available at [https://awesome-sdk-demo.readthedocs.io](https://awesome-sdk-demo.readthedocs.io)

## Development

### Setup

```bash
git clone https://github.com/example/awesome-sdk-demo.git
cd awesome-sdk-demo
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Building Documentation

```bash
cd docs
make html
```

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a list of changes and version history.

## Support

- 📧 Email: support@example.com
- 🐛 Issues: [GitHub Issues](https://github.com/example/awesome-sdk-demo/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/example/awesome-sdk-demo/discussions)
"""
    (package_dir / "README.md").write_text(readme_content, encoding="utf-8")


def _create_license(package_dir: Path):
    """Create MIT License file."""
    license_content = """MIT License

Copyright (c) 2024 Awesome SDK Demo

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
    (package_dir / "LICENSE").write_text(license_content, encoding="utf-8")


def _create_setup_py(package_dir: Path):
    """Create setup.py for backward compatibility."""
    setup_content = '''#!/usr/bin/env python3
"""Setup script for awesome-sdk-demo package."""

from setuptools import setup, find_packages
import os

# Read README for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="awesome-sdk-demo",
    version="1.2.3",
    author="Demo Developer",
    author_email="developer@example.com",
    description="A demonstration SDK package showing best practices",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/example/awesome-sdk-demo",
    project_urls={
        "Bug Tracker": "https://github.com/example/awesome-sdk-demo/issues",
        "Documentation": "https://awesome-sdk-demo.readthedocs.io",
        "Source Code": "https://github.com/example/awesome-sdk-demo",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "isort>=5.10.0",
            "flake8>=5.0.0",
            "mypy>=0.991",
            "pre-commit>=2.20.0",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.0.0",
            "myst-parser>=0.18.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "awesome-demo=awesome_sdk_demo.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
'''
    (package_dir / "setup.py").write_text(setup_content)


def _create_pyproject_toml(package_dir: Path):
    """Create modern pyproject.toml configuration."""
    pyproject_content = """[build-system]
requires = ["setuptools>=65.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "awesome-sdk-demo"
version = "1.2.3"
authors = [
    {name = "Demo Developer", email = "developer@example.com"},
]
description = "A demonstration SDK package showing best practices"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.8"
classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Internet :: WWW/HTTP",
    "Topic :: Utilities",
]
keywords = ["sdk", "api", "demo", "example"]
dependencies = [
    "requests>=2.28.0",
    "pydantic>=1.10.0",
    "typing-extensions>=4.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "black>=22.0.0",
    "isort>=5.10.0",
    "flake8>=5.0.0",
    "mypy>=0.991",
    "pre-commit>=2.20.0",
]
docs = [
    "sphinx>=5.0.0",
    "sphinx-rtd-theme>=1.0.0",
    "myst-parser>=0.18.0",
]

[project.urls]
Homepage = "https://github.com/example/awesome-sdk-demo"
Documentation = "https://awesome-sdk-demo.readthedocs.io"
Repository = "https://github.com/example/awesome-sdk-demo.git"
"Bug Tracker" = "https://github.com/example/awesome-sdk-demo/issues"
Changelog = "https://github.com/example/awesome-sdk-demo/blob/main/CHANGELOG.md"

[project.scripts]
awesome-demo = "awesome_sdk_demo.cli:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
awesome_sdk_demo = ["py.typed", "*.json", "*.yaml"]

[tool.black]
line-length = 88
target-version = ['py38']
include = '\\.pyi?$'
extend-exclude = '''
/(
  # directories
  \\.eggs
  | \\.git
  | \\.hg
  | \\.mypy_cache
  | \\.tox
  | \\.venv
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
known_first_party = ["awesome_sdk_demo"]

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false

[tool.pytest.ini_options]
minversion = "7.0"
addopts = "-ra -q --strict-markers --strict-config"
testpaths = ["tests"]
filterwarnings = [
    "error",
    "ignore::UserWarning",
    "ignore::DeprecationWarning",
]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
]

[tool.coverage.run]
source = ["src"]
omit = [
    "*/tests/*",
    "*/test_*",
    "setup.py",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if self.debug:",
    "if settings.DEBUG",
    "raise AssertionError",
    "raise NotImplementedError",
    "if 0:",
    "if __name__ == .__main__.:",
    "class .*\\bProtocol\\):",
    "@(abc\\.)?abstractmethod",
]
"""
    (package_dir / "pyproject.toml").write_text(pyproject_content)


def _create_requirements(package_dir: Path):
    """Create requirements files."""
    # Main requirements
    requirements_content = """requests>=2.28.0,<3.0.0
pydantic>=1.10.0,<2.0.0
typing-extensions>=4.0.0
"""
    (package_dir / "requirements.txt").write_text(requirements_content)

    # Development requirements
    dev_requirements_content = """# Development dependencies
pytest>=7.0.0
pytest-cov>=4.0.0
pytest-mock>=3.10.0
black>=22.0.0
isort>=5.10.0
flake8>=5.0.0
mypy>=0.991
pre-commit>=2.20.0
tox>=4.0.0

# Documentation
sphinx>=5.0.0
sphinx-rtd-theme>=1.0.0
myst-parser>=0.18.0

# Security scanning
bandit>=1.7.4
safety>=2.3.0
"""
    (package_dir / "requirements-dev.txt").write_text(dev_requirements_content)


def _create_source_code(package_dir: Path):
    """Create source code structure."""
    src_dir = package_dir / "src" / "awesome_sdk_demo"
    src_dir.mkdir(parents=True)

    # __init__.py
    init_content = '''"""Awesome SDK Demo - A demonstration SDK package.

This package showcases best practices for SDK development, including:
- Clean API design
- Comprehensive error handling
- Type hints and validation
- Security considerations
- Testing and documentation
"""

__version__ = "1.2.3"
__author__ = "Demo Developer"
__email__ = "developer@example.com"

from .client import AwesomeClient
from .models import APIResponse, ErrorResponse
from .exceptions import AwesomeSDKError, AuthenticationError, RateLimitError

__all__ = [
    "AwesomeClient",
    "APIResponse",
    "ErrorResponse",
    "AwesomeSDKError",
    "AuthenticationError",
    "RateLimitError",
]
'''
    (src_dir / "__init__.py").write_text(init_content)

    # Type marker
    (src_dir / "py.typed").write_text("")

    # Main client
    client_content = '''"""Main client for Awesome SDK Demo."""

import os
from typing import Dict, Any, Optional, Union
import requests
from pydantic import BaseModel, validator

from .models import APIResponse, ErrorResponse
from .exceptions import AwesomeSDKError, AuthenticationError, RateLimitError


class AwesomeClient:
    """Main client for interacting with the Awesome API.

    This client provides a simple interface for making API requests
    with proper error handling, authentication, and response validation.

    Example:
        >>> client = AwesomeClient(api_key="your-key")
        >>> response = client.get_data(query="example")
        >>> print(response.data)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.awesome-demo.com/v1",
        timeout: int = 30,
        retries: int = 3
    ):
        """Initialize the Awesome API client.

        Args:
            api_key: API key for authentication. If None, will look for
                    AWESOME_API_KEY environment variable.
            base_url: Base URL for the API endpoints.
            timeout: Request timeout in seconds.
            retries: Number of retry attempts for failed requests.

        Raises:
            AuthenticationError: If no API key is provided.
        """
        self.api_key = api_key or os.getenv("AWESOME_API_KEY")
        if not self.api_key:
            raise AuthenticationError("API key is required")

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.retries = retries

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": f"awesome-sdk-demo/1.2.3",
            "Content-Type": "application/json"
        })

    def get_data(self, query: str, limit: int = 10) -> APIResponse:
        """Retrieve data based on query.

        Args:
            query: Search query string.
            limit: Maximum number of results to return.

        Returns:
            APIResponse containing the query results.

        Raises:
            AwesomeSDKError: If the API request fails.
            RateLimitError: If rate limit is exceeded.
        """
        params = {"q": query, "limit": limit}
        return self._make_request("GET", "/search", params=params)

    def create_resource(self, data: Dict[str, Any]) -> APIResponse:
        """Create a new resource.

        Args:
            data: Resource data to create.

        Returns:
            APIResponse containing the created resource.
        """
        return self._make_request("POST", "/resources", json=data)

    def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> APIResponse:
        """Make an HTTP request to the API.

        Args:
            method: HTTP method (GET, POST, etc.).
            endpoint: API endpoint path.
            **kwargs: Additional arguments for requests.

        Returns:
            Parsed API response.

        Raises:
            AwesomeSDKError: For various API errors.
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=self.timeout,
                **kwargs
            )

            if response.status_code == 401:
                raise AuthenticationError("Invalid API key")
            elif response.status_code == 429:
                raise RateLimitError("Rate limit exceeded")
            elif not response.ok:
                error_data = response.json() if response.content else {}
                raise AwesomeSDKError(
                    f"API request failed: {response.status_code}",
                    status_code=response.status_code,
                    response_data=error_data
                )

            return APIResponse.parse_obj(response.json())

        except requests.RequestException as e:
            raise AwesomeSDKError(f"Request failed: {e}") from e
'''
    (src_dir / "client.py").write_text(client_content)

    # Models
    models_content = '''"""Data models for Awesome SDK Demo."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class APIResponse(BaseModel):
    """Standard API response model."""

    success: bool = Field(description="Whether the request was successful")
    data: Any = Field(description="Response data")
    message: Optional[str] = Field(None, description="Optional message")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    class Config:
        """Pydantic config."""
        extra = "forbid"


class ErrorResponse(BaseModel):
    """Error response model."""

    success: bool = Field(False, description="Always False for errors")
    error: str = Field(description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")

    class Config:
        """Pydantic config."""
        extra = "forbid"


class SearchResult(BaseModel):
    """Individual search result."""

    id: str = Field(description="Unique identifier")
    title: str = Field(description="Result title")
    description: Optional[str] = Field(None, description="Result description")
    score: float = Field(description="Relevance score", ge=0.0, le=1.0)
    url: Optional[str] = Field(None, description="Result URL")

    class Config:
        """Pydantic config."""
        extra = "forbid"


class SearchResponse(APIResponse):
    """Search-specific response model."""

    data: List[SearchResult] = Field(description="Search results")
    total: int = Field(description="Total number of results", ge=0)
    page: int = Field(description="Current page number", ge=1)
    per_page: int = Field(description="Results per page", ge=1)

    class Config:
        """Pydantic config."""
        extra = "forbid"
'''
    (src_dir / "models.py").write_text(models_content)

    # Exceptions
    exceptions_content = '''"""Custom exceptions for Awesome SDK Demo."""


class AwesomeSDKError(Exception):
    """Base exception for all SDK errors."""

    def __init__(
        self,
        message: str,
        status_code: int = None,
        response_data: dict = None
    ):
        """Initialize the exception.

        Args:
            message: Error message.
            status_code: HTTP status code if applicable.
            response_data: Response data from the API.
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_data = response_data or {}


class AuthenticationError(AwesomeSDKError):
    """Exception raised for authentication errors."""
    pass


class RateLimitError(AwesomeSDKError):
    """Exception raised when rate limit is exceeded."""
    pass


class ValidationError(AwesomeSDKError):
    """Exception raised for validation errors."""
    pass


class NotFoundError(AwesomeSDKError):
    """Exception raised when a resource is not found."""
    pass
'''
    (src_dir / "exceptions.py").write_text(exceptions_content)

    # CLI module
    cli_content = '''"""Command-line interface for Awesome SDK Demo."""

import argparse
import json
import sys
from typing import Optional

from . import AwesomeClient
from .exceptions import AwesomeSDKError


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="awesome-demo",
        description="Awesome SDK Demo CLI"
    )

    parser.add_argument(
        "--api-key",
        help="API key for authentication"
    )
    parser.add_argument(
        "--base-url",
        default="https://api.awesome-demo.com/v1",
        help="Base URL for API requests"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search for data")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum results to return"
    )

    # Version command
    version_parser = subparsers.add_parser("version", help="Show version")

    args = parser.parse_args()

    if args.command == "version":
        from . import __version__
        print(f"awesome-sdk-demo {__version__}")
        return 0

    if not args.command:
        parser.print_help()
        return 1

    try:
        client = AwesomeClient(
            api_key=args.api_key,
            base_url=args.base_url
        )

        if args.command == "search":
            response = client.get_data(args.query, limit=args.limit)
            print(json.dumps(response.dict(), indent=2))

        return 0

    except AwesomeSDKError as e:
        print(f"Error: {e.message}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
'''
    (src_dir / "cli.py").write_text(cli_content)


def _create_tests(package_dir: Path):
    """Create comprehensive test suite."""
    tests_dir = package_dir / "tests"
    tests_dir.mkdir()

    # Test __init__.py
    (tests_dir / "__init__.py").write_text("")

    # Conftest.py for shared fixtures
    conftest_content = '''"""Shared test fixtures and configuration."""

import pytest
from unittest.mock import Mock, patch
import requests
from awesome_sdk_demo import AwesomeClient


@pytest.fixture
def mock_response():
    """Mock requests response."""
    response = Mock()
    response.ok = True
    response.status_code = 200
    response.json.return_value = {
        "success": True,
        "data": {"test": "data"},
        "message": "Success"
    }
    return response


@pytest.fixture
def client():
    """Create test client."""
    with patch.dict("os.environ", {"AWESOME_API_KEY": "test-key"}):
        return AwesomeClient()


@pytest.fixture
def client_with_key():
    """Create test client with explicit API key."""
    return AwesomeClient(api_key="test-api-key")
'''
    (tests_dir / "conftest.py").write_text(conftest_content)

    # Test client
    test_client_content = '''"""Tests for the main client."""

import pytest
from unittest.mock import patch, Mock
import requests
from awesome_sdk_demo import AwesomeClient
from awesome_sdk_demo.exceptions import (
    AwesomeSDKError, AuthenticationError, RateLimitError
)


class TestAwesomeClient:
    """Test cases for AwesomeClient."""

    def test_init_with_api_key(self):
        """Test client initialization with API key."""
        client = AwesomeClient(api_key="test-key")
        assert client.api_key == "test-key"
        assert client.base_url == "https://api.awesome-demo.com/v1"
        assert client.timeout == 30
        assert client.retries == 3

    def test_init_without_api_key(self):
        """Test client initialization without API key raises error."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(AuthenticationError):
                AwesomeClient()

    def test_init_with_env_api_key(self):
        """Test client initialization with environment API key."""
        with patch.dict("os.environ", {"AWESOME_API_KEY": "env-key"}):
            client = AwesomeClient()
            assert client.api_key == "env-key"

    def test_init_custom_params(self):
        """Test client initialization with custom parameters."""
        client = AwesomeClient(
            api_key="test-key",
            base_url="https://custom.api.com",
            timeout=60,
            retries=5
        )
        assert client.base_url == "https://custom.api.com"
        assert client.timeout == 60
        assert client.retries == 5

    @patch('requests.Session.request')
    def test_get_data_success(self, mock_request, client):
        """Test successful get_data request."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "data": [{"id": "1", "title": "Test"}],
            "metadata": {"total": 1}
        }
        mock_request.return_value = mock_response

        result = client.get_data("test query")

        assert result.success is True
        assert result.data == [{"id": "1", "title": "Test"}]
        mock_request.assert_called_once()

    @patch('requests.Session.request')
    def test_get_data_with_limit(self, mock_request, client):
        """Test get_data with custom limit."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "data": [],
            "metadata": {}
        }
        mock_request.return_value = mock_response

        client.get_data("test", limit=5)

        args, kwargs = mock_request.call_args
        assert kwargs['params']['limit'] == 5

    @patch('requests.Session.request')
    def test_create_resource_success(self, mock_request, client):
        """Test successful create_resource request."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "success": True,
            "data": {"id": "new-resource", "name": "Test Resource"}
        }
        mock_request.return_value = mock_response

        data = {"name": "Test Resource", "type": "example"}
        result = client.create_resource(data)

        assert result.success is True
        assert result.data["id"] == "new-resource"

        args, kwargs = mock_request.call_args
        assert kwargs['json'] == data

    @patch('requests.Session.request')
    def test_authentication_error(self, mock_request, client):
        """Test authentication error handling."""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 401
        mock_request.return_value = mock_response

        with pytest.raises(AuthenticationError):
            client.get_data("test")

    @patch('requests.Session.request')
    def test_rate_limit_error(self, mock_request, client):
        """Test rate limit error handling."""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 429
        mock_request.return_value = mock_response

        with pytest.raises(RateLimitError):
            client.get_data("test")

    @patch('requests.Session.request')
    def test_general_api_error(self, mock_request, client):
        """Test general API error handling."""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_response.content = b'{"error": "Internal server error"}'
        mock_response.json.return_value = {"error": "Internal server error"}
        mock_request.return_value = mock_response

        with pytest.raises(AwesomeSDKError) as exc_info:
            client.get_data("test")

        assert "500" in str(exc_info.value)
        assert exc_info.value.status_code == 500

    @patch('requests.Session.request')
    def test_request_exception(self, mock_request, client):
        """Test handling of requests exceptions."""
        mock_request.side_effect = requests.RequestException("Network error")

        with pytest.raises(AwesomeSDKError) as exc_info:
            client.get_data("test")

        assert "Network error" in str(exc_info.value)

    def test_session_headers(self, client):
        """Test that session headers are set correctly."""
        headers = client.session.headers

        assert "Authorization" in headers
        assert headers["Authorization"] == f"Bearer {client.api_key}"
        assert "User-Agent" in headers
        assert "awesome-sdk-demo" in headers["User-Agent"]
        assert headers["Content-Type"] == "application/json"
'''
    (tests_dir / "test_client.py").write_text(test_client_content)

    # Test models
    test_models_content = '''"""Tests for data models."""

import pytest
from pydantic import ValidationError
from awesome_sdk_demo.models import APIResponse, ErrorResponse, SearchResult


class TestAPIResponse:
    """Test cases for APIResponse model."""

    def test_valid_response(self):
        """Test creating valid API response."""
        data = {
            "success": True,
            "data": {"key": "value"},
            "message": "Success"
        }
        response = APIResponse(**data)

        assert response.success is True
        assert response.data == {"key": "value"}
        assert response.message == "Success"
        assert response.metadata is None

    def test_minimal_response(self):
        """Test creating minimal API response."""
        data = {"success": True, "data": None}
        response = APIResponse(**data)

        assert response.success is True
        assert response.data is None
        assert response.message is None

    def test_invalid_extra_field(self):
        """Test that extra fields are forbidden."""
        data = {
            "success": True,
            "data": {},
            "extra_field": "not allowed"
        }

        with pytest.raises(ValidationError):
            APIResponse(**data)


class TestErrorResponse:
    """Test cases for ErrorResponse model."""

    def test_valid_error_response(self):
        """Test creating valid error response."""
        data = {
            "error": "Something went wrong",
            "error_code": "ERR_001",
            "details": {"field": "error details"}
        }
        response = ErrorResponse(**data)

        assert response.success is False  # Default value
        assert response.error == "Something went wrong"
        assert response.error_code == "ERR_001"
        assert response.details == {"field": "error details"}

    def test_minimal_error_response(self):
        """Test creating minimal error response."""
        data = {"error": "Error message"}
        response = ErrorResponse(**data)

        assert response.success is False
        assert response.error == "Error message"
        assert response.error_code is None
        assert response.details is None


class TestSearchResult:
    """Test cases for SearchResult model."""

    def test_valid_search_result(self):
        """Test creating valid search result."""
        data = {
            "id": "result-1",
            "title": "Test Result",
            "description": "A test search result",
            "score": 0.95,
            "url": "https://example.com/result"
        }
        result = SearchResult(**data)

        assert result.id == "result-1"
        assert result.title == "Test Result"
        assert result.description == "A test search result"
        assert result.score == 0.95
        assert result.url == "https://example.com/result"

    def test_minimal_search_result(self):
        """Test creating minimal search result."""
        data = {
            "id": "result-1",
            "title": "Test Result",
            "score": 0.5
        }
        result = SearchResult(**data)

        assert result.id == "result-1"
        assert result.title == "Test Result"
        assert result.score == 0.5
        assert result.description is None
        assert result.url is None

    def test_invalid_score_range(self):
        """Test that score must be between 0 and 1."""
        # Score too high
        with pytest.raises(ValidationError):
            SearchResult(
                id="test",
                title="Test",
                score=1.5
            )

        # Score too low
        with pytest.raises(ValidationError):
            SearchResult(
                id="test",
                title="Test",
                score=-0.1
            )
'''
    (tests_dir / "test_models.py").write_text(test_models_content)

    # Test CLI
    test_cli_content = '''"""Tests for CLI functionality."""

import pytest
from unittest.mock import patch, Mock
from awesome_sdk_demo.cli import main
from awesome_sdk_demo.exceptions import AwesomeSDKError


class TestCLI:
    """Test cases for CLI functionality."""

    def test_version_command(self, capsys):
        """Test version command."""
        with patch('sys.argv', ['awesome-demo', 'version']):
            exit_code = main()

        captured = capsys.readouterr()
        assert exit_code == 0
        assert "awesome-sdk-demo 1.2.3" in captured.out

    def test_no_command_shows_help(self, capsys):
        """Test that no command shows help."""
        with patch('sys.argv', ['awesome-demo']):
            exit_code = main()

        captured = capsys.readouterr()
        assert exit_code == 1
        assert "usage:" in captured.out.lower()

    @patch('awesome_sdk_demo.cli.AwesomeClient')
    def test_search_command_success(self, mock_client_class, capsys):
        """Test successful search command."""
        # Mock client and response
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_response = Mock()
        mock_response.dict.return_value = {
            "success": True,
            "data": [{"id": "1", "title": "Test Result"}]
        }
        mock_client.get_data.return_value = mock_response

        test_args = [
            'awesome-demo',
            '--api-key', 'test-key',
            'search',
            'test query'
        ]

        with patch('sys.argv', test_args):
            exit_code = main()

        assert exit_code == 0
        mock_client.get_data.assert_called_once_with('test query', limit=10)

        captured = capsys.readouterr()
        assert '"success": true' in captured.out.lower()

    @patch('awesome_sdk_demo.cli.AwesomeClient')
    def test_search_command_with_limit(self, mock_client_class):
        """Test search command with custom limit."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_response = Mock()
        mock_response.dict.return_value = {"success": True, "data": []}
        mock_client.get_data.return_value = mock_response

        test_args = [
            'awesome-demo',
            '--api-key', 'test-key',
            'search',
            'test query',
            '--limit', '5'
        ]

        with patch('sys.argv', test_args):
            exit_code = main()

        assert exit_code == 0
        mock_client.get_data.assert_called_once_with('test query', limit=5)

    @patch('awesome_sdk_demo.cli.AwesomeClient')
    def test_search_command_api_error(self, mock_client_class, capsys):
        """Test search command with API error."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_client.get_data.side_effect = AwesomeSDKError("API Error")

        test_args = [
            'awesome-demo',
            '--api-key', 'test-key',
            'search',
            'test query'
        ]

        with patch('sys.argv', test_args):
            exit_code = main()

        assert exit_code == 1

        captured = capsys.readouterr()
        assert "Error: API Error" in captured.err

    @patch('awesome_sdk_demo.cli.AwesomeClient')
    def test_search_command_unexpected_error(self, mock_client_class, capsys):
        """Test search command with unexpected error."""
        mock_client_class.side_effect = Exception("Unexpected error")

        test_args = [
            'awesome-demo',
            '--api-key', 'test-key',
            'search',
            'test query'
        ]

        with patch('sys.argv', test_args):
            exit_code = main()

        assert exit_code == 1

        captured = capsys.readouterr()
        assert "Unexpected error:" in captured.err
'''
    (tests_dir / "test_cli.py").write_text(test_cli_content)


def _create_documentation(package_dir: Path):
    """Create documentation structure."""
    docs_dir = package_dir / "docs"
    docs_dir.mkdir()

    # Sphinx configuration
    conf_py_content = '''"""Sphinx configuration for Awesome SDK Demo."""

import os
import sys

# Add the source directory to the path
sys.path.insert(0, os.path.abspath('../src'))

# Project information
project = 'Awesome SDK Demo'
copyright = '2024, Demo Developer'
author = 'Demo Developer'
version = '1.2.3'
release = '1.2.3'

# Extensions
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'myst_parser',
]

# Templates path
templates_path = ['_templates']

# Source file extensions
source_suffix = {
    '.rst': None,
    '.md': None,
}

# Master document
master_doc = 'index'

# Exclude patterns
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# HTML theme
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# Intersphinx mapping
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'requests': ('https://docs.python-requests.org/en/latest/', None),
}

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
'''
    (docs_dir / "conf.py").write_text(conf_py_content)

    # Main index
    index_md_content = """# Awesome SDK Demo Documentation

Welcome to the Awesome SDK Demo documentation!

## Overview

Awesome SDK Demo is a demonstration package that showcases best practices for:

- Clean API design
- Comprehensive error handling
- Type hints and validation
- Security considerations
- Testing and documentation

## Quick Start

```python
from awesome_sdk_demo import AwesomeClient

# Initialize client
client = AwesomeClient(api_key="your-api-key")

# Make a request
response = client.get_data("search query")
print(response.data)
```

## Contents

```{toctree}
:maxdepth: 2

installation
quickstart
api_reference
examples
contributing
changelog
```

## Indices and tables

* {ref}`genindex`
* {ref}`modindex`
* {ref}`search`
"""
    (docs_dir / "index.md").write_text(index_md_content)

    # API Reference
    api_ref_content = """# API Reference

## Client

```{eval-rst}
.. autoclass:: awesome_sdk_demo.AwesomeClient
   :members:
   :undoc-members:
   :show-inheritance:
```

## Models

```{eval-rst}
.. automodule:: awesome_sdk_demo.models
   :members:
   :undoc-members:
   :show-inheritance:
```

## Exceptions

```{eval-rst}
.. automodule:: awesome_sdk_demo.exceptions
   :members:
   :undoc-members:
   :show-inheritance:
```
"""
    (docs_dir / "api_reference.md").write_text(api_ref_content)

    # Create Makefile for docs
    makefile_content = """# Makefile for Sphinx documentation

SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build

.PHONY: help Makefile

help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

clean:
	rm -rf $(BUILDDIR)/*

livehtml:
	sphinx-autobuild "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
"""
    (docs_dir / "Makefile").write_text(makefile_content)


def _create_ci_config(package_dir: Path):
    """Create CI/CD configuration."""
    github_dir = package_dir / ".github" / "workflows"
    github_dir.mkdir(parents=True)

    ci_workflow_content = """name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.8', '3.9', '3.10', '3.11']

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"

    - name: Lint with flake8
      run: |
        flake8 src/ tests/

    - name: Check formatting with black
      run: |
        black --check src/ tests/

    - name: Check import sorting with isort
      run: |
        isort --check-only src/ tests/

    - name: Type checking with mypy
      run: |
        mypy src/

    - name: Run tests
      run: |
        pytest --cov=awesome_sdk_demo --cov-report=xml

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

  security:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install bandit safety

    - name: Run Bandit security scan
      run: |
        bandit -r src/

    - name: Run Safety dependency check
      run: |
        safety check
"""
    (github_dir / "ci.yml").write_text(ci_workflow_content)


def _create_build_config(package_dir: Path):
    """Create build configuration files."""
    # Makefile
    makefile_content = """.PHONY: help clean test install build upload docs lint format type-check security

help:
	@echo "Available targets:"
	@echo "  install     Install package in development mode"
	@echo "  test        Run test suite"
	@echo "  lint        Run linting checks"
	@echo "  format      Format code with black and isort"
	@echo "  type-check  Run type checking with mypy"
	@echo "  security    Run security scans"
	@echo "  build       Build package distributions"
	@echo "  upload      Upload package to PyPI"
	@echo "  docs        Build documentation"
	@echo "  clean       Clean build artifacts"

install:
	pip install -e ".[dev]"

test:
	pytest --cov=awesome_sdk_demo --cov-report=html --cov-report=term

lint:
	flake8 src/ tests/
	black --check src/ tests/
	isort --check-only src/ tests/

format:
	black src/ tests/
	isort src/ tests/

type-check:
	mypy src/

security:
	bandit -r src/
	safety check

build: clean
	python -m build

upload: build
	python -m twine upload dist/*

docs:
	cd docs && make html

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
"""
    (package_dir / "Makefile").write_text(makefile_content)

    # tox.ini for multi-environment testing
    tox_ini_content = """[tox]
envlist = py38,py39,py310,py311,lint,security,docs
isolated_build = true

[testenv]
deps =
    pytest
    pytest-cov
    pytest-mock
commands = pytest {posargs}

[testenv:lint]
deps =
    flake8
    black
    isort
    mypy
commands =
    flake8 src/ tests/
    black --check src/ tests/
    isort --check-only src/ tests/
    mypy src/

[testenv:security]
deps =
    bandit
    safety
commands =
    bandit -r src/
    safety check

[testenv:docs]
changedir = docs
deps =
    sphinx
    sphinx-rtd-theme
    myst-parser
commands = sphinx-build -W -b html . _build/html
"""
    (package_dir / "tox.ini").write_text(tox_ini_content)


def _create_changelog(package_dir: Path):
    """Create changelog file."""
    changelog_content = """# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure
- SDK validation pipeline integration

## [1.2.3] - 2024-01-15

### Added
- Enhanced error handling for rate limiting
- Support for custom base URLs
- Comprehensive test coverage

### Changed
- Improved API response validation
- Updated documentation structure

### Fixed
- Authentication error handling
- Memory leak in session management

## [1.2.2] - 2024-01-10

### Added
- CLI interface for basic operations
- Type hints throughout codebase

### Fixed
- Issue with malformed JSON responses
- Timeout handling improvements

## [1.2.1] - 2024-01-05

### Fixed
- Critical bug in authentication flow
- Documentation formatting issues

## [1.2.0] - 2024-01-01

### Added
- Search functionality
- Resource creation endpoints
- Comprehensive error handling
- Full test suite

### Changed
- Migrated to pydantic for data validation
- Improved API design

## [1.1.0] - 2023-12-15

### Added
- Basic API client functionality
- Authentication support
- Initial documentation

## [1.0.0] - 2023-12-01

### Added
- Initial release
- Core client implementation
- Basic error handling
"""
    (package_dir / "CHANGELOG.md").write_text(changelog_content)


def _create_security_config(package_dir: Path):
    """Create security configuration files."""
    # .bandit config
    bandit_config = """[bandit]
exclude_dirs = ["tests", "docs", "build", "dist"]
skips = ["B101", "B601"]
"""
    (package_dir / ".bandit").write_text(bandit_config)

    # Security policy
    security_md_content = """# Security Policy

## Supported Versions

We actively support the following versions of Awesome SDK Demo:

| Version | Supported          |
| ------- | ------------------ |
| 1.2.x   | :white_check_mark: |
| 1.1.x   | :white_check_mark: |
| < 1.1   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in Awesome SDK Demo, please report it to us in a responsible manner:

### Private Disclosure Process

1. **Do not** create a public GitHub issue for security vulnerabilities
2. Email us directly at security@example.com
3. Include a detailed description of the vulnerability
4. Provide steps to reproduce the issue
5. Include any relevant proof-of-concept code

### What to Include

Please include the following information in your report:

- Description of the vulnerability
- Steps to reproduce
- Affected versions
- Potential impact
- Suggested mitigation (if any)

### Response Timeline

We are committed to responding to security reports promptly:

- **24 hours**: Initial acknowledgment of your report
- **72 hours**: Initial assessment and severity classification
- **7 days**: Detailed response with our planned timeline for fixes
- **30 days**: Resolution or status update

## Security Best Practices

When using Awesome SDK Demo:

### API Key Management

- Never hardcode API keys in your source code
- Use environment variables or secure configuration management
- Rotate API keys regularly
- Use different API keys for different environments

### Network Security

- Always use HTTPS endpoints
- Implement proper timeout settings
- Use connection pooling appropriately
- Monitor for unusual traffic patterns

### Data Handling

- Validate all input data
- Sanitize output when displaying to users
- Follow principle of least privilege
- Implement proper error handling without exposing sensitive information

## Security Updates

We will announce security updates through:

- GitHub Security Advisories
- Release notes
- Email notifications to registered users

## Contact

For security-related questions or concerns:

- Email: security@example.com
- PGP Key: [Public Key Link]

Thank you for helping keep Awesome SDK Demo secure!
"""
    (package_dir / "SECURITY.md").write_text(security_md_content)


def main():
    """CLI entry point for creating demo package."""
    import argparse

    parser = argparse.ArgumentParser(description="Create a demonstration SDK package structure")
    parser.add_argument(
        "--output-dir", help="Directory to create the package in (default: temp directory)"
    )
    parser.add_argument(
        "--validate", action="store_true", help="Run SDK validation on the created package"
    )

    args = parser.parse_args()

    # Create the demo package
    package_path = create_demo_package(args.output_dir)

    # Optionally run validation
    if args.validate:
        print("\n🔍 Running SDK validation on created package...")

        try:
            # Import and run the validator
            import sys
            from pathlib import Path

            # Add scripts directory to path
            scripts_dir = Path(__file__).parent.parent / "scripts"
            sys.path.insert(0, str(scripts_dir))

            from validate_sdk_publishing import SDKValidator

            validator = SDKValidator()
            report = validator.validate_all(package_path)

            print("\n📊 Validation Results:")
            print(f"Overall Status: {report.overall_status.upper()}")
            summary = report.get_summary()
            print(f"✅ Pass: {summary['pass']}")
            print(f"⚠️  Warning: {summary['warning']}")
            print(f"❌ Fail: {summary['fail']}")
            print(f"⏭️  Skip: {summary['skip']}")

            # Show any critical issues
            critical_issues = [
                r for r in report.results if r.severity == "critical" and r.status == "fail"
            ]
            if critical_issues:
                print("\n🚨 Critical Issues:")
                for issue in critical_issues:
                    print(f"   • {issue.name}: {issue.message}")

        except ImportError as e:
            print(f"⚠️  Could not run validation: {e}")
            print("Make sure the validation script is available.")

    print("\n🎉 Demo package structure created successfully!")
    print(f"📁 Location: {package_path}")
    print("\nNext steps:")
    print(f"  1. cd {package_path}")
    print("  2. pip install -e '.[dev]'")
    print("  3. pytest")
    print("  4. python scripts/validate_sdk_publishing.py .")


if __name__ == "__main__":
    main()
