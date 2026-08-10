# HR Policy Bot

> RAG-powered chatbot that answers employee HR policy questions from any uploaded PDF — with source page citations and follow-up suggestions.

****🚀 Live Demo:** https://zeta-policy-assistant.onrender.com*

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.60-red)
![Groq](https://img.shields.io/badge/Groq-llama--3.3--70b-orange)
![FAISS](https://img.shields.io/badge/Vector%20Store-FAISS-green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## The Problem

In a 500-person healthcare BPO, HR teams field hundreds of repetitive policy questions monthly — leave entitlements, probation terms, reimbursement limits, notice periods. Most answers exist in a handbook PDF that employees rarely read and HR staff have to look up manually for every query.

## Solution

A Retrieval-Augmented Generation (RAG) chatbot that ingests any HR policy PDF at runtime, indexes it semantically, and answers natural language questions — pointing employees to the exact page it used. No hardcoded documents, no retraining, no API dependency beyond Groq.

---

## Features

- Upload any HR handbook PDF — indexed in seconds
- Natural language Q&A with exact page citations
- Conversation memory — follow-up questions use prior context
- Suggested follow-up questions after each answer
- Works with any HR document: handbooks, leave policies, code of conduct, benefits guides
- Strictly answers from the document — never invents policy details
- Clear "not found" response when a topic isn't in the document

---

## Architecture

```
HR Policy PDF (any document, uploaded at runtime)
        │
        ▼
pdfplumber — text extraction by page
        │
        ▼
Chunker — 500-word overlapping chunks with 100-word overlap
        │
        ▼
TF-IDF Embeddings → FAISS IndexFlatIP (cosine similarity)
        │
Employee Question ──► Query vector → Top 4 chunks retrieved
                                          │
                              Groq llama-3.3-70b
                              (answer + page citations)
                                          │
                              Streamlit Chat UI
                              + Follow-up suggestions
```

---

## Setup

```bash
git clone https://github.com/zabeelbasheer/hr-policy-bot.git
cd hr-policy-bot
uv python pin 3.11
uv sync
cp .env.example .env   # Add your Groq API key
uv run streamlit run app.py
```

### `.env`
```
GROQ_API_KEY=your_groq_key_here
MODEL_NAME=llama-3.3-70b-versatile
```

---

## Sample Questions to Try

Upload any HR policy PDF and ask:

- *"What is the annual leave entitlement for a confirmed employee?"*
- *"How many sick days am I allowed per year?"*
- *"What is the notice period if I resign?"*
- *"Can I carry forward unused leave to next year?"*
- *"What is the reimbursement process for business travel?"*
- *"What happens if I am absent without notice?"*

---

## Healthcare BPO Context

Built for high-volume healthcare BPO environments where HR policy queries are frequent and consistent answers matter for compliance. Particularly useful for:

- Onboarding large cohorts of medical coders, billers, and RCM analysts
- Night shift staff who cannot reach HR during business hours
- Multi-site operations where policy documents vary by geography (Philippines vs India)
- Reducing HR ticket volume on repetitive entitlement queries

---

## Roadmap

- [ ] Multi-document support — query across multiple policy PDFs simultaneously
- [ ] Admin panel — upload and manage the knowledge base without re-indexing
- [ ] Role-based filtering — employee vs manager vs HR views of the same policy
- [ ] Audit log — track what questions were asked and how they were answered
- [ ] Integration with HRIS — push unanswered questions to HR ticketing system
- [ ] Multilingual support — Filipino and Tamil for Manila and Chennai operations

---

## About

Built by [Zabeel M. Basheer](https://linkedin.com/in/zabeelbasheer) — VP Business Excellence & India Site Lead at Shearwater Health. Part of a 6-project healthcare AI portfolio built to demonstrate applied AI in healthcare BPO operations.

---

## Tags

`healthcare-ai` `rag` `hr-tech` `langchain` `faiss` `streamlit` `groq` `llm` `healthcare-bpo` `python`
