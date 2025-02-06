"""FastAPI entrypoint for the Q‑Struct OS backend.

This module wires together the parser, grammar validator, risk engine,
probability model, optimizer, explainer and audit logging to provide a simple
REST API.  The API is intentionally minimal and returns fully structured
objects that can be consumed by the frontend.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List

from fastapi import FastAPI

from .models.rfq import (
    AuditRecord,
    MissingField,
    OptimizationResult,
    PayoffObject,
    RFQInput,
    QuoteAlternative,
)
from .rfq_parser.parser import parse_rfq
from .payoff_grammar.validator import validate_payoff
from .risk_engine.risk import assess_risk
from .hit_probability.hit_model import estimate_win_probability, estimate_desk_economics, estimate_win_probability_detail
from .optimizer.counterfactual import generate_alternatives
from .explanation.explainer import generate_explanation
from .audit.audit_store import AuditStore


app = FastAPI(title="Q‑Struct OS Backend", version="0.1.0")
audit_store = AuditStore()


@app.get("/api/health")
def health() -> Dict[str, str]:
    """Return basic service status and version."""
    return {"status": "ok", "version": app.version}


@app.post("/api/rfq/parse")
def parse_rfq_endpoint(rfq: RFQInput) -> Dict[str, Any]:
    """Parse a free‑form RFQ into a payoff object, parser notes and missing fields."""
    payoff, missing, notes = parse_rfq(rfq)
    grammar_missing = validate_payoff(payoff)
    return {
        "payoff_object": payoff,
        "missing_fields": missing + grammar_missing,
        "parser_notes": notes,
    }


@app.post("/api/quote/analyze")
def analyze_quote(rfq: RFQInput) -> Dict[str, Any]:
    """Analyze the current quote quality, risk assessment and win probability for an RFQ."""
    payoff, missing, notes = parse_rfq(rfq)
    grammar_missing = validate_payoff(payoff)
    risk = assess_risk(payoff)
    win_detail = estimate_win_probability_detail(payoff)
    desk_econ = estimate_desk_economics(payoff)
    return {
        "payoff_object": payoff,
        "missing_fields": missing + grammar_missing,
        "parser_notes": notes,
        "risk_assessment": risk,
        "win_probability_detail": win_detail,
        "desk_economics_score": desk_econ,
    }


@app.post("/api/quote/optimize")
def optimize_quote(rfq: RFQInput) -> OptimizationResult:
    """Full optimisation pipeline for an RFQ.

    Parses the RFQ, validates the payoff, assesses risk, estimates win probability
    and desk economics, generates counterfactual alternatives, ranks them,
    produces an explanation, persists an audit record, and returns an
    :class:`OptimizationResult` object.
    """
    payoff, missing, notes = parse_rfq(rfq)
    grammar_missing = validate_payoff(payoff)
    # Current scores
    risk = assess_risk(payoff)
    win_detail = estimate_win_probability_detail(payoff)
    desk_econ = estimate_desk_economics(payoff)
    # Alternatives
    alternatives: List[QuoteAlternative] = generate_alternatives(payoff)
    # Explanation
    explanation: str = generate_explanation(alternatives)
    recommended_id: str | None = alternatives[0].alternative_id if alternatives else None
    # Build result
    result = OptimizationResult(
        original_payoff=payoff,
        missing_fields=missing + grammar_missing,
        current_quote_quality={
            "parser_notes": notes,
            "win_probability_detail": win_detail,
            "desk_economics_score": desk_econ,
            "risk_assessment": risk.dict(),
        },
        alternatives=alternatives,
        recommended_alternative_id=recommended_id,
        explanation=explanation,
        limitations="All values are synthetic and for research only. Human review required.",
        audit_id=str(uuid.uuid4()),
    )
    # Persist audit
    audit_store.log_record(result)
    return result


@app.get("/api/audit")
def get_audit() -> List[AuditRecord]:
    """Return the list of past audit records."""
    return audit_store.get_records()
