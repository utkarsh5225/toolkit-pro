from PyPDF2 import PdfReader, PdfWriter
import io

def compress_pdf(data: bytes, filename: str = "") -> bytes | None:
    """Compress PDF by removing metadata and optimizing content."""
    try:
        reader = PdfReader(io.BytesIO(data))
        writer = PdfWriter()
        
        for page in reader.pages:
            writer.add_page(page)
        
        # Strip metadata
        writer.add_metadata({})
        
        output = io.BytesIO()
        writer.write(output)
        return output.getvalue()
    except Exception as e:
        print(f"PDF compress error: {e}")
        return None
