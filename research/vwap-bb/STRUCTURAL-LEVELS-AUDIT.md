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

## 1. The table

| # | level | spec clause (quoted) | in `lv` (cluster) | in `menu` (target) | status |
|---|---|---|---|---|---|
| 1 | **Prior-day H/L** | §6 menu: *"...prior-day H/L; weekly H/L..."* | no (not a cluster type) | **yes** — `spec_current.py:225-226`, `if prev_hl: menu += list(prev_hl)` | **COMPUTED** |
| 2 | **Weekly H/L** | §6 menu: *"...prior-day H/L; **weekly H/L**; pullback origin..."* | no | **no** — `menu` is built from `dmid`/`dsig` (daily VWAP), `nmid`/`nsig` (NY VWAP), `p` (POC), and `prev_hl` only; no weekly aggregate exists anywhere in the build | **NOT COMPUTED** — named in the menu clause, absent from the menu. Already flagged, `OUT-OF-SCOPE-BRANCHES.md` branch 9. |
| 3 | **Pre-market H/L** | §2: *"Session boxes \| Asia / London / NY"*; §6 menu: *"session extremes (Asia/London/pre-market)"* | no | **no** — `spec_current.py`'s live `menu` never references `pre_hi`/`pre_lo` | **PARTIAL** — computed only in `p3_select.py:345` (`pre_hi`/`pre_lo`, a reporting/diagnostic dump), never wired into the live detector's cluster or target lists. Newly surfaced this audit. |
| 4 | **Asia session box** | §2: *"Session boxes \| Asia / London / NY"* | no | no | **NOT COMPUTED** — zero matches for "Asia" anywhere in `*.py`. Already flagged, `OUT-OF-SCOPE-BRANCHES.md` branch 8. |
| 5 | **London session box** | §2: *"Session boxes \| Asia / London / NY"* | no | no | **NOT COMPUTED** — zero matches for "London" anywhere in `*.py`. Same branch 8. |
| 6 | **NY VWAP ±3σ** | §2: *"NY session VWAP \| ...±1σ/±2σ/±3σ..."*; §3: *"over-extension: touch of NY VWAP ±2σ (extreme ±3σ)"* | **partial** — only mid and ±1σ (conditionally eligible per A8/A13) reach `lv` | **no** — `menu`'s NY block (`nmid, nmid±nsig, nmid±2·nsig`) stops at ±2σ; no `±3·nsig` term anywhere | **PARTIAL / NOT COMPUTED for ±3σ** — the σ band exists as a *concept* (over-extension check references it) but ±3σ is never built as a level in either list. Newly surfaced this audit. |
| 7 | **Daily VWAP ±3σ** | §2: *"Daily VWAP \| ...Full band set ±1σ/±2σ/±3σ..."* | no — `lv`'s daily band stops at ±2σ per §3's cluster definition | **no** — `menu`'s daily block (`dmid, dmid±dsig, dmid±2·dsig`) stops at ±2σ | **NOT COMPUTED for ±3σ** — same shape as NY ±3σ, daily side. Newly surfaced this audit. |
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

---

## 2. Summary, grouped by disposition

**COMPUTED (5):** prior-day H/L (#1), POC (#8), 4h range recorded (#14), pullback origin / B2
default (#15), BB MA (#17).

**PARTIAL — diagnostic-only or band-truncated, not wired into the live lists (2):** pre-market
H/L (#3, exists in `p3_select.py` reporting only), NY VWAP ±1σ (#6, eligible under A8/A13
conditions but the ±3σ tier named alongside it is not).

**NOT COMPUTED, already flagged pre-existing (`OUT-OF-SCOPE-BRANCHES.md`) (3):** Asia box (#4),
London box (#5), VAH/VAL/HVN/LVN (#9, #10).

**NOT COMPUTED, newly surfaced by this audit (7):** weekly H/L (#2 — Angus's named "second case"),
NY VWAP ±3σ (#6's extreme tier), daily VWAP ±3σ (#7), weekly volume-profile anchor (#11),
"structural" confluence type (#12 — a spec-internal contradiction, not just an absence), 1h range
(#13), HTF range as a target-menu level (#16), data extremes (#18, additionally ill-defined).

**Total structural/level-type references checked: 18. Computed in the live path: 5 of 18 (28%).**

## 3. Answering "there may be more" directly

There are **seven** more beyond the weekly-H/L case Angus named as the second: NY VWAP ±3σ, daily
VWAP ±3σ, weekly volume-profile anchor, the "structural" confluence type, 1h range, HTF range as a
menu level, and "data extremes." Two of these (#12 structural-type, #18 data-extremes) are not
simple absences — they are cases where the spec's own text is internally inconsistent or
insufficiently defined even before asking whether code implements it.

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
