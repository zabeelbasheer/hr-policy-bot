"""
embeddings.py — PDF processing and FAISS vector store
Supports single PDF upload, batch upload, and incremental addition
of new documents to an existing index.
"""

import io
import math
import hashlib
import re
from collections import Counter
import numpy as np
import pdfplumber
import faiss


# ── Text extraction ───────────────────────────────────────────────────────────

def extract_text_from_pdf(pdf_file, source_name: str = "") -> list[dict]:
    """Extract text from a PDF file object, page by page."""
    chunks = []
    with pdfplumber.open(pdf_file) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            text = page.extract_text()
            if text and text.strip():
                chunks.append({
                    "page":   page_num,
                    "text":   text.strip(),
                    "source": source_name,
                })
    return chunks


def chunk_text(pages: list[dict], chunk_size: int = 500, overlap: int = 100) -> list[dict]:
    """Split pages into overlapping word-level chunks."""
    chunks = []
    for page_data in pages:
        words = page_data["text"].split()
        start = 0
        while start < len(words):
            end = min(start + chunk_size, len(words))
            chunks.append({
                "page":   page_data["page"],
                "source": page_data.get("source", ""),
                "text":   " ".join(words[start:end]),
            })
            if end == len(words):
                break
            start += chunk_size - overlap
    return chunks


# ── Embeddings ────────────────────────────────────────────────────────────────

def tokenize(text: str) -> list[str]:
    return re.findall(r'\b[a-zA-Z]{2,}\b', text.lower())


def build_vocab_and_idf(all_chunks: list[dict], max_vocab: int = 2048) -> tuple[dict, dict]:
    """Build vocabulary and IDF weights from a list of chunks."""
    all_tokens = []
    doc_tokens = []
    for c in all_chunks:
        tokens = tokenize(c["text"])
        all_tokens.extend(tokens)
        doc_tokens.append(tokens)

    vocab = {w: i for i, w in enumerate(sorted(set(all_tokens))) if i < max_vocab}
    N = len(doc_tokens)
    idf = {}
    for word in vocab:
        df = sum(1 for tokens in doc_tokens if word in tokens)
        idf[word] = math.log((N + 1) / (df + 1)) + 1

    return vocab, idf


def vectorize(text: str, vocab: dict, idf: dict) -> np.ndarray:
    """Convert text to a normalised TF-IDF vector."""
    vocab_size = max(vocab.values()) + 1 if vocab else 2048
    tokens = tokenize(text)
    counter = Counter(tokens)
    total = len(tokens) or 1
    vec = np.zeros(vocab_size, dtype=np.float32)
    for word, idx in vocab.items():
        if word in counter:
            vec[idx] = (counter[word] / total) * idf.get(word, 1.0)
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec /= norm
    return vec


def build_index(chunks: list[dict], client=None) -> tuple:
    """
    Build a FAISS index from a list of chunks.
    Returns (index, chunks, vocab, idf).
    """
    vocab, idf = build_vocab_and_idf(chunks)
    vectors = np.array([vectorize(c["text"], vocab, idf) for c in chunks], dtype=np.float32)
    dim = vectors.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(vectors)
    return index, chunks, vocab, idf


def merge_indexes(existing_state: dict, new_chunks: list[dict]) -> tuple:
    """
    Add new chunks to an existing index state.
    Rebuilds vocab/IDF across all chunks (old + new) for consistency.
    existing_state: {"chunks": [...], "vocab": {...}, "idf": {...}}
    Returns (index, all_chunks, vocab, idf)
    """
    all_chunks = existing_state.get("chunks", []) + new_chunks
    return build_index(all_chunks)


# ── Query ─────────────────────────────────────────────────────────────────────

def query_index(query: str, index, chunks: list[dict],
                vocab: dict, idf: dict, top_k: int = 5) -> list[dict]:
    """Search the FAISS index and return the top_k most relevant chunks."""
    vec = vectorize(query, vocab, idf).reshape(1, -1)
    scores, indices = index.search(vec, min(top_k, len(chunks)))
    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx >= 0:
            results.append({**chunks[idx], "score": float(score)})
    return results


# ── Utilities ─────────────────────────────────────────────────────────────────

def get_pdf_hash(pdf_bytes: bytes) -> str:
    return hashlib.md5(pdf_bytes).hexdigest()


def get_source_summary(chunks: list[dict]) -> dict:
    """Return a summary of documents and page counts in the index."""
    sources = {}
    for c in chunks:
        src = c.get("source", "Unknown")
        sources[src] = max(sources.get(src, 0), c["page"])
    return sources
