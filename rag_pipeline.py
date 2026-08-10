"""
rag_pipeline.py — RAG query pipeline
Generates cited answers from retrieved chunks.
Optionally weaves in geo-specific labour law context when relevant.
"""

import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """You are an HR policy assistant for a healthcare organisation.
Answer employee questions accurately based on the HR policy context provided.
When labour law context is also provided, weave it in naturally only if it adds 
value to the answer — do not force it.

Rules:
- Answer ONLY from the provided context. Never invent policy details.
- If the answer is not in the documents, say clearly: 
  "This topic is not covered in the uploaded policy documents. Please contact HR directly."
- Always cite the document name and page number you found the answer on.
- When labour law context is provided and relevant, reference the specific law by name.
- Be concise and direct.
- Never give legal advice — note that employees should consult HR or legal counsel for legal matters.
- If policy and law are in tension, note both clearly."""


def get_client():
    return Groq(api_key=os.getenv("GROQ_API_KEY"))


def get_model():
    return os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")


def format_context(chunks: list[dict]) -> str:
    parts = []
    for chunk in chunks:
        src   = chunk.get("source", "Policy Document").replace(".pdf","")
        page  = chunk["page"]
        score = chunk.get("score", 0)
        parts.append(
            f"[Source: {src} | Page {page} | Relevance: {score:.2f}]\n{chunk['text']}"
        )
    return "\n\n---\n\n".join(parts)


def answer_question(
    question: str,
    chunks: list[dict],
    conversation_history: list[dict],
    law_context: str = None,
    geo: str = None,
) -> tuple[str, list[int]]:
    """
    Generate an answer from retrieved policy chunks.
    Optionally include geo-specific labour law context.
    Returns (answer_text, list_of_cited_pages).
    """
    client  = get_client()
    context = format_context(chunks)

    law_section = ""
    if law_context:
        law_section = (
            f"\n\nApplicable Labour Law Context ({geo or 'selected geography'}):\n"
            f"{law_context}\n"
            f"(Include this only if directly relevant to the answer.)"
        )

    user_content = (
        f"HR Policy Documents:\n\n{context}"
        f"{law_section}\n\n"
        f"Employee Question: {question}\n\n"
        f"Provide a clear, cited answer."
    )

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if conversation_history:
        messages += conversation_history[-4:]
    messages.append({"role": "user", "content": user_content})

    response = get_client().chat.completions.create(
        model=get_model(),
        messages=messages,
        temperature=0.1,
        max_tokens=700,
    )

    answer      = response.choices[0].message.content.strip()
    cited_pages = list(set(c["page"] for c in chunks))
    return answer, cited_pages


def suggest_followup_questions(question: str, answer: str) -> list[str]:
    """Generate 3 follow-up question suggestions."""
    try:
        response = get_client().chat.completions.create(
            model=get_model(),
            messages=[{
                "role": "user",
                "content": (
                    f"An employee asked: '{question}'\n"
                    f"The HR policy answer was: '{answer[:300]}'\n\n"
                    f"Suggest 3 short follow-up questions the employee might ask next. "
                    f"Return ONLY a JSON array of 3 question strings. No markdown."
                )
            }],
            temperature=0.4,
            max_tokens=150,
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        questions = json.loads(raw.strip())
        return questions[:3] if isinstance(questions, list) else []
    except Exception:
        return []
