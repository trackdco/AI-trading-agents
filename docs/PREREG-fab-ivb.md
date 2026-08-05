# PREREG — fab-ivb: NY opening-battle breakout (FAB-1/FAB-2 event tree)

Committed BEFORE any census or test touches data. Family: NYA-IVB-01.
Source: research/findings/fabervaale-diagnosis.md (FAB-1, FAB-2);
research/transcripts/fabervaale/EXTRACTION-A-models.md (cUTsoU-15Tc, StaphlRH8NQ).
Program: NY-AM (this session's chat). Owner: Claude; verdicts to Angus.

## Thesis (plain language)

The first 30 minutes of the New York cash session is the day's main battle:
the side that first breaks the initial balance (IB = 09:30-10:00 high/low)
has won it, and the day tends to continue that way far enough to pay. The
counterparty: traders positioned inside the balance whose stops sit beyond
the opposite extreme, and breakout-faders fighting the resolved auction.
Claimed numbers to TEST, not trust: +13.5% skew over coinflip at 1:1 (long
side); a statistical excursion target hit 65-70% of the time. Independent
literature: IB direction predicts break side 74-81% (large sample); BUT a
direct MNQ study found every ORB variant dies at 2-pt friction — cost realism
decides this family.

## Declared universe and spans

- Sessions: all RTH days, data/reference/nq_1m_master.parquet, 2023-01 →
  2026-07 (911 sessions; amt_days.parquet substrate).
- Era discipline: discover 2025, validate 2026, inverse pass (discover 2026 /
  validate 2025), 2023-2024 as additional structure (NOT the sealed holdout —
  the six sealed months stay untouched).
- Flow span (2025-06 → 2026-07) for all order-flow arms.

## Event tree (one family, all arms share the ledger)

- BRANCH A (breakout): IB = high/low of 09:30-10:00. First 1-min close
  beyond IB high/low after 10:00 = direction event. Expressions declared:
  A1 enter at the close-beyond bar; A2 enter on retrace to the IB midpoint;
  A3 enter on retrace into the IB volume-profile POC-to-nearest-value-edge
  zone (his "block of orders"; IB profile from 1-min bars, volume-at-price
  approximation). Invalidation for retrace arms: 1-min close through the far
  value edge of the IB profile.
- BRANCH B (pre-break range fade): before any break, fade a touch of the IB
  extreme back toward the IB midpoint. Only 10:00-10:30 touches (IB must be
  complete); dies at the first break.
- IB-length variants 15/60 min are DECLARED arms (each ledgered) — 30 min is
  primary per source.

## L0 census (before any P&L)

1. Break frequency + first-break side vs prior-day close direction.
2. The +13.5% claim: P(close of day beyond entry by >= initial risk) at 1:1
   from the first-break close, long and short separately.
3. Excursion ladder: post-break MFE quantiles (the "protection level" is a
   quantile — derive ours; test the 65-70% hit claim).
4. Conditioning previews (census only): IB size vs ATR (narrow-IB claim),
   day type, open type, gap state.

## Kill classes (declared)

- K1 premise kill (legal at L0): first-break direction shows NO skew (<52%
  at 1:1 both eras) → family dies.
- K2 era-flip kill: any arm profitable in one era and losing in the other
  after full conditioning → that arm dies.
- K3 expectancy kill: legal ONLY after the full conditioning search
  (candle + flow-at-entry + geometry arms complete) per §3.2 kill-class law.
- Cost stack: base 1pt friction AND strict 2pt; an arm that only survives
  base gets the friction flag on its label (§2.5; the MNQ result is the bar).

## Declared conditioning variables (searched before any expectancy kill)

IB size/ATR; open type; day type; gap state; overnight range position;
pre-market CVD pressure (P6 gate — cross-feed); flow-at-entry at the break
(delta at break bar, absorption at IB extreme, effortless-move flag from the
P7 library when built); depth-wall state at IB extreme (heatmap span).

## Redundancy gates (early, mandatory)

- vs canon gold leg (09:40-10:30 clock overlap): pairwise vs canon's actual
  fills BEFORE refinement (euro-handoff precedent).
- vs Brake's NY candidates as they emit (shared vault).

## Exit ownership

Arms declared at L1 after census geometry is known; tournament then FREEZE
per ship contract. Time-stop family: 11:00/11:30/EOD declared now.

## Promotion rule (declared 2026-08-05 under §6.0 law; branch A already dead)

Branch B (range fade), if its census passes: DEFAULT SPEC by mechanism prior
= fade the completed-IB extreme touch toward IB mid, stop beyond the extreme,
10:00-10:30 only. Displacement of the default requires PBO < 0.5 on the arm
matrix AND holdout adjudication — never in-sample rank. Family promotion
requires era-consistent positive at base friction + merged-ledger recording +
correlation battery vs canon (clock overlap known).

## Trial ledger

Every arm above counts. Narrative in research/candidates/nya-ivb.md; numbers
in output/trial_ledger.parquet via src/validation/trial_ledger.py (§6.0).
Program-level deflation merged with Brake's NY program.

## SEARCH EXPANSION — declared 2026-08-05c (ANGUS: "we really arent testing enough")

Branch B search space widened BEFORE running, all arms ledgered:
- EVENT EXPANSION: E-all = every touch (incl. re-touches after a rejected
  touch) until the IB first breaks; window arms 10:00-11:00 and 10:00-12:00;
  per-day multi-trade allowed (one open position at a time).
- STOP CAPS: absolute caps 20/30 pts on the 0.25xIB stop (large-IB days
  currently risk 40+ pts).
- STATE-CONDITIONAL FLOW (the drawdown question): flow-at-entry re-tested
  WITHIN states — strategy trailing-5-trade P&L negative/positive; day
  one-timeframing state at entry (no-lookahead); entry after a prior same-day
  loser.
- FLOW DEFINITION VARIANTS: absorption at eff_z >= 1.5 (looser), delta lean
  windows 5m and 10m, CVD session-side agreement.
- CANON VARIABLE MAP: on receipt of the canon build's full variable list
  (Angus, from the rebuild chat), each canon variable class gets a declared
  analog arm here. Placeholder classes now: vwap-sd position at entry,
  prior-day close relationship, gap state, trigger-density analog
  (touch count so far today).
