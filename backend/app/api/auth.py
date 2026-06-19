"""Authentication API endpoints."""
from flask import Blueprint, jsonify, request, current_app
from itsdangerous import URLSafeTimedSerializer

from ..extensions import db
from ..models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/register")
def register():
    """Register a new user."""
    try:
        data = request.get_json(force=True, silent=True) or {}
        
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not email or not password:
            return jsonify({'error': 'Username, email, and password required'}), 400
        
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already exists'}), 409
        
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already exists'}), 409
        
        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Generate token
        secret = current_app.config.get('SECRET_KEY', 'canvas3t-dev-secret')
        serializer = URLSafeTimedSerializer(secret)
        token = serializer.dumps({'user_id': user.id, 'username': user.username})
        
        return jsonify({
            'message': 'User registered successfully',
            'token': token,
            'user_id': user.id,
            'username': user.username,
            'user': user.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500


@auth_bp.post("/login")
def login():
    """Login user and return token."""
    try:
        data = request.get_json(force=True, silent=True) or {}
        
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        # Find user
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            return jsonify({'error': 'Invalid username or password'}), 401
        
        # Generate token using application SECRET_KEY so tokens persist across restarts
        secret = current_app.config.get('SECRET_KEY', 'canvas3t-dev-secret')
        serializer = URLSafeTimedSerializer(secret)
        token = serializer.dumps({'user_id': user.id, 'username': user.username})
        
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': user.to_dict()
        }), 200
    
    except Exception as e:
        return jsonify({'error': f'Login failed: {str(e)}'}), 500


@auth_bp.post("/verify")
def verify_token():
    """Verify token validity."""
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')

        if not token:
            return jsonify({'error': 'No token provided'}), 400

        # Use app SECRET_KEY to validate token
        secret = current_app.config.get('SECRET_KEY', 'canvas3t-dev-secret')
        serializer = URLSafeTimedSerializer(secret)
        data = serializer.loads(token, max_age=86400*7)  # 7 days
        user = User.query.get(data['user_id'])
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'valid': True,
            'user': user.to_dict()
        }), 200
    
    except Exception as e:
        return jsonify({'error': 'Token verification failed'}), 401


