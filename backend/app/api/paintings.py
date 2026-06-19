"""Paintings API endpoints."""
import os
import uuid
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request
from PIL import Image
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from io import BytesIO
from urllib.parse import urlparse

from ..extensions import db
from ..models import Painting, User

paintings_bp = Blueprint("paintings", __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_image(file, username='anonymous', folder='', is_public=False):
    """Save uploaded image and return metadata.
    
    Public images are saved in /app/images/public/ folder.
    Private images are saved in /app/images/{username}/ folder.
    """
    try:
        image_dir = current_app.config.get('IMAGE_DIR', '/app/images')
        os.makedirs(image_dir, exist_ok=True)
        
        # Determine save location based on public status
        if is_public:
            # Public images go to /app/images/public/
            user_folder = 'public'
            user_dir = os.path.join(image_dir, user_folder)
            os.makedirs(user_dir, exist_ok=True)
            # Create subfolder for organization if provided
            if folder:
                folder_name = secure_filename(folder)
                file_dir = os.path.join(user_dir, folder_name)
                os.makedirs(file_dir, exist_ok=True)
            else:
                file_dir = user_dir
        else:
            # Private images go to /app/images/{username}/
            user_folder = secure_filename(username)
            user_dir = os.path.join(image_dir, user_folder)
            os.makedirs(user_dir, exist_ok=True)
            
            # Create subfolder if provided
            if folder:
                folder_name = secure_filename(folder)
                file_dir = os.path.join(user_dir, folder_name)
                os.makedirs(file_dir, exist_ok=True)
            else:
                file_dir = user_dir
        
        # Generate prefix (UUID)
        prefix = str(uuid.uuid4())[:8]
        
        # Secure and create filename
        original_name = secure_filename(file.filename or 'image')
        name, ext = os.path.splitext(original_name)
        if not ext or ext.lower() not in [f".{e}" for e in ALLOWED_EXTENSIONS]:
            ext = '.png'
        
        filename = f"{prefix}_{name}{ext.lower()}"
        file_path = os.path.join(file_dir, filename)
        
        # Save original
        file.save(file_path)
        
        # Get image info
        img = Image.open(file_path)
        width, height = img.size
        img_format = img.format or 'PNG'
        
        # Create thumbnail
        thumb_filename = f"{prefix}_{name}_thumb.jpg"
        thumb_path = os.path.join(file_dir, thumb_filename)
        img.thumbnail((200, 200), Image.Resampling.LANCZOS)
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        img.save(thumb_path, 'JPEG', quality=85)
        
        # Build relative paths
        if folder:
            rel_path = f"{user_folder}/{folder_name}/{filename}".replace('\\', '/')
            thumb_rel_path = f"{user_folder}/{folder_name}/{thumb_filename}".replace('\\', '/')
        else:
            rel_path = f"{user_folder}/{filename}".replace('\\', '/')
            thumb_rel_path = f"{user_folder}/{thumb_filename}".replace('\\', '/')
        
        return {
            'filename': rel_path,
            'thumbnail': thumb_rel_path,
            'prefix': prefix,
            'width': width,
            'height': height,
            'format': ext.lstrip('.').lower()
        }
    except Exception as e:
        current_app.logger.error(f"Image save failed: {e}")
        return None


@paintings_bp.post("/import-url")
def import_remote_image():
    """Import image from remote URL."""
    try:
        payload = request.get_json(force=True, silent=True) or {}
        if 'image_url' not in payload:
            return jsonify({'error': 'Missing image_url'}), 400

        image_url = payload.get('image_url')
        title = payload.get('title', 'Imported')
        folder = payload.get('folder', '').strip()
        is_public_str = str(payload.get('is_public', 'false')).strip().lower()
        is_public = is_public_str in ('true', '1', 'yes', 'on')
        tags = payload.get('tags', '')

        # Download the image
        import requests as req_lib
        response = req_lib.get(image_url, timeout=15)
        response.raise_for_status()

        # Determine filename from URL
        parsed = urlparse(image_url)
        filename = secure_filename(parsed.path.split('/')[-1] or 'imported.png')
        if not filename:
            filename = 'imported.png'

        # Build a FileStorage-like object so save_image can use it
        file_stream = BytesIO(response.content)
        content_type = response.headers.get('Content-Type', 'application/octet-stream')
        file_storage = FileStorage(stream=file_stream, filename=filename, content_type=content_type)

        # Determine user from Authorization header if present
        user_id = None
        username = 'anonymous'
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            try:
                from itsdangerous import URLSafeTimedSerializer
                serializer = URLSafeTimedSerializer(current_app.config.get('SECRET_KEY', 'canvas3t-dev-secret'))
                token_data = serializer.loads(token, max_age=7*24*3600)
                user_id = token_data.get('user_id')
            except Exception as e:
                current_app.logger.warning(f"Token validation failed: {e}")

        if user_id:
            user = User.query.get(user_id)
            if user:
                username = user.username

        # Save the downloaded image into storage (with public segregation)
        result = save_image(file_storage, username=username, folder=folder, is_public=is_public)
        if not result:
            return jsonify({'error': 'Failed to save imported image'}), 500

        # Create painting record
        painting = Painting(
            user_id=user_id,
            title=title,
            description=payload.get('description', ''),
            filename=result['filename'],
            thumbnail=result['thumbnail'],
            prefix=result['prefix'],
            folder=folder,
            width=result.get('width', 0),
            height=result.get('height', 0),
            format=result.get('format', 'png'),
            is_public=is_public,
            tags=tags,
            source_url=image_url
        )

        db.session.add(painting)
        db.session.commit()

        return jsonify({
            'message': 'Imported and saved successfully',
            'painting': painting.to_dict()
        }), 201
    
    except Exception as e:
        current_app.logger.error(f"Import failed: {e}")
        return jsonify({'error': f'Import failed: {str(e)}'}), 500


@paintings_bp.post("")
def create_painting():
    """Upload and save a painting."""
    try:
        # Get form data
        user_id = request.form.get('user_id', type=int)
        title = request.form.get('title', 'Untitled').strip()
        folder = request.form.get('folder', '').strip()
        is_public_str = request.form.get('is_public', 'false').strip().lower()
        is_public = is_public_str in ('true', '1', 'yes', 'on')
        description = request.form.get('description', '').strip()
        tags = request.form.get('tags', '').strip()
        
        # Try to extract user_id from Bearer token if not provided in form
        if not user_id:
            from itsdangerous import URLSafeTimedSerializer
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]
                try:
                    serializer = URLSafeTimedSerializer(current_app.config.get('SECRET_KEY', 'dev'))
                    token_data = serializer.loads(token, max_age=7*24*3600)
                    user_id = token_data.get('user_id')
                except Exception as e:
                    current_app.logger.warning(f"Token validation failed: {e}")
        
        # Check file
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'error': f'File type not allowed. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400
        
        # Get or create user
        username = 'anonymous'
        if user_id:
            user = User.query.get(user_id)
            if not user:
                return jsonify({'error': 'User not found'}), 404
            username = user.username
        else:
            user_id = None
        
        # Save image (with public folder segregation)
        result = save_image(file, username=username, folder=folder, is_public=is_public)
        if not result:
            return jsonify({'error': 'Failed to save image'}), 500
        
        # Create painting record
        painting = Painting(
            user_id=user_id,
            title=title,
            description=description,
            filename=result['filename'],
            thumbnail=result['thumbnail'],
            prefix=result['prefix'],
            folder=folder,
            width=result['width'],
            height=result['height'],
            format=result['format'],
            is_public=is_public,
            tags=tags,
            source_url=request.form.get('source_url')
        )
        
        db.session.add(painting)
        db.session.commit()
        
        return jsonify({
            'message': 'Painting created successfully',
            'painting': painting.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Upload failed: {e}")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500


@paintings_bp.get("")
def list_paintings():
    """List paintings (public by default, or user's own)."""
    try:
        user_id = request.args.get('user_id', type=int)
        folder = request.args.get('folder', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = int(os.getenv('RESULTS_PER_PAGE', 24))
        
        query = Painting.query
        
        # Filter by user
        if user_id:
            user = User.query.get(user_id)
            if not user:
                return jsonify({'error': 'User not found'}), 404
            query = query.filter_by(user_id=user_id)
        else:
            # Default to public paintings for anonymous users
            query = query.filter_by(is_public=True)
        
        # Filter by folder
        if folder:
            query = query.filter_by(folder=folder)
        
        # Paginate
        paginated = query.order_by(Painting.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Return a consistent paginated shape expected by frontend
        return jsonify({
            'total': paginated.total,
            'page': page,
            'per_page': per_page,
            'pages': paginated.pages,
            'paintings': [p.to_dict() for p in paginated.items]
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"List failed: {e}")
        return jsonify({'error': f'Failed to fetch paintings: {str(e)}'}), 500



@paintings_bp.get("/<int:painting_id>")
def get_painting(painting_id: int):
    """Return a single painting by id."""
    try:
        painting = Painting.query.get(painting_id)
        if not painting:
            return jsonify({'error': 'Painting not found'}), 404
        # If painting is public, return it. Otherwise verify token owner.
        if painting.is_public:
            return jsonify(painting.to_dict()), 200

        # Try to get user id from Authorization header
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            try:
                from itsdangerous import URLSafeTimedSerializer
                serializer = URLSafeTimedSerializer(current_app.config.get('SECRET_KEY', 'canvas3t-dev-secret'))
                token = auth_header[7:]
                data = serializer.loads(token, max_age=7*24*3600)
                token_user_id = data.get('user_id')
                if token_user_id == painting.user_id:
                    return jsonify(painting.to_dict()), 200
            except Exception:
                pass

        return jsonify({'error': 'Access denied'}), 403
    except Exception as e:
        current_app.logger.error(f"Get painting failed: {e}")
        return jsonify({'error': f'Failed to fetch painting: {str(e)}'}), 500


@paintings_bp.put("/<int:painting_id>")
def update_painting(painting_id: int):
    """Update painting metadata or replace image."""
    try:
        painting = Painting.query.get(painting_id)
        if not painting:
            return jsonify({'error': 'Painting not found'}), 404

        # Authorization: try to extract user from token if present
        auth_header = request.headers.get('Authorization', '')
        token_user_id = None
        if auth_header.startswith('Bearer '):
            try:
                from itsdangerous import URLSafeTimedSerializer
                serializer = URLSafeTimedSerializer(current_app.config.get('SECRET_KEY', 'canvas3t-dev-secret'))
                token = auth_header[7:]
                data = serializer.loads(token, max_age=7*24*3600)
                token_user_id = data.get('user_id')
            except Exception:
                token_user_id = None

        # Only owner can update
        if painting.user_id and token_user_id != painting.user_id:
            return jsonify({'error': 'Forbidden'}), 403

        # Parse fields
        title = request.form.get('title')
        folder = request.form.get('folder')
        description = request.form.get('description')
        tags = request.form.get('tags')
        is_public_str = request.form.get('is_public')
        if title is not None:
            painting.title = title.strip()
        if description is not None:
            painting.description = description.strip()
        if tags is not None:
            painting.tags = tags.strip()
        if folder is not None:
            painting.folder = folder.strip()
        if is_public_str is not None:
            painting.is_public = str(is_public_str).strip().lower() in ('true', '1', 'yes', 'on')

        # If new image provided, save and update paths
        if 'image' in request.files:
            file = request.files['image']
            username = painting.user.username if painting.user else 'anonymous'
            result = save_image(file, username=username, folder=painting.folder)
            if not result:
                return jsonify({'error': 'Failed to save new image'}), 500
            painting.filename = result['filename']
            painting.thumbnail = result['thumbnail']
            painting.prefix = result['prefix']
            painting.width = result.get('width', painting.width)
            painting.height = result.get('height', painting.height)
            painting.format = result.get('format', painting.format)

        db.session.commit()
        return jsonify({'message': 'Painting updated', 'painting': painting.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update painting failed: {e}")
        return jsonify({'error': f'Update failed: {str(e)}'}), 500





