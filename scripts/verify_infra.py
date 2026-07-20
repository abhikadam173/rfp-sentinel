"""
M1 verification: confirm Qdrant and Postgres are actually reachable and usable,
not just that the containers report "Up". Writes and reads a throwaway record
in each, then cleans up.

Run from the repo root: venv/bin/python -m scripts.verify_infra
"""
import os

from dotenv import load_dotenv

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
POSTGRES_URL = os.getenv(
    "POSTGRES_URL", "postgresql://rfp_sentinel:rfp_sentinel@localhost:5432/rfp_sentinel"
)


def verify_qdrant() -> None:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, PointStruct, VectorParams

    client = QdrantClient(url=QDRANT_URL)
    test_collection = "_verify_infra_test"

    if client.collection_exists(test_collection):
        client.delete_collection(test_collection)
    client.create_collection(
        collection_name=test_collection,
        vectors_config=VectorParams(size=4, distance=Distance.COSINE),
    )
    client.upsert(
        collection_name=test_collection,
        points=[PointStruct(id=1, vector=[0.1, 0.2, 0.3, 0.4], payload={"check": "ok"})],
    )
    result = client.retrieve(collection_name=test_collection, ids=[1])
    assert result and result[0].payload["check"] == "ok", "Qdrant round-trip failed"

    client.delete_collection(test_collection)
    print("Qdrant: OK — wrote and read back a test point.")


def verify_postgres() -> None:
    import psycopg2

    conn = psycopg2.connect(POSTGRES_URL)
    try:
        with conn.cursor() as cur:
            cur.execute("CREATE TABLE IF NOT EXISTS _verify_infra_test (id INT, note TEXT);")
            cur.execute("INSERT INTO _verify_infra_test (id, note) VALUES (1, 'ok');")
            cur.execute("SELECT note FROM _verify_infra_test WHERE id = 1;")
            (note,) = cur.fetchone()
            assert note == "ok", "Postgres round-trip failed"
            cur.execute("DROP TABLE _verify_infra_test;")
        conn.commit()
    finally:
        conn.close()
    print("Postgres: OK — wrote and read back a test row.")


if __name__ == "__main__":
    verify_qdrant()
    verify_postgres()
    print("\nBoth Qdrant and Postgres are reachable and working.")
