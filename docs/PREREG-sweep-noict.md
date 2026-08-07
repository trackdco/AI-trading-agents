# PREREG — SWP-02: JadeCap's sweep premise, non-ICT entries

**Committed before any number exists.**

Date: 2026-08-05
Family: `SWP-02`
Authorises: `scripts/swp02_census.py`

---

## 0. What is kept and what is thrown away

ANGUS 2026-08-05: *"id like to see his sweep idea but a different entry mechanism tbh…
its good to see how hes bascially mechanised ict, but i reckon we could do it better
without ict based entry"*.

**KEPT — the premise, because it is a liquidity claim and therefore measurable:**

- daily bias from the D1 close (candle-over-candle), which side you are allowed to hunt
- 1-hour swing points marked from the prior day, **untapped only** — a swing low is a
  candle whose neighbours both have higher lows, confirmed only on the third candle's close
- the **raid**: price trades beyond an untapped level
- the **confirmation**: an hourly candle **closes back inside**. *"No raid, no trade."*

**THROWN AWAY — the entry, because it is convention rather than mechanism:**

- 5-minute fair value gap, inverted FVG, order block, breaker, change-in-state-of-delivery
- "stop below candle two of the fair value gap"

His own words undercut the entry layer: he says the entry model is interchangeable —
*"VWAP, moving averages, volume profiles, whatever"* — *"because the context and narrative
is already in place"*. **If the author says the entry is interchangeable, testing his
specific one as though it were load-bearing is a category error.** So we test ours.

## 1. Why this satisfies the design constraints agreed today

- **Rare by mechanism, not by filtering.** Untapped hourly swing points get raided a
  handful of times a session at most. There is no big population being filtered down, so
  there is no filter to overfit — the failure mode that has killed every family this week.
- **Not another level-fade.** It is a *liquidity* event (stops consumed, book dries up
  behind the new extreme) with a confirmation requirement, not a reaction to a
  price level being touched.
- **Adaptive.** No absolute constants. Swing points are structural, the confirmation is a
  close, and every tunable below is a trailing quantile.

## 2. The entry arms — declared head-to-head on identical triggers

The E3/EC/E4 comparison on `LDN-CAN-01` showed this methodology works: same trigger set,
one variable changed, scored side by side. **None of these is ICT.**

| arm | entry | rationale |
|---|---|---|
| **A-CLOSE** | market at the confirming hourly close | decision and entry are the same instant, so flow and depth at that moment are legitimately measurable — the property that took L3 three attempts to get right |
| **A-RETEST** | limit at the raided level itself | the level is the structure; if it holds, the sweep thesis is intact. No FVG required. |
| **A-FLOW** | market on the first lower-timeframe minute where delta agrees with the reversal | uses the tape rather than a price pattern |

**Stop, all arms: beyond the sweep extreme.** That is where the thesis is wrong — if price
returns past the raid, the SFP failed. Structural, and no ICT object involved.

**Targets: a declared grid**, not his fixed 2R. Testing one geometry answers nothing —
`LDN-PO3-01` was killed twice at a target its own file recorded as unsettled.

## 3. Census, and the declared kill line (§5.9.1)

L0 measures the EVENT only. No P&L, no expectancy claim in either direction.

Reported: raids per session; how many produce a confirming hourly close; per era; per
session-hour; **and the mechanism test — the forward move after confirmation versus a
matched control of raids that did NOT confirm.** That control is the point: if confirmed
and unconfirmed raids behave the same, the SFP adds nothing and the whole premise is
decoration.

**KILL LINE, declared now:**

- **fewer than 0.5 confirmed setups per session**, or
- **confirmed raids do not beat unconfirmed raids** in the bias direction, in **both** eras

## 4. The bar downstream

`src/validation/prop_score.py`: net ≥ 4 pt/trade after 2pt friction (design target +10),
T ≥ 2, N ≥ 200, green days ≥ 55%, max day ≤ 30%, every year green.

## 5. Sessions

**NY and London both.** He explicitly refuses London — *"I would not anticipate trading
during London session if I'm going to trade NASDAQ"* — which makes London a genuine
out-of-sample test of his premise rather than a replication. If the mechanism is real it
should not care which session it is in; if it only works where he says, that is itself
informative.

## 6. Sealed

2023/24 sealed days untouched.
