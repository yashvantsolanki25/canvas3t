"""Flask extensions initialization."""
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from app.utils.rate_limit import SimpleLimiter

db = SQLAlchemy()
cors = CORS(resources={
    r"/api/*": {
        "origins": ["*"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Length"],
        "supports_credentials": False
    }
})
limiter = SimpleLimiter()

