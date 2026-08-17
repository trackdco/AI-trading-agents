"""Live-book logger for a run in progress.

Writes to output/books/<run>/<sess_day>_<run>.jsonl, which is READABLE, so the
orchestrator can verify every row, audit as it goes and resume cleanly. See
output/books/README.md: output/agent_runs/** stays deny-listed so no session can
read ANOTHER run's outcomes, and a completed run is MOVED there to seal it.

Same row shape and the same close-of-day ordering as the jn1 logger; only the
path and the run identity differ, so every downstream tool that takes a path
works unchanged on a live book or a sealed one.
"""
import json, os, shutil, sys
sys.path.insert(0, "/Users/barbelldaddy/AI-trading-agents")

ROOT = "/Users/barbelldaddy/AI-trading-agents"
BOOKS = f"{ROOT}/output/books"
SEALED = f"{ROOT}/output/agent_runs"


def logpath(run, sess_day):
    return f"{BOOKS}/{run}/{sess_day}_{run}.jsonl"


def versions():
    from scripts.replay_tools.jn1 import versions as _v
    return _v()


def write(run, sess_day, row):
    p = logpath(run, sess_day)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "a") as f:
        f.write(json.dumps(row) + "\n")
    return p


def read(run, sess_day):
    p = logpath(run, sess_day)
    return [json.loads(l) for l in open(p) if l.strip()] if os.path.exists(p) else []


def sort_log(run, sess_day):
    """Chronological + lifecycle order. Contents never change, only row order.

    Lifted from jn1.sort_log and parameterised on the path - candidates are
    adjudicated in parallel so rows land in completion order, and the audit's
    check B (decision minutes non-decreasing) fails on the raw file.
    """
    from scripts.audit_run_leak import _mins
    p = logpath(run, sess_day)
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


def seal(run):
    """Move a COMPLETED, scored, committed run into output/agent_runs/.

    From then on it is outcome data and no future orchestrator may read it. Never
    call this on a live run - the day's own state lives in the book.
    """
    src = f"{BOOKS}/{run}"
    moved = []
    for fn in sorted(os.listdir(src)):
        if fn.endswith(".jsonl"):
            shutil.move(f"{src}/{fn}", f"{SEALED}/{fn}")
            moved.append(fn)
    return moved
