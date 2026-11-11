"""Plain Python functions that can be tested without external services."""


def split_text(text: str, size: int = 600, overlap: int = 100) -> list[str]:
    """Split plain text into overlapping character chunks."""
    if size <= 0 or overlap < 0 or overlap >= size:
        raise ValueError("Expected size > overlap >= 0")
    text = text.strip()
    if not text:
        return []
    chunks = []
    stride = size - overlap
    for start in range(0, len(text), stride):
        chunk = text[start:start + size]
        if chunk:
            chunks.append(chunk)
        if start + size >= len(text):
            break
    return chunks


def format_context(documents: list[str], sources: list[str]) -> str:
    if len(documents) != len(sources):
        raise ValueError("Documents and sources must match")
    return "\n\n".join(
        f"[Source: {source}]\n{document}"
        for document, source in zip(documents, sources)
    )
