from flask import Blueprint, send_file, current_app, jsonify
import os
import mimetypes

media_bp = Blueprint('media', __name__, url_prefix='/media')


@media_bp.route('/images/<path:filename>', methods=['GET'])
def serve_image(filename):
    """Serve image from storage"""
    try:
        image_dir = current_app.config.get('IMAGE_DIR', '/app/images')
        file_path = os.path.join(image_dir, filename)

        if not os.path.exists(file_path):
            return jsonify({'error': 'Image not found'}), 404

        # Security: prevent path traversal
        if not os.path.abspath(file_path).startswith(os.path.abspath(image_dir)):
            return jsonify({'error': 'Access denied'}), 403

        # Guess mimetype
        mime_type, _ = mimetypes.guess_type(file_path)
        return send_file(file_path, mimetype=mime_type or 'application/octet-stream')

    except Exception as e:
        return jsonify({'error': f'Failed to serve image: {str(e)}'}), 500


@media_bp.route('/download/<path:filename>', methods=['GET'])
def download_image(filename):
    """Download image as attachment"""
    try:
        image_dir = current_app.config.get('IMAGE_DIR', '/app/images')
        file_path = os.path.join(image_dir, filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'Image not found'}), 404
        
        # Security: prevent path traversal
        if not os.path.abspath(file_path).startswith(os.path.abspath(image_dir)):
            return jsonify({'error': 'Access denied'}), 403
        
        return send_file(file_path, as_attachment=True, download_name=os.path.basename(file_path))
    
    except Exception as e:
        return jsonify({'error': f'Download failed: {str(e)}'}), 500