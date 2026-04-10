"""Image processing utilities for mandato profile pictures."""
from __future__ import annotations

from io import BytesIO

from PIL import Image

PROFILE_SIZE = 400
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


def resize_and_crop(file_bytes: bytes, content_type: str) -> bytes:
    """Center-crop then resize image to PROFILE_SIZE x PROFILE_SIZE JPEG.

    Args:
        file_bytes: Raw bytes of the uploaded image.
        content_type: MIME type of the uploaded file (e.g. ``image/jpeg``).

    Returns:
        JPEG-encoded bytes of the 400×400 result.

    Raises:
        ValueError: If the content type is not supported.
        OSError: If Pillow cannot open/decode the image.
    """
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise ValueError(
            f"Tipo de imagem não suportado: {content_type!r}. "
            f"Permitidos: {', '.join(sorted(ALLOWED_CONTENT_TYPES))}"
        )

    img = Image.open(BytesIO(file_bytes))

    # Convert to RGB so JPEG encoding always works (drops alpha channel)
    if img.mode != "RGB":
        img = img.convert("RGB")

    w, h = img.size
    side = min(w, h)

    # Center crop to square
    left = (w - side) // 2
    top = (h - side) // 2
    img = img.crop((left, top, left + side, top + side))

    # Resize to target dimensions with high-quality downsampling
    img = img.resize((PROFILE_SIZE, PROFILE_SIZE), Image.LANCZOS)

    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85, optimize=True)
    return buf.getvalue()
