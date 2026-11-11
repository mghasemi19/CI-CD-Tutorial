"""Connections to the embedding microservice, Chroma, and the LLM API."""
import os
import time
import httpx
import chromadb
from openai import OpenAI

COLLECTION_NAME = "tutorial_documents"
EMBEDDING_URL = os.getenv("EMBEDDING_URL", "http://embeddings:8001").rstrip("/")
CHROMA_HOST = os.getenv("CHROMA_HOST", "chroma")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))


def embed_texts(texts: list[str]) -> list[list[float]]:
    with httpx.Client(timeout=90.0) as client:
        response = client.post(f"{EMBEDDING_URL}/embed", json={"texts": texts})
        response.raise_for_status()
        data = response.json()
    vectors = data["embeddings"]
    if len(vectors) != len(texts):
        raise RuntimeError("Embedding service returned unexpected vector count")
    return vectors


def get_chroma_collection():
    # HTTP, not a local PersistentClient: the database lives in ANOTHER container.
    client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
    # Vectors are normalized, making L2 and cosine ranking equivalent.
    # We supply embeddings explicitly for add/upsert/query, so Chroma does not
    # need to download or run its own embedding model.
    return client.get_or_create_collection(name=COLLECTION_NAME)


def wait_for_services(retries: int = 30, delay: float = 2.0):
    for attempt in range(retries):
        try:
            with httpx.Client(timeout=5.0) as client:
                client.get(f"{EMBEDDING_URL}/health").raise_for_status()
            collection = get_chroma_collection()
            return collection
        except (httpx.HTTPError, ConnectionError, RuntimeError, ValueError):
            if attempt == retries - 1:
                raise
            time.sleep(delay)


def generate_answer(question: str, context: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_MODEL", "").strip()
    base_url = os.getenv("OPENAI_BASE_URL", "").strip()
    if not api_key or api_key == "replace-with-your-api-key" or not model:
        raise ValueError("Configure OPENAI_API_KEY and OPENAI_MODEL in the .env file")

    client = OpenAI(
        api_key=api_key,
        base_url=base_url or None,
        timeout=45.0,
        max_retries=1,
    )
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": (
                "You are a helpful assistant answering questions about a small tutorial knowledge base. "
                "Use ONLY the supplied context. If the context doesn't contain the answer, "
                "say you don't know based on these documents. Never invent a source. "
                "Answer concisely and mention relevant source file names."
            )},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ],
    )
    answer = response.choices[0].message.content
    if not answer:
        raise RuntimeError("The LLM returned an empty answer")
    return answer
