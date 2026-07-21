"""
M9: extract_rfp_criteria() -- turns an uploaded RFP PDF into a clean list of
structured, checkable criteria.

v1 shortcut, done deliberately under time pressure: mandatory/category are
decided by keyword heuristics, not an LLM call. Fast, no new untested LLM
dependency added today. Worth upgrading to LLM-based extraction later, once
there's time to validate it the way ollama_client.py was -- tracked here,
not hidden.
"""
import re
import sys
from pathlib import Path

from backend.models.rfp import Criterion, StructuredRFP
from ingestion.chunker import chunk_document
from ingestion.extract_tables import extract_tables_by_page
from ingestion.extract_text import PageText, extract_text_by_page
from ingestion.language_filter import filter_english

_MANDATORY_KEYWORDS = re.compile(r"\b(shall|must|mandatory|required|should)\b", re.IGNORECASE)
_OPTIONAL_KEYWORDS = re.compile(r"\b(may|optional|preference|at the discretion)\b", re.IGNORECASE)
_FINANCIAL_KEYWORDS = re.compile(
    r"\b(turnover|emd|price|payment|financial|discount|₹|rs\.|crore|lakh|bank guarantee|security)\b",
    re.IGNORECASE,
)

_MIN_WORDS = 15  # skip tiny fragments that aren't real criteria

# GeM bid PDFs end with a standard disclaimer introducing a numbered list of
# buyer drafting-mistakes ("Incorporating any clause against MSME policy...",
# "Mentioning specific Brand/Make/Model...") -- these are numbered like real
# criteria but describe what the BUYER must not do, not bidder requirements.
# Confirmed against a real GeM bid document (NIELIT) where this exact
# boilerplate phrase introduces that list, right before the closing GTC
# clause/thank-you page. Once seen, everything after it is this same
# guidance content, not real criteria -- heuristic based on the one
# document tested; may need broadening if other RFP templates phrase it
# differently.
_GUIDANCE_SECTION_MARKER = re.compile(
    r"(shall be treated as null and void|prohibited practices|do'?s and don'?ts)",
    re.IGNORECASE,
)


def _infer_mandatory(text: str) -> bool:
    if _OPTIONAL_KEYWORDS.search(text) and not _MANDATORY_KEYWORDS.search(text):
        return False
    return True  # default mandatory -- safer to over-flag for human review than silently drop


def _infer_category(text: str) -> str:
    return "financial" if _FINANCIAL_KEYWORDS.search(text) else "eligibility"


def extract_rfp_criteria(pdf_path: Path, rfp_id: str) -> StructuredRFP:
    pages = extract_text_by_page(pdf_path)
    pages = [PageText(p.page_number, filter_english(p.text)) for p in pages]
    tables = extract_tables_by_page(pdf_path)
    chunks = chunk_document(pages, tables)

    criteria = []
    in_guidance_section = False
    for i, chunk in enumerate(chunks):
        if chunk.chunk_type != "prose":
            continue
        if _GUIDANCE_SECTION_MARKER.search(chunk.text):
            in_guidance_section = True
        if in_guidance_section:
            continue
        if chunk.clause_ref is None:
            continue
        if len(chunk.text.split()) < _MIN_WORDS:
            continue

        criteria.append(Criterion(
            id=f"{rfp_id}_c{i}",
            text=chunk.text,
            mandatory=_infer_mandatory(chunk.text),
            category=_infer_category(chunk.text),
            page_number=chunk.page_number,
            clause_ref=chunk.clause_ref,
        ))

    return StructuredRFP(rfp_id=rfp_id, source_file=pdf_path.name, criteria=criteria)


if __name__ == "__main__":
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/rfps/Gem Bid Document.pdf")
    result = extract_rfp_criteria(path, rfp_id="test-rfp-1")
    print(f"{len(result.criteria)} criteria extracted from {path.name}\n")
    for c in result.criteria:
        print(f"[{c.clause_ref}] mandatory={c.mandatory} category={c.category} (page {c.page_number})")
        print(f"  {c.text[:150]}")
        print()
