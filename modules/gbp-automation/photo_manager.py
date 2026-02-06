"""
GBP Automation Module - Photo Manager
Upload pipeline with format/size validation, resizing, categorization,
and location assignment.
"""

import io
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from config import (
    PHOTO_ALLOWED_FORMATS,
    PHOTO_MAX_BYTES,
    PHOTO_MIN_BYTES,
    PHOTO_SPECS,
)
from models import MediaFormat, Photo, PhotoCategory


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class PhotoValidationError(Exception):
    """Raised when a photo fails validation checks."""


def validate_format(file_path: str) -> MediaFormat:
    """Check that the file extension is JPG or PNG.

    Returns the ``MediaFormat`` enum value on success.
    Raises ``PhotoValidationError`` on failure.
    """
    ext = Path(file_path).suffix.lstrip(".").upper()
    if ext not in PHOTO_ALLOWED_FORMATS:
        raise PhotoValidationError(
            f"Unsupported format '{ext}'. "
            f"Allowed: {', '.join(sorted(PHOTO_ALLOWED_FORMATS))}"
        )
    if ext == "JPG":
        return MediaFormat.JPEG
    return MediaFormat(ext)


def validate_size(file_path: str) -> int:
    """Check that file size is between 10 KB and 5 MB.

    Returns the file size in bytes on success.
    Raises ``PhotoValidationError`` on failure.
    """
    size = Path(file_path).stat().st_size
    if size < PHOTO_MIN_BYTES:
        raise PhotoValidationError(
            f"Photo too small ({size:,} bytes). "
            f"Minimum is {PHOTO_MIN_BYTES:,} bytes (10 KB)."
        )
    if size > PHOTO_MAX_BYTES:
        raise PhotoValidationError(
            f"Photo too large ({size:,} bytes). "
            f"Maximum is {PHOTO_MAX_BYTES:,} bytes (5 MB)."
        )
    return size


def validate_photo(file_path: str) -> Tuple[MediaFormat, int]:
    """Run all validation checks on a photo file.

    Returns ``(MediaFormat, size_bytes)`` on success.
    """
    fmt = validate_format(file_path)
    size = validate_size(file_path)
    return fmt, size


# ---------------------------------------------------------------------------
# Resizing
# ---------------------------------------------------------------------------


def resize_photo(
    file_path: str,
    category: PhotoCategory,
    output_path: Optional[str] = None,
) -> str:
    """Resize a photo to the platform spec for the given category.

    Uses Pillow (PIL) for image processing. The resized image is saved to
    ``output_path`` (defaults to ``<original>_resized.<ext>``).

    Returns the path to the resized file.
    """
    from PIL import Image

    spec = PHOTO_SPECS.get(category.value)
    if spec is None:
        raise ValueError(f"Unknown photo category: {category}")

    target_w = spec["width"]
    target_h = spec["height"]

    img = Image.open(file_path)
    original_format = img.format or "JPEG"

    # Resize using high-quality Lanczos resampling, preserving aspect ratio
    # then center-cropping to exact dimensions.
    img_ratio = img.width / img.height
    target_ratio = target_w / target_h

    if img_ratio > target_ratio:
        # Image is wider -- scale by height, crop width
        new_h = target_h
        new_w = int(target_h * img_ratio)
    else:
        # Image is taller -- scale by width, crop height
        new_w = target_w
        new_h = int(target_w / img_ratio)

    img = img.resize((new_w, new_h), Image.LANCZOS)

    # Center crop
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    img = img.crop((left, top, left + target_w, top + target_h))

    if output_path is None:
        p = Path(file_path)
        output_path = str(p.parent / f"{p.stem}_resized{p.suffix}")

    save_format = original_format if original_format in ("JPEG", "PNG") else "JPEG"
    img.save(output_path, format=save_format, quality=90)
    return output_path


def get_image_dimensions(file_path: str) -> Tuple[int, int]:
    """Return (width, height) of an image without loading fully into memory."""
    from PIL import Image

    with Image.open(file_path) as img:
        return img.size


# ---------------------------------------------------------------------------
# Categorization
# ---------------------------------------------------------------------------


def categorize_photo(file_path: str, hint: Optional[str] = None) -> PhotoCategory:
    """Determine the best GBP photo category.

    If ``hint`` is provided (e.g. ``cover``, ``profile``, ``post``), it is
    used directly. Otherwise the function falls back to ``ADDITIONAL``.
    """
    if hint:
        hint_upper = hint.upper()
        try:
            return PhotoCategory(hint_upper)
        except ValueError:
            pass
    return PhotoCategory.ADDITIONAL


# ---------------------------------------------------------------------------
# Upload Pipeline
# ---------------------------------------------------------------------------


def prepare_photo(
    file_path: str,
    company_key: str,
    category_hint: Optional[str] = None,
    auto_resize: bool = True,
) -> Photo:
    """Full preparation pipeline for a single photo.

    1. Validate format (JPG/PNG).
    2. Validate size (10 KB - 5 MB).
    3. Categorize (COVER / PROFILE / ADDITIONAL / POST).
    4. Optionally resize to platform spec.
    5. Return a ``Photo`` model ready for upload.
    """
    fmt, size = validate_photo(file_path)
    category = categorize_photo(file_path, hint=category_hint)

    final_path = file_path
    width, height = get_image_dimensions(file_path)

    spec = PHOTO_SPECS.get(category.value, {})
    needs_resize = (
        auto_resize
        and spec
        and (width != spec.get("width") or height != spec.get("height"))
    )
    if needs_resize:
        final_path = resize_photo(file_path, category)
        width, height = get_image_dimensions(final_path)
        size = Path(final_path).stat().st_size

    return Photo(
        company_key=company_key,
        category=category,
        media_format=fmt,
        local_path=final_path,
        width=width,
        height=height,
        size_bytes=size,
    )


def upload_photo_to_location(
    client,  # GBPClient
    location_name: str,
    file_path: str,
    company_key: str,
    category_hint: Optional[str] = None,
    auto_resize: bool = True,
) -> Photo:
    """End-to-end: validate, resize, categorize, and upload a photo.

    Args:
        client: A ``GBPClient`` instance.
        location_name: GBP resource name for the target location.
        file_path: Path to the image file on disk.
        company_key: Registry key of the owning company.
        category_hint: Optional category hint (``cover``, ``profile``, etc.).
        auto_resize: Whether to auto-resize to platform spec.

    Returns:
        A ``Photo`` model with the upload result.
    """
    photo = prepare_photo(
        file_path,
        company_key,
        category_hint=category_hint,
        auto_resize=auto_resize,
    )
    uploaded = client.upload_photo(
        location_name,
        photo.local_path,
        category=photo.category.value,
    )
    # Merge local metadata into the upload result
    uploaded.company_key = company_key
    uploaded.width = photo.width
    uploaded.height = photo.height
    uploaded.media_format = photo.media_format
    return uploaded
