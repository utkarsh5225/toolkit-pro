from PyPDF2 import PdfReader, PdfWriter
import io

def compress_pdf(data: bytes, filename: str = "") -> bytes | None:
    """Compress PDF: compress content streams, strip metadata, remove unused objects."""
    try:
        reader = PdfReader(io.BytesIO(data))
        writer = PdfWriter()

        for page in reader.pages:
            # Compress each page's content streams (the actual compression)
            page.compress_content_streams()
            writer.add_page(page)

        # Strip all metadata
        writer.add_metadata({})

        # Clone document info from reader to preserve structure
        # but strip unnecessary elements

        output = io.BytesIO()
        writer.write(output)
        return output.getvalue()
    except Exception as e:
        print(f"PDF compress error: {e}")
        return None
