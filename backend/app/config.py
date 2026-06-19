from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent
DATA_DIR = Path(os.getenv("DATA_DIR", ROOT_DIR / "data"))
DB_DIR = Path(os.getenv("DB_DIR", DATA_DIR / "db"))
IMAGE_DIR = Path(os.getenv("IMAGE_DIR", DATA_DIR / "images"))
THUMBNAIL_DIR = Path(os.getenv("THUMBNAIL_DIR", IMAGE_DIR / "thumbnails"))
DB_PATH = Path(os.getenv("DB_PATH", DB_DIR / "app.db"))


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "canvas3t-dev-secret")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_UPLOAD_MB", "20")) * 1024 * 1024
    IMAGE_DIR = str(IMAGE_DIR)
    THUMBNAIL_DIR = str(THUMBNAIL_DIR)
    DATA_DIR = str(DATA_DIR)
    DB_DIR = str(DB_DIR)
    THUMBNAIL_SIZE = int(os.getenv("THUMBNAIL_SIZE", "512"))
    RESULTS_PER_PAGE = int(os.getenv("RESULTS_PER_PAGE", "20"))
    CORS_ALLOW_ORIGINS = os.getenv("CORS_ALLOW_ORIGINS", "*")
    ENABLE_RATE_LIMITS = os.getenv("ENABLE_RATE_LIMITS", "true").lower() == "true"
    RATE_LIMIT = os.getenv("RATE_LIMIT", "50/minute")

