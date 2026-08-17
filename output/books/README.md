# output/books/ — ACTIVE run logs, readable by the orchestrator

## Why this directory exists

`output/agent_runs/**` is **deny-listed for Read** in `.claude/settings.json`,
and that is deliberate: it stops an orchestrator session (or an agent) from
reading OTHER runs' outcomes and being contaminated by knowing how earlier
days resolved. It is one of the load-bearing parts of the no-leak
architecture and it should not be relaxed.

But an orchestrator producing a run MUST be able to read back the log it is
writing — that is where the day's own state lives (position, fills, spent
candidates, thesis in force). Reading your own live book is not a leak; it is
bookkeeping. The two needs were colliding, so they are now separated by
location rather than by weakening the rule:

| directory | contains | Read |
|---|---|---|
| `output/books/<run>/` | the run being produced RIGHT NOW | allowed |
| `output/agent_runs/` | every completed, archived run | denied |

## The rule

1. **While a run is live**, write its day logs to
   `output/books/<run>/<sess_day>_<run>.jsonl`. Read them freely — audit,
   verify, resume, recover.
2. **When a run is complete, scored and committed**, MOVE its logs into
   `output/agent_runs/`. That seals them: from then on they are outcome data,
   and no future orchestrator may read them.

```bash
git add -f output/books/<run>/<sess_day>_<run>.jsonl        # while live
mv output/books/<run>/*.jsonl output/agent_runs/            # on completion
```

Analysis scripts take paths as arguments and run OUTSIDE an agent context, so
they read either location without difficulty — they are the sanctioned way to
consume sealed run data, and they print aggregates rather than dumping
outcomes into a reasoning context.

## What has NOT changed

The deny list is untouched. `output/agent_runs/**`, the narrated-day corpus,
the teaching loop and the analysis documents all stay denied exactly as
before. This adds a location for live work; it removes no protection.
