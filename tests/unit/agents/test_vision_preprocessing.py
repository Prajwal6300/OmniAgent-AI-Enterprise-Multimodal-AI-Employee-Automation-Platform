"""
Unit Tests for Vision Agent Image Preprocessing and File Validation.
Verifies format validation, magic byte detection, dimension boundaries,
decompression safeguards, corruption detection, and EXIF handling.
"""

import io

import pytest
from PIL import Image

from agents.vision.exceptions import VisionValidationError
from agents.vision.preprocessing import (
    preprocess_image,
    safe_inspect_and_load,
    validate_image_magic_bytes,
    validate_image_metadata,
)


def create_test_image_bytes(
    fmt: str = "JPEG",
    size: tuple[int, int] = (200, 200),
    color: str = "blue",
    mode: str = "RGB",
) -> bytes:
    """Helper creating valid in-memory image bytes."""
    buf = io.BytesIO()
    img = Image.new(mode, size, color=color)
    img.save(buf, format=fmt)
    return buf.getvalue()


# --- 1. Format & Magic Byte Tests ---


def test_valid_jpeg_magic_bytes():
    jpeg_bytes = create_test_image_bytes("JPEG")
    fmt = validate_image_magic_bytes(jpeg_bytes)
    assert fmt == "JPEG"


def test_valid_png_magic_bytes():
    png_bytes = create_test_image_bytes("PNG")
    fmt = validate_image_magic_bytes(png_bytes)
    assert fmt == "PNG"


def test_valid_webp_magic_bytes():
    webp_bytes = create_test_image_bytes("WEBP")
    fmt = validate_image_magic_bytes(webp_bytes)
    assert fmt == "WEBP"


def test_executable_disguised_as_image():
    fake_exe = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff"
    with pytest.raises(VisionValidationError) as exc:
        validate_image_magic_bytes(fake_exe)
    assert "Executable file disguised" in str(exc.value)


def test_elf_binary_disguised_as_image():
    fake_elf = b"\x7fELF\x02\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    with pytest.raises(VisionValidationError) as exc:
        validate_image_magic_bytes(fake_elf)
    assert "ELF binary disguised" in str(exc.value)


def test_svg_rejected_for_safety():
    svg_bytes = b"<svg width='100' height='100'><circle cx='50' cy='50' r='40'/></svg>"
    with pytest.raises(VisionValidationError) as exc:
        validate_image_magic_bytes(svg_bytes)
    assert "SVG vector format is unsupported" in str(exc.value)


def test_empty_or_tiny_bytes():
    with pytest.raises(VisionValidationError) as exc:
        validate_image_magic_bytes(b"short")
    assert "empty or too small" in str(exc.value)


# --- 2. File Metadata & Extension Validation Tests ---


def test_valid_jpg_metadata():
    img_bytes = create_test_image_bytes("JPEG")
    fmt = validate_image_metadata("inspection.jpg", img_bytes, "image/jpeg")
    assert fmt == "JPEG"


def test_valid_png_metadata():
    img_bytes = create_test_image_bytes("PNG")
    fmt = validate_image_metadata("diagram.png", img_bytes, "image/png")
    assert fmt == "PNG"


def test_valid_webp_metadata():
    img_bytes = create_test_image_bytes("WEBP")
    fmt = validate_image_metadata("photo.webp", img_bytes, "image/webp")
    assert fmt == "WEBP"


def test_unsupported_file_extension():
    with pytest.raises(VisionValidationError) as exc:
        validate_image_metadata("script.py", b"print('hello')", "text/x-python")
    assert "Unsupported file extension" in str(exc.value)


def test_unsupported_mime_type():
    img_bytes = create_test_image_bytes("JPEG")
    with pytest.raises(VisionValidationError) as exc:
        validate_image_metadata("image.jpg", img_bytes, "application/pdf")
    assert "Unsupported MIME type" in str(exc.value)


def test_oversized_file_size():
    # 11 MB fake payload
    oversized = b"\xff\xd8\xff" + b"0" * (11 * 1024 * 1024)
    with pytest.raises(VisionValidationError) as exc:
        validate_image_metadata("big.jpg", oversized, "image/jpeg")
    assert "exceeds maximum limit" in str(exc.value)


# --- 3. Corrupted Image & Safe Loading Tests ---


def test_corrupted_image_stream():
    # Valid header but chopped/corrupted body
    corrupt = (
        b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb"
        + b"\x00" * 20
    )
    with pytest.raises(VisionValidationError) as exc:
        safe_inspect_and_load(corrupt)
    assert "corrupted" in str(exc.value).lower() or "failed" in str(exc.value).lower()


# --- 4. Preprocessing & Normalization Tests ---


def test_preprocess_rgb_image():
    raw_bytes = create_test_image_bytes("JPEG", size=(300, 200), color="red")
    pre_bytes, meta = preprocess_image(raw_bytes, "sample.jpg", "image/jpeg")

    assert pre_bytes is not None
    assert len(pre_bytes) > 0
    assert meta["width"] == 300
    assert meta["height"] == 200
    assert meta["format"] == "JPEG"
    assert meta["channels"] == 3


def test_preprocess_rgba_converts_to_rgb_with_background():
    raw_bytes = create_test_image_bytes(
        "PNG", size=(150, 150), color="green", mode="RGBA"
    )
    pre_bytes, meta = preprocess_image(raw_bytes, "transparent.png", "image/png")

    assert pre_bytes is not None
    assert meta["channels"] == 3  # Normalized to RGB
    assert meta["format"] == "PNG"


def test_preprocess_resizes_oversized_dimensions():
    # Test constrained resize with max 400x400
    raw_bytes = create_test_image_bytes("JPEG", size=(800, 400), color="gray")
    _pre_bytes, meta = preprocess_image(
        raw_bytes, "wide.jpg", "image/jpeg", max_width=400, max_height=400
    )

    assert meta["width"] == 400
    assert meta["height"] == 200  # Aspect ratio preserved (2:1)
