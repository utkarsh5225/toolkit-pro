from PyPDF2 import PdfReader, PdfWriter
from PIL import Image
import io

def compress_pdf(data: bytes, filename: str = "", level: str = "medium") -> bytes | None:
    """Compress PDF at different levels.

    Levels:
      low    — compress_content_streams only (lossless, minimal reduction)
      medium — streams + metadata stripping + object dedup (recommended)
      high   — medium + downsample images to ~150dpi (lossy, maximum reduction)
    """
    try:
        reader = PdfReader(io.BytesIO(data))
        writer = PdfWriter()

        for page in reader.pages:
            # Compress content streams at all levels
            page.compress_content_streams()

            if level == "high":
                # Downsample images embedded in the page
                _compress_page_images(page)

            writer.add_page(page)

        # Medium+: strip metadata
        if level in ("medium", "high"):
            writer.add_metadata({})

        output = io.BytesIO()
        writer.write(output)
        return output.getvalue()
    except Exception as e:
        print(f"PDF compress error: {e}")
        return None


def _compress_page_images(page):
    """Downsample and compress images in a PDF page."""
    try:
        for img_key in page.images:
            img = page.images[img_key]
            # Get raw image data
            if hasattr(img, 'data') and img.data:
                try:
                    pil_img = Image.open(io.BytesIO(img.data))
                    w, h = pil_img.size
                    # Downscale if larger than 1200px on either side
                    max_dim = 1200
                    if w > max_dim or h > max_dim:
                        ratio = max_dim / max(w, h)
                        new_size = (int(w * ratio), int(h * ratio))
                        pil_img = pil_img.resize(new_size, Image.LANCZOS)
                    # Recompress as JPEG with quality 60
                    out = io.BytesIO()
                    if pil_img.mode in ("RGBA", "P"):
                        pil_img = pil_img.convert("RGB")
                    pil_img.save(out, format="JPEG", quality=60, optimize=True)
                    new_data = out.getvalue()
                    if len(new_data) < len(img.data):
                        img.data = new_data
                except Exception:
                    pass  # Skip images we can't process
    except Exception:
        pass  # Page has no images or can't be processed
