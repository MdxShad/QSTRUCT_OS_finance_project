# Payoff Grammar

Structured products are often described in free‑form language.  To process an RFQ programmatically, Q‑Struct OS parses the text into a **payoff object** with well‑defined fields.  The grammar used here is intentionally simplified and covers only autocallables, snowball notes and barrier notes with worst‑of baskets.

## Required fields for autocallables

For an autocallable payoff to be valid, the following fields must be present:

| Field                | Meaning                                                       |
|----------------------|---------------------------------------------------------------|
| `product_type`       | The product category, e.g. `autocallable`, `snowball`         |
| `currency`           | Settlement currency such as `USD`, `EUR`, `HKD`              |
| `tenor_months`       | Maturity expressed in months (e.g. `24` for a 2‑year note)    |
| `coupon_target_min`  | Lower bound of the target coupon range (percentage)           |
| `coupon_target_max`  | Upper bound of the target coupon range (percentage)           |
| `observation_frequency` | How often the autocall feature is observed (`monthly`, `quarterly`, `semiannual`, `annual`) |
| `barrier_level`      | Knock‑in level expressed as a percentage of spot (e.g. `60`)  |
| `autocall_trigger`   | Knock‑out (call) level expressed as a percentage (e.g. `100`) |
| `basket_rule`        | Aggregation rule for multiple underlyings (`worst‑of`, `best‑of`, `average basket`) |
| `underlyings`        | List of underlying asset names                                |
| `wrapper`            | Legal wrapper such as `note`, `swap`, `warrant`               |
| `client_segment` or `region` | One of these must be provided to understand distribution channel |

If any of these fields are missing, the RFQ is flagged for human review.  Additional optional fields include `callable_after_months` (the time after which the note may be called) and `confidence_score` (an internal measure of parsing confidence).

## Grammar validation

The backend performs a secondary validation after parsing.  For autocallables, it verifies that all required fields are present and that at least one of `client_segment` or `region` is provided.  Missing fields are returned to the caller with a severity level.

This grammar is intentionally narrow.  It does not capture complex payoffs such as step‑down coupons, digital barriers, dual currency structures or call spread notes.  Extending the grammar would require domain expertise and careful design.
