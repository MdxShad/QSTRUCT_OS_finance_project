"""Pydantic models for RFQs, payoff objects and results.

These models define the input and output schema for the FastAPI backend.  Fields are
optional where the parser may not extract values, and simple types are used to
facilitate JSON serialisation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RFQInput(BaseModel):
    """Raw request for quote input as provided by the client or frontend."""

    raw_text: str = Field(..., description="The free‑form RFQ description.")
    client_segment: Optional[str] = Field(
        None, description="Optional client segment such as APAC distributor, private bank, etc."
    )
    region: Optional[str] = Field(
        None, description="Optional region hint such as APAC, EMEA, Americas."
    )


class PayoffObject(BaseModel):
    """Structured representation of a product payoff extracted from an RFQ."""

    product_type: Optional[str] = None
    currency: Optional[str] = None
    tenor_months: Optional[int] = None
    coupon_target_min: Optional[float] = None
    coupon_target_max: Optional[float] = None
    observation_frequency: Optional[str] = None
    barrier_type: Optional[str] = None
    barrier_level: Optional[float] = None
    autocall_trigger: Optional[float] = None
    basket_rule: Optional[str] = None
    underlyings: Optional[List[str]] = None
    wrapper: Optional[str] = None
    callable_after_months: Optional[int] = None
    client_segment: Optional[str] = None
    region: Optional[str] = None
    confidence_score: Optional[float] = None

    # Phase 2 additional fields
    # notional size of the trade (e.g. in million USD)
    notional: Optional[float] = None
    # settlement type: cash, physical, etc.
    settlement_type: Optional[str] = None
    # whether the issuer has a call right beyond autocall
    issuer_call: Optional[bool] = None
    # whether the coupon has memory (accumulates if missed)
    memory_coupon: Optional[bool] = None
    # coupon barrier level (if different from knock‑in barrier)
    coupon_barrier: Optional[float] = None
    # protection type: e.g. "protected" for principal protection, "capital at risk" otherwise
    protection_type: Optional[str] = None
    # boolean indicating whether capital is at risk (True) or protected (False)
    capital_at_risk: Optional[bool] = None
    # number of names in the basket
    basket_size: Optional[int] = None
    # worst underlying name (for worst‑of structures)
    worst_underlying: Optional[str] = None
    # current market regime (e.g. "bull", "bear", "volatile")
    market_regime: Optional[str] = None
    # jurisdiction or wrapper region (e.g. "HK", "KR", "EU")
    jurisdiction_or_wrapper_region: Optional[str] = None
    # documentation complexity level on a simple scale (e.g. 1–5)
    documentation_complexity_level: Optional[int] = None


class MissingField(BaseModel):
    """Represents a missing field or inconsistency detected while parsing or validating."""

    field_name: str
    severity: str
    reason: str


class RiskAssessment(BaseModel):
    """Synthetic risk assessment with detailed component scores.

    Each score is normalised between 0 and 1, with higher values indicating
    increased risk or complexity.  The `overall_risk_score` is an aggregate
    measure based on the component scores.  The `warnings` list contains
    narrative messages highlighting specific concerns.
    """

    # Distance between the barrier level and full protection (1 – barrier_level/100)
    barrier_distance_score: float
    # Concentration of the basket (e.g. high‑vol names in a worst‑of increase this)
    basket_concentration_score: float
    # Penalty applied to worst‑of structures
    worst_of_penalty: float
    # Average volatility pressure based on underlying risk profiles
    volatility_pressure_score: float
    # Average gap risk based on underlying risk profiles
    gap_risk_score: float
    # Difficulty of hedging due to number of names and liquidity
    hedge_difficulty_score: float
    # Sensitivity to correlation and basket rule
    correlation_sensitivity_score: float
    # Tenor‑related risk (longer tenors have higher scores)
    tenor_risk_score: float
    # Complexity of documentation and wrapper
    documentation_complexity_score: float
    # Suitability or regulatory warning factor
    suitability_warning_score: float
    # Attractiveness for the desk (inverse of average risk)
    desk_attractiveness_score: float
    # Aggregate risk score across all components
    overall_risk_score: float
    # List of warnings and notes explaining specific risk drivers
    warnings: List[str] = []


class QuoteAlternative(BaseModel):
    """Represents a single counterfactual alternative suggestion."""

    alternative_id: str
    title: str
    changed_terms: Dict[str, Any]
    payoff_object: PayoffObject
    # Detailed metrics for the alternative
    win_probability: float
    desk_economics_score: float
    risk_score: float
    documentation_score: float
    # Deltas versus the original quote (positive means improvement)
    win_probability_delta: float
    desk_economics_delta: float
    risk_reduction: float
    documentation_delta: float
    # Composite final score used to rank alternatives
    final_score: float
    # Narrative explanations
    expected_client_impact: str
    expected_desk_impact: str
    main_tradeoff: str
    approval_required: bool
    human_approval_note: str


class OptimizationResult(BaseModel):
    """Full optimisation result returned by the `/api/quote/optimize` endpoint."""

    original_payoff: PayoffObject
    missing_fields: List[MissingField]
    current_quote_quality: Dict[str, Any]
    alternatives: List[QuoteAlternative]
    recommended_alternative_id: Optional[str]
    explanation: str
    limitations: str
    audit_id: str


class AuditRecord(BaseModel):
    """Audit record stored after each optimisation.

    The timestamp is stored as an ISO 8601 string for easy logging.  The scores
    field aggregates the quote quality metrics (win probability, desk economics,
    risk assessment, etc.).
    """

    audit_id: str
    timestamp: str
    # The raw RFQ and metadata provided by the user
    input_rfq: RFQInput
    # The parsed payoff object resulting from the RFQ parser
    parsed_payoff: PayoffObject
    # Notes from the parser: which fields were extracted, uncertain or assumed
    parser_notes: Dict[str, Any]
    # List of validation warnings or missing fields
    validation_warnings: List[MissingField]
    # Original quote quality metrics (win probability, desk economics, risk assessment)
    original_scores: Dict[str, Any]
    # Alternatives generated during optimisation
    alternatives: List[QuoteAlternative]
    # ID of the recommended alternative
    recommendation: Optional[str]
    # Version of the scoring and ranking formula used
    ranking_version: str
    # Version string for the synthetic data design
    synthetic_data_version: str
    # Human readable limitations and safety disclaimer
    limitations: str
