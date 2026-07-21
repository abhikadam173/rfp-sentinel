"""
M6: convert chunk text into embedding vectors using nomic-embed-text via
Ollama — this is "the translator": text in, a list of 768 numbers out.
"""
import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")


def embed_text(text: str) -> list[float]:
    resp = requests.post(
        f"{OLLAMA_BASE_URL}/api/embeddings",
        json={"model": EMBED_MODEL, "prompt": text},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["embedding"]


def embed_texts(texts: list[str]) -> list[list[float]]:
    """One call per chunk, sequentially — no GPU here, so keeping memory
    use predictable matters more than the speed a batched call might give."""
    return [embed_text(t) for t in texts]


if __name__ == "__main__":
    samples = [
        "The Seller shall offer a minimum discount of 10% on MRP.",
        "Micro and Small Enterprises are eligible for tender exemptions.",
    ]
    vectors = embed_texts(samples)
    for text, vector in zip(samples, vectors):
        print(f"{len(vector)}-dim vector for: {text[:60]!r}")
        print(f"first 5 values: {vector[:5]}\n")
