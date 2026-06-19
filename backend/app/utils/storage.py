from __future__ import annotations

import os
import uuid
from PIL import Image
from werkzeug.utils import secure_filename
from flask import current_app


class StorageError(RuntimeError):
    pass


SUPPORTED_FORMATS = {
    "PNG": "png",
    "JPEG": "jpg",
    "JPG": "jpg",
    "WEBP": "webp",
}


def _safe_name(filename: str, extension: str) -> tuple[str, str]:
    base = Path(filename).stem or "canvas3t"
    cleaned = secure_filename(base)
    prefix = uuid4().hex
    return prefix, f"{prefix}_{cleaned}.{extension}"


def _resolve_format(desired: str | None, detected: str | None) -> tuple[str, str]:
    target = (desired or detected or "PNG").upper()
    if target not in SUPPORTED_FORMATS:
        raise StorageError(f"Unsupported format: {target}")
    return target, SUPPORTED_FORMATS[target]


def persist_image_stream(
    stream: BinaryIO,
    original_name: str,
    image_dir: str,
    *,
    subdir: str | None = None,
    desired_format: str | None = None,
) -> tuple[str, Path, int, int, str, str]:
    base_dir = Path(image_dir)
    target_dir = base_dir / subdir if subdir else base_dir
    target_dir.mkdir(parents=True, exist_ok=True)

    buffer = BytesIO(stream.read())
    buffer.seek(0)

    try:
        image = Image.open(buffer)
    except Exception as exc:
        raise StorageError("Invalid image payload") from exc

    fmt, ext = _resolve_format(desired_format, image.format)
    prefix, filename = _safe_name(original_name, ext)
    target_path = target_dir / filename

    if fmt == "JPEG":
        image = image.convert("RGB")
    else:
        image = image.convert("RGBA")

    image.save(target_path, format=fmt)
    return (
        str(target_path.relative_to(base_dir)),
        target_path,
        image.width,
        image.height,
        fmt,
        prefix,
    )


def save_image_file(
    file_storage: FileStorage,
    image_dir: str,
    *,
    subdir: str | None = None,
    desired_format: str | None = None,
) -> tuple[str, Path, int, int, str, str]:
    if not file_storage or not file_storage.filename:
        raise StorageError("Missing image file")

    file_storage.stream.seek(0)
    return persist_image_stream(
        file_storage.stream,
        file_storage.filename,
        image_dir,
        subdir=subdir,
        desired_format=desired_format,
    )


def download_image_stream(url: str) -> tuple[BytesIO, str]:
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
    except requests.RequestException as exc:  # pragma: no cover
        raise StorageError("Unable to download remote image") from exc

    filename = Path(url.split("?")[0]).name or "remote.png"
    stream = BytesIO(response.content)
    stream.seek(0)
    return stream, filename


def save_remote_image(
    url: str, image_dir: str, *, subdir: str | None = None, desired_format: str | None = None
) -> tuple[str, Path, int, int, str, str]:
    stream, filename = download_image_stream(url)
    return persist_image_stream(
        stream, filename, image_dir, subdir=subdir, desired_format=desired_format
    )


def delete_file(path: str | Path) -> None:
    try:
        Path(path).unlink(missing_ok=True)
    except OSError as exc:  # pragma: no cover - best effort cleanup
        raise StorageError(f"Unable to delete file: {path}") from exc


def save_image(file, subdir=''):
    """
    Save uploaded image with thumbnail and return metadata.
    Returns dict with: rel_path, image_url, thumbnail_url, prefix, width, height, format
    """
    try:
        # Ensure IMAGE_DIR exists
        image_dir = current_app.config.get('IMAGE_DIR', '/app/images')
        os.makedirs(image_dir, exist_ok=True)
        
        # Create subdirectory for user/folder
        if subdir:
            user_subdir = os.path.join(image_dir, secure_filename(subdir))
            os.makedirs(user_subdir, exist_ok=True)
        else:
            user_subdir = image_dir
        
        # Generate unique prefix
        prefix = str(uuid.uuid4())
        
        # Secure filename
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        ext = ext.lower() or '.png'
        
        # Create filename with prefix
        final_filename = f"{prefix}_{name}{ext}"
        final_path = os.path.join(user_subdir, final_filename)
        
        # Save original image
        file.save(final_path)
        
        # Get image metadata
        img = Image.open(final_path)
        width, height = img.size
        img_format = img.format or 'PNG'
        
        # Generate thumbnail
        thumbnail_filename = f"{prefix}_{name}_thumb.jpg"
        thumbnail_path = os.path.join(user_subdir, thumbnail_filename)
        
        # Create 200x200 thumbnail
        img.thumbnail((200, 200), Image.Resampling.LANCZOS)
        img.save(thumbnail_path, 'JPEG', quality=85)
        
        # Build relative paths
        if subdir:
            rel_path = os.path.join(subdir, final_filename).replace('\\', '/')
            thumb_rel_path = os.path.join(subdir, thumbnail_filename).replace('\\', '/')
        else:
            rel_path = final_filename
            thumb_rel_path = thumbnail_filename
        
        # Build URLs for serving
        image_url = f'/media/images/{rel_path}'
        thumbnail_url = f'/media/images/{thumb_rel_path}'
        
        return {
            'rel_path': rel_path,
            'image_url': image_url,
            'thumbnail_url': thumbnail_url,
            'prefix': prefix,
            'width': width,
            'height': height,
            'format': ext.lstrip('.').lower()
        }
    
    except Exception as e:
        return {'error': f'Image save failed: {str(e)}'}

