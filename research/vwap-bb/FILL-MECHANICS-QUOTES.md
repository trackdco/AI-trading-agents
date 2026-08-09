# FILL MECHANICS — FOUR CLAUSES, QUOTED IN FULL, NO PARAPHRASE

**2026-08-08. Amendment 05 round 2, item 2.**

---

## 1. A5, entire

> ### A5 — 2026-08-08 — §5.4: minimum stop distance of 10.00 points
>
> **Change.** §5.4 now carries a floor: effective stop = **max(structural stop, 10.00 pt)**. The
> floor applies at placement only; the "never widened" rule is unchanged, and a structural stop
> already beyond 10.00 pt is used as-is.
>
> **Reason — fill realism and measured spread, not performance.**
>
> 1. **The measured spread makes tighter stops meaningless.** Top-of-book spread over 5,781 RTH
>    snapshots on 99 sessions is **0.75 pt median (3 ticks), 1.50 pt at p90**
>    (`research/STATE.md` COSTS). A 10.00 pt stop is **40 ticks — 13.3× the median spread and
>    6.7× the p90.** Below roughly that scale the stop is not measuring structure, it is
>    measuring the width of the book.
> 2. **It bounds cost as a fraction of risk.** At the measured base stop-exit cost of 0.975 pt,
>    a 10 pt stop puts costs at **9.75% of risk**. The frozen geometry's 3.12 pt median put them
>    at **31.2%**, which moved cost-adjusted breakeven from 40.6% to 46.4% on its own.
> 3. **It never excludes behaviour the author demonstrated.** The hand log's smallest in-scope
>    stop is **11.00 pts**; the floor sits below it. Every trade Angus actually took under the
>    settled session convention is admissible under A5. This uses the author's recorded stop
>    *distances*, not his P&L.
> 4. **It sits inside the feasible region**, jointly with A4 — the two are coupled, since a floor
>    on R raises the distance a target must reach to clear 1.5R
>    (`target-stop-reconciliation.md` §5).
>
> **Grounds.** **No outcome was computed, no P&L, no configuration compared, nothing ranked.**
>
> **Tag: [FIAT].** §5.4 stated no minimum.
>
> **Consequences, recorded so they are not rediscovered later:**
> - A5 is a **floor, not a repair.** The 29.6% of triggers whose E1 entry falls on the wrong side
>   of the wick extreme remain invalid and are still skipped. The E1-plus-wick pairing is
>   degenerate at both ends and that is **still an open gate-4 item**.
> - With A4, the minimum target distance becomes 15.00 pts (10.00 × 1.5).
> - The §1 note that "median trade resolves ~30 min" was derived under the old geometry. Wider
>   stops lengthen holds, so the 30-minute one-position lockout used in the signal count is a
>   **declared placeholder that A5 makes more approximate, not less**.

**Notably absent from A5, checked directly: no sentence in it states an order type, and no
sentence in it addresses what happens if the market does not return to the stop-derived level.**
A5 is entirely about the **distance**, not the **mechanism** of transacting at it.

---

## 2. The clause specifying what order is placed at the level, and its order type

**§5.3, rule 3, quoted in full — this is the entirety of what the spec says about placing the
entry order:**

> *"3. **Limit price — TOURNAMENT (replaces "what makes the most sense"):**
> - **E1:** limit at the BB MA (most frequent in journals)
> - **E2:** limit at the 50% level of the trigger candle's wick
> - **E3:** limit at the penetrated cluster level nearest the block's close"*

**The order type, checked precisely: never stated as a type declaration — but effectively named
by word choice.** The section header is *"Limit price"*, and every one of the three variants says
*"limit at [level]"*. A price whose defining property is that it is a **limit** is, by
construction, describing a **limit order** — there is no separate sentence anywhere that says
"place a limit order" as opposed to a market or stop order, but there does not need to be: calling
the number a "limit price" already answers the order-type question the same way "stop: beyond the
wick extreme" (§5.4) answers it for the stop.

**What is genuinely never stated is the *execution semantics* of that limit order** — how long it
rests, whether it can be worked across more than one bar, what happens if price never returns to
it. The only clause that touches this is §5.5:

> *"5. No fill → no chase. Order cancels if price runs T_cancel points beyond entry without
> filling. T_cancel: CALIBRATE."*

This confirms the ORDER TYPE reading (a "no-chase cancel" rule only makes sense for a resting
order that can fail to fill — a market order can't fail to fill) but **T_cancel has no stated
start value** and is DISABLED under both implementations in this project (A9's doctrine in this
repo; `AMBIGUITIES.md` A-09 in the blind build), so **the one clause that would operationalise
limit-order semantics is present in name only and inert in practice.**

**The finding, stated plainly:** the order type is not "nowhere stated" — it is named by
implication ("limit price") and corroborated by the no-chase clause's existence. **What is
missing is everything needed to actually SIMULATE that order type**: how long it rests, whether
partial-bar touches count, what "no chase" means operationally once T_cancel has no value. The
gap is in the **mechanics**, not the **label**.

---

## 3. The clause defining the 1.5R admission screen, and which price it evaluates against

**§6, rule 5, quoted in full, as amended by A4:**

> *"5. **RR floor — target is the nearest *valid* target, and "valid" means it clears the
> floor.** Walk the ladder of opposing menu levels outward from entry. The working target is the
> **first level whose front-run-adjusted distance is ≥ 1.5R**. Skip only if **no** level in the
> menu clears the floor. RR floor: CALIBRATE. [AMENDED 2026-08-08 — see Amendment Log A4]"*

**Which price it evaluates against, stated in the clause's own words: "outward from ENTRY."**
Not the fill. `entry` in this spec's own vocabulary is the E1/E2/E3 **limit** price from §5.3 —
the same price A5's stop floor is also measured from ("Effective stop = max(structural stop,
10.00 pt)" is a distance from that same entry).

**A4's full amendment, for the reasoning behind "outward from entry" and its own confirmation of
what price is meant:**

> *"**Change.** §6 rule 5 previously read "nearest valid target < 1.5R → skip." It is now: walk
> the ladder of opposing menu levels outward from entry and take the **first level whose
> front-run-adjusted distance is ≥ 1.5R**; skip only if **no** level in the menu clears the
> floor."*
>
> *"Reading "valid" as "clears the floor" is the only reading under which rule 5 is not
> self-defeating, and it is consistent with rule 1 ("list opposing structural levels beyond
> entry, **by distance**") — a list ordered by distance implies walking it."*

**Confirmed: the admission screen is evaluated entirely against the intended limit, never against
a fill.** Nothing in §6 rule 5 or A4 contemplates a fill price at all — the entire target-selection
and floor-clearing logic operates on `entry` as defined in §5.3, before any accounting rule about
transacting at that price has even entered the picture.

---

## 4. What happens when a bar opens through the intended entry

**No clause in `strategy-definition-v1.0.md` addresses this at all.** The spec's own text is
silent on gap-through behaviour. The only place this is addressed is `PREREGISTRATION.md`'s
accounting rules — a **separate document**, governing the backtest, not the strategy:

> ### 4. ACCOUNTING RULES — fixed in advance
>
> *"These are committed here so they cannot be chosen after seeing a result."*
>
> *"2. **Entry fills at the OPEN of the bar after the signal bar closes.** The signal bar must
> close to confirm (§5.2); the earliest actionable price is the next bar's open. **No fill at the
> signal bar's close, and no fill at the limit price unless it is also the next open.**
>   - **Consequence, accepted:** this departs from E1's stated limit-at-the-BB-MA. Modelling
>     limit-fill probability is a fill model, not an accounting rule, and building one after
>     seeing the data is exactly the freedom this document exists to remove. The next-open
>     convention is worse than a filled limit and better than nothing, and it is fixed now."*

**This is the exact clause, and it is unambiguous: there is no "opens through the limit, fill
favourably" branch anywhere in this project's own accounting rules.** The rule fills at the open
**unconditionally** — better, worse, or indifferent to the limit, and explicitly forbids filling
at the limit price itself unless the open happens to equal it. **The project's own accounting
rule already discloses that this "departs from E1's stated limit-at-the-BB-MA" and is "worse than
a filled limit"** — this is not a newly discovered gap; it is a documented, deliberate departure
that nobody had yet quantified until `FILL-ACCOUNTING-FORK.md` and the geometry-only report did
so.

**What accounting rule 4.2 does NOT address, and which the blind build's alternative reading
(`AMBIGUITIES.md` A-10) invented on its own:** the "otherwise the fill is the limit itself" branch
— i.e., what happens on the (now measured, §3 of the geometry report) **52.2% of trades whose
fill bar never even reaches the limit at all.** Rule 4.2 doesn't have an "otherwise" clause; it
always fills at the open. The blind build's true-limit reading supplies one, but it is the blind
build's own invention, not something either the spec or the pre-registration states.

---

## Summary of the finding

| question | answer |
|---|---|
| Is an order type stated? | **Implied, not declared** — "limit price" (§5.3) plus the no-chase clause (§5.5) make it unambiguous *what kind* of order was intended |
| Is the fill *mechanism* for that order type stated? | **No.** T_cancel (the one parameter that would operationalise it) has no value and is disabled everywhere |
| What price does the 1.5R screen evaluate? | **The intended limit ("entry"), stated explicitly — "outward from entry"** |
| What price does the trade actually transact at? | **The next bar's open, unconditionally (`PREREGISTRATION.md` 4.2)** — a documented, self-disclosed departure from the limit |
| Does anything reconcile these two facts? | **No.** The screen and the accounting rule were written independently, each internally consistent, and nothing in either document checks that the price the screen certifies is the price the accounting rule delivers |
