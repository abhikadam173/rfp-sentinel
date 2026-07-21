# Roadmap

Deferred scope, tracked deliberately so it's not forgotten — not a backlog to pull from early.

## Norm data follow-ups (near-term, not blocking current milestone)

- Source and ingest the **MSME Public Procurement Policy (MSEs) Amendment Order, 2018** (Gazette S.O. 5670(E), 9 Nov 2018) as its own document — changes the procurement target from 20% to 25% and adds a 3% women-owned-MSE sub-target, effective 1 April 2019. Currently only the unamended 2012 base order is ingested (flagged in `data/norms/manifest.json`). The copy found during research was a poor-quality OCR scan (page 1's bilingual header extracted as garbled text) — worth finding a cleaner digital-native source, or handling as a v2+ OCR case if not.
- Periodically re-check GeM GTC for a newer version (we caught 1.22 → 1.23 by chance while researching manifest metadata, not via any monitoring — there's no mechanism that would catch this automatically, by design, since the project doesn't crawl/poll GeM's servers).
- Still missing from the original 6-category norm list: GFR 2017 Rule 189, the DPIIT Make-in-India order, a dedicated BIS CRS list.
- **Policy to define later**: once the superseded-status mechanism (keep old norm versions, flip `status` instead of deleting) is actually in use for real evaluations, decide a retention rule for eventually removing old superseded PDFs from the `data/norms/` working folder (Qdrant's superseded *points* stay for audit regardless — this is only about whether the source PDF file itself needs to stick around locally indefinitely).

## v1.1

- Credential-based auth with three roles: Buyer, Admin, Bidder.
- Three dashboards (buyer/evaluator, admin, bidder).
- Bidder self-service upload (6–n bidders per RFP).
- RFP legitimacy check — flags RFP citations to norms with `status != active`.
- Plain-language RFP summary for bidders.

## v2+

- OCR fallback for scanned PDFs (v1 assumes digital-native text).
- Multilingual support beyond the current English-only / Hindi-stripped approach.
- Some GeM-generated PDFs (confirmed in at least one `data/rfps/` "Bid Document") embed Hindi glyphs without a proper Unicode character map — pdfplumber/pdfminer can't decode them at all, so they come out as raw `(cid:N)` placeholders instead of real Devanagari text or even garbled-but-present characters. `language_filter.py`'s Devanagari-codepoint strip can't catch this, since there's no actual Devanagari text to strip — the extraction itself loses that content. Doesn't affect v1 (all 3 real norm PDFs are cleanly encoded), but will surface again at M9 when RFP/bid documents from `data/rfps/` get ingested. Possible v2+ fixes: OCR fallback specifically for pages/cells with unmapped glyphs, or a manual cid-to-glyph lookup table for GeM's specific font.
- LlamaIndex hierarchical chunking / auto-merging retrieval layered under Qdrant.
- More robust auth (JWT/session-based) if the app moves beyond a single local machine.
- LangGraph `Send`-based parallel evidence extraction across bids/criteria.
- Concurrent-evaluator support (Postgres already removes the main blocker).
- Checkpoint B shortlist reordering in the UI (v1 is confirm-only).
- Interview with a real procurement officer for ground-truth validation.
- Presentation-style architecture diagram (interview/viva deliverable).
