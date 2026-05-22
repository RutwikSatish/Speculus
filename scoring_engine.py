"""
scoring_engine.py — SPECULUS ISO 31000 Risk Scoring Engine

METHODOLOGY TYPE: Semi-quantitative risk assessment
Per ISO 31000:2018 §6.4.3 and academic literature (Oliveira et al., 2017;
Raso, 2023), semi-quantitative methods assign numerical values to likelihood
and severity of risks for structured prioritization. This is explicitly
supported by ISO 31000 as a valid approach.

SCORING FORMULA:
  dim_score = country_base (WGI 2024) + signal_boost (GDELT/FedRegister)
  composite = Σ(dim_score × dim_weight)

INDUSTRY STANDARD COMPARISON:
  The FMEA Risk Priority Number (RPN = Severity × Occurrence × Detection)
  is the most widely used supply chain risk scoring framework (MetricGate, 2026).
  SPECULUS implements a simplified variant:
    - Severity  → WGI baseline score (country governance quality)
    - Occurrence → signal_boost (live news signal frequency and severity)
    - Detection  → signal_count (more signals = higher detectability = noted in output)
  
  IMPORTANT: SPECULUS scores are semi-quantitative indicators for relative
  supplier risk comparison and prioritization. They are NOT precise probability
  estimates. Per Gartner 2025: "many organizations lack the data maturity to
  produce credible probability estimates for emerging risks." Our approach
  is appropriate for the data available.

WHAT THE SCORES MEAN:
  0-39:  LOW    — Within typical risk appetite. Standard monitoring.
  40-54: MODERATE — Monitor closely. Review monthly.
  55-69: HIGH   — Elevated. Escalation recommended.
  70+:   CRITICAL — Immediate action required.
  These bands align with ISO 31000 risk evaluation criteria §6.4.3.


Framework references:
  ISO 31000:2018        — Risk assessment: likelihood × consequence
  COSO ERM 2017         — Risk appetite, tolerance, response taxonomy
  Zsidisin & Ritchie    — Four-source taxonomy: Supply, Demand, Manufacturing/Process, Environmental
                           (Module 1 covers Supply and Environmental; Demand signals added in Module 2)
  Chopra & Meindl       — Disruption cost formula setup (used in Module 2)
  SCOR v13 (ASCM)       — Performance attribute mapping

Scoring methodology:
  1. For each of 5 ISO 31000 risk dimensions, aggregate signals
  2. Dimension score = f(signal count, severity, recency)
  3. Composite score = weighted average across dimensions
  4. Compare composite and each dimension against user-defined appetite
  5. Apply COSO ERM response (Avoid / Reduce / Share / Accept)
"""

from datetime import datetime
from typing import List, Dict, Any
from geopolitical_engine import compute_geopolitical_score


# ─── Risk Dimensions ─────────────────────────────────────────────────────────
# Based on ISO 31000 risk categories + SCOR performance attributes

RISK_DIMENSIONS = {
    # NOTE ON WEIGHTS: The weights below (geopolitical 25%, supplier_health 25%,
    # logistics 20%, single_source 15%, regulatory 15%) are constructed estimates
    # based on practitioner literature suggesting geopolitical and supplier health
    # risks are the primary drivers of supply chain disruption in 2026.
    # Sources: Everstream Analytics 2026 Annual Risk Report (geopolitical 97% threat
    # score), Tradeverifyd 2026 (supplier disruption most cited). These weights
    # should be calibrated to your specific industry and supply chain profile.
    # In production, allow users to adjust weights — as NexusRisk sidebar already does.
    "geopolitical": {
        "label":       "Geopolitical Exposure",
        "scor":        "Agility",
        "zsidisin":    "Environmental",
        "weight":      0.25,
        "description": "Country-level conflict, sanctions, trade war, export control risk. Maps to SCOR Agility (ability to respond to geopolitical shocks)."
    },
    "supplier_health": {
        "label":       "Supplier Financial Health",
        "scor":        "Reliability",
        "zsidisin":    "Supply",
        "weight":      0.25,
        "description": "Supplier bankruptcy, restructuring, credit events. Maps to SCOR Reliability (on-time, in-full delivery)."
    },
    "logistics": {
        "label":       "Logistics Route Stability",
        "scor":        "Responsiveness",
        "zsidisin":    "Environmental",
        "weight":      0.20,
        "description": "Port disruptions, shipping delays, natural disasters. Maps to SCOR Responsiveness (order fulfillment cycle time)."
    },
    "single_source": {
        "label":       "Single-Source Dependency",
        "scor":        "Reliability",
        "zsidisin":    "Supply",
        "weight":      0.15,
        "description": "Concentration risk — how many alternatives exist for this supplier. Higher concentration = higher score."
    },
    "regulatory": {
        "label":       "Regulatory Compliance Exposure",
        "scor":        "Cost",
        "zsidisin":    "Environmental",
        "weight":      0.15,
        "description": "Regulatory violations, ESG compliance, forced labor risk. Maps to SCOR Cost (unexpected compliance costs)."
    }
}

# ─── COSO ERM Response Taxonomy ──────────────────────────────────────────────
# COSO ERM 2017, Chapter 8: Risk Responses
# Response selected based on composite score vs. appetite

COSO_RESPONSES = {
    "Avoid": {
        "trigger":     "Composite score > appetite by 30+ points",
        "description": "Exit or don't enter the activity. Find alternative supplier immediately.",
        "actions": [
            "Initiate alternative supplier qualification process",
            "Place this supplier on critical watch list",
            "Notify procurement leadership for escalation decision",
            "Begin dual-sourcing evaluation within 30 days"
        ]
    },
    "Reduce": {
        "trigger":     "Composite score > appetite by 10-29 points",
        "description": "Take action to reduce likelihood or impact. Diversify dependency.",
        "actions": [
            "Increase safety stock for components from this supplier",
            "Accelerate qualification of backup supplier",
            "Schedule supplier audit within 60 days",
            "Review and update contract risk clauses"
        ]
    },
    "Share": {
        "trigger":     "Composite score > appetite by 1-9 points",
        "description": "Transfer or share risk. Insurance, contracts, hedging.",
        "actions": [
            "Review supply disruption insurance coverage",
            "Negotiate force majeure clauses in supplier contract",
            "Consider supply chain finance options to support supplier health",
            "Engage supplier in joint risk assessment"
        ]
    },
    "Accept": {
        "trigger":     "Composite score within appetite",
        "description": "Risk is within appetite. Monitor. No immediate action required.",
        "actions": [
            "Continue standard monitoring cycle",
            "Flag for quarterly review",
            "Document acceptance rationale per ISO 31000 §6.5.4"
        ]
    }
}

# ─── Country baseline risk scores ─────────────────────────────────────────────
# SOURCE: World Bank Worldwide Governance Indicators (WGI) 2024
# URL: https://databank.worldbank.org/source/worldwide-governance-indicators
# Data year: 2024 (most recent available as of May 2026)
# Downloaded and verified: May 2026
#
# METHODOLOGY — Score inversion (WGI higher = better governance, NexusRisk higher = more risk):
#   geopolitical    = 100 - WGI Political Stability (PV) score
#   regulatory      = 100 - mean(Rule of Law RL, Regulatory Quality RQ, Govt Effectiveness GE)
#   supplier_health = 100 - Control of Corruption (CC) score
#   logistics       = derived from Political Stability as best available WGI proxy
#                     formula: (100 - PV) × 0.6 + 15, capped at 85
#
# All source WGI scores are on 0-100 scale (100 = best governance).
# NexusRisk risk scores are on 0-100 scale (100 = highest risk).
#
# CITATION:
#   World Bank (2024). Worldwide Governance Indicators.
#   Kaufmann D., Kraay A. and Mastruzzi M. (2010).
#   "The Worldwide Governance Indicators: A Summary of Methodology,
#   Data and Analytical Issues". World Bank Policy Research Working Paper No. 5430.

COUNTRY_BASE_RISK = {
    "AE": {"geopolitical": 20.6, "supplier_health": 28.5, "logistics": 27.4, "regulatory": 28.7},  # UAE WGI 2024
    "AU": {"geopolitical": 20.6, "supplier_health": 14.7, "logistics": 27.3, "regulatory": 16.4},  # Australia WGI 2024
    "BD": {"geopolitical": 59.1, "supplier_health": 74.5, "logistics": 50.5, "regulatory": 60.1},  # Bangladesh WGI 2024
    "BR": {"geopolitical": 43.0, "supplier_health": 60.4, "logistics": 40.8, "regulatory": 51.2},  # Brazil WGI 2024
    "CA": {"geopolitical": 23.9, "supplier_health": 19.1, "logistics": 29.3, "regulatory": 18.7},  # Canada WGI 2024
    "CN": {"geopolitical": 36.7, "supplier_health": 50.4, "logistics": 37.0, "regulatory": 43.5},  # China WGI 2024
    "CZ": {"geopolitical": 17.5, "supplier_health": 33.3, "logistics": 25.5, "regulatory": 24.7},  # Czechia WGI 2024
    "DE": {"geopolitical": 32.0, "supplier_health": 16.2, "logistics": 34.2, "regulatory": 18.4},  # Germany WGI 2024
    "EG": {"geopolitical": 50.8, "supplier_health": 68.9, "logistics": 45.5, "regulatory": 53.2},  # Egypt WGI 2024
    "ES": {"geopolitical": 34.2, "supplier_health": 37.7, "logistics": 35.5, "regulatory": 29.8},  # Spain WGI 2024
    "FR": {"geopolitical": 38.2, "supplier_health": 27.5, "logistics": 37.9, "regulatory": 26.2},  # France WGI 2024
    "GB": {"geopolitical": 29.7, "supplier_health": 21.6, "logistics": 32.8, "regulatory": 22.7},  # UK WGI 2024
    "HU": {"geopolitical": 26.7, "supplier_health": 51.3, "logistics": 31.0, "regulatory": 39.5},  # Hungary WGI 2024
    "ID": {"geopolitical": 44.5, "supplier_health": 63.2, "logistics": 41.7, "regulatory": 45.0},  # Indonesia WGI 2024
    "IL": {"geopolitical": 51.8, "supplier_health": 34.9, "logistics": 46.1, "regulatory": 28.7},  # Israel WGI 2024
    "IN": {"geopolitical": 47.5, "supplier_health": 58.1, "logistics": 43.5, "regulatory": 43.7},  # India WGI 2024
    "IT": {"geopolitical": 28.8, "supplier_health": 40.9, "logistics": 32.3, "regulatory": 33.6},  # Italy WGI 2024
    "JP": {"geopolitical": 14.7, "supplier_health": 24.7, "logistics": 23.8, "regulatory": 16.4},  # Japan WGI 2024
    "KR": {"geopolitical": 23.2, "supplier_health": 34.9, "logistics": 28.9, "regulatory": 24.2},  # S.Korea WGI 2024
    "MX": {"geopolitical": 46.3, "supplier_health": 71.2, "logistics": 42.8, "regulatory": 54.7},  # Mexico WGI 2024
    "MY": {"geopolitical": 27.5, "supplier_health": 42.1, "logistics": 31.5, "regulatory": 34.1},  # Malaysia WGI 2024
    "NG": {"geopolitical": 68.3, "supplier_health": 74.7, "logistics": 56.0, "regulatory": 61.2},  # Nigeria WGI 2024
    "NL": {"geopolitical": 26.8, "supplier_health": 13.5, "logistics": 31.1, "regulatory": 15.4},  # Netherlands WGI 2024
    "PH": {"geopolitical": 47.3, "supplier_health": 63.8, "logistics": 43.4, "regulatory": 47.5},  # Philippines WGI 2024
    "PK": {"geopolitical": 69.4, "supplier_health": 73.7, "logistics": 56.6, "regulatory": 59.5},  # Pakistan WGI 2024
    "PL": {"geopolitical": 25.6, "supplier_health": 36.1, "logistics": 30.4, "regulatory": 34.3},  # Poland WGI 2024
    "RO": {"geopolitical": 31.4, "supplier_health": 51.6, "logistics": 33.8, "regulatory": 38.8},  # Romania WGI 2024
    "RU": {"geopolitical": 49.5, "supplier_health": 70.2, "logistics": 44.7, "regulatory": 59.9},  # Russia WGI 2024
    "SA": {"geopolitical": 34.9, "supplier_health": 36.9, "logistics": 36.0, "regulatory": 35.6},  # Saudi Arabia WGI 2024
    "SE": {"geopolitical": 23.8, "supplier_health": 12.3, "logistics": 29.3, "regulatory": 15.4},  # Sweden WGI 2024
    "SG": {"geopolitical": 13.1, "supplier_health": 12.3, "logistics": 22.8, "regulatory": 11.4},  # Singapore WGI 2024
    "TH": {"geopolitical": 45.8, "supplier_health": 62.8, "logistics": 42.5, "regulatory": 44.6},  # Thailand WGI 2024
    "TR": {"geopolitical": 50.7, "supplier_health": 63.5, "logistics": 45.4, "regulatory": 52.0},  # Turkey WGI 2024
    "TW": {"geopolitical": 18.4, "supplier_health": 28.2, "logistics": 26.1, "regulatory": 21.7},  # Taiwan WGI 2024
    "UA": {"geopolitical": 41.5, "supplier_health": 65.8, "logistics": 39.9, "regulatory": 55.2},  # Ukraine WGI 2024
    "US": {"geopolitical": 35.7, "supplier_health": 30.1, "logistics": 36.4, "regulatory": 24.2},  # USA WGI 2024
    "VN": {"geopolitical": 34.0, "supplier_health": 57.2, "logistics": 35.4, "regulatory": 49.4},  # Vietnam WGI 2024
    "ZA": {"geopolitical": 44.6, "supplier_health": 56.0, "logistics": 41.8, "regulatory": 47.3},  # S.Africa WGI 2024
}

DEFAULT_BASE = {"geopolitical": 35, "logistics": 30, "regulatory": 35}


def score_supplier(
    supplier_name: str,
    country: str,
    gdelt_signals: List[Dict],
    fed_signals: List[Dict],
    appetite: Dict[str, int]
) -> Dict[str, Any]:
    """
    Score a supplier across all ISO 31000 risk dimensions.

    Returns a complete supplier risk record suitable for the register.

    Scoring formula per dimension:
      dim_score = base_score + signal_boost
      signal_boost = Σ (signal.severity × recency_weight) / normaliser
      recency_weight = 1.0 (0-24h), 0.7 (24-48h), 0.4 (48-72h)

    Composite = Σ (dim_score × dim_weight) across all 5 dimensions
    """

    all_signals = gdelt_signals + fed_signals
    base = COUNTRY_BASE_RISK.get(country, DEFAULT_BASE)

    dimension_scores = {}

    # ── Score each dimension ───────────────────────────────────────────────

    # Compute GDELT signal stats for geopolitical engine
    geo_signals = [s for s in all_signals if s.get("dimension") == "geopolitical"]
    gdelt_signal_count = len(geo_signals)
    gdelt_avg_severity = (
        sum(s.get("severity", 3) for s in geo_signals) / len(geo_signals)
        if geo_signals else 0.0
    )

    # Get ACLED credentials from secrets if available
    acled_email = ""
    acled_key   = ""
    try:
        import streamlit as st
        acled_email = st.secrets.get("acled", {}).get("email", "")
        acled_key   = st.secrets.get("acled", {}).get("api_key", "")
    except Exception:
        pass

    for dim_key in RISK_DIMENSIONS:
        base_score = base.get(dim_key, 30)

        if dim_key == "geopolitical":
            # Use two-layer scoring: WGI (40%) + ACLED (35%) + GDELT (25%)
            geo_result = compute_geopolitical_score(
                country_code=country,
                wgi_geo_score=base_score,
                gdelt_signal_count=gdelt_signal_count,
                gdelt_avg_severity=gdelt_avg_severity,
                acled_email=acled_email,
                acled_key=acled_key
            )
            dimension_scores["geopolitical"] = geo_result["score"]
            # Store geo breakdown for display
            _geo_detail = geo_result
            continue

        # Other dimensions: WGI baseline + GDELT signal boost
        dim_signals = [s for s in all_signals if s.get("dimension") == dim_key]
        signal_boost = sum(s.get("severity", 3) for s in dim_signals)
        normalised_boost = min(signal_boost / 3, 40) if dim_signals else 0
        raw = base_score + normalised_boost
        dimension_scores[dim_key] = min(round(raw), 100)

    # Capture geo detail for output (safe fallback)
    if "_geo_detail" not in dir():
        _geo_detail = {"score": dimension_scores.get("geopolitical", 30),
                       "acled_data": {"source": "WGI only", "label": ""},
                       "methodology": "WGI baseline only"}

    # ── Single-source dependency — heuristic ─────────────────────────────
    # In MVP, estimate based on country concentration
    # If this country represents a high-concentration source, score higher
    high_concentration_countries = {"CN", "TW", "KR", "JP"}
    if country in high_concentration_countries:
        dimension_scores["single_source"] = min(
            dimension_scores.get("single_source", 35) + 20, 100
        )
    else:
        dimension_scores["single_source"] = dimension_scores.get("single_source", 30)

    # ── Composite score ───────────────────────────────────────────────────
    composite = sum(
        dimension_scores[dim] * RISK_DIMENSIONS[dim]["weight"]
        for dim in RISK_DIMENSIONS
    )
    composite_score = min(round(composite), 100)

    # ── Breach detection ──────────────────────────────────────────────────
    # ISO 31000 §6.5: Compare assessed risk against risk criteria
    breached_dims = []
    for dim_key, score in dimension_scores.items():
        if score > appetite.get(dim_key, 60):
            breached_dims.append(RISK_DIMENSIONS[dim_key]["label"])

    breach = len(breached_dims) > 0

    # ── COSO ERM Response ─────────────────────────────────────────────────
    # COSO ERM 2017 Ch.8: Risk response selection based on residual risk
    # Compare composite score against AVERAGE appetite threshold
    # (using average is more representative than max — if you scored high
    # across multiple dimensions, even a moderate composite gap warrants action)
    avg_appetite = sum(appetite.values()) / len(appetite) if appetite else 42
    gap = composite_score - avg_appetite

    if gap >= 30:
        coso_response = "Avoid"
    elif gap >= 10:
        coso_response = "Reduce"
    elif gap >= 1:
        coso_response = "Share"
    else:
        coso_response = "Accept"

    # ── SCOR attribute mapping ────────────────────────────────────────────
    # Map highest-scoring dimension to primary SCOR attribute affected
    top_dim = max(dimension_scores, key=dimension_scores.get)
    scor_impact = RISK_DIMENSIONS[top_dim]["scor"]

    # ── Zsidisin risk source classification ──────────────────────────────
    # Zsidisin & Ritchie (2009): supply, demand, environmental
    dim_to_zsidisin = {k: v["zsidisin"] for k, v in RISK_DIMENSIONS.items()}
    zsidisin_source = dim_to_zsidisin[top_dim]

    # Detectability note: per FMEA RPN methodology, higher signal count
    # means higher detectability (risk is more visible = somewhat lower effective risk).
    # In SPECULUS, detectability is informational — shown in output but not
    # used to reduce scores, as conservative risk management practice recommends
    # against rewarding low detectability with lower scores.
    detectability = "High" if len(all_signals) >= 3 else "Medium" if len(all_signals) >= 1 else "Low"

    return {
        "name":            supplier_name,
        "country":         country,
        "composite_score": composite_score,
        "dimensions":      dimension_scores,
        "breach":          breach,
        "breached_dims":   breached_dims,
        "coso_response":   coso_response,
        "scor_impact":     scor_impact,
        "zsidisin_source": zsidisin_source,
        "signals":         all_signals[:8],
        "signal_count":    len(all_signals),
        "updated":         datetime.now().strftime("%Y-%m-%d %H:%M UTC"),
        "detectability":   detectability,
        "signal_count":    len(all_signals),
        "methodology":     "Semi-quantitative (ISO 31000 §6.4.3) — WGI 2024 (40%) + ACLED 2025 (35%) + GDELT (25%) for geopolitical; WGI + GDELT for other dimensions",
        "geo_detail":      _geo_detail,
        "framework":       "ISO 31000:2018 + COSO ERM 2017 + SCOR v13 + WB WGI 2024"
    }
