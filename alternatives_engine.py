"""
alternatives_engine.py — SPECULUS Alternative Supplier Intelligence

When a supplier breaches risk appetite, SPECULUS recommends specific
lower-risk alternatives in the same product/industry category.

Data source: Curated database of major suppliers by category and country,
with estimated qualification timelines from industry benchmarks.

Sources:
  - Qualification timelines: APICS CSCP body of knowledge
  - Supplier lists: publicly known major manufacturers by category
  - Country risk scores: SPECULUS scoring_engine.py (WGI 2024 + ACLED 2025)
"""

from typing import List, Dict


# ─── Supplier alternatives database ──────────────────────────────────────────
# Organized by product category.
# Each entry: {name, country, risk_approx, qualification_months, notes}

ALTERNATIVES_DB = {

    "semiconductor": [
        {"name": "Samsung Foundry",      "country": "KR", "risk": 31, "qual_months": "18-24", "note": "Leading foundry, 3nm capable"},
        {"name": "GlobalFoundries",      "country": "US", "risk": 22, "qual_months": "18-24", "note": "Mature nodes, US-based, CHIPS Act beneficiary"},
        {"name": "Intel Foundry",        "country": "US", "risk": 22, "qual_months": "24-36", "note": "New foundry services, Intel 18A"},
        {"name": "UMC",                  "country": "TW", "risk": 29, "qual_months": "12-18", "note": "Specialty nodes, same geo risk as TSMC"},
        {"name": "SMIC",                 "country": "CN", "risk": 44, "qual_months": "6-12",  "note": "Mature nodes only, US export restriction risk"},
        {"name": "Tower Semiconductor",  "country": "IL", "risk": 52, "qual_months": "12-18", "note": "Analog/mixed signal specialty"},
    ],

    "electronics_assembly": [
        {"name": "Flex Ltd",             "country": "SG", "risk": 17, "qual_months": "6-12",  "note": "Lowest risk EMS provider, Singapore-based"},
        {"name": "Jabil Circuit",        "country": "MY", "risk": 34, "qual_months": "6-12",  "note": "Malaysia operations, strong quality systems"},
        {"name": "Celestica",            "country": "CA", "risk": 18, "qual_months": "6-12",  "note": "Canada-based, strong in aerospace/defense"},
        {"name": "Sanmina",              "country": "US", "risk": 22, "qual_months": "6-12",  "note": "US operations, vertically integrated"},
        {"name": "Wistron",              "country": "TW", "risk": 29, "qual_months": "9-12",  "note": "Same geo risk as Foxconn"},
    ],

    "automotive_components": [
        {"name": "Bosch Automotive",     "country": "DE", "risk": 26, "qual_months": "12-24", "note": "Low-risk, global footprint"},
        {"name": "Continental AG",       "country": "DE", "risk": 26, "qual_months": "12-24", "note": "Tier 1, strong quality systems"},
        {"name": "Aptiv",               "country": "IE", "risk": 15, "qual_months": "18-24", "note": "Ireland-based, excellent governance"},
        {"name": "Magna International", "country": "CA", "risk": 18, "qual_months": "12-24", "note": "Canada, diversified Tier 1"},
        {"name": "Hyundai Mobis",        "country": "KR", "risk": 31, "qual_months": "18-24", "note": "Korean Tier 1, growing global"},
    ],

    "logistics": [
        {"name": "DHL Supply Chain",     "country": "DE", "risk": 26, "qual_months": "1-3",   "note": "Global leader, low risk"},
        {"name": "Kuehne+Nagel",         "country": "CH", "risk": 10, "qual_months": "1-3",   "note": "Switzerland-based, stable"},
        {"name": "DB Schenker",          "country": "DE", "risk": 26, "qual_months": "1-3",   "note": "Rail-road-air multimodal"},
        {"name": "Geodis",               "country": "FR", "risk": 22, "qual_months": "1-3",   "note": "French-based, global network"},
        {"name": "XPO Logistics",        "country": "US", "risk": 22, "qual_months": "1-3",   "note": "US-based, strong LTL"},
    ],

    "raw_materials_steel": [
        {"name": "ArcelorMittal",        "country": "LU", "risk": 8,  "qual_months": "3-6",   "note": "Luxembourg-based, global leader"},
        {"name": "Nucor Corporation",    "country": "US", "risk": 22, "qual_months": "3-6",   "note": "US EAF steel, low risk"},
        {"name": "POSCO",                "country": "KR", "risk": 31, "qual_months": "3-6",   "note": "Korean steel, high quality"},
        {"name": "Thyssenkrupp Steel",   "country": "DE", "risk": 26, "qual_months": "3-6",   "note": "German engineering steel"},
    ],

    "default": [
        {"name": "Diversified Supplier",    "country": "DE", "risk": 26, "qual_months": "6-18", "note": "EU-based alternative recommended"},
        {"name": "North American Supplier", "country": "CA", "risk": 18, "qual_months": "6-18", "note": "Nearshore alternative recommended"},
        {"name": "Southeast Asia Supplier", "country": "SG", "risk": 17, "qual_months": "6-18", "note": "ASEAN alternative — lower risk than CN/TW"},
    ]
}

# Keyword → category classifier
CATEGORY_KEYWORDS = {
    "semiconductor": ["tsmc", "samsung", "foundry", "chip", "wafer", "semiconductor", "smic", "intel fab", "umc"],
    "electronics_assembly": ["foxconn", "jabil", "flex", "wistron", "pegatron", "assembly", "ems", "pcb"],
    "automotive_components": ["bosch", "continental", "aptiv", "denso", "aisin", "automotive", "tier 1", "tier1"],
    "logistics": ["dhl", "fedex", "ups", "shipping", "logistics", "freight", "transport", "kuehne"],
    "raw_materials_steel": ["tata steel", "steel", "arcelormittal", "nucor", "metal", "aluminum"],
}


def get_category(supplier_name: str) -> str:
    """Classify a supplier into a product category."""
    name_lower = supplier_name.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in name_lower for kw in keywords):
            return category
    return "default"


def get_alternatives(
    supplier_name: str,
    supplier_country: str,
    supplier_score: int,
    top_n: int = 3
) -> List[Dict]:
    """
    Return top N lower-risk alternatives for a given supplier.

    Filters out:
    - The supplier itself
    - Suppliers in the same country (same geo risk)
    - Suppliers with higher risk than the breaching supplier

    Returns alternatives sorted by risk score ascending.
    """
    category = get_category(supplier_name)
    candidates = ALTERNATIVES_DB.get(category, ALTERNATIVES_DB["default"])

    alternatives = []
    for alt in candidates:
        # Skip same supplier or same country
        if alt["name"].lower() == supplier_name.lower():
            continue
        if alt["country"] == supplier_country:
            continue
        # Only recommend lower-risk alternatives
        if alt["risk"] < supplier_score:
            alternatives.append(alt)

    # Sort by risk ascending (lowest risk first)
    alternatives.sort(key=lambda x: x["risk"])
    return alternatives[:top_n]


def format_alternatives_for_ai(
    supplier_name: str,
    supplier_country: str,
    supplier_score: int,
    breached_dims: list
) -> str:
    """
    Format alternative supplier data for injection into Groq AI brief prompt.
    """
    alts = get_alternatives(supplier_name, supplier_country, supplier_score)

    if not alts:
        return "No pre-qualified alternatives identified in SPECULUS database for this supplier category."

    lines = [f"RECOMMENDED ALTERNATIVE SUPPLIERS (lower risk, same category):"]
    for i, alt in enumerate(alts, 1):
        lines.append(
            f"  {i}. {alt['name']} ({alt['country']}) — "
            f"Risk score: ~{alt['risk']}/100 — "
            f"Qualification timeline: {alt['qual_months']} months — "
            f"{alt['note']}"
        )

    lines.append(
        f"\nKey consideration: Qualification timeline assumes standard "
        f"supplier approval process per APICS CSCP guidelines. "
        f"Expedited qualification is possible for critical supply continuity."
    )

    return "\n".join(lines)
