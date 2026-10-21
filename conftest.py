"""
conftest.py - Pytest configuration and shared fixtures.
Makes the project root findable by pytest for the 'src' package.
"""
import sys
import os

# Add project root to path so 'src.*' imports work when running pytest from project root
sys.path.insert(0, os.path.dirname(__file__))
