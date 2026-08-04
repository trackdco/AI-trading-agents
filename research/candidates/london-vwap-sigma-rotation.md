---
date: 2026-08-04
status: thesis-pending
tags: [london, vwap, session-structure]
sources: ["articles/sweep-2026-08-04-session-vwap.md#SS4", "articles/sweep-2026-08-04-session-vwap.md#SS5", "articles/sweep-2026-08-04-session-vwap.md#SS7"]
---

# london-vwap-sigma-rotation — your σ-location principle as the strategy itself

## Thesis (for Angus)

Your standing rule — longing at +2σ is a different trade than longing at −1σ —
promoted from filter to mechanism. Outside catalyst days, London on NQ is
rotational: US institutional flow is absent, so nobody active has the size to
relocate value. Price stretched to ±2σ of the overnight-anchored VWAP is the
marginal chaser paying the worst price with no follow-on buyer behind them;
absent acceptance, inventory reverts to the mean. Three legs, one location logic:
(1) rotational days — fade the ±2σ touch on rejection, target the mean;
(2) trend days (accepted Asia-range break) — DON'T fade; buy the pullback to the
anchored VWAP from the move's origin, where the drivers' average entry gets
defended — same trend as the breakout chaser, at −1σ instead of +2σ;
(3) late-window — a London trend stalling ≥ +1.5σ into the 05:00–06:30 lull with
no fresh flow until the US arrives; late longs are the pullback's liquidity.
DAX implied-vol-band research (4,634 days: middle-of-range opens close inside the
1σ band ~84%) supports the rotational base case. The regime split (rotation vs
trend) IS the hard part — misclassify and leg 1 fades a trend day.

## Mechanical skeleton

Overnight VWAP anchored 18:00 ET, σ from realized 1-min dispersion. Regime gate:
skip fades on drive opens / bottom-quintile Asia range / no VWAP cross since
02:00. Leg 1: first ±2σ touch + rejection close → toward VWAP; stop ~2.5–3σ; two
consecutive closes beyond 2σ = acceptance, stand down all session. Leg 2: after
accepted break, pullback tags origin-anchored AVWAP within −1σ-to-flat and holds
→ with trend; stop = acceptance below AVWAP. Leg 3: 05:00–06:30 stall ≥ +1.5σ at
a structural magnet, no new extreme ≥ 30–45 min → fade; flat by 08:00 ET.

## Flags

- Data: candles-only (absorption gate on the 2σ touch optional).
- Crowding: VWAP-band fading hugely published for RTH; overnight-anchored London
  version thin. The quoted 70–80% reversion stats are retail-lit claims — ignore,
  measure ourselves.
- **NY-canon input-family overlap: MEDIUM (VWAP — NY's G bit reads
  ent_vs_vwap_sd_dir).** Different mechanism (NY uses it as entry-quality gate;
  this trades the location itself), but the family flag stands.
- Three legs = three arms in ONE ledger family, not three discoveries.
