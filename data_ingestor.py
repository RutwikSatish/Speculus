"""
data_ingestor.py — SPECULUS Signal Ingestion Layer

PERFORMANCE FIX: Single compound query per supplier (was 24 calls per supplier).
Timeout: 3 seconds hard limit per request.
Demo mode: bypasses all network calls entirely.

Sources (all free, no API key required):
  1. GDELT 2.0 Doc API  — geopolitical events, disruption news
  2. Federal Register RSS — US tariff and trade policy changes

Framework alignment:
  ISO 31000:2018 §6.4.2 — Risk identification requires
  continuous environmental scanning.
"""

import requests
import urllib.parse
from datetime import datetime, timedelta
from typing import List, Dict

GDELT_BASE = "https://api.gdeltproject.org/api/v2/doc/doc"

# Single combined risk keyword string for compound GDELT query
# One query per supplier instead of 24
RISK_TERMS = (
    "sanctions OR tariff OR \"export controls\" OR \"trade war\" OR "
    "conflict OR blockade OR embargo OR "
    "\"port strike\" OR \"shipping disruption\" OR \"factory fire\" OR "
    "earthquake OR flood OR \"supply shortage\" OR \"plant closure\" OR "
    "bankruptcy OR insolvency OR layoffs OR \"factory shutdown\" OR "
    "restructuring OR \"forced labor\" OR \"compliance violation\" OR recall"
)

COUNTRY_NAMES = {
    "CN": "China", "TW": "Taiwan", "KR": "South Korea",
    "JP": "Japan", "DE": "Germany", "US": "United States",
    "IN": "India", "MX": "Mexico", "VN": "Vietnam",
    "TH": "Thailand", "MY": "Malaysia", "SG": "Singapore",
    "ID": "Indonesia", "PH": "Philippines", "BD": "Bangladesh",
    "PK": "Pakistan", "BR": "Brazil", "TR": "Turkey",
    "GB": "United Kingdom", "FR": "France", "IT": "Italy",
    "ES": "Spain", "NL": "Netherlands", "SE": "Sweden",
    "PL": "Poland", "CZ": "Czech Republic", "HU": "Hungary",
    "RO": "Romania", "ZA": "South Africa", "EG": "Egypt",
    "NG": "Nigeria", "SA": "Saudi Arabia", "AE": "UAE",
    "IL": "Israel", "UA": "Ukraine", "RU": "Russia",
    "CA": "Canada", "AU": "Australia", "NZ": "New Zealand",
}

# Keyword → ISO 31000 dimension classifier
DIMENSION_MAP = {
    "sanctions": "geopolitical", "tariff": "geopolitical",
    "export controls": "geopolitical", "trade war": "geopolitical",
    "conflict": "geopolitical", "blockade": "geopolitical",
    "embargo": "geopolitical", "military": "geopolitical",
    "port strike": "logistics", "shipping disruption": "logistics",
    "factory fire": "logistics", "earthquake": "logistics",
    "flood": "logistics", "typhoon": "logistics",
    "supply shortage": "logistics", "plant closure": "logistics",
    "port congestion": "logistics",
    "bankruptcy": "supplier_health", "insolvency": "supplier_health",
    "layoffs": "supplier_health", "factory shutdown": "supplier_health",
    "restructuring": "supplier_health", "financial difficulty": "supplier_health",
    "forced labor": "regulatory", "compliance violation": "regulatory",
    "recall": "regulatory", "penalty": "regulatory",
    "environmental fine": "regulatory", "safety violation": "regulatory",
}


# Company aliases for broader GDELT coverage
COMPANY_ALIASES = {
    "TSMC":               ["TSMC", "Taiwan Semiconductor", "Taiwan chip"],
    "Foxconn":            ["Foxconn", "Hon Hai", "Apple supplier China"],
    "Samsung Electronics":["Samsung Electronics", "Samsung foundry"],
    "Bosch Automotive":   ["Bosch", "Robert Bosch"],
    "Tata Steel":         ["Tata Steel", "Tata Group"],
    "Flex Ltd":           ["Flex Ltd", "Flextronics"],
    "Jabil Circuit":      ["Jabil"],
    "Murata Manufacturing":["Murata"],
    "Infineon Technologies":["Infineon"],
    "DHL Supply Chain":   ["DHL", "Deutsche Post DHL"],
    "Reliance Industries":["Reliance Industries", "Mukesh Ambani"],
}


def fetch_gdelt_signals(supplier_name: str, country_code: str) -> List[Dict]:
    """
    Compound query per supplier with aliases — broader coverage.
    Timeout: 3 seconds. Returns empty list on any failure.
    """
    signals = []
    country_name = COUNTRY_NAMES.get(country_code, country_code)

    # Build supplier search terms (use aliases if available)
    aliases = COMPANY_ALIASES.get(supplier_name, [supplier_name])
    supplier_terms = " OR ".join(f'"{a}"' for a in aliases[:3])

    # Combine supplier/country with risk terms
    query = f'({supplier_terms} OR "{country_name}") ({RISK_TERMS})'
    encoded = urllib.parse.quote(query)

    url = (
        f"{GDELT_BASE}"
        f"?query={encoded}"
        f"&mode=artlist"
        f"&maxrecords=10"
        f"&timespan=72h"
        f"&sort=DateDesc"
        f"&format=json"
    )

    try:
        resp = requests.get(url, timeout=3)  # 3 second hard limit
        if resp.status_code != 200:
            return []

        data = resp.json()
        articles = data.get("articles", [])

        for article in articles:
            title = article.get("title", "")
            dimension = _classify_dimension(title)
            signals.append({
                "title":     title[:150],
                "url":       article.get("url", ""),
                "source":    "GDELT",
                "date":      article.get("seendate", ""),
                "dimension": dimension,
                "severity":  _estimate_severity(title, dimension),
                "subject":   country_name
            })

    except Exception:
        # Any failure — timeout, connection error, parse error — returns empty
        # Scoring engine handles missing signals gracefully via WGI baseline
        return []

    # Deduplicate
    seen, deduped = set(), []
    for s in signals:
        key = s["title"][:50].lower()
        if key not in seen:
            seen.add(key)
            deduped.append(s)

    return deduped[:8]


def fetch_federal_register_signals(country_code: str) -> List[Dict]:
    """
    Single RSS fetch for Federal Register trade policy signals.
    Timeout: 3 seconds. Returns empty list on any failure.
    """
    country_name = COUNTRY_NAMES.get(country_code, "")
    if not country_name:
        return []

    encoded = urllib.parse.quote(f"tariff {country_name}")
    feed_url = (
        f"https://www.federalregister.gov/documents/search.rss"
        f"?conditions%5Bterm%5D={encoded}"
        f"&conditions%5Bpublication_date%5D%5Bgte%5D="
        f"{(datetime.now() - timedelta(days=30)).strftime('%m/%d/%Y')}"
    )

    try:
        # Use requests directly — feedparser can hang on slow servers
        resp = requests.get(
            feed_url,
            timeout=3,
            headers={"User-Agent": "SPECULUS/1.0 Supply Chain Risk Intelligence"}
        )
        if resp.status_code != 200:
            return []

        # Simple XML parse — no feedparser dependency needed
        import xml.etree.ElementTree as ET
        root = ET.fromstring(resp.content)
        signals = []

        for item in root.findall(".//item")[:3]:
            title_el = item.find("title")
            link_el  = item.find("link")
            pub_el   = item.find("pubDate")

            if title_el is not None and title_el.text:
                signals.append({
                    "title":     title_el.text[:150],
                    "url":       link_el.text if link_el is not None else "",
                    "source":    "Federal Register",
                    "date":      pub_el.text if pub_el is not None else "",
                    "dimension": "regulatory",
                    "severity":  _estimate_fed_severity(title_el.text),
                    "subject":   country_name
                })

        return signals

    except Exception:
        return []


def _classify_dimension(title: str) -> str:
    """Classify a news title into an ISO 31000 risk dimension."""
    title_lower = title.lower()
    for keyword, dimension in DIMENSION_MAP.items():
        if keyword in title_lower:
            return dimension
    return "geopolitical"  # default


def _estimate_severity(title: str, dimension: str) -> int:
    """Estimate signal severity 1-10 from article title keywords."""
    title_lower = title.lower()
    critical = ["war", "conflict", "invasion", "ban", "blockade", "shutdown",
                "bankruptcy", "collapse", "earthquake", "flood", "sanctions",
                "embargo", "forced labor", "recall", "explosion", "fire"]
    moderate = ["tariff", "strike", "shortage", "delay", "disruption", "concern",
                "risk", "threat", "warning", "investigation", "restriction", "penalty"]

    score = 3
    for term in critical:
        if term in title_lower:
            score += 3
            break
    for term in moderate:
        if term in title_lower:
            score += 2
            break
    if dimension == "geopolitical":
        score += 1
    return min(score, 10)


def _estimate_fed_severity(title: str) -> int:
    """Estimate severity of a Federal Register notice."""
    title_lower = title.lower()
    if any(t in title_lower for t in ["emergency", "national security", "ban"]):
        return 8
    if any(t in title_lower for t in ["final rule", "tariff increase", "export control"]):
        return 6
    if any(t in title_lower for t in ["proposed rule", "notice"]):
        return 3
    return 2
