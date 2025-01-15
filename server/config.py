"""Configuration settings for the BookChat server."""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Server configuration
PORT = int(os.getenv('PORT', 8000))
REPO_PATH = os.getenv('REPO_PATH', os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Feature flags
MESSAGE_VERIFICATION_ENABLED = os.getenv('MESSAGE_VERIFICATION', 'false').lower() == 'true'

# Static file configuration
STATIC_DIR = "static"
TEMPLATE_DIR = "templates"

# Storage configuration
DEFAULT_STORAGE_TYPE = 'git'
