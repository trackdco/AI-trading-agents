#!/usr/bin/env python3
"""Grade the completed chained-2026 Long Walk (139/139, 0 errors) on the identical
health-gate + book-resolution logic as run_v07_walk.py cmd_ingest, using the raw
per-day verdict array pulled from the Workflow's task output (chained never wrote
response.txt files — results live only in the JSON return value / journal.jsonl).

    python -m scripts.grade_chained_2026

Writes output/v07/chained2026/ledger.csv and prints the same report format as
run_v07_walk.py ingest, for direct side-by-side comparison with fresh-eyes.
"""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.run_v07_walk import champ_health_map, champ_pick  # noqa: E402

# committed raw agent verdicts (travels with repo); fall back to the original session task file
RESULT_FILE = "output/handoff/chained2026_agent_verdicts.json"
if not Path(RESULT_FILE).exists():
    RESULT_FILE = "/tmp/claude-0/-home-user-AI-trading-agents/8f4cdd65-f942-532a-87f2-c9c07c27272a/tasks/wyoz6a0lw.output"
BOOKS = "output/allyears_daily_books_r1r2.csv"
OUT = Path("output/v07/chained2026")

_BOOK = {"rotation": "ROTATION", "momentum": "MOMENTUM", "champion": "CHAMPION"}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    raw = json.loads(Path(RESULT_FILE).read_text())
    results = raw["result"]["results"]
    print(f"loaded {len(results)} chained verdicts "
          f"(total={raw['result']['total']} answered={raw['result']['answered']})")

    vec = pd.read_csv("output/regime_vector.csv")
    books = pd.read_csv(BOOKS).set_index("day")
    health_map = champ_health_map()

    stance_current = "risk_on"  # chained's own starting stance, per the workflow script
    ledger = []
    for v in results:
        d = v["date"]
        if d not in books.index:
            print(f"{d}: SKIP (not in books)")
            continue
        e3, e4 = float(books.loc[d, "E3"]), float(books.loc[d, "E4"])
        book = _BOOK.get(str(v.get("book", "champion")).lower(), "CHAMPION")
        stance_req = str(v.get("regime_stance", "risk_on")).lower()
        if stance_req not in ("risk_on", "risk_off"):
            stance_req = "risk_on"

        # IDENTICAL health gate to cmd_ingest: healthy tape overrides an unjustified risk_off
        health = health_map.get(d)
        health = health if health is not None else 0.0
        overridden = False
        if stance_req == "risk_off" and health > 0:
            stance_req = "risk_on"
            overridden = True
        stance_current = stance_req

        if stance_req == "risk_off":
            act, pl = "FLAT", 0.0
        else:
            act = champ_pick(d, vec) if book == "CHAMPION" else book
            pl = 1.0 * (e3 if act == "ROTATION" else e4)  # BINARY: full size always

        orc = max(e3, e4, 0.0)
        oracle = "FLAT" if max(e3, e4) <= 0 else ("ROTATION" if e3 >= e4 else "MOMENTUM")
        ledger.append(dict(day=d, stance=stance_req, stance_asked=v.get("regime_stance"),
                            health_override=overridden, book=book, act=act,
                            size=1.0 if act != "FLAT" else 0.0, pl=round(pl), oracle=oracle,
                            hit=act == oracle, orc=round(orc), e3=round(e3), e4=round(e4)))

    L = pd.DataFrame(ledger)
    L.to_csv(OUT / "ledger.csv", index=False)
    if len(L):
        L["y"] = L.day.str[:4]
        ceil = L.orc.sum()
        print(f"\n=== v0.7 CHAINED [2026] {len(L)} days ===")
        for y, g in L.groupby("y"):
            c = g.orc.sum()
            print(f"  {y}: ${g.pl.sum():+,.0f} = {g.pl.sum()/c*100:.0f}%  reads {g.hit.mean()*100:.0f}%  "
                  f"flat {(g.act=='FLAT').mean()*100:.0f}%  risk_off {(g.stance=='risk_off').mean()*100:.0f}%  "
                  f"health_override {(g.health_override).mean()*100:.0f}%")
        print(f"  ALL: ${L.pl.sum():+,.0f} = {L.pl.sum()/ceil*100:.0f}% of ${ceil:,.0f}")


if __name__ == "__main__":
    main()
