"""
main.py — Zeta Health AI · Policy Assistant
FastAPI backend serving the RAG pipeline and geo-law context engine.
"""

import io
import os
import uuid
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from embeddings import (
    extract_text_from_pdf, chunk_text, build_index,
    merge_indexes, query_index, get_pdf_hash, get_source_summary
)
from rag_pipeline import answer_question, suggest_followup_questions
from geo_law import get_labour_law_context, GEO_CONFIG

app = FastAPI(title="Zeta Health AI — Policy Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── In-memory session store (single-user local / demo mode) ───────────────────
# For multi-user production: replace with Redis or DB-backed sessions
class AppState:
    def __init__(self):
        self.reset()

    def reset(self):
        self.chunks         = []
        self.index          = None
        self.vocab          = {}
        self.idf            = {}
        self.indexed_hashes = set()
        self.chat_history   = []
        self.law_cache      = {}

state = AppState()


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return FileResponse("index.html")


@app.post("/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    """Index one or more PDF files."""
    results = []
    new_chunks = []

    for file in files:
        if not file.filename.endswith(".pdf"):
            results.append({"name": file.filename, "status": "skipped", "reason": "not a PDF"})
            continue

        pdf_bytes = await file.read()
        h = get_pdf_hash(pdf_bytes)

        if h in state.indexed_hashes:
            results.append({"name": file.filename, "status": "already_indexed"})
            continue

        try:
            pages  = extract_text_from_pdf(io.BytesIO(pdf_bytes), source_name=file.filename)
            chunks = chunk_text(pages)
            new_chunks.extend(chunks)
            state.indexed_hashes.add(h)
            results.append({
                "name":   file.filename,
                "status": "indexed",
                "pages":  max(c["page"] for c in chunks) if chunks else 0,
                "chunks": len(chunks),
            })
        except Exception as e:
            results.append({"name": file.filename, "status": "error", "reason": str(e)})

    if new_chunks:
        if state.chunks:
            idx, all_chunks, vocab, idf = merge_indexes({"chunks": state.chunks}, new_chunks)
        else:
            idx, all_chunks, vocab, idf = build_index(new_chunks)

        state.chunks = all_chunks
        state.index  = idx
        state.vocab  = vocab
        state.idf    = idf

    return {
        "files":    results,
        "summary":  get_source_summary(state.chunks),
        "total_chunks": len(state.chunks),
    }


class ChatRequest(BaseModel):
    question:  str
    geo:       Optional[str] = None
    state_str: Optional[str] = None


@app.post("/chat")
async def chat(req: ChatRequest):
    """Answer a question using the indexed documents."""
    if not state.index:
        raise HTTPException(status_code=400, detail="No documents indexed yet.")

    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question is empty.")

    geo       = req.geo   if req.geo   and req.geo   != "None" else None
    state_str = req.state_str if req.state_str and req.state_str != "All states / national" else None

    # Retrieve relevant chunks
    relevant_chunks = query_index(
        question, state.index, state.chunks,
        state.vocab, state.idf, top_k=5,
    )

    # Geo law context
    law_context = law_geo_label = None
    if geo:
        cache_key = f"{geo}|{state_str or 'national'}|{question[:60]}"
        if cache_key not in state.law_cache:
            ctx = get_labour_law_context(question, geo, state_str)
            state.law_cache[cache_key] = ctx
        else:
            ctx = state.law_cache[cache_key]

        if ctx.get("is_relevant"):
            law_context   = ctx.get("summary")
            law_geo_label = f"{geo}{' — ' + state_str if state_str else ''}"

    # Generate answer
    answer, _ = answer_question(
        question, relevant_chunks, state.chat_history,
        law_context=law_context, geo=law_geo_label,
    )

    followups = suggest_followup_questions(question, answer)

    # Build citations grouped by source
    citations = {}
    for chunk in relevant_chunks:
        src = chunk.get("source", "Policy Document")
        citations.setdefault(src, set()).add(chunk["page"])
    citations = {k: sorted(list(v)) for k, v in citations.items()}

    # Update history
    state.chat_history.extend([
        {"role": "user",      "content": question},
        {"role": "assistant", "content": answer},
    ])
    # Keep last 8 turns
    if len(state.chat_history) > 16:
        state.chat_history = state.chat_history[-16:]

    return {
        "answer":      answer,
        "citations":   citations,
        "law_context": law_context,
        "law_geo":     law_geo_label,
        "followups":   followups,
    }


@app.post("/clear")
async def clear(what: str = "all"):
    """Clear chat history or full index."""
    if what == "chat":
        state.chat_history = []
        return {"cleared": "chat"}
    else:
        state.reset()
        return {"cleared": "all"}


@app.get("/docs-summary")
async def docs_summary():
    """Return indexed document summary."""
    return {
        "summary":      get_source_summary(state.chunks),
        "total_chunks": len(state.chunks),
        "geo_config":   {k: v.get("states", []) for k, v in GEO_CONFIG.items()},
    }

