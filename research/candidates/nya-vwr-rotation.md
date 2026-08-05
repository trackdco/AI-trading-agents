# NYA-VWR-01 — VWAP sd2 rotation fade, RTH (Orochi, as taught)

Prereg: `docs/PREREG-vwap-rotation.md` (+ amendments 1–4, all committed
before the corrected census produced a number). Card: `research/FUNNEL.md`.
Brief: `docs/BRIEF-vwap-rotation-chat.md`. Spec source:
`research/transcripts/orochi/RESPEC-as-taught-2026-08-05.md` SPEC 1 + SPEC 3.
Harness: `scripts/nya_vwr_census.py`. Ledger rows 241–255.

### Trial 1 — stage 1 uncapped raw census (2026-08-05)

Span FIT ONLY 2025-06-02 → 2026-07-15, 290 RTH sessions. No holdout look
spent. 15 arms, all ledgered.

**THE EVENT EXISTS — no census kill available (§5.9.1).** 2,168 distinct
sd2 reaches, 09:45–15:55, on 289 of 290 sessions (100%). 446 are the first
reach of a session on that side (1.54/session). The taught trigger fires;
K1 (structural absence) does not apply, so nothing dies here regardless of
what the P&L looks like.

**The gate does more work than taught.** RESPEC §8 expected strict gating
to remove "about half" of raw sd2 touches. G1 (default: 2 consecutive
closes beyond a ±1σ edge = acceptance) removes **89%** — 2,168 → 242. The
survivors run 0.83/session, inside his taught 0–2/day cadence, so the
cadence matches even though the attrition does not. G2 325, G3 626, G4 113,
G5 161.

**Raw P&L, default arm (E-a / S1cap20 / T1 mean / developing / G1):**
n=242, WR 27.7%, **−392 pts**, **+$4,397** at $160/R, PF 1.14, mean +0.114R.
Strict cost (2pt): +$927, PF 1.03. Halves: 25H1 +$280 (n=17) / 25H2 +$958
(n=104) / 26H1 +$4,378 (n=114) / 26H2 −$1,219 (n=7). Years: 2025 PF 1.08 /
2026 PF 1.21.

**That headline does not survive its own diagnostics. Three findings, any
one of which voids it as evidence of edge:**

1. **Causality (§2.5 — "or it doesn't count").** S1 sets the stop beyond
   the TRIGGER bar's extreme, which is not known when the limit fills
   intrabar; the trade survives that bar's adverse move for free. The
   strictly causal sibling **S1c** (stop beyond the PRIOR bar's extreme)
   returns **−$58, PF 1.00, mean −0.001R**. Essentially the entire apparent
   edge is the non-causal stop placement. "Looked great leaky, died honest."
2. **Fragility (§7.1-3, drop-top-3).** Total +27.5R; the top three trades
   are +26.0R. Remainder over the other 239 trades: **+1.5R = +$242.** The
   rr_floor-1.5 retraction precedent exactly.
3. **Risk skew.** Winners carry 10.8 pt average risk, losers 13.9 pt, which
   is why the arm is −392 points but +27.5R. At fixed-$ risk the dollar
   result is produced by the stop rule's sizing interaction, not by the
   entry.

**Every other arm is flat or negative.** Entries: E-b +$1,415 PF 1.10
(147 of 348 events filled — the close-back-inside requirement vetoes 58%);
E-c (his sweep-case literal, re-entry into ±1σ) **−$5,151 PF 0.77**; E-d
(the SPEC-3 retest + compound-add grammar, his most mechanical sequence)
**−$1,652 PF 0.86**, 175 of 240 reaching a retest. Stops: S1c −$58,
S2 +$756 PF 1.02, S3 −$2,349 PF 0.91, S4cap30 −$4,691 PF 0.78 — monotone
worse as the cap widens. Targets: T2 far edge +$3,853 PF 1.12, T1 frozen
+$5,916 PF 1.19 (both inherit the S1 causality problem). Gates: G2 +$3,413
PF 1.07, G3 −$7,553 PF 0.95, G4 −$69 PF 1.00, G5 +$2,558 PF 1.13. Warm-up
10 min +$1,093 PF 1.03. **No arm's t-stat exceeds 1.1** (max |t| = 1.76 on
S4cap30, negative).

**In-trade shape (§5.12-5, recorded from birth).** Mean R at t+2 +0.030,
t+3 +0.247, t+5 +0.438, t+8 −0.011, t+10 +0.057, t+15 +0.037, t+30 +0.480.
The trade is best around t+5 and gives it back by t+8 — the fade works
briefly and then decays, which is where an in-trade management search would
look. MFE median +1.15R, MAE median −1.00R.

**Fill-realism flag for stage 2.** Stops are modelled as filling at the
stop price, but price travels a median **0.79R beyond the stop inside the
stopping minute**. Any stage-2 economics should carry a stop-slippage
assumption rather than inherit this one.

**E-d note.** The two-tranche sizing (1/3 at the retest, 2/3 on the
acceptance-back-inside add) means its R is scaled by design; 65 of 240
events never produced a retest and were recorded `cancelled_no_retest`
rather than dropped.

### Status

**NO BIN, NO VERDICT — census stage only.** Per §5.9.1 the only legal kill
here is structural absence, and the event fires on essentially every
session. Per §5.9.2 raw ugliness cannot deny entry to the deep search. The
raw set is unprofitable once made causal, which is the *expected* starting
state (§3.1: the canon's own raw triggers were unprofitable).

**Owed before any verdict:** the complete variable search — order-flow
confirmations at entry (CVD/delta, absorption), depth where covered
(08:00–10:29 ET only, so the first hour of RTH), conviction-based sizing,
in-trade management against the t+5/t+8 decay, and the §3.2 loser autopsy.
An expectancy kill before that search is PREMATURE and gets vacated on
review.

**Recommendation to Angus: stage 2 is your call.** The honest read is that
this family enters the deep search with a weaker prior than the IVB fade
did — the causal raw set is flat, not merely ugly, and the overnight cousin
(NYO-ROT-01) already failed its corrected-grammar retest today. That is an
argument about *priority against the slate*, not a kill.
