# Demo Script

This demo script walks through a typical workflow using the Q‑Struct OS prototype.  It assumes that the backend and frontend have been installed and are running locally.

## 1. Start the backend

```bash
cd qstruct-os/backend
source .venv/bin/activate  # activate your virtual environment
uvicorn app.main:app --reload
```

You should see Uvicorn start up on `http://localhost:8000`.  Open `http://localhost:8000/docs` in your browser to explore the API endpoints.

## 2. Start the frontend

Open a new terminal:

```bash
cd qstruct-os/frontend
npm install
npm run dev
```

This will launch a Vite development server on `http://localhost:5173` and automatically open the application in your default browser.

## 3. Enter an RFQ

On the left panel of the UI, click **Seed Demo** to populate the input box with a sample RFQ:

> Client wants 2Y USD autocallable, quarterly observation, worst‑of basket on Nvidia, Samsung and HSI, KI 60%, KO 100%, target coupon 11‑13%, callable after 6M, note format, APAC distributor.

Alternatively, you can type your own free‑form RFQ using the same style.

## 4. Parse the RFQ

Click **Parse** to extract a structured payoff object.  The middle panel shows the fields that were successfully detected (product type, currency, tenor, coupon range, underlyings, etc.).  Any missing fields are listed below the input box.

## 5. Optimise the quote

Click **Optimize** to run the full optimisation pipeline.  The UI will update with:

- **Quote quality cards** showing synthetic win probability, desk economics and risk scores.
- **Counterfactual alternatives** presented in a table, ranked by final score.  The recommended alternative is highlighted.
- **Explanation panel** summarising why the recommended alternative may help the client and the desk.
- **Audit trace** listing previous optimisation runs with timestamps and recommendations.

## 6. Inspect the audit log

The audit panel updates automatically after each optimisation.  You can also query past records via the API:

```bash
curl http://localhost:8000/api/audit
```

Each record includes the audit ID, timestamp, parsed payoff, scores and recommended alternative ID.

## 7. Review limitations

Remember that all calculations and recommendations are synthetic and should **never** be used for real trading or investment decisions.  Consult the [limitations](limitations.md) document for details.
