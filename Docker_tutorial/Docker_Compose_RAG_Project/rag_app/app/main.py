"""A minimal FastAPI RAG app with a tiny static browser UI."""
import logging
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from openai import APIError

from .core import format_context
from .services import embed_texts, get_chroma_collection, generate_answer

logger = logging.getLogger(__name__)
app = FastAPI(title="Simple Docker RAG")
INDEX_HTML = Path(__file__).resolve().parent.parent / "static" / "index.html"


class Question(BaseModel):
    question: str = Field(min_length=1, max_length=1000)


@app.get("/")
def home():
    return FileResponse(INDEX_HTML)


@app.get("/health")
def health():
    return {"status": "ok", "service": "rag-app"}


@app.get("/stats")
def stats():
    try:
        return {"documents": get_chroma_collection().count()}
    except Exception:
        logger.exception("Failed to read Chroma stats")
        raise HTTPException(status_code=503, detail="ChromaDB is unavailable")


@app.post("/ask")
def ask(payload: Question):
    try:
        collection = get_chroma_collection()
        count = collection.count()
        if count == 0:
            raise HTTPException(status_code=409, detail="Knowledge base is empty. Run the ingest command from README.")
        embedding = embed_texts([payload.question])[0]
        result = collection.query(
            query_embeddings=[embedding],
            n_results=min(3, count),
            include=["documents", "metadatas", "distances"],
        )
        docs = (result.get("documents") or [[]])[0]
        metadata = (result.get("metadatas") or [[]])[0]
        sources = [item.get("source", "unknown") if item else "unknown" for item in metadata]
        context = format_context(docs, sources)
        answer = generate_answer(payload.question, context)
        return {"answer": answer, "sources": sorted(set(sources)), "matches": len(docs)}
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except APIError as exc:
        logger.exception("LLM provider returned HTTP error (%s)", exc.status_code)
        raise HTTPException(status_code=502, detail="LLM provider rejected the request. Check API key, model and quota.") from exc
    except Exception as exc:
        logger.exception("RAG request failed")
        raise HTTPException(status_code=503, detail="RAG service request failed; check docker compose logs.") from exc
