# RULING — every applied change is MECHANICAL. No agent discretion in or near the trade path.

**Angus, 2026-07-26 (verbatim):** *"all changes we apply should be mechanical btw, i dont want
agent discretion involved if we've built a heavily profitable engine already. agent discretion
with lack of live experience could make it worse rather than better, so now i want the agents
to stick to the mechanical rulebook."*

This extends the standing doctrine (zero LLM in the trade path; agents ADD, never subtract;
the spine has "no judgment, no LLM, no tuning in the moment") from the RUNTIME to the
CHANGE PROCESS itself:

- **Agents may discover.** Measurement, leak-hunting, threshold derivation, OOS validation —
  all of today's work — is agent territory.
- **Agents may not decide or adapt.** Nothing an agent "thinks" at runtime touches an order.
  No adaptive thresholds, no regime judgment calls, no LLM-picked parameters at trade time.
- **What ships is a frozen constant or deterministic rule**, backtest-validated, signed off by
  Angus, applied by code that would produce the identical trade from the identical inputs
  forever. If it can't be expressed that way, it doesn't ship.

## The current change list, in its mandatory mechanical form

| change | mechanical form |
|---|---|
| news blackout (ADOPTED) | table lookup on a frozen dated calendar snapshot; fetcher observes only |
| 09:55–10:00 dead-zone entry cut (ADOPTED 2026-07-26) | one frozen interval, `dead_zones=[(595,600)]` in `build_canon` |
| ~~rr_floor 1.5~~ **RETRACTED 2026-07-26** — 80% of the gain was one degenerate 6pt-stop fill; ex-freak the 1.5 book is −6.9R worse. Floor stays 2.0 | (no change; two new guards below) |
| walk_menu target sanity clamp (≤ K·R) + fill-time min-stop recheck | two frozen constants |
| stop-width fix, if H3 wins instead | frozen stop-sizing rule (e.g. k×structure), re-derived book |
| 3-min cut re-calibration at the new floor | two frozen thresholds (r_3, fw_3), re-derived like Layer 2d |
| post_open_min_stop review (verify CONFIRMED +14.1R) | keep / change / delete one frozen constant — Angus ruling |
| daily loss halt | −4R constant against the day's base_dollar (already ruled) |
| late-window subsets (exploratory) | if ever adopted: frozen check thresholds, same freeze→OOS ritual |
| CVD/depth NaN handling | fail-closed code rule: missing data = missing context, never a score |

Agents remain welcome OUTSIDE the path: calendar upkeep, parity checking, alerting, journal
audit, discovery. The boundary is the order: nothing between signal and broker consults a model.
