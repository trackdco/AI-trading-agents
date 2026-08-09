# EVERYTHING GENUINELY IMPLEMENTED + true-limit fill — corrected population count

**2026-08-08. Corrects `MINIMAL-FROZEN-SPEC-BUILD.md`**, which restricted the level set to the 5
literal rows `STRUCTURAL-LEVELS-AUDIT.md` marked COMPUTED. Angus's correction: *"minimal" means
everything GENUINELY IMPLEMENTED... include VWAP mid and the sigma bands, BB, POC, prior-day H/L —
everything actually coded. Drop only the 7 newly-surfaced absences and the previously scoped-out
branches.* `implemented_levels_limit_fill_build.py`,
`data/implemented_levels_limit_fill.json`. **No outcome computed** — same discipline as every
other geometry/count report this round.

## 1. The restriction collapses to no restriction at all

Every one of the "newly-surfaced absences" (weekly H/L, weekly volume-profile anchor, the
"structural" confluence type, 1h range, HTF-range-as-menu-level, "data extremes" — down from 7 to
5 clean gaps after `STRUCTURAL-LEVELS-AUDIT.md`'s own errata, §0-bis there) and the previously
scoped-out branches (Asia/London, VAH/VAL/HVN/LVN, pre-market H/L) were **already absent** from
`spec_current.py` / `invariants_2b.py`'s `lv`/`menu` construction — there was never anything extra
in there to drop. "Everything genuinely implemented, minus those absences" is therefore
**identical to the current, unmodified `lv`/`menu` construction**: BB MA, POC, daily VWAP
mid/±1σ/±2σ/±3σ (all four tiers — confirmed in code, see the errata), NY VWAP mid + conditionally-
eligible ±1σ, the running combined session extreme (`sess_hi`/`sess_lo`, newly documented in the
same errata), and prior-day H/L.

**This build therefore reuses `invariants_2b._instrumented()` unchanged, imported directly rather
than hand-copied.** The ±3σ mislabeling in the original audit came from transcribing the level
lists into prose by hand; importing the real function removes that failure mode entirely — the
level construction cannot silently drift from what the live code actually does.

## 2. The one real change: true single-bar limit fill, declared explicitly

Same declaration as the superseded build: the bar immediately after the signal bar closes is
checked for reachability (long: fills iff `bar_low <= limit`, short: iff `bar_high >= limit`);
fill price is the limit or better (`min(open, limit)` long / `max(open, limit)` short); no reach,
no trade, no later bar checked. `T_cancel` has no stated value and is disabled everywhere in this
project, so a multi-bar rest can't be built without inventing a parameter the spec doesn't supply.

Exit resolution (stop-vs-target) is used only to gate one-at-a-time re-entry, structurally
identical to `invariants_2b._admit` — no exit label is ever stored or reported.

## 3. Result

```
workbench sessions 539   processed 501   excluded {'holiday / short session': 22,
                                                    'roll session': 8, 'session after roll': 8}

candidates reaching the fill decision : 3104
  filled (bar reached the limit)      : 1444
  NOT filled (bar never reached it)   : 1660

ADMITTED-AND-FILLED TRADE COUNT: 1444
clears 661? YES  (1444 vs 661)
```

**1,444 trades. Clears 661.** Session accounting matches `invariants_2b.build_trade_list()`
exactly (539/501, same three exclusion reasons), confirming only the fill rule changed.

**Why this is close to, not far below, the original 1,472** (unlike the 47.8%-would-fill figure
`fill_fork_report.py` found on the *original* admission list): that figure was a **post-hoc**
filter over trades admitted under next-open-fill's one-at-a-time gating, where a filled position
occupies its day's slot until stop or target resolves. Here, the fill decision happens **inside**
admission itself — a no-fill frees the day's slot again at the very next minute rather than never
consuming it as a position, so far more raw candidates (3,104 vs ~1,472-ish before) get a turn
across the same sessions, and roughly the same 46.5% fill rate on a much larger raw pool lands
close to the original count. This is a real structural difference in the point process, not a
contradiction between the two reports — both are exact within their own stated construction.

## 4. N_trials

**Unaffected.** One configuration (the full current level set, true-limit fill, current-code
forks), stated before it ran, one count reported, no comparison by outcome. Same footing as the
988-trade build it corrects and the original identity-churn admission-count sweep. **N_trials: 1
of 5, unchanged.**
