#!/usr/bin/env python3
"""Build the elicitation label deck — historical setups for his take/skip calls.

    python -m scripts.build_label_deck

Elicitation, not introspection: each card is a real scanner candidate at a
real minute. He pulls the moment up in TradingView replay (the card gives
the exact calendar date/time), looks at the chart AS OF that minute, and
fills two columns: `call` (take / skip) and `why` (free text, short).

Deck design:
  - stratified, not random: Monday opens (the burning question), CHOP-state
    candidates (the map), fresh-extreme vs hammered zones (the freshness
    fork), and a background sample;
  - recent regime only (2025-09 onward) so the chart reads like the market
    he trades;
  - reserved tapes (agent-run weeks) EXCLUDED so his labels stay blind;
  - NO outcome fields on the card. He labels the setup, not the result.

Output: output/labels/deck_001.csv (+ a .jsonl mirror with full features
for the extraction step). Labels go straight into the csv; the extractor
joins on card_id.
"""
from __future__ import annotations

import csv
import gzip
import json
import random
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

RECENT = "2025-09-01"
SEED = 20260820
PER = {"monday_open": 50, "chop": 40, "fresh_extreme": 30, "hammered": 30,
       "background": 50}


def tv_datetime(sess_day: str, minute: str) -> str:
    """The CALENDAR datetime to punch into TV replay (sessions anchor 18:00,
    so an 03:12 minute belongs to the following calendar day)."""
    ts = pd.Timestamp(f"{sess_day} {minute}")
    if ts.hour < 17:
        ts = ts + pd.Timedelta(days=1)
    return f"{ts:%Y-%m-%d %H:%M} ET"


def main() -> int:
    src = ROOT / "output/analysis/candidate_corpus_enriched.jsonl.gz"
    rows = [json.loads(l) for l in gzip.open(src, "rt")]
    pool = [r for r in rows
            if r["sess_day"] >= RECENT and not r["reserved"]
            and r.get("window") in ("LONDON", "NY_AM")]
    rng = random.Random(SEED)

    strata = {
        "monday_open": [r for r in pool if r["dow"] == 6],
        "chop": [r for r in pool if r.get("chop_state") == "CHOP"],
        "fresh_extreme": [r for r in pool if r.get("zone_touches_session", 99) <= 1],
        "hammered": [r for r in pool if r.get("zone_touches_session", 0) >= 9],
        "background": pool,
    }
    deck, seen = [], set()
    for name, cand in strata.items():
        rng.shuffle(cand)
        n = 0
        for r in cand:
            key = (r["sess_day"], r["minute"])
            if key in seen:
                continue
            seen.add(key)
            deck.append((name, r))
            n += 1
            if n >= PER[name]:
                break
    rng.shuffle(deck)

    out = ROOT / "output/labels"
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "deck_001.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["card_id", "tv_replay_datetime", "window", "direction",
                    "shape", "trigger_price", "second_legs", "call(take/skip)",
                    "why"])
        for i, (name, r) in enumerate(deck, 1):
            legs = ",".join((r.get("second_levels_closed") or [])
                            + (r.get("second_levels_rejected") or []))
            w.writerow([f"C{i:03d}", tv_datetime(r["sess_day"], r["minute"]),
                        r["window"], r["direction"], r["shape"],
                        r.get("price"), legs, "", ""])
    with gzip.open(out / "deck_001_features.jsonl.gz", "wt") as fh:
        for i, (name, r) in enumerate(deck, 1):
            fh.write(json.dumps({"card_id": f"C{i:03d}", "stratum": name, **r}) + "\n")
    print(f"deck: {len(deck)} cards -> {out/'deck_001.csv'}")
    for name in PER:
        print(f"  {name:14} {sum(1 for s, _ in deck if s == name):>3}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
