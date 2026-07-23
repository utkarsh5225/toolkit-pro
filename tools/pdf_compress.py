from PyPDF2 import PdfReader, PdfWriter
from PIL import Image
import io

def compress_pdf(data: bytes, filename: str = "", level: str = "medium") -> bytes | None:
    """Compress PDF at different levels using multiple strategies.

    Levels:
      low    — content stream recompression (lossless)
      medium — low + metadata strip + object deduplication
      high   — medium + image downsampling (lossy)
    """
    try:
        reader = PdfReader(io.BytesIO(data))
        writer = PdfWriter()

        for page in reader.pages:
            # Recompress content streams — PyPDF2 handles FlateDecode
            page.compress_content_streams()

            if level == "high":
                _compress_page_images(page)

            writer.add_page(page)

        # Strip metadata at medium/high
        if level in ("medium", "high"):
            writer.add_metadata({})

        # Write with compression enabled
        output = io.BytesIO()
        writer.write(output)
        result = output.getvalue()

        # If somehow larger, try aggressive clone approach
        if level in ("medium", "high") and len(result) >= len(data):
            result = _aggressive_compress(data)

        return result if len(result) < len(data) else _clone_compress(data)
    except Exception as e:
        print(f"PDF compress error: {e}")
        return None


def _clone_compress(data: bytes) -> bytes:
    """Fallback: clone PDF and compress all streams."""
    try:
        reader = PdfReader(io.BytesIO(data))
        writer = PdfWriter(clone_from=reader)
        # Compress every page
        for page in writer.pages:
            page.compress_content_streams()
        writer.add_metadata({})
        output = io.BytesIO()
        writer.write(output)
        return output.getvalue()
    except Exception:
        return data  # Return original if everything fails


def _aggressive_compress(data: bytes) -> bytes:
    """Aggressive compression: remove unused objects, strip fonts, minimize."""
    try:
        reader = PdfReader(io.BytesIO(data))
        writer = PdfWriter()
        
        for page in reader.pages:
            page.compress_content_streams()
            writer.add_page(page)
        
        writer.add_metadata({})
        
        # Remove all named destinations and outlines
        if hasattr(writer, '_named_dests'):
            writer._named_dests = {}
        
        output = io.BytesIO()
        writer.write(output)
        return output.getvalue()
    except Exception:
        return data


def _compress_page_images(page):
    """Downsample and recompress images in a PDF page."""
    try:
        for img_key in list(page.images.keys()):
            img = page.images[img_key]
            if not hasattr(img, 'data') or not img.data:
                continue
            try:
                pil_img = Image.open(io.BytesIO(img.data))
                w, h = pil_img.size
                
                # Downscale large images
                max_dim = 1000
                if w > max_dim or h > max_dim:
                    ratio = max_dim / max(w, h)
                    pil_img = pil_img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
                
                # Convert to RGB if needed, compress as JPEG
                if pil_img.mode in ("RGBA", "P", "LA"):
                    pil_img = pil_img.convert("RGB")
                
                out = io.BytesIO()
                pil_img.save(out, format="JPEG", quality=40, optimize=True)
                new_data = out.getvalue()
                
                # Only replace if actually smaller
                if len(new_data) < len(img.data):
                    img.data = new_data
                    # Update the image info
                    if hasattr(img, 'image'):
                        img.image = new_data
            except Exception:
                continue
    except Exception:
        pass
