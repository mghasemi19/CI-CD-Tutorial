# Simple Docker Compose RAG: 3 containers, 1 question-answer app

A deliberately small, working-example RAG project for learning **Docker images, containers, Compose, networking, volumes, and an OpenAI-compatible LLM API**. It uses **only three services**.

> **Training project, not production security guidance.** It has no user authentication. The browser binds to `127.0.0.1` for local use. Never commit `.env` or expose the app publicly without proper controls.

## 1. Understand the architecture

```text
YOUR BROWSER on Windows              DOCKER COMPOSE DEFAULT NETWORK
http://localhost:8501
         |
         | host 8501 --> container 8000
         v
  [rag-app: FastAPI + UI] --------------------------------------> [LLM API on the internet]
         |                         OpenAI-compatible request       (not a container)
         |
         +--- POST http://embeddings:8001/embed ---> [embeddings container]
         |                                            SentenceTransformers
         |                                            all-MiniLM-L6-v2
         |                                            384-number vectors
         |
         +--- chroma:8000 -------------------------> [ChromaDB container]
                                                      |
                                               named volume chroma-data
```

- **rag-app**: serves the tiny HTML user interface on port 8000 *inside* Docker; creates prompts and calls your LLM API.
- **embeddings**: loads the free local SentenceTransformers `all-MiniLM-L6-v2` model on CPU, exposing `/embed` on port 8001 *inside* Docker. It does **not** need a Hugging Face API key or paid inference service. The first startup downloads the model from Hugging Face.
- **chroma**: a separate published ChromaDB server image storing your chunks and embeddings on a named volume. Port 8000 is internal and is **not** published to Windows.

The containers talk using the *Compose service names*: `embeddings`, `chroma`. Using `localhost` between containers would be wrong: it refers to each container itself.

## 2. What you need

- Docker Desktop running on Windows (Linux container mode), or Docker Engine + Compose on Linux/macOS.
- Internet connection **for the first build** and to download the embedding model. If you use a VPN/proxy, Docker Desktop and the containers must be able to access those endpoints.
- An API key, model name, and base URL from **an OpenAI-compatible Chat Completions provider** (OpenAI, OpenRouter, or another compatible provider). The provider must support `chat.completions.create` and accept the `temperature` option (some reasoning models do not).
- Approximately several GB of free disk space for Python, PyTorch/model, and Chroma images. Building the embedding image can take time.

**No local Python installation is required to run the project using Docker.**

## 3. Folder structure

```text
simple_docker_rag/
├── compose.yaml                   # Starts THREE services
├── .env.example                   # Copy to .env, then edit
├── .gitignore
├── documents/
│   ├── docker_basics.txt
│   ├── docker_compose.txt
│   └── rag_explained.txt
├── embedding_service/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py                    # /health and /embed
└── rag_app/
    ├── Dockerfile
    ├── requirements.txt
    ├── app/
    │   ├── __init__.py
    │   ├── main.py                 # /, /health, /stats, /ask
    │   ├── ingest.py               # Index .txt documents (run once)
    │   ├── services.py             # embedding + Chroma + LLM calls
    │   └── core.py                 # chunking and formatting
    ├── static/index.html          # Simple browser UI
    └── tests/test_core.py
```

## 4. Step-by-step setup (Windows PowerShell)

### Step 1: Extract ZIP and open terminal in project root

You must be in the directory that contains `compose.yaml`:

```powershell
cd path\to\simple_docker_rag
dir
```

You should see `compose.yaml`, `documents`, `rag_app` and `embedding_service`.

### Step 2: Create your secret file

```powershell
Copy-Item .env.example .env
notepad .env
```

Example for the **official OpenAI API**:

```dotenv
OPENAI_API_KEY=sk-your-real-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4.1-mini
```

Example for **OpenRouter** (the model shown here is a placeholder; pick a model actually available to your account):

```dotenv
OPENAI_API_KEY=sk-or-your-real-api-key
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=your-chosen-chat-model
```

Do not put quotes around these example values. **Do not share or commit `.env`.** The RAG app receives these values through Compose `env_file` at runtime. The Docker image does not contain them.

### Step 3: Check the Compose syntax

```powershell
docker compose config --quiet
```

This validates the YAML/Compose configuration. (Do not paste the complete output of `docker compose config` publicly: resolved environment variables can include your API key.)

### Step 4: Build images and start all services

```powershell
docker compose up --build -d
```

Docker will:
1. Pull the official Python and Chroma base images.
2. Build `simple-rag-embeddings:1.0` and `simple-rag-app:1.0` from their respective Dockerfiles.
3. Create a Compose network named `simple-rag_default`.
4. Create named volumes `simple-rag_chroma-data` and `simple-rag_huggingface-cache`.
5. Start ChromaDB and the embedding service. The latter downloads its Hugging Face model on first startup.
6. Wait for **both health checks** and then start `rag-app`.

**First startup is slower** because installing PyTorch and downloading model weights consumes time and disk. No paid Hugging Face API is used.

### Step 5: Inspect services

```powershell
docker compose ps
```

You should see `embeddings` and `chroma` as healthy, and `rag-app` running. If the app is not yet running, inspect startup logs:

```powershell
docker compose logs -f embeddings
```

Press `Ctrl+C` to **stop following logs**, not to stop the containers.

Useful alternatives:

```powershell
docker compose logs --tail 50 chroma
docker compose logs --tail 50 rag-app
```

### Step 6: INGEST (index) your sample documents — required once

```powershell
docker compose exec rag-app python -m app.ingest
```

This executes a Python command **inside the running RAG container**. It:
1. Reads the three text files mounted from `./documents` into `/documents`.
2. Splits them into small overlapping text chunks.
3. Calls `http://embeddings:8001/embed` in the separate embedding container.
4. Upserts the returned vectors plus source metadata into `chroma:8000`.

Expected output resembles:

```text
Ingested N text chunks from 3 documents.
Chroma collection 'tutorial_documents' has N records.
Ingestion complete. Open http://localhost:8501 to ask questions.
```

`N` depends on the exact text/chunk lengths. If you repeat ingestion without changing the files, IDs are deterministic and existing chunks are overwritten rather than duplicated. If you delete or substantially edit existing source files, the simple tutorial does not automatically remove stale chunks; reset its volume for a completely fresh reindex.

### Step 7: Open the web app

Open **http://localhost:8501** and ask:

- `What is the difference between an image and a container?`
- `What does Docker Compose do?`
- `Why do we use the same embedding model when ingesting and querying?`

The UI shows the answer, source filenames, and number of retrieved chunks.

FastAPI interactive API docs: **http://localhost:8501/docs**

### Step 8: Test from PowerShell without the browser

```powershell
$body = @{ question = "What does Docker Compose do?" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8501/ask" -Method Post -ContentType "application/json" -Body $body
```

Inspect document count:

```powershell
Invoke-RestMethod http://localhost:8501/stats
```

### Step 9: Explore networking from INSIDE the RAG container

```powershell
docker compose exec rag-app sh
```

Inside the container, run:

```sh
python -c "import httpx; print(httpx.get('http://embeddings:8001/health').json())"
python -c "import chromadb; print(chromadb.HttpClient(host='chroma',port=8000).heartbeat())"
exit
```

You will see that services can communicate **without** publishing the embedding or Chroma ports to your Windows host.

### Step 10: Stop and start later

Stop the services, keep containers:

```powershell
docker compose stop
```

Start existing containers again:

```powershell
docker compose start
```

Remove the containers and network, but **keep the document vectors and model cache**:

```powershell
docker compose down
```

Then recreate:

```powershell
docker compose up -d
```

If you intentionally want to DELETE both the indexed vectors and cached model files:

```powershell
docker compose down -v
```

**Warning:** `-v` removes project named volumes. You will have to download the model again and re-run `app.ingest`.

## 5. Learn the image/network/volume concepts

| What | In this project | Why it matters |
|---|---|---|
| Image | `simple-rag-app:1.0` | Packaged app code and dependencies |
| Image | `simple-rag-embeddings:1.0` | Packaged embedding API and libraries |
| Image | `chromadb/chroma:1.5.3` | Prebuilt Chroma server, pulled from registry |
| Container | Running service instance | Separate processes/filesystems |
| Compose network | `simple-rag_default` | Hostname routing: `rag-app` → `embeddings` / `chroma` |
| Port mapping | `127.0.0.1:8501:8000` | Browser accesses RAG app from host |
| Volume | `chroma-data:/data` | Keeps indexed documents/vectors |
| Volume | `huggingface-cache:/models` | Reuses model files across container recreation |
| `.env` | Runtime key, model, base URL | Config changes without rebuilding images |

**Key distinction**: `localhost:8501` is for your Windows browser. `http://embeddings:8001` and `chroma:8000` are for container-to-container calls. The LLM API is external and requires internet connectivity.

## 6. Troubleshooting

**`/ask` returns 409 knowledge base empty:** Run `docker compose exec rag-app python -m app.ingest`.

**`/ask` returns 502 provider rejected request:** Ensure `.env` has a valid API key, Chat Completions model name, `OPENAI_BASE_URL`, working credits and provider compatibility. For OpenRouter, free models can return rate limits (429). API billing is separate from Docker.

**Error `bind ... address already in use`:** Host port 8501 is taken. Change only the **left** side in Compose, e.g. `"127.0.0.1:8502:8000"`, then use `http://localhost:8502`.

**Embedding service unhealthy / cannot download model:** Inspect `docker compose logs embeddings`. Docker/WSL might not route outbound traffic through your VPN; Docker proxy settings and host networking can affect this. No Hugging Face inference token is required, but a model download is required initially.

**ChromaDB unhealthy:** Inspect `docker compose logs chroma`. This project uses Chroma v1.5.3 and mounts its current persistence path `/data`. Avoid mixing its existing volume with incompatible server versions.

**Changing `.env` doesn't change a running container:** Recreate the RAG app container without rebuilding all images:

```powershell
docker compose up -d --force-recreate rag-app
```

**Changing Python source files:** Rebuild the changed service:

```powershell
docker compose up --build -d rag-app
```

**Changing or adding sample documents:** Rerun ingestion. For a clean knowledge base after removing documents, use `docker compose down -v` (deletes both named volumes), restart, then ingest.

**Inspect current logs:**

```powershell
docker compose logs --tail 100 rag-app
```

## 7. Mini exercises

1. Run `docker images` and identify all three service images.
2. Run `docker compose ps` and identify which service publishes a host port.
3. Change the host port from `8501` to `8502` and test the UI.
4. Enter the RAG container with `docker compose exec rag-app sh` and call the embedding health endpoint.
5. Add a new `.txt` document under `documents/`, rerun ingestion and ask a question from it.
6. Run `docker compose down` and then `docker compose up -d`; confirm Chroma still has indexed data.

## 8. What is deliberately left out?

No LangChain, agents, Redis, PostgreSQL, authentication, streaming, background jobs, reranking, PDF extraction or GPU setup. Those are useful later, but they distract from the **three Docker concepts you're studying first: images, networking, volumes**.

The app uses only plain text files and raw Chroma/HTTP calls so you can understand every step of RAG and the container boundaries.

## 9. Commands cheat sheet

```powershell
docker compose config --quiet
docker compose up --build -d
docker compose ps
docker compose logs -f embeddings
docker compose exec rag-app python -m app.ingest
docker compose exec rag-app sh
docker compose down
docker compose down -v
```

---

**Technical source for the Chroma image and data path:** the Chroma Docker deployment guide documents `chromadb/chroma:1.5.3` with `/data` persistence and the `/api/v2/heartbeat` health endpoint: https://cookbook.chromadb.dev/running/running-chroma/ .
