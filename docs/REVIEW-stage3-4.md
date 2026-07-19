# Stage-3/4 review — paper broker + risk guards (Pat directive, 19 Jul)

Same adversarial treatment as the Stage-2 review: probe the failure scenarios, fix what
breaks, regression-test every finding. Two real bugs, one data-integrity gap, one
documentation gap.

## Findings and resolutions

**F1 — REAL BUG: risk-guard amnesia on restart.**
Probed the crash-restart scenario: the broker restored its trades from the ledger, but a
fresh RiskGuard knew nothing — `gate()` returned None on a day that had already hit the
daily loss limit. A crash-looping bot would re-trade straight through its daily loss
limit and equity floor. → Added `RiskGuard.seed(trades)`: rebuilds guard state from the
restored broker's trades WITHOUT re-announcing halts that already fired (on_halt
suppressed during seeding). Startup order documented: restore broker → seed guard → wire
Vault. Regression tests: seed-is-silent + full crash-restart drill.

**F2 — REAL BUG (alert noise): max-trades backstop equal to the engine cap.**
Default `max_trades_per_day=2` == the champion's own cap, so EVERY normal 2-trade day
announced a "max_trades halt" — daily false alarms that train the humans to ignore the
one real one. → Default raised to 3 (a backstop fires only if the engine's own cap
somehow failed) with the reasoning in the dataclass. Regression test: two normal trades
at defaults → no halt, no announcement.

**F3 — data integrity: the ledger fabricated fields on restore.**
`trigger_ts` and `stop_initial` weren't persisted, so `restore()` invented them
(stop_initial=entry). Fine for totals, wrong for audits and for any future logic reading
restored trades. → Ledger now persists the full trade (trigger_ts, stop_initial,
target_level added); restore is verbatim, NaN-safe for null targets. Regression tests
for verbatim round-trip and null handling. (Schema change is pre-deployment; no live
ledgers exist.)

**F4 — documentation: enforcement granularity.**
The dollar loss guard books a loss when a trade COMPLETES, so it cannot stop a second
admission inside the same one-minute bar; the engine's own -2R damage halt covers the
intra-bar case. Now stated explicitly in the module docstring instead of implied.

Cosmetic: `self_key` → `k` in restore.

## Re-verification after fixes
- 244 tests green (5 new regression tests), ruff clean.
- Real-data end-to-end re-run (Mar 17–20, new ledger schema): **defaults leave the
  champion untouched** — 6 trades / $25,000 → $30,995, identical to the ungated run —
  and the restart drill restores the account verbatim and seeds the guard with all four
  days' state.
- Vault/champion/engine untouched by this review → the Stage-7 parity gates stand.
