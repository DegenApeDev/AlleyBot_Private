"""
Test package initialization.
Loads .env so all tests have access to environment variables.
"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / '.env'
    load_dotenv(env_path)
except ImportError:
    pass
