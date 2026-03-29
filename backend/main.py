"""
FastAPI server for the AI Agent application.
Serves the frontend and provides the chat API endpoint.
"""

import os
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

# Add parent dir to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.agent import run_agent

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


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message to the AI agent and get a response."""
    try:
        if not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")

        response = await run_agent(request.message, request.history)

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
