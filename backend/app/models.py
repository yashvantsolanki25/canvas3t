"""Database models."""
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db


class User(db.Model):
    """User model for authentication."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    paintings = db.relationship('Painting', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password."""
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    def check_password(self, password):
        """Verify password against hash."""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Return user as dictionary."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<User {self.username}>'


class Painting(db.Model):
    """Painting/Image model."""
    __tablename__ = 'paintings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True, index=True)
    title = db.Column(db.String(255), nullable=False, default='Untitled')
    description = db.Column(db.Text, default='')
    filename = db.Column(db.String(512), nullable=False)  # relative path with subdir
    prefix = db.Column(db.String(36), nullable=True)  # UUID prefix for uniqueness
    folder = db.Column(db.String(255), default='')  # user-defined folder
    width = db.Column(db.Integer, default=0)
    height = db.Column(db.Integer, default=0)
    format = db.Column(db.String(10), default='png')
    is_public = db.Column(db.Boolean, default=False, nullable=False, index=True)
    tags = db.Column(db.Text, default='')
    thumbnail = db.Column(db.String(512))
    source_url = db.Column(db.String(1024))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        db.Index('idx_user_public_created', 'user_id', 'is_public', 'created_at'),
    )
    
    def to_dict(self):
        """Return painting as dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else 'Anonymous',
            'title': self.title,
            'description': self.description,
            'filename': self.filename,
            'prefix': self.prefix,
            'folder': self.folder,
            'width': self.width,
            'height': self.height,
            'format': self.format,
            'is_public': self.is_public,
            'tags': self.tags,
            'thumbnail': self.thumbnail,
            'source_url': self.source_url,
            # Add URLs for frontend convenience (served by media blueprint)
            'image_url': f"/media/images/{self.filename}" if self.filename else None,
            'thumbnail_url': f"/media/images/{self.thumbnail}" if self.thumbnail else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Painting {self.title}>'


