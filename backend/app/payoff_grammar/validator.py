"""Payoff grammar validation rules.

This validator checks that a parsed :class:`PayoffObject` satisfies the minimal
grammar for known product types such as autocallables.  It returns a list of
:class:`MissingField` objects that identify which required fields are absent.
"""

from __future__ import annotations

from typing import List

from ..models.rfq import PayoffObject, MissingField


def validate_payoff(payoff: PayoffObject) -> List[MissingField]:
    """Validate a payoff object against the grammar for its product type.

    Parameters
    ----------
    payoff: PayoffObject
        The payoff object to validate.

    Returns
    -------
    List[MissingField]
        A list of additional missing fields required by the grammar.  If the
        product type is unknown or unspecified, no extra validation is performed.
    """

    missing: List[MissingField] = []
    if not payoff.product_type:
        return missing

    if payoff.product_type.lower() == "autocallable":
        required = [
            "product_type",
            "currency",
            "tenor_months",
            "coupon_target_min",
            "coupon_target_max",
            "observation_frequency",
            "barrier_level",
            "autocall_trigger",
            "basket_rule",
            "underlyings",
            "wrapper",
        ]
        # either client_segment or region is required
        region_or_segment = getattr(payoff, "client_segment") or getattr(payoff, "region")
        for field_name in required:
            if getattr(payoff, field_name) is None:
                missing.append(
                    MissingField(
                        field_name=field_name,
                        severity="high",
                        reason="Required by autocallable payoff grammar",
                    )
                )
        if not region_or_segment:
            missing.append(
                MissingField(
                    field_name="client_segment/region",
                    severity="high",
                    reason="Either client segment or region must be specified for autocallable products",
                )
            )
        # Additional validations: barrier suitability and concentration
        # Low barrier (<50%) triggers a warning but is allowed
        if payoff.barrier_level is not None and payoff.barrier_level < 50:
            missing.append(
                MissingField(
                    field_name="barrier_level",
                    severity="warning",
                    reason="Barrier level below 50% triggers suitability/documentation warning",
                )
            )
        # If basket is worst-of with more than 3 high volatility names, warn
        if payoff.basket_rule and payoff.basket_rule.lower() == "worst-of" and payoff.underlyings and len(payoff.underlyings) > 3:
            missing.append(
                MissingField(
                    field_name="underlyings",
                    severity="warning",
                    reason="Large worst-of basket may require additional hedging and documentation complexity",
                )
            )
        # Long tenor and high coupon combination
        if payoff.tenor_months and payoff.tenor_months > 24 and payoff.coupon_target_max and payoff.coupon_target_max > 12:
            missing.append(
                MissingField(
                    field_name="tenor_months",
                    severity="warning",
                    reason="Long tenor with high coupon may be infeasible under risk limits",
                )
            )
    # Additional product types could be handled here
    return missing
