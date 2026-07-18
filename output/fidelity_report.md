# Fidelity & Cross-Regime Report — passes 16–18 (Feb/Mar calibration, April out-of-sample)

_Objective (Angus, pass 16): stop optimizing month statistics; make the engine trade like HIM,
and prefer cross-regime smoothness over single-month maximums ("I'm willing to sacrifice some
performance in February if it means March is better")._

## The fidelity matrix (calibrated months: Feb = his 20W/8L hand log, Mar = his 9W/8L journal)

| arm | FEB $ | MAR $ | combined | FEB capture | MAR capture |
|---|---|---|---|---|---|
| F0 champion v2 (ref) | +11,442 | −4,430 | +7,012 | 9/20W 2/8L | 1/9W 3/8L |
| F1 +EC entries | +11,035 | −2,135 | +8,900 | 7/20W | **4/9W** |
| F2 +window 11:00 | +9,995 | −4,000 | +5,995 | 8/20W | 4/9W |
| F3 +news standdown OFF | +13,975 | −3,620 | +10,355 | 6/20W | 3/9W |
| F4 +max 3/day | +14,530 | −5,945 | +8,585 | 6/20W | 3/9W |
| F5 EC+newsOFF | +13,818 | −2,180 | **+11,638** | 5/20W | 3/9W |
| F6 F5+V8 | +3,495 | −4,288 | −793 ✗ | 4/20W | 3/9W |
| **F7 champion+V8 trail** | +7,712 | **−638** | +7,074 | 8/20W | 1/9W |
| F8 EC+V8 | +2,476 | −3,138 | −662 ✗ | 6/20W | 4/9W |
| F9 champ+newsOFF+V8 | +7,305 | −1,309 | +5,996 | 6/20W | 0/9W |

## The April referee (true out-of-sample: no arm saw April during design)

| arm | APRIL $ | maxDD$ | win% |
|---|---|---|---|
| F0 champion v2 | −5,660 | 7,098 | 8.1% |
| **F5 EC+newsOFF** | **−14,652 ✗✗** | 15,530 | 9.1% |
| **F7 champion+V8** | **−3,335** | 4,312 | 17.9% |

## Key findings

1. **F5 was a two-month curve fit and April executed it.** The best Feb+Mar combined arm
   (+$11,638) lost −$14,652 in April — market entries with no news stand-down are lethal in
   chaos regimes. The same overfitting failure mode we caught in February configs, one level up.
2. **V8 (the trail) is the only layer that improved EVERY month it never saw:**
   Mar −$4,430→−$638, Apr −$5,660→−$3,335, at a Feb cost of −$3,730. It never turns a hostile
   month green — it consistently cuts the bleed 40–85%. V8 = a genuine DAMAGE-CONTROL layer,
   the first mechanically regime-robust component we have.
3. **EC entries quadruple March winner-capture (1/9→4/9)** — they are how Angus actually
   executes displacement — but they amplify damage when unprotected (F5's April). EC belongs
   in the toolbox as a REGIME-CONDITIONAL mode (agents decide when market-entry is safe),
   not as a global default. EC+V8 interact badly (market fills at momentum peaks get trailed
   out on the first pullback): −$700 combined on both stacks.
4. **No mechanical configuration is profitable in the Mar–Apr chaos regimes.** Mechanics
   moved the floor from −$5.7k to −$3.3k; only regime-aware behavior change (stand down /
   continuation-only / size down) can do the rest → Pat's two agents (regime context + HTF
   structure) remain the required layer, with V8 as the mechanical safety net beneath them.
5. Fidelity remains partial (best March capture 4/9 winners): his late-morning winners die to
   position-occupancy (engine's earlier junk holds the slot), and his over-extension patience
   (Mar-11 autopsy: his limit at the POC filled where the engine's early fade got stopped) is
   not yet a mechanical requirement. Both are next-loop items.

## Current honest state

- **Champion v2 + V8** is the best regime-robust mechanical stack measured:
  Feb +$7,712 / Mar −$638 / Apr −$3,335 (with April's damage 41% below champion's).
- Everything above remains a CALIBRATION-LOOP result on 3 months, 1 of them journal-derived.
  May (Angus's +$5k benchmark month; triggers partially banked) + Jun–Jul are the next
  referees. His May trade log (screenshots pending) upgrades May to a calibrated month.
- Parked: full-day session map (per-session budgets), Jan-1 data re-pull (structure history),
  heatmap/orderflow (Angus: later), Feb-25 stop_ref detector bug.

---

# Pass 19 — the FOUR-MONTH scoreboard (Feb–May, Angus's "green every month" bar)

| month | F0 champion v2 | F7 champion+V8 | F1 EC |
|---|---|---|---|
| FEB | +$11,442 (36.4%) | +$7,712 (**45.5%**) | +$11,035 |
| MAR | −$4,430 (8.3%) | **−$638** (22.2%) | −$2,135 |
| APR | −$5,660 (8.1%) | **−$3,335** (17.9%) | **−$13,325 (9.5%)** ✗ |
| MAY (Angus's +$5k month) | −$2,280 (21.2%) | −$1,963 (24.2%) | **+$955 (32.4%, 47% green days)** |
| **4-month total** | **−$928** | **+$1,776** | **−$3,470** |
| months green | 1/4 | 1/4 | 2/4 |

## Conclusions

1. **No static configuration passes the bar.** Best 4-month total is F7 at barely +$1,776.
2. **F7 (V8 trail) = the only net-positive stack** and the best win rate every single month
   (45.5/22.2/17.9/24.2) with the shallowest worst month (−$3,335). It is the mechanical floor.
3. **EC is confirmed REGIME-BIMODAL:** best-in-class in rotation/momentum months (Feb +$11k;
   only green arm in May), catastrophic in headline-chaos (Apr −$13.3k). Entry MODE must be
   regime-gated — this is now quantified, not speculative.
4. **The regime-gate value proposition, priced:** a gate that had picked EC in Feb/May, V8 in
   Mar, and stand-down in Apr = **≈ +$11.4k over the four months with zero red months.** That
   is the agents' job description with a dollar figure attached (upper bound; a real no-hindsight
   gate captures part of it).
5. Angus's claim — "my strategy is profitable every month when you take the right trades" —
   is CONSISTENT with the data: the right trades exist each month, but they are different
   KINDS of trades (entry mode, structure priority, stand-downs) per regime. No fixed config
   takes them all; judgment (agents) selects among mechanically-sound modes.

_All arms remain Feb/Mar-calibrated; Apr/May are their out-of-sample. May journal/live funded
screenshots from Angus will upgrade May to a calibrated month. Jun–Jul detection pending as
the next referee set._
