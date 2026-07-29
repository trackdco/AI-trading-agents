"""Agent-driven canon runtime — the live desk path, end to end, made testable.

This wires the desk exactly as the canon skills describe, so a parity run measures what the
AGENTS emit, not a re-run of our scripts:

    hermes-router   route each candidate to a book by the ET clock (a lookup)
    canon engine    SHELL OUT to the EXACT scripts — scripts/canon_mechanical.py (NY) and
                    scripts/london_canon.py (London). We never re-implement a check/score.
    dollar-risk sizer   Python applies baseline_dollar_risk.size_book (frozen schedule).
    file-drop       each taken trade's verdict is written atomically to a watched dir.
    canon-relay     THE AGENT: read each verdict file and emit its bytes VERBATIM.

**The structural guarantee (why the agent cannot recompute a check, score, or size):**
`relay_one` takes a verdict-file's bytes and returns `json.loads(raw)` — nothing else. It
has no access to features, matrices, thresholds, or the scorer code; it holds no market
model; it cannot size, score, or gate. Its only power is to pass bytes through unchanged.
Correctness therefore comes entirely from the exact Python canon upstream — the relay can
only preserve or corrupt, never invent. `test_canon_runtime.py` proves relay(perturbed) ==
perturbed (the relay never "fixes" a number, i.e. it never computes).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from datetime import time as dtime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.baseline_dollar_risk import size_book

NY = "America/New_York"

# --------------------------------------------------------------------------- hermes-router
_OPEN = dtime(8, 0)


def book_for_clock(ts_utc: pd.Timestamp, dst_misaligned: bool = False) -> str:
    """hermes-router: ET clock -> book. Pure lookup, no market input. Windows per
    docs/desk-skills/canon/hermes-router.md. `dst_misaligned` shifts London +1h."""
    et = pd.Timestamp(ts_utc).tz_convert(NY)
    m = et.hour * 60 + et.minute
    lon_lo, lon_hi = (240, 360) if dst_misaligned else (180, 300)   # 04:00-06:00 or 03:00-05:00
    if lon_lo <= m < lon_hi:
        return "LONDON"
    if 480 <= m <= 630:                                              # 08:00-10:30 ET (pre+gold)
        return "NY"
    return "NONE"


# --------------------------------------------------------------------------- canon engine
def run_canon_engine() -> tuple[pd.DataFrame, pd.DataFrame]:
    """SHELL OUT to the exact scorer scripts — no re-implementation. Returns their books."""
    for mod in ("scripts.canon_mechanical", "scripts.london_canon"):
        r = subprocess.run([sys.executable, "-m", mod], cwd=ROOT,
                           capture_output=True, text=True, check=False)
        if r.returncode != 0:
            sys.stderr.write(r.stdout[-1500:] + r.stderr[-1500:])
            raise SystemExit(f"canon engine {mod} failed (exit {r.returncode})")
    return (pd.read_parquet("output/canon_book.parquet"),
            pd.read_parquet("output/london_canon_book.parquet"))


# --------------------------------------------------------------------------- file-drop
def drop_verdicts(sized: pd.DataFrame, drop_dir: Path) -> int:
    """Write one verdict file per taken trade, IN ORDER, filename = global index — atomic
    temp+rename per the receiver.py file-drop contract. `sized` is the already-sized book in
    Python's canonical order; the index-in-filename preserves that order so the relay (which
    reads filenames sorted) reproduces it exactly. The relay never re-orders — ordering is
    Python's, not the agent's."""
    drop_dir.mkdir(parents=True, exist_ok=True)
    for i, row in enumerate(sized.itertuples(index=False)):
        rec = {
            "session": row.session, "day": str(row.day),
            "fill": pd.Timestamp(row.fill).tz_convert("UTC").isoformat(),
            "direction": row.direction, "conviction": float(row.conviction),
            "risk_pts": float(row.risk_pts), "risk_dollars": float(row.risk_dollars),
            "micros": int(row.micros), "dollars_1lot": float(row.dollars_1lot),
            "pl": float(row.pl), "yr": int(row.yr),
        }
        # Execution levels for the LIVE lane's spine intent — added only when present, so the
        # research/parity callers (baseline sizing, agent_replay) drop the exact same schema.
        for k in ("entry", "stop", "target"):
            if hasattr(row, k) and getattr(row, k) is not None:
                rec[k] = float(getattr(row, k))
        tmp = drop_dir / f".{i:05d}.json.tmp"
        final = drop_dir / f"{i:05d}.json"
        tmp.write_text(json.dumps(rec))
        os.replace(tmp, final)          # atomic — the receiver never sees a half-written file
    return len(sized)


# --------------------------------------------------------------------------- canon-relay (AGENT)
def relay_one(raw: str) -> dict:
    """THE AGENT, in full. Read a verdict file's bytes, return them parsed — unchanged.
    No feature access, no scorer, no arithmetic. It cannot recompute; it can only relay."""
    return json.loads(raw)


def relay(drop_dir: Path) -> list[dict]:
    return [relay_one((drop_dir / f).read_text())
            for f in sorted(os.listdir(drop_dir)) if f.endswith(".json")]


# --------------------------------------------------------------------------- orchestrator
def produce_agent_replay(out: str = "agent_replay_live.parquet") -> pd.DataFrame:
    ny_book, lon_book = run_canon_engine()
    # Canonical order — IDENTICAL to scripts/baseline_dollar_risk.main() (concat NY+London,
    # then sort_values("fill")). Python owns the ordering; the relay only preserves it. We do
    # NOT re-sort after the relay — a relay that reorders is a relay that computes.
    ny_sized = size_book(ny_book, "NY")
    lon_sized = size_book(lon_book, "LONDON")
    canonical = pd.concat([ny_sized, lon_sized], ignore_index=True) \
        .sort_values("fill").reset_index(drop=True)
    n_ny, n_lon = len(ny_sized), len(lon_sized)
    drop_dir = Path(tempfile.mkdtemp(prefix="verdict_drop_"))
    drop_verdicts(canonical, drop_dir)
    relayed = relay(drop_dir)                         # <- what the AGENT emits, in drop order
    book = pd.DataFrame(relayed)                      # NO re-sort — order is Python's
    book.to_parquet(out)

    # router diagnostic: does the clock lookup agree with each trade's engine session?
    et = pd.to_datetime(book["fill"], utc=True)
    routed = [book_for_clock(t) for t in et]
    agree = sum(r == s for r, s in zip(routed, book["session"]))
    print(f"engine: NY {n_ny} + London {n_lon} taken; dropped {n_ny + n_lon} verdict files; "
          f"agent relayed {len(relayed)}")
    print(f"router agreement (clock->book == engine session): {agree}/{len(book)}")
    print(f"wrote {out}: {len(book)} trades, P&L ${book.pl.sum():+,.2f}")
    return book


if __name__ == "__main__":
    produce_agent_replay(sys.argv[1] if len(sys.argv) > 1 else "agent_replay_live.parquet")
