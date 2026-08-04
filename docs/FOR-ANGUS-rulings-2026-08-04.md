# FOR ANGUS — rulings owed this week (staged 2026-08-04)

**Status: DECISION MEMO.** The five rulings your brief (§5) says you owe, staged one
per section, each ending with a blank `RULING:` line. Every number is sourced; nothing
here self-authorizes. `[OPEN — needs Angus/Pat]` marks facts no repo file settles.

Drafted on `claude/canon-rebuild-deployment-7m48yv`, off the live arming branch — this
file must never land on the arming branch casually (a docs commit makes the next arm
refuse on provenance, live HANDOFF §4). `docs/REPORT-correlation-2026-08-04.md`
already cites this memo's §1 as the blocker it is waiting on.

---

## 1. ACCOUNT ARCHITECTURE — same funded account or separate (the big one)

**The question.** When a promoted strategy (Brake's first London survivor) goes live,
does it trade on the same funded account as the NY canon, or its own?

**What "same account" means mechanically.** One shared DLL: the budget accumulator is
`realized losses + in-flight risk + new risk ≤ base × 16/3` = **$853.33/day at $160**
(`scripts/funded_book.py` docstring), and one $2k EOD-trailing line. The correlation
thresholds proposed in `docs/REPORT-correlation-2026-08-04.md` (max |ρ| 0.30, tail
≤ 0.25, min 60 common days, combined P(bust) ≤ 1.0%, ≥3-shared-families veto — all
[PROPOSED — Angus to ratify]) become **load-bearing co-ship law**. Note the veto trips
today: NY↔London share **3 of 7** input families (depth walls, overnight structure,
order flow — battery, verified at source in `src/canon/scorer_ny.py` /
`scripts/london_canon.py`), so same-account co-shipping starts with a waiver decision.

**What "separate accounts" means.** Correlation softens from a shipping veto to a
portfolio monitor (firm concentration, marginal contribution). Each strategy gets its
own $2k trailing buffer and its own payout clock. The correlation infrastructure's job
changes from "may these two share a DLL" to "is the portfolio diversified and where is
it concentrated" — the brief's own framing: this ruling changes what that
infrastructure is *for*.

**The measured facts** (`docs/REPORT-correlation-2026-08-04.md`, seed 7, repo state
`2157069`; common span 2025-06-02..2026-07-08, NY active 230 days / London 109 /
both-active 99):

| | |
|---|---|
| Day-level Pearson, union n=240 | −0.094 [95% CI −0.185..+0.003]; both-active −0.110 |
| Tail co-crash P(LDN worst decile \| NY worst decile) | 0.10 — exactly the independence floor |
| Tail-conditioned Pearson (either worst decile, n=19) | −0.451 — *hedging*, direction only at that n |
| Simultaneous open-risk minutes | **0** across all 240 days (measured, not structural — London has no session flatten; 2/136 taken trades exited 09:00/09:30 ET) |
| Combined ruin, paired vs shuffled P(bust) | 0.5% vs 0.4% — dependence costs ≈ nothing |
| NY alone → combined (native sizing) | median net/yr +$86,165 → +$123,458 (+43%); p95 maxDD $1,954 → **$2,697** |
| London alone at native research sizing | P(bust) **6.9%**, median worst day −$1,292 vs an $853 budget — NOT shippable as-is |

On returns the books are indistinguishable from independent, mildly hedging in the
tail. On inputs they are cousins. The report's own caveat: 13 months is one regime —
the structural-cousin risk (shared families re-correlating when the regime ends) is
untestable on this span, which is exactly why the input-family veto stays load-bearing
either way.

**The funded-eval math that decides it** (all from `scripts/funded_book.py` docstring
MC block + `scripts/mc_funded_lab.py` defaults + `docs/CANON-QA-LOG.md` entry 42):

- Extraction per account is **clock-capped, not P&L-capped**. Payout = $2,000 when
  balance ≥ $54k AND ≥5 winning days (≥$150) since the last payout ("54k for a full
  2k payout because you can only withdraw 50%" — your words, QA-LOG 42). The NY agent
  book already runs **median 53 payouts (~$106k withdrawn) per 252-day year** — one
  payout per ~4.8 trading days (derived: 252/53), i.e. the 5-win-day clock is nearly
  saturated by NY alone. Adding London to the *same* account adds net but can barely
  add payouts (London's marginal contribution to the clock: it is active on only 10
  union days where NY was flat — 240 vs 230). A **second account adds a second
  clock**: extraction scales with account count, not with net-per-account.
- A new account is cheap: eval (+$3k target) passes **100.0% of sims in median 8
  days** at base $160 (funded_book docstring MC), and the recovered PROMOTION-GATE §0
  (git `d420b10~1`) prices an eval attempt at ~$100 — "the eval IS the test."
- Same-account co-shipping is *unmeasured where it matters*: every favourable combined
  number above was computed at separately-capitalized sizing. "Under one shared
  $853.33 budget the answer must be re-run; that is the data contract's first job"
  (report; the data contract is `docs/CONTRACT-strategy-emission.md`). And the shared
  budget contends even at zero correlation: budget counts *realized* losses, and
  London's fills (measured 03:01–05:50 ET — min/max fill of the 136 taken trades,
  `output/london_canon_book.parquet`, 2026-08-04; supersedes the 03:02–05:54 ET range
  quoted in the HANDOFF/brief/correlation report) are realized hours
  before NY's first order at 08:00 — a red London morning pre-spends the budget the
  NY book was sized to use alone.
- Combined p95 maxDD $2,697 sits **above** the $2,000 trailing line at native sizing;
  P(bust) 0.5% already prices that, but only in the ungoverned framing.

**Honest case for same-account:** one eval fee, one ops stack (each live arm needs its
own authorization and a fresh phrase — live HANDOFF §8.4), and the measured negative
correlation means the combined book on one line is smoother than the sum suggests.
If firm or capital constraints cap account count, same-account is how London's +43%
median net gets banked at all.

**Honest case for separate:** the payout clock (the binding constraint on money out)
multiplies only with accounts; the marginal account costs ~$100 + 8 median eval days;
the tripped 3/7 input-family veto and the one-regime caveat stay uninsured on a shared
line; and no shared-budget accounting exists yet — ruling "same" today means shipping
Brake's survivor into an unmeasured contention channel or waiting on the re-run.

**RECOMMENDATION: separate accounts** — promoted strategies get their own account by
default; same-account co-shipping becomes the *exception*, available only after (a)
the shared-budget MC is run under one DLL (the data contract's first job) and (b) you
explicitly waive the input-family veto for that pair. This keeps the correlation
battery load-bearing where it is strongest (the structural veto + portfolio
contribution) without betting the live line on its weakest span (one regime). It also
maximizes the §5 denominator, which is the roadmap's actual unit of account.

**Deadline: before Brake's first survivor arrives** (brief §5) — the battery's
shared-budget re-run, the data contract's funded-profile London book, and the
promotion criterion in `docs/VALIDATION-PROCESS.md` §6 rung 3 are all parked on this
line.

**RULING:** ____________________________________________

---

## 2. THE 5-DAY LOOP — bugs now, optimisation later

"Based off results fix + optimize, next 5 trading days repeat" is two different
actions sharing a line (brief §5). The split is already encoded, awaiting only your
signature: **`docs/VALIDATION-PROCESS.md` §9 — "Live-period change control — the
5-day-loop law [NEW — brief §5, ratified with this doc]":**

- **Bugs ship now** — via the deliberate re-cert flow (Pat certifies the new SHA, the
  authorization is re-issued, the two-party step re-runs; the live example is the
  standing R16 re-authorization in live HANDOFF §0). Never a casual commit to the
  arming branch.
- **Optimisations NEVER ship off live results.** Five live days is noise —
  VALIDATION-PROCESS §2.2 makes that quantitative (≥30 trades per era cell before a
  direction claim, [PROPOSED]) — and every mid-flight change resets the
  live-vs-backtest parity record. Candidates are logged (vault, status: proposed),
  validated offline through the full ladder (§1→§6), shipped as a versioned release
  with a new certified SHA.
- The existing stop-and-review discipline stands beside it (any canon/sizer/spine/
  relay change, any D1-class event, 2 consecutive halt days → stop and review).

Nothing new to decide beyond ratifying §9 as written (it ratifies with the
VALIDATION-PROCESS doc; a RULING here directs that signature).

**RULING:** ____________________________________________

---

## 3. WHO OWNS THE LIVE ACCOUNT DAILY

**The division that already exists:** Pat operates the box and monitors system health
— he doesn't trade (brief §5). The daily instruments are already defined: `turns` per
trade (all zeros = agents mute) and `agent_R` vs `v8_R` per managed trade (live
HANDOFF §8.7; the shadow V8 runs on every trade, §2). A live-vs-backtest divergence is
a **trading judgement** and routes to you or Brake — the brief leaves *which of you is
the default* to you. Propose: name one primary owner and a deputization rule, so a
divergence at 09:35 has a phone number.

**The payout runbook — three [OPEN] questions, with the inputs you need:**

1. **Trailing-DD math vs the withdrawal threshold.** [OPEN — needs Angus]
   Inputs: $2k EOD-trailing line, locks at $50k; payout at $54k / $2,000 / 5 win days
   ≥$150 (QA-LOG 42; `mc_funded_lab.py` defaults). Taking every payout on trigger
   resets the buffer over the locked line to **$2,000** — and the de-risk ramp (half
   size below $1,000 buffer, half again below $500, ARMING-REFERENCE row H) was
   measured **dormant** only on paths with no withdrawals (min buffer $1,642 fit /
   $1,698 holdout). From a post-payout $2,000 buffer, a holdout-class maxDD ($1,548
   mechanical; $878 agent fit) lands at $452 → quarter size (derived from the cited
   figures). The question: pay out on trigger and accept ramp activations, or bank a
   margin above $54k first — and if so, how much?
2. **The balance where elite-tier risk stops.** [OPEN — needs Angus]
   No repo file sets one; the ramp is tier-blind. Inputs: elite = 2.0× base = $320
   risk at $160, max 1/day, ~2/week, Wilson floor 64% (funded_book docstring;
   QA-LOG 37–38). The question: is there a buffer level below which the 2.0x slot is
   refused (e.g. inside ramp territory), or does the ramp's half-sizing already answer
   it?
3. **Who presses the button.** [OPEN — needs Angus/Pat]
   A withdrawal changes the account's risk state (buffer resets), so it is not pure
   box ops; but Pat holds the account console. Decide with it: the funded-account arm
   already needs its own authorization and a FRESH phrase when the eval passes (live
   HANDOFF §8.4) — payout authority belongs in that same two-party decision, before
   the P&L makes it emotional (brief §5).

**RULING (daily owner + the three runbook answers):** ____________________________________________

---

## 4. THE PARKED LONDON WALL-ARM CANDIDATE — confirm or overrule

**What it is, per the repo** (no repo file specs the candidate itself — BRAKE-BRIEF is
not in this repo; exact spec and park status [OPEN — needs Angus/Pat]): a
wall-mechanism London entry. London's wall checks — `W` (no wall behind, **+28/+19pp**)
and `FAR` (wall ahead > 4.5pt) — read the *identical* `dep_wall_*` columns as NY's
W/D/WALLSZ gates (`scripts/london_canon.py`; `src/canon/scorer_ny.py`; battery
FAMILIES table). Depth walls are the flagship of the 3/7 shared input families. The
old London book's own pre-registered holdout question list already includes "W/FAR
collapse (r=0.86)" (`scripts/london_canon.py`).

**Why Brake's brief parks it** (your brief §5): it is a cousin of the canon, and its
holdout look should not be spent.

**RECOMMENDATION: confirm the park.** Three grounds:
1. It maximally trips the input-family veto — a wall-arm London entry is the
   *definition* of the structural cousin the battery warns about, and the one-regime
   caveat means today's clean return correlation cannot retire that
   (`docs/REPORT-correlation-2026-08-04.md`).
2. Look economics: one look per family, never one per knob (`docs/VALIDATION-PROCESS.md`
   §4). Spending the cousin's look now — before your §1 ruling and before Brake's
   non-cousin candidates exist — buys the least information per look on the ledger.
3. Sequencing: if §1 rules separate accounts, the cousin penalty softens and the
   candidate can be re-costed then, having burnt nothing. A park is not a tombstone —
   vault status: proposed (not accepted to queued); holdout_plan: none; holdout look
   UNSPENT.

**RULING (confirm park / overrule):** ____________________________________________

---

## 5. ACCOUNT COUNT ARITHMETIC — the one-hour worksheet

The roadmap's denominator: **payout per account per month × accounts × firms.** The
numbers that exist, and the slots only you (or firm docs) can fill:

| Row | Value | Source / status |
|---|---|---|
| Payout per cycle (Lucid 50k shell) | $2,000 at $54k + 5 win days ≥$150 | QA-LOG 42; mc_funded_lab defaults |
| Payout frequency, NY agent book | median 53/yr ≈ 1 per 4.8 trading days — clock-bound | funded_book docstring MC; derived |
| **Payout per account per month** | **~$8.8k median** (~$106k/yr ÷ 12) | derived from funded_book docstring MC |
| P(bust) per account (agent book, $160) | 0.1% | funded_book docstring MC |
| Cost to stand up an account | ~$100 eval fee + median 8 eval days (100.0% pass in MC) | PROMOTION-GATE §0 (recovered, git `d420b10~1`); funded_book docstring |
| Withdrawal rule above $54k (does the $2k scale with balance? the MC models it fixed) | [OPEN — needs Angus: exact Lucid rule] | — |
| Accounts allowed per firm / per trader | [OPEN — needs Angus: firm rules] | — |
| Firms | Lucid (live eval `LFE050-9YSC047M-TEST001`); you have named "alpha futures or my funded futures pro accounts" | live HANDOFF §1; QA-LOG 47 |
| Payout/DD rules at non-Lucid firms | [OPEN — needs Angus: firm docs] | — |
| Ops ceiling: arms Pat can run (each = own authorization + fresh phrase + box load) | [OPEN — needs Pat] | live HANDOFF §8.4 |
| Concentration: max share of monthly extraction at one firm | [OPEN — needs Angus — "a conscious choice", brief §5] | — |

**The multiplication as it stands:** ~$8.8k/mo × N accounts, with N bounded by firm
rules and Pat's ops ceiling, spread across ≥2 firms once concentration is ruled.
Note what the clock-cap means: `scaled600` (+$272,847 fit) makes more *net* on one
account but cannot extract faster under a fixed $2k/5-win-day rule — unless the
[OPEN] withdrawal rule scales with balance, which is the single highest-leverage fact
missing from this table. This row-set is why §1 recommends separate accounts: the
denominator grows by account count, and accounts are cheap.

**RULING (target N, firm split, and the [OPEN] rows filled):** ____________________________________________

---

*Cross-references: `docs/REPORT-correlation-2026-08-04.md` (battery + proposed
thresholds), `docs/VALIDATION-PROCESS.md` (the process doc §2 ratifies),
`docs/CONTRACT-strategy-emission.md` (the data contract §1 leans on),
`docs/HANDOFF-london-rebuild.md` (Brake's method), live HANDOFF 2026-08-04, ANGUS
brief week of 2026-08-04. Stale-figure note: the London docstring's `day-corr +0.11`
is SUPERSEDED by the battery (−0.09/−0.11); quote the report.*
