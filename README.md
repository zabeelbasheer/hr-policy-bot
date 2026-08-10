# Zeta Health AI — Policy Assistant

> Multi-document HR policy chatbot with geo-aware labour law context. Upload any combination of HR policy PDFs, ask questions across all of them simultaneously, and get cited answers enriched with applicable labour law by region.

**🚀 Live Demo:** https://zeta-policy-assistant.onrender.com

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green)
![Groq](https://img.shields.io/badge/Groq-llama--3.3--70b-orange)
![FAISS](https://img.shields.io/badge/Vector%20Store-FAISS-teal)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## The Problem

In a multi-geography healthcare BPO, HR policy questions arrive from employees across Manila, Chennai, and the US — each operating under different labour laws, entitlements, and statutory obligations. A standard policy chatbot answers from the document. It cannot tell an employee in Tamil Nadu that their transport entitlement is also a legal obligation under the Tamil Nadu Shops and Establishments Act, not just a company policy.

Most RAG chatbots also lock you into a single document. Employees need answers that span the Code of Conduct, the Leave Policy, the Transportation Policy, and the Referral Program — simultaneously, in one conversation.

---

## What This Tool Does

Upload one or more HR policy PDFs — individually or as a batch. Ask any question. The tool retrieves the most relevant sections across all documents, generates a cited answer, and — when a geography is selected — determines whether applicable labour law adds context to the answer. If it does, a law context box appears below the answer citing the specific legislation by name. If it doesn't, nothing extra appears.

---

## Labour Law Integration by Region

Select a geography in the sidebar before asking questions. The tool assesses each answer for legal relevance and surfaces applicable law only when it matters.

### 🇵🇭 Philippines
**Primary legislation covered:**
- Labor Code of the Philippines (Presidential Decree No. 442)
- DOLE Department Orders
- Republic Act 11058 — Occupational Safety and Health Law
- Republic Act 10173 — Data Privacy Act

**States / regions:** Metro Manila, Cebu, Davao, Laguna, Cavite, Pampanga, Batangas

**Government sources ranked first:** dole.gov.ph, ble.dole.gov.ph, nlrc.gov.ph, sss.gov.ph, philhealth.gov.ph, hdmf.gov.ph

---

### 🇮🇳 India
**Primary legislation covered:**
- Industrial Disputes Act 1947
- Shops and Establishments Act (state-specific)
- Payment of Gratuity Act 1972
- Maternity Benefit Act 1961
- Payment of Bonus Act 1965
- Employees' Provident Funds Act 1952
- Code on Wages 2019
- Occupational Safety Health and Working Conditions Code 2020

**States / regions:** Tamil Nadu, Maharashtra, Karnataka, Telangana, Delhi, Gujarat, West Bengal, Kerala

**Government sources ranked first:** labour.gov.in, epfindia.gov.in, esic.in, shramsuvidha.gov.in, clc.gov.in

---

### 🇺🇸 United States
**Primary legislation covered:**
- Fair Labor Standards Act (FLSA)
- National Labor Relations Act (NLRA)
- Title VII of the Civil Rights Act
- Americans with Disabilities Act (ADA)
- Family and Medical Leave Act (FMLA)
- Occupational Safety and Health Act (OSHA)
- Age Discrimination in Employment Act (ADEA)

**States / regions:** California, New York, Texas, Florida, Illinois, Pennsylvania, Ohio, Georgia, North Carolina, Michigan, New Jersey, Virginia

**Government sources ranked first:** dol.gov, eeoc.gov, nlrb.gov, osha.gov

---

## Source Credibility Ranking

The law context engine ranks sources in this order:

1. **Government websites** — `.gov`, `.gov.in`, `.gov.ph` domains. Statutory text, official guidance, and regulatory updates.
2. **Authoritative references** — Bar associations, law school portals, and established legal reference sites that cite primary government sources.

Law context only appears when the LLM determines the question has a genuine legal dimension. Administrative questions (timesheet submission, IT requests) return policy-only answers with no law box.

---

## Features

- Upload multiple PDFs simultaneously or one at a time — indexes merge automatically
- Natural language Q&A across all documents in a single question
- Per-answer citations showing document name and page number
- Geo-law context box — appears only when legally relevant, never forced
- Friendly status messages during processing ("🔍 Hunting for the most relevant sections…")
- Follow-up question suggestions after each answer
- Drag-and-drop PDF upload
- Clear chat or full reset without page refresh

---

## Architecture

```
HR Policy PDFs (one or many, uploaded at runtime)
          │
          ▼
pdfplumber — text extraction by page, tagged with source filename
          │
          ▼
Chunker — 500-word overlapping chunks (100-word overlap)
          │
          ▼
TF-IDF Embeddings → FAISS IndexFlatIP
          │
Employee Question ──► Query vector → Top 5 chunks retrieved
                                          │
                              ┌───────────┴───────────┐
                              ▼                       ▼
                    Groq llama-3.3-70b        Geo-Law Engine
                    (answer + citations)      (relevance check
                                              + law summary)
                              │                       │
                              └───────────┬───────────┘
                                          ▼
                               FastAPI JSON response
                                          │
                                          ▼
                              Vanilla JS frontend
                              (citations · law box · follow-ups)
```

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | FastAPI 0.111 + Uvicorn |
| LLM inference | Groq API — llama-3.3-70b-versatile |
| Vector search | FAISS IndexFlatIP (cosine similarity) |
| PDF parsing | pdfplumber |
| Embeddings | TF-IDF (zero external API dependency) |
| Frontend | Pure HTML + CSS + Vanilla JS (single file) |
| Deployment | Render.com |

---

## Setup

```bash
git clone https://github.com/zabeelbasheer/hr-policy-bot.git
cd hr-policy-bot
uv python pin 3.11
uv sync
cp .env.example .env   # Add your Groq API key
uv run uvicorn main:app --reload --port 8000
```

Open `http://localhost:8000`

### `.env`
```
GROQ_API_KEY=your_groq_key_here
MODEL_NAME=llama-3.3-70b-versatile
```

---

## Sample Policy Documents Included

The `sample_data/` folder contains four Zeta Health AI branded HR policy documents for testing:

| File | Content |
|------|---------|
| `01_Code_of_Conduct.pdf` | Workplace behaviour, data confidentiality, anti-bribery, reporting violations |
| `02_India_Transportation_Policy.pdf` | Cab zones, female employee night shift provisions, vendor standards |
| `03_Employee_Referral_Program.pdf` | Bonus structure by band (PHP and INR), eligibility, submission process |
| `04_Performance_Management.pdf` | Rating scale, calibration, PIP process, goal-setting framework |

---

## Cross-Document Questions to Test

These questions deliberately span multiple documents:

- *"Can an employee on a PIP refer a candidate for a bonus?"* — Performance Management + Referral Program
- *"What are the transport obligations for female employees on night shifts in Tamil Nadu?"* — India Transportation Policy + Tamil Nadu labour law
- *"What is the notice period and what rating would trigger a PIP?"* — Code of Conduct + Performance Management
- *"How much referral bonus would I get for hiring a Senior Manager in India?"* — Referral Program (INR band)

---

## Roadmap

- [ ] Azure AD SSO — employee authentication before accessing HR documents
- [ ] PostgreSQL session store — multi-user support beyond single-instance in-memory
- [ ] Real-time labour law fetch — live web search against government portals
- [ ] Document version management — track policy updates and flag outdated content
- [ ] Audit log — record what questions were asked and what answers were given
- [ ] Multilingual support — Filipino and Tamil for Manila and Chennai operations
- [ ] Mobile-responsive layout

---

## About

Built by [Zabeel M. Basheer](https://linkedin.com/in/zabeelbasheer) — VP Business Excellence & India Site Lead at Shearwater Health. Part of the [Zeta Health AI](https://github.com/zabeelbasheer) portfolio of applied AI tools for healthcare operations.

*Clinical operations, intelligently governed.*

---

## Tags

`healthcare-ai` `rag` `hr-tech` `faiss` `fastapi` `groq` `llm` `healthcare-bpo` `python` `labour-law` `multi-document`
