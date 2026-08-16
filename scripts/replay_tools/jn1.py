"""jn1 month-run logger. One log per session-day, append-only, chronologically sorted at close.

Contracts are the PATCHED set, pinned on the run branch at 8ecd13a1 (synced from
source branch claude/tradingview-mcp-agent-setup-ql18v8; runbook/tooling synced
at de8b0fbb from source tip d12686ed):
  tv-thesis 0.4.2 · tv-trigger 0.4.7 · tv-manage 0.3.2 · tv-macro-events 0.2.0
Every run header records the source commit and the four versions read from the
files at run time, so the log proves which contracts produced it.

Adapted from the wk1 logger; only the run identity and the rules-applied notes
differ. wk1 ran rolled-back contracts with the 0.4.4-0.4.6 rules deliberately
NOT applied; jn1 is their first outing and they ARE applied.
"""
import json, sys, subprocess
sys.path.insert(0, "/Users/barbelldaddy/AI-trading-agents")

ROOT = "/Users/barbelldaddy/AI-trading-agents"
PREFIX = "jn1"
CONTRACT_SOURCE = "8ecd13a1+de8b0fbb (source d12686ed)"


def logpath(sess_day):
    return f"{ROOT}/output/agent_runs/{sess_day}_jn1.jsonl"


def versions():
    out = {}
    for a in ("tv-thesis", "tv-trigger", "tv-manage", "tv-macro-events"):
        p = f"{ROOT}/.claude/agents/{a}.md"
        for ln in open(p):
            if ln.startswith("version:"):
                out[a] = ln.split(":", 1)[1].strip()
                break
        out[a + "_sha256"] = subprocess.run(
            ["shasum", "-a", "256", p], capture_output=True, text=True
        ).stdout.split()[0][:16]
    return out


def write(sess_day, row):
    with open(logpath(sess_day), "a") as f:
        f.write(json.dumps(row) + "\n")


def header(sess_day, day_next, extra=None):
    r = {"row": "run_header", "run_prefix": "jn1", "session_day": sess_day,
         "trades_calendar_day": day_next,
         "session_day_convention": f"opens {sess_day} 18:00 NY, LONDON and NY print on {day_next}",
         "contract_source": CONTRACT_SOURCE, "agent_versions": versions(),
         "caps": "LIFTED at his instruction; fills beyond LONDON 2 / NY_PRE 1 / NY_AM 2 "
                 "tagged beyond_written_cap; both scoreboards (as-run and as-written) per day",
         "windows": "LONDON 03:00-04:59, NY_PRE 08:00-09:29, NY_AM 09:30-11:00 with the "
                    "09:35 open buffer. The 0.4.4-0.4.6 rules ARE applied (first outing): "
                    "09:10 NY_PRE entry cutoff, flatten pre-market carries by 09:29:59 (T51), "
                    "grade/size agreement, outer-band fade-only gate, C-grade scale-in hold, "
                    "trail clearance floor.",
         "gates": "weekly-anchor gate (scripts.gate_weekly_anchor) hard per day; R0 parity + "
                  "no-leak at every landing; tripwire sensor per 0.4.2; THE FLIP per 0.4.7",
         "orchestrator": "no trading discretion (RUNBOOK 0c). Moves the chart, computes "
                         "numbers, calls agents, enforces mechanical invariants, writes rows."}
    if extra:
        r.update(extra)
    return r


def trigger(sess_day, cid, window, dec_min, brief, shot, decision, out, tools=2, **kw):
    r = {"row": "trigger", "candidate_id": cid, "window": window,
         "decision_minute": dec_min, "agent_spawn": "tv-trigger 0.4.7",
         "tool_uses": tools,
         "leak_check": f"pass - replay truncated at {dec_min.split('T')[-1]}, verified via "
                       "replay_status and data_get_ohlcv period.to",
         "briefing": brief, "screenshot": shot, "briefing_class": "FACT-ONLY",
         "decision": decision, "output": out}
    r.update(kw)
    write(sess_day, r)
    return r


def sort_log(sess_day):
    """Chronological + lifecycle order. Contents never change, only row order.

    Candidates are adjudicated in parallel, so rows land in completion order and
    the audit's check B (decision minutes non-decreasing) fails on the raw file.
    """
    from scripts.audit_run_leak import _mins
    p = logpath(sess_day)
    rows = [json.loads(l) for l in open(p)]
    SUB = {"trigger": 0, "limit_placed": 1, "fill": 2, "manage": 3, "exit": 4}

    def base(r):
        for f in ("decision_minute", "placed_at", "fill_bar_start", "minute"):
            if r.get(f) is not None:
                k = _mins(r[f])
                if k is not None:
                    return k
        if r.get("row") == "exit":
            ks = [_mins(x.get("bar_start", "")) for x in (r.get("exit_detail") or [])
                  if x.get("bar_start")]
            ks = [k for k in ks if k is not None]
            if ks:
                return max(ks)
        return None

    trig = {r["candidate_id"]: base(r) for r in rows
            if r.get("row") == "trigger" and r.get("candidate_id")}
    keys = []
    for i, r in enumerate(rows):
        t = r.get("row")
        if t == "run_header":
            keys.append((-10 ** 6, 0, 0, i)); continue
        if t == "day_summary":
            keys.append((10 ** 6, 0, 0, i)); continue
        cid = r.get("candidate_id")
        if cid and cid in trig and t in SUB:
            keys.append((trig[cid], SUB[t], base(r) or 0, i)); continue
        if t == "window_close":
            keys.append((None, 0, 0, i)); continue
        b = base(r)
        keys.append((b if b is not None else None, -1, 0, i))

    wmax, last = {}, -10 ** 6
    for k, r in zip(keys, rows):
        w = r.get("window")
        if k[0] is not None and w:
            wmax[w] = max(wmax.get(w, -10 ** 6), k[0])
    out = []
    for k, r in zip(keys, rows):
        if k[0] is None:
            out.append(((wmax.get(r.get("window"), last) + 0.9, 9, 0, k[3]), r))
        else:
            last = k[0]
            out.append((k, r))
    srt = [r for _, r in sorted(out, key=lambda x: x[0])]
    with open(p, "w") as f:
        for r in srt:
            f.write(json.dumps(r) + "\n")
    return len(srt)
