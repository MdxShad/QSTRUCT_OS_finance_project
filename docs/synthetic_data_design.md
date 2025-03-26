# Synthetic Data Design

To respect client confidentiality and regulatory constraints, Q‑Struct OS operates solely on synthetic data.  This means that all inputs, underlyings, risk profiles and client preferences are fabricated for demonstration purposes.  The synthetic datasets are small but structured to exercise the parsing, scoring and optimisation logic.

## Demo RFQs

The file `backend/app/demo_data/demo_rfqs.json` contains example RFQs, each with an `id`, `raw_text`, `client_segment` and `region`.  These samples mirror common patterns seen in APAC distributor flows but omit any real identifiers.

## Underlying risk profiles

`underlying_risk_profiles.json` maps underlying names to simple volatility and gap risk measures.  These values feed into the risk engine heuristics.  For example, `Nvidia` has a volatility of 0.35 and gap risk of 0.25, while `SPX` has lower values reflecting the broad index’s stability.

## Client preferences

`client_preferences.json` describes preferred product types, coupon ranges, tenor ranges and underlyings for several fictitious client segments such as "APAC distributor", "Korean distributor", "private bank" and "institutional client".  These preferences are currently not consumed by the optimisation algorithm but serve as a foundation for future enhancements.

## Audit log

Optimisation requests are written to `audit_log.json` under `backend/app/demo_data/`.  Each entry contains the timestamp, parsed payoff, scores and recommended alternative ID.  This file grows over time and can be inspected via the `/api/audit` endpoint.

## Limitations

Because the data is synthetic, the system does not connect to market data, vol surfaces, correlation matrices or live RFQs.  The underlyings, risk measures and client segments are fictional and should not be used for any real financial decisions.
