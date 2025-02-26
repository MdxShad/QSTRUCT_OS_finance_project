"""Explanation generator for optimisation results.

This module builds human‑readable explanations for why a given alternative is
recommended.  Explanations highlight the trade‑offs between client benefits and
desk benefits and remind the user that all outputs are synthetic and require
human review.
"""

from __future__ import annotations

from typing import List

from ..models.rfq import QuoteAlternative


def generate_explanation(alternatives: List[QuoteAlternative]) -> str:
    """Generate a textual explanation for the optimisation result.

    If there are no alternatives, returns a generic message.  Otherwise, picks
    the top‑scoring alternative and summarises its benefits and trade‑offs.
    """
    if not alternatives:
        return (
            "No viable alternatives were generated. This may be due to missing inputs or an inability to improve the current structure. "
            "Please review the RFQ details and try again."
        )
    best = alternatives[0]
    # Use the expected client and desk impact fields introduced in phase 2
    explanation = (
        f"Alternative '{best.title}' is recommended because it {best.expected_client_impact.lower()} "
        f"while {best.expected_desk_impact.lower()}. The main trade‑off is that {best.main_tradeoff.lower()}. "
        f"This recommendation is based on synthetic scoring (final score {best.final_score:.2f}) and must be reviewed by a human before execution."
    )
    return explanation
