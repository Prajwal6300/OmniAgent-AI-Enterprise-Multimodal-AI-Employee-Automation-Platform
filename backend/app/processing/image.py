"""
OmniAgent AI — Image Validation & Processing Module
Enforces strict magic bytes, size limits, dimension limits, and decompression bomb prevention.
"""

import io
from typing import Any

import structlog
from PIL import Image

logger = structlog.get_logger(__name__)

# Magic byte signatures
ALLOWED_IMAGE_SIGNATURES = {
    "image/jpeg": (b"\xff\xd8\xff",),
    "image/png": (b"\x89PNG\r\n\x1a\n",),
    "image/webp": (b"RIFF",),
}

MAX_IMAGE_BYTES = 15 * 1024 * 1024  # 15 MB
MAX_DIMENSION = 4096
MAX_PIXELS = 16_000_000  # 16 MP cap to prevent decompression bombs


def validate_and_process_image(
    file_bytes: bytes,
    max_bytes: int = MAX_IMAGE_BYTES,
) -> dict[str, Any]:
    """
    Validates magic bytes, verifies PIL integrity, and checks pixel count.
    Returns metadata dict with dimensions and format.
    """
    if len(file_bytes) > max_bytes:
        raise ValueError(f"Image exceeds maximum allowed size of {max_bytes // (1024 * 1024)} MB")

    # Detect matching mime type from magic bytes
    detected_mime = None
    for mime, signatures in ALLOWED_IMAGE_SIGNATURES.items():
        if any(file_bytes.startswith(sig) for sig in signatures):
            if mime == "image/webp" and b"WEBP" not in file_bytes[:16]:
                continue
            detected_mime = mime
            break

    if not detected_mime:
        raise ValueError("Invalid image format: magic byte header does not match JPEG, PNG, or WebP")

    # Guard against decompression bomb attacks
    Image.MAX_IMAGE_PIXELS = MAX_PIXELS

    try:
        with Image.open(io.BytesIO(file_bytes)) as img:
            img.verify()
    except Exception as exc:
        raise ValueError("Image file corrupted or invalid") from exc

    # Re-open after verify() to inspect properties safely
    with Image.open(io.BytesIO(file_bytes)) as img:
        width, height = img.size
        if width > MAX_DIMENSION or height > MAX_DIMENSION:
            raise ValueError(
                f"Image dimensions ({width}x{height}) exceed maximum allowed dimension ({MAX_DIMENSION}px)"
            )

        if width * height > MAX_PIXELS:
            raise ValueError("Image total pixel count exceeds maximum allowable threshold")

        return {
            "format": img.format,
            "mime_type": detected_mime,
            "width": width,
            "height": height,
            "size_bytes": len(file_bytes),
        }
