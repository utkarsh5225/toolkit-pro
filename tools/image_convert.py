from PIL import Image
import io

MIME_MAP = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
}

FORMAT_MAP = {
    "jpg": "JPEG",
    "jpeg": "JPEG",
    "png": "PNG",
    "webp": "WEBP",
}

def convert_image(data: bytes, target_format: str) -> tuple[bytes | None, str]:
    """Convert image to target format. Returns (bytes, mime_type)."""
    try:
        img = Image.open(io.BytesIO(data))
        
        # Handle RGBA → RGB for JPEG
        if target_format in ("jpg", "jpeg") and img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        
        pil_format = FORMAT_MAP.get(target_format, "PNG")
        mime = MIME_MAP.get(target_format, "image/png")
        
        output = io.BytesIO()
        img.save(output, format=pil_format)
        return output.getvalue(), mime
    except Exception as e:
        print(f"Image conversion error: {e}")
        return None, ""
