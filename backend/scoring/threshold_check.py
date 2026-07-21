"""
Deterministic threshold checker — the "let the computer do the math" alternative
to backend.llm.ollama_client.classify() for criteria that reduce to a plain
number comparison (e.g. "minimum 10% discount", "at least 3 years experience").

Exists because Llama 3.2 3B was empirically found (M8 testing) to reliably
extract the right numbers from text but then draw the wrong conclusion from
them — consistently, even at temperature=0. Extraction is one thing to trust
a small model with; the actual comparison never should be, so this module
does the comparison in plain Python instead and is never wrong.

Try this first. If it returns None, the text doesn't cleanly reduce to a
number comparison — fall back to the LLM classifier for qualitative judgment.
"""
import re
from dataclasses import dataclass

# Keyword must be within ~30 non-terminator characters of the number, so
# "minimum discount of 10%" matches but an unrelated "Maximum Retail Price"
# elsewhere in the same sentence (as in real GeM clauses) doesn't falsely
# trigger a maximum-direction match.
_MIN_PATTERN = re.compile(
    r"(?:minimum|at least|not less than|no less than)(?:[^.%]{0,30}?)(\d+(?:\.\d+)?)\s*%",
    re.IGNORECASE,
)
_MAX_PATTERN = re.compile(
    r"(?:maximum|at most|not more than|no more than|up to)(?:[^.%]{0,30}?)(\d+(?:\.\d+)?)\s*%",
    re.IGNORECASE,
)
_PERCENT_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*%")


@dataclass
class ThresholdCheckResult:
    verdict: str  # "pass" | "fail"
    reasoning: str


def check_percentage_threshold(rule_text: str, subject_text: str) -> ThresholdCheckResult | None:
    """Returns None if this doesn't look like a clean percentage-threshold
    rule — caller should fall back to the LLM classifier in that case."""
    min_match = _MIN_PATTERN.search(rule_text)
    max_match = _MAX_PATTERN.search(rule_text)

    if min_match and not max_match:
        threshold = float(min_match.group(1))
        direction = "minimum"
    elif max_match and not min_match:
        threshold = float(max_match.group(1))
        direction = "maximum"
    else:
        return None  # no direction keyword found, or ambiguous — bail to LLM

    subject_match = _PERCENT_PATTERN.search(subject_text)
    if not subject_match:
        return None  # no number in the subject text to compare against

    actual = float(subject_match.group(1))

    if direction == "minimum":
        passed = actual >= threshold
        symbol = ">=" if passed else "<"
    else:
        passed = actual <= threshold
        symbol = "<=" if passed else ">"

    verdict = "pass" if passed else "fail"
    reasoning = f"Rule requires {direction} {threshold}%; subject states {actual}% ({actual}{symbol}{threshold}) -> {verdict}"
    return ThresholdCheckResult(verdict=verdict, reasoning=reasoning)


if __name__ == "__main__":
    # The exact case that broke the LLM classifier at M8 — proves this fixes it.
    rule = (
        "xi. Sellers shall offer minimum discount of 10% on the Maximum Retail Price (MRP) "
        "mandatorily on GeM Marketplace (unless otherwise specified)."
    )
    subject = "The bidder has offered a 12% discount on MRP for all listed products."

    result = check_percentage_threshold(rule, subject)
    print(result)
    assert result is not None, "should have matched — check the regex"
    assert "10.0%" in result.reasoning, f"threshold extraction is wrong: {result.reasoning!r}"
    assert "12.0%" in result.reasoning, f"actual-value extraction is wrong: {result.reasoning!r}"
    assert result.verdict == "pass", f"expected pass, got {result.verdict}"

    # A case where the correct answer is genuinely "fail" — proves the
    # verdict isn't just trivially right regardless of what's extracted.
    failing_subject = "The bidder has offered a 5% discount on MRP for all listed products."
    fail_result = check_percentage_threshold(rule, failing_subject)
    print(fail_result)
    assert fail_result is not None
    assert fail_result.verdict == "fail", f"expected fail, got {fail_result.verdict}"

    print("\nCorrect — deterministic check gets both cases right where the LLM did not.")
