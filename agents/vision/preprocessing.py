"""
Image Preprocessing and Validation Pipeline.
Implements safe validation, decompression bomb safeguards, magic byte inspection,
EXIF orientation correction, metadata sanitization, and RGB normalization.
Preserves original files immutably without overwriting.
"""

import io
from pathlib import Path

from PIL import Image, ImageFile, ImageOps

try:
    from app.core.config import settings
except ImportError:
    try:
        from backend.app.core.config import settings
    except ImportError:

        class SettingsFallback:
            VISION_MAX_FILE_SIZE_MB = 10
            VISION_MAX_WIDTH = 4096
            VISION_MAX_HEIGHT = 4096
            VISION_MAX_IMAGE_PIXELS = 16_777_216
            VISION_OCR_ENABLED = True
            VISION_OBJECT_DETECTION_ENABLED = True
            VISION_PROVIDER = "mock"
            VISION_MODEL = "gpt-4o"

        settings = SettingsFallback()

from agents.vision.exceptions import VisionProcessingError, VisionValidationError

# Supported MIME types and extensions
SUPPORTED_MIME_TYPES = {
    "image/jpeg": [".jpg", ".jpeg"],
    "image/jpg": [".jpg", ".jpeg"],
    "image/png": [".png"],
    "image/webp": [".webp"],
}

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

# Set PIL safety threshold to prevent decompression bombs (e.g. pixel floods)
ImageFile.LOAD_TRUNCATED_IMAGES = False
Image.MAX_IMAGE_PIXELS = getattr(settings, "VISION_MAX_IMAGE_PIXELS", 16_777_216)


def validate_image_magic_bytes(file_bytes: bytes) -> str:
    """
    Validates the binary header signature (magic bytes) to verify genuine image content.
    Returns the detected canonical format: 'JPEG', 'PNG', or 'WEBP'.
    Raises VisionValidationError if signatures do not match or are unsupported.
    """
    if not file_bytes or len(file_bytes) < 12:
        raise VisionValidationError(
            "Image file is empty or too small to contain valid headers."
        )

    # JPEG signature: 0xFF 0xD8 0xFF
    if file_bytes.startswith(b"\xff\xd8\xff"):
        return "JPEG"

    # PNG signature: 0x89 0x50 0x4E 0x47 0x0D 0x0A 0x1A 0x0A
    if file_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "PNG"

    # WEBP signature: 'RIFF' at 0..4 and 'WEBP' at 8..12
    if file_bytes.startswith(b"RIFF") and file_bytes[8:12] == b"WEBP":
        return "WEBP"

    # Check for dangerous or unapproved binary headers
    if file_bytes.startswith(b"MZ"):
        raise VisionValidationError(
            "Executable file disguised as image is strictly forbidden."
        )
    if file_bytes.startswith(b"\x7fELF"):
        raise VisionValidationError(
            "ELF binary disguised as image is strictly forbidden."
        )
    if file_bytes.startswith(b"GIF8"):
        raise VisionValidationError(
            "GIF format is currently unsupported. Please upload JPEG, PNG, or WEBP."
        )
    if b"<svg" in file_bytes[:100].lower() or b"<?xml" in file_bytes[:100].lower():
        raise VisionValidationError(
            "SVG vector format is unsupported for safety reasons."
        )

    raise VisionValidationError(
        "Unsupported or invalid image file signature. Allowed formats: JPEG, PNG, WEBP."
    )


def validate_image_metadata(
    filename: str, file_bytes: bytes, mime_type: str | None = None
) -> str:
    """
    Validates file extension, MIME type, file size, and magic bytes.
    Returns canonical format string ('JPEG', 'PNG', 'WEBP').
    """
    # 1. Extension validation
    ext = Path(filename).suffix.lower()
    if not ext or ext not in SUPPORTED_EXTENSIONS:
        raise VisionValidationError(
            f"Unsupported file extension '{ext}'. Only JPEG (.jpg, .jpeg), PNG (.png), and WEBP (.webp) are supported.",
            details={"filename": filename, "extension": ext},
        )

    # 2. File size limit
    max_mb = getattr(settings, "VISION_MAX_FILE_SIZE_MB", 10)
    max_bytes = max_mb * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise VisionValidationError(
            f"Image size exceeds maximum limit of {max_mb} MB (actual: {len(file_bytes) / (1024 * 1024):.2f} MB).",
            details={"file_size_bytes": len(file_bytes), "max_bytes": max_bytes},
        )

    # 3. MIME type validation if provided
    if mime_type:
        clean_mime = mime_type.lower().split(";")[0].strip()
        if clean_mime not in SUPPORTED_MIME_TYPES:
            raise VisionValidationError(
                f"Unsupported MIME type '{mime_type}'. Supported: image/jpeg, image/png, image/webp.",
                details={"mime_type": mime_type},
            )

    # 4. Binary signature (magic bytes) validation
    detected_format = validate_image_magic_bytes(file_bytes)
    return detected_format


def safe_inspect_and_load(file_bytes: bytes) -> Image.Image:
    """
    Safely opens, verifies integrity against corruption, and loads the PIL Image.
    Protects against decompression bombs, truncated buffers, and corrupted streams.
    """
    # Verify image integrity first
    try:
        verify_stream = io.BytesIO(file_bytes)
        with Image.open(verify_stream) as img_verify:
            img_verify.verify()
    except Exception as exc:  # noqa: BLE001
        raise VisionValidationError(
            f"Image stream is corrupted or unreadable: {exc!s}",
            details={"error": str(exc)},
        )

    # Re-open for actual processing (verify closes stream/clears image)
    try:
        load_stream = io.BytesIO(file_bytes)
        img = Image.open(load_stream)
        img.load()  # Force load pixel data to ensure buffer is complete
        return img
    except Exception as exc:  # noqa: BLE001
        raise VisionValidationError(
            f"Failed to read image pixel data: {exc!s}", details={"error": str(exc)}
        )


def preprocess_image(
    file_bytes: bytes,
    filename: str = "image.jpg",
    mime_type: str | None = None,
    max_width: int | None = None,
    max_height: int | None = None,
) -> tuple[bytes, dict]:
    """
    Executes standard enterprise preprocessing pipeline:
    1. Validate format, size, and binary signature.
    2. Inspect for decompression bombs and corruption.
    3. Auto-orient according to EXIF Orientation tag.
    4. Strip sensitive metadata (e.g. GPS coordinates).
    5. Convert to normalized standard RGB (rendering transparency on white background).
    6. Resize smoothly if image exceeds maximum configured width/height.
    7. Export clean preprocessed JPEG or PNG bytes.

    Returns:
        (preprocessed_bytes, metadata_dict)
    """
    detected_format = validate_image_metadata(filename, file_bytes, mime_type)
    img = safe_inspect_and_load(file_bytes)

    orig_width, orig_height = img.size
    max_w = max_width or getattr(settings, "VISION_MAX_WIDTH", 4096)
    max_h = max_height or getattr(settings, "VISION_MAX_HEIGHT", 4096)
    max_pixels = getattr(settings, "VISION_MAX_IMAGE_PIXELS", 16_777_216)

    # Decompression / Dimensional validation
    if orig_width > max_w * 2 or orig_height > max_h * 2:
        raise VisionValidationError(
            f"Image dimensions ({orig_width}x{orig_height}) exceed extreme dimensional bounds ({max_w * 2}x{max_h * 2}).",
            details={"width": orig_width, "height": orig_height},
        )

    if (orig_width * orig_height) > max_pixels:
        raise VisionValidationError(
            f"Total pixel count ({orig_width * orig_height}) exceeds maximum limit ({max_pixels}).",
            details={
                "total_pixels": orig_width * orig_height,
                "max_pixels": max_pixels,
            },
        )

    try:
        # 1. Orientation correction via EXIF
        img = ImageOps.exif_transpose(img)

        # 2. Convert to normalized RGB
        if img.mode in ("RGBA", "LA", "P"):
            # Render on clean neutral white background
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            if "A" in img.mode:
                background.paste(img, mask=img.split()[-1])
            else:
                background.paste(img)
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")

        # 3. Constrain dimensions if required while preserving exact aspect ratio
        cur_w, cur_h = img.size
        if cur_w > max_w or cur_h > max_h:
            img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
            cur_w, cur_h = img.size

        # 4. Save to clean preprocessed JPEG buffer (quality=92, optimized, no EXIF)
        output_buffer = io.BytesIO()
        img.save(output_buffer, format="JPEG", quality=92, optimize=True)
        preprocessed_bytes = output_buffer.getvalue()

        metadata = {
            "original_width": orig_width,
            "original_height": orig_height,
            "width": cur_w,
            "height": cur_h,
            "format": detected_format,
            "channels": len(img.getbands()),
            "preprocessed_format": "JPEG",
            "preprocessed_size_bytes": len(preprocessed_bytes),
            "original_size_bytes": len(file_bytes),
        }

        return preprocessed_bytes, metadata

    except VisionValidationError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise VisionProcessingError(
            f"Image preprocessing failed during normalization: {exc!s}",
            details={"error": str(exc)},
        )
