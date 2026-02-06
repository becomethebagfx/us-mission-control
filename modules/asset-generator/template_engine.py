"""
Visual Asset Generator - Template Engine
HTML/CSS template loading with Jinja2 variable injection and Pillow rendering.
"""

import textwrap
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from PIL import Image, ImageDraw, ImageFont

from config import (
    BRAND_PALETTES,
    FONT_BODY_FALLBACK,
    FONT_HEADING_FALLBACK,
    TEMPLATES_DIR,
    get_brand,
)


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color string to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def get_contrast_color(hex_color: str) -> str:
    """Return white or dark text based on background luminance."""
    r, g, b = hex_to_rgb(hex_color)
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return "#FFFFFF" if luminance < 0.5 else "#1B2A4A"


class TemplateEngine:
    """Loads HTML/CSS templates with Jinja2, renders via Pillow fallback."""

    def __init__(self, templates_dir: Optional[Path] = None):
        self.templates_dir = templates_dir or TEMPLATES_DIR
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=True,
        )

    def render_html(self, template_name: str, variables: dict[str, str]) -> str:
        """Render an HTML template with Jinja2 variable injection.

        Args:
            template_name: Name of the HTML template file.
            variables: Dict of template variables to inject.

        Returns:
            Rendered HTML string.

        Raises:
            TemplateNotFound: If the template file does not exist.
        """
        template = self.env.get_template(template_name)
        return template.render(**variables)

    def inject_brand(self, company_key: str, variables: dict[str, str]) -> dict[str, str]:
        """Inject brand palette colors into template variables.

        Args:
            company_key: Company identifier (e.g., 'us_framing').
            variables: Existing template variables to augment.

        Returns:
            Variables dict with brand colors injected.
        """
        brand = get_brand(company_key)
        injected = {
            "company_name": brand["name_full"],
            "company_short": brand["name_short"],
            "primary_color": brand["primary"],
            "accent_color": brand["accent"],
            "text_light": brand["text_light"],
            "text_dark": brand["text_dark"],
            "font_heading": brand["font_heading"],
            "font_body": brand["font_body"],
        }
        injected.update(variables)
        return injected

    def render_to_image(
        self,
        template_type: str,
        company_key: str,
        variables: dict[str, str],
        width: int = 1200,
        height: int = 627,
        output_path: Optional[Path] = None,
    ) -> Image.Image:
        """Render a template to an image using Pillow.

        Creates a branded image with text overlays on a solid color background.
        This is the primary rendering path -- no browser/Playwright needed.

        Args:
            template_type: One of project_showcase, social_quote, stat_card, company_header.
            company_key: Company identifier for brand injection.
            variables: Template-specific variables.
            width: Output image width in pixels.
            height: Output image height in pixels.
            output_path: Optional path to save the image.

        Returns:
            PIL Image object.
        """
        brand = get_brand(company_key)
        merged = self.inject_brand(company_key, variables)

        primary_rgb = hex_to_rgb(brand["primary"])
        accent_rgb = hex_to_rgb(brand["accent"])
        text_light_rgb = hex_to_rgb(brand["text_light"])

        img = Image.new("RGB", (width, height), primary_rgb)
        draw = ImageDraw.Draw(img)

        # Load fonts with fallback
        heading_font = _load_font(FONT_HEADING_FALLBACK, size=int(height * 0.08))
        body_font = _load_font(FONT_BODY_FALLBACK, size=int(height * 0.045))
        small_font = _load_font(FONT_BODY_FALLBACK, size=int(height * 0.035))
        large_font = _load_font(FONT_HEADING_FALLBACK, size=int(height * 0.18))

        # Accent bar at top
        bar_height = max(int(height * 0.015), 4)
        draw.rectangle([(0, 0), (width, bar_height)], fill=accent_rgb)

        # Accent bar at bottom
        draw.rectangle([(0, height - bar_height), (width, height)], fill=accent_rgb)

        # Route to template-specific layout
        if template_type == "project_showcase":
            _render_project_showcase(
                draw, merged, width, height, heading_font, body_font, small_font,
                text_light_rgb, accent_rgb,
            )
        elif template_type == "social_quote":
            _render_social_quote(
                draw, merged, width, height, heading_font, body_font, small_font,
                text_light_rgb, accent_rgb,
            )
        elif template_type == "stat_card":
            _render_stat_card(
                draw, merged, width, height, large_font, body_font, small_font,
                text_light_rgb, accent_rgb,
            )
        elif template_type == "company_header":
            _render_company_header(
                draw, merged, width, height, heading_font, body_font, small_font,
                text_light_rgb, accent_rgb,
            )
        else:
            # Generic fallback -- just render title text centered
            title = merged.get("title", merged.get("company_name", ""))
            _draw_centered_text(draw, title, heading_font, text_light_rgb, width, height // 2)

        # Company watermark in bottom-right
        company_short = merged.get("company_short", "")
        if company_short:
            watermark_font = _load_font(FONT_BODY_FALLBACK, size=int(height * 0.03))
            bbox = draw.textbbox((0, 0), company_short, font=watermark_font)
            tw = bbox[2] - bbox[0]
            draw.text(
                (width - tw - int(width * 0.03), height - int(height * 0.06)),
                company_short,
                font=watermark_font,
                fill=accent_rgb,
            )

        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(str(output_path), "PNG", quality=95)

        return img

    def list_templates(self) -> list[str]:
        """List available HTML template files."""
        if not self.templates_dir.exists():
            return []
        return [f.name for f in self.templates_dir.glob("*.html")]


# ──────────────────────────────────────────────────────────────
# Private Rendering Helpers
# ──────────────────────────────────────────────────────────────


def _load_font(font_name: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load a font with graceful fallback to default."""
    try:
        return ImageFont.truetype(font_name, size)
    except (OSError, IOError):
        try:
            return ImageFont.truetype(f"{font_name}.ttf", size)
        except (OSError, IOError):
            return ImageFont.load_default()


def _draw_centered_text(
    draw: ImageDraw.Draw,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    fill: tuple[int, int, int],
    canvas_width: int,
    y: int,
) -> None:
    """Draw text horizontally centered at a given y position."""
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    x = (canvas_width - tw) // 2
    draw.text((x, y), text, font=font, fill=fill)


def _wrap_text(text: str, max_chars: int = 40) -> list[str]:
    """Wrap text into lines of max_chars width."""
    return textwrap.wrap(text, width=max_chars)


def _render_project_showcase(
    draw: ImageDraw.Draw,
    variables: dict[str, str],
    width: int,
    height: int,
    heading_font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    body_font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    small_font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    text_color: tuple[int, int, int],
    accent_color: tuple[int, int, int],
) -> None:
    """Render project showcase layout."""
    padding_x = int(width * 0.08)
    y_cursor = int(height * 0.12)

    # "PROJECT COMPLETE" label
    draw.text((padding_x, y_cursor), "PROJECT COMPLETE", font=small_font, fill=accent_color)
    y_cursor += int(height * 0.07)

    # Project name
    project_name = variables.get("project_name", "Project Name")
    draw.text((padding_x, y_cursor), project_name, font=heading_font, fill=text_color)
    y_cursor += int(height * 0.14)

    # Divider line
    draw.line(
        [(padding_x, y_cursor), (width - padding_x, y_cursor)],
        fill=accent_color,
        width=2,
    )
    y_cursor += int(height * 0.06)

    # Stats row
    stats_data = [
        ("SQFT", variables.get("sqft", "N/A")),
        ("TIMELINE", variables.get("timeline", "N/A")),
        ("LOCATION", variables.get("location", "N/A")),
    ]
    col_width = (width - 2 * padding_x) // len(stats_data)
    for i, (label, value) in enumerate(stats_data):
        x = padding_x + i * col_width
        draw.text((x, y_cursor), label, font=small_font, fill=accent_color)
        draw.text((x, y_cursor + int(height * 0.05)), value, font=body_font, fill=text_color)

    # Company name at bottom
    company_name = variables.get("company_name", "")
    _draw_centered_text(draw, company_name, body_font, text_color, width, height - int(height * 0.12))


def _render_social_quote(
    draw: ImageDraw.Draw,
    variables: dict[str, str],
    width: int,
    height: int,
    heading_font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    body_font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    small_font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    text_color: tuple[int, int, int],
    accent_color: tuple[int, int, int],
) -> None:
    """Render social quote card layout."""
    padding_x = int(width * 0.10)
    y_cursor = int(height * 0.15)

    # Opening quotation mark
    quote_mark_font = _load_font(FONT_HEADING_FALLBACK, size=int(height * 0.20))
    draw.text((padding_x, y_cursor - int(height * 0.05)), "\u201C", font=quote_mark_font, fill=accent_color)
    y_cursor += int(height * 0.12)

    # Quote text (wrapped)
    quote_text = variables.get("quote_text", "Quote text here")
    max_chars = max(int(width / 22), 20)
    lines = _wrap_text(quote_text, max_chars=max_chars)
    for line in lines:
        draw.text((padding_x, y_cursor), line, font=body_font, fill=text_color)
        y_cursor += int(height * 0.06)

    y_cursor += int(height * 0.04)

    # Accent divider
    divider_width = int(width * 0.15)
    draw.line(
        [(padding_x, y_cursor), (padding_x + divider_width, y_cursor)],
        fill=accent_color,
        width=3,
    )
    y_cursor += int(height * 0.05)

    # Attribution
    author = variables.get("quote_author", "")
    role = variables.get("quote_role", "")
    if author:
        draw.text((padding_x, y_cursor), author, font=body_font, fill=text_color)
        y_cursor += int(height * 0.05)
    if role:
        draw.text((padding_x, y_cursor), role, font=small_font, fill=accent_color)


def _render_stat_card(
    draw: ImageDraw.Draw,
    variables: dict[str, str],
    width: int,
    height: int,
    large_font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    body_font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    small_font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    text_color: tuple[int, int, int],
    accent_color: tuple[int, int, int],
) -> None:
    """Render stat/infographic card layout."""
    # Large stat value centered
    stat_value = variables.get("stat_value", "0")
    _draw_centered_text(draw, stat_value, large_font, accent_color, width, int(height * 0.22))

    # Stat label below
    stat_label = variables.get("stat_label", "")
    _draw_centered_text(draw, stat_label.upper(), body_font, text_color, width, int(height * 0.52))

    # Description
    stat_desc = variables.get("stat_description", "")
    if stat_desc:
        lines = _wrap_text(stat_desc, max_chars=50)
        y = int(height * 0.65)
        for line in lines:
            _draw_centered_text(draw, line, small_font, text_color, width, y)
            y += int(height * 0.05)

    # Company name
    company_name = variables.get("company_name", "")
    _draw_centered_text(draw, company_name, small_font, text_color, width, height - int(height * 0.10))


def _render_company_header(
    draw: ImageDraw.Draw,
    variables: dict[str, str],
    width: int,
    height: int,
    heading_font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    body_font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    small_font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    text_color: tuple[int, int, int],
    accent_color: tuple[int, int, int],
) -> None:
    """Render company header/banner layout."""
    # Accent stripe on left side
    stripe_width = int(width * 0.015)
    draw.rectangle([(0, 0), (stripe_width, height)], fill=accent_color)

    # Company name centered
    company_name = variables.get("company_name", "")
    _draw_centered_text(draw, company_name, heading_font, text_color, width, int(height * 0.30))

    # Tagline below
    tagline = variables.get("tagline", "")
    if tagline:
        _draw_centered_text(draw, tagline, body_font, accent_color, width, int(height * 0.55))

    # Bottom accent stripe
    draw.rectangle(
        [(0, height - stripe_width), (width, height)],
        fill=accent_color,
    )
