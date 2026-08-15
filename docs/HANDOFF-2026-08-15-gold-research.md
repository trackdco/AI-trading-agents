# HANDOFF — gold research track, as of 2026-08-15

**Read this first if you are a fresh session picking up this work.** It is written for an
agent with no prior context. Everything below was verified against the repo at commit
`adac7b9`, not recalled.

---

## 0. Paste this into the new session

> Read `docs/HANDOFF-2026-08-15-gold-research.md` on branch
> `claude/video-plugin-setup-t89hhm` of `trackdco/AI-trading-agents`, then tell me what
> state the work is in and what the blocker is before you do anything else.

---

## 1. Coordinates

| | |
|---|---|
| repo | `trackdco/AI-trading-agents` |
| working branch | **`claude/video-plugin-setup-t89hhm`** — develop and push here only |
| open PR | **#14** — pushing to the branch updates it, do not open another |
| default branch | `claude/ai-trading-agents-repo-r64muf` (NOT `main`/`master`) |
| commits in this stream | 24, from `bc9649f` through `adac7b9` |

## 2. Division of labour — do not drift off it

**Angus is doing NQ. The user is doing gold.** The user said this explicitly after I kept
surfacing NQ results. NQ work is still legitimate as a *control* or as borrowed
methodology, but do not recommend NQ strategy work as the next step — it is not their lane.

**Vocabulary trap:** the word "gold" in this repo's older docs means the **09:40–10:30 ET
session window**, not the metal. `docs/CANON.md`, `docs/BASE-RATES.md` and anything
NQ-era use it that way. The new gold work means GC/XAUUSD. Read every pre-existing
"gold" mention as the time window until proven otherwise.

## 3. The law

**Repo non-negotiables** (`docs/CANON.md` is the single source of truth):
- No LLM in the risk or execution path.
- **No parameter tuning to make a backtest look better.** Divergences get reported, not
  fixed. This is the rule most likely to be broken by accident.
- The strategy doc outranks the code. If they disagree, the code is wrong.
- No lookahead. `test_autopsy_features_cannot_see_past_the_signal` is the pattern —
  truncate the series after the fill and demand identical feature values.
- Keys live in `.env`, gitignored, never printed and never committed.

**`.claude/settings.json` has a deny list. It is deliberate — respect it.** It blocks
`data/narrated_days/**`, `docs/CORPUS-narrated-days.md`, `docs/FINDINGS-selection-effect.md`
and `output/agent_runs/**` so a cloud session cannot leak scored agent runs. Do not read
around it, do not ask for it to be lifted.

**Methodology bar** — every result in this stream clears these, and a new one has to too:
- **Day-clustered bootstrap** (BR-42) for every interval. Trades on the same day are not
  independent.
- **Dual currency** (Law 3) — win% *and* EV on every row. A filter that lifts win rate and
  not EV is a refutation, not an improvement. BR-20/46/48 are three recorded cases.
- **Both-era clearance** (E1.4) — split the sample in half; a cell must clear zero in both.
  On gold, 8 of 14 cells cleared zero on the full sample and only 1 cleared both halves.
  That gap is the entire reason the bar exists.
- **First trigger per structural fight** (BR-9/BR-10). BR-10 records the same population
  reading −0.04R to +0.20R across conventions, so state the convention up front.
- **Post-entry variables are not findings** (BR-41).
- **Risk-coupled features must be flagged** (Law 2) — most "wider stops are better"
  results are the cost denominator, not a market fact.

## 4. What is established

Ranked by how much weight it will bear.

### SOLID — BR-1 transfers to gold
`docs/FINDINGS-gold-htf-census.md`. GC, 1,276,717 1m bars, 4,934 displacement episodes
over 934 session-days.

| | rate |
|---|---|
| touch of the moving 15m BB MA before session close | **92.85%** [92.26, 93.42] |
| same MA **frozen** at displacement (placebo) | 71.73% [70.52, 72.94] |
| **edge** | **+21.1pp** |

NQ's BR-1 is 89%. It transfers slightly stronger, on both sides, in both eras, and the
edge over control *grows* across the sample. This is the one unambiguous positive of the
whole stream, and it is a base rate, not an edge.

**The session split in that doc is a clock artifact and the correction matters.** Raw
touch rates read asia 99.95% / london 99.14% / ny 80.42%, which looks like "gold reverts
in Asia and trends in NY." It does neither — sessions start 18:00 NY so an Asia
displacement has ~20 hours left and an NY one has ~4. Inside a fixed horizon the windows
converge (60 min: 37.9 / 34.5 / 39.9). Always ask "how much session was left?" before
believing a session table.

### QUALIFIED — `vah · break` on gold
`docs/FINDINGS-gold-level-census.md` and `docs/DECLARATIONS-gold-vah-break.md`.
71,328 first-of-fight rows over 932 session-days.

- **+0.111R** [+0.064, +0.158] at the gate-selected 0.2-point floor, H1 +0.092 / H2 +0.131.
  The only cell of fourteen clearing both eras.
- **Quote +0.111, not +0.148.** The +0.148 figure is the 0.5-point risk floor. Both are in
  the docs; the honest headline is the gate-selected one.
- **The locus does not transfer, the census does.** NQ's break-arm winners were vwap_m1
  (+0.248) and val (+0.234) with vah near the bottom (+0.068). On gold vah wins and
  vwap_m1 is mid-pack. Porting NQ's *answer* would have picked the wrong level; porting
  NQ's *method* found the right one.
- **It is NOT metal-specific.** The pre-registered control test (D8) came back: pre-cost EV
  is GC +0.149 / DX +0.144 / 6J +0.122, and `vah · break` is top-ranked on all three. The
  controls only look negative because a two-tick cost assumption eats twice as much of
  their R. This is a generic level-break effect whose viability is decided by **tick
  geometry**, not by gold.
- **Caveat on the controls:** GC↔DX correlates −0.41 and GC↔6J +0.31, so they are not
  independent controls. The user challenged this and the challenge was fair.

### NEGATIVE, and clean — tomtrades CBR loser autopsy
`docs/FINDINGS-tomtrades-autopsy.md`. 2,411 trades over 920 NY days.

**Winners and losers are separable and the separation is worthless.** A model reaches
out-of-sample AUC **0.712** against a 0.495 null — and **0.507** once reward:risk is held
fixed. Everything it knows is one thing: how far away the target is. Sorting by
out-of-sample EV and taking the best fifth returns **+0.004R (p = 0.87)**.

Book: 67.86% win rate, mean win +0.4395R, every loss exactly −1R, **expectancy −0.0232R**,
−56.0R total. Break-even needs 69.47%. Median reward:risk at entry is **0.40** and
**82.7% of trades risk more than they can make**.

The strategy does not lose because it picks bad trades. It loses because of where it puts
the target, and no entry-time filter reaches that.

**The 89.86% win-rate cell loses money** — it is the lowest reward:risk quintile (RR 0.08),
EV −0.0345. That is the cleanest dual-currency inversion in the repo; use it as the
teaching example.

### NEGATIVE — fixed dollar targets on the CBR book
Addendum to the same doc, `scripts/tomtrades_dollar_targets.py`, GC at $100/pt.

At zero cost: his impulse-50% rule is **+$4.46/trade, +$10,757 total** and is the *only*
one of six positive in dollars. $50 → −$3.37, $100 → −$3.23, $200 → −$4.56, $300 → −$3.14,
$500 → −$1.32.

Two things to carry forward:
- **$100 fixed loses at the same win rate his rule wins at** (68.03% vs 67.86%). A fixed
  target does not scale with the stop, so on wide-risk trades you win $100 and lose $500.
- **Sign disagreement.** His rule is best in dollars and among the worst in R (−0.023 vs
  −0.004 for $50). Its dollar profit is earned by loading risk, not by edge — fixed-contract
  sizing rewards it, fixed-risk sizing does not. BR-10's convention hazard, live.
- One tick round turn ($10) buries all six. His rule goes +$10,757 → −$13,352.

### REFUTED — DodgysDD's "data high/low" claim
`docs/FINDINGS-dodgy-data-wick.md`. He claims ~99% same-day return on abnormal-wick news
highs/lows. Measured on NQ with a control, **it fails backwards**: news wicks return
**8–11pp LESS often** than ordinary abnormal wicks at every threshold rung
(2×: 83.5% vs 93.3%; 8×: 75.7% vs 83.6%).

### NEGATIVE — DodgysDD iFVG trigger
`docs/FINDINGS-dodgy-ifvg.md`, read the **CORRECTION section at the bottom** — the top of
that file ran on a mis-specified detector.

Corrected: **−0.135R** after cost [−0.145, −0.125], **−0.020R** before. The liquidity sweep
he states as required subtracts. The breakeven rule — 1,958 mentions across 472
transcripts, more than "fair value gap" itself — moves EV by under 0.01R. His "obviousness"
filter does nothing across the whole ladder. The NY session restriction makes it worse
*before* cost.

## 5. What was WITHDRAWN — do not re-cite these

A fresh session reading the docs top-to-bottom will hit these numbers before hitting their
retractions.

| withdrawn claim | correct value | why |
|---|---|---|
| "+0.099R from stacking context" on the iFVG | **~+0.035R** | detector bugs 1 & 2 |
| "trading toward the 15m MA helps" (+0.020) | **−0.008 — it hurts** | same |
| `vah · break` = +0.148R | **+0.111R** | +0.148 was the 0.5 floor, not the gate-selected 0.2 |
| gold reverts in Asia, trends in NY | **no session difference** | time-remaining confound |
| permutation calibration on cell means | **no power, invalid** | shuffling within cells preserves cell means; it returned `null = real ± 0.0000` |
| iFVG "207 signals/day" | 87.7/day | double-counted one move across stale gaps |

**The permutation one is a live hazard.** `autopsy.permute` shuffles outcomes *within*
(session, mech) cells. That is fine for testing a *contrast between* cells and useless for
testing whether a cell's mean differs from zero. If it ever returns a null identical to the
real value, that is a test with no power, not a result.

## 6. THE BLOCKER — the gold data is not in git

This is the first thing to check and the reason a fresh clone cannot reproduce anything
above.

| file | ~size | state |
|---|---|---|
| `data/gc_1m.parquet` | 20 MB | **gitignored — container-local only** |
| `data/dx_1m.parquet` | 14 MB | **gitignored — container-local only** |
| `data/6j_1m.parquet` | 17 MB | **gitignored — container-local only** |
| `data/transcripts/dodgysdd/` | 473 JSON | gitignored, but **re-fetchable** |
| `data/reference/nq_1m_master.parquet` | 22 MB | tracked — safe |

`.gitignore` line 8 excludes `data/*.parquet`; `data/reference/` is deliberately committed
as ground truth. **The three gold-track parquets exist only in this session's ephemeral
container and are destroyed when it is reclaimed.**

Contents, so they can be identified if re-sourced: 1m OHLCV + `symbol` + `roll`, continuous
front month, GC 1,276,717 bars 2023-01-02 → 2026-08-11, DX 970,929 bars → 2026-07-24,
6J 1,256,667 bars → 2026-08-11.

**No committed script produces them** and no doc records their provenance — that is a real
gap in this stream's reproducibility, and it is mine. The user has declined to pay for
Databento ("I am not paying $130"), so re-sourcing needs a free route.
`scripts/ingest_dukascopy.py` and `scripts/fetch_gold_ticks.py` are the free path that was
being built for XAUUSD; that download died at 1,000 of 1,623 hours and was never finished.

**Options for the new session, in order:**
1. If the user still has the container alive, force-add the three parquets
   (`git add -f`) — ~51 MB, against the repo's stated convention, so it is the user's call.
2. Re-source GC 1m from wherever these came from.
3. Finish the Dukascopy XAUUSD ingest and re-run on spot gold — note spot has no real
   volume, which breaks VAH/POC/VAL (already recorded as an amendment in
   `docs/DECLARATIONS-gold-vah-break.md`).

Until one of those lands, **every gold number above is unreproducible** and the only
runnable track is NQ, which is Angus's lane.

## 7. Environment facts that cost me time

- **No sklearn, no scipy.** `src/research/tomtrades/autopsy.py` hand-rolls logistic
  regression (IRLS), Spearman and AUC. Use them; do not try to install.
- **Background processes get reaped** when no tool call is active. The level census takes
  ~6 minutes and *must* run in the foreground. A "crash at day ~500" was reaping, not a bug.
- **Never `pkill`/`kill` by name** — it killed my own shell twice (exit 144). Get the PID
  via `ps ... awk`, then kill the number.
- **YouTube captions: use yt-dlp, never `youtube-transcript-api`.** The API hits the
  timedtext endpoint which hard-blocks datacenter IPs — it died at 42 videos with
  `IpBlocked` and slower pacing did not help because it is a cooldown, not a rate window.
  yt-dlp goes through the player response and was never blocked: 472/474 videos in four
  passes. `scripts/fetch_channel_transcripts.py` carries this warning in its docstring —
  do not "simplify" it back to the API.
- **YouTube auto-caption VTT is rolling** — each cue repeats the previous line. 2,659 cues
  de-rolled to 1,330 distinct lines. `parse_vtt` in that script handles it.
- **Dukascopy:** free tick data is hourly `.bi5`, LZMA-alone, 20-byte records `>IIIff`, and
  **the month in the URL is zero-indexed**. It throttles on *rate*, not volume, and 429s
  are indistinguishable from closed-market hours unless you check explicitly — my first
  ingest reported "52 empty hours" that were 27 HTTP 429s.
- **`profile_at_minutes(bin_width=...)` is scale-dependent.** The 1.0 default produced zero
  profile fights on 6J and a 4× shortfall on DX, so the first control pass never tested the
  candidate at all. `scripts/gold_level_census.py` rebinds it to `4.0 * tick`.
- **Merge on `sid`, with `validate="one_to_one"`.** `simulate()` drops rows
  non-contiguously, so positional slicing silently pairs each trade with a different
  signal's context.
- **Delete stale parquets after a smoke test.** I quoted n=31 figures from an
  `output/tomtrades_autopsy_trades.parquet` I had overwritten with a 60k-bar smoke run.

## 8. Where the code is

| path | what |
|---|---|
| `src/research/tomtrades/autopsy.py` | the analysis toolkit — `dboot_mean`, `permute`, `oos_auc_within`, `day_folds`, `top_bin_ev`, `bucket_table`, `split_half`, `cost_ladder`. Reused by everything downstream. |
| `src/research/tomtrades/detector.py` | CBR detector + shape annotations + `be_trigger_r` |
| `src/research/gold/htf_census.py` | BR-1 on gold |
| `scripts/gold_level_census.py` | level-family census, parameterised by instrument |
| `scripts/dodgy_ifvg_test.py` | iFVG trigger — **contains both bug fixes**, read the `signals()` docstring |
| `scripts/dodgy_ifvg_context.py` | cross-strategy filter test |
| `scripts/tomtrades_dollar_targets.py` | fixed-dollar-target test |
| `scripts/fetch_channel_transcripts.py` | yt-dlp transcript fetcher |
| `scripts/mine_rules.py` | scans a transcript corpus for TERM + modal MARKER sentences with video id and timestamp |
| `.claude/skills/tomtrades-model/SKILL.md` | quote-grounded reconstruction of the CBR method. **Unvalidated hypothesis catalogue, not a measured edge.** |

## 9. Open queue, ranked

1. **Measure GC's actual round-turn cost.** This is worth more than any further census.
   `vah · break` at +0.111R is carrying an *assumed* 0.20-point round turn against a
   +0.149R pre-cost book — the entire edge is the gap between two numbers, one of which
   was never measured. If the true round turn is 0.10 the candidate roughly doubles; if it
   is 0.30 the candidate is gone.
2. **Room-to-run on gold** (BR-32/35). Untested there, and it was the largest non-flow gate
   on NQ. Needs all loci at each minute — a second pass. Note it *reversed sign* on the
   iFVG trigger, so it does not port for free.
3. **Re-mine the DodgysDD corpus.** 472 transcripts fetched, only ~42 extracted. The term
   census already showed the 42-video sample misled me about what he actually teaches.
4. **Seal a holdout on gold and re-run `vah · break`.** Everything so far is fit-side on the
   whole sample; 14 cells tested, 1 survivor, which is about what a generous multiplicity
   budget permits.
5. **XAUUSD Dukascopy replication** — download died at 1,000/1,623 hours.

Explicitly dropped by the user: **SMT** ("who cares about SMT it doesn't actually work"),
1,183 mentions in the corpus and still untested. Do not re-propose it unless asked.

Never finished for an unrelated reason: the `.claude/settings.json` plugin declaration,
blocked by the permission classifier.

## 10. Tone note

The user wants numbers first and hedging last, and will say so bluntly if you bury the
answer. When they ask "how long", give a figure in the first sentence. When a result is
bad, lead with that. Several of the corrections in §5 exist because they pushed back on
something that looked too good, and they were right each time.
