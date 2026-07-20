"""
M3: extract per-page text from a PDF using pdfplumber.

extract_text_by_page() is the sole seam where an OCR fallback would slot in
later — if a page's extracted text comes back empty (a scanned image page),
that's the trigger point for it, not implemented in v1.
"""
import sys
from dataclasses import dataclass
from pathlib import Path

import pdfplumber


@dataclass
class PageText:
    page_number: int
    text: str


def extract_text_by_page(pdf_path: Path) -> list[PageText]:
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            pages.append(PageText(page_number=i, text=text))
    return pages


if __name__ == "__main__":
    path = Path(sys.argv[1])
    for page in extract_text_by_page(path):
        print(f"--- page {page.page_number} ({len(page.text)} chars) ---")
        print(page.text[:500])
        print()
