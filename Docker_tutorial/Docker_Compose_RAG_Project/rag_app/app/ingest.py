"""Load the example .txt files into Chroma using the independent embedding API.

Run INSIDE the RAG app container:
    docker compose exec rag-app python -m app.ingest
"""
import hashlib
import os
from pathlib import Path

from .core import split_text
from .services import embed_texts, wait_for_services

DOCS_DIR = Path(os.getenv("DOCS_DIR", "/documents"))


def main():
    collection = wait_for_services()
    paths = sorted(DOCS_DIR.glob("*.txt"))
    if not paths:
        raise SystemExit(f"No .txt files found in {DOCS_DIR}")

    records = []
    for path in paths:
        for index, chunk in enumerate(split_text(path.read_text(encoding="utf-8"))):
            records.append((
                hashlib.sha256(f"{path.name}:{index}:{chunk}".encode()).hexdigest(),
                chunk,
                {"source": path.name, "chunk": index},
            ))

    # Restrict batch sizes to stay within the embedding service's 32-text limit.
    batch_size = 16
    for start in range(0, len(records), batch_size):
        batch = records[start:start + batch_size]
        contents = [item[1] for item in batch]
        vectors = embed_texts(contents)
        collection.upsert(
            ids=[item[0] for item in batch],
            documents=contents,
            metadatas=[item[2] for item in batch],
            embeddings=vectors,
        )

    print(f"Ingested {len(records)} text chunks from {len(paths)} documents.")
    print(f"Chroma collection '{collection.name}' has {collection.count()} records.")
    print("Ingestion complete. Open http://localhost:8501 to ask questions.")


if __name__ == "__main__":
    main()
