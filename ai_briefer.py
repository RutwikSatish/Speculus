"""
ai_briefer.py — NexusRisk Groq AI Risk Brief Generator

Generates ISO 31000-structured plain-language risk briefs
for suppliers that breach risk appetite thresholds.

Output format mirrors the intelligence packages produced by
enterprise SCRM teams (Lockheed Martin, Apple, Boeing internal
risk teams produce briefs in this exact structure).
"""

import requests
import json
from typing import Dict, Any


GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL    = "llama3-8b-8192"  # Default: fast, free-tier friendly

def get_model():
    """Read model from Streamlit secrets if available, else use default."""
    try:
        import streamlit as st
        return st.secrets.get("groq", {}).get("model", MODEL)
    except Exception:
        return MODEL


def generate_risk_brief(
    supplier_data: Dict[str, Any],
    appetite: Dict[str, int],
    groq_api_key: str
) -> str:
    """
    Generate a structured ISO 31000 risk brief for a breaching supplier
    using Groq AI.

    The brief follows the standard SCRM intelligence package format:
    1. Executive summary (2 sentences)
    2. Risk signal summary (what was detected)
    3. Dimension breakdown (per ISO 31000 risk categories)
    4. COSO ERM response recommendation
    5. Immediate actions (0-7 days)
    6. Short-term actions (1-4 weeks)
    7. Strategic actions (1 quarter+)
    """

    if not groq_api_key:
        return "_Groq API key required for AI briefs. Add your free key in the sidebar._"

    dims = supplier_data.get("dimensions", {})
    signals = supplier_data.get("signals", [])
    signal_summaries = "\n".join([
        f"- [{s.get('source')}] {s.get('title', '')[:100]}"
        for s in signals[:5]
    ]) or "No live signals detected in past 72 hours."

    breached = ", ".join(supplier_data.get("breached_dims", []))
    composite = supplier_data.get("composite_score", 0)
    coso = supplier_data.get("coso_response", "Monitor")

    system_prompt = """You are a senior supply chain risk analyst at a Fortune 500 company.
You produce ISO 31000-compliant risk briefs that supply chain directors and CFOs act on.
Your output is precise, structured, actionable, and grounded in SCRM best practices.
Never use generic filler. Every sentence must contain a specific fact or action.
Write in the voice of a practitioner, not a consultant pitch."""

    # Extract alternatives context if provided
    alternatives_context = supplier_data.get("alternatives_context", "")

    user_prompt = f"""Generate a supply chain risk brief for this supplier breach.

SUPPLIER: {supplier_data.get('name')} ({supplier_data.get('country')})
COMPOSITE RISK SCORE: {composite}/100
BREACHED DIMENSIONS: {breached}
COSO ERM RESPONSE: {coso}

DIMENSION SCORES:
- Geopolitical Exposure: {dims.get('geopolitical', 0)}/100 (appetite: {appetite.get('geopolitical', 60)})
- Supplier Health: {dims.get('supplier_health', 0)}/100 (appetite: {appetite.get('supplier_health', 55)})
- Logistics Stability: {dims.get('logistics', 0)}/100 (appetite: {appetite.get('logistics', 50)})
- Single-Source Dependency: {dims.get('single_source', 0)}/100 (appetite: {appetite.get('single_source', 65)})
- Regulatory Compliance: {dims.get('regulatory', 0)}/100 (appetite: {appetite.get('regulatory', 55)})

LIVE SIGNALS DETECTED (past 72 hours):
{signal_summaries}

SCOR PERFORMANCE ATTRIBUTE PRIMARILY AFFECTED: {supplier_data.get('scor_impact', 'Reliability')}
ZSIDISIN RISK SOURCE TYPE: {supplier_data.get('zsidisin_source', 'Supply')}
GEOPOLITICAL SCORING METHOD: {supplier_data.get('geo_detail', {}).get('methodology', 'WGI + GDELT')}

{alternatives_context}

Generate a brief with these exact sections:
## Executive Summary
(2 sentences: what the risk is, why it breaches appetite)

## Signal Analysis
(What the live signals indicate. Be specific about what was detected.)

## Dimension Breakdown
(For each breached dimension: what drives the score and what it means operationally)

## COSO ERM Response Rationale
(Why {coso} is the appropriate response per COSO ERM 2017 Chapter 8)

## Recommended Actions
**Immediate (0–7 days):**
- [specific action with timeline]
- [specific action with owner]

**Short-term (1–4 weeks):**
- [specific action — reference alternatives if relevant]
- [specific action]

**Strategic (this quarter):**
- [specific action — dual-sourcing recommendation if single-source risk is high, reference specific alternative suppliers from the list above with estimated qualification timeline]

## Risk Register Note
(One sentence for the ISO 31000 §6.7 audit trail)"""

    try:
        headers = {
            "Authorization": f"Bearer {groq_api_key}",
            "Content-Type":  "application/json"
        }
        payload = {
            "model":       get_model(),
            "max_tokens":  900,
            "temperature": 0.3,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt}
            ]
        }

        response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    except requests.exceptions.HTTPError as e:
        return f"_API error: {e}. Check your Groq API key._"
    except Exception as e:
        return f"_Brief generation failed: {str(e)[:100]}_"
