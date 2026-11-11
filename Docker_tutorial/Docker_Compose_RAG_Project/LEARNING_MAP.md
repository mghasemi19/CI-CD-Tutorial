# One question: trace the full request

After you have indexed your text documents, ask:

> What is the difference between a Docker image and a container?

1. **Browser** (`rag_app/static/index.html`) sends `POST /ask` with JSON to `http://localhost:8501`.
2. **RAG app** (`rag_app/app/main.py`) checks that Chroma has documents.
3. **RAG app** (`rag_app/app/services.py`) sends the question to `http://embeddings:8001/embed`.
4. **Embedding service** (`embedding_service/main.py`) converts text to a 384D vector; returns JSON.
5. **RAG app** queries **Chroma** (`chroma:8000`) using the vector, requesting the top 3 document chunks.
6. **Chroma** returns text and source metadata saved by `app.ingest`.
7. **RAG app** formats those passages as context and calls the external OpenAI-compatible Chat Completions API.
8. **RAG app** returns the answer and source filenames as JSON.
9. **Browser** displays the result.

## Distinguish the 3 services from the external LLM

| Component | In Docker Compose? | Own image? | Needs outbound internet after first setup? |
|---|---|---|---|
| `embeddings` | Yes | Built from `embedding_service/Dockerfile` | Normally no; needs access for first model download |
| `chroma` | Yes | Pulled `chromadb/chroma:1.5.3` | Normally no |
| `rag-app` | Yes | Built from `rag_app/Dockerfile` | Yes, when calling LLM |
| OpenAI-compatible LLM | No | No image in this project | External API |

## Beginner exercise

Enter the RAG container:

```bash
docker compose exec rag-app sh
```

Try running these commands:

```sh
python -c "import httpx; print(httpx.get('http://embeddings:8001/health').json())"
python -c "import chromadb; print(chromadb.HttpClient(host='chroma',port=8000).heartbeat())"
```

Now try `http://localhost:8001` *from inside the container*. It will not reach the embedding service, because `localhost` points to the **RAG app container**, not the embeddings container.
