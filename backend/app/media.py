"""Media serving endpoints."""
import os
from flask import Blueprint, current_app, send_from_directory, jsonify

media_bp = Blueprint("media", __name__)


@media_bp.get("/images/<path:filename>")
def serve_image(filename: str):
    """Serve image from storage."""
    try:
        image_dir = current_app.config.get('IMAGE_DIR', '/app/images')
        
        # Security: prevent path traversal
        if not os.path.abspath(os.path.join(image_dir, filename)).startswith(os.path.abspath(image_dir)):
            return jsonify({'error': 'Access denied'}), 403
        
        return send_from_directory(image_dir, filename)
    except Exception as e:
        return jsonify({'error': f'Failed to serve image: {str(e)}'}), 500


@media_bp.get("/thumbnails/<path:filename>")
def serve_thumbnail(filename: str):
    """Serve thumbnail from storage."""
    try:
        image_dir = current_app.config.get('IMAGE_DIR', '/app/images')
        
        # Security: prevent path traversal
        if not os.path.abspath(os.path.join(image_dir, filename)).startswith(os.path.abspath(image_dir)):
            return jsonify({'error': 'Access denied'}), 403
        
        return send_from_directory(image_dir, filename)
    except Exception as e:
        return jsonify({'error': f'Failed to serve thumbnail: {str(e)}'}), 500


@media_bp.get("/download/<path:filename>")
def download_image(filename: str):
    """Download image as attachment."""
    try:
        image_dir = current_app.config.get('IMAGE_DIR', '/app/images')
        
        # Security: prevent path traversal
        if not os.path.abspath(os.path.join(image_dir, filename)).startswith(os.path.abspath(image_dir)):
            return jsonify({'error': 'Access denied'}), 403
        
        return send_from_directory(image_dir, filename, as_attachment=True)
    except Exception as e:
        return jsonify({'error': f'Download failed: {str(e)}'}), 500


