"""
M9: check_rfp_compliance() -- for every extracted criterion, decide whether
it conflicts with government norms, before the buyer sees the RFP as final.

Tries the deterministic threshold checker first (never wrong, for criteria
that reduce to a number comparison); only falls back to the LLM classifier
for genuinely qualitative judgment. See backend/scoring/threshold_check.py
and backend/llm/ollama_client.py for why, and Current Progress in the plan
for the M8 finding that made this two-tool design necessary.
"""
import sys
from pathlib import Path

from backend.llm.ollama_client import ReferenceChunk, classify
from backend.models.rfp import Criterion, StructuredRFP
from backend.rag.embeddings import embed_text
from backend.rag.qdrant_client import get_client, search_active

_VERDICT_OPTIONS = ["compliant", "violation", "unclear"]
_INSTRUCTION = (
    "Does the criterion below conflict with the referenced government norm clause(s)? "
    "Classify it as compliant, violation, or unclear. "
    "Use 'violation' ONLY if the reference material describes a requirement that directly "
    "contradicts or is incompatible with the criterion. If the reference material simply does "
    "not mention this specific criterion at all, that is 'unclear', not 'violation' -- the "
    "absence of a matching rule is not the same as breaking one."
)


def check_rfp_compliance(structured_rfp: StructuredRFP) -> StructuredRFP:
    client = get_client()

    for criterion in structured_rfp.criteria:
        query_vector = embed_text(criterion.text)
        matches = search_active(client, query_vector, top_k=2)  # kept small -- long prompts were timing out
        if not matches:
            continue  # nothing relevant found -- leave unflagged, not a false violation

        references = [
            ReferenceChunk(
                text=m.payload["text"],
                citation={
                    "norm_name": m.payload["norm_name"],
                    "clause_ref": m.payload.get("clause_ref"),
                    "page_number": m.payload["page_number"],
                },
            )
            for m in matches
        ]

        # Try deterministic first -- only the top match, since threshold_check
        # needs one rule text to compare against, not several candidates.
        threshold_result = None
        top_match = matches[0]
        try:
            from backend.scoring.threshold_check import check_percentage_threshold
            threshold_result = check_percentage_threshold(top_match.payload["text"], criterion.text)
        except ImportError:
            pass

        if threshold_result is not None:
            if threshold_result.verdict == "fail":
                criterion.compliance_issue = threshold_result.reasoning
                criterion.compliance_citation = references[0].citation
            continue  # deterministic answer found -- skip the LLM entirely

        result = classify(
            subject_text=criterion.text[:600],  # long clauses were making prompts too slow
            references=references,
            verdict_options=_VERDICT_OPTIONS,
            instruction=_INSTRUCTION,
        )
        # An uncited "violation" isn't a grounded finding -- it's the model
        # guessing without support from the retrieved norm text. Never
        # surface a compliance flag that can't be traced to a real citation.
        if result.verdict == "violation" and result.citation is not None:
            criterion.compliance_issue = result.reasoning
            criterion.compliance_citation = result.citation

    return structured_rfp


if __name__ == "__main__":
    from backend.graph.extract_rfp_criteria import extract_rfp_criteria

    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/rfps/Gem Bid Document.pdf")
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 6  # keep it fast -- first N criteria only

    rfp = extract_rfp_criteria(path, rfp_id="test-rfp-1")
    rfp.criteria = rfp.criteria[:n]
    rfp = check_rfp_compliance(rfp)

    flagged = [c for c in rfp.criteria if c.compliance_issue]
    print(f"{len(rfp.criteria)} criteria checked, {len(flagged)} flagged\n")
    for c in rfp.criteria:
        status = "FLAGGED" if c.compliance_issue else "ok"
        print(f"[{c.clause_ref}] {status}")
        if c.compliance_issue:
            print(f"  issue: {c.compliance_issue}")
            print(f"  citation: {c.compliance_citation}")
        print()
