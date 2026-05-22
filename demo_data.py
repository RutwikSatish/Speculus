"""
demo_data.py — NexusRisk Demo Supplier Portfolio

Purpose: Pre-loaded demo data for live demonstrations and portfolio showcasing.

Design principles:
  1. Real company names and correct country codes so WGI scores are genuine
  2. Geographic and risk diversity — shows full range from low to high risk
  3. Mix of semiconductor, automotive, logistics, and industrial suppliers
     reflecting a realistic mid-size manufacturing company's supplier base
  4. Includes at least one supplier per major risk tier so COSO responses
     across Avoid / Reduce / Share / Accept are all visible in a demo

All companies listed are real publicly known companies.
This data is for demonstration purposes only and does not represent
any actual risk assessment of these companies.
"""

# ─── Demo supplier portfolio ──────────────────────────────────────────────────
# Format: {"name": str, "country": str (ISO 2-letter)}
# Selected to represent a realistic electronics/automotive manufacturer
# sourcing from a globally diversified supplier base.

DEMO_SUPPLIERS = [
    # ── Semiconductor / Electronics ──────────────────────────────────────────
    {"name": "TSMC",                    "country": "TW"},  # Taiwan — high concentration, geopolitical exposure
    {"name": "Samsung Electronics",     "country": "KR"},  # South Korea — strong governance, some geo risk
    {"name": "Foxconn Technology",      "country": "CN"},  # China — regulatory and trade policy signals
    {"name": "Murata Manufacturing",    "country": "JP"},  # Japan — low risk, high governance
    {"name": "Infineon Technologies",   "country": "DE"},  # Germany — low risk, EU regulatory stability

    # ── Logistics and Distribution ───────────────────────────────────────────
    {"name": "DHL Supply Chain",        "country": "DE"},  # Germany — stable
    {"name": "Flex Ltd",                "country": "SG"},  # Singapore — lowest risk in dataset
    {"name": "Jabil Circuit",           "country": "MY"},  # Malaysia — moderate, some corruption exposure

    # ── Raw Materials and Components ─────────────────────────────────────────
    {"name": "Bosch Automotive",        "country": "DE"},  # Germany — benchmark low risk
    {"name": "Tata Steel",              "country": "IN"},  # India — emerging market, moderate risk
    {"name": "Reliance Industries",     "country": "IN"},  # India — large, some regulatory exposure

    # ── High-Risk Geographies (intentionally included for demo contrast) ─────
    {"name": "Pakistan Vendor A",       "country": "PK"},  # Pakistan — will show high risk + breach
    {"name": "Nigeria Supplier B",      "country": "NG"},  # Nigeria — will show high risk + breach
    {"name": "Bangladesh Garments Co",  "country": "BD"},  # Bangladesh — elevated risk
]

# ─── Demo signals — pre-seeded for realistic scoring during demo ──────────────
# These simulate what GDELT would return in a typical week.
# Used when GDELT is unavailable (offline demo, sandbox, rate limits).
# Labeled clearly as simulated signals.

DEMO_SIGNALS = {
    "TSMC": [
        {
            "title": "Taiwan Strait military exercises increase frequency near strait",
            "source": "DEMO — simulated GDELT signal",
            "date": "2026-05-20",
            "dimension": "geopolitical",
            "severity": 8,
            "subject": "Taiwan",
            "url": "https://gdeltproject.org"
        },
        {
            "title": "US semiconductor export controls extended to advanced chip designs",
            "source": "DEMO — simulated Federal Register",
            "date": "2026-05-18",
            "dimension": "regulatory",
            "severity": 7,
            "subject": "Taiwan",
            "url": "https://federalregister.gov"
        }
    ],
    "Foxconn Technology": [
        {
            "title": "China announces new data regulation compliance requirements for manufacturers",
            "source": "DEMO — simulated GDELT signal",
            "date": "2026-05-19",
            "dimension": "regulatory",
            "severity": 6,
            "subject": "China",
            "url": "https://gdeltproject.org"
        },
        {
            "title": "Supply chain disruptions reported at major Chinese manufacturing hubs",
            "source": "DEMO — simulated GDELT signal",
            "date": "2026-05-17",
            "dimension": "logistics",
            "severity": 5,
            "subject": "China",
            "url": "https://gdeltproject.org"
        }
    ],
    "Pakistan Vendor A": [
        {
            "title": "Pakistan economic crisis deepens, currency reserves at critical low",
            "source": "DEMO — simulated GDELT signal",
            "date": "2026-05-21",
            "dimension": "geopolitical",
            "severity": 8,
            "subject": "Pakistan",
            "url": "https://gdeltproject.org"
        },
        {
            "title": "Pakistan supplier sector faces financing constraints amid IMF conditions",
            "source": "DEMO — simulated GDELT signal",
            "date": "2026-05-20",
            "dimension": "supplier_health",
            "severity": 7,
            "subject": "Pakistan",
            "url": "https://gdeltproject.org"
        }
    ],
    "Nigeria Supplier B": [
        {
            "title": "Nigeria port congestion worsens, logistics delays reported across Lagos",
            "source": "DEMO — simulated GDELT signal",
            "date": "2026-05-22",
            "dimension": "logistics",
            "severity": 7,
            "subject": "Nigeria",
            "url": "https://gdeltproject.org"
        }
    ],
    "Tata Steel": [
        {
            "title": "India regulatory compliance update: new environmental standards for steel producers",
            "source": "DEMO — simulated GDELT signal",
            "date": "2026-05-15",
            "dimension": "regulatory",
            "severity": 4,
            "subject": "India",
            "url": "https://gdeltproject.org"
        }
    ]
}

# ─── Demo mode banner text ────────────────────────────────────────────────────
DEMO_BANNER = """
**Demo Mode** — This register uses a pre-loaded supplier portfolio and 
simulated signals designed to demonstrate NexusRisk capabilities. 
Country risk baseline scores are real (World Bank WGI 2024). 
Signal data is simulated for demonstration purposes and clearly labeled.
Switch to **Live Mode** to ingest real-time signals from GDELT and Federal Register.
"""
