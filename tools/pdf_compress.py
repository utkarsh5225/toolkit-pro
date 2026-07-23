from PyPDF2 import PdfReader, PdfWriter
from PIL import Image
import io, subprocess, os, shutil

GS_PATHS = [
    r"C:\Program Files\gs\gs10.04.0\bin\gswin64c.exe",
    r"C:\Program Files\gs\gs10.03.0\bin\gswin64c.exe",
    r"C:\Program Files\gs\gs10.02.0\bin\gswin64c.exe",
    "gswin64c", "gs",
]

# Quality → Ghostscript preset mapping
# Higher % = more compression, lower quality
QUALITY_PRESETS = {
    (0, 20):   "prepress",   # ~300dpi, lossless
    (21, 50):  "printer",    # ~300dpi, moderate
    (51, 80):  "ebook",      # ~150dpi, good compression
    (81, 100): "screen",     # ~72dpi, max compression
}


def _find_gs() -> str | None:
    for p in GS_PATHS:
        if os.path.exists(p) or shutil.which(p):
            return p if os.path.exists(p) else shutil.which(p)
    return None


def _quality_to_preset(quality: int) -> str:
    """Map percentage quality (0-100) to Ghostscript PDFSETTINGS."""
    for (lo, hi), preset in QUALITY_PRESETS.items():
        if lo <= quality <= hi:
            return preset
    return "ebook"  # default


def compress_pdf(data: bytes, filename: str = "", quality: int = 50) -> bytes | None:
    """Compress PDF — quality slider 0-100 (higher = smaller file, lower quality).

    0-20%  → /prepress  (300dpi, near-lossless)
    20-50% → /printer   (300dpi, moderate)
    50-80% → /ebook     (150dpi, good — default)
    80-100% → /screen   (72dpi, maximum compression)
    """
    try:
        gs = _find_gs()
        if gs:
            preset = _quality_to_preset(quality)
            result = _gs_compress(gs, data, preset)
            if result and len(result) < len(data):
                return result

        # PyPDF2 fallback if no GS or GS enlarged
        reader = PdfReader(io.BytesIO(data))
        writer = PdfWriter()

        for page in reader.pages:
            page.compress_content_streams()
            writer.add_page(page)

        writer.add_metadata({})
        output = io.BytesIO()
        writer.write(output)
        result = output.getvalue()

        if len(result) >= len(data):
            return _clone_compress(data)
        return result

    except Exception as e:
        print(f"PDF compress error: {e}")
        return None


def _gs_compress(gs_path: str, data: bytes, preset: str = "ebook") -> bytes | None:
    """Ghostscript compression with given preset."""
    try:
        proc = subprocess.run(
            [gs_path, "-q", "-dNOPAUSE", "-dBATCH", "-dSAFER",
             "-sDEVICE=pdfwrite",
             "-dCompatibilityLevel=1.4",
             f"-dPDFSETTINGS=/{preset}",
             "-dEmbedAllFonts=true",
             "-dSubsetFonts=true",
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
        writer = PdfWriter()
        for page in reader.pages:
            page.compress_content_streams()
            writer.add_page(page)
        writer.add_metadata({})
        out = io.BytesIO()
        writer.write(out)
        return out.getvalue()
    except Exception:
        return data
