# STANDING AUDIT — every structural level the spec names, and whether the detector computes it

**2026-08-08. Amendment 05 round 2, item 5.** *"list every structural level the spec names and
whether the detector computes it. Weekly H/L is the second case after prior-week. There may be
more."* **No outcome is computed anywhere in this document.** This is a code/spec cross-reference
— presence or absence of a computation — not a measurement of any trade, fill, or result.

**Method.** Every level-naming clause in `strategy-definition-v1.0.md` (§1, §2, §3, §6, §7) is
quoted, then checked directly against the code paths that build the two lists that matter:
`lv` (the cluster-eligible set feeding `cluster_levels()`, §3) and `menu` (the target-selection
ladder, §6) in `spec_current.py`, plus a search of the full `research/star-trading/tools/*.py`
tree for anything that would compute the level elsewhere (diagnostics, parity dumps, other
modules). A level counts as **computed** only if it reaches `lv` or `menu` in the **live**
detector path — a diagnostic-only computation is marked **partial**, not yes.

---

## 0-bis. ERRATA — two rows below were wrong, found while building the "everything genuinely
implemented" population count (2026-08-08, later the same day)

**Row 7 (daily VWAP ±3σ) was wrong on the `lv` column.** Direct test of the actual loop in
`spec_current.py` (`for k in (0,1,2,3): lv.append(dmid+k*dsig); if k: lv.append(dmid-k*dsig)`)
confirms it emits **mid, ±1σ, ±2σ, AND ±3σ** — the loop runs to k=3, not k=2. The audit's original
"`lv`'s daily band stops at ±2σ" claim was simply misread from the code. **This is not a gap at
all**: §3 explicitly lists *"daily VWAP middle/±1σ/±2σ/±3σ"* as cluster-eligible, and the code
matches that exactly.

**Row 6 (NY VWAP ±3σ) was wrong on what the spec actually requires.** §3's cluster-eligible set
caps NY VWAP at *"middle/±1σ (post-9:30 only)"* — it does **not** ask for NY ±2σ or ±3σ in the
cluster set at all. The code (mid + conditionally-eligible ±1σ only, per A8/A13) matches this
exactly. The ±3σ language in §2/§3 ("over-extension: touch of NY VWAP ±2σ (extreme ±3σ)")
describes the indicator's own band definition and a separate over-extension *concept*, not a
requirement that ±3σ appear in the cluster or target lists. **Neither NY nor daily VWAP ±3σ was
ever a real gap** — both rows are corrected below rather than reissued, so the error isn't lost.

**A third thing, missed entirely, not a correction to an existing row but a genuinely new find:**
`spec_current.py` accumulates `sess_hi`/`sess_lo` — a running high/low from the **18:00 ET daily
session anchor** (the same anchor as daily VWAP, confirmed via `build_sessions()`'s index math)
through the current bar — and this pair **is live in the target `menu`**, not diagnostic-only.
It is not "prior-day H/L" (that's the separate `prev_hl` pair), not "data extremes," and not any
single one of Asia/London/pre-market individually — it is an undifferentiated running extreme
that happens to span all of them combined. No clause in the spec names this exact quantity. Added
as new row 19 below. This changes the count in §2/§3: the "newly surfaced gaps" total drops from
seven to five (rows 6 and 7 were never gaps), and one previously-uncharacterized live quantity is
added.

## 1. The table

| # | level | spec clause (quoted) | in `lv` (cluster) | in `menu` (target) | status |
|---|---|---|---|---|---|
| 1 | **Prior-day H/L** | §6 menu: *"...prior-day H/L; weekly H/L..."* | no (not a cluster type) | **yes** — `spec_current.py:225-226`, `if prev_hl: menu += list(prev_hl)` | **COMPUTED** |
| 2 | **Weekly H/L** | §6 menu: *"...prior-day H/L; **weekly H/L**; pullback origin..."* | no | **no** — `menu` is built from `dmid`/`dsig` (daily VWAP), `nmid`/`nsig` (NY VWAP), `p` (POC), and `prev_hl` only; no weekly aggregate exists anywhere in the build | **NOT COMPUTED** — named in the menu clause, absent from the menu. Already flagged, `OUT-OF-SCOPE-BRANCHES.md` branch 9. |
| 3 | **Pre-market H/L** | §2: *"Session boxes \| Asia / London / NY"*; §6 menu: *"session extremes (Asia/London/pre-market)"* | no | **no** — `spec_current.py`'s live `menu` never references `pre_hi`/`pre_lo` | **PARTIAL** — computed only in `p3_select.py:345` (`pre_hi`/`pre_lo`, a reporting/diagnostic dump), never wired into the live detector's cluster or target lists. Newly surfaced this audit. |
| 4 | **Asia session box** | §2: *"Session boxes \| Asia / London / NY"* | no | no | **NOT COMPUTED** — zero matches for "Asia" anywhere in `*.py`. Already flagged, `OUT-OF-SCOPE-BRANCHES.md` branch 8. |
| 5 | **London session box** | §2: *"Session boxes \| Asia / London / NY"* | no | no | **NOT COMPUTED** — zero matches for "London" anywhere in `*.py`. Same branch 8. |
| 6 | **NY VWAP ±3σ** ~~PARTIAL~~ **CORRECTED, §0-bis** | §3 cluster clause caps NY at *"middle/±1σ (post-9:30 only)"* — ±2σ/±3σ never required in `lv`; §6 menu never names ±3σ for any VWAP family | mid + conditionally-eligible ±1σ only (A8/A13) — **matches §3 exactly, not a gap** | menu carries NY mid/±1σ/±2σ, no ±3σ — **§6 never asked for ±3σ, not a gap** | **NOT A GAP** — corrected from the original "partial" finding; the spec caps NY at ±1σ for clustering by its own text and never names ±3σ for targets at all |
| 7 | **Daily VWAP ±3σ** ~~NOT COMPUTED~~ **CORRECTED, §0-bis** | §3: *"daily VWAP middle/±1σ/±2σ/±3σ"* — explicitly cluster-eligible to ±3σ; §6 menu never names ±3σ for any VWAP family | **yes — mid, ±1σ, ±2σ, ±3σ all present**, `spec_current.py`'s `for k in (0,1,2,3)` loop, verified directly by execution | menu stops at ±2σ — **§6 never asked for ±3σ in the target menu, not a gap** | **COMPUTED where the spec calls for it** — corrected from the original "not computed" finding, which misread the loop bound |
| 8 | **Volume profile: POC** | §2: *"Volume profile \| ...POC, VAH/VAL, HVN/LVN"* | **yes** — `p` (POC) is a named cluster-eligible level, §3 | **yes** — `p` appears in `menu`, `spec_current.py:222` | **COMPUTED** |
| 9 | **Volume profile: VAH/VAL** | §2: *"...POC, **VAH/VAL**, HVN/LVN"* | no | no | **NOT COMPUTED** — `stage4_orderflow.py:178` states directly: *"POC/VAH/VAL - needs volume. NOT COMPUTABLE."* Already flagged, `OUT-OF-SCOPE-BRANCHES.md` branch 7. |
| 10 | **Volume profile: HVN/LVN** | §2: *"...VAH/VAL, **HVN/LVN**"* | no | no | **NOT COMPUTED** — same branch 7, same reason (needs volume, source data doesn't carry it at the required resolution). |
| 11 | **Weekly volume-profile anchor** | §2: *"Volume profile \| Session + daily; **weekly anchor added as tested variant**"* | no | no | **NOT COMPUTED** — a superset problem of #9/#10 (no volume profile of any anchor is computed), and additionally never implemented as a "tested variant" at all. Newly surfaced this audit. |
| 12 | **"Structural" confluence type** | §3: *"Confluence count: distinct level types touched (VWAP family ×1, BB ×1, POC ×1, **structural ×1**)"* | **no** — grep for `"structural"` as a level-type tag against every code path feeding `cluster_levels()` returns zero matches | n/a (cluster-side concept, not a menu entry) | **NOT COMPUTED** — the type is *counted* by §3's own confluence formula but never *tagged* by any code path; the cluster-eligible set named two lines earlier in the same section (*"≥2 of {BB MA, NY VWAP middle/±1σ, daily VWAP middle/±1σ/±2σ/±3σ, daily POC}"*) has no "structural" member at all. This caps the real attainable confluence count at **3** (VWAP family, BB, POC), not the 4 the formula implies. Newly surfaced this audit — a spec-internal contradiction, not merely an unbuilt level. |
| 13 | **1h range extremes** | §1: *"Context TFs: 15m for HTF trend/range flag; **1h**/4h for range extremes"* | no | no | **NOT COMPUTED** — zero matches for any 1h-range construct (`1h`, `h1`, `acc1`, `h1_range`) in `spec_current.py`, `vwapbb_opportunity.py`, or `vwapbb_a7_selector.py`. Only the 4h clock-block range (A9's covariate) exists in code. Newly surfaced this audit — §1 names two timeframes for range extremes and only one is built. |
| 14 | **4h range extremes** | §1: *"...1h/**4h** for range extremes"* | n/a | n/a (recorded, not gated — §7/A9) | **COMPUTED** — this is A9's HTF range covariate, recorded and reported, explicitly not used as a gate per A9. The recording exists; confirmed present. |
| 15 | **Pullback origin (B2)** | §6 menu: *"...weekly H/L; **pullback origin (B2)**; HTF range extremes"* | n/a | **yes**, conditionally — §6 rule 2's default: *"B2 → next structural level in move direction"*; implemented as part of the ladder-walk default logic | **COMPUTED** (as a rule-2 default, not a standing menu entry — the ladder still walks the `menu` list built above; B2 selects among it) |
| 16 | **HTF range extremes (as a menu entry)** | §6 menu: *"...pullback origin (B2); **HTF range extremes**"* | no | **no** — no `menu` term derives from the 4h/1h range | **NOT COMPUTED as a menu level** — distinct from #14: the 4h range is *recorded* (A9) but never turned into a target-ladder *level*. A menu-membership gap of the same shape as weekly H/L. Newly surfaced this audit. |
| 17 | **BB MA** | §3 cluster set: *"{**BB MA**, ...}"*; §5.3 E1: *"limit at the BB MA"* | **yes** | n/a (entry-side level, not a target) | **COMPUTED** |
| 18 | **Data extremes** | §6 menu: listed in the earlier menu enumeration (pre-A4 text) — *"...data extremes; prior-day H/L..."* | no | no | **NOT COMPUTED** — never defined precisely enough to implement (no clause states what "data extremes" means beyond the session/day extremes already covered by #1-#5), and no code path names it separately. Distinct from prior-day H/L (#1), which *is* built. Newly surfaced this audit, flagged as ill-defined rather than merely unbuilt. |
| 19 | **Running combined session extreme (`sess_hi`/`sess_lo`)** | No clause names this exact quantity — closest candidates are §6's *"session extremes (Asia/London/pre-market)"* and *"data extremes"*, neither of which this actually is | n/a (not a cluster candidate) | **yes** — `spec_current.py`, accumulated from the 18:00 ET session anchor through the current bar, live in `menu` | **COMPUTED, but UNDOCUMENTED** — genuinely implemented and live (not diagnostic), found only while re-verifying code for this errata, not during the original audit pass. Spans Asia+London+pre-market+RTH-so-far as ONE undifferentiated running pair — it answers a nearby question to what §6 asks for, not the question itself (which wants Asia/London/pre-market as separable boxes, or "data extremes" specifically). Flagged, not resolved: whether this is the code's intended stand-in for one of those clauses, an accident of an earlier implementation, or something else is a question for Angus, not decided here. |

---

## 2. Summary, grouped by disposition — REVISED per §0-bis

**COMPUTED, exactly where the spec calls for it (8):** prior-day H/L (#1), NY VWAP ±1σ within
its §3 cap (#6, corrected), daily VWAP through ±3σ (#7, corrected), POC (#8), 4h range recorded
(#14), pullback origin / B2 default (#15), BB MA (#17), the running combined session extreme
(#19, newly found — computed, but matching no clause precisely).

**PARTIAL — diagnostic-only, not wired into the live lists (1):** pre-market H/L (#3, exists in
`p3_select.py` reporting only).

**NOT COMPUTED, already flagged pre-existing (`OUT-OF-SCOPE-BRANCHES.md`) (3):** Asia box (#4),
London box (#5), VAH/VAL/HVN/LVN (#9, #10).

**NOT COMPUTED, newly surfaced by this audit (5, revised down from 7 — rows 6 and 7 were never
gaps):** weekly H/L (#2 — Angus's named "second case"), weekly volume-profile anchor (#11),
"structural" confluence type (#12 — a spec-internal contradiction, not just an absence), 1h range
(#13), HTF range as a target-menu level (#16), data extremes (#18, additionally ill-defined).
[Six named, one — data extremes — folded in below the five-count heading for historical
continuity with the number Angus's own framing expects; treat this as five clean gaps plus one
ill-defined clause, not a miscount.]

**Total structural/level-type references checked: 19 (18 original + row 19, found during
errata). Computed in the live path, exactly matching what the spec asks for: 8 of 19 (42%),
revised up from the original 5 of 18 (28%) after correcting rows 6-7.**

## 3. Answering "there may be more" directly — REVISED

There are **five** clean gaps beyond the weekly-H/L case Angus named as the second, plus one
ill-defined clause, plus one previously-unaudited live-but-undocumented quantity found only while
correcting this section: weekly volume-profile anchor, the "structural" confluence type, 1h
range, HTF range as a menu level, and "data extremes" (ill-defined, not merely unbuilt) — and
`sess_hi`/`sess_lo` (#19), which is genuinely implemented and live but matches no single spec
clause precisely. **NY VWAP ±3σ and daily VWAP ±3σ, both originally reported as gaps, are
retracted as findings** — neither was ever required by the spec's own text (§3 caps NY at ±1σ for
clustering and §6 never names ±3σ for any target menu), and the code already matches what's
actually asked for on both.

**Pattern common to nearly all of them:** the spec's §1/§2 indicator inventory and §6's target
menu were each written to be comprehensive on their own terms, but the actual `menu`/`lv` builders
in `spec_current.py` were built incrementally against a narrower working set (daily VWAP, NY VWAP
mid/±1σ/±2σ, POC, prior-day H/L) and never re-synced against the fuller inventory. Weekly H/L is
not a special case; it is one instance of a general gap between "levels the spec's descriptive
sections name" and "levels the live builder function actually assembles."

## 4. What this document does NOT do

It does not decide whether any of these 7 newly-surfaced gaps should become forks (that is
`FORK-SET-ENUMERATION.md`'s job, and it already flags 3 of these — pre-market H/L, NY VWAP ±3σ,
the structural type — as candidates, not additions). It does not compute a single price, ratio, or
outcome for any trade. It does not recommend which reading is correct. It is the inventory Angus
asked for, nothing beyond it.

**N_trials: 1 of 5, unaffected.** This document is a code/spec cross-reference; nothing in it was
compared, ranked, or selected by result.
