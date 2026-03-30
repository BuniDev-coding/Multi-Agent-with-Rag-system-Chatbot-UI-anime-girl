"""
FastAPI server for the AI Agent application.
Serves the frontend and provides the chat API endpoint.
"""

import io
import os
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

try:
    import pypdf
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

try:
    import docx
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

# Add parent dir to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.agent import run_agent
from backend.rag import add_document, retrieve_context, list_documents, delete_document

app = FastAPI(title="AI Agent", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Models ---

class ChatRequest(BaseModel):
    message: str
    history: list = []

class ChatResponse(BaseModel):
    response: str
    has_code: bool = False

# --- API Routes ---

@app.get("/api/health")
async def health():
    return {"status": "ok", "agent": "LangGraph AI Agent"}


TEXT_EXTENSIONS = {".txt", ".md", ".html", ".css", ".js", ".json", ".csv", ".py"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def _extract_pdf(raw: bytes) -> str:
    reader = pypdf.PdfReader(io.BytesIO(raw))
    return "\n\n".join(page.extract_text() or "" for page in reader.pages).strip()


def _extract_docx(raw: bytes) -> str:
    doc = docx.Document(io.BytesIO(raw))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


@app.get("/api/documents")
async def get_documents():
    return {"documents": list_documents()}


@app.delete("/api/documents/{doc_id}")
async def remove_document(doc_id: str):
    deleted = delete_document(doc_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"deleted": True, "doc_id": doc_id}


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), store: bool = False):
    """Upload a file. If store=true, adds to RAG knowledge base. Otherwise returns raw text."""
    ext = Path(file.filename).suffix.lower()

    allowed = TEXT_EXTENSIONS | ({".pdf"} if HAS_PDF else set()) | ({".docx"} if HAS_DOCX else set())
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"File type '{ext}' not supported. Allowed: {', '.join(sorted(allowed))}")

    raw = await file.read()
    if len(raw) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    if ext == ".pdf":
        if not HAS_PDF:
            raise HTTPException(status_code=400, detail="PDF support not installed. Run: pip install pypdf")
        content = _extract_pdf(raw)
    elif ext == ".docx":
        if not HAS_DOCX:
            raise HTTPException(status_code=400, detail="DOCX support not installed. Run: pip install python-docx")
        content = _extract_docx(raw)
    else:
        try:
            content = raw.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="Cannot read file — please use UTF-8 encoded text")

    if not content.strip():
        raise HTTPException(status_code=400, detail="File appears to be empty or has no readable text")

    if store:
        result = add_document(file.filename, content)
        return {"filename": file.filename, "doc_id": result["doc_id"], "chunks": result["chunks"], "stored": True}

    return {"filename": file.filename, "content": content}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message to the AI agent and get a response."""
    try:
        if not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")

        rag_context = retrieve_context(request.message)
        response = await run_agent(request.message, request.history, rag_context=rag_context)

        # Check if response contains HTML code
        has_code = "<!DOCTYPE html>" in response or "<html" in response or "```html" in response

        return ChatResponse(response=response, has_code=has_code)

    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Serve Frontend ---

frontend_dir = Path(__file__).parent.parent / "frontend"

@app.get("/")
async def serve_index():
    return FileResponse(frontend_dir / "index.html")

# Mount static files
app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")


if __name__ == "__main__":
    import uvicorn
    print("\n[*] AI Agent Server Starting...")
    print("[>] Open http://localhost:8000 in your browser\n")
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
