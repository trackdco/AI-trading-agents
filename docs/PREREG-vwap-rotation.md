# PREREG — Orochi VWAP-SD2 rotation fade, RTH (NYA-VWR-01), as taught

Committed BEFORE any census touches data. Source:
`research/transcripts/orochi/RESPEC-as-taught-2026-08-05.md` SPEC 1
(regime-gated sd2 fade) and SPEC 3 (retest + compound-add grammar);
instrument definition pinned in transcript `IMs472GOwnY`. Credibility:
`research/findings/orochi-credibility.md` — anonymous, ~10-month footprint,
recaps are post-hoc chart markups with no execution evidence. We test
mechanics and ignore every claim. Program: NY-AM. Owner: this chat;
verdicts to Angus. §5.9 / §5.9.1 / §5.10 / §5.11 / §5.12(+.1) / §6.0 in
force from birth.

## Thesis (plain language)

One falsifiable sentence: **when the New York session is rotating inside its
own value — nobody has established acceptance beyond either 1-sigma edge —
a stretch to the 2-sigma band of the session VWAP is an over-extension that
pays a trip back toward the mean.**

Mechanism (why the market should pay this, not just what the pattern looks
like): the 2-sigma band is where the session's chasers are. They bought (or
sold) a stretch away from a price the whole session's volume agrees on,
while no auction has actually accepted business out there. They are offside
against fair value and their exits are the fuel for the trip back. The
setup exists *because* the crowd fades sd2 indiscriminately — his own words:
"a lot of people are always trying to trade off of the second standard
deviation. That's just not the case. Only in certain kind of market
conditions." The regime gate is the entire edge claim; without it this is
the crowd's losing trade.

## HISTORY ON THE RECORD (read before the numbers arrive)

This family's OVERNIGHT cousin (NYO-ROT-01) was tested and park-recommended
TODAY. Trials 3-4: the corrected as-taught grammar ran **WORSE** than the
strawman it replaced (V-A n=63 PF 0.92; V-B n=74 PF 0.82) and no
era-consistent gate was found. That is context, not fate — this is the RTH
version, his actual primary session, and it is untested. But the prior is
recorded now, before results exist, so a weak outcome cannot be
re-narrated later as a surprise.

## Declared universe

- **Span: FIT ONLY = 2025-06-02 → 2026-07-15**, 290 RTH sessions, verified
  present in `data/reference/nq_1m_master.parquet` (the 13 full-coverage
  months, §5.11-9a). **Holdout look: NO — fit-only, no holdout look spent.**
  OOF = the six sealed 2023/24 months, single look, later, Angus's call.
- **Session: RTH 09:30–16:00 ET.** Vault vocab currently defines `ny-pre`
  and `ny-gold` only; this declares a new value **`ny-rth`** per the
  "extend per session actually defined" clause — flagged for ratification
  (VAULT-SCHEMA §5 is [OPEN — needs Angus]).
- **Entry type:** limit/rotation, E3-style.
- **Mechanism family:** `vwap` (VWAP geometry). Input-family note for the
  correlation veto: this family is `vwap`-only at census; it shares NO
  gating family with the canon at this stage (canon's edge is
  depth/displacement). Stage 2 adds `order-flow` / `depth-walls`, which
  WOULD start sharing families — the veto question is declared now, owed
  before stage 2, not after.
- **Input columns (exact, census stage):** from `nq_1m_master.parquet` —
  `ts_event`, `open`, `high`, `low`, `close`, `volume`. Everything else is
  derived in-script and named here: `vwap`, `sd`, `sd1_up`, `sd1_dn`,
  `sd2_up`, `sd2_dn`, `vwap_slope15`, `sd2_dist_sigma`, `band_w_pts`,
  `tap_n`, `regime_state`, `gap_pts`, `clock`.
- **Costs:** base 1 pt round-turn, strict 2 pt, both reported (house
  convention). **Limit fills count only when price trades THROUGH the
  level, never on a touch** (§2.5).
- **Reporting:** per arm, per YEAR-HALF (§5.11-5), to `research/FUNNEL.md`.

## The instrument (his exact definition, DECLARED)

- Session-anchored VWAP on typical price (hlc3), volume-weighted, bands from
  the running volume-weighted standard deviation — TradingView "standard
  VWAP", the same construction as `scripts/nyo_rotation_respec.bands()`,
  extended to ±2σ.
- **±1σ = the value area. ±2σ = the rotational extreme.** All bands
  DEVELOP (recomputed every minute; they move).
- **Anchor: 09:30 ET RTH — DECLARED PRIMARY** for this chat. His NQ
  examples used the Globex daily (18:00 ET) anchor; **A2 = the 18:00-anchor
  variant, a declared arm**, not a silent choice.
- **Warm-up exclusion:** first 15 minutes skipped — first eligible trigger
  minute **09:45**. Declared arm W2 = 10 minutes (09:40). His words:
  "pretty much useless for the first 10 15 minutes."

## The EVENT (what gets counted as a raw trigger)

Price **reaches** the ±2σ band while the session is **rotational within
value**. Reach = bar high ≥ sd2_up (short side) or bar low ≤ sd2_dn (long
side), on **closed 1-min bars** (arm: 5-min trigger bar, D4).

**UNCAPPED, per standing convention:** every qualifying sd2 reach counts;
sequential re-entries allowed; **no per-day cap**; time-of-day RECORDED,
never filtered. Tap number recorded per session per side.

## The regime gate (his hard gate — the whole edge claim)

At trigger time, **no acceptance established beyond either ±1σ edge this
session**. "Acceptance" is HIS gap; declared arms, none silently picked:

- **G1 (default):** 1 close beyond an edge does NOT kill the gate;
  **2 consecutive closes beyond an edge = acceptance**, gate dead for the
  session on that side.
- **G2:** N=3 consecutive closes = acceptance.
- **G3:** time-based — ≥15 cumulative minutes beyond an edge = acceptance.
- **G4 (D2 classifier variant):** price currently inside ±1σ AND has traded
  both sides of VWAP this session.
- **G5 (weakest textual support, declared as arm not default):** VWAP slope
  filter — |`vwap_slope15`| under threshold. He defines imbalance as "VWAP
  trending with price", so this is an arm, per RESPEC D2(c).

## Entry arms (D1 — never silently pick one)

- **E-a (DEFAULT):** fade the first sd2 touch, at the touch.
- **E-b:** wick beyond sd2 + close back inside sd2; entry at that close.
- **E-c:** his sweep-case literal — entry only on re-entry into the ±1σ
  band ("nothing has changed yet until we get back into value").
- **E-d (SPEC 3 grammar, its own arm):** first rejection → **RETEST entry
  with 1/3 risk** → **add remaining 2/3** on acceptance-back-inside after a
  shallow poke out (<0.5σ excursion declared as "slightly"). His only
  taught sizing law anywhere; a single-entry census understates this arm's
  expectancy shape, so it runs as a two-tranche sim.

## Stop arms — HOUSE INVENTION, declared as such

**The stop is NEVER TAUGHT anywhere in the corpus** (RESPEC SPEC 1 §3,
cross-spec flag). Every stop below is ours, and per Angus's standing rule
**no oversized stops — capped from birth**:

- **S1 (default):** beyond the trigger bar extreme + 1 pt buffer, **capped
  at 20 pts**.
- **S2:** 0.5σ beyond the sd2 band, capped at 20 pts.
- **S3:** fixed 20 pt cap (cap20 — the expression that rescued the IB
  family, §5.11-3).
- **S4:** fixed 30 pt cap.

Stop choice cannot be a silent kill vector: all four run, all four carded.

## Target arms (taught)

- **T1 (default):** the mean — developing VWAP. His first-named target.
- **T2:** the opposite ±1σ edge ("the other side of value").
- **T3:** POC/VWAP-interrupt scratch (the taught exit mechanic from SPEC 2 —
  the mean "can stop that move").
- **Frozen vs developing:** targets run BOTH as frozen-at-entry and as the
  developing line (RESPEC cross-spec flag — frozen-level backtests are a
  systematic deviation from what he trades).
- Time stop: flat at 15:55 ET if neither side hit.

## Recorded per event, from birth (§5.12-5)

`side`, `sd2_dist_sigma` (how far beyond the band), `band_w_pts`,
`regime_state` (which gate arm passed/failed), `vwap_slope15`, `clock`,
`tap_n`, `gap_pts` (overnight gap context), MFE/MAE, checkpoints at
**t+2/3/5/8/10** (canon §5.12-5 grid) **and t+15/30** (brief), and the
outcome under **every** declared exit arm. Terminal status on every
candidate trigger (`filled` / `vetoed_<reason>` / `cancelled_<reason>`) so
the funnel has no silent drops (§5.12-1).

## Acceptance bars

Census stage has no pass/fail bar — it is a count and a card. The bars that
govern anything downstream, declared now so they cannot be shopped later:
≥30 trades per era cell for a direction claim, ≥100 pooled for a magnitude
claim (§2.2); family-wise permutation null ≥1,000 shuffles at p ≤ 0.01
(§2.3); DSR ≥ 0.95, PBO ≤ 0.25 (0.25–0.50 INCONCLUSIVE and blocks, ≥0.50
condemns the search) (§2.4); era-consistency in the same direction in every
era; drop-top-3 fragility; strict-cost survival.

## Kill classes

- **K1 — structural absence, the ONLY legal census kill (§5.9.1):** the
  taught trigger never fires, or the claimed event does not occur. Nothing
  else dies at this stage.
- **K2 — era-flip per arm**, legal only AFTER the declared search runs.
- **K3 — expectancy**, legal ONLY after the complete conditioning search
  including the flow cross-check (§5.9.1: an expectancy kill that predates
  the flow search is PREMATURE and gets vacated).

**NO BIN OFF RAW.** Ugly raw P&L is the expected shape — the canon's own
raw triggers were unprofitable. Raw ugliness is not evidence against this
family and will not be reported as if it were.

## Promotion rule (§6.0 — declared BEFORE the tournament that could exploit it)

- **Default spec = the mechanism-prior as-taught expression:** anchor 09:30,
  warm-up 15 min, gate G1, entry E-a, stop S1-capped20, target T1 (mean),
  developing line.
- **Rank-and-promote-the-top-scorer is condemned and is not available
  here.** No arm displaces the default because it out-scored its siblings
  on the fit span. An alternative arm may displace the default ONLY on
  **PBO < 0.5 on the arm matrix AND out-of-fit adjudication**. In-sample
  rank alone never suffices.
- Every arm — winner, loser, abandoned — gets a row in
  `output/trial_ledger.parquet` (240 rows at writing). Trials recorded in
  prose only do not exist for deflation purposes.

## Known limits, stated up front

1. **The source is unverified and anonymous.** No track record, no
   execution evidence, 13 self-hosted reviews. We are testing mechanics
   that happen to be well-specified, nothing more.
2. **The overnight cousin failed on corrected grammar** (above). If this
   one also comes back weak, the family-level reading is that the taught
   sd2 grammar does not survive honest testing on NQ — but that reading
   needs BOTH results, and stage 1 is not where it gets made.
3. **The stop is entirely ours.** Any expectancy result is partly a
   verdict on our stop choice, not purely on his teaching. This is why
   four stop arms run from birth.
4. **Depth coverage does not span RTH.** Depth is 08:00–10:29 ET, so it
   covers only the first hour of the RTH session — stage-2 depth work will
   be structurally thin on afternoon triggers, and will say so rather than
   pool it away.
5. **Overlapping trades:** the uncapped convention permits concurrent
   positions; per-trade statistics will need the effective-N correction
   (§2.2), not raw trade count, at any significance stage.
6. **Provenance disclosure (§0 law 4 — stated, not hidden):** before this
   prereg was written, this session computed *data-availability* statistics
   (session-day counts per month, symbol composition) on the STALE bar
   files of an old branch, while establishing that the working data
   existed. No strategy outcome, trigger, or P&L was computed at any point
   before this file was committed. The census below is the first scoring
   contact with the fit span.

## Artifacts

- Census script: `scripts/nya_vwr_census.py` (adapting
  `scripts/nyo_rotation_respec.py` band machinery + the
  `scripts/nya_ibc_census_uncapped.py` uncapped sequential pattern).
- Event set: `output/nya_vwr_events.parquet`.
- Card: `research/FUNNEL.md` (raw, per §5.10).
- Candidate file: `research/candidates/nya-vwr-rotation.md`.
- Ledger: `output/trial_ledger.parquet`.

## Stage gate

Stage 1 = **prereg → uncapped census → raw card → STOP.** Stage 2
(flow / depth / conviction / in-trade per §5.11-9c) does not begin without
an Angus ruling. Nothing here self-authorizes.
