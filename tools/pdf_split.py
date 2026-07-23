from PyPDF2 import PdfReader, PdfWriter
import io

def parse_page_ranges(pages_str: str, total_pages: int) -> list[int]:
    """Parse page ranges like '1-3,5,7-9' into 0-indexed page numbers."""
    pages = set()
    for part in pages_str.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start, end = part.split("-", 1)
            for p in range(int(start), int(end) + 1):
                if 1 <= p <= total_pages:
                    pages.add(p - 1)
        else:
            try:
                p = int(part)
                if 1 <= p <= total_pages:
                    pages.add(p - 1)
            except ValueError:
                continue
    return sorted(pages)

def split_pdf(data: bytes, pages_str: str) -> bytes | None:
    """Split PDF to only include specified pages."""
    try:
        reader = PdfReader(io.BytesIO(data))
        total = len(reader.pages)
        
        if not pages_str.strip():
            # No page selection = return all pages (no-op)
            return data
        
        page_indices = parse_page_ranges(pages_str, total)
        if not page_indices:
            return None
        
        writer = PdfWriter()
        for idx in page_indices:
            writer.add_page(reader.pages[idx])
        
        output = io.BytesIO()
        writer.write(output)
        return output.getvalue()
    except Exception as e:
        print(f"PDF split error: {e}")
        return None
