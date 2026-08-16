#!/usr/bin/env python3
"""OFFLINE RE-ADJUDICATION — prepare saved briefings for a contract A/B.

    python -m scripts.readjudicate --arm amended --out <dir>

Every trigger briefing his Mac ever served is on disk, and (certified by
`scripts/certify_offline_briefings.py`, 100% exact on the current era) every
number in it is reproducible from committed bars. So a CONTRACT change can be
tested by re-running the trigger agent against those frozen briefings — no
TradingView, no replay, no supervised day.

WHAT THIS SCRIPT DOES: writes one prompt file per candidate, ready to hand to
`tv-trigger`. It does not call the agent (the harness above it does) and it
never touches run logs.

THREE ARMS, and the third is the control that makes the comparison mean
something:

  mac        the verdict actually logged on his Mac, with its screenshot.
             Historical; not re-run.
  baseline   the SAME contract, re-run offline, no screenshot.
  amended    the new contract, re-run offline, no screenshot.

`baseline` exists solely to price the missing screenshot. `amended - baseline`
is the contract effect with the screenshot difference cancelled out; a
comparison against `mac` alone would confound the two and could credit a
contract change for something the chart's absence caused.

THE SCREENSHOT NOTE IS HONEST, NOT A NUDGE. Offline prompts state plainly
that no chart image is available and that every candle, level and behaviour
block in the briefing is stated numerically and was regenerated exactly from
committed bars. It tells the agent nothing about the future, nothing about
outcome, and nothing about what to decide — and it is IDENTICAL in both
offline arms, so it cannot move the A/B.

FRESHNESS FIELDS. The amended arm's briefing gains
`level_visits_this_session` and `tests_15m_60min` for the candidate's own
rejected level, computed by `scripts.level_visits` — a mechanical fact the
orchestrator owes the contract (runbook §0c), the same standing as the T46
behaviour blocks. The baseline arm does not get them: they are part of the
change being tested.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.leak_report import LOG, WEEKS, _rows, _short_cid    # noqa: E402
from scripts.level_visits import freshness                       # noqa: E402
from scripts.offline_briefings import get_bars                   # noqa: E402

NO_CHART = (
    "NO CHART IMAGE IS AVAILABLE for this adjudication. This briefing was "
    "served with a screenshot during the original run; the image is not "
    "reachable from this environment. Every candle, level, and "
    "higher-timeframe behaviour block below is stated NUMERICALLY and was "
    "verified to reproduce exactly from committed bars. Adjudicate on the "
    "numbers. Do not refuse for the missing image, and do not treat its "
    "absence as evidence for or against the trade — say so in `reason` if it "
    "changes your confidence."
)


def collect():
    """Every logged trigger decision whose briefing is still on disk."""
    out = []
    for week in WEEKS:
        for day in WEEKS[week]:
            p = ROOT / "output/agent_runs" / LOG[week].format(d=day)
            if not p.exists():
                continue
            prior_takes: list[tuple[str, float]] = []
            for r in _rows(p):
                if r.get("row") != "trigger":
                    continue
                o = r.get("output") if isinstance(r.get("output"), dict) else {}
                dec = str(o.get("decision") or r.get("decision") or "")
                bp = r.get("briefing")
                if not bp or not (ROOT / str(bp)).exists():
                    continue
                dm = str(r.get("decision_minute", ""))
                minute = dm[-8:-3] if dm.endswith(" ET") else dm[-5:]
                rl = o.get("rejected_level") or {}
                px = rl.get("price")
                out.append({
                    "week": week[:3], "day": day,
                    "cid": _short_cid(r.get("candidate_id")),
                    "minute": minute, "logged_decision": dec,
                    "logged_conviction": str(o.get("conviction") or "?")[:1],
                    "rejected_price": px if isinstance(px, (int, float))
                    else None,
                    "briefing": str(bp),
                    "prior_takes": [x[1] for x in prior_takes]})
                if dec.startswith("take") and isinstance(px, (int, float)):
                    prior_takes.append((minute, float(px)))
    return out


def build(arm: str, outdir: Path):
    bars = get_bars()[["open", "high", "low", "close"]]
    outdir.mkdir(parents=True, exist_ok=True)
    idx = []
    for rec in collect():
        b = json.loads((ROOT / rec["briefing"]).read_text())
        b.pop("screenshot", None)
        b.pop("HOW_TO_READ_THIS_SCREENSHOT", None)
        b["chart_image"] = NO_CHART
        if arm == "amended" and rec["rejected_price"] is not None:
            b["level_visits_this_session"] = freshness(
                bars, rec["day"], rec["minute"], rec["rejected_price"],
                rec["prior_takes"])
        name = f"{rec['week']}_{rec['day']}_{rec['cid']}_{rec['minute'].replace(':','')}"
        (outdir / f"{name}.json").write_text(json.dumps(b, indent=1))
        idx.append({**{k: v for k, v in rec.items() if k != "prior_takes"},
                    "prompt_file": str(outdir / f"{name}.json"),
                    "name": name})
    (outdir / "_index.json").write_text(json.dumps(idx, indent=1))
    return idx


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arm", choices=("baseline", "amended"), required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    idx = build(a.arm, Path(a.out))
    takes = sum(1 for x in idx if x["logged_decision"].startswith("take"))
    print(f"  {a.arm}: {len(idx)} prompts written to {a.out} "
          f"({takes} logged takes, {len(idx) - takes} logged passes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
