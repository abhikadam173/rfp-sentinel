"""
Ask a question against the ingested norms and see what comes back — the same
retrieval step the evidence-extraction agent will use later, for you to
explore by hand.

Run: python -m scripts.query_norms "your question here"
"""
import sys

from backend.rag.embeddings import embed_text
from backend.rag.qdrant_client import get_client, search_active

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python -m scripts.query_norms "your question here"')
        sys.exit(1)

    query = sys.argv[1]
    vector = embed_text(query)
    results = search_active(get_client(), vector, top_k=5)

    print(f'Query: "{query}"\n')
    for r in results:
        payload = r.payload
        print(f"score={r.score:.3f} | {payload['norm_name']} | clause_ref={payload.get('clause_ref')} | page={payload['page_number']}")
        print(payload["text"][:300])
        print()
