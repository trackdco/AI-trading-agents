#!/usr/bin/env python3
"""JOURNAL — what the agents were thinking, trade by trade, in their own words.

    python -m scripts.journal_report output/agent_runs/2026-06-21.jsonl
    python -m scripts.journal_report output/agent_runs/*.jsonl --passes

**This is the primary artifact of a run, not the scorecard.** His ruling (T45):

    "The biggest thing would just be me going through trade by trade and looking
    at the journal, looking at what the agents were thinking when it was taking
    those trades, win or loss. If I can reason with that thinking, then I would
    be happy... If we can even get it just taking the same trades, taking its own
    trades with the right thesis behind them, the right thought process, then I
    would be quite happy."

So the bar is REASONING, not R:
  - a LOSING trade with sound reasoning is a pass;
  - a WINNING trade with incoherent reasoning is a failure;
  - he does not expect the agent to match his R — "I can trade."

Output is plain prose, readable without tooling, ordered by time. Every trade
shows the standing thesis it was taken under, why this candidate, what was
rejected and how it graded, where the stop went and why, every management call,
and the outcome LAST — so the reasoning can be judged before the result is
known, which is the only way to judge reasoning at all.

Passes are hidden by default (there are many) and shown with --passes. They are
worth reading periodically: the passes are where the boundary lives.
"""
from __future__ import annotations

import argparse
import glob
import json
import re
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

HHMM = re.compile(r"(?<![\d:])([01]?\d|2[0-3]):([0-5]\d)(?!:?\d)")
W = 88


def _payload(r: dict) -> dict:
    out = dict(r)
    if isinstance(r.get("output"), dict):
        out.update(r["output"])
    return out


def _t(r: dict) -> str:
    m = HHMM.search(str(r.get("decision_minute", "")))
    return m.group(0) if m else "--:--"


def _wrap(label: str, text, indent: int = 6) -> str:
    if text in (None, "", [], {}):
        return ""
    if isinstance(text, (dict, list)):
        text = json.dumps(text, separators=(", ", ": "))
    body = textwrap.fill(str(text), width=W - indent,
                         initial_indent=" " * indent,
                         subsequent_indent=" " * (indent + 2))
    return f"{' ' * (indent - 3)}{label}\n{body}\n"


def _span(stem: str) -> str:
    """Say which CALENDAR days a session-day covers, out loud.

    The 18:00 anchor means the label is the evening the session OPENED, so
    every London and NY trade on it prints the FOLLOWING calendar day. He has
    twice scrubbed to the label's date, found different price action, and
    reasonably asked whether the replay was misconfigured. Printing the span
    costs one line and removes the whole class of confusion.
    """
    try:
        import datetime as _dt
        d0 = _dt.date.fromisoformat(stem[:10])
    except ValueError:
        return ""
    d1 = d0 + _dt.timedelta(days=1)
    return (f"  opens {d0:%a %d %b} 18:00 NY  ·  "
            f"LONDON and NY trade on {d1:%a %d %b}  ·  closes {d1:%a} 17:00")


def _level(d) -> str:
    if isinstance(d, dict):
        lv, px = d.get("level", "?"), d.get("price")
        beh = d.get("behavior") or d.get("behaviour")
        s = f"{lv}" + (f" @ {px}" if px else "")
        return s + (f" — {beh}" if beh else "")
    return str(d) if d else ""


def report(paths: list[Path], show_passes: bool) -> None:
    for p in paths:
        rows = []
        for line in p.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue

        exits = {r.get("candidate_id"): r for r in rows if r.get("row") == "exit"}
        manages = {}
        for r in rows:
            if r.get("row") in ("manage", "management") or "action" in _payload(r):
                manages.setdefault(r.get("candidate_id"), []).append(r)

        print("\n" + "=" * W)
        print(f"  {p.stem}   —   what the agents were thinking")
        print(f"  {_span(p.stem)}")
        print("=" * W)

        standing = None
        for r in rows:
            pay = _payload(r)

            # ---- thesis emissions set the context every later trade inherits
            if "bias" in pay and "decision" not in pay:
                standing = pay
                trg = pay.get("event_trigger", "window_open")
                print(f"\n  ── {_t(r)}  THESIS ({trg})"
                      f"{'  [flush]' if pay.get('flush') else ''}")
                print(f"      bias: {pay.get('bias','?')}"
                      f"{'  two-sided' if pay.get('two_sided') else ''}")
                tg = ", ".join(_level(x) for x in (pay.get("targets") or []))
                if tg:
                    print(f"      targets: {tg}")
                if pay.get("invalidation"):
                    print(f"      invalidation: {_level(pay['invalidation'])}")
                if pay.get("waiting_for"):
                    print(f"      waiting for: {pay['waiting_for']}")
                if pay.get("condition_for_other_side"):
                    print(f"      other side licensed by: "
                          f"{pay['condition_for_other_side']}")
                if pay.get("escalation_response"):
                    print(f"      [escalated re-read → {pay['escalation_response']}]")
                sys.stdout.write(_wrap("reasoning:", pay.get("reasoning")))
                continue

            dec = str(pay.get("decision", ""))
            if not dec:
                continue
            took = dec.startswith("take")
            if not took and not show_passes:
                continue

            cid = r.get("candidate_id", "?")
            head = "TOOK" if took else "PASSED"
            print(f"\n  {'─' * (W - 4)}")
            print(f"  {_t(r)}  {head}  {cid}   "
                  f"{pay.get('direction','?')}  [{dec}]"
                  f"{'  conviction ' + str(pay.get('conviction')) if pay.get('conviction') else ''}")

            if pay.get("rejected_level"):
                print(f"      rejected: {_level(pay['rejected_level'])}")
            if pay.get("levels_closed"):
                print(f"      broke: {', '.join(pay['levels_closed'])}"
                      f"   ({pay.get('pair_shape','?')})")
            sys.stdout.write(_wrap("why:", pay.get("reason")))

            if took:
                bits = []
                for k, lbl in (("entry", "entry"), ("stop", "stop")):
                    if pay.get(k) is not None:
                        bits.append(f"{lbl} {pay[k]}")
                tg = ", ".join(_level(x) for x in (pay.get("targets") or []))
                if tg:
                    bits.append(f"target {tg}")
                if bits:
                    print(f"      plan: {'  ·  '.join(bits)}")
                sys.stdout.write(_wrap("stop rationale:", pay.get("stop_rationale")))
                if pay.get("tripwire_level"):
                    print(f"      tripwire: {_level(pay['tripwire_level'])}")
            else:
                cf = pay.get("constraints_failed")
                if cf:
                    print(f"      constraints failed: {', '.join(cf)}")
            if pay.get("escalation"):
                print(f"      ↑ escalated: {_level(pay['escalation'])}")

            # ---- management calls, in order
            for mr in manages.get(cid, []):
                mp = _payload(mr)
                if "action" not in mp:
                    continue
                print(f"\n      {_t(mr)}  MANAGE → {mp['action']}"
                      f"{'  favouring: ' + mp['favouring'] if mp.get('favouring') else ''}")
                if mp.get("level_read"):
                    print(f"          at: {_level(mp['level_read'])}")
                if mp.get("new_stop") is not None:
                    print(f"          stop → {mp['new_stop']}")
                if mp.get("partial_pct"):
                    print(f"          booked {float(mp['partial_pct']) * 100:.0f}%")
                sys.stdout.write(_wrap("why:", mp.get("reason"), indent=10))

            # ---- outcome LAST, so reasoning can be judged before the result
            ex = exits.get(cid)
            if ex:
                rf, rb = ex.get("r_result"), ex.get("r_blended")
                bit = f"{rf:+.2f}R" if isinstance(rf, (int, float)) else "?"
                if isinstance(rb, (int, float)) and rb != rf:
                    bit += f"  ({rb:+.2f}R blended)"
                print(f"\n      ⟶ OUTCOME  {bit}")
                if ex.get("management_trail"):
                    sys.stdout.write(_wrap("trail:", ex["management_trail"], indent=10))
            elif took:
                print("\n      ⟶ OUTCOME  no fill")

        print()


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--passes", action="store_true",
                    help="include passed candidates (the boundary lives here)")
    a = ap.parse_args()
    paths = sorted({Path(x) for pat in a.runs for x in glob.glob(pat)})
    paths = [x for x in paths if x.is_file()]
    if not paths:
        raise SystemExit("no run files matched")
    report(paths, a.passes)
    print("  Judge the REASONING, not the R (T45). A loser you can reason with is")
    print("  a pass; a winner you cannot is a failure. Where you cannot follow the")
    print("  thinking, that is the next teaching-loop entry.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
