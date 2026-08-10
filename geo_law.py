"""
geo_law.py — Geo-aware labour law context engine
Fetches current labour law summaries from credible sources ranked by:
  1. Government websites (.gov, .gov.in, .gov.ph)
  2. Authoritative references (law firms, bar associations, official portals)
Uses Groq to determine relevance and summarise findings per question.
"""

import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# ── Geography configuration ───────────────────────────────────────────────────
GEO_CONFIG = {
    "Philippines": {
        "states": [
            "Metro Manila", "Cebu", "Davao", "Laguna",
            "Cavite", "Pampanga", "Batangas",
        ],
        "primary_laws": [
            "Labor Code of the Philippines (Presidential Decree No. 442)",
            "DOLE Department Orders",
            "Republic Act 11058 (OSH Law)",
            "Republic Act 10173 (Data Privacy Act)",
        ],
        "gov_sources": [
            "dole.gov.ph", "ble.dole.gov.ph", "nlrc.gov.ph",
            "sss.gov.ph", "philhealth.gov.ph", "hdmf.gov.ph",
        ],
        "authoritative_sources": [
            "chanrobles.com", "lawphil.net", "philippinelaw.info",
        ],
    },
    "India": {
        "states": [
            "Tamil Nadu", "Maharashtra", "Karnataka", "Telangana",
            "Delhi", "Gujarat", "West Bengal", "Kerala",
        ],
        "primary_laws": [
            "Industrial Disputes Act 1947",
            "Shops and Establishments Act (state-specific)",
            "Payment of Gratuity Act 1972",
            "Maternity Benefit Act 1961",
            "Payment of Bonus Act 1965",
            "Employees' Provident Funds Act 1952",
            "Code on Wages 2019",
            "Occupational Safety Health and Working Conditions Code 2020",
        ],
        "gov_sources": [
            "labour.gov.in", "epfindia.gov.in", "esic.in",
            "shramsuvidha.gov.in", "clc.gov.in",
        ],
        "authoritative_sources": [
            "indiacode.nic.in", "bareactslive.com", "legalserviceindia.com",
        ],
    },
    "United States": {
        "states": [
            "California", "New York", "Texas", "Florida",
            "Illinois", "Pennsylvania", "Ohio", "Georgia",
            "North Carolina", "Michigan", "New Jersey", "Virginia",
        ],
        "primary_laws": [
            "Fair Labor Standards Act (FLSA)",
            "National Labor Relations Act (NLRA)",
            "Title VII of the Civil Rights Act",
            "Americans with Disabilities Act (ADA)",
            "Family and Medical Leave Act (FMLA)",
            "Occupational Safety and Health Act (OSHA)",
            "Age Discrimination in Employment Act (ADEA)",
        ],
        "gov_sources": [
            "dol.gov", "eeoc.gov", "nlrb.gov",
            "osha.gov", "irs.gov",
        ],
        "authoritative_sources": [
            "shrm.org", "nolo.com", "lexisnexis.com",
        ],
    },
}

RELEVANCE_SYSTEM = """You are a labour law expert specialising in employment law 
across the Philippines, India, and the United States.

Given a question asked in an HR policy chatbot and a geography, determine:
1. Whether the question has any labour law dimension (leave entitlements, 
   termination, discrimination, working hours, transport obligations, 
   benefits, data privacy, health and safety, etc.)
2. If relevant, provide a concise 2-4 sentence summary of the applicable 
   legal framework for that geography and state (if specified).

Be precise — cite the specific law or regulation by name where applicable.
Do not fabricate law names or section numbers.
If the question is purely administrative (e.g. "how do I submit a timesheet") 
with no legal dimension, mark it as not relevant.

Respond in this exact JSON format:
{
  "is_relevant": true or false,
  "summary": "2-4 sentence legal context. Cite law names. Empty string if not relevant.",
  "primary_law": "Name of the most applicable law, or empty string.",
  "source_tier": "government" or "authoritative" or "none"
}"""


def get_client():
    return Groq(api_key=os.getenv("GROQ_API_KEY"))


def get_labour_law_context(question: str, geo: str, state: str = None) -> dict:
    """
    Determine if a question has a labour law dimension for the given geography.
    Returns dict with is_relevant, summary, primary_law, source_tier.
    """
    if not geo or geo == "None":
        return {"is_relevant": False, "summary": "", "primary_law": "", "source_tier": "none"}

    config = GEO_CONFIG.get(geo, {})
    primary_laws  = ", ".join(config.get("primary_laws", []))
    gov_sources   = ", ".join(config.get("gov_sources", []))
    auth_sources  = ", ".join(config.get("authoritative_sources", []))

    geo_context = f"Geography: {geo}"
    if state:
        geo_context += f" — {state}"

    prompt = (
        f"{geo_context}\n"
        f"Key applicable laws: {primary_laws}\n"
        f"Government sources: {gov_sources}\n"
        f"Authoritative references: {auth_sources}\n\n"
        f"Employee question: {question}\n\n"
        f"Assess whether this question has a labour law dimension and provide context."
    )

    client = get_client()
    try:
        response = client.chat.completions.create(
            model=os.getenv("MODEL_NAME", "llama-3.3-70b-versatile"),
            messages=[
                {"role": "system", "content": RELEVANCE_SYSTEM},
                {"role": "user",   "content": prompt},
            ],
            temperature=0.1,
            max_tokens=300,
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        import json
        result = json.loads(raw.strip())
        return result
    except Exception as e:
        return {
            "is_relevant": False,
            "summary":     "",
            "primary_law": "",
            "source_tier": "none",
        }
