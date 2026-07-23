"""Text tools — server-side processing for text operations."""

def count_words(text: str) -> dict:
    words = text.split()
    chars = len(text)
    chars_no_spaces = len(text.replace(" ", "").replace("\n", "").replace("\t", ""))
    lines = text.count("\n") + 1 if text else 0
    return {
        "words": len(words),
        "chars": chars,
        "chars_no_spaces": chars_no_spaces,
        "lines": lines,
    }

def convert_case(text: str, case_type: str) -> str:
    if case_type == "upper":
        return text.upper()
    elif case_type == "lower":
        return text.lower()
    elif case_type == "title":
        return text.title()
    elif case_type == "sentence":
        return ". ".join(s.capitalize() for s in text.split(". "))
    return text
