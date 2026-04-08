import io
import logging
from PIL import Image
from rembg import remove

logger = logging.getLogger(__name__)


def remove_background(image_bytes: bytes) -> bytes:
    """Remove the background from an image, returning RGBA PNG bytes."""
    return remove(image_bytes)


def resize_for_sticker(image_bytes: bytes, bg_remove: bool = True) -> bytes:
    """
    Process an image for use as a Telegram sticker:
    1. Optionally remove background
    2. Resize so the longest side is 512px
    3. Convert to PNG with transparency
    """
    # Step 1: Remove background if requested
    if bg_remove:
        try:
            image_bytes = remove_background(image_bytes)
        except Exception as e:
            logger.warning(f"Background removal failed, proceeding without it: {e}")

    # Step 2: Open and resize
    img = Image.open(io.BytesIO(image_bytes))
    img = img.convert("RGBA")

    max_side = max(img.size)
    if max_side != 512:
        scale = 512 / max_side
        new_size = (int(img.width * scale), int(img.height * scale))
        img = img.resize(new_size, Image.LANCZOS)

    # Step 3: Save as PNG
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()
