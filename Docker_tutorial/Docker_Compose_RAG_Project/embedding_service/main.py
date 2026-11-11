"""A separate HTTP service for SentenceTransformers embeddings."""
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer

MODEL_NAME = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
# The first startup downloads model files; the /models volume caches them.
model = SentenceTransformer(MODEL_NAME, device="cpu")

app = FastAPI(title="Embedding service")


class EmbeddingRequest(BaseModel):
    texts: list[str] = Field(min_length=1, max_length=32)


@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL_NAME}


@app.post("/embed")
def embed(request: EmbeddingRequest):
    if any(not text.strip() or len(text) > 4000 for text in request.texts):
        raise HTTPException(status_code=422, detail="Each text must contain 1–4000 characters.")
    vectors = model.encode(request.texts, convert_to_numpy=True, normalize_embeddings=True)
    return {"embeddings": vectors.tolist(), "dimension": int(vectors.shape[1])}
