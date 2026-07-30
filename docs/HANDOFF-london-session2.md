# HANDOFF — London canon, session 2 → session 3

**Written 2026-07-30 at the end of the second London session (weekly limit hit; account hop).**
Read this top to bottom before touching anything. The previous handoff
(`docs/HANDOFF-london-rebuild.md`) covers the original L0→L4 rebuild; this one covers everything
since. Assume the reader has NEITHER session's context.

---

## 0. State of the repo

- **Branch: `claude/london-canon-strategy-3p57jk`** — everything committed and pushed through
  `e0d851c`. Working tree clean. Develop and push on this branch (or whatever new designated
  branch the harness assigns — if so, cherry-pick nothing; re-cut from this branch's HEAD).
- **Environment:** system Python is 3.11 but the pins need ≥3.12. A `uv`-built **Python 3.13
  venv at `.venv/`** has exact pins. Run everything as `.venv/bin/python -m scripts.<name>`.
  No scipy — where Spearman is needed, compute Pearson-on-ranks.
- **Data:** all fit-side artifacts are in `output/` (parquet). The sealed holdout span is
  2023/24 (`data/reference/holdout_2023_24_days.csv`, 128 days) plus
  `data/reference/depth_london_2023_24/`. **The sealed span has never been read for outcomes**
  — only its trigger census / feature matrix were built (L0–L3 with `--span holdout`). Keep it
  that way until the sign-offs in §5.

## 1. The frozen strategy (do not move any of this)

Canonical source: **`docs/LONDON-PREREGISTRATION.md` (rev 2a)** §1. Summary:

- Window **08:00–10:00 Europe/London**, DST-resolved per day (03:00–05:00 ET normally,
  04:00–06:00 ET on ~20 misaligned days/yr).
- Arm **`wall` = (W OR FAR)**, score ≥ 1 (binary). W/FAR are one signal (r=0.834).
- **Uncapped** per session + **$400 day stop**; order lives to **window end** (no distance
  cancel — ANGUS ruling); risk floor **9.5pt, no ceiling**; engine E3/V8 with
  **`v8_be_at_open=False`** (flag added to `src/backtest/engine.py`, default True for NY).
- Sizing **flat 1 NQ lot** — ANGUS: *"no sizing until the validated volume is visible."*
- Fit book (the anchor): **187 trades / 107 days, +$22,795, 57% WR, mean R +0.513**.
  Declared forward expectation **mean R ≈ +0.48**.

**Rejected, never relitigate on fit evidence:** old4 arm (ROOM is null, ASIA backwards),
**risk floor 5** (era crossing; see §3.4 below for WHY it crosses), 22pt distance cancel.

## 2. Verified sanity anchors (re-verify before trusting any downstream number)

- `python -m scripts.funded_book --profile lucid` on the post-`d420b10` datasets reproduces
  **NY lucid fit: 920 trades / 230 days / +$90,015 / worst −$762 / maxDD $1,603 / 13 green**.
  `scripts/london_combined_job.py --stage preflight` asserts exactly this and hard-fails
  otherwise. **Never** use a book that doesn't pass preflight — the deleted pre-rebuild book
  burned us once.
- NY-alone P(bust) under the corrected payout model must land **0.5–4%** (comes out ≈2.4%).
  The payout model is: 5 trading days of +$100 since last payout (ANGUS rule), withdraw down to
  a **$4k retained buffer** (lucid optimum, `docs/PAYOUT-BUFFER-SWEEP.md`). The old
  every-touch-$54k model inflates bust to 11.8% and is WRONG.
- Baseline for any combined replay = **NY replayed under the same $800 budget rule with an
  empty London book** (+$90,249), NOT the raw book sum (+$90,015). The $234 gap is the budget
  rule's own effect; crediting it to London is an error we made once and fixed.

## 3. What session 2 did (chronological, each with its verdict doc)

All fit-only; every doc states its own guards. Scripts are all
`scripts/london_<name>.py`, runnable standalone.

1. **Tier test** (`docs/LONDON-TIER-TEST.md`). London's score is binary → no conviction ladder
   existed. Shape vs scale split. Shape: sizing both-W+FAR above exactly-one beats flat at
   matched risk, permutation p=0.0085 pooled, 14/14 jackknife, but per-era 0.117/0.021 →
   secondary, not primary. Scale: **1.5/0.5 ladder** is the pick (+$18,170 fit, still +$8,477
   at half-edge, +$1,516 at zero-edge where flat 1.0/1.5 go negative). Off-ladder tiers (>2.0)
   excluded — that'd be an NY-profile change, not a London decision. All prior London P&L was
   1-NQ-lot (~1.7–1.9× funded tier-1.0); "+$22,795" was never a funded number.
2. **Loss anatomy** (`docs/LONDON-LOSS-ANATOMY.md`). 81 losers, all stops. Duration: losses die
   fast (0–3min bucket 68% loss) — borderline only. Day character (volume/choppiness): **null**
   — the choppy-day hypothesis is not supported. The one Bonferroni-clearing signal:
   **entry-vs-VWAP dir-adjusted, AUC 0.628, p=0.003** — losers enter wrong side of VWAP
   (fading value), winners enter with it.
3. **VWAP filter** (`docs/LONDON-VWAP-FILTER.md`). Never-fade-VWAP **loses $5,856** — the
   dropped wrong-side trades are net +$9,094 (low WR, big snap-back winners). Loss RATE ≠
   negative expectancy. It's a risk trade only (maxDD $2,440→$935). Mild cut at −0.25 keeps
   ~all net; flagged as selection-mined, deferred.
4. **Fade conviction** (`docs/LONDON-FADE-CONVICTION.md`). Order-flow "strength at the
   extreme" inside the 73 deep fades: depth-lens direction is consistent with absorption,
   delta/CVD are not; composite **failed** its random-split guard. `wall_behind` excluded as
   structural circularity (W check = "no wall behind"). Hypothesis-generation only.
5. **Prereg trade-off** (`docs/LONDON-PREREG-TRADEOFF.md`). Power analysis: 128 days project
   to **~84 trades** (fit rate ×0.45), SE(mean R) ≈ ±0.171. Primary 78% power at k=2. **Frame
   every hypothesis as the decision it drives** — S1 framed as book-vs-book was 2% power;
   framed as one-sample expectancy on the incremental band it's 91%. S3/S4 are mutually
   exclusive and futile at this n.
6. **Prereg rev 2 + 2a** (`docs/LONDON-PREREGISTRATION.md`). Now: **2 gated tests** (primary +
   S1 sub-9.5-band expectancy, Šidák α=0.0253) + **S2 descriptive** (both-vs-one split,
   reporting item 10, NO inference, NO decision — if any decision is ever taken on S2 it
   retroactively becomes a 3-test family; written into §4). S3/S4 declined with reasons.
   **Rev 2a correction on record (§5):** an earlier draft called floor-5 "the biggest lever"
   off the band's POOLED mean R +0.590 — withdrawn; per-era it's +0.904 (2025) vs +0.211/39%WR
   (2026), the era crossing itself. S1 stays **"reported, not acted on"** per the standing
   ANGUS ruling.
7. **Era diagnosis** (`docs/LONDON-ERA-DIAGNOSIS.md`) — answers "why so shit in 2026":
   **2026 was the shipped book's BEST year** (+$14,618, mean R +0.570). Only the tight-stop
   band broke: median session range went 101→179pt (+78%) while the band's stop stayed 6.5pt,
   so it fell from 5.8% to 3.5% of range — a **units problem, not alpha decay**. A 9.5pt floor
   was 9.4% of range in 2025, 5.3% in 2026 (parity would need 16.9pt). Forward risk: the
   shipped book's stop/range is eroding too (8.07%→5.61%) — watch stop/range as a live health
   metric. Vol-scaled floor = NEW hypothesis, needs its own prereg, NOT this holdout.
8. **Late bucket** (`docs/LONDON-LATE-BUCKET.md`) — answers "what makes 09:30–10:00 bad":
   hit-rate problem (40% WR, winners still +1.64R). NOT window truncation (37% exit after
   10:00). Mechanisms: highest room-ahead (0.63 — the loss-anatomy loser signature) + lowest
   stop/range (5.45%) against the largest realized range. Cutting it: **−$994 net for −$1,115
   maxDD** (ROdd 9.3→16.5), but time-permutation guard (worst-of-4-buckets null) gives
   **p=0.076 → do NOT cut**. Instead: check the bucket profile on the holdout as descriptive
   output (costs no alpha).
9. **10:00–10:30 extension** — dead on arrival: **all 295 depth files end at 09:59 London**
   (verified), and the wall check is built from depth. Raw (unfiltered) 10:00+ loses money
   everywhere. Extending needs a new MBP-10 purchase — a data-spend decision for Angus, not
   analysis.

## 4. The meta-lesson of session 2 (tell the user this if they push for more fit-side work)

Three consecutive improvement ideas measured well on the surface and **failed their guards**:
VWAP filter (profit trap), depth-conviction composite (random-split guard), late-bucket cut
(worst-of-4 permutation). London's edge is concentrated in the wall check; marginal
refinements keep resolving to noise or drawdown-only trades. **The strategy as frozen is
probably finished. The remaining work is the holdout run, not more fit-side search.**

## 5. Open items, in order

1. **Brake re-confirms rev 2a draft sign-off** — the rev-1 signature predates §2/§3/§4/§5
   changes and does not carry forward (prereg §6).
2. **ANGUS sign-off** on §1 (frozen config), §3 (secondaries), §4 (multiplicity). The sealed
   set may NOT be opened on a draft signature.
3. **The single sealed holdout run** — once, frozen, 128 days, 1 NQ lot. Report §2's items
   1–10 + S1. Read at the declared resolution: **a near-miss on +0.48 is not decay; a sign
   flip is.** Optionally (needs authorisation, flagged in `docs/LONDON-ERA-DIAGNOSIS.md`):
   measure the sealed span's session ranges to contextualise the result — `on_range` is a
   market-condition feature, not an outcome, but it IS sealed-span data, so ask first.
4. **Post-holdout, if primary validates:** the sizing decision (the 1.5/0.5 ladder from the
   tier test is the declared candidate; S2's descriptive split is the pre-declared number it
   gets judged against). Also the NY profile decision (lucid vs scaled600) — a bigger dollar
   lever than all of London.
5. **Parked for forward data (do not re-open on fit evidence):** S3 mild VWAP filter, S4
   depth-gated fades, late-bucket cut, vol-scaled floor, 10:00+ window (needs data purchase).

## 6. Traps burned into this session (append to the original burn list)

1. **Pooled means hide era crossings.** The floor-5 band: +0.590 pooled = +0.904 (2025)
   averaged with +0.211 (2026). Always split by era before claiming anything.
2. **Loss rate ≠ expectancy.** Twice: VWAP filter, late bucket. High-loss-rate cells can be
   net positive via big winners. Price the cut, never assume it.
3. **Frame hypotheses as the decision they drive.** One-sample vs two-sample framing moved S1
   from 2% to 91% power on identical data.
4. **Descriptive ≠ inferential.** A reported number with no decision attached consumes no
   family-wise alpha — but that's binding both ways (see prereg §4).
5. **Baseline must share the mechanism.** Combined-replay deltas are vs NY-under-budget-rule,
   not raw NY. The zero-edge column exposing a constant +$234 offset was the tell.
6. **Coverage-gate before Bonferroni.** `wall_behind` at 2/73 non-null returned AUC 1.000 —
   degenerate, and structurally circular for London.
7. **Search breadth must be paid for.** Worst-of-k permutation nulls (late bucket), declared
   grids with stage-3-curve shrinkage (tier test), min-bucket statistics — every selection got
   charged. Keep doing this.
8. **`risk` in `lon_book()` output is DOLLARS** (points × 20). Divide by 20 for points.
   `itertuples` + non-identifier column names still bites (`risk_$` → `risk_usd`).
9. **Read artifact mtimes before quoting a "re-run".** A crashed rebuild once nearly reported
   stale parquet as "unchanged after fix".

## 7. Standing user instructions (verbatim, still in force)

- "Fit spans only. Holdout stays sealed — fail loudly if any code path touches a sealed span."
- "Write a verdict file per stage, commit and push between stages, assume this context won't
  survive."
- "If a stage fails, write a FAILED marker and continue to the independent stages; skip only
  its dependents. Never emit partial numbers as results."
- "Report every null as a null."
- "Floor stays 9.5 if it survives; the era crossing already rejects floor 5 and I'm not
  relitigating it."
- "Causally implementable priority rules only." (London fills 03:02–05:54 ET, NY starts 07:45.)
- Do not resample the two books independently in Monte Carlo — it destroys the correlation
  being measured.
- NY sanity anchors: +$90,015 / 920 / 230 / maxDD $1,603; NY-alone P(bust) near 1% (accept
  0.5–4%).

## 8. How to resume in one command

```bash
git fetch origin claude/london-canon-strategy-3p57jk && \
git checkout claude/london-canon-strategy-3p57jk && \
.venv/bin/python -m scripts.london_combined_job --stage preflight   # must print PREFLIGHT PASS
```

Then read `docs/LONDON-PREREGISTRATION.md` end to end. The immediate conversation state at
hop time: the user had just received the late-bucket verdict (don't cut; p=0.076) and the
recommendation that fit-side search is exhausted. **The next concrete action is §5.1–5.2:
getting the two sign-offs, then running the holdout.**
