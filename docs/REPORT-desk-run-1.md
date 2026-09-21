# Desk-run 1 recalibration report — June + September 2025 (2026-07-30)

ANGUS's checkpoint ruling: run two months, stop, recalibrate, re-run. This is the
recalibration. Run: chained desk-live agents (Sonnet, one conversation per trade,
event-driven turns, day-granular journal), 173 canon trades on identical fills vs shipped
V8. Chain stopped at Sept close as ruled; Dec + 2026 months unrun, reserved for run 2.

## 1. Headline

| | June (82) | Sept (91) | Total (173) |
|---|---|---|---|
| Agent | +34.9R | +19.5R | **+54.4R** |
| V8 | +27.8R | +12.6R | **+40.4R** |
| Delta | +7.1R | +6.9R | **+14.0R (+0.081R/trade)** |

Both months independently positive. Honesty first: paired delta SE is 0.069R, so t≈1.18 —
**a consistent pattern, not yet statistical proof.** The full run-2 sample exists to settle
that; nothing here is a verdict.

## 2. The decomposition — where the money actually moves

| behavior class | n | delta |
|---|---|---|
| V8 losers, agent managed the loss (took exit path) | 71 | **+23.9R** |
| V8 losers, agent refused the exit | 7 | **+7.8R** |
| V8 winners, agent took the exit path anyway | 44 | **−12.1R** |
| V8 winners, agent refused the exit | 32 | **−6.6R** |

The agent's edge is ENTIRELY loss-side (+31.7R): flow-against exits, tightened stops and
partials on dying trades (V8 losers realize −0.32R/−0.57R under the agent vs −0.79R/−0.89R).
The cost is ENTIRELY win-side (−18.7R): the same protective toolkit fired on trades that
were going to win — early partials and tightened stops clip winners even when the agent
does NOT refuse the exit. Defense is skill; defense-on-winners is the leak. The press
mandate ("hold when flow presses") has not shown up as offense at all — refusals broke
19 won / 25 lost.

## 3. What ANGUS ruled at this checkpoint

1. **Close-and-reverse adopted** (holdout look #3 priced it: CR-V8 $97,327 fit / $59,407
   holdout vs shipped $90,015 / $56,409). Clarified semantics: every trade keeps its own
   full bracket; the opposing signal's fill is an ADDITIONAL exit that flattens-and-reverses;
   an unfilled opposing signal changes nothing. Canon-law rewrite (funded_book references,
   conformance, Pat's flip spec) happens in one operation after run 2 validates CR
   end-to-end.
2. **Run 2 proceeds on the remaining sample** (2025-12, 2026-02/04/06, ~295 trades) under
   the recalibrated config below; June+Sept re-run under CR only if their run-1 numbers are
   needed as CR-comparable (decide at run-2 grading).

## 4. Run-2 configuration changes (proposed, for ANGUS sign-off)

1. **CR harness law**: a trade's lifetime hard-ends at an opposing canon fill (closed at
   the flip price, like the EOD flatten); the flip trade's card carries reversal context;
   the dying trade's final event names the opposing signal. Baseline becomes CR-V8 per
   trade.
2. **Asymmetric protection doctrine (the offense fix)**: protective actions (partial /
   tighten / exit) are FORBIDDEN while the trade is in the measured press state (>=+0.5R by
   minute 3-5, still green, within 0.25R of its own peak — the 79-88% all-era winner) unless
   the flow flip is volume-confirmed. The state line will carry an explicit `press_state`
   flag so this is checkable, not vibes. Defense doctrine on non-press trades stays
   untouched — it is the edge.
3. **Journal carries the decomposition**: the digest will show the agent its own
   defense-vs-offense split so the learning curve can see the leak directly.

## 5. Artifacts

- Monthly pages: June `claude.ai/code/artifact/ec9a1523...`, Sept `.../8fb7e2e4...`
- Journal + per-trade transcripts: `runs/desk/` (committed through `75c1d5f`)
- Driver: `scripts/capture_desk_run.py`
