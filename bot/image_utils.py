import io
from PIL import Image


def resize_for_sticker(image_bytes: bytes) -> bytes:
    """Resize an image so the longest side is 512px, convert to PNG."""
    img = Image.open(io.BytesIO(image_bytes))
    img = img.convert("RGBA")

    max_side = max(img.size)
    if max_side != 512:
        scale = 512 / max_side
        new_size = (int(img.width * scale), int(img.height * scale))
        img = img.resize(new_size, Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()
