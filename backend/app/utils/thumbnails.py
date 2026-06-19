from __future__ import annotations

from pathlib import Path
from typing import Tuple

from PIL import Image


def generate_thumbnail(
    image_path: Path,
    thumbnail_dir: str,
    *,
    max_size: int = 512,
) -> tuple[str, Path]:
    """Generate a thumbnail for the given image and return relative + absolute paths."""
    thumbnail_root = Path(thumbnail_dir)
    thumbnail_root.mkdir(parents=True, exist_ok=True)

    with Image.open(image_path) as img:
        img.thumbnail((max_size, max_size))
        thumb_name = f"{image_path.stem}_thumb{image_path.suffix}"
        thumb_path = thumbnail_root / thumb_name
        img.save(thumb_path)

    return thumb_path.name, thumb_path

