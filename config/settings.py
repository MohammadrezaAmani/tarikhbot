import os
from pathlib import Path
from typing import Dict, List, Optional, Union
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base project directory
BASE_DIR = Path(__file__).parent.parent

# Bot settings
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Database settings
DB_URL = os.getenv(
    "DATABASE_URL", 
    f"sqlite://{BASE_DIR / 'db.sqlite3'}"
)

# Google API settings
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "")
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/gmail.send",
]

# Default user settings
DEFAULT_TIMEZONE = "UTC"
DEFAULT_LANGUAGE = "en"
AVAILABLE_LANGUAGES = ["en", "es", "fr", "de", "ru", "zh"]

# Application settings
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Scheduler settings
SCHEDULER_API_ENABLED = False
SCHEDULER_TIMEZONE = "UTC"
SCHEDULER_JOB_DEFAULTS = {
    "coalesce": False,
    "max_instances": 3,
}

# File storage
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"
MAX_UPLOAD_SIZE = 20 * 1024 * 1024  # 20MB

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-default-key-change-in-production")

# Chart settings
CHART_COLORS = {
    "primary": "#4A6FFF",
    "secondary": "#FF6B6B",
    "success": "#59CB74",
    "warning": "#FFBB54",
    "danger": "#FF5370",
    "info": "#2DCEFF",
    "light": "#F8F9FA",
    "dark": "#343A40",
}

# Currency settings
DEFAULT_CURRENCY = "USD"
SUPPORTED_CURRENCIES = ["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "INR", "CNY"]

# Export settings
PDF_LOGO_PATH = MEDIA_ROOT / "logo.png"
REPORT_TEMPLATES_DIR = BASE_DIR / "templates" / "reports"

# Environment-specific overrides
if os.getenv("ENVIRONMENT") == "production":
    DEBUG = False
    LOG_LEVEL = "WARNING"
    # Production-specific settings

# Create a unified settings object
SETTINGS = {
    "api_id": API_ID,
    "api_hash": API_HASH,
    "bot_token": BOT_TOKEN,
    "db_url": DB_URL,
    "google": {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "scopes": GOOGLE_SCOPES,
    },
    "user": {
        "default_timezone": DEFAULT_TIMEZONE,
        "default_language": DEFAULT_LANGUAGE,
        "available_languages": AVAILABLE_LANGUAGES,
    },
    "app": {
        "debug": DEBUG,
        "log_level": LOG_LEVEL,
        "secret_key": SECRET_KEY,
    },
    "scheduler": {
        "api_enabled": SCHEDULER_API_ENABLED,
        "timezone": SCHEDULER_TIMEZONE,
        "job_defaults": SCHEDULER_JOB_DEFAULTS,
    },
    "media": {
        "root": str(MEDIA_ROOT),
        "url": MEDIA_URL,
        "max_upload_size": MAX_UPLOAD_SIZE,
    },
    "chart": {
        "colors": CHART_COLORS,
    },
    "finance": {
        "default_currency": DEFAULT_CURRENCY,
        "supported_currencies": SUPPORTED_CURRENCIES,
    },
    "export": {
        "pdf_logo_path": str(PDF_LOGO_PATH),
        "report_templates_dir": str(REPORT_TEMPLATES_DIR),
    },
}