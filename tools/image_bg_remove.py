from PIL import Image
from rembg import remove
import io

def remove_background(data: bytes) -> tuple[bytes | None, str]:
    """Remove background from image using rembg. Returns (bytes, mime_type)."""
    try:
        input_image = Image.open(io.BytesIO(data)).convert("RGBA")
        result = remove(input_image)
        
        output = io.BytesIO()
        result.save(output, format="PNG")
        return output.getvalue(), "image/png"
    except Exception as e:
        print(f"Background removal error: {e}")
        return None, ""
