from PyPDF2 import PdfReader, PdfWriter
from PIL import Image
import io, subprocess, os, shutil

GS_PATHS = [
    r"C:\Program Files\gs\gs10.04.0\bin\gswin64c.exe",
    r"C:\Program Files\gs\gs10.03.0\bin\gswin64c.exe",
    r"C:\Program Files\gs\gs10.02.0\bin\gswin64c.exe",
    r"C:\Program Files\gs\gs9.55.0\bin\gswin64c.exe",
    "gswin64c", "gs",
]

def _find_gs() -> str | None:
    for p in GS_PATHS:
        if os.path.exists(p) or shutil.which(p):
            return p if os.path.exists(p) else shutil.which(p)
    return None


def compress_pdf(data: bytes, filename: str = "", level: str = "medium") -> bytes | None:
    """Compress PDF at different levels.

    Levels:
      low    — content stream recompression (lossless, minimal)
      medium — low + metadata strip + object dedup
      high   — Ghostscript /ebook preset (maximum, lossy)
    """
    try:
        # High: use Ghostscript for real compression
        if level == "high":
            gs = _find_gs()
            if gs:
                result = _gs_compress(gs, data)
                if result and len(result) < len(data):
                    return result
            # Fall through to PyPDF2 if GS fails

        # Low & Medium: PyPDF2-based
        reader = PdfReader(io.BytesIO(data))
        writer = PdfWriter()

        for page in reader.pages:
            page.compress_content_streams()
            if level == "high":
                _compress_page_images(page)
            writer.add_page(page)

        if level in ("medium", "high"):
            writer.add_metadata({})

        output = io.BytesIO()
        writer.write(output)
        result = output.getvalue()

        if len(result) >= len(data) and level != "low":
            result = _clone_compress(data)

        return result if len(result) < len(data) else _clone_compress(data)
    except Exception as e:
        print(f"PDF compress error: {e}")
        return None


def _gs_compress(gs_path: str, data: bytes) -> bytes | None:
    """Use Ghostscript to aggressively compress PDF. /ebook = 150dpi images."""
    try:
        proc = subprocess.run(
            [gs_path, "-q", "-dNOPAUSE", "-dBATCH", "-dSAFER",
             "-sDEVICE=pdfwrite",
             "-dCompatibilityLevel=1.4",
             "-dPDFSETTINGS=/ebook",
             "-dEmbedAllFonts=true",
             "-dSubsetFonts=true",
             "-dColorImageDownsampleType=/Bicubic",
             "-dColorImageResolution=150",
             "-dGrayImageDownsampleType=/Bicubic",
             "-dGrayImageResolution=150",
             "-dMonoImageDownsampleType=/Bicubic",
             "-dMonoImageResolution=150",
             "-sOutputFile=%stdout", "-"],
            input=data, capture_output=True, timeout=60)
        if proc.returncode == 0 and proc.stdout:
            return proc.stdout
    except Exception as e:
        print(f"Ghostscript error: {e}")
    return None


def _clone_compress(data: bytes) -> bytes:
    """Fallback: clone and recompress all streams."""
    try:
        reader = PdfReader(io.BytesIO(data))
        writer = PdfWriter(clone_from=reader)
        for page in writer.pages:
            page.compress_content_streams()
        writer.add_metadata({})
        out = io.BytesIO()
        writer.write(out)
        return out.getvalue()
    except Exception:
        return data


def _compress_page_images(page):
    """Downsample images (fallback when no Ghostscript)."""
    try:
        for img_key in list(page.images.keys()):
            img = page.images[img_key]
            if not hasattr(img, 'data') or not img.data:
                continue
            try:
                pil_img = Image.open(io.BytesIO(img.data))
                w, h = pil_img.size
                if w > 1000 or h > 1000:
                    r = 1000 / max(w, h)
                    pil_img = pil_img.resize((int(w*r), int(h*r)), Image.LANCZOS)
                if pil_img.mode in ("RGBA", "P", "LA"):
                    pil_img = pil_img.convert("RGB")
                out = io.BytesIO()
                pil_img.save(out, format="JPEG", quality=40, optimize=True)
                if len(out.getvalue()) < len(img.data):
                    img.data = out.getvalue()
            except Exception:
                continue
    except Exception:
        pass
