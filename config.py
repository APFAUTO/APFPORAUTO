"""
Configuration settings for POR Upload Application.
"""

import os
from typing import Set

# Application Settings
APP_NAME = "POR Upload System"
APP_VERSION = "2.0.0"
DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'

# File Upload Settings
UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS: Set[str] = {'xlsx', 'xls'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

# Database Settings
DATABASE_URL = os.environ.get('DATABASE_URL', "sqlite:///por.db")

# Pagination Settings
RECORDS_PER_PAGE = 10

# PO Counter Settings
STARTING_PO = 1000
PO_COUNTER_PATH = "po_counter.txt"

# Security Settings
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Logging Settings
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Server Settings
HOST = os.environ.get('HOST', '0.0.0.0')
PORT = int(os.environ.get('PORT', 5000))

# Development Settings
RELOAD_ON_CHANGE = DEBUG 