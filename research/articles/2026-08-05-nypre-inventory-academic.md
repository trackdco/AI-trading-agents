---
date: 2026-08-05
status: reference
tags: [ny-pre, overnight-structure, order-flow, research-sweep]
sources: ["https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr917.pdf", "https://libertystreeteconomics.newyorkfed.org/2026/07/the-disappearing-overnight-drift/", "https://personal.lse.ac.uk/polk/research/TugOfWar.pdf", "https://elmwealth.com/night-moves-overnight-drift/", "https://www.marketcalls.in/market-profile/trading-inventory-imbalances-and-inventory-adjustments-market-profile-tutorial-reloaded.html", "https://www.cmegroup.com/articles/2025/reassessing-liquidity-beyond-order-book-depth.html"]
---

# The inventory-risk account of the pre-open — and the one-month-old paper that kills half of it

Full-text sources, not snippets. The NY Fed staff report was fetched as PDF
(98pp) and mined directly; the Liberty Street follow-up was published
**2026-07-01, five weeks ago**, and materially changes what is worth testing.

---

## A1 — The mechanism (Boyarchenko, Larsen & Whelan, NY Fed SR917 / *RFS* 2023)

The paper's subject is US equity index futures over 24 hours, 1998–2020, on ES
with NQ and YM as cross-checks. The claim is an inventory story:

> Liquidity providers "post resting limit orders and absorb the residual buy or
> sell pressure at the end of the U.S. trading day. When institutional flows tilt
> heavily to one side in the final hour of trading, LPs step in as buyers of last
> resort and carry the resulting inventory overnight. That inventory is risky:
> overnight markets are thin, prices can move against the LPs before they can
> offload, and internal risk limits tighten when volatility is high. To absorb the
> imbalance at all, LPs demand a discount at the close." *(Liberty Street, 2026-07-01)*

Formally the expected overnight return is the product of three observable
factors: **closing order imbalance × return variance × LPs' risk-bearing
capacity**. The drift dies if any one collapses.

Conditioning variable, exactly as defined: **relative signed volume (RSV)**, the
net buyer-initiated share of volume over **15:15–16:15 ET**, bounded [−1, +1],
"large and negative on heavy sell-off closes and near zero on balanced days."

Asymmetry, from the abstract: *"market selloffs generate robust positive overnight
reversals, while reversals following market rallies are much more modest."*
Attributed to time-varying market-maker risk-bearing capacity, and explicitly
**not** to VIX — the paper double-sorts and finds VIX distributions similar across
positive and negative imbalance days.

## A2 — The finding that sits inside our session

Two statements locate structure in the NY pre-market window specifically.

> "**Thirty minutes prior to the opening of the cash market at 9:30 equity returns
> are initially large and negative** and become smaller in magnitude but remain
> persistently negative until 12:00. **We dub negative return realizations between
> 9:00 – 10:00 'opening hour' returns.**" *(SR917)*

> "Panel (b) zooms in on the overnight session revealing three U-shaped patterns:
> between 18:00 and 2:00 (Asia), between 2:00 and 3:00 (European opening), and
> **between 3:00 and 8:30 which coincides with scheduled U.S. macro announcements**."
> *(SR917, on volume)*

And in the 2026 follow-up, the bin-sorted chart of next-day cumulative returns by
closing imbalance carries two shaded regions:

> "Shaded regions mark the overnight drift window (2:00–3:00 ET) **and the opening
> reversal (8:30–10:00 ET)**." *(Liberty Street, 2026-07-01)*

So the authors treat the pre-open as a **separate leg of the same inventory
cycle**, not as part of the 2am drift. 08:30–10:00 ET is our window.

## A3 — 🔴 The kill: the 2am overnight drift is dead, and they say so on NQ

This is the single most valuable thing in this round, because it stops us
spending arms.

> "the 2:00–3:00 window that previously generated roughly 3.7 percent per annum
> has averaged close to zero since 2021... The 2:00–3:00 window — previously
> responsible for more than 60 percent of the contract's 5.9 percent annualized
> close-to-close return — is flat. **The same pattern holds in the E-mini
> Nasdaq-100 (NQ) and E-mini Dow Jones (YM) contracts.**"

Cause, per their own decomposition: **channel 1 collapsed.** Closing-imbalance
*dispersion* (rolling 252-day SD of end-of-day RSV) fell **6.5% → 2.9%**, more
than halved. Channels 2 and 3 are ~unchanged: VIX mean 20.4 → 19.4 (medians 18.6
→ 18.2), overnight share of E-mini volume 15% → 16%. Mechanism given: *"limit
orders posted at the close have become smaller in the post-publication sample,
consistent with algorithmic liquidity providers slicing flow more finely and
transmitting less residual inventory onto end-of-day counterparties."*

Corroborating market evidence they cite: NightShares launched NSPY/NIWM in June
2022 to harvest exactly this, citing this paper's mechanism in the prospectus.
Both closed fourteen months later.

**Consequences for us, stated plainly:**
1. Any "hold overnight / buy the European open" idea is dead on arrival for NQ.
   Do not spend an arm on it.
2. The fade is in **dispersion of the conditioning variable**, not in the
   mechanism. Their own falsifiable prediction: *"if order-imbalance dispersion
   widens back toward its pre-2020 range, the overnight drift should reappear in
   the same 2:00–3:00 window."* That means the correct form of any surviving
   trade is **conditional on a large imbalance**, never unconditional — the
   tail days still exist even when the SD halves.
3. The 2021–25 bin chart shows the spread "much narrower" but **the opening-reversal
   window is shaded separately and is not separately declared dead.** That is an
   open, cheap, one-census question and it is ours.

## A4 — The tug-of-war (Lou, Polk & Skouras)

Overnight and intraday expected returns are opposite in sign for essentially every
Fama-French-Carhart anomaly: momentum is earned overnight, value/profitability/
investment intraday. Their interpretation is a clientele tug-of-war where the side
positioned for the close-to-close pattern is constrained and leaves part of the
abnormal return unexploited. Relevant to us only as background: **overnight and
the RTH day are different return-generating regimes and should never be pooled**
— which is an argument for treating ny-pre as its own sleeve rather than an
extension of the canon's pre leg.

## A5 — Dalton's overnight inventory (the practitioner version of the same idea)

Dalton's framing, independent of the academic literature and reached from auction
theory: overnight inventory is neutral, or it is long/short and the market adjusts
it during the day session — *"resulting in a rebalancing in the form of a long
liquidation break or short covering rally"* — or it is one-sided and the market
doesn't care. *"When overnight inventory is 100% short, the odds favor a counter
auction or correction."* The stated hard part is discriminating "old business"
(inventory unwind) from "old business plus new buying" (real repricing).

That discrimination is exactly what depth and signed flow are for, and it is the
same question C2 in the video sweep raises from the retail side. Two traditions,
one unresolved conditional.

## A6 — CME on why depth alone will mislead us here

> "Order book depth may provide an incomplete and potentially misleading picture
> of liquidity... metrics such as price impact together with volume density
> functions provide a more insightful picture." Example given: E-mini S&P traded
> ~65% more volume in December 2018 as volatility rose, **despite order book depth
> falling 75%** versus September 2018.

Directly load-bearing for us: we hold MBP-10 snapshots for this window. A thin
book is not the same as an illiquid one, and a wall is not the same as a
defended level. Any depth-based trigger must be paired with what actually
executed, not just what was resting.

---

## What's usable

- The conditioning variable is **fully specified and we can compute it**: signed
  volume 15:15–16:15 ET on the prior day, from the CVD footprint parquets. It is
  a *prior-day, pre-session* input — no lookahead, and structurally uncorrelated
  with every session-structure candidate in the book.
- The window is named by the authors: **08:30–10:00 ET opening reversal**, with
  the 09:00–09:30 leg documented as "large and negative."
- The asymmetry is specified and testable: sell-side closes produce robust
  reversals, buy-side closes weak ones. If our census finds a *symmetric* effect,
  that is evidence we measured something other than the inventory channel.
- The failure mode is specified in advance: if imbalance dispersion in our era is
  as compressed as they report, the number of qualifying tail days may be too
  small to clear A1 sample sufficiency. **That is a sample-size kill, not an
  edge kill, and it should be declared before the census, not discovered after.**

## What's noise

- The unconditional overnight drift. Dead on NQ, on the authors' own five extra
  years. Any arm spent here is a wasted arm.
- VIX as a conditioner for this mechanism — explicitly ruled out by their double
  sort.
- Retail "overnight continuation" base rates that ignore the closing imbalance:
  they are averaging across a conditioning variable that the source literature
  says is the whole effect.

## Contradictions between sources

- **Dalton vs the Fed on direction.** Dalton says one-sided overnight inventory is
  corrected *during the day session* (a flush at/after the open). The Fed's
  inventory unwinds into the *European* open, with a further negative leg into
  the US open. Both describe an unwind; they disagree on where it lands. Since
  the European leg is now flat, the two accounts converge on the US open — which
  is a genuine, non-obvious reason to expect the effect to have *migrated into
  our window* rather than vanished. This is the thesis of
  `nypre-closing-imbalance-unwind` and it is the strongest single idea from this
  round.
- **Our own census vs the published risk-premium claim.** `nypre-prerelease-premium`
  measured 04:00→08:25 drift NEGATIVE in both eras against a published positive
  claim. SR917's third volume U-shape (03:00–08:30, scheduled macro) and the
  persistent negative pre-open returns are consistent with our sign, not the
  published one. Two independent confirmations of a sign we already measured.

## Candidate leads

- `nypre-closing-imbalance-unwind` — A1 + A2 + A3(2) + A5. Primary.
- `nypre-derisk-into-print` — A2 second quote + our own killed census's residue.
- `nypre-thin-break-trap` — A6 + the video sweep's C2.
