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

## 7. Depth at the causally clean decision point — verified: real, modest, gold-concentrated

*The sweep's depth agent was cut off before reporting; the trial was re-run from
its script, then independently verified by an adversarial recompute. Coverage:
19,131/19,137 walked; 18,822 in the risk≥2pt population; 16,969 depth-evaluable.
Convention: snapshot = archive row minute T−1 (the book at the close), features vs
the displacement entry price, W/D/WALLSZ built exactly as `l3_check_trial`.*

**Causality is airtight — verified, not assumed.** 250/250 randomly sampled rows
reproduce exactly from the raw depth CSVs with fully independent selection code;
zero rows used a snapshot labeled past T−1; the archive's labeling was proven
floor-of-minute of the last book state (so row T−1 completes strictly before
boundary T); a synthetic test confirmed `depth_at` cannot leak the T row. All 24
lift-table numbers reproduce, and 250 rows recomputed end-to-end from raw
bars+depth (independent walk implementation) match 250/250. The at-close depth
convention is clean.

Pooled lift tables (2R / hold arms):

| check | cell | 2R lift | hold lift |
|---|---|---|---|
| W | pre·25 / pre·26 | −0.230 / +0.355 | +0.863 / −1.284 |
| D | gold·25 / gold·26 | +0.108 / +0.674 | +0.750 / +0.980 |
| WALLSZ | pre·25 / pre·26 | +0.154 / +0.068 | +0.446 / +1.064 |
| WALLSZ | gold·25 / gold·26 | +0.061 / +0.278 | +0.245 / +0.504 |

**Verifier corrections (both accepted):**

1. **Zero-fill bug in the WALLSZ table**: `WALLSZ` is never NaN by construction,
   so 621 depth-NaN rows were silently parked on the off side despite the
   "excluded, never zero-filled" claim (W and D tables excluded them correctly).
   Fixed: still 8/8 positive, but shaved — pre·26 2R +0.068→**+0.048**, gold·26
   hold +0.504→**+0.445**. The bug flattered 2026.
2. **Pooled counts overstate independent support.** The 16,969 rows collapse to
   ~1,602 same-direction ≤15-min episodes (mean 10.6 rows per episode). Under
   clustered views the 8/8 pattern breaks: equal-day weighting → 5/8 positive;
   episode-mean collapse → 4/8 (**all four gold cells positive, all four pre
   cells negative**); first-trigger-per-episode → 4/8 with gold·25 2R negative
   (−0.329). LODO (leave-one-day-out) keeps all 8 pooled cells positive, and the
   effect survives riskband stratification (8/8 in every band), kind mix, D==1
   restriction, and hold-clipping at +5R — so it is not an artifact; it is
   *smaller and narrower* than pooled counts suggest.

**Verified verdict per check:**

- **WALLSZ — a real but modest, GOLD-concentrated wall-size effect.** Gold cells
  survive every robustness cut except first-trigger collapse in 2025 (which is
  marginal: pooled +0.061, day-mean −0.069, episode-mean +0.046). Gold dose-
  response is weakly monotone (Spearman z=3–4; threshold 7 is NOT magic in gold —
  every threshold 3–15 is positive). Pre cells fail clustered views broadly, and
  pre·26 2R is positive *only* at exactly threshold 7 (magic cut — inadmissible
  under the threshold rule). Hold-arm pre magnitudes are ~90% a few >5R runner
  days. **Status: gold-scoped candidate, strongest in 2026 (discover-era support
  is the weak point); episode-clustered errors mandatory in the assembly test.**
- **D — a thin-book-day observation, not a per-trade edge.** The gold off-cohort
  is ~a dozen days / ~14 episodes per era (2026-03-16/17/18 alone contribute 57
  of 108 rows, all stopped). LODO stays positive in all four gold cells, but the
  2025 hold lift sign-flips under equal-day weighting (+0.750 pooled → −0.170
  day-mean). Honest reading: candle-closes-into-visible-vacuum days are bad days;
  carry as a gold stand-down *hypothesis* with ~14 episodes of support per era,
  not a validated gate.
- **W — noise, not even a sign-flip worth interpreting.** The on-cohort is 13
  days/23 episodes (2025) and 7 days/13 episodes (2026); day-mean disagrees with
  pooled in 2 of 4 cells; LODO crosses zero. Combined with its death at limit
  fills (`docs/FINDING-depth-lookahead.md`): W never measured anything real.
- **The structural point survives the corrections:** at limit fills the honest
  depth family was dead or halved; at the causally clean close, a verified
  (if modest) wall-size effect exists in gold. The depth information — whatever
  its size — lives at the close, and the archive's end-of-minute snapshot IS the
  book at the close, so under the decide-at-the-candle law
  (`docs/SPEC-EC-entry-matrix.md`) the instrument is correctly timed by
  construction.

## 8. Standing rules

Holdout untouched. One look, later, for one frozen candidate — human-authorized.
No profitability promised: the honest state is "census with a small set of
era-consistent filters, none yet positive net of costs in the discover era."
