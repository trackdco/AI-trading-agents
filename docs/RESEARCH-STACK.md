# Research stack (disarmed)

Built 2026-11-03. Nothing here places an order, holds a credential, or calls a broker.

The old canon dollar totals are withdrawn. `docs/CANON.md` says why.

## What runs

| Piece | Where |
|---|---|
| Firm rules, with the URL and the page date | `config/prop_rules.yaml` |
| One account path: max loss, daily loss, consistency, contracts, hours, payout | `src/research/prop/account.py` |
| Pass / payout Monte Carlo on a win-rate and average-win/loss distribution | `src/research/prop/montecarlo.py` |
| Causal tape, session VWAP, footprint, stacked imbalance, absorption, MBP-10 as-of | `src/research/features/` |
| Empty setup card. The harness will not invent a setup | `config/setup_card.yaml` |
| Walk-forward scoring, sign-flip null, prop path, kill file | `src/research/setup/harness.py` |
| High-impact USD blackout, reading the existing news archive | `src/research/news.py` |

The kill file is the same path the live vault uses, `output/live/KILL`. The live spine in `src/canon/spine.py` is untouched and still disarmed.

## Order-flow definitions

CVD is buy-aggressor volume minus sell-aggressor volume. Side `B` is the buyer (lifted the offer). Side `A` is the seller (hit the bid). This is the sign in `data/reference/cvd/README.md`. `scripts/build_cvd_minute.py` documented the opposite sign and is not used.

Session VWAP anchors at 18:00 America/New_York. `session_vwap_trades` is the volume-weighted trade price. `bar_vwap` uses each bar's open, which is the TradingView "session open" source, and it ignores a bar until that bar has closed.

A stacked imbalance is three or more consecutive prices on one closed minute where buy volume at P is at least 3× sell volume at P minus one tick, or the mirror for sells. A zero on the other side still counts when the printed side has at least one contract. The minute is invisible until it closes.

Absorption, over the 30 seconds ending at the decision: the trades in the window span at most 0.50 points, at least 50 contracts of aggressive volume print at the level (within one tick), and the defending side of the book is still there at the decision (at least half of the size it showed at the start of the window, or at least 20 contracts if it opened empty). Sellers attacking a bid, or buyers attacking an ask. If there is no book, the result is a proxy and `confirmed` is false. A proxy is not absorption.

MBP-10 is read as-of the decision. If a snapshot is labelled with the old archive convention (the minute stamp holds the last state of that minute), pass `convention="minute_label_end_state"`. A decision at the label then sees the previous minute, not that snapshot. The old selector, `ts <= label`, is what `docs/FINDING-depth-lookahead.md` caught. A test fails if the causal reader returns that snapshot.

## Data

Tests build their own trades and books. This environment has no Databento key and the committed files are minute footprints and minute depth, not raw ticks. `footprint_minutes_to_trades` can load the existing minute footprint, and it stamps each row at the minute close so a decision inside the minute cannot see it. Real tick and MBP-10 event timestamps are still required before any setup is judged. Depth that only exists as an end-of-minute label has to be read with the convention above, and it still cannot support a sub-minute absorption call.

## Prop simulator assumptions

Each fill is realized immediately. A pass is marked at the session close. A max-loss breach is marked on the fill. Eval profit does not carry into the funded account (Topstep says this; Lucid's pages do not, and that assumption is flagged). Topstep's payout cap is the standard cap, not the limited-time doubled cap. LucidFlex payouts use 50% of cycle profit. Lucid's dollar fees were not in the help article, so Lucid EV is computed at a fee of zero and marked unconfirmed. Items nobody should treat as confirmed are the `unconfirmed` list in `config/prop_rules.yaml`.

The closed-form 40% pass rate is a static floor, infinite horizon, no consistency rule, no costs: drawdown / (drawdown + target). The Monte Carlo is lower once the floor trails, the consistency rule is on, and the horizon is 60 trading days. `docs/PROP-BASELINE.md` is that run.
