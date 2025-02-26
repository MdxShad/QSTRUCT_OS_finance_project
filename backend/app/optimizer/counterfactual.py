"""Counterfactual alternative generator.

This module suggests small modifications to an existing payoff object in order
to improve win probability and desk economics while respecting basic risk
constraints.  Each alternative is synthetic and does not constitute advice.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List

from ..models.rfq import PayoffObject, QuoteAlternative
from ..risk_engine.risk import assess_risk
from ..hit_probability.hit_model import estimate_win_probability_detail, estimate_win_probability, estimate_desk_economics


def _generate_id() -> str:
    return uuid.uuid4().hex[:8]


def generate_alternatives(payoff: PayoffObject) -> List[QuoteAlternative]:
    """Generate a set of counterfactual alternatives for a payoff.

    This upgraded version produces up to five alternatives that explore
    different structural tweaks.  Each alternative computes deltas versus the
    original quote, includes narrative explanations and indicates whether
    additional human approval is required.  Final scores are calculated using
    the weighting from the product thesis (0.30 * win_probability + 0.25 *
    desk_economics + 0.20 * risk_reduction + 0.10 * documentation_quality
    + 0.10 * client_fit + 0.05 * explanation_quality).
    """
    alternatives: List[QuoteAlternative] = []
    # Original metrics
    original_risk = assess_risk(payoff)
    original_win_detail = estimate_win_probability_detail(payoff)
    original_win_prob = original_win_detail["win_probability"]
    original_desk = estimate_desk_economics(payoff)
    original_doc_quality = 1.0 - original_risk.documentation_complexity_score
    # A proxy for client fit: use 1 - suitability warning score
    original_client_fit = 1.0 - original_risk.suitability_warning_score

    def build_alternative(title: str, changed_terms: Dict[str, Any], new_payoff: PayoffObject,
                          client_impact: str, desk_impact: str, tradeoff: str, approval_note: str) -> None:
        """Helper to build and append a QuoteAlternative object with computed metrics."""
        risk_new = assess_risk(new_payoff)
        win_detail_new = estimate_win_probability_detail(new_payoff)
        win_new = win_detail_new["win_probability"]
        desk_new = estimate_desk_economics(new_payoff)
        doc_quality_new = 1.0 - risk_new.documentation_complexity_score
        client_fit_new = 1.0 - risk_new.suitability_warning_score
        risk_reduction = max(0.0, original_risk.overall_risk_score - risk_new.overall_risk_score)
        win_delta = win_new - original_win_prob
        desk_delta = desk_new - original_desk
        doc_delta = doc_quality_new - original_doc_quality
        # Weighted final score per thesis
        final_score = (
            0.30 * win_new
            + 0.25 * desk_new
            + 0.20 * risk_reduction
            + 0.10 * doc_quality_new
            + 0.10 * client_fit_new
            + 0.05 * 0.5  # explanation quality constant
        )
        # Determine if human approval required: if suitability warning very high or documentation very complex
        approval_required = risk_new.suitability_warning_score > 0.5 or risk_new.documentation_complexity_score > 0.7
        alt = QuoteAlternative(
            alternative_id=_generate_id(),
            title=title,
            changed_terms=changed_terms,
            payoff_object=new_payoff,
            win_probability=win_new,
            desk_economics_score=desk_new,
            risk_score=risk_new.overall_risk_score,
            documentation_score=doc_quality_new,
            win_probability_delta=win_delta,
            desk_economics_delta=desk_delta,
            risk_reduction=risk_reduction,
            documentation_delta=doc_delta,
            final_score=final_score,
            expected_client_impact=client_impact,
            expected_desk_impact=desk_impact,
            main_tradeoff=tradeoff,
            approval_required=approval_required,
            human_approval_note=approval_note,
        )
        alternatives.append(alt)

    # A. Barrier‑relief alternative: increase barrier by 5–10% up to 95%
    if payoff.barrier_level is not None:
        new_barrier = min(payoff.barrier_level + 10.0, 95.0)
        new_payoff = payoff.copy(deep=True)
        new_payoff.barrier_level = new_barrier
        # Adjust coupon down slightly to reflect safer structure
        if new_payoff.coupon_target_min is not None:
            new_payoff.coupon_target_min = max(0.0, new_payoff.coupon_target_min - 0.5)
        if new_payoff.coupon_target_max is not None:
            new_payoff.coupon_target_max = max(new_payoff.coupon_target_min or 0.0, new_payoff.coupon_target_max - 0.5)
        build_alternative(
            title="Barrier relief",
            changed_terms={"barrier_level": {"from": payoff.barrier_level, "to": new_barrier}},
            new_payoff=new_payoff,
            client_impact="Improves downside protection by raising the knock‑in level, increasing client comfort.",
            desk_impact="Reduces gap risk and hedge difficulty, improving desk margin.",
            tradeoff="Slightly reduces coupon, potentially lowering client headline return.",
            approval_note="Higher barrier changes pricing; ensure coupon remains acceptable to client."
        )

    # B. Underlying substitution alternative: replace last underlying with SPX or HSI
    if payoff.underlyings:
        new_underlyings = payoff.underlyings.copy()
        replacement = "SPX" if "SPX" not in [u.upper() for u in new_underlyings] else "HSI"
        old = new_underlyings[-1]
        new_underlyings[-1] = replacement
        new_payoff = payoff.copy(deep=True)
        new_payoff.underlyings = new_underlyings
        build_alternative(
            title="Underlying substitution",
            changed_terms={"underlyings": {"from": payoff.underlyings, "to": new_underlyings}},
            new_payoff=new_payoff,
            client_impact=f"Replaces {old} with {replacement}, introducing a more familiar or liquid index to clients.",
            desk_impact="Simplifies hedging by using a highly liquid benchmark.",
            tradeoff="Alters correlation profile; may impact payoff pricing.",
            approval_note="Confirm that the replacement underlying aligns with client investment universe."
        )

    # C. Coupon‑risk rebalance alternative: lower coupon by 1–2 points
    if payoff.coupon_target_min is not None and payoff.coupon_target_max is not None:
        new_min = max(0.0, payoff.coupon_target_min - 1.0)
        new_max = max(new_min, payoff.coupon_target_max - 1.0)
        new_payoff = payoff.copy(deep=True)
        new_payoff.coupon_target_min = new_min
        new_payoff.coupon_target_max = new_max
        build_alternative(
            title="Coupon/risk rebalance",
            changed_terms={
                "coupon_target_min": {"from": payoff.coupon_target_min, "to": new_min},
                "coupon_target_max": {"from": payoff.coupon_target_max, "to": new_max},
            },
            new_payoff=new_payoff,
            client_impact="Lower coupons are easier to achieve, potentially increasing win probability.",
            desk_impact="Reduces financing cost and hedge complexity, improving desk economics.",
            tradeoff="Client receives a lower headline coupon.",
            approval_note="Ensure the new coupon range still meets client expectations."
        )

    # D. Observation/autocall schedule alternative: set observation to monthly and raise KO by 5%
    new_payoff = payoff.copy(deep=True)
    changed: Dict[str, Any] = {}
    if new_payoff.observation_frequency and "monthly" not in new_payoff.observation_frequency.lower():
        changed["observation_frequency"] = {"from": new_payoff.observation_frequency, "to": "monthly"}
        new_payoff.observation_frequency = "monthly"
    if new_payoff.autocall_trigger is not None:
        new_trigger = min(new_payoff.autocall_trigger + 5.0, 120.0)
        changed["autocall_trigger"] = {"from": new_payoff.autocall_trigger, "to": new_trigger}
        new_payoff.autocall_trigger = new_trigger
    if changed:
        build_alternative(
            title="Schedule/trigger adjustment",
            changed_terms=changed,
            new_payoff=new_payoff,
            client_impact="More frequent observations and a higher call trigger offer additional redemption opportunities and shorter investment horizon.",
            desk_impact="Earlier potential call dates shorten exposure duration, lowering risk.",
            tradeoff="Increased operational workload from frequent observations.",
            approval_note="Verify operational feasibility of increased observation frequency."
        )

    # E. Documentation simplification alternative: simplify wrapper and remove exotic features
    new_payoff = payoff.copy(deep=True)
    changed_doc: Dict[str, Any] = {}
    # Set wrapper to 'note' to reduce complexity
    if new_payoff.wrapper and new_payoff.wrapper.lower() != "note":
        changed_doc["wrapper"] = {"from": new_payoff.wrapper, "to": "note"}
        new_payoff.wrapper = "note"
    # Remove memory coupon
    if new_payoff.memory_coupon:
        changed_doc["memory_coupon"] = {"from": new_payoff.memory_coupon, "to": False}
        new_payoff.memory_coupon = False
    # Remove issuer call
    if new_payoff.issuer_call:
        changed_doc["issuer_call"] = {"from": new_payoff.issuer_call, "to": False}
        new_payoff.issuer_call = False
    if changed_doc:
        build_alternative(
            title="Documentation simplification",
            changed_terms=changed_doc,
            new_payoff=new_payoff,
            client_impact="Simplifies the product structure, making documentation faster and easier to understand for clients.",
            desk_impact="Reduces legal and operational complexity, speeding up execution.",
            tradeoff="May remove features that some clients value, such as memory coupon or issuer call options.",
            approval_note="Check that simplified wrapper still meets client needs."
        )

    # Sort alternatives by final score descending
    alternatives.sort(key=lambda alt: alt.final_score, reverse=True)
    return alternatives
