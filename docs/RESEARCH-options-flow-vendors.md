# RESEARCH — options-flow / gamma-wall vendors with MCP access

Angus asked, 2026-08-12, what could feed **real** put/call walls into the agent
stack — the thing Pine cannot compute (see `pine/nq_expected_move_vxn.pine` for
why: no OI, no gamma, no dealer positioning in Pine). Explicitly **not a build
decision** — his words: *"for now we will work on validating my strategy as is
before we look for additions."* This is the map for when that changes.

Researched 2026-08-12. Prices and tiers move; re-check before committing.

---

## THE ONE ARCHITECTURAL TRAP, before any vendor

**Replay validation needs HISTORICAL options data, not live.** Feeding today's
gamma walls into a June replay is the purest lookahead this project has yet
invented — worse than the phantom-high leak, because the whole point of a wall
is that it predicts where price stalls.

So the vendor filter is: **does it serve as-of historical OI/GEX at intraday
resolution?** A live-only API cannot be validated against the corpus and cannot
enter a replay briefing at all.

The integration pattern is already established and needs no new machinery: the
**orchestrator** fetches (as-of in replay, live in production) and drops the
levels into the briefing. The agents stay `tools: []`/`[Read]` and never hold
the vendor MCP — same reason `tv-macro-events` never holds WebSearch.

---

## Candidates

### FlashAlpha — the closest fit
`github.com/FlashAlpha-lab/flashalpha-mcp` · MCP server, 70+ tools

- **Explicit call/put walls, gamma flip, dealer-positioning levels** — computed,
  not raw.
- **Covers CME equity-index futures (NQ=F, ES=F)** alongside QQQ / SPX / IWM.
  ~250 symbols at the top tier.
- **Historical replay at MINUTE resolution back to April 2018** — this is the
  deciding feature. It makes as-of backtesting against the narrated week and
  the Feb–July walk-forward possible.
- Also: DEX/VEX/CHEX by strike, IV surface/SVI, 0DTE strike-by-strike intraday
  exposure change, order flow, earnings expected-move.
- **Free tier: 5 calls/day, one expiry, 15-minute freshness** — enough to eyeball
  whether walls line up with the days already replayed.
- Paid: Basic $79/mo, Growth $299/mo, Alpha $1,499/mo (real-time, uncached).
- Auth: `/mcp` with an apiKey param, or `/mcp-oauth` (OAuth 2.1 + PKCE).
- **Watch:** 15-minute cache on free/basic. Fine for replay validation, useless
  for a live 2m entry decision — the live use case needs the top tier.

### Quant Data — raw per-strike, cheaper flat rate
`api.quantdata.us/mcp` · hosted MCP

- Per-strike call/put gamma for **SPY, SPX, QQQ, NDX** + 6,000 tickers.
- `interval-map` gives a **per-minute time series of gamma by strike** — good
  granularity.
- **No pre-computed walls or zero-gamma level** — you aggregate the raw
  `exposureMap` yourself. More work, but you control the model.
- 365+ days of history (vs FlashAlpha's 2018), which still covers Feb–July.
- $149.99/mo ($124.99 annual), 240 req/min, no monthly quota.
- Exchange-licensed data; no latency figure published.

### Others worth knowing
- **Unusual Whales** — official API + MCP, 100+ endpoints: options flow, dark
  pool, Greek exposure, CME futures. Retail-oriented; strong on flow, and it
  also carries congressional/insider noise that is irrelevant here.
- **EODHD** — options API with MCP, full Greeks + IV + OI, 42 fields/contract.
  Cheaper, more EOD-oriented; check intraday freshness before relying on it.
- **Databento** — already the futures data source for this repo. Carries OPRA,
  but as **raw options ticks**: no GEX computation, and the full firehose is
  expensive. Only sensible if the goal is building the dealer model in-house.

---

## FOUR CAVEATS THAT DECIDE WHETHER THIS IS WORTH IT

1. **Every "wall" is a MODEL, not an observation.** OI by strike is fact; gamma
   exposure is OI transformed through an assumption about who is long and who
   is short — conventionally that customers buy puts and sell calls, so dealers
   hold the other side. That assumption is contested. **Two vendors will
   disagree about where the wall is from the same chain.** Treat any single
   vendor's level as one opinion.
2. **The walls that move NQ are mostly not NQ's own options.** NQ futures
   options carry far less OI concentration than QQQ and NDX, and SPX/SPY drag
   the whole complex. QQQ is the practical proxy; NQ=F coverage is a
   convenience, not the source of the effect.
3. **Walls move.** OI shifts daily, and intraday as 0DTE prints. A level that
   mattered at the open can be gone by 11:00 — which is exactly the window he
   trades.
4. **It must survive the same bar as everything else here.** Adding a wall layer
   is a new input to the thesis/trigger briefing, so it gets the same treatment
   as the fib layer did: encode his convention, run it in replay, and score
   whether decisions using it beat decisions without it. **If it does not move
   the agreement or outcome numbers, it does not go in**, however good the
   theory sounds.

---

## CHEAPEST NEXT STEP, when he wants it

FlashAlpha free tier + its historical replay: pull the walls for **five days
already replayed**, and check by eye whether his entries and the agent's cluster
near them. Five API calls, no subscription, and it answers the only question
that matters before spending anything — **do the walls line up with where price
actually stalled on days we already know cold?**
