"""
M4: strip Hindi (Devanagari-script) text, keep English. v1 scope only —
multilingual support beyond this strip-and-discard approach is tracked in
ROADMAP.md as a v2+ item.

Approach: character-level removal of the Devanagari Unicode block, rather than
dropping whole lines. Real GeM documents frequently pair a Hindi label and an
English label on the same line/cell (e.g. "बिड विवरण/Bid Details") — a
line-level drop would throw away real English content sitting right next to
the Hindi, not just the Hindi itself.
"""
import re
import sys
from pathlib import Path

DEVANAGARI_START = "ऀ"
DEVANAGARI_END = "ॿ"


def _is_devanagari(ch: str) -> bool:
    return DEVANAGARI_START <= ch <= DEVANAGARI_END


def filter_english(text: str) -> str:
    stripped = "".join(ch for ch in text if not _is_devanagari(ch))

    # Clean up artifacts left behind where Hindi used to sit: dangling "/"
    # separators, doubled-up whitespace, blank lines.
    lines = []
    for line in stripped.splitlines():
        line = re.sub(r"\s*/\s*/\s*", " / ", line)  # "Hindi/English" -> just "English" leaves "/English"... collapse doubled slashes
        line = re.sub(r"^\s*/\s*", "", line)  # leading "/" left when Hindi label was first
        line = re.sub(r"\s*/\s*$", "", line)  # trailing "/" left when Hindi label was last
        line = re.sub(r"[ \t]+", " ", line).strip()
        if line:
            lines.append(line)
    return "\n".join(lines)


if __name__ == "__main__":
    from ingestion.extract_text import extract_text_by_page

    path = Path(sys.argv[1])
    for page in extract_text_by_page(path):
        filtered = filter_english(page.text)
        print(f"--- page {page.page_number} ---")
        print(filtered[:800])
        print()
