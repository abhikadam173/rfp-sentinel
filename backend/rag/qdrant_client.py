"""
M6: Qdrant setup and storage — "the filing cabinet". Creates the `norms`
collection with the right structure, saves chunks into it, and provides a
cheap way to flip a norm's status (active/superseded/withdrawn) without
re-processing its PDF.
"""
import os
import sys
import uuid

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PayloadSchemaType,
    PointStruct,
    VectorParams,
)

from ingestion.chunker import Chunk

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
NORMS_COLLECTION = "norms"
VECTOR_SIZE = 768

# Fixed namespace so the same doc_id + chunk_index always produces the same
# point ID — re-running ingestion overwrites existing points instead of
# creating duplicates.
_ID_NAMESPACE = uuid.UUID("a3f1c9d2-4e6b-4a1a-9c3d-8f2b1e6a7c90")


def get_client() -> QdrantClient:
    return QdrantClient(url=QDRANT_URL)


def ensure_norms_collection(client: QdrantClient) -> None:
    if not client.collection_exists(NORMS_COLLECTION):
        client.create_collection(
            collection_name=NORMS_COLLECTION,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
        client.create_payload_index(NORMS_COLLECTION, "status", PayloadSchemaType.KEYWORD)
        client.create_payload_index(NORMS_COLLECTION, "norm_name", PayloadSchemaType.KEYWORD)
        client.create_payload_index(NORMS_COLLECTION, "doc_id", PayloadSchemaType.KEYWORD)


def chunk_point_id(doc_id: str, chunk_index: int) -> str:
    """Deterministic — same inputs always produce the same ID."""
    return str(uuid.uuid5(_ID_NAMESPACE, f"{doc_id}:{chunk_index}"))


def upsert_chunks(
    client: QdrantClient,
    doc_id: str,
    chunks: list[Chunk],
    vectors: list[list[float]],
    doc_metadata: dict,
) -> None:
    """doc_metadata carries the per-document fields that are the same for
    every chunk (source_file, norm_name, status, version, effective_date,
    language) — per-chunk fields (text, page_number, clause_ref, chunk_type)
    come from the chunk itself."""
    points = [
        PointStruct(
            id=chunk_point_id(doc_id, i),
            vector=vector,
            payload={
                "doc_id": doc_id,
                "chunk_type": chunk.chunk_type,
                "page_number": chunk.page_number,
                "clause_ref": chunk.clause_ref,
                "text": chunk.text,
                **doc_metadata,
            },
        )
        for i, (chunk, vector) in enumerate(zip(chunks, vectors))
    ]
    client.upsert(collection_name=NORMS_COLLECTION, points=points)


def mark_status(client: QdrantClient, norm_name: str, new_status: str) -> None:
    """Cheap payload-only update — flips every chunk belonging to a norm to
    a new status (active/superseded/withdrawn) without touching vectors or
    re-reading the PDF. This is the mechanism for 'norm A got disabled.'"""
    client.set_payload(
        collection_name=NORMS_COLLECTION,
        payload={"status": new_status},
        points=Filter(must=[FieldCondition(key="norm_name", match=MatchValue(value=norm_name))]),
    )


def search_active(client: QdrantClient, query_vector: list[float], top_k: int = 5):
    return client.query_points(
        collection_name=NORMS_COLLECTION,
        query=query_vector,
        query_filter=Filter(must=[FieldCondition(key="status", match=MatchValue(value="active"))]),
        limit=top_k,
    ).points


if __name__ == "__main__":
    client = get_client()
    ensure_norms_collection(client)
    print(f"Collection '{NORMS_COLLECTION}' ready.")
    print(f"Example deterministic ID for ('gem-gtc_4.0', 0): {chunk_point_id('gem-gtc_4.0', 0)}")
    print(f"Same inputs again: {chunk_point_id('gem-gtc_4.0', 0)}")
