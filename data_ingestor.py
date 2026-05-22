"""
data_ingestor.py — NexusRisk Signal Ingestion Layer

Sources (all free, no API key required):
  1. GDELT 2.0 Doc API  — geopolitical events, disruption news
  2. Federal Register RSS — US tariff and trade policy changes

Framework alignment:
  ISO 31000:2018 §6.4.2 — Risk identification requires
  continuous environmental scanning.
"""

import requests
import feedparser
import urllib.parse
from datetime import datetime, timedelta
from typing import List, Dict


# ─── GDELT 2.0 Doc API ───────────────────────────────────────────────────────
# Completely free. No API key. Updated every 15 minutes globally.
# Covers 100+ languages, 65+ countries.
# Docs: https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/

GDELT_BASE = "https://api.gdeltproject.org/api/v2/doc/doc"

# Risk-relevant CAMEO event keywords mapped to our ISO 31000 dimensions
GDELT_RISK_KEYWORDS = {
    "geopolitical": [
        "sanctions", "tariff", "export controls", "trade war",
        "geopolitical", "military", "conflict", "blockade",
        "embargo", "nationalization"
    ],
    "logistics": [
        "port strike", "port congestion", "shipping disruption",
        "factory fire", "earthquake", "flood", "typhoon",
        "supply shortage", "production halt", "plant closure"
    ],
    "supplier_health": [
        "bankruptcy", "insolvency", "layoffs", "factory shutdown",
        "financial difficulty", "credit downgrade", "restructuring"
    ],
    "regulatory": [
        "regulation", "compliance violation", "penalty",
        "forced labor", "ESG", "customs violation", "recall",
        "safety violation", "environmental fine"
    ]
}

# Country name map for GDELT queries (GDELT uses country names not codes)
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


def fetch_gdelt_signals(supplier_name: str, country_code: str) -> List[Dict]:
    """
    Query GDELT 2.0 Doc API for news signals relevant to a supplier
    and its country over the past 72 hours.

    Returns a list of signal dicts with keys:
      title, url, source, date, dimension, severity
    """
    signals = []
    country_name = COUNTRY_NAMES.get(country_code, country_code)

    # Build compound query: supplier name OR country + risk keywords
    # GDELT supports boolean queries
    for dimension, keywords in GDELT_RISK_KEYWORDS.items():
        # Try supplier-specific first, then country-level
        for query_subject in [supplier_name, country_name]:
            # Pick top 3 keywords per dimension to keep queries focused
            for keyword in keywords[:3]:
                query = f'"{query_subject}" "{keyword}"'
                encoded = urllib.parse.quote(query)

                url = (
                    f"{GDELT_BASE}"
                    f"?query={encoded}"
                    f"&mode=artlist"
                    f"&maxrecords=3"
                    f"&timespan=72h"
                    f"&sort=DateDesc"
                    f"&format=json"
                )

                try:
                    resp = requests.get(url, timeout=8)
                    if resp.status_code != 200:
                        continue

                    data = resp.json()
                    articles = data.get("articles", [])

                    for article in articles:
                        signals.append({
                            "title":     article.get("title", "")[:150],
                            "url":       article.get("url", ""),
                            "source":    "GDELT",
                            "date":      article.get("seendate", ""),
                            "dimension": dimension,
                            "severity":  _estimate_severity(article.get("title", ""), dimension),
                            "subject":   query_subject
                        })

                except (requests.RequestException, ValueError, KeyError):
                    # GDELT is eventually consistent — gracefully handle failures
                    continue

    # Deduplicate by title similarity (simple approach)
    seen_titles = set()
    deduped = []
    for s in signals:
        title_key = s["title"][:60].lower()
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            deduped.append(s)

    return deduped[:15]  # cap at 15 signals per supplier


def fetch_federal_register_signals(country_code: str) -> List[Dict]:
    """
    Fetch US Federal Register RSS for trade policy and tariff actions
    relevant to a specific country.

    Federal Register publishes RSS feeds for all new rules and notices.
    This is public domain, no authentication required.
    """
    signals = []
    country_name = COUNTRY_NAMES.get(country_code, "")

    # Federal Register search RSS for trade-related documents
    base_rss = "https://www.federalregister.gov/documents/search.rss"

    # Build search terms relevant to supply chain risk
    search_terms = [
        f"tariff {country_name}",
        f"import duties {country_name}",
        f"export controls {country_name}",
        f"trade restrictions {country_name}",
    ]

    for term in search_terms:
        encoded_term = urllib.parse.quote(term)
        feed_url = (
            f"{base_rss}"
            f"?conditions%5Bterm%5D={encoded_term}"
            f"&conditions%5Bpublication_date%5D%5Bgte%5D="
            f"{(datetime.now() - timedelta(days=30)).strftime('%m/%d/%Y')}"
        )

        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:3]:
                signals.append({
                    "title":     entry.get("title", "")[:150],
                    "url":       entry.get("link", ""),
                    "source":    "Federal Register",
                    "date":      entry.get("published", ""),
                    "dimension": "regulatory",
                    "severity":  _estimate_fed_severity(entry.get("title", "")),
                    "subject":   country_name
                })
        except Exception:
            continue

    return signals[:6]


def _estimate_severity(title: str, dimension: str) -> int:
    """
    Estimate signal severity (1-10) from article title keywords.
    Higher severity = more extreme risk indicator.

    Based on SCOR model disruption severity tiers:
    1-3: Monitor, 4-6: Moderate, 7-10: Critical
    """
    title_lower = title.lower()

    critical_terms = [
        "war", "conflict", "invasion", "ban", "blockade",
        "shutdown", "bankruptcy", "collapse", "catastrophe",
        "earthquake", "flood", "sanctions", "embargo",
        "forced labor", "recall", "explosion", "fire"
    ]
    moderate_terms = [
        "tariff", "strike", "shortage", "delay", "disruption",
        "concern", "risk", "threat", "warning", "investigation",
        "protest", "tension", "restriction", "penalty"
    ]

    score = 3  # baseline
    for term in critical_terms:
        if term in title_lower:
            score += 3
            break
    for term in moderate_terms:
        if term in title_lower:
            score += 2
            break

    # Geopolitical signals carry more weight per Zsidisin environmental risk
    if dimension == "geopolitical":
        score += 1

    return min(score, 10)


def _estimate_fed_severity(title: str) -> int:
    """Estimate severity of a Federal Register notice."""
    title_lower = title.lower()
    if any(t in title_lower for t in ["emergency", "immediate", "national security", "ban"]):
        return 8
    if any(t in title_lower for t in ["final rule", "tariff increase", "export control"]):
        return 6
    if any(t in title_lower for t in ["proposed rule", "notice", "comment period"]):
        return 3
    return 2
