# Overnight run — 2026-08-04

**Read this first.** Everything below is committed and pushed to
`claude/dsr-pbo-strategy-validation-mzp0wv`.

---

## Headline

**The sweep found nothing worth testing, so nothing was tested. No trials were spent, and
the ledger still stands at 34.**

23 hypotheses generated across five independent search angles, 9 taken to adversarial
screen: **8 REJECT, 1 WEAK, 0 PURSUE.** Under the rules declared before the sweep ran
(rule 8), a null sweep means the trial-ledger work instead — that is what I did.

**But the sweep paid for itself anyway, on a by-product: a look-ahead defect in the depth
data that reaches the NY canon.** That is the thing to read.

---

## 1. BLOCKING — depth snapshots carry ~59 seconds of look-ahead

Full detail: `docs/FINDING-depth-snapshot-lookahead.md`.
Reproduce: `python -m scripts.verify_depth_lookahead` (read-only).

The sweep raised it; **I verified it independently before reporting it.**

Every condensed depth snapshot is stamped with the **start** of the minute but holds the
book state from the **end** of it. `condense_depth.py` takes `tail(1)` — the last message of
the minute — and labels it with the floored minute. `depth_at` then correctly selects
`ts <= minute` and gets a book from up to 59 seconds in the future.

**`depth_at` is not the bug.** The data underneath it is mislabelled.

| dataset | \|mid − bar OPEN\| | \|mid − bar CLOSE\| | |
|---|---|---|---|
| London depth | 9.00 ticks | **1.00 tick** | end-of-minute |
| **NY canon depth** | 15.50 ticks | **1.00 tick** | **end-of-minute** |

London also still carries `ts_recv`: median **59.82s** into the labelled minute, **100%** of
rows more than 30s in.

**Scope, stated precisely: this is a backtest and calibration bias, not a live execution
bug.** A live feed has no future in it, and `src/live/` and `src/desk/` do not call
`depth_at` today. What it means is that every depth feature was *measured*, and every depth
threshold *calibrated*, on data with ~59s of foresight — so those features have less to work
with live than the backtest suggests.

**This strengthens the London nulls** (they were null *with* the bias helping them). **The
NY canon is the exposure** — its depth features were not null.

**I changed no code.** This touches `src/canon/`, and the rule I bound myself to was that
live and canon code are not modified unsupervised. It needs your decision.

---

## 2. Trial ledger built — and it corrects something I told you

`src/validation/trial_ledger.py` + `scripts/backfill_trial_ledger.py`. 34 trials backfilled
from the signed-off verdicts, **matching the declared running total exactly** — the prose
counting was right.

**I told you this would almost certainly make the bar harder. It made it easier.**

| | before (my 6-cell estimate) | now (recorded ledger) |
|---|---|---|
| trial-effect sd | 0.1054 | **0.0812** |
| luck bar @ 34 trials | +0.2239 | **+0.1724** |
| best observed | +0.1607 | +0.1607 |
| **shortfall** | −0.0632 | **−0.0117** |

Same verdict — the best result is still below what chance would produce. But it goes from
*comfortably* below to *marginally* below, and I had told you to expect the opposite. The
margin, not the conclusion, is what changed.

**Caveat on the record:** only **26 of 34** trials could be standardised. LDN-INV-01 reports
a regression coefficient in its own units, and LDN-SWP-01 published group means with no p or
se. Both are **counted** but excluded from the variance. If those 8 are more dispersed than
the 26, the true bar is higher than the one computed.

---

## 3. My own process breach — sealed-span hygiene

**I have to report this against myself.**

My workflow prompt gave the sweep agents the full data inventory but **never told them the
2023/24 span is a sealed holdout.** That was my omission in designing the workflow.

What I verified in the agent transcripts:
- The only direct sealed-path *load* was `holdout_2023_24_days.csv` — the guard list itself,
  which `fit_only()` also reads. **That is not a look.**
- The sweep's own memo self-reports that a scoping probe read 2023–24 minutes from the 1-min
  master for a calibration constant.

**Assessment: no statistical look was spent.** A holdout look requires measuring an outcome
and making a decision from it. No outcome was measured, no candidate advanced (0 PURSUE),
nothing entered the ledger, and no verdict depends on it. **The holdout's integrity is
intact.**

**But the guard failed**, and it failed because I did not declare it. Remediation:
1. Nothing from that probe may be reused. Any revival recalibrates on the fit span.
2. **Every future workflow prompt must state the sealed span explicitly.** The agents had no
   way to know.

---

## 4. Genuinely useful discovery — the holdout has depth and footprint

`data/reference/depth_london_2023_24/` holds **128 days** of identical-format London MBP-10,
and `footprint_holdout_*.parquet` covers exactly those months — a 128/128 intersection.

Three of the swept candidates asserted this data does not exist. It does. **Any future
book-based work has a genuine second era available** — when someone decides to spend the
holdout look, which has still never been spent.

---

## 5. What the sweep concluded (memo highlights)

- **No validated evidence base for "confluence"** as the education industry practises it.
  The arithmetic it did give is worth keeping: base signal + 8 conditioners, subsets of
  k ≤ 3, is **186 candidate rules**, and per Novy-Marx a "best 3 of 8" search prices like a
  ~500-way search. The rejected candidates would have added **72 trials** — more than
  doubling our denominator — for hypotheses whose primary statistics measure at zero.
- **The literature recommends things we have already disproved.** Three separate proposals
  were restatements of LDN-INV-01, which is tombstoned.
- **Claims with no evidential base, now measured on our own book:** "thin DOM means price
  travels" — the first ask gap is 1 tick in **94.9%** of snapshots, and P(large move | thin)
  is 0.187 vs **0.204** for thick, i.e. the gate carries *negative* information. Deep-book
  imbalance as "latent demand" — L2–10 holds 2–4 contracts at **1.06 contracts per order**,
  which is algorithmic 1-lots.
- **Honest limit:** most full texts were **unread** — arXiv, SSRN, NBER, OUP, ScienceDirect
  all returned 403 to the egress proxy. The sweep rests on titles, abstracts and search
  snippets, not papers. Treat its literature claims accordingly.

---

## What needs you

1. **Decide on the depth look-ahead.** It blocks any depth-gated deployment including the NY
   canon. Fix is cheap (re-stamp the condense, or take `head(1)`); the expensive part is
   re-deriving every `dep_*` feature and re-measuring what the canon claims from them.
2. **EU release calendar** — still the cheapest high-value unblock, and still needs your
   machine. The network policy here blocks ECB, Eurostat and Destatis outright (403 on
   CONNECT), not just Forex Factory.
3. **Ratify or reject** the four process amendments in `LONDON-PROGRAMME-CLOSEOUT.md`. The
   depth defect is now the strongest argument for the causality-audit-as-assertions one — a
   prose audit of `depth_at` would have **passed**.

Nothing was armed. Nothing was deployed. No holdout look was spent.
