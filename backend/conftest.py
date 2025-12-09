"""
Pytest configuration file.

This file ensures that imports work correctly when running tests.
It adds the backend directory to sys.path so that modules can be imported.
"""
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))


