---
date: 2026-08-04
status: reference
tags: [london, session-structure, vwap, research-sweep]
sources: ["see per-concept lists below"]
---

# Sweep record — session-structure / VWAP angle (agent sweep, 2026-08-04)

Sourcing: WebSearch extracts only; direct fetches 403-blocked. Cited statistics
are claims-from-search-snippets, not verified page reads. URLs = deep-dive leads.

## SS#1 asia-sweep-reject → candidate `london-asia-sweep-reversal`
Adds the σ-location native framing: the sweep typically terminates stretched
at/beyond +2σ of overnight-anchored VWAP — the fade is reversion-from-stretch,
the losing trade is the +2σ chase. Same event as OF#1/AMT#2.
Sources: fxnx.com/en/blog/ict-asian-range-liquidity-... · innercircletrader.net/tutorials/... ·
fxreplay.com/strategies/judas-swing-model · en.forexclub.pl/Asian-Range-Liquidity-Sweep-... ·
liquidityfinder.com/news/asian-session-secrets-...
Crowding: extreme as discretionary lore; very lightly mechanized publicly.

## SS#2 narrow-asia-expansion-break → candidate `london-asia-sweep-continuation`
Narrow Asia (bottom-percentile trailing range) = unresolved positioning; European
open forces resolution. Herman 17-yr NQ study: narrow-Asia sessions make London
markedly more aggressive; London follows through on the side already breached in
the 00:00–02:00 dead hour. σ-condition: only take breaks launching within ±1σ of
overnight VWAP — a break fired from +2σ has spent its fuel.
Sources: hermantrading.pro/backtest-library/... · x.com/R_Herman_/status/1947998216764391925 ·
nqstats.com/aln_sessions.html · quantifiedstrategies.com/london-breakout-strategy/ ·
edgeful.com/blog/posts/best-time-to-trade-futures
Crowding: naive London breakout heavily published (and marginal); this conditioned
NQ-native version niche.

## SS#3 euro-open-gap-location-regime → candidate `london-inventory-fade` (+ go-branch to euro-open-drive)
Location-conditioned open classification: NQ gap studies (2,791 RTH days
2015–2025) — small inside-prior-range gaps fill ~78%, large outside-range gaps
~8%; DAX cash-open fades ~71% with EOD stop. Mechanism (inside-value opens revert
to settlement; outside-value opens with acceptance trend) re-anchored to 03:00 ET
vs prior NY settlement. Numbers do NOT port; mechanism does.
Sources: tradingstats.net/gap-fill-strategy/ · tradingstats.net/when-do-gaps-fill/ ·
quantifiedstrategies.com/gap-fill-trading-strategies/ · marketcalls.in/market-profile/... ·
jimdaltontrading.com/glossary/overnight-inventory · edgeful.com/blog/posts/trading-gap-fills
Crowding: NY-open gap fading arbed/decayed; London re-anchor rarely measured.

## SS#4 london-vwap-2sigma-fade → candidate `london-vwap-sigma-rotation`
Outside catalyst days London is rotational (no US institutional flow to relocate
value): ±2σ of overnight VWAP = marginal chaser at worst price with nobody behind
them. Retail lit quotes ~70–80% reversion from 2–3σ touches (RTH-derived,
unverified); Bouhmidi DAX work (4,634 days): middle-of-range European opens close
inside the 1σ implied-vol band ~84%. Purest expression of the σ-location
principle: the trade only exists BECAUSE entry is at ±2σ.
Sources: ninjatrader.com/futures/blogs/vwap-strategies-futures/ · crosstrade.io/learn/... ·
trendsandbreakouts.com/vwap-bands · tradingview.com/script/Nuh4yGoj-... ·
ungeracademy.com/blog/dax-trading-strategies-breakout-bias · tradersuite.online/blog/...
Crowding: VWAP-band fading hugely published for RTH; overnight-anchored London
version thin.

## SS#5 avwap-handoff-pullback → candidate `london-vwap-sigma-rotation` (trend leg)
After an ACCEPTED Asia-range break, the AVWAP anchored at the originating extreme
tracks the drivers' average entry; pullbacks to it get defended. Buys the pullback
at −1σ-to-flat instead of paying +2σ on the breakout — same trend, better location.
Sources: alphatrends.net/anchored-vwap/ · cmtassociation.org/wp-content/uploads/2024/01/Shannon-... ·
tradingsim.com/blog/anchored-vwap-strategies · tradersmastermind.com/anchored-vwap-... ·
tradingview.com/script/axdZYTOT-Pre-Cash-Positioning-VWAP/ · warriortrading.com/using-vwap-...
Crowding: AVWAP fashionable among equity swing traders; London futures usage niche-of-niche.

## SS#6 first-hour-momentum-carry → candidate `london-euro-open-drive`
Academic intraday momentum (Gao et al. JFE 2018 + follow-ups, 17 developed-market
index futures incl. 8 European): first half-hour predicts later session, strongest
on high-volume/news days. Re-specified: European-cash first hour (03:00–04:00 ET)
direction, structure-confirmed, carries through the London morning to ~06:00 ET.
Sources: sciencedirect.com/science/article/abs/pii/S0304405X18301351 ·
sciencedirect.com/science/article/abs/pii/S0304405X21001598 · c.mql5.com/forextsd/forum/173/... ·
tapescript.io/blog/intraday-momentum-strategy · edgeful.com/blog/posts/trading-sessions-explained
Crowding: anomaly widely known as RTH first→last half-hour; London re-spec ~unpublished.

## SS#7 pre-ny-exhaustion-fade → candidate `london-vwap-sigma-rotation` (late-window leg)
The London move often completes before the US arrives: volume dries into the
05:00–06:30 ET lull ("London creates intention, not completion"). Trend stalling
late, stretched ≥ +1.5σ, pressing a structural magnet with shrinking range = the
marginal European buyer is done; late longs are the pullback's liquidity. Counter
of SS#6 separated by window-phase and σ-location.
Sources: zayecapitalmarkets.com/london-new-york-overlap-session-2/ ·
alphaflowtrader.com/trading-sessions-guide/ · arongroups.co/forex-articles/new-york-reversal/ ·
edgeful.com/blog/posts/trading-sessions-explained · arxiv.org/pdf/1810.12099
Crowding: "NY reverses London" is standard lore triggered at 08:00+; pre-NY-lull
σ-gated version not mainstream.

## SS#8 dow-dst-session-gates → SPEC LAYER (DoW/DST gates + endogenous open detector)
(a) DoW: Tue–Thu cleanest breakouts per London-breakout writeups; Monday favors
continuation (ES ORB research: Monday+up ~72% continuation); Friday favors fading
follow-through. (b) DST mismatch: ~2–3 weeks/yr the European cash open lands at
02:00 ET, and every ET-clocked algo fires an hour off the true liquidity event.
Robust fix: detect the open endogenously — first 1-min bar in 01:45–03:15 ET with
volume z-score above threshold. The DST fortnights are either skip-weeks or
deliberately-traded weeks while ET-clocked participants misfire.
Sources: easyindicators.substack.com/p/how-daylight-saving-time-affects · fxglobe.com/... ·
tradingstats.net/orb-strategy-research/ · edgeful.com/blog/posts/best-day-of-week-... ·
newyorkcityservers.com/blog/london-breakout-strategy · tradinghours.com/markets/xetra
Crowding: DoW effects broadly published; the DST-mismatch angle ~undocumented as edge.
