# Roadmap

Deferred scope, tracked deliberately so it's not forgotten — not a backlog to pull from early.

## v1.1

- Credential-based auth with three roles: Buyer, Admin, Bidder.
- Three dashboards (buyer/evaluator, admin, bidder).
- Bidder self-service upload (6–n bidders per RFP).
- RFP legitimacy check — flags RFP citations to norms with `status != active`.
- Plain-language RFP summary for bidders.

## v2+

- OCR fallback for scanned PDFs (v1 assumes digital-native text).
- Multilingual support beyond the current English-only / Hindi-stripped approach.
- LlamaIndex hierarchical chunking / auto-merging retrieval layered under Qdrant.
- More robust auth (JWT/session-based) if the app moves beyond a single local machine.
- LangGraph `Send`-based parallel evidence extraction across bids/criteria.
- Concurrent-evaluator support (Postgres already removes the main blocker).
- Checkpoint B shortlist reordering in the UI (v1 is confirm-only).
- Interview with a real procurement officer for ground-truth validation.
- Presentation-style architecture diagram (interview/viva deliverable).
