# THE DESK — the live dashboard

```bash
python -m scripts.desk_server --run w49 --replay 40    # play a finished book back
python -m scripts.desk_server --run j49                # follow a run as it happens
```
then open <http://127.0.0.1:8787>.

## Why this needed almost no new code

**The run log is already the event stream.** Every decision the stack makes is
appended to `output/books/<run>/<sess_day>_<run>.jsonl` as one structured JSON
row, in order, carrying the agent's own reasoning verbatim. The dashboard is a
tail, a server-sent-event socket, and a page. **Nothing in the agents changed
and they do not know it exists.**

Because replay and live write the same schema, the same dashboard renders
both — so a finished book can be replayed at any speed, and the UI is useful
before live trading exists at all.

## What it shows

| panel | source |
|---|---|
| day P&L in R and points, equity spark | `exit` rows |
| open position, entry, stop, grade | `fill` / `exit` rows |
| **agent comms feed** | every `thesis` / `trigger` / `manage` row, tagged by agent, `output.reason` printed verbatim |
| decision funnel — candidates, passed, taken, filled | `trigger` and `fill` rows |
| session state — window, chop state, range | `chop_state` on trigger briefings |
| stack versions and model | `run_header` |

The comms feed is the point. It is not a log tail — it is each tier saying, in
its own words, why it did what it did, in the order it happened.

**One honesty note on "agents talking to each other":** they do not. The
orchestrator briefs each tier and each returns a verdict; tiers never address
one another. What the feed shows is the real cascade — thesis sets the frame,
trigger adjudicates against it, manage works the position. That is more
interesting than a chat transcript, and it is what actually happens.

## The kill switch

The one control that writes anything. It creates `output/HALT`; the
orchestrator checks for that file before each decision and stops.

**It can only make the system do less.** It cannot place, modify or cancel an
order, and it cannot resume by itself — resuming is a second deliberate click.
Everything else the server touches is opened read-only. The button a human
reaches for in a hurry should only ever be able to stop things.

**Still to wire on the orchestrator side:** the `output/HALT` check before each
decision. The button writes the file today; the runbook loop does not yet read
it.

## Deliberately absent

**No order-flow / depth panel.** It looked spectacular in the first mockup and
it was lookahead — the depth data was not as-of. Anything that cannot be proven
causal at the decision minute does not belong on a screen used to judge
decisions.
