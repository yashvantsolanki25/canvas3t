"""Flask application factory."""
from __future__ import annotations

import logging
import os
from pathlib import Path

from flask import Flask
from sqlalchemy.exc import IntegrityError

from app.config import Config
from app.extensions import db, cors, limiter
from app.models import User

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_app(config_class: type[Config] | None = None) -> Flask:
    """Application factory."""
    app = Flask(__name__, static_folder=None)
    app.config.from_object(config_class or Config())
    
    # Create required directories
    _ensure_storage_dirs(app)
    
    # Initialize extensions
    db.init_app(app)
    cors.init_app(app)
    limiter.init_app(app)
    
    # Create database tables
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database tables created/verified")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
    
    # Register blueprints
    _register_blueprints(app)
    
    # Seed default user
    with app.app_context():
        _seed_default_user()
    
    # Health check route — excluded from rate limiting
    @app.get("/api/health")
    def health():
        return {"status": "ok"}, 200
    
    return app


def _ensure_storage_dirs(app: Flask) -> None:
    """Create required directories for data persistence."""
    dirs = [
        app.config.get("IMAGE_DIR"),
        app.config.get("THUMBNAIL_DIR"),
        app.config.get("DB_DIR"),
    ]
    for dir_path in dirs:
        if dir_path:
            Path(dir_path).mkdir(parents=True, exist_ok=True)


def _register_blueprints(app: Flask) -> None:
    """Register all API blueprints."""
    from app.api.auth import auth_bp
    from app.api.users import users_bp
    from app.api.paintings import paintings_bp
    from app.api.media import media_bp
    from app.api.search import search_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(users_bp, url_prefix="/api/users")
    app.register_blueprint(paintings_bp, url_prefix="/api/paintings")
    app.register_blueprint(search_bp, url_prefix="/api/search")
    app.register_blueprint(media_bp, url_prefix="/media")


def _seed_default_user() -> None:
    """Create default user if not exists."""
    if User.query.first():
        return
    
    try:
        user = User(
            username="demo",
            email="demo@canvas3t.local"
        )
        user.set_password("demo123456")
        db.session.add(user)
        db.session.commit()
        logger.info("Default user 'demo' created")
    except IntegrityError:
        db.session.rollback()
        logger.info("Default user already exists")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to seed default user: {e}")


