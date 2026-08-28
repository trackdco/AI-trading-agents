#!/usr/bin/env python3
"""OFFLINE CANDIDATE SCANNER — the orchestrator's mechanical eye, from bars.

    python -m scripts.offline_scan 2026-06-23
    python -m scripts.offline_scan 2026-06-23 --against v44   # bridge check
    python -m scripts.offline_scan 2026-06-23 --json

Runbook R2 step 2, reproduced exactly: *"A candidate exists when a 2m or 3m
candle closes through its own BB(20) MA and a second level (VWAP band / POC /
profile edge — rejection counts). Lone MA closure = pending, live for
SEQ_CANDLES = 3."*

Every candidate carries the shape vocabulary the served briefings use —
`same_candle` / `sequential`, plus the rejection-first flag — so a scanned
day is directly comparable to a day his Mac scanned.

WHY THIS IS THE PIECE THAT MATTERS. Agent quality is irrelevant if the two
paths never see the same moments: the candidate set IS the day. So this
scanner is bridge-tested against the minutes his Mac actually adjudicated,
recovered from the committed briefing corpus (filenames + decision_minute),
never from run logs — the outcome-bearing artifacts stay untouched.

WHAT A REJECTION DOES, RECOVERED FROM HIS MAC RATHER THAN ASSUMED. The
runbook's "rejection counts" first read as "a rejected level can BE the
second leg". His Mac says otherwise, and says it unambiguously: on
2026-06-23 the 3m candle closing 03:45 crossed its own MA and rejected the
daily POC, and the Mac did NOT open a candidate there — it held the MA leg
pending and paired it with the NEXT candle, which CLOSED the POC, producing
the 03:48 sequential ("own-MA leg at 03:42 (+3m)"). Its briefings say the
same in prose every time: the qualifying leg is a close, and rejections ride
along as recorded colour ("The 60m MA is recorded rejected").

So: **inside one candle the second leg must be a close-through; a
simultaneous rejection is recorded, not qualifying.** A candle REJECTS a
level when its range contains the level but it closes back on the side it
opened from — no magnitude threshold, the narrowest reading, no invented
constant. That un-thresholded geometry is mine and unratified.

REJECTION-FIRST is the third shape, and it is a SEQUENCE, not a
simultaneity — which is what the name says and what reconciles the evidence
above. Sequential runs MA-leg → second-level-close; rejection-first runs
level-rejected → own-MA-close. Both span candles, both expire after
SEQ_CANDLES. A same-candle rejection is neither, which is exactly why the
Mac passed over 03:45 and later paired it.

PENDING LEGS ARE A QUEUE, NOT A SLOT. On 2026-06-22 the Mac paired the
09:06 close with an MA leg from the 08:57 bar while a *newer* leg (09:00)
also existed, and it had already spent a same-candle candidate at 09:03.
So: forming a candidate does not extinguish other live legs, legs expire
only by age, and a pairing takes the OLDEST live leg of matching direction.
A single-slot reading loses real candidates — it lost this one.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.agent_context import volume_profile                 # noqa: E402
from scripts.offline_briefings import (SEQ_CANDLES, candle,      # noqa: E402
                                       get_bars, hist_before,
                                       session_bounds)
from src.htf_ma.levels import NY, bb_ma_asof, vwap_bands         # noqa: E402

# Runbook §3 / the served briefings' own strings. Entry cutoffs are the
# harness's business, not the scanner's: it reports every candidate in the
# window and lets the state machine apply T-rulings (09:10 NY_PRE cutoff).
WINDOWS = {"LONDON": ("03:00", "04:59"),
           "NY_PRE": ("08:00", "09:29"),
           "NY_AM": ("09:30", "11:00")}
# FULL-DAY sweep (his frequency ruling 2026-08-20: "let it trade all day.
# there is setups in asia, there is setups in london, all day every day.
# entry mechanism stays the same"). Session boxes per his v1.2 spec
# (Asia 18:00-03:00 with the 19:00 VWAP warm-up, London 03:00-09:30
# incl. pre-market, NY 09:30 to the 15:55 flatten). Used for the corpus
# export; the agent-stack windows above are untouched.
FULL_WINDOWS = {"ASIA": ("19:00", "02:59"),
                "LONDON": ("03:00", "09:29"),
                "NY": ("09:30", "15:55")}
SIGNAL_TFS = (2, 3)
# Second-leg population, pinned by certification against served
# `levels_closed_SCANNER` lists (see scripts/offline_briefings.SCANNER_LEVELS).
SECOND_LEGS = ("vwap", "vwap_p1", "vwap_p2", "vwap_p3",
               "vwap_m1", "vwap_m2", "vwap_m3",
               "daily_poc", "daily_val", "daily_vah", "bb_ma_15m", "bb_ma_60m")


def _crossed(o: float, c: float, lv: float) -> bool:
    return np.isfinite(lv) and (o - lv) * (c - lv) < 0


def _rejected(cndl: dict, lv: float) -> bool:
    """Traded through the level and closed back where it came from.

    Deliberately un-thresholded — see the module docstring. A candle that
    closes exactly at the level is not a rejection (it resolved nothing)."""
    if not np.isfinite(lv):
        return False
    if not (cndl["low"] <= lv <= cndl["high"]):
        return False
    o, c = cndl["open"], cndl["close"]
    if o == lv or c == lv:
        return False
    return (o - lv) * (c - lv) > 0


def day_levels(bars: pd.DataFrame, sess_day: str) -> dict:
    """Per-minute level series for one session-day, as-of by construction.

    Vectorised where the maths allows (VWAP, BB MAs) and one profile
    recompute per candle-close minute — the same `volume_profile` the
    certified briefing generator uses, never a second implementation."""
    t0, _ = session_bounds(sess_day, "23:00")
    t_end = t0 + pd.Timedelta(hours=23)
    hist = hist_before(bars, t0, t_end)
    if hist.empty:
        raise ValueError(f"no bars for session-day {sess_day}")
    out = {"t0": t0, "hist": hist,
           "vwap": vwap_bands(hist),
           "ma": {tf: bb_ma_asof(hist, tf)[0] for tf in (2, 3, 15, 60)}}
    return out


def levels_asof(D: dict, t: pd.Timestamp) -> dict:
    """Every second-leg level as the decision at `t` may legally see it:
    the row stamped strictly before t (the 1m bar closing AT t)."""
    v = D["vwap"]
    v = v[v.index < t]
    lv = {}
    if not v.empty:
        r = v.iloc[-1]
        for k in ("vwap", "vwap_p1", "vwap_p2", "vwap_p3",
                  "vwap_m1", "vwap_m2", "vwap_m3"):
            lv[k] = round(float(r[k]), 2)
    for tf, s in D["ma"].items():
        s = s[s.index < t]
        if not s.empty and np.isfinite(s.iloc[-1]):
            lv[f"bb_ma_{tf}m"] = round(float(s.iloc[-1]), 2)
    seg = D["hist"]
    seg = seg[(seg.index >= D["t0"]) & (seg.index < t)]
    poc, val, vah = volume_profile(seg)
    lv["daily_poc"], lv["daily_val"], lv["daily_vah"] = poc, val, vah
    return lv


def _legs(cndl: dict, lv: dict) -> tuple[list[str], list[str]]:
    """(second levels closed through, second levels rejected)."""
    closed = [n for n in SECOND_LEGS
              if n in lv and _crossed(cndl["open"], cndl["close"], lv[n])]
    rej = [n for n in SECOND_LEGS
           if n in lv and _rejected(cndl, lv[n])]
    return closed, rej


def scan_day(bars: pd.DataFrame, sess_day: str,
             windows: dict | None = None,
             rejection_first: bool = False) -> list[dict]:
    """Every candidate of one session-day, in chronological order.

    `rejection_first` is OFF by default and that is an evidence call, not
    laziness: both current-era corpora (v44 0.4.x, m1 0.4.5) reproduce at
    100% without it, while the only briefings carrying `pair_shape:
    rejection_first` come from the earliest prefix, whose whole schema
    predates the current one. Enabling it adds candidates his recent Mac
    runs did not adjudicate. Kept implemented and switchable so the question
    is his to settle, not silently decided here."""
    windows = windows or WINDOWS
    D = day_levels(bars, sess_day)
    t0 = D["t0"]

    # Live unpaired legs per TF, oldest first. `ma` = a lone own-MA close
    # awaiting a second level; `rej` = a rejected level awaiting an own-MA
    # close. Entries are (close_time, direction, label); they expire by age
    # only — never by another candidate forming (see the docstring).
    live: dict[int, dict[str, list]] = {tf: {"ma": [], "rej": []}
                                        for tf in SIGNAL_TFS}
    found: dict[pd.Timestamp, dict] = {}

    def take(tf: int, kind: str, t: pd.Timestamp, d: int):
        """Oldest live leg of this kind still inside its window, same
        direction. Expired legs are dropped as we go."""
        q = live[tf][kind]
        q[:] = [x for x in q
                if (t - x[0]).total_seconds() / 60 <= SEQ_CANDLES * tf]
        for i, (pt, pdir, label) in enumerate(q):
            if pdir == d:
                return q.pop(i), True
        return None, False

    for wname, (a, b) in windows.items():
        _, ta = session_bounds(sess_day, a)
        _, tb = session_bounds(sess_day, b)
        # walk the window minute by minute; a TF acts only on its own grid
        t = ta
        while t <= tb:
            mins = int((t - t0).total_seconds() // 60)
            for tf in SIGNAL_TFS:
                if mins % tf:
                    continue
                c = candle(bars, t, tf)
                if c is None:
                    continue
                lv = levels_asof(D, t)
                own = lv.get(f"bb_ma_{tf}m")
                if own is None:
                    continue
                own_now = _crossed(c["open"], c["close"], own)
                closed, rej = _legs(c, lv)
                d = 1 if c["close"] > c["open"] else -1

                start = f"{t - pd.Timedelta(minutes=tf):%H:%M}"
                if own_now and closed:
                    shape, tag = "same_candle", f"own_ma_{tf}m"
                elif own_now:
                    # An own-MA close ALWAYS becomes a live leg. Letting the
                    # rejection-first branch consume it instead cost two real
                    # v44 candidates (03:48, 03:58) — a leg that pairs one way
                    # must stay available to pair the other.
                    live[tf]["ma"].append((t, d, f"own_ma_{tf}m_at_{start}"))
                    if rej:
                        live[tf]["rej"].append((t, d, f"rejected_at_{start}"))
                    leg, ok = (take(tf, "rej", t, d) if rejection_first
                               else (None, False))
                    if not ok:
                        continue
                    shape, tag = "rejection_first", leg[2]
                elif closed:
                    leg, ok = take(tf, "ma", t, d)
                    if not ok:
                        if rej:
                            live[tf]["rej"].append((t, d, f"rejected_at_{start}"))
                        continue
                    shape, tag = "sequential", leg[2]
                else:
                    if rej:
                        live[tf]["rej"].append((t, d, f"rejected_at_{start}"))
                    continue

                rec = found.setdefault(t, {
                    "decision_minute": f"{t:%Y-%m-%dT%H:%M}",
                    "minute": f"{t:%H:%M}", "sess_day": sess_day,
                    "window": wname, "tfs": [], "shape": shape,
                    "direction": "UP" if d > 0 else "DOWN",
                    "own_ma_tags": [], "second_levels_closed": [],
                    "second_levels_rejected": [], "price": c["close"]})
                rec["tfs"].append(tf)
                rec["own_ma_tags"].append(tag)
                for n in closed:
                    if n not in rec["second_levels_closed"]:
                        rec["second_levels_closed"].append(n)
                for n in rej:
                    if n not in rec["second_levels_rejected"]:
                        rec["second_levels_rejected"].append(n)
                if shape == "same_candle":
                    rec["shape"] = "same_candle"      # dominates a pairing
            t += pd.Timedelta(minutes=1)
    return [found[k] for k in sorted(found)]


def briefing_minutes(prefix: str, sess_day: str) -> list[str]:
    """The minutes his Mac actually adjudicated, from the briefing corpus.

    Filenames + each briefing's own `decision_minute` — the run logs (which
    carry outcomes and are deny-listed) are never opened."""
    out = []
    for f in sorted((ROOT / "output/briefings").glob(f"{prefix}_*_trigger.json")):
        try:
            b = json.loads(f.read_text())
        except json.JSONDecodeError:
            continue
        dm = b.get("decision_minute", "").replace(" ET", "").strip()
        if "(session-day" in dm:
            dm, _, rest = dm.partition("(session-day")
            if rest.strip(" )") != sess_day:
                continue
            dm = dm.strip()
        t = pd.Timestamp(dm, tz=NY)
        if str((t - pd.Timedelta(hours=18)).date()) != sess_day:
            continue
        out.append(f"{t:%H:%M}")
    return sorted(set(out))


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("days", nargs="+", help="session-day(s), 18:00 NY anchor")
    ap.add_argument("--against", default=None, metavar="PREFIX",
                    help="bridge-check against a Mac run's briefing corpus")
    ap.add_argument("--rejection-first", action="store_true",
                    help="also scan the rejection-first shape (see scan_day)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    bars = get_bars()
    allc = {}
    for day in a.days:
        allc[day] = scan_day(bars, day, rejection_first=a.rejection_first)

    if a.json:
        print(json.dumps(allc, indent=1))
        return 0

    for day, cands in allc.items():
        print("\n" + "=" * 78)
        print(f"  OFFLINE SCAN — session-day {day}   {len(cands)} candidates")
        print("=" * 78)
        print(f"  {'minute':<8}{'win':<9}{'tf':<8}{'dir':<6}{'shape':<12}"
              f"second legs")
        for c in cands:
            legs = ",".join(c["second_levels_closed"])
            if c["second_levels_rejected"]:
                legs += f"  (rej: {','.join(c['second_levels_rejected'])})"
            print(f"  {c['minute']:<8}{c['window']:<9}"
                  f"{'+'.join(str(x) for x in c['tfs']) + 'm':<8}"
                  f"{c['direction']:<6}{c['shape']:<12}{legs}")

        if a.against:
            mac = briefing_minutes(a.against, day)
            if not mac:
                print(f"\n  no {a.against}_* trigger briefings for {day}")
                continue
            mine = [c["minute"] for c in cands]
            both = sorted(set(mac) & set(mine))
            only_mac = sorted(set(mac) - set(mine))
            only_me = sorted(set(mine) - set(mac))
            print("\n  " + "-" * 74)
            print(f"  BRIDGE CHECK vs {a.against}: "
                  f"{len(both)}/{len(mac)} of his Mac's adjudicated minutes "
                  f"reproduced ({100 * len(both) / len(mac):.0f}%)")
            if only_mac:
                print(f"    MISSED by the offline scanner ({len(only_mac)}): "
                      f"{', '.join(only_mac)}")
            if only_me:
                print(f"    EXTRA, not adjudicated on the Mac "
                      f"({len(only_me)}): {', '.join(only_me)}")
            print("    Extras are not automatically defects — a Mac window "
                  "that hit its\n    fill cap or closed a position stops "
                  "adjudicating. Misses are.")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
