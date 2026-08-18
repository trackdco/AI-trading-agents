# PROPOSAL — the j49 fixes (drafted, NOT applied)

**Status: nothing in this document is in any contract.** Per the standing
rule, contract edits wait for his verdict pass on the trade sheet. Section
A is plumbing — it encodes no trading opinion and is ready to land the
moment he says go. Section B encodes trading judgement and is written as
five questions with draft language, because the calibration source for
those answers is him, not us.

**His framing, which this document accepts as the spec:** *"I could
guarantee you I could get on this chart, and I would be fucking profitable…
there is a problem in which we've calibrated the agents."* Correct — with
one sharpening the book insists on: the agents executed his STATED rules
faithfully (T40 is his sentence, run twice, escalation included). The gap
j49 measured is between what he says and what he does. The fix is to
extract the unstated parts — at the exact decision points where the two
diverged — and write them down. That is the same teaching loop that built
the w49 doctrine, pointed at five new days.

---

## The defect ledger j49 proved

| # | defect | cost on this tape |
|---|--------|-------------------|
| D1 | T40-as-absolute + escalation that reaffirms by restating the gate (Mon). Precedent: w49 Monday 06-22, stand-aside thesis, good 03:42 short passed — **he called it wrong then**. Second occurrence. | −6.88R delta |
| D2 | Thesis bias anchoring: v1→v2→v3 short with the same zone numbers through an up-grind (Tue); jn1's stack was long by 09:46 | bulk of −3.75R |
| D3 | Condition semantics: A5@10:34 read "last complete 15m ~30557 → unmet"; A6@10:45 read "3/4 of last 4 above → met". Same test, opposite readings | part of D2 |
| D4 | Frozen numbers: thesis wrote 30580–586; live VAH 30616; triggers flagged it twice, no lane to act | part of D2 |
| D5 | Range-entry stop geometry: 03:22 short, j49 30pt stop died at 30523; jn1 49pt stop survived the same push, +1.78R | −2.78R swing |
| D6 | tv-manage trail-before-TP1 ambiguity: three managers did, one refused as illegal | ±, unmeasured |

## §A — mechanical fixes, ready to land (no trading opinion encoded)

**A1. LEVEL-TRUTH GUARD** (runbook). After every thesis emit, the
orchestrator diffs each level PRICE the thesis names against the live
briefing's levels. Any named level off by more than tol (8pt flat, or
0.25× current 15m ATR, whichever is larger) → one bounce-back: *"restate
with current levels."* One retry, then proceed with the restated thesis.
Mechanical fact-check under §0c — the orchestrator checks arithmetic, it
does not judge the thesis.

**A2. CONDITION GRAMMAR** (tv-thesis). Every licence / relicense /
invalidation condition must be written as EVENT + PERSISTENCE + REFERENCE:

- EVENT — "a 15m close beyond L", "a 2m/3m decisive close through L"
- PERSISTENCE — "**latches** for the rest of the window" OR
  "**instantaneous** (most recent close governs)": one of the two, stated
- REFERENCE — a **named level**, evaluated at its CURRENT price from the
  trigger's own briefing; never a frozen number

Trigger-side default: a condition missing its persistence clause is read
as **latched** — a decisive close changes the state until a decisive
opposite close, which is how he trades closes. (D3, D4.)

**A3. ESCALATION REFORM** (tv-thesis + runbook).
- (i) An escalation response may not reaffirm SOLELY by restating a
  calendar/default gate (T40 or any other). It must engage the escalated
  structure on merits. A reaffirm that only re-cites the gate is invalid
  and the orchestrator re-spawns the escalation once. (D1.)
- (ii) MANDATORY ESCALATION COUNTER (runbook, mechanical): the **second**
  same-direction pass in a window whose stated ground rests on thesis
  licence forces a thesis re-read — the orchestrator counts pass rows, it
  does not read charts. On 06-01 this fires at 08:42, before either losing
  short was taken. (D2.)

**A4. FRESH-EYES WINDOW OPEN** (runbook order change). At each window open
the thesis agent first commits bias + levels from the chart and briefing
alone; the prior thesis is then provided in a reconcile step which may
only (a) keep it, or (b) change with a stated reason. Week-horizon
continuity survives in the reconcile; the v1→v2→v3 anchor chain does not.
(D2.)

**A5. CERTIFIER + CONVENTIONS** (harness, no contract). Teach
`certify_offline_briefings.py` the fast-path serving conventions (partial
current candle; call-anchored windows) so the current era certifies exact
again; the Mac session freezes serving conventions from here.

## §B — his calls (the sheet pass supplies these)

**B1 — Monday 03:12.** No gap, 43pt overnight coil, it broke and ran. Take
or skip? If TAKE: T40 gains its exception, in his words — draft to react
to, not to adopt: *"Monday London without a significant gap defaults
stand-aside, EXCEPT a coiled overnight range in the bottom decile of
normal 3h width that breaks with a decisive close is tradeable in the
break direction, structural target."* If SKIP: T40 stands, and the honest
baseline for this tape is +1.12R — the recalibration weight then shifts to
Tuesday.

**B2 — Tuesday morning, 08:00→10:45.** Narrate it: where does HE flip, and
on what? (jn1 flipped by 09:46; the thesis's bar printed 10:00.) His
narration writes the relicense-placement rule; nothing is drafted here on
purpose — this one is pure extraction.

**B3 — the 03:22 stop.** 30pt or 49pt? Draft rule if 49: *"an entry taken
inside a marked/tight range carries its stop beyond the RANGE EXTREME plus
buffer, or passes on R grounds; only a break entry may stop behind the
break structure."*

**B4 — NY_PRE.** The standing ruling (cut PRE, effective after j49) takes
effect now — but the j49 book adds **+2.32R of PRE fills** (05-31 P2
+0.19, 06-03 P2 +0.09, 06-04 P3 +2.04), the week's second-best trade among
them, on a book that lost −4.16R everywhere else. Confirm the cut or
reverse it; one line either way, and `docs/RULING-cut-ny-pre.md` records
it.

**B5 — Tiers.** His standing verdict (uniform grade, uniform 50/50
partial) was waiting on j49. j49 adds the `take_light` at conviction A row
(grade/size disagreement surviving 0.4.5) and nothing that rescues
tiering. Implement with this batch unless the sheet read changes his mind.

## Process once §B lands

1. One contract batch: §A + the §B rules (trigger 0.4.11, thesis 0.4.3,
   manage 0.3.3, runbook). No drip-feeding — one version, attributable.
2. **Regression: re-run w49** under the batch. The fit week must not
   degrade; if it does, the batch is wrong, not the week.
3. **Re-run j49** under the batch. Passes when: 03:12 is taken (or skipped
   with his blessing per B1), Tuesday flips near his narrated point, 03:22
   survives if 49pt is his answer.
4. **Fresh out-of-fit week** — a never-touched week (June wk2 or July).
   j49 is teaching data now; it can never be the test again.
5. Then the path he already set: paper days (with HALT wiring done first),
   Tradovate sync, the zero-discretion execution agent.
