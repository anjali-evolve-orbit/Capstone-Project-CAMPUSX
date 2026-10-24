"""
CAMPUSX — Discover People Behind the Work System
Application Configuration & Design System Constants
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env
load_dotenv(BASE_DIR / ".env")

# --- Branding & Identity ---
PROJECT_NAME = "CAMPUSX"
TAGLINE = "Discover People Behind the Work System"
SUPPORTING_TEXT = "Discover the people, research, ideas and connections behind the work happening across your campus."
APP_VERSION = "1.0.0"

# --- Database Configuration (MySQL Exclusive) ---
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "campusx_db")

# --- API Server Configuration ---
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_BASE_URL = os.getenv("API_BASE_URL", f"http://{API_HOST}:{API_PORT}")
SECRET_KEY = os.getenv("SECRET_KEY", "campusx_secret_key_2026")

# --- Email / SMTP Configuration ---
SMTP_HOST = os.getenv("SMTP_HOST", "").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "").strip()
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip()
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USER or "noreply@campusx.edu").strip()
SMTP_TLS = os.getenv("SMTP_TLS", "true").lower() in ("true", "1", "yes")
DEV_MODE = os.getenv("DEV_MODE", "true").lower() in ("true", "1", "yes")

# --- Asset Paths ---
ASSETS_DIR = BASE_DIR / "assets"
LOGO_PATH = ASSETS_DIR / "campusx_logo.png"

# --- Official CAMPUSX Design System Colors ---
COLOR_DEEP_NAVY = "#0B1F33"
COLOR_ACADEMIC_BLUE = "#1E4E8C"
COLOR_BRIGHT_BLUE = "#3B82F6"
COLOR_PURPLE = "#6C5CE7"
COLOR_CYAN = "#22C7E8"
COLOR_SOFT_BG = "#F6F8FC"
COLOR_WHITE = "#FFFFFF"
COLOR_DARK_TEXT = "#0F172A"
COLOR_SECONDARY_TEXT = "#64748B"
COLOR_BORDER = "#E2E8F0"
COLOR_CARD_BG = "#FFFFFF"
COLOR_MUTED_BG = "#EDF2F7"
COLOR_SUCCESS = "#10B981"
COLOR_WARNING = "#F59E0B"
COLOR_DANGER = "#EF4444"

# --- Typography & Sizes ---
FONT_FAMILY = "Segoe UI"  # Clean modern sans-serif supported out of the box on Windows/macOS/Linux
FONT_HEADING = (FONT_FAMILY, 24, "bold")
FONT_SUBHEADING = (FONT_FAMILY, 16, "bold")
FONT_SECTION = (FONT_FAMILY, 14, "bold")
FONT_BODY = (FONT_FAMILY, 12)
FONT_BODY_BOLD = (FONT_FAMILY, 12, "bold")
FONT_CAPTION = (FONT_FAMILY, 10)
