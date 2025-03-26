# Scoring Logic

Q‑Struct OS uses simplified scoring models to evaluate a proposed structured product and its counterfactual alternatives.  These models are **synthetic** and do not reflect real pricing or risk calculations.  They are meant to illustrate how a desk might trade off between client appeal, risk and economics.

## Risk assessment

The risk engine assigns values between 0 and 1 (higher means worse) across several dimensions:

- **Coupon feasibility** – High target coupons are harder to achieve; the score scales with the coupon relative to 20%.
- **Barrier risk** – A lower knock‑in level means more downside risk; the score is `1 – barrier/100`.
- **Downside convexity** – A fixed constant representing residual tail risk (0.5 in the prototype).
- **Hedge difficulty** – More underlyings increase hedging complexity; the score is `min(N / 5, 1)`.
- **Correlation sensitivity** – Worst‑of baskets receive 0.8, best‑of 0.3, average basket 0.5.
- **Documentation complexity** – Notes are easiest (0.3), swaps hardest (0.6), warrants moderate (0.5).
- **Desk attractiveness** – Computed as `1 – average(risk components)`.

The **overall risk score** is simply the average of all risk components except desk attractiveness.  The backend also emits warnings when certain thresholds are crossed, such as very low barriers, large baskets or extremely high coupons.

## Win probability

The win probability estimates the likelihood that a client will accept the quote.  Starting from a baseline of 60%, it is adjusted by:

- Coupon level – Moderate coupons around 10% are most appealing; very high or low coupons reduce the chance.
- Barrier level – Higher barriers improve perceived safety.
- Observation frequency – Monthly observations add 10 percentage points, quarterly adds 5 points, semiannual adds 2 points.
- Basket rule – Worst‑of baskets reduce probability (–10 points), best‑of increase it (+5 points).

All adjustments are capped so that the final probability remains between 0 and 1.

## Desk economics

Desk economics is a proxy for margin and operational effort.  Starting from 0.5, the score increases with:

- Lower coupons – Up to 0.3 added when coupons are at or below 12%.
- Higher barriers – Up to ±0.25 based on the barrier relative to 50%.
- Fewer underlyings – Up to 0.25 when there is only one underlying.
- Wrapper complexity – Notes add 0.05, swaps subtract 0.05.

The final value is clamped between 0 and 1.

## Final score for alternatives

Each counterfactual alternative is assigned a **final score** to enable ranking.  The score is a weighted sum of:

```
final_score =
  0.35 × win_probability
  + 0.30 × desk_economics_score
  + 0.20 × risk_improvement
  + 0.10 × documentation_score
  + 0.05 × explanation_quality
```

Where:

- `risk_improvement` = `max(0, original_risk – new_risk)` to reward genuine risk reduction.
- `documentation_score` = `1 – documentation_complexity_score`.
- `explanation_quality` is a constant 0.5 in the prototype.

The alternative with the highest final score is presented as the recommendation.  However, the system emphasises that **human approval is always required**.
