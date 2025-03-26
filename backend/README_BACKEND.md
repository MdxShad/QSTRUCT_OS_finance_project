Backend for Q‑Struct OS
=======================

This directory contains the FastAPI implementation of the Q‑Struct OS backend.  It exposes a handful of endpoints for parsing free‑form RFQ text into a structured payoff object, analysing quote quality and risk, generating counterfactual alternatives, and retrieving past audit records.

## Installation

Ensure you have Python 3.11 or later.  Create a virtual environment and install dependencies:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running the server

Launch the API using Uvicorn.  The `--reload` flag enables hot reloading during development.

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.  An OpenAPI spec and interactive Swagger UI are served at `http://localhost:8000/docs`.

## API endpoints

- **GET /api/health** – returns `{status: "ok", version: "0.1.0"}`.
- **POST /api/rfq/parse** – accepts a JSON body with `raw_text` and optional `client_segment` and `region`.  Returns a structured payoff object and list of missing fields according to the payoff grammar.
- **POST /api/quote/analyze** – parses the RFQ and returns current quote quality metrics: risk assessment, win probability and desk economics.
- **POST /api/quote/optimize** – runs the full optimisation pipeline.  Returns the parsed payoff, missing fields, current scores, a set of alternative structures ranked by synthetic final score, an explanation and a randomly generated audit ID.  Each call appends an audit record to `app/demo_data/audit_log.json`.
- **GET /api/audit** – returns a list of all audit records stored since the server was first started.  Records are persisted in `audit_log.json` within the `demo_data` folder.

## Working with the models

The `app/models` package defines Pydantic models for RFQ inputs (`RFQInput`), payoff objects (`PayoffObject`), missing fields (`MissingField`), risk assessments (`RiskAssessment`), alternatives (`QuoteAlternative`), optimisation results (`OptimizationResult`) and audit records (`AuditRecord`).  These models enforce type validation and allow automatic JSON serialisation.

## Notes

All scoring and optimisation logic is **synthetic** and for demonstration only.  Real structuring, pricing, risk management and documentation require robust quantitative models and legal review.  The current implementation operates solely on artificial heuristic formulas and does not connect to any market data or trading systems.
