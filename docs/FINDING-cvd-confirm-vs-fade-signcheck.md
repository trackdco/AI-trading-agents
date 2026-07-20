# CVD selection edge: it's CONFIRMATION, not fade — sign/label reconciliation

**TL;DR:** The engine lane's `selection_study.py` and an independent data-lane check found the
**same real edge** — gating entries on pre-entry aggressive flow lifts win rate ~25%→40%. But
the script's **labels are inverted**: it calls the winning gate a "fade (flow against the
trade)" when the trades it actually selects are **flow that CONFIRMS the trade** (buyers
dominant before a long). The gate picks the right trades; the mechanism story is backwards.
Flagging so downstream design doesn't build on "fade aggressive counter-flow" when the truth is
"enter with confirming flow." @Angus please confirm the intended sign convention.

## Evidence (on `selection_study.py`'s own candidate set, n=159)

| Bucket (Angus's label) | n | win | $ |
|---|---|---|---|
| `cvd<=0` — labeled **"FADE"** | 96 | **40%** | +12,469 |
| `cvd>0` — labeled "follow" | 63 | 25% | +2,144 |

Translation for LONGS: `load_cvd_delta()` computes `A - B` (sell − buy), so `cvd<=0` ⇒
`A ≤ B` ⇒ **buyers dominated the 3-min pre-entry window** ⇒ that's **confirmation**, not a fade.
- longs `cvd<=0` (buyers dominant): 53t, **43%** win
- longs `cvd>0` (sellers dominant): 34t, 26% win

Independent data-lane check on `journal_champion.csv` (n=146), plain buyers-vs-sellers,
3-min causal pre-entry window:
- flow **WITH** trade (confirm): 83t, **37%** win, +$10,929
- flow **against** trade (fade): 63t, 27% win, +$2,928
- longs: winners avg net-buy **+68**, losers **−25** (buyers before winning longs).

Both tests agree: **entering with confirming flow is the edge.**

## Root cause
`load_cvd_delta()` (line ~53): `np.where(side=="A", +vol, -vol)` = `A − B` (sell − buy), but the
docstring (line ~14) says "signed aggressive delta (**buy-sell**)". The variable is sign-flipped
vs its stated definition, so the "FADE = flow against (low/negative)" framing labels the
confirmation bucket as fade. The `cvd<=thr` gate still selects the right (confirming) trades —
only the naming/interpretation is wrong.

## Confound check (completes the step `selection_study.py` crashed on)
The script raises `AttributeError: 'DataFrame' object has no attribute 'date'` at line ~157
(`P0.date`) — the groupby-apply left `date` in the index, so the proxy check never ran.
Completed here — **confirmation beats non-confirmation within every segment** (not a
time-of-day / WAR proxy):

| Segment | CONFIRM win | NON-confirm win |
|---|---|---|
| pre-open | 37% (+$7,828) | 26% (+$2,469) |
| post-open | 48% (+$4,642) | 25% (−$325) |
| non-WAR | 60% (+$3,927) | 22% (−$681) |
| WAR | 37% (+$8,542) | 26% (+$2,825) |

## Magnitude reality (don't over-sell it)
- Oracle+stand-down ceiling = **$30,109**; 60% target = $18,066.
- Current champion P0 static-2: $14,009 (47% of ceiling), 33% win.
- Confirmation gate (`cvd<=0`): ~38% win but ~$12.5k — **higher win rate, slightly fewer
  dollars** (it also drops some winners). Strict confirmation (`cvd<=-200`): 57% win, but only
  14 trades / $1,116.
- So confirmation is a real **selectivity / win-rate** lever, **not** a P&L multiplier. It
  raises accuracy toward the ~50% target on far fewer trades; total dollars don't jump.

## Recommendation
1. Confirm the sign convention and relabel "fade" → "confirmation" in `selection_study.py` so the
   mechanism story is right (affects what features we build next).
2. Fix the `P0.date` crash (reset_index before the proxy check).
3. Confirmation gate is worth keeping as a win-rate lever; pair it with outer-band VWAP location
   (±2σ/±3σ respected 67–77% in April) rather than confluence-count (which was backwards) or
   heatmap depth (no edge in April) or VIX (null).
