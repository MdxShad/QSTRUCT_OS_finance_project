"""Very simple RFQ parser.

This module contains a deterministic parser that uses regular expressions and
rule‑based string matching to convert free‑form RFQ descriptions into a
structured :class:`PayoffObject` together with a list of :class:`MissingField` items.
The goal is not to be perfect but to extract enough fields for demonstration
purposes.  Whenever the parser cannot find a value, the field is left as
``None`` and a missing field entry is added.
"""

from __future__ import annotations

import re
from typing import List, Tuple

from ..models.rfq import RFQInput, PayoffObject, MissingField


_CURRENCIES = ["USD", "EUR", "INR", "HKD", "KRW"]
_PRODUCT_TYPES = ["autocallable", "snowball", "barrier note"]
_FREQUENCIES = ["monthly", "quarterly", "semiannual", "semi-annual", "annual"]
_BASKET_RULES = ["worst-of", "best-of", "average basket"]
_WRAPPERS = ["note", "swap", "warrant"]


def _extract_percentage(text: str, pattern: str) -> float | None:
    """Helper to extract the first percentage number matched by a regex pattern.

    The pattern should capture the numeric portion in the first group.  Returns a float
    if found, otherwise ``None``.
    """

    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        try:
            return float(match.group(1))
        except (IndexError, ValueError):
            return None
    return None


def parse_rfq(rfq: RFQInput) -> Tuple[PayoffObject, List[MissingField], dict]:
    """Parse a raw RFQ into a :class:`PayoffObject`, list of missing fields and parser notes.

    This deterministic parser now supports a wider set of phrases and patterns:
    - Tenor expressions like "2Y", "two year", "24M", "twenty‑four months".
    - Observation frequency phrases like "monthly obs", "quarterly observation".
    - Barrier and coupon barrier definitions (e.g. "KI 60", "knock‑in barrier at 60", "coupon barrier at 70").
    - Autocall trigger variations ("KO 100", "autocall trigger 100%", etc.).
    - Memory or non‑memory coupon flags.
    - Protection type ("protected note", "capital at risk note").
    - Underlying lists prefaced by "basket on" or "worst of".
    - Notional and settlement type indications.

    The function also collects parser_notes with keys:
    - ``extracted_fields``: list of field names successfully parsed.
    - ``uncertain_fields``: field names with ambiguous values.
    - ``assumptions``: field names for which defaults or assumptions were applied.

    Parameters
    ----------
    rfq: RFQInput
        The input RFQ containing a free form ``raw_text`` field.

    Returns
    -------
    Tuple[PayoffObject, List[MissingField], dict]
        A payoff object populated with fields found in the RFQ, a list of
        missing fields indicating what could not be extracted, and parser notes.
    """

    text = rfq.raw_text or ""
    lower = text.lower()
    payoff = PayoffObject()
    missing: List[MissingField] = []
    notes: dict = {"extracted_fields": [], "uncertain_fields": [], "assumptions": []}

    # Product type
    for pt in _PRODUCT_TYPES:
        if pt in lower:
            payoff.product_type = pt
            notes["extracted_fields"].append("product_type")
            break

    # Currency
    for curr in _CURRENCIES:
        if curr.lower() in lower:
            payoff.currency = curr
            notes["extracted_fields"].append("currency")
            break

    # Tenor: recognise patterns like "2y", "two year", "24m", "24 months"
    tenor_months: int | None = None
    # numeric years (e.g. 2y, 2-year)
    m = re.search(r"(\d+)\s*-?\s*y(?:ear)?", lower)
    if m:
        tenor_months = int(m.group(1)) * 12
    else:
        # numeric months (e.g. 24m)
        m = re.search(r"(\d+)\s*-?\s*m(?:onth)?", lower)
        if m:
            tenor_months = int(m.group(1))
        else:
            # textual numbers (e.g. two year, three years)
            word_to_num = {
                "one": 1,
                "two": 2,
                "three": 3,
                "four": 4,
                "five": 5,
                "six": 6,
                "seven": 7,
                "eight": 8,
                "nine": 9,
                "ten": 10,
            }
            m = re.search(r"(one|two|three|four|five|six|seven|eight|nine|ten)\s+year", lower)
            if m:
                tenor_months = word_to_num[m.group(1)] * 12
    if tenor_months is not None:
        payoff.tenor_months = tenor_months
        notes["extracted_fields"].append("tenor_months")

    # Coupon target/range
    # look for 11-13% or 11% - 13% or "target coupon 11 to 13 percent"
    m = re.search(r"(\d+(?:\.\d+)?)\s*%-\s*(\d+(?:\.\d+)?)\s*%", lower)
    if m:
        payoff.coupon_target_min = float(m.group(1))
        payoff.coupon_target_max = float(m.group(2))
        notes["extracted_fields"].extend(["coupon_target_min", "coupon_target_max"])
    else:
        m = re.search(r"target\s*coupon\s*(\d+(?:\.\d+)?)", lower)
        if m:
            val = float(m.group(1))
            payoff.coupon_target_min = val
            payoff.coupon_target_max = val
            notes["extracted_fields"].extend(["coupon_target_min", "coupon_target_max"])
        else:
            # target coupon 11 to 13 percent
            m = re.search(r"target\s*coupon\s*(\d+(?:\.\d+)?)\s*(?:to|-|–)\s*(\d+(?:\.\d+)?)", lower)
            if m:
                payoff.coupon_target_min = float(m.group(1))
                payoff.coupon_target_max = float(m.group(2))
                notes["extracted_fields"].extend(["coupon_target_min", "coupon_target_max"])

    # Observation frequency: accept words like "monthly obs", "quarterly observation"
    for freq in _FREQUENCIES:
        pattern = freq
        if pattern in lower:
            normalized = freq.replace("semi-annual", "semiannual")
            payoff.observation_frequency = normalized
            notes["extracted_fields"].append("observation_frequency")
            break
    else:
        # match "monthly obs" pattern
        m = re.search(r"(monthly|quarterly|semiannual|semi-annual|annual)\s*(?:obs|observation)", lower)
        if m:
            normalized = m.group(1).replace("semi-annual", "semiannual")
            payoff.observation_frequency = normalized
            notes["extracted_fields"].append("observation_frequency")

    # Barrier type and level (knock‑in / KI)
    m = re.search(r"(?:ki|knock[-\s]?in|knock\s*in\s*barrier(?:\s*at)?|knock-in barrier)\s*(\d+(?:\.\d+)?)%", lower)
    if m:
        payoff.barrier_type = "KI"
        payoff.barrier_level = float(m.group(1))
        notes["extracted_fields"].append("barrier_level")

    # Coupon barrier level (if different from knock in)
    m = re.search(r"coupon\s*barrier\s*(\d+(?:\.\d+)?)%", lower)
    if m:
        payoff.coupon_barrier = float(m.group(1))
        notes["extracted_fields"].append("coupon_barrier")

    # Autocall trigger (KO / autocall)
    m = re.search(r"(?:ko|autocall|autocall\s*trigger)\s*(\d+(?:\.\d+)?)%", lower)
    if m:
        payoff.autocall_trigger = float(m.group(1))
        notes["extracted_fields"].append("autocall_trigger")

    # Memory coupon flag
    if re.search(r"memory\s+coupon", lower):
        payoff.memory_coupon = True
        notes["extracted_fields"].append("memory_coupon")
    elif re.search(r"non\s*-?memory\s+coupon", lower):
        payoff.memory_coupon = False
        notes["extracted_fields"].append("memory_coupon")

    # Protection type / capital at risk
    if "protected note" in lower or "principal protected" in lower:
        payoff.protection_type = "protected"
        payoff.capital_at_risk = False
        notes["extracted_fields"].extend(["protection_type", "capital_at_risk"])
    elif "capital at risk" in lower:
        payoff.protection_type = "capital at risk"
        payoff.capital_at_risk = True
        notes["extracted_fields"].extend(["protection_type", "capital_at_risk"])

    # Notional (e.g. 10m, 5 million)
    m = re.search(r"(\d+(?:\.\d+)?)\s*(m|mm|million)\b", lower)
    if m:
        amt = float(m.group(1))
        payoff.notional = amt * 1.0  # treat as million units without scaling further
        notes["extracted_fields"].append("notional")

    # Settlement type (cash, physical)
    if "cash settled" in lower or "cash settlement" in lower:
        payoff.settlement_type = "cash"
        notes["extracted_fields"].append("settlement_type")
    elif "physical delivery" in lower or "physical settled" in lower:
        payoff.settlement_type = "physical"
        notes["extracted_fields"].append("settlement_type")

    # Basket rule: recognise worst-of, best-of, average basket
    for rule in _BASKET_RULES:
        if rule in lower:
            payoff.basket_rule = rule
            notes["extracted_fields"].append("basket_rule")
            break

    # Underlyings: search for patterns like "worst of NVDA/Samsung/HSI" or "basket on Nvidia, Samsung and HSI"
    underlying_match = re.search(r"(?:worst\s+of\s+|basket\s+on\s+|on\s+)([a-zA-Z0-9/\s,]+)", lower)
    if underlying_match:
        underlying_str = underlying_match.group(1)
        # Replace separators
        cleaned = re.sub(r"/", ",", underlying_str)
        parts: List[str] = []
        for seg in cleaned.split(','):
            subparts = re.split(r"\band\b", seg)
            for sp in subparts:
                name = sp.strip().strip('.')
                if name:
                    # remove trailing qualifiers (like indices, ki etc.)
                    name_clean = re.sub(r"\b(k(?:i|o)|ki|ko|knock[-\s]?in|knock[-\s]?out)\b.*", "", name, flags=re.IGNORECASE).strip()
                    if name_clean:
                        parts.append(name_clean.title())
        if parts:
            payoff.underlyings = parts
            notes["extracted_fields"].append("underlyings")

    # Basket size and worst underlying (assumption)
    if payoff.underlyings:
        payoff.basket_size = len(payoff.underlyings)
        # We cannot know the true worst underlying without price data; assume last name as placeholder
        payoff.worst_underlying = payoff.underlyings[-1]
        notes["assumptions"].extend(["basket_size", "worst_underlying"])

    # Wrapper
    for w in _WRAPPERS:
        if re.search(rf"\b{w}\b", lower):
            payoff.wrapper = w
            notes["extracted_fields"].append("wrapper")
            break

    # Callable after X months or years
    m = re.search(r"callable\s+after\s+(\d+)\s*([ym])", lower)
    if m:
        number = int(m.group(1))
        unit = m.group(2)
        months = number * 12 if unit == 'y' else number
        payoff.callable_after_months = months
        notes["extracted_fields"].append("callable_after_months")

    # Client segment and region
    payoff.client_segment = rfq.client_segment
    payoff.region = rfq.region
    if payoff.client_segment is None:
        m = re.search(r"(apac distributor|korean distributor|private bank|institutional client)", lower)
        if m:
            payoff.client_segment = m.group(1)
            notes["extracted_fields"].append("client_segment")
    if payoff.region is None:
        m = re.search(r"\b(apac|emea|americas)\b", lower)
        if m:
            payoff.region = m.group(1).upper()
            notes["extracted_fields"].append("region")

    # Jurisdiction or wrapper region (e.g. Korean, HK, EU)
    m = re.search(r"\b(korean|hk|kr|eu|us|sg)\b", lower)
    if m:
        payoff.jurisdiction_or_wrapper_region = m.group(1).upper()
        notes["extracted_fields"].append("jurisdiction_or_wrapper_region")

    # Market regime (bull, bear, volatile)
    m = re.search(r"\b(bull|bear|volatile)\b", lower)
    if m:
        payoff.market_regime = m.group(1)
        notes["extracted_fields"].append("market_regime")

    # Documentation complexity level: derive a simple proxy from wrapper and number of features
    complexity = 0
    if payoff.wrapper == "swap":
        complexity += 3
    elif payoff.wrapper == "warrant":
        complexity += 2
    else:
        complexity += 1
    # add complexity for memory coupon, issuer call, protection type other than 'note'
    if payoff.memory_coupon:
        complexity += 1
    if payoff.issuer_call:
        complexity += 1
    if payoff.protection_type and payoff.protection_type != "capital at risk":
        complexity += 1
    if payoff.basket_size and payoff.basket_size > 3:
        complexity += 1
    payoff.documentation_complexity_level = complexity or None

    # Confidence score: ratio of extracted fields to total expected core fields
    total_fields = [
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
        "callable_after_months",
        "client_segment",
        "region",
    ]
    filled = sum(1 for f in total_fields if getattr(payoff, f) is not None)
    payoff.confidence_score = filled / len(total_fields)

    # Determine missing fields with severity tags
    required_fields = {
        "product_type": "core",
        "currency": "core",
        "tenor_months": "core",
        "coupon_target_min": "core",
        "coupon_target_max": "core",
        "observation_frequency": "core",
        "barrier_level": "core",
        "autocall_trigger": "core",
        "basket_rule": "core",
        "underlyings": "core",
        "wrapper": "core",
        "client_segment": "supplemental",
        "region": "supplemental",
        "notional": "supplemental",
    }
    for field_name, severity_tag in required_fields.items():
        if getattr(payoff, field_name) is None:
            missing.append(
                MissingField(
                    field_name=field_name,
                    severity="high" if severity_tag == "core" else "medium",
                    reason="Not found in RFQ text",
                )
            )

    return payoff, missing, notes
