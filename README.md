# COBOL Modernization Assistant

A tool that analyzes legacy COBOL mainframe programs and helps migrate them to modern Python — combining rule-based parsing with AI-powered explanation and code conversion.

Built by **Manoharan Mudaliar** — 13+ years IBM Mainframe Developer currently leading IMS/DB2-to-SAP modernization at Accenture.

---

## Why This Exists

Enterprises run billions of transactions daily on COBOL mainframe systems written in the 1980s–90s. The original developers have retired. Nobody fully understands what the code does. Migrating it is risky and expensive.

This tool bridges that gap — using rule-based parsing to extract structure and metrics, and AI to explain business logic in plain English and generate equivalent Python code.

---

## Features

| Feature | Description |
|---|---|
| **Rule-based Parser** | Extracts divisions, variables, files, paragraphs, PERFORM calls |
| **Complexity Scoring** | Scores programs LOW / MEDIUM / HIGH / VERY HIGH based on IF, EVALUATE, GO TO, CICS, DB2, IMS |
| **Migration Warnings** | Flags GO TO statements, CICS commands, IMS DLI calls, DB2 SQL |
| **AI Explanation** | Plain-English description of what the program does and why |
| **Python Conversion** | AI-generated equivalent Python 3 code with type hints and docstrings |
| **Migration Plan** | Phased migration roadmap with effort estimate, risk level, and testing strategy |
| **Web UI** | Clean browser interface — paste COBOL, get full analysis |
| **Sample Programs** | Includes real COBOL samples: customer billing, account reconciliation |

---

## Tech Stack

- **Python 3** — core language
- **Flask** — web framework
- **Claude API (Anthropic)** — AI explanation and code conversion
- **Rule-based NLP** — regex-driven COBOL structure extraction

---

## Getting Started

```bash
# Clone the repo
git clone https://github.com/yourusername/cobol-modernization-assistant
cd cobol-modernization-assistant

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py

# Open browser
http://localhost:5000
```

---

## How It Works

```
COBOL Source
     │
     ▼
CobolParser (rule-based)
     │ ├── Divisions detected
     │ ├── Variables extracted
     │ ├── Files & FD parsed
     │ ├── Paragraphs & PERFORM calls mapped
     │ └── Complexity scored
     │
     ▼
AI Analyzer (Claude API)
     │ ├── Plain-English explanation
     │ ├── Python 3 conversion
     │ └── Migration plan
     │
     ▼
Web UI (Flask + HTML)
     └── Results rendered in browser
```

---

## Sample Programs Included

**CUSTBILL.cbl** — Customer Billing Calculation
- Reads customer master file (VSAM sequential)
- Applies residential/commercial/industrial rates
- Computes discounts based on usage thresholds
- Calculates tax and writes billing output
- Logs errors for inactive/zero-usage accounts

**ACCTRECON.cbl** — Account Reconciliation
- Compares mainframe balances vs external system
- Flags out-of-balance records within tolerance
- Identifies MF-only and EXT-only accounts
- Produces reconciliation report

---

## Background

This project reflects real problems I work on daily:

- **Out-of-balance analysis** between mainframe and SAP during migration
- **IMS and DB2 application migration** to modern platforms
- **ETL pipeline monitoring** and batch job management
- **Business rule documentation** for legacy COBOL programs

The same skills that make a mainframe developer valuable also make them the best person to build and validate AI-assisted modernization tools.

---

## Project Structure

```
cobol-modernization-assistant/
├── app.py                  # Flask web application
├── cobol_parser.py         # Rule-based COBOL parser
├── ai_analyzer.py          # Claude API integration
├── requirements.txt        # Python dependencies
├── templates/
│   └── index.html          # Web UI
└── sample_cobol/
    ├── CUSTBILL.cbl        # Customer billing sample
    └── ACCTRECON.cbl       # Reconciliation sample
```

---

## License

MIT
