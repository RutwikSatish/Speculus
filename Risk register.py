"""
risk_register.py — NexusRisk Register Builder

Produces the ISO 31000-mandated risk register output.
ISO 31000:2018 §6.7: Recording and reporting
  "The organisation should document its risk management process."

Register format follows:
  - ISO 31000:2018 documentation requirements
  - COSO ERM 2017 risk register template
  - ASCM SCOR v13 performance attribute mapping
"""

import csv
import io
from datetime import datetime
from typing import List, Dict, Any

from scoring_engine import RISK_DIMENSIONS, COSO_RESPONSES


def build_register(scored_suppliers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Build the full risk register from scored supplier data.
    Adds COSO response actions and SCOR dimension descriptions.
    Sorts by composite score descending (highest risk first).
    """
    register = []

    for supplier in scored_suppliers:
        coso_key  = supplier.get("coso_response", "Accept")
        coso_data = COSO_RESPONSES.get(coso_key, COSO_RESPONSES["Accept"])

        entry = {
            **supplier,
            "coso_description": coso_data["description"],
            "coso_trigger":     coso_data["trigger"],
            "recommended_actions": coso_data["actions"],
            "register_date":    datetime.now().strftime("%Y-%m-%d"),
            "review_date":      _next_review_date(supplier["composite_score"]),
            "iso_status":       _iso_status(supplier["composite_score"]),
        }

        # Add SCOR dimension labels for reporting clarity
        dim_labels = {}
        for dim_key, score in supplier.get("dimensions", {}).items():
            dim_info = RISK_DIMENSIONS.get(dim_key, {})
            dim_labels[dim_key] = {
                "score":       score,
                "label":       dim_info.get("label", dim_key),
                "scor":        dim_info.get("scor", ""),
                "zsidisin":    dim_info.get("zsidisin", ""),
                "description": dim_info.get("description", "")
            }
        entry["dimension_details"] = dim_labels

        register.append(entry)

    return sorted(register, key=lambda x: x["composite_score"], reverse=True)


def export_register_csv(register: List[Dict[str, Any]]) -> str:
    """
    Export risk register as CSV.
    Column structure matches ISO 31000 documentation requirements.
    """
    output = io.StringIO()

    fieldnames = [
        "Supplier Name",
        "Country Code",
        "Composite Risk Score",
        "ISO Status",
        "COSO Response",
        "COSO Description",
        "Primary SCOR Attribute Affected",
        "Zsidisin Risk Source Type",
        "Geopolitical Score",
        "Supplier Health Score",
        "Logistics Score",
        "Single Source Score",
        "Regulatory Score",
        "Breach Detected",
        "Breached Dimensions",
        "Recommended Actions",
        "Register Date",
        "Next Review Date",
        "Live Signals Detected",
        "Framework"
    ]

    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()

    for entry in register:
        dims = entry.get("dimensions", {})
        writer.writerow({
            "Supplier Name":                     entry.get("name", ""),
            "Country Code":                      entry.get("country", ""),
            "Composite Risk Score":              entry.get("composite_score", 0),
            "ISO Status":                        entry.get("iso_status", ""),
            "COSO Response":                     entry.get("coso_response", ""),
            "COSO Description":                  entry.get("coso_description", ""),
            "Primary SCOR Attribute Affected":   entry.get("scor_impact", ""),
            "Zsidisin Risk Source Type":         entry.get("zsidisin_source", ""),
            "Geopolitical Score":                dims.get("geopolitical", 0),
            "Supplier Health Score":             dims.get("supplier_health", 0),
            "Logistics Score":                   dims.get("logistics", 0),
            "Single Source Score":               dims.get("single_source", 0),
            "Regulatory Score":                  dims.get("regulatory", 0),
            "Breach Detected":                   "YES" if entry.get("breach") else "NO",
            "Breached Dimensions":               "; ".join(entry.get("breached_dims", [])),
            "Recommended Actions":               " | ".join(entry.get("recommended_actions", [])),
            "Register Date":                     entry.get("register_date", ""),
            "Next Review Date":                  entry.get("review_date", ""),
            "Live Signals Detected":             entry.get("signal_count", 0),
            "Framework":                         "ISO 31000:2018 + COSO ERM 2017 + SCOR v13"
        })

    return output.getvalue()


def _next_review_date(composite_score: int) -> str:
    """
    ISO 31000 §6.6: Monitoring and review frequency
    based on risk level.
      Score >= 70: Weekly review
      Score 40-69: Monthly review
      Score < 40:  Quarterly review
    """
    from datetime import timedelta
    now = datetime.now()
    if composite_score >= 70:
        next_date = now + timedelta(weeks=1)
        cadence = "weekly"
    elif composite_score >= 40:
        next_date = now + timedelta(days=30)
        cadence = "monthly"
    else:
        next_date = now + timedelta(days=90)
        cadence = "quarterly"

    return f"{next_date.strftime('%Y-%m-%d')} ({cadence})"


def _iso_status(composite_score: int) -> str:
    """
    ISO 31000-aligned status labels for risk register.
    """
    if composite_score >= 70:
        return "CRITICAL — Immediate action required"
    elif composite_score >= 55:
        return "HIGH — Escalation recommended"
    elif composite_score >= 40:
        return "MODERATE — Monitor closely"
    elif composite_score >= 25:
        return "LOW — Standard monitoring"
    else:
        return "MINIMAL — Quarterly review sufficient"
