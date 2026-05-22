# ◈ SPECULUS
### Supply Chain Risk Intelligence Platform

> *See the risk before it sees you.*

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://speculus.streamlit.app)

---

## What it does

SPECULUS is an ISO 31000-compliant supply chain risk intelligence platform that turns a static spreadsheet into a living, AI-powered risk register. It watches your supplier portfolio continuously — so you don't get blindsided.

**Two core problems solved:**

1. **The risk register dies the moment it's created.** SPECULUS automates the ISO 31000 monitoring loop using live signals from GDELT 2.0 and the US Federal Register. Never stale.

2. **Risk signals exist. Nobody knows what they cost.** SPECULUS scores every supplier against verified World Bank Governance Indicators (WGI 2024) and COSO ERM risk appetite thresholds, then maps each breach to a SCOR performance attribute and recommended action.

---

## Academic foundations

| Framework | Applied in SPECULUS |
|---|---|
| **ISO 31000:2018** | Core risk assessment loop, documentation format, review cadence |
| **COSO ERM 2017** | Risk appetite thresholds, Avoid/Reduce/Share/Accept response taxonomy |
| **SCOR v13 (ASCM)** | Maps each risk dimension to a supply chain performance attribute |
| **Zsidisin & Ritchie (2009)** | Three-source risk taxonomy: Supply, Demand, Environmental |
| **World Bank WGI 2024** | Verified country baseline risk scores (38 countries, 5 indicators) |

---

## Data sources

| Source | Cost | What it provides |
|---|---|---|
| GDELT 2.0 Doc API | Free, no key | Geopolitical events, disruption news, 100+ languages |
| US Federal Register RSS | Free, public domain | Tariff rules, export controls, trade policy |
| World Bank WGI 2024 | Free, public domain | Country governance baseline scores |

---

## Setup

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/speculus.git
cd speculus

# 2. Install
pip install -r requirements.txt

# 3. Add Groq API key (optional — enables AI briefs)
cp .streamlit/secrets.toml.template .streamlit/secrets.toml
# Edit secrets.toml and add your key from console.groq.com

# 4. Run
streamlit run app.py
```

---

## Deploy to Streamlit Cloud (free)

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Set main file: `app.py`
5. Add Groq API key in Settings → Secrets:
```toml
[groq]
api_key = "your_key_here"
```
6. Deploy

---

## Scoring methodology

```
For each supplier:

  1. Fetch live signals (GDELT + Federal Register)
  2. For each of 5 ISO 31000 dimensions:
       dim_score = WGI_baseline + signal_boost
  3. Composite = Σ(dim_score × weight)
       Weights: Geopolitical 25% · Supplier Health 25%
                Logistics 20% · Single-Source 15% · Regulatory 15%
  4. Compare against COSO ERM appetite thresholds
  5. Apply response: Avoid / Reduce / Share / Accept
```

---

## References

- ISO 31000:2018 *Risk management — Guidelines*
- COSO (2017). *Enterprise Risk Management — Integrating with Strategy and Performance*
- ASCM (2022). *SCOR Supply Chain Reference Model v13*
- Zsidisin, G.A. & Ritchie, B. (2009). *Supply Chain Risk*. Springer
- World Bank (2024). *Worldwide Governance Indicators*
- Kaufmann, Kraay & Mastruzzi (2010). WB Policy Research Working Paper No. 5430

---

**Built by Rutwik Satish** · MS Engineering Management, Northeastern University  
Boston, MA · [linkedin.com/in/rutwiksatish](https://linkedin.com/in/rutwiksatish) · [github.com/rutwiksatish](https://github.com/rutwiksatish)
