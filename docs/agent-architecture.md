# Agent Architecture — RFP Sentinel

*How many agents, what each one does, what tools it uses, and how they connect.*

---

## 1. The count: 1 real agent today, 2 more designed but not yet built, 1 deliberate non-agent

| # | Name | Status |
|---|---|---|
| 1 | RFP Criteria Extraction | **Not an agent, as shipped** — pure regex/keyword rules, zero LLM calls. See §2. |
| 2 | RFP Compliance Agent | **Yes — built, tested, and running.** The one real agent in the system today. |
| 3 | Bid Evidence Extraction Agent | **Designed, not yet built.** Deferred milestone (bid upload/evaluation). Would reuse Agent 2's exact tool pattern. |
| — | Deterministic Scoring Engine | **No** — fixed formula, no tools, no judgment (deliberately) |

The bar for calling something an "agent" here isn't "it's a step in the pipeline" — it's **does it use more than one tool, and does its output change depending on what it discovers, rather than always computing the same thing.** Only the compliance-check step genuinely does that today. Extraction was originally *designed* to be agentic (see below) but shipped as plain rule-based code under time pressure — worth being upfront about that distinction rather than overclaiming three agents when one is live.

---

## 2. RFP Criteria Extraction (`extract_rfp_criteria`) — currently NOT an agent

**Job**: turn an uploaded RFP PDF into a clean list of structured, checkable criteria.

**How it actually works, as shipped**: the same PDF extraction/chunking pipeline (`extract_text.py`, `extract_tables.py`, `language_filter.py`, `chunker.py`) already proven on norm documents pulls out clause-shaped chunks. Each surviving chunk (clause reference present, 15+ words) becomes a `Criterion`, classified by two independent keyword-regex checks — **no LLM call anywhere in this step**:
- `mandatory`: contains an "optional"-type word (may/optional/at the discretion) and no "mandatory"-type word (shall/must/required) → `False`; otherwise defaults `True`.
- `category`: contains a money-related word (turnover/EMD/price/₹/lakh/crore/...) → `"financial"`, else → `"eligibility"`. (`"technical"` exists in the data model but the current rules never produce it.)

**Why it's not an agent today**: it doesn't use more than one tool, and it doesn't make a judgment that varies based on what it discovers — it's a fixed filter plus two if/else keyword checks. Always the same regex, regardless of content.

**The originally intended design** (not yet built): real RFPs split key facts across two places — a **table** holds the actual number (e.g. "minimum turnover: ₹139 Lakh"), while separate **prose** clauses explain how to apply it (e.g. "MSE/Startup bidders are exempted"). An LLM step reading both and synthesizing one complete criterion would be smarter and would be a genuine agent (tool use: retrieval of both chunk types + an LLM call; judgment: what to combine). This was deliberately deferred — extraction already works well enough on real test data (33 real criteria from `data/rfps/Gem Bid Document.pdf`) without the added latency and reliability risk of a new, untested LLM call in this step. Worth upgrading once there's time to test it the way `ollama_client.py` was tested.

**Output**: a plain Python `list[Criterion]` (text, mandatory flag, category, page number, clause ref) — serialized to a JSON array, stored inside LangGraph's Postgres checkpoint, and returned as-is by `GET /rfp/{id}/criteria`.

---

## 3. The real agent — RFP Compliance Check (`check_rfp_compliance`)

**Job**: for every extracted criterion, decide whether it conflicts with government norms — *before* the buyer ever sees the RFP as final.

**Tools it uses**:
1. **Search** (`search_active()`) — retrieves the norm clauses relevant to this specific criterion, filtered to only currently-active regulations.
2. **The deterministic threshold checker** (`threshold_check.py`) — for criteria that reduce to a plain number comparison (e.g. "minimum 10% discount").
3. **The LLM classifier** (`ollama_client.classify`) — for criteria that need real reading/understanding rather than arithmetic (e.g. does an exemption clause apply here).

**The decision it makes**: for each criterion, it first decides *which tool even applies* — is this a number-comparison case, or does it need real judgment? — then produces a verdict: `compliant` / `violation` / `unclear`, with a citation pointing at the exact norm clause behind that verdict.

**Why two different tools (#2 and #3) instead of just the LLM for everything**: testing found Llama 3.2 3B reliably extracts the right numbers from text but consistently draws the *wrong conclusion* from them — even at zero randomness, it correctly said "12 is bigger than 10" and then still concluded "fail" against a *minimum* of 10. Since that failure was reproducible and didn't respond to two rounds of prompt fixes, numeric comparisons got moved to plain, always-correct Python code instead — the same "determinism over cleverness" principle already used for the final scoring engine, just applied one step earlier.

**Output**: each criterion gets two new fields — `compliance_issue` (what's wrong, if anything) and `compliance_citation` (which norm clause backs that up) — feeding directly into **Checkpoint A**, where the buyer reviews flagged criteria and fixes or overrides them before proceeding.

---

## 4. Bid Evidence Extraction (`retrieve_and_extract_evidence`) — designed, not yet built

**Status**: this is the next deferred milestone (bid upload/evaluation) — no code exists for it yet. Described here as the intended design, reusing what's already proven, not as something you can currently demo.

**Job**: for every bidder's uploaded document, check it against every criterion the buyer already approved.

**Tools it would use**: the same three-tool pattern as the compliance-check agent, just pointed at a bid instead of an RFP — bid-specific search (filtered to one `bid_id`, so bids never leak into each other's results), the same deterministic threshold checker, the same LLM classifier.

**The decision it would make**: for each (bid, criterion) pair, retrieve the bid's relevant content, decide which tool applies, and produce a verdict: `pass` / `fail` / `partial` / `not_found`, with a citation (which page/section of the bid supports it). `not_found` would be treated as a distinct, legitimate outcome — not a bug — since it means nothing relevant was retrieved, which is different from actively failing a stated requirement.

**Output (planned)**: an `EvidenceItem` per (bid, criterion), feeding into the deterministic scoring engine.

---

## 5. The Deterministic Scoring Engine — deliberately not an agent

**Job**: turn all the `EvidenceItem` verdicts into a ranked shortlist.

**No tools. No LLM. No judgment calls.** Every input always produces the exact same output:
- **Stage 1 (technical gate)**: any mandatory criterion marked `fail` → the bid is out, full stop. This mirrors GeM's actual pass/fail gate.
- **Stage 2 (financial ranking)**: Stage-1-passed bids get ranked either by lowest price (**L1**) or a weighted blend of technical score and price (**QCBS**, default 70/30 split) — both plain arithmetic.
- **Shortlist**: the top 5 ranked bids, each carrying its full evidence trail for the human reviewer.

This feeds into **Checkpoint B**, where the evaluator confirms the shortlist — the system never auto-selects a winner.

---

## 6. Full flow, agents and checkpoints together

```
RFP PDF uploaded
      │
      ▼
Criteria Extraction (NOT an agent — regex/keyword rules only)  ──uses──▶  PDF pipeline
      │
      ▼
[Real agent] Compliance Check  ──uses──▶  Search + Threshold Checker + LLM Classifier
      │
      ▼
◆ CHECKPOINT A (human) — buyer reviews flagged criteria, approves/edits          ◀── built & working today
════════════════════════ everything below is designed, not yet built ════════════════════════
      │
      ▼
Bidder PDF(s) uploaded
      │
      ▼
[Planned agent] Evidence Extraction  ──uses──▶  Search + Threshold Checker + LLM Classifier
      │
      ▼
Deterministic Scoring Engine (not an agent) — Stage 1 gate → Stage 2 rank → Top-5
      │
      ▼
◆ CHECKPOINT B (human) — evaluator confirms shortlist
      │
      ▼
Confirmed shortlist + full audit trail
```

**LangGraph's role in this**: it's the conductor, not a worker — it calls each agent in order, passes state between them, and — critically — pauses the entire flow at both checkpoints (potentially for hours or days) and resumes exactly where it left off once a human responds. This pause/resume-later capability is why LangGraph specifically was chosen, not built by hand.

---

## 7. Quick answer for an interview

> "Criteria extraction is plain rule-based code today — regex and keyword checks, no LLM, chosen deliberately for speed and reliability under time pressure. The one real agent in the system is the RFP compliance check: for every extracted criterion it retrieves the relevant government rule via vector search, then picks between a deterministic checker for plain number comparisons and an LLM classifier for judgments that need real reading comprehension — that tool choice, plus a verdict that depends on what's actually retrieved, is what makes it an agent rather than a fixed function. Bid evidence extraction is designed to reuse that exact same pattern but isn't built yet. The final ranking step is deliberately *not* an agent either — it's a plain formula, because an AI-computed score isn't defensible in a government audit. LangGraph coordinates all of it and owns the human checkpoint, pausing the pipeline until a person approves or edits something."

If pushed on why the LLM isn't trusted with number comparisons: *"Testing showed the model reliably identifies the right numbers but consistently draws the wrong conclusion from them — even with zero randomness. Rather than trying to prompt-engineer around a known, reproducible model weakness, we moved that comparison to plain code, which is never wrong, and kept the LLM for what it's actually suited to: reading and judgment calls that can't be reduced to arithmetic."*
