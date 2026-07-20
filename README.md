# RFP Sentinel

A RAG-based bid-evaluation co-pilot for GeM Technical Evaluators (Electronics category) — the buyer/evaluator side of government procurement, not the bidder-response side that every commercial RFP tool already covers.

## Status

Phase 1 in progress: building the knowledge base (norm-document ingestion pipeline). See `ROADMAP.md` for what's deferred to later versions.

## Stack

Llama 3.2 3B + nomic-embed-text (Ollama, local) · Qdrant · Postgres · LangGraph · FastAPI · Streamlit

## Local setup

1. Copy `.env.example` to `.env`.
2. `docker compose up -d` — brings up Qdrant and Postgres.
3. Ensure Ollama is running locally with `llama3.2:3b` and `nomic-embed-text` pulled.
4. `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`

Run scripts as modules from the repo root, e.g. `python -m ingestion.ingest_norms` — this keeps imports between `ingestion/` and `backend/` working without needing the project installed as a package.
