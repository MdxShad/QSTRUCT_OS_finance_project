Q‑Struct OS
============

Q‑Struct OS is a research prototype and decision‑intelligence sandbox for quoting synthetic structured products.  It is **not** a trading bot, pricing engine, investment advice tool, or general chatbot.  The goal of the MVP is to explore how small changes to a client RFQ (request for quote) can improve the probability of execution while protecting desk economics, risk limits, documentation quality and execution speed.

The current version focuses on autocallable/snowball/worst‑of/barrier note RFQs in APAC distributor style using only **synthetic data**.  It exposes a small FastAPI backend with a React/TypeScript frontend.  All results are purely illustrative and require human review.

## What this is not

- It is not connected to any broker or trading API.
- It does not provide real pricing and makes no guarantee of profitability.
- It never uses real client data – only synthetic demo data is supplied.
- It is not investment advice.  Every suggestion requires human approval.

## Project structure

```
qstruct-os/
├── backend/                  # FastAPI application
│   ├── app/
│   │   ├── main.py           # entry point for the API server
│   │   ├── models/           # Pydantic models
│   │   ├── rfq_parser/       # simple RFQ parser using regex and rules
│   │   ├── payoff_grammar/   # grammar validation rules
│   │   ├── risk_engine/      # synthetic risk scoring
│   │   ├── hit_probability/  # win probability and desk economics
│   │   ├── optimizer/        # counterfactual alternative generator
│   │   ├── explanation/      # explanation builder
│   │   ├── audit/            # audit logging
│   │   └── demo_data/        # synthetic demo data used by the backend
│   ├── requirements.txt      # python dependencies
│   └── README_BACKEND.md     # how to run the backend
├── frontend/                 # React + TypeScript client using Vite
│   ├── package.json          # node dependencies
│   ├── index.html            # entrypoint
│   ├── vite.config.ts        # vite configuration
│   ├── src/
│   │   ├── main.tsx          # client bootstrap
│   │   ├── App.tsx           # root application component
│   │   ├── api/client.ts     # simple fetch wrapper for API calls
│   │   ├── components/       # UI components (input form, panels, tables, etc.)
│   │   └── styles/           # stylesheet
│   └── README_FRONTEND.md    # how to run the frontend
├── docs/                     # product and technical documentation
│   ├── product_thesis.md
│   ├── payoff_grammar.md
│   ├── scoring_logic.md
│   ├── synthetic_data_design.md
│   ├── demo_script.md
│   └── limitations.md
└── README.md                 # this file
```

## Running the backend

You need Python 3.11+ and `pip`.  First install the dependencies:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Then run the API using Uvicorn:

```bash
uvicorn app.main:app --reload
```

This will start the server on `http://localhost:8000`.  Use the interactive documentation at `http://localhost:8000/docs` to test the endpoints.

## Running the frontend

You need Node 18+ and `npm`.  From the project root:

```bash
cd frontend
npm install
npm run dev
```

This starts a Vite development server (typically at `http://localhost:5173`) and proxies API calls to the backend.  See `README_FRONTEND.md` for details.

## Demo RFQ

A sample RFQ that you can paste into the UI or call through the API is:

> "Client wants 2Y USD autocallable, quarterly observation, worst‑of basket on Nvidia, Samsung and HSI, KI 60%, KO 100%, target coupon 11‑13%, callable after 6M, note format, APAC distributor."

The backend parses the text into a formal payoff object, scores the risk, win probability and desk economics, generates several counterfactual alternatives, recommends one, and logs an audit record.  All values are synthetic.

## Limitations

See `docs/limitations.md` for a detailed list of limitations.  In short, this system operates entirely on synthetic data and simplified scoring rules.  It is not a real pricing engine, does not capture the complexity of structured products, and must never be used for production trading decisions.