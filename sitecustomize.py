"""Test/Runtime path bootstrap.
Automatically ensures repository root is on sys.path so that 'tests.utils.metrics'
and peer packages can be imported without dynamic import hacks.

Python automatically imports sitecustomize if present on sys.path before running modules.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    # Prepend so local modules shadow any similarly named external ones
    sys.path.insert(0, str(ROOT))
