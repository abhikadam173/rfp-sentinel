"""
M2 verification: confirm Ollama is reachable, has llama3.2:3b and nomic-embed-text
pulled, and that both models actually work — a real generate call and a real
embedding call, not just checking they're listed.

Run from the repo root: venv/bin/python -m scripts.verify_env
"""
import os

import requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("OLLAMA_LLM_MODEL", "llama3.2:3b")
EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")


def verify_models_pulled() -> None:
    resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
    resp.raise_for_status()
    names = {m["name"] for m in resp.json()["models"]}

    for model in (LLM_MODEL, EMBED_MODEL):
        # Ollama tags carry a ":latest"/":3b" suffix that a bare name like "nomic-embed-text" won't match
        found = model in names or any(n.startswith(f"{model}:") for n in names)
        assert found, f"{model} not found in pulled models: {names}"
    print(f"Ollama: OK — {LLM_MODEL} and {EMBED_MODEL} are both pulled.")


def verify_generate() -> None:
    resp = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json={"model": LLM_MODEL, "prompt": "Reply with the single word: OK", "stream": False},
        timeout=60,
    )
    resp.raise_for_status()
    text = resp.json()["response"]
    assert text.strip(), "Empty response from generate call"
    print(f"Ollama generate: OK — model responded ({len(text)} chars): {text.strip()[:80]!r}")


def verify_embeddings() -> None:
    resp = requests.post(
        f"{OLLAMA_BASE_URL}/api/embeddings",
        json={"model": EMBED_MODEL, "prompt": "test embedding call"},
        timeout=30,
    )
    resp.raise_for_status()
    vector = resp.json()["embedding"]
    assert len(vector) > 0, "Empty embedding vector"
    print(f"Ollama embeddings: OK — got a {len(vector)}-dimensional vector.")


if __name__ == "__main__":
    verify_models_pulled()
    verify_generate()
    verify_embeddings()
    print("\nOllama is reachable and both models work.")
