"""Synthetic risk scoring module with enhanced components.

This module computes a rich risk assessment for a parsed payoff object.  All
scores are synthetic proxies intended for demonstration only.  Higher values
indicate increased risk or complexity.  The calculation leverages basic
underlying risk profiles (volatility and gap risk) defined in the demo data.

The risk assessment includes:

* **barrier_distance_score** – how far the knock‑in barrier sits below full
  protection.  Low barriers increase downside risk.
* **basket_concentration_score** – measures concentration of volatile names in
  the basket.  Baskets with few high‑volatility names score higher.
* **worst_of_penalty** – additional penalty for worst‑of payoff structures.
* **volatility_pressure_score** – the average volatility across underlyings.
* **gap_risk_score** – the average gap risk across underlyings.
* **hedge_difficulty_score** – increased by the number of names and by
  volatility/gap risk; more names and riskier names make hedging harder.
* **correlation_sensitivity_score** – depends on the basket rule: worst‑of
  exhibits the highest correlation sensitivity.
* **tenor_risk_score** – longer tenors increase risk.  12 months → low risk,
  60 months → high risk.
* **documentation_complexity_score** – complexity arising from wrapper type and
  extra features like memory coupon or issuer call.
* **suitability_warning_score** – composite warning factor for low barriers,
  high volatility baskets and long tenors with high coupons.  Values near 1
  indicate strong suitability concerns.
* **desk_attractiveness_score** – complement of the average of other risk
  components; higher values indicate more appealing trades for the desk.
* **overall_risk_score** – average of all risk components except
  desk_attractiveness_score, summarising total perceived risk.
* **warnings** – narrative warnings describing specific risk drivers.

Real structured product risk assessment requires sophisticated models,
correlation matrices, market data and legal review.  Here we provide a
transparent formula‑based approximation for demonstration purposes.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from ..models.rfq import PayoffObject, RiskAssessment


# Load underlying risk profiles once at import time.  These profiles are
# synthetic proxies for volatility and gap risk of common names.  They live
# alongside demo data so that new names can be added by editing the JSON.
_RISK_PROFILE_PATH = Path(__file__).resolve().parent / "../demo_data/underlying_risk_profiles.json"
try:
    _PROFILES: Dict[str, Dict[str, float]] = json.loads(_RISK_PROFILE_PATH.read_text())
except Exception:
    _PROFILES = {}


def _get_profile(name: str) -> Dict[str, float]:
    """Return the risk profile for a given underlying name.

    If the name is unknown, a neutral profile with moderate volatility and gap
    risk is returned.  Names are matched in a case‑insensitive manner.
    """
    key = name.title()
    return _PROFILES.get(key, {"volatility": 0.25, "gap_risk": 0.20})


def assess_risk(payoff: PayoffObject) -> RiskAssessment:
    """Compute a synthetic risk assessment for a payoff object.

    Parameters
    ----------
    payoff : PayoffObject
        Parsed payoff containing information such as barrier, underlyings and
        product features.

    Returns
    -------
    RiskAssessment
        Structured object with component scores and warnings.
    """
    # Barrier distance: measure from 100% to barrier level.  Missing barrier
    # implies no downside risk (score 0.0) since the payoff may be principal
    # protected.  Score saturates at 1.0 when barrier is 0%.
    barrier_level = payoff.barrier_level if payoff.barrier_level is not None else 100.0
    barrier_distance_score = max(0.0, min(1.0, 1.0 - (barrier_level / 100.0)))

    # Underlying volatility and gap risk
    names = payoff.underlyings or []
    if not names:
        # treat as single neutral name if no underlyings specified
        names = ["Unknown"]
    volatilities: List[float] = []
    gap_risks: List[float] = []
    for name in names:
        prof = _get_profile(name)
        volatilities.append(prof.get("volatility", 0.25))
        gap_risks.append(prof.get("gap_risk", 0.20))
    avg_vol = sum(volatilities) / len(volatilities)
    avg_gap = sum(gap_risks) / len(gap_risks)

    # Basket concentration: if one name dominates volatility, the score is high.
    # We approximate by taking the max volatility divided by the sum of vols.
    if len(volatilities) > 1:
        basket_concentration_score = max(volatilities) / (sum(volatilities) + 1e-6)
    else:
        basket_concentration_score = 0.0
    # Introduce extra penalty for high concentration in worst‑of structures
    if (payoff.basket_rule or "").lower() == "worst-of":
        basket_concentration_score = min(1.0, basket_concentration_score * 1.5)

    # Worst‑of penalty: fixed penalty if basket rule is worst‑of
    worst_of_penalty = 0.2 if (payoff.basket_rule or "").lower() == "worst-of" else 0.0

    # Volatility pressure is simply the average volatility (scaled by 0.5)
    volatility_pressure_score = min(1.0, avg_vol / 0.5)

    # Gap risk score is the average gap risk (scaled by 0.5)
    gap_risk_score = min(1.0, avg_gap / 0.5)

    # Hedge difficulty: more names and higher vol/gap increase difficulty
    num_names = len(names)
    hedge_difficulty_score = min(1.0, (num_names / 5.0) + (avg_vol + avg_gap) / 2.0)

    # Correlation sensitivity: depends on basket rule
    rule = (payoff.basket_rule or "").lower()
    if rule == "worst-of":
        correlation_sensitivity_score = 0.8
    elif rule == "best-of":
        correlation_sensitivity_score = 0.3
    elif rule == "average basket":
        correlation_sensitivity_score = 0.5
    else:
        correlation_sensitivity_score = 0.4

    # Tenor risk: scale tenor to 0–1 over 12–60 months.  Unknown tenor implies moderate risk 0.25.
    if payoff.tenor_months is None:
        tenor_risk_score = 0.25
    else:
        months = payoff.tenor_months
        # clamp between 12 and 60 months for scaling
        adj = max(0, min(months, 60) - 12)
        tenor_risk_score = min(1.0, adj / 48.0)

    # Documentation complexity: base complexity from wrapper type
    wrapper = (payoff.wrapper or "note").lower()
    if wrapper == "note":
        doc_complexity = 0.3
    elif wrapper == "swap":
        doc_complexity = 0.6
    elif wrapper == "warrant":
        doc_complexity = 0.5
    else:
        doc_complexity = 0.4
    # Add 0.1 for memory coupon, issuer call or exotic protection types
    if payoff.memory_coupon:
        doc_complexity += 0.1
    if payoff.issuer_call:
        doc_complexity += 0.1
    if payoff.protection_type and payoff.protection_type != "capital at risk":
        doc_complexity += 0.1
    # Cap complexity
    documentation_complexity_score = min(1.0, doc_complexity)

    # Suitability warning: composite of barrier, volatility concentration and long tenor/high coupon
    suitability_warning = 0.0
    # Low barrier (<50%) triggers strong warning
    if payoff.barrier_level is not None and payoff.barrier_level < 50:
        suitability_warning += 0.4
    # High concentration with high vol (>0.3) triggers warning
    if basket_concentration_score > 0.4 and avg_vol > 0.3:
        suitability_warning += 0.3
    # Long tenor (>24 months) combined with high coupon (>12%) triggers warning
    max_coupon = payoff.coupon_target_max or payoff.coupon_target_min or 0.0
    if payoff.tenor_months is not None and payoff.tenor_months > 24 and max_coupon > 12:
        suitability_warning += 0.3
    suitability_warning_score = min(1.0, suitability_warning)

    # Aggregate risk score (excluding desk attractiveness)
    components = [
        barrier_distance_score,
        basket_concentration_score,
        worst_of_penalty,
        volatility_pressure_score,
        gap_risk_score,
        hedge_difficulty_score,
        correlation_sensitivity_score,
        tenor_risk_score,
        documentation_complexity_score,
        suitability_warning_score,
    ]
    overall_risk_score = sum(components) / len(components)

    # Desk attractiveness is complement of average risk (excluding itself)
    desk_attractiveness_score = max(0.0, 1.0 - overall_risk_score)

    # Narrative warnings
    warnings: List[str] = []
    if payoff.barrier_level is not None and payoff.barrier_level < 50:
        warnings.append("Barrier below 50% may breach suitability thresholds.")
    if len(names) > 3:
        warnings.append("Basket contains many names, increasing hedge difficulty.")
    if avg_vol > 0.3:
        warnings.append("High underlying volatility increases coupon feasibility pressure.")
    if avg_gap > 0.25:
        warnings.append("Significant gap risk could lead to large slippage.")
    if suitability_warning_score > 0.5:
        warnings.append("Multiple factors trigger suitability warnings; documentation may be complex.")

    return RiskAssessment(
        barrier_distance_score=barrier_distance_score,
        basket_concentration_score=basket_concentration_score,
        worst_of_penalty=worst_of_penalty,
        volatility_pressure_score=volatility_pressure_score,
        gap_risk_score=gap_risk_score,
        hedge_difficulty_score=hedge_difficulty_score,
        correlation_sensitivity_score=correlation_sensitivity_score,
        tenor_risk_score=tenor_risk_score,
        documentation_complexity_score=documentation_complexity_score,
        suitability_warning_score=suitability_warning_score,
        desk_attractiveness_score=desk_attractiveness_score,
        overall_risk_score=overall_risk_score,
        warnings=warnings,
    )