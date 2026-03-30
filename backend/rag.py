"""
RAG layer using ChromaDB with local sentence-transformers embeddings.
No external embedding API needed — runs fully local.
"""

import hashlib
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

# --- Setup ---

CHROMA_DIR = str(Path(__file__).parent.parent / "chroma_db")

_client = chromadb.PersistentClient(path=CHROMA_DIR)
_ef = embedding_functions.DefaultEmbeddingFunction()  # all-MiniLM-L6-v2 (local)
_col = _client.get_or_create_collection(
    name="agent_documents",
    embedding_function=_ef,
)

# --- Helpers ---

def _make_doc_id(filename: str) -> str:
    return hashlib.sha256(filename.encode()).hexdigest()[:16]


def _chunk_text(text: str, size: int = 1000, overlap: int = 150) -> list[str]:
    step = size - overlap
    return [text[i:i + size] for i in range(0, len(text), step)]


# --- Public API ---

def add_document(filename: str, text: str) -> dict:
    """Chunk, embed, and store a document. Re-uploads replace previous version."""
    doc_id = _make_doc_id(filename)

    # Remove existing chunks for this doc
    existing = _col.get(where={"doc_id": doc_id})
    if existing["ids"]:
        _col.delete(ids=existing["ids"])

    chunks = _chunk_text(text)
    ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
    metadatas = [
        {"doc_id": doc_id, "filename": filename, "chunk_index": i, "total_chunks": len(chunks)}
        for i in range(len(chunks))
    ]

    _col.add(documents=chunks, metadatas=metadatas, ids=ids)
    return {"doc_id": doc_id, "filename": filename, "chunks": len(chunks)}


_FILE_KEYWORDS = {"ไฟล์", "file", "document", "เอกสาร", "อัพโหลด", "upload", "ที่อัพ", "ข้างต้น", "ด้านบน"}


def _mentions_file(query: str, stored_filenames: list[str]) -> bool:
    """Check if the query references an uploaded file."""
    q_lower = query.lower()
    # Check generic file keywords
    if any(kw in q_lower for kw in _FILE_KEYWORDS):
        return True
    # Check if any stored filename is mentioned
    return any(fname.lower() in q_lower or fname.lower().rsplit(".", 1)[0] in q_lower
               for fname in stored_filenames)


def _get_full_context() -> str:
    """Return complete content of all stored documents (used when file is explicitly mentioned)."""
    result = _col.get(include=["documents", "metadatas"])
    # Group chunks by doc_id in order
    docs_chunks: dict[str, list] = {}
    for doc, meta in zip(result["documents"], result["metadatas"]):
        doc_id = meta["doc_id"]
        if doc_id not in docs_chunks:
            docs_chunks[doc_id] = {"filename": meta["filename"], "chunks": {}}
        docs_chunks[doc_id]["chunks"][meta["chunk_index"]] = doc

    parts = []
    for entry in docs_chunks.values():
        ordered = [entry["chunks"][i] for i in sorted(entry["chunks"])]
        parts.append(f"[Document: {entry['filename']}]\n{''.join(ordered)}")
    return "\n\n---\n\n".join(parts)


def retrieve_context(query: str, k: int = 5) -> str | None:
    """Return relevant document context. Returns None if no docs stored.
    - If user mentions a file/filename → return full document content
    - Otherwise → return top-k semantically similar chunks
    """
    if _col.count() == 0:
        return None

    stored = list_documents()
    filenames = [d["filename"] for d in stored]

    if _mentions_file(query, filenames):
        return _get_full_context()

    results = _col.query(query_texts=[query], n_results=min(k, _col.count()))
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]

    if not docs:
        return None

    parts = [f"[Source: {m.get('filename','?')}]\n{d}" for d, m in zip(docs, metas)]
    return "\n\n---\n\n".join(parts)


def list_documents() -> list[dict]:
    if _col.count() == 0:
        return []
    result = _col.get(include=["metadatas"])
    seen = {}
    for meta in result["metadatas"]:
        doc_id = meta["doc_id"]
        if doc_id not in seen:
            seen[doc_id] = {
                "doc_id": doc_id,
                "filename": meta["filename"],
                "chunks": meta["total_chunks"],
            }
    return list(seen.values())


def delete_document(doc_id: str) -> bool:
    result = _col.get(where={"doc_id": doc_id})
    if not result["ids"]:
        return False
    _col.delete(ids=result["ids"])
    return True
