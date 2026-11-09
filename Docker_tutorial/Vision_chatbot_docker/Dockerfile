# Build a reproducible educational ML model in a separate stage.
FROM python:3.12-slim AS trainer
WORKDIR /project
COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt
COPY ml ./ml
RUN python -m ml.train

FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 MODEL_DIR=/app/artifacts
WORKDIR /app
COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt && \
    groupadd --system appgroup && useradd --system --gid appgroup --home-dir /app appuser
COPY app ./app
COPY --from=trainer /project/artifacts ./artifacts
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=3)"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
