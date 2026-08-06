# FINDING — the displacement-entry discovery sweep (2026-08-06)

**Fit span only. Holdout sealed. 13 agents: 1 harness attack, 6 measurement
families, 5 independent verifications, 1 synthesis. Every number below survived
independent recomputation unless marked otherwise.**

Entry model under test (ANGUS): TF candle closes through the level(s) → market at
the open of the next 1m bar; stop = signal-bar adverse extreme ∓1 tick. Outcome
arms: naive 2R-or-stop and EOD-hold (15:55). Population: all 19,137 fit triggers,
risk ≥ 2pt. Era discipline: 2025 = discover, 2026 = confirm.

---

## 1. The headline is dead: the never-filled cohort was selected by the future

The pilot's 83.4%/80.6% WR and +4.3R EOD-hold on never-filled limits
(`scripts/audit_displacement_entry.py`) reproduced exactly — and were then killed
by a mechanical proof, not a statistical argument:

**For 100% of never-filled rows, the candle stop sits at/beyond the limit-fill
price.** (Long: stop = bar_low − 1 tick, and the bar's low is above the limit —
that's what "never filled" means.) So during the working window, hitting the
candle stop *implies the limit would have filled first*. "Never filled" therefore
*guarantees* the market entry ran unstopped from entry through ~11:00. The cohort's
win rate is a tautology of its own definition. Supporting facts: NF stopped-ever
48.4% vs 95.2% for the filled cohort; the 6.1% of NF stops that occur before 11:00
are entirely an L1 bug (see §5), not real stops; effective sample is ~554
independent episodes, not 1,860 (~3.4 same-move sibling rows each).

The London-side "1,100 never-filled winners" reading is the same artifact and
should be treated as dead there too, absent an independent proof otherwise.

**The causal salvage path (open, unmeasured):** the runners insight is not
worthless — it becomes a *management* hypothesis measurable at T: enter at the
close, and treat any later retrace to the old limit level as the regime fork
(that retrace IS the old strategy's fill). Needs its own discover/confirm pass.

## 2. The honest baseline: the unfiltered family has no net edge

Causal ALL-triggers displacement entry, verified:

- **2R-or-stop:** 2025 negative at every cost level; 2026 +0.010 meanR at
  commission-only → **−0.003 at 1 tick of slippage**. The entire fixed-target
  edge sits inside one tick.
- **EOD-hold:** 2025 +0.009 at commission-only → −0.016 at 1 tick; 2026 +0.196 at
  1 tick — but hold means are tail-carried (top 5% of trades = 45–49% of total R;
  clipping at +10R flips **both** eras negative: +0.036→−0.326, +0.236→−0.222).
- **Slippage is understated by construction:** 99.1% of entry bars have range
  >8 ticks (median 1m entry-bar range 13.25pt). Market orders fire into fast bars;
  the 2-tick arm is a mid case, not a bound. No bid/ask or book impact modeled.

Conclusion: **a trigger census to filter, not a strategy** — the same starting
point the limit canon had before its check trial.

## 3. What survived discover-and-confirm (small, relative, mostly negative space)

1. **Candle-risk floor ≥7pt** — the strongest candidate. 2R lift +0.064 (2025) /
   +0.061 (2026), same quartile hump both eras (2–7pt worst, 15–30pt peak, 30+
   fades). Cost-coherent: the sub-7pt tail is where costs bite (−0.10..−0.29 at
   all cost levels, both eras), so the lift *strengthens* net. Thin flag: 2026
   gold/other OFF sides n=96/189. Open: floor vs 7–30pt band (both era-consistent).
2. **bp5opp absorption, GOLD only** — ≥3 of last 5 pre-signal minutes opposed.
   Positive both eras, both arms (2R +0.058/+0.110; hold +0.106/+0.282). The old
   canon's gold-window absorption story re-emerging under honest re-anchoring.
   Caveats: U-shaped count gradient in 2025 (magic-threshold risk), reverses
   outside gold, one of 15/42 sign-consistent cells under multiplicity.
3. **RANGEX ≥1 as a HOLD-horizon veto (inverse signal)** — signal-bar range vs
   trailing ATR: hold lift negative in all 6 era-session cells, 2026 quartiles
   monotone down. **Bigger displacement bars are worse to hold** — an exhaustion
   read, the opposite of the expansion thesis. 2R arm does not confirm;
   hold-scoped derate only, never an entry gate.
4. **Mon–Thu over Friday** — Friday worst both eras (2R lift +0.066/+0.089).
   Borderline; secondary check, not a law.
5. **Other-session d30 confirming-flow cluster** — positive both eras/arms but
   flips elsewhere and the 'other' bucket is a regime mix; candidate only after
   the session buckets are cleaned.

**None of these makes 2025 positive net of costs.** No profitability is claimed.

## 4. What died (the important kills)

- **FLOWCONF (signal-bar delta agrees with the break)** — the core flow thesis.
  2025 hold lifts (+0.07..+0.29 all sessions) fail 2026 (pre −0.179, other
  −0.109); quartile trend outright reverses. The era-stable residue is real but
  EV-neutral: flow-confirmed closes finish positive 1.4–2.2× more often in every
  cell, both eras, *offset by smaller winners*. **Flow through the close tells you
  the break is more likely to hold, not that it is worth more.** Exit-research
  lead, not a gate.
- **VOLX, CLOSELOC, the FLOWCONF×CLOSELOC "conviction close"** — sign flips,
  non-monotone, magic thresholds. Dead.
- **Tc/Tp/T2 pre-signal CVD trend, both anchorings** — era sign-flips everywhere;
  2025 actually favors *opposed* 15-min flow. Dead.
- **Close-through geometry (THRUDEPTH)** — causal form: non-monotone, no
  consistent lift. The strong-looking deep-thru penalty (−0.45..−0.74) exists only
  vs the old limit price on the fill-selected cohort — never-filled runners close
  *deeper* (median frac 0.45–0.51 vs 0.28–0.32), so conditioning on fill
  manufactures the penalty. **The central trap of the sweep.** Inadmissible at T.
- **VWAP/BB placement at T, LONSLOPE** — nothing confirmable; the 2026-gold
  |sd|≥2 cell (+0.60/+3.43) is an n_on=43 one-cell wonder.
- **KIND (displacement > rejection_block)** — the pilot's split does NOT hold:
  2R +0.051 (2025) reverses to −0.013 (2026); hold negative both eras; largely a
  riskband effect (displacement candles ~2× wider). Bears directly on the EC
  matrix — see §6.
- **STRUCT_EVENT (broke/rejected)** — biggest lifts in the sweep (+0.9..+1.4
  everywhere) and **100% post-T** (all struct_ts ≥ T). Near-tautological outcome
  description; banned from entry, promoted to exit/management research.
- **TRIG, AGE, TF, first-hour, session base rates** — dead (AGE additionally 4.9%
  post-T contaminated via overnight tape through 08:00 on 07:45–07:59 entries).
- **The EOD-hold arm as a ranker** — tail-carried; hold-only lifts cannot gate an
  entry check.
- **Old vetoes as laws:** under displacement entry, **vetoed_bb_vwap outperforms
  the allowed population in 9/12 cells** (advantage survives close-through-depth
  control, 2026 confirms 2025) and vetoed_rr_floor looks similarly obsolete
  (thin). Both re-opened as flags. vetoed_bad_geometry: (thin) supportive — keep.
  news_preopen / window: era flips — undecided.

## 5. Harness verdict and the bugs that become conventions

Attack verdict on `scripts/audit_displacement_entry.py`: **SOUND-WITH-CAVEATS.**
All headline numbers reproduce; walk mechanics are correct and, where ambiguous,
conservative. Label convention CLOSE is settled — empirically 239/240 and
source-corroborated (`src/engine/triggers.py:80` "ISO ET — candle close time";
`src/engine/sessions.py` resample `label='right'`); conclusions survive the wrong
convention too. Bugs found (all small, all now rebuild conventions):

- **L1 fill walk skips the trigger bar** (`scripts/build_l1_fills.py:83`,
  searchsorted `side='right'`): "never filled" is not exactly "price never traded
  there" — ~6% of NF stops trace to fills L1 never evaluated. Fix: evaluate the
  bar at ts inclusive.
- **Gap-through-stop silently dropped** (risk ≤ 0 → None): only 6 rows under
  CLOSE but 192 under START and adversely selected — must be scored as immediate
  losses, never dropped.
- Resolver compares vs NaN entry for non-outcome statuses (printed n=240 was a
  NaN artifact), tie-breaks toward the wrong convention, dead r_eod code.
- 09:30–09:40 falls in no session bucket — silently 'other'. Must be named or
  excluded explicitly.
- 2R "WR" counted positive-EOD-close as a win (2–3pp inflation) — report pure-2R
  WR alongside.

Full convention set for the rebuild (cost ladder with 1-tick as the deciding
column, per-feature pre-T causality audit, episode-level clustering, monotone-
support threshold rule, versioned feature builders, riskband-stratified era
comparisons): see the synthesis record in the run journal
(`wf_b89638d4-ea6`) — to be codified in the L1–L4 rebuild spec.

## 6. Consequence for the EC matrix (`docs/SPEC-EC-entry-matrix.md`)

The decide-at-the-candle law is *strengthened* by this sweep (the two admissibility
kills — NF cohorting and fill-conditioned THRUDEPTH — are exactly what the law
forbids). But the matrix's per-kind row assignment is currently **unsupported**:
KIND died as a separator once riskband is controlled. Whether rejection blocks
belong on the limit leg is an open question for the EC run (rejection-block limit
outcomes re-trialed with features frozen at T, vs their market-at-close
counterfactual, riskband-stratified) — not a settled premise.

## 7. Depth at the causally clean decision point

*The sweep's depth agent completed its harness but was cut off before reporting;
the trial was re-run directly from its script
(`scratchpad/honest_disp_depth.py` → results below).*

**PENDING — this section is filled by the re-run.**

## 8. Standing rules

Holdout untouched. One look, later, for one frozen candidate — human-authorized.
No profitability promised: the honest state is "census with a small set of
era-consistent filters, none yet positive net of costs in the discover era."
