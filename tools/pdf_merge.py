from PyPDF2 import PdfReader, PdfWriter
import io

def merge_pdfs(files: list[tuple[bytes, str]]) -> bytes | None:
    """Merge multiple PDFs into one."""
    try:
        writer = PdfWriter()
        
        for data, filename in files:
            reader = PdfReader(io.BytesIO(data))
            for page in reader.pages:
                writer.add_page(page)
        
        output = io.BytesIO()
        writer.write(output)
        return output.getvalue()
    except Exception as e:
        print(f"PDF merge error: {e}")
        return None
