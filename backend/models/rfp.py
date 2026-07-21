"""
M9: the shapes extract_rfp_criteria() and check_rfp_compliance() work with.
"""
from pydantic import BaseModel


class Criterion(BaseModel):
    id: str
    text: str
    mandatory: bool
    category: str  # "technical" | "financial" | "eligibility"
    page_number: int
    clause_ref: str | None = None
    compliance_issue: str | None = None
    compliance_citation: dict | None = None


class StructuredRFP(BaseModel):
    rfp_id: str
    source_file: str
    category: str = "Electronics"
    evaluation_method: str = "L1"  # "L1" | "QCBS"
    criteria: list[Criterion] = []
