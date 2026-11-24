"""AI-ESCALATE image preprocessing (DESIGN 5.2): status bar cropped, long edge
<= 1,568 px, JPEG q70, EXIF and all other metadata stripped.

Image bytes are content: never log them, never write them to disk.
"""

from __future__ import annotations

import base64
import binascii
import io
import warnings

from PIL import Image, ImageOps

from app.proxy.config import ImageConfig


class ImageInputError(ValueError):
    """The request image could not be decoded. Carries no content."""


def preprocess_image_b64(image_b64: str, cfg: ImageConfig) -> str:
    """Return base64 JPEG ready for an image content block."""
    try:
        raw = base64.b64decode(image_b64, validate=True)
    except (binascii.Error, ValueError):
        raise ImageInputError("image_b64_invalid") from None
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as src:
                if src.width * src.height > cfg.max_source_pixels:
                    raise ImageInputError("image_too_large")
                src.load()
                # Apply the EXIF orientation, then drop every tag (we never pass exif=).
                img = ImageOps.exif_transpose(src)
    except ImageInputError:
        raise
    except (OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise ImageInputError("image_undecodable") from None

    img = img.convert("RGB")
    crop = int(round(img.height * cfg.status_bar_crop_frac))
    if 0 < crop < img.height:
        img = img.crop((0, crop, img.width, img.height))
    long_edge = max(img.width, img.height)
    if long_edge > cfg.long_edge_px:
        scale = cfg.long_edge_px / long_edge
        size = (max(1, round(img.width * scale)), max(1, round(img.height * scale)))
        img = img.resize(size, Image.Resampling.LANCZOS)
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=cfg.jpeg_quality, optimize=True)
    return base64.b64encode(out.getvalue()).decode("ascii")
