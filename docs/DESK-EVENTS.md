# The Desk — live event schema

The contract between **Hermes (the engine)** and **the dashboard UI** (Lovable-built or
otherwise). Hermes *publishes* events; the UI *subscribes* and renders. This is the only
thing the dashboard needs to know about the engine — get these fields right and any front-end
can render the real desk faithfully.

## The one rule: the stream is READ-ONLY

The dashboard and the "talk to Jarvis" chat **consume** events. They never send trade
commands back. Zero LLM / zero UI in the trade path — Hermes decides mechanically, the UI
only reflects and explains. The socket is one-directional (engine → UI) for everything that
touches a trade. (A chat may send *questions* to a separate read-only Q&A endpoint that can
query the journal and current state, but it cannot place, size, cancel, or modify anything.)

## Transport (self-host)

Everything runs on the one VPS. The engine exposes a local WebSocket; the browser connects to
it. Nothing is exposed to the public internet.

```
Hermes / Python engine ──►  FastAPI WebSocket  ──►  ws://localhost:8787/stream  ──►  browser (Mac/phone on LAN)
```

- On connect, the server immediately sends one **`snapshot`** event (full current state), then
  streams incremental events as they happen.
- If the socket drops, the UI reconnects and gets a fresh `snapshot`. UIs must be able to
  rebuild entirely from a snapshot — never assume they saw every prior event.

## Envelope

Every message is a single JSON object with this envelope:

```json
{ "type": "agent_report", "ts": "2026-07-24T03:14:07.512Z", "seq": 4821, "session": "london", "data": { ... } }
```

| field | type | meaning |
|---|---|---|
| `type` | string | event type (catalog below) |
| `ts` | ISO-8601 UTC | engine timestamp |
| `seq` | int | monotonic sequence number (gap ⇒ you missed one ⇒ reconnect for a snapshot) |
| `session` | `"pre" \| "gold" \| "london" \| null` | active book, if any |
| `data` | object | type-specific payload (below) |

---

## Event catalog

### `snapshot` — full state on connect
Everything a fresh UI needs to draw the whole desk at once.
```json
{ "type": "snapshot", "data": {
  "engine": { "version": "2.1", "threshold_hash": "9f3c", "feed": "ok", "parity": "locked", "spine": "armed" },
  "clock": { "utc": "2026-07-24T03:14:07Z", "session": "london", "window": "0800-1000 Europe/London" },
  "account": { /* see account_tick */ },
  "position": { /* see position or null */ },
  "agents": [ /* last agent_report per subagent */ ],
  "verdict": { /* last verdict */ },
  "candles": [ {"t":"...","o":20352.0,"h":20353.5,"l":20351.0,"c":20352.75}, ... ],
  "depth": { /* see depth */ },
  "cvd": 1240,
  "equity_today": [0, 900, 1800]
} }
```

### `agent_report` — one subagent finished its part of the read
The subagents are the specialists; each emits one of these when it evaluates a candidate.
```json
{ "type": "agent_report", "data": {
  "agent": "STRUCTURE",                       // STRUCTURE | ORDER_FLOW | SETUP | RISK  (match Pat's set)
  "status": "pass",                            // pass | fail | info
  "summary": "wall behind NO · ahead 6.2pt · room_R 3.8",
  "checks": [                                  // the raw canon checks — bit AND value (journaling mandate)
    { "name": "W",      "pass": true,  "value": null,  "note": "no wall behind" },
    { "name": "FAR",    "pass": true,  "value": 6.2,   "note": "wall ahead > 4.5pt" },
    { "name": "ROOM",   "pass": true,  "value": 3.8,   "note": "room_R in (2.48, 9.56]" }
  ],
  "score_contrib": 3                           // how much this agent added to the book score
} }
```
Notes: `checks[].name` are the real canon feature names and differ by book (London: W/FAR/ROOM/ASIA; NY-gold: D/Tc/X/AGE/PAQ; pre: its own set). The UI can render them generically. Always send both the boolean and the raw value — the journal wants both.

### `verdict` — Hermes' final call
```json
{ "type": "verdict", "data": {
  "decision": "trade",                         // trade | skip
  "book": "london",
  "direction": "long",                         // long | short
  "pattern": "B2",
  "score": 3,
  "conviction": 1.5,                           // 0.25 | 0.5 | 0.75 | 1.0 | 1.5 | 2.25
  "of_stack": "both",                          // both | one | zero  (order-flow confirmations)
  "reason": "score 3 · OF stack both → x1.5",  // human-readable, for the chat/journal
  "skip_reason": null                          // set when decision == skip (e.g. "B setup, score 2")
} }
```

### `sizing` — dollar-risk sizing resolved (may be folded into `verdict`)
```json
{ "type": "sizing", "data": {
  "conviction": 1.5,
  "stop_points": 12.5,
  "risk_dollars": 300,                         // min(2.0, conviction) * base_risk_1_0
  "base_risk_1_0": 200,                        // 200 + 75 * floor((available_dd - 3000)/1000)
  "available_dd": 2340,
  "micros": 12,                                // min(40, round(risk_dollars / (stop_points * 2)))
  "clamped": false                             // true if the 40-micro spine clamp bit
} }
```

### `fill` — order placed and filled (limit bracket)
```json
{ "type": "fill", "data": {
  "trade_id": 47, "book": "london", "direction": "long",
  "entry": 20355.25, "stop": 20342.75, "target": 20392.75,
  "micros": 12, "risk_dollars": 300, "conviction": 1.5,
  "order_kind": "limit_bracket",
  "mbo_capture": { "path": "mbo/2026-07-24T0314.parquet", "bytes": 2202009 }
} }
```

### `position` — in-trade tick (send on each meaningful change)
```json
{ "type": "position", "data": {
  "trade_id": 47, "open": true, "direction": "long",
  "entry": 20355.25, "stop": 20342.75, "target": 20392.75, "micros": 12,
  "last": 20378.5, "r_multiple": 1.86, "unrealized": 558,
  "mae_r": -0.3, "mfe_r": 1.9
} }
```
Send `{ "open": false }` (or a `trade_close`) when flat.

### `trade_close`
```json
{ "type": "trade_close", "data": {
  "trade_id": 47, "exit": 20392.75, "exit_reason": "target",   // target | stop | time | manual
  "r_multiple": 3.0, "realized": 900, "hold_min": 42
} }
```

### `account_tick` — the account panel
```json
{ "type": "account_tick", "data": {
  "firm": "Lucid Flex 50k",
  "start_balance": 50000,
  "balance": 52340,
  "day_pl": 900,
  "trades_today": 1,
  "eod_floor": 50000,                          // the locked/ trailing floor
  "available_dd": 2340,                        // balance - eod_floor
  "base_risk_1_0": 200,
  "withdrawn_total": 0,
  "winning_days_since_payout": 3               // toward the 5-day (>=+$150) payout gate
} }
```

### `payout` — Build-6 withdrawal
```json
{ "type": "payout", "data": { "amount": 2000, "new_balance": 54340, "withdrawn_total": 2000, "policy": "build-6" } }
```

### `depth` — MBP-10 ladder (drives the heatmap)
```json
{ "type": "depth", "data": {
  "mid": 20355.25,
  "levels": [
    { "price": 20357.75, "side": "ask", "size": 88,  "is_wall": false },
    { "price": 20357.50, "side": "ask", "size": 420, "is_wall": true  },
    { "price": 20355.25, "side": "mid", "size": 0,   "is_wall": false },
    { "price": 20355.00, "side": "bid", "size": 140, "is_wall": false }
  ]
} }
```
`size` is contracts; the UI maps it to heat intensity (normalize per snapshot). `is_wall` = the FAR/wall check flagged it.

### `candle` — chart (append or update last)
```json
{ "type": "candle", "data": { "t": "2026-07-24T03:15:00Z", "o": 20355.0, "h": 20356.5, "l": 20354.0, "c": 20355.75, "final": false } }
```
`final:false` = still forming (update the last candle); `final:true` = closed (append next).

### `cvd` — cumulative delta tick
```json
{ "type": "cvd", "data": { "session_cvd": 1240, "delta_1m": 34 } }
```

### `spine_event` — a guardrail fired (rare, important)
```json
{ "type": "spine_event", "data": {
  "rule": "available_dd_halt",                 // available_dd_halt | daily_loss_halt | contract_clamp | spread_guard | feed_stale | fail_closed | ...
  "action": "halt",                            // halt | clamp | reject
  "detail": "available_dd $240 <= $250 buffer — flatten and stop for the day"
} }
```

### `heartbeat` — liveness (every ~5s)
```json
{ "type": "heartbeat", "data": { "feed": "ok", "spread_rel": 0.8, "parity": "locked", "orders_per_min": 0 } }
```

---

## Self-host wiring (minimal)

**Engine side** (FastAPI, on the VPS):
```python
# one broadcaster; Hermes calls emit(...) wherever it decides/acts/journals
import asyncio, json
from fastapi import FastAPI, WebSocket
app = FastAPI(); clients = set()

async def emit(evtype, data, session=None):
    msg = json.dumps({"type": evtype, "ts": now_iso(), "seq": next_seq(),
                      "session": session, "data": data})
    for ws in list(clients):
        try: await ws.send_text(msg)
        except Exception: clients.discard(ws)

@app.websocket("/stream")
async def stream(ws: WebSocket):
    await ws.accept(); clients.add(ws)
    await ws.send_text(json.dumps(current_snapshot()))   # full state first
    try:
        while True: await ws.receive_text()              # ignore inbound — READ-ONLY
    except Exception: clients.discard(ws)
```

**UI side** (what Lovable wires to):
```js
const ws = new WebSocket("ws://localhost:8787/stream");
ws.onmessage = (e) => {
  const { type, data } = JSON.parse(e.data);
  if (type === "snapshot")      hydrateWholeDesk(data);
  else if (type === "verdict")  renderVerdict(data);
  else if (type === "position") renderPosition(data);
  else if (type === "depth")    renderHeatmap(data.levels);
  // ... one handler per type; unknown types ignored
};
ws.onclose = () => setTimeout(connect, 1000);            // reconnect → fresh snapshot
```

## Mapping to the desk panels (my mockup → these events)

| Panel | Fed by |
|---|---|
| Hermes core (subagents light up) | `agent_report` (one per subagent), `verdict` (core pulse) |
| Verdict / final call | `verdict`, `sizing` |
| Price chart + bracket | `candle` (line), `fill` (draw bracket), `position` (price marker) |
| Depth heatmap | `depth` |
| CVD strip | `cvd` |
| Account tiles | `account_tick`, `payout` |
| Position card | `fill`, `position`, `trade_close` |
| Equity line | `account_tick.day_pl` (accumulate), `trade_close` |
| Comms feed | every event's human-readable `summary`/`reason` |
| "Talk to Jarvis" chat | read-only Q&A endpoint over the journal + latest snapshot (never writes) |

Hand this file + the mockup (`docs/desk-hud.html`) to Lovable/Pat: the mockup is the look,
this is the data. The build is then just "render each event type into its panel."
