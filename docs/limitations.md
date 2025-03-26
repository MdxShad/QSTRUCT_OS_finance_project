# Limitations

This prototype is designed for exploration and demonstration only.  It has many limitations that users must be aware of:

1. **Synthetic data** – All RFQs, underlyings, risk profiles and client preferences are fictional.  There is no connection to real market data, client orders or positions.
2. **Simplistic scoring** – Risk, win probability and desk economics are computed using heuristic formulas with arbitrary scaling factors.  They do not reflect real pricing or risk management models.
3. **Narrow grammar** – The RFQ parser understands only a small subset of structured product features (autocallables, snowballs, barrier notes with worst‑of baskets).  It cannot parse complex structures such as step‑down coupons, digital barriers or dual currency notes.
4. **No pricing** – The system does not calculate fair values or implied volatilities.  Coupon ranges are interpreted qualitatively, not priced.
5. **No broker connectivity** – There are no APIs to execute trades, fetch live quotes or hedge positions.  The tool should never be used to automate trading.
6. **Requires human review** – Every recommendation is a suggestion only.  A trained structurer or salesperson must validate all changes before communicating them to clients.
7. **Limited front‑end features** – The UI is deliberately minimal.  It does not support authentication, session persistence or complex error handling.

The creators of Q‑Struct OS emphasise that this software is a *decision‑support sandbox*, not a production system.  Use it responsibly and always consult appropriate subject matter experts.
