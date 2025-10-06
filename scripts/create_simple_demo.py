#!/usr/bin/env python3
"""
Simple SDK Validation Demo

Creates a basic package structure for testing SDK validation without Unicode issues.
"""

import tempfile
from pathlib import Path


def create_simple_demo_package(output_dir: str = None) -> str:
    """Create a simple demo package for SDK validation testing."""
    if output_dir is None:
        output_dir = tempfile.mkdtemp()

    package_dir = Path(output_dir) / "simple-sdk-demo"
    package_dir.mkdir(exist_ok=True)

    # README.md
    readme_content = """# Simple SDK Demo

A basic demonstration SDK package for validation testing.

## Features

- Clean API design
- Comprehensive testing
- Security best practices
- CI/CD ready

## Installation

```bash
pip install simple-sdk-demo
```

## Quick Start

```python
from simple_sdk_demo import SimpleClient

client = SimpleClient(api_key="your-key")
result = client.get_data("query")
print(result)
```

## Documentation

See the docs/ directory for full documentation.

## Contributing

We welcome contributions! Please see CONTRIBUTING.md for details.

## License

This project is licensed under the MIT License.
"""

    # Write files with explicit UTF-8 encoding
    with open(package_dir / "README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)

    # LICENSE
    license_content = """MIT License

Copyright (c) 2024 Simple SDK Demo

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

    with open(package_dir / "LICENSE", "w", encoding="utf-8") as f:
        f.write(license_content)

    # setup.py
    setup_content = """from setuptools import setup, find_packages

setup(
    name="simple-sdk-demo",
    version="1.0.0",
    author="Demo Developer",
    author_email="developer@example.com",
    description="A simple demonstration SDK package",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
"""

    with open(package_dir / "setup.py", "w", encoding="utf-8") as f:
        f.write(setup_content)

    # requirements.txt
    requirements_content = """requests>=2.28.0
typing-extensions>=4.0.0
"""

    with open(package_dir / "requirements.txt", "w", encoding="utf-8") as f:
        f.write(requirements_content)

    # Create source directory
    src_dir = package_dir / "src" / "simple_sdk_demo"
    src_dir.mkdir(parents=True)

    # __init__.py
    init_content = '''"""Simple SDK Demo package."""

__version__ = "1.0.0"

from .client import SimpleClient

__all__ = ["SimpleClient"]
'''

    with open(src_dir / "__init__.py", "w", encoding="utf-8") as f:
        f.write(init_content)

    # client.py
    client_content = '''"""Main client for Simple SDK Demo."""

import requests
from typing import Dict, Any, Optional


class SimpleClient:
    """Simple API client for demonstration."""

    def __init__(self, api_key: str, base_url: str = "https://api.example.com"):
        """Initialize the client.

        Args:
            api_key: API key for authentication
            base_url: Base URL for API requests
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })

    def get_data(self, query: str) -> Dict[str, Any]:
        """Get data based on query.

        Args:
            query: Search query

        Returns:
            API response data
        """
        response = self.session.get(
            f"{self.base_url}/search",
            params={"q": query}
        )
        response.raise_for_status()
        return response.json()

    def create_resource(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new resource.

        Args:
            data: Resource data

        Returns:
            Created resource data
        """
        response = self.session.post(
            f"{self.base_url}/resources",
            json=data
        )
        response.raise_for_status()
        return response.json()
'''

    with open(src_dir / "client.py", "w", encoding="utf-8") as f:
        f.write(client_content)

    # Create tests directory
    tests_dir = package_dir / "tests"
    tests_dir.mkdir()

    with open(tests_dir / "__init__.py", "w", encoding="utf-8") as f:
        f.write("")

    # test_client.py
    test_content = '''"""Tests for SimpleClient."""

import pytest
from unittest.mock import Mock, patch
from simple_sdk_demo import SimpleClient


class TestSimpleClient:
    """Test cases for SimpleClient."""

    def test_init(self):
        """Test client initialization."""
        client = SimpleClient("test-key")
        assert client.api_key == "test-key"
        assert client.base_url == "https://api.example.com"

    @patch('requests.Session.get')
    def test_get_data(self, mock_get):
        """Test get_data method."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": "test"}
        mock_get.return_value = mock_response

        client = SimpleClient("test-key")
        result = client.get_data("test query")

        assert result == {"data": "test"}
        mock_get.assert_called_once()

    @patch('requests.Session.post')
    def test_create_resource(self, mock_post):
        """Test create_resource method."""
        mock_response = Mock()
        mock_response.json.return_value = {"id": "123", "name": "test"}
        mock_post.return_value = mock_response

        client = SimpleClient("test-key")
        result = client.create_resource({"name": "test"})

        assert result == {"id": "123", "name": "test"}
        mock_post.assert_called_once()
'''

    with open(tests_dir / "test_client.py", "w", encoding="utf-8") as f:
        f.write(test_content)

    # Create CI workflow
    github_dir = package_dir / ".github" / "workflows"
    github_dir.mkdir(parents=True)

    ci_content = """name: CI

on:
  push:
    branches: [main]
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
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: |
        pip install -e .
        pip install pytest
    - name: Run tests
      run: pytest
"""

    with open(github_dir / "ci.yml", "w", encoding="utf-8") as f:
        f.write(ci_content)

    # Create Makefile
    makefile_content = """.PHONY: test install clean

test:
	pytest

install:
	pip install -e .

clean:
	rm -rf build dist *.egg-info
"""

    with open(package_dir / "Makefile", "w", encoding="utf-8") as f:
        f.write(makefile_content)

    print(f"✅ Simple demo package created at: {package_dir}")
    return str(package_dir)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create simple demo SDK package")
    parser.add_argument("--output-dir", help="Output directory")
    parser.add_argument("--validate", action="store_true", help="Run validation")

    args = parser.parse_args()

    package_path = create_simple_demo_package(args.output_dir)

    if args.validate:
        print("\n🔍 Running SDK validation...")

        try:
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

        except ImportError as e:
            print(f"⚠️  Could not run validation: {e}")

    print("\n🎉 Demo package created successfully!")
    print(f"📁 Location: {package_path}")
