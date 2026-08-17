"""Build a 0.4.9 trigger briefing: mkcand + the two new mechanical facts.

level_visits_this_session and chop_state are COMPUTED BY SCRIPT here, never
typed. Both are mechanical facts under runbook 0c - stated, never judged.
"""
import json, os, subprocess, sys
V = "/Users/barbelldaddy/AI-trading-agents/.venv/bin/python"
R = "/Users/barbelldaddy/AI-trading-agents"
sys.path.insert(0, R)


def _run(mod, args):
    p = subprocess.run([V, "-m", mod] + args, capture_output=True, text=True, cwd=R)
    if p.returncode:
        raise SystemExit(f"{mod} failed:\n{p.stderr[-2000:]}")
    return json.loads(p.stdout)


def facts(sess_day, dec, levels, prior_takes):
    """levels: {name: price} - EVERY candidate level, so whichever the agent
    names as its rejected_level is covered. Picking one for it would be the
    orchestrator judging the setup, which 0c forbids.
    prior_takes: list of 'HH:MM=price' for every PRIOR TAKE of the session."""
    names = list(levels)
    a = [sess_day, dec]
    for n in names:
        a += ["--level", str(levels[n])]
    for pt in prior_takes:
        a += ["--prior-take", pt]
    a.append("--json")
    res = _run("scripts.level_visits", a)          # --level is repeatable: ONE call
    if isinstance(res, dict):
        res = [res]                                 # it unwraps a single level
    lv = dict(zip(names, res))
    cs = _run("scripts.chop_state", [sess_day, "--at", dec, "--json"])
    return lv, cs


def build(spec, levels, prior_takes):
    lv, cs = facts(spec["sd"], spec["dec"], levels, prior_takes)
    extra = dict(spec.get("extra") or {})
    extra["level_visits_this_session"] = dict(by_level=lv, _source=(
        "scripts.level_visits - MECHANICAL FACT under runbook 0c. Counts takes already "
        "adjudicated at this level THIS SESSION (the current candidate counts as visit 1) "
        "and completed 15m candles in the last 60 minutes whose range contained it. "
        "Passes are not visits. A candidate re-adjudicated after an escalation is ONE take."),
        _what_it_governs=(
        "tv-trigger 0.4.8: freshness CAPS THE GRADE and nothing else. Only a fresh level may "
        "grade A; a stale one tops out at B; a third visit caps at C. The LICENCE is untouched - "
        "a T48 re-entry stays licensed, it just no longer comes at A size."))
    extra["chop_state"] = dict(cs, _source=(
        "scripts.chop_state - MECHANICAL FACT under runbook 0c. His definition implemented "
        "literally: a SMALL range (bottom quartile of the normal 3-hour NQ range, ~104pt over "
        "44 days) that has LASTED about three hours. Size and duration only."),
        _what_it_governs=(
        "tv-trigger 0.4.9: chop tells you HOW to trade, not whether to. In CHOP an edge trigger "
        "is licensed toward the far side, targeting the STRUCTURAL level near it rather than the "
        "range extreme; the middle is dead; and an edge fade is NOT counter-trend, so it does not "
        "cap at C."))
    spec = dict(spec); spec["extra"] = extra
    from scripts.replay_tools.mkcand import build as _b
    out, fires = _b(spec)
    return out, fires, lv, cs


if __name__ == "__main__":
    spec = json.load(open(sys.argv[1]))
    levels = json.loads(sys.argv[2])          # {"name": price, ...}
    prior = sys.argv[3:] if len(sys.argv) > 3 else []
    out, fires, lv, cs = build(spec, levels, prior)
    print(out)
    print("outer_band_gate_fires", fires)
    for n, d in lv.items():
        print(f"  level_visits {n:16s} @{d['level']:>10} visits={d['level_visits_this_session']} tests15m={d['tests_15m_60min']} fresh={d['fresh']}")
    print("  chop_state", cs["state"], "| zone", cs["zone_now"], "|", cs["reason"])
