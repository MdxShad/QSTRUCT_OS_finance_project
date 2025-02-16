"""Synthetic models for win probability and desk economics.

These functions provide highly simplified estimates of the probability that a
client will accept the quote and the attractiveness for the desk.  They use
heuristics based on coupon, barrier and observation frequency.  Real models
would require statistical analysis and back‑testing on historical RFQs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from ..models.rfq import PayoffObject

# Load client preference profiles from the demo data.  The file maps client segments
# to their preferred product types, coupon ranges, tenor ranges and underlyings.
_PREFERENCES_PATH = Path(__file__).resolve().parent / "../demo_data/client_preferences.json"
try:
    _CLIENT_PREFS: Dict[str, Dict[str, List]] = json.loads(_PREFERENCES_PATH.read_text())
except Exception:
    _CLIENT_PREFS = {}

def estimate_win_probability_detail(payoff: PayoffObject) -> Dict[str, any]:
    """Estimate a synthetic win probability with drivers and reason codes.

    The returned dict includes:
    - ``win_probability``: the estimated probability between 0 and 1.
    - ``drivers_positive``: list of narrative factors improving the chance of a win.
    - ``drivers_negative``: list of narrative factors reducing the chance of a win.
    - ``confidence_level``: heuristic confidence in the estimate (0–1).
    - ``reason_codes``: machine‑friendly codes representing the main drivers.

    The model is purely illustrative and leverages client preferences from the
    demo data.  In practice, win probability modelling would require statistical
    analysis of historical RFQs and client behaviour.
    """
    # Default baseline
    prob = 0.5
    drivers_pos: List[str] = []
    drivers_neg: List[str] = []
    reason_codes: List[str] = []

    # Resolve client preferences if available
    prefs = None
    if payoff.client_segment:
        prefs = _CLIENT_PREFS.get(payoff.client_segment, None)

    # Coupon attractiveness
    max_coupon = payoff.coupon_target_max or payoff.coupon_target_min or 0.0
    if prefs and "preferred_coupon_range" in prefs:
        low, high = prefs["preferred_coupon_range"]
        if low <= max_coupon <= high:
            prob += 0.1
            drivers_pos.append("Coupon is within client target range")
            reason_codes.append("COUPON_IN_TARGET_RANGE")
        elif max_coupon < low:
            drivers_neg.append("Coupon appears too low versus client expectation")
            prob -= 0.05
            reason_codes.append("LOW_COUPON")
        else:
            drivers_neg.append("Coupon exceeds typical target range; client may see it as risky")
            prob -= 0.05
            reason_codes.append("HIGH_COUPON")
    else:
        # general triangular attractiveness peaking at 10%
        if max_coupon:
            if max_coupon <= 10:
                prob += max_coupon / 50.0
            else:
                prob += max(0.0, (20 - max_coupon) / 50.0)

    # Product type preference
    if prefs and "preferred_products" in prefs:
        if payoff.product_type and payoff.product_type.lower() in [p.lower() for p in prefs["preferred_products"]]:
            prob += 0.05
            drivers_pos.append("Preferred product type for this client segment")
            reason_codes.append("PREFERRED_PRODUCT_TYPE")
        else:
            prob -= 0.05
            drivers_neg.append("Product type not typical for this client segment")
            reason_codes.append("NON_PREFERRED_PRODUCT_TYPE")

    # Underlying familiarity
    if prefs and "preferred_underlyings" in prefs and payoff.underlyings:
        overlap = set(u.title() for u in payoff.underlyings).intersection(set(prefs["preferred_underlyings"]))
        if overlap:
            prob += 0.05
            drivers_pos.append("Contains familiar underlyings: " + ", ".join(sorted(overlap)))
            reason_codes.append("FAMILIAR_UNDERLYINGS")
        else:
            prob -= 0.03
            drivers_neg.append("Underlyings unfamiliar to client segment")
            reason_codes.append("UNFAMILIAR_UNDERLYINGS")

    # Tenor fit
    if prefs and "preferred_tenor_months" in prefs and payoff.tenor_months is not None:
        low, high = prefs["preferred_tenor_months"]
        if low <= payoff.tenor_months <= high:
            prob += 0.05
            drivers_pos.append("Tenor matches client preference")
            reason_codes.append("TENOR_MATCH")
        else:
            prob -= 0.05
            drivers_neg.append("Tenor outside client preferred range")
            reason_codes.append("TENOR_MISMATCH")

    # Complexity penalty based on documentation complexity
    # A simple heuristic: high doc complexity (>0.5) reduces win probability
    from ..risk_engine.risk import assess_risk  # local import to avoid cycles
    risk = assess_risk(payoff)
    if risk.documentation_complexity_score > 0.6:
        prob -= 0.05
        drivers_neg.append("High documentation complexity may deter clients")
        reason_codes.append("HIGH_COMPLEXITY_PENALTY")

    # Barrier comfort: high barrier (closer to 100%) increases client comfort
    if payoff.barrier_level is not None:
        if payoff.barrier_level >= 70:
            prob += 0.05
            drivers_pos.append("High knock‑in barrier improves downside protection")
            reason_codes.append("BARRIER_ABOVE_COMFORT")
        elif payoff.barrier_level < 50:
            prob -= 0.05
            drivers_neg.append("Low barrier may make clients uncomfortable")
            reason_codes.append("BARRIER_BELOW_COMFORT")

    # Observation frequency: monthly > quarterly > semiannual > annual
    freq = (payoff.observation_frequency or "").lower()
    if "monthly" in freq:
        prob += 0.05
        drivers_pos.append("Frequent observation schedule offers more early redemption opportunities")
        reason_codes.append("HIGH_FREQUENCY_OBS")
    elif "quarterly" in freq:
        prob += 0.02
    elif "semiannual" in freq:
        prob += 0.01

    # Ensure probability within [0,1]
    prob = max(0.0, min(1.0, prob))

    # Confidence level: fewer missing core fields → higher confidence
    core_fields = [
        payoff.product_type,
        payoff.currency,
        payoff.tenor_months,
        payoff.coupon_target_min,
        payoff.coupon_target_max,
        payoff.observation_frequency,
        payoff.barrier_level,
        payoff.autocall_trigger,
        payoff.basket_rule,
        payoff.underlyings,
        payoff.wrapper,
    ]
    missing_count = sum(1 for f in core_fields if f is None)
    confidence_level = max(0.3, 1.0 - missing_count * 0.05)

    return {
        "win_probability": prob,
        "drivers_positive": drivers_pos,
        "drivers_negative": drivers_neg,
        "confidence_level": confidence_level,
        "reason_codes": reason_codes,
    }



def estimate_win_probability(payoff: PayoffObject) -> float:
    """Return only the win probability (scalar) for compatibility.

    This function delegates to :func:`estimate_win_probability_detail` and
    extracts the ``win_probability`` field.  Existing code that depended on
    a simple float can continue to call this function without modification.
    """
    return estimate_win_probability_detail(payoff)["win_probability"]


def estimate_desk_economics(payoff: PayoffObject) -> float:
    """Estimate a synthetic desk economics score for the payoff.

    The score is between 0 and 1, where higher values indicate that the product
    is more attractive for the desk (easier to hedge, better margin proxy).
    """
    score = 0.5
    max_coupon = payoff.coupon_target_max or payoff.coupon_target_min or 0.0
    barrier = payoff.barrier_level or 100.0
    num_underlyings = len(payoff.underlyings or []) or 1
    wrapper = (payoff.wrapper or "note").lower()

    # Lower coupons are generally more profitable for the desk
    score += max(0.0, (12 - max_coupon) / 40)  # up to +0.3 when coupon <=12

    # Higher barriers reduce gap risk and increase margin
    score += (barrier - 50) / 200  # +/-0.25

    # Fewer underlyings simplify hedging
    score += max(0.0, (5 - num_underlyings) / 20)  # up to +0.25 if single underlying

    # Wrapper complexity: note easiest, swap hardest
    if wrapper == "note":
        score += 0.05
    elif wrapper == "swap":
        score -= 0.05

    return max(0.0, min(1.0, score))
