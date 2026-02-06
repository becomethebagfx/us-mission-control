"""
Visual Asset Generator - Platform Sizer
Resize images for all 8 platform dimensions with proper cropping and safe zones.
"""

from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw

from config import OUTPUT_DIR, PLATFORM_SIZES


def resize_for_platform(
    source_path: str | Path,
    platform_key: str,
    output_dir: Optional[Path] = None,
    maintain_aspect: bool = True,
    add_safe_zone: bool = True,
    safe_zone_pct: float = 0.10,
) -> Path:
    """Resize an image for a specific platform.

    Uses center-crop to maintain aspect ratio. Optionally adds safe zone
    padding to keep text away from edges.

    Args:
        source_path: Path to the source image.
        platform_key: Platform identifier (e.g., 'linkedin_post').
        output_dir: Directory to save the resized image.
        maintain_aspect: If True, center-crop to fit. If False, stretch.
        add_safe_zone: If True, inset content by safe_zone_pct.
        safe_zone_pct: Percentage of each dimension for safe zone (0.10 = 10%).

    Returns:
        Path to the resized image file.

    Raises:
        FileNotFoundError: If source image does not exist.
        KeyError: If platform_key is not valid.
    """
    source_path = Path(source_path)
    if not source_path.exists():
        raise FileNotFoundError(f"Source image not found: {source_path}")

    if platform_key not in PLATFORM_SIZES:
        valid = ", ".join(PLATFORM_SIZES.keys())
        raise KeyError(f"Unknown platform '{platform_key}'. Valid keys: {valid}")

    platform = PLATFORM_SIZES[platform_key]
    target_w = platform["width"]
    target_h = platform["height"]

    img = Image.open(source_path)
    src_w, src_h = img.size

    if maintain_aspect:
        img = _center_crop_resize(img, target_w, target_h)
    else:
        img = img.resize((target_w, target_h), Image.LANCZOS)

    out_dir = output_dir or OUTPUT_DIR / "resized"
    out_dir.mkdir(parents=True, exist_ok=True)

    stem = source_path.stem
    filename = f"{stem}_{platform_key}_{target_w}x{target_h}.png"
    output_path = out_dir / filename

    img.save(str(output_path), "PNG", quality=95)
    return output_path


def resize_for_all_platforms(
    source_path: str | Path,
    output_dir: Optional[Path] = None,
    skip_platforms: Optional[list[str]] = None,
) -> dict[str, Path]:
    """Resize an image for all configured platforms.

    Args:
        source_path: Path to the source image.
        output_dir: Directory to save resized images.
        skip_platforms: Optional list of platform keys to skip.

    Returns:
        Dict mapping platform_key to output file path.
    """
    skip = set(skip_platforms or [])
    results = {}

    for platform_key in PLATFORM_SIZES:
        if platform_key in skip:
            continue
        output_path = resize_for_platform(
            source_path=source_path,
            platform_key=platform_key,
            output_dir=output_dir,
        )
        results[platform_key] = output_path

    return results


def get_safe_zone(width: int, height: int, pct: float = 0.10) -> dict[str, int]:
    """Calculate safe zone boundaries for text placement.

    Returns the inner rectangle where text should be placed to avoid
    being clipped by platform UI elements.

    Args:
        width: Image width in pixels.
        height: Image height in pixels.
        pct: Safe zone percentage (0.10 = 10% padding on each side).

    Returns:
        Dict with left, top, right, bottom pixel boundaries.
    """
    pad_x = int(width * pct)
    pad_y = int(height * pct)
    return {
        "left": pad_x,
        "top": pad_y,
        "right": width - pad_x,
        "bottom": height - pad_y,
        "inner_width": width - 2 * pad_x,
        "inner_height": height - 2 * pad_y,
    }


def visualize_safe_zones(
    width: int,
    height: int,
    pct: float = 0.10,
    output_path: Optional[Path] = None,
) -> Image.Image:
    """Create a visualization of safe zones for a given dimension.

    Draws the safe zone boundary as a dashed rectangle overlay.

    Args:
        width: Image width.
        height: Image height.
        pct: Safe zone percentage.
        output_path: Optional path to save the visualization.

    Returns:
        PIL Image with safe zone visualization.
    """
    img = Image.new("RGB", (width, height), (40, 40, 60))
    draw = ImageDraw.Draw(img)

    zone = get_safe_zone(width, height, pct)

    # Draw safe zone rectangle
    draw.rectangle(
        [(zone["left"], zone["top"]), (zone["right"], zone["bottom"])],
        outline=(100, 200, 100),
        width=2,
    )

    # Draw corner markers
    marker_len = min(width, height) // 20
    corners = [
        (zone["left"], zone["top"]),
        (zone["right"], zone["top"]),
        (zone["left"], zone["bottom"]),
        (zone["right"], zone["bottom"]),
    ]
    for cx, cy in corners:
        draw.line([(cx - marker_len, cy), (cx + marker_len, cy)], fill=(255, 100, 100), width=2)
        draw.line([(cx, cy - marker_len), (cx, cy + marker_len)], fill=(255, 100, 100), width=2)

    # Draw center crosshair
    center_x, center_y = width // 2, height // 2
    draw.line([(center_x - 10, center_y), (center_x + 10, center_y)], fill=(200, 200, 200), width=1)
    draw.line([(center_x, center_y - 10), (center_x, center_y + 10)], fill=(200, 200, 200), width=1)

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(output_path), "PNG")

    return img


def _center_crop_resize(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """Resize image to target dimensions using center-crop strategy.

    First scales the image so the smaller dimension matches the target,
    then crops from the center to achieve exact dimensions.

    Args:
        img: Source PIL Image.
        target_w: Target width in pixels.
        target_h: Target height in pixels.

    Returns:
        Resized and cropped PIL Image.
    """
    src_w, src_h = img.size
    target_ratio = target_w / target_h
    src_ratio = src_w / src_h

    if src_ratio > target_ratio:
        # Source is wider -- scale to target height, crop width
        scale_h = target_h
        scale_w = int(src_w * (target_h / src_h))
    else:
        # Source is taller -- scale to target width, crop height
        scale_w = target_w
        scale_h = int(src_h * (target_w / src_w))

    img = img.resize((scale_w, scale_h), Image.LANCZOS)

    # Center crop
    left = (scale_w - target_w) // 2
    top = (scale_h - target_h) // 2
    right = left + target_w
    bottom = top + target_h

    return img.crop((left, top, right, bottom))


def list_platform_sizes() -> list[dict[str, str | int]]:
    """List all platform sizes with their dimensions.

    Returns:
        List of dicts with name, key, width, height.
    """
    sizes = []
    for key, info in PLATFORM_SIZES.items():
        sizes.append({
            "key": key,
            "name": info["name"],
            "width": info["width"],
            "height": info["height"],
        })
    return sizes


if __name__ == "__main__":
    print("Available platform sizes:")
    for size in list_platform_sizes():
        print(f"  {size['key']}: {size['name']} ({size['width']}x{size['height']})")
