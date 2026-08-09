#!/usr/bin/env python3
"""Corrected "minimal frozen spec" build — everything GENUINELY IMPLEMENTED, not the 5 literal
STRUCTURAL-LEVELS-AUDIT.md rows. Supersedes minimal_frozen_spec_build.py per Angus's correction.

"Everything genuinely implemented" turns out to require NO restriction of lv/menu at all: every
one of the 7 (now 5, post-errata) newly-surfaced absences in STRUCTURAL-LEVELS-AUDIT.md was
already absent from spec_current.py / invariants_2b.py's lv/menu construction — there is nothing
extra in that construction to drop. So this script reuses invariants_2b._instrumented() UNCHANGED
(imported directly, not hand-copied — the ±3σ mislabeling in the prior audit came from
hand-transcribing the level lists into prose; importing the real function eliminates that risk
entirely) and changes ONLY the fill/admission step, from invariants_2b._admit's unconditional
next-open fill to true single-bar limit-order fill (declared, not inherited from
PREREGISTRATION.md 4.2): fills at the limit or better if the very next bar's range reaches it,
no trade at all otherwise.

No outcome is computed. Exit resolution gates one-at-a-time re-entry only, exactly as
invariants_2b._admit already does, and is never stored as a win/loss label.
"""
from __future__ import annotations

import sys
sys.path = [p for p in sys.path if p != "/usr/lib/python3/dist-packages"]

import collections
import json
from pathlib import Path

from vwapbb_signals import build_sessions, minute_of_day
from vwapbb_opportunity import assert_workbench, WORKBENCH_END
from vwapbb_a7_selector import tie_break, MAX_TRADES_DAY
from stage2_smoke import contract_key, EOD_FLATTEN
import invariants_2b as I2B

OUT = Path(__file__).resolve().parents[2] / "vwap-bb" / "data" / "implemented_levels_limit_fill.json"


def _admit_limit(bars, cands, d, syms, stats):
    """Same one-at-a-time / MAX_TRADES_DAY structure as invariants_2b._admit; only the fill
    step differs (true single-bar limit-or-better fill instead of unconditional next-open)."""
    idxs = sorted(bars)
    pending, pos, n_adm = None, None, 0
    out = []
    for j in idxs:
        o, h, l, c, v = bars[j]
        mj = minute_of_day(j)
        if pending is not None and pos is None:
            if mj >= EOD_FLATTEN:
                pending = None
            else:
                w, pending = pending, None
                stats["candidates_seen"] += 1
                if w["direction"] == "long":
                    reaches = (l <= w["entry"])
                    fill_px = min(o, w["entry"])
                else:
                    reaches = (h >= w["entry"])
                    fill_px = max(o, w["entry"])
                if reaches:
                    stats["filled"] += 1
                    pos = {**w, "fill_px": fill_px, "fill_min": mj, "fill_bar": j}
                    n_adm += 1
                else:
                    stats["no_fill"] += 1
        if pos is not None:
            if mj >= EOD_FLATTEN:
                rel = True
            elif pos["direction"] == "long":
                rel = (l <= pos["stop_px"]) or (h >= pos["tgt_px"])
            else:
                rel = (h >= pos["stop_px"]) or (l <= pos["tgt_px"])
            if rel:
                out.append({**pos, "release_min": mj, "release_bar": j,
                            "session_date": d, "symbols": syms})
                pos = None
        if pos is None and pending is None and n_adm < MAX_TRADES_DAY:
            g = cands.get(mj + 1)
            if g:
                win, lvl = tie_break(g)
                if win is not None:
                    pending = {**win, "lvl": lvl, "n_at_minute": len(g)}
    if pos is not None:
        out.append({**pos, "release_min": None, "release_bar": None,
                    "session_date": d, "symbols": syms})
    return out


def main():
    sess, sym_of = build_sessions()
    days = [d for d in sorted(sess) if d <= WORKBENCH_END]
    for d in days:
        assert_workbench(d)
    rolls, prev = set(), None
    for d in days:
        s = sorted(sym_of[d], key=contract_key)[-1]
        if prev and contract_key(s) > contract_key(prev):
            rolls.add(d)
        prev = s
    after = {days[i + 1] for i, d in enumerate(days) if d in rolls and i + 1 < len(days)}

    trades, prev_hl, processed = [], None, 0
    excl = collections.Counter()
    stats = collections.Counter()
    for d in days:
        bars = sess[d]
        this_hl = (max(x[1] for x in bars.values()), min(x[2] for x in bars.values()))
        if d in rolls:
            excl["roll session"] += 1
            prev_hl = None
        elif d in after:
            excl["session after roll"] += 1
        elif len(sym_of[d]) > 1:
            excl["mixed contract"] += 1
        else:
            cands = I2B._instrumented(bars, prev_hl)          # UNCHANGED, imported not copied
            if cands is None:
                excl["holiday / short session"] += 1
            else:
                processed += 1
                for t in _admit_limit(bars, cands, d, sorted(sym_of[d]), stats):
                    trades.append(t)
        if d not in rolls:
            prev_hl = this_hl

    n = len(trades)
    report = {
        "n_trades_admitted_and_filled": n,
        "comparison_baseline_661": 661,
        "clears_661": n >= 661,
        "candidates_seen_at_fill_decision": stats["candidates_seen"],
        "filled": stats["filled"],
        "no_fill_bar_never_reached_limit": stats["no_fill"],
        "sessions_processed": processed,
        "sessions_excluded": dict(excl),
        "workbench_days_total": len(days),
    }
    print("=" * 92)
    print("EVERYTHING GENUINELY IMPLEMENTED + true-limit fill (corrected 'minimal' build)")
    print("=" * 92)
    print(f"workbench sessions {len(days)}   processed {processed}   excluded {dict(excl)}")
    print()
    print(f"candidates reaching the fill decision : {stats['candidates_seen']}")
    print(f"  filled (bar reached the limit)      : {stats['filled']}")
    print(f"  NOT filled (bar never reached it)   : {stats['no_fill']}")
    print()
    print(f"ADMITTED-AND-FILLED TRADE COUNT: {n}")
    print(f"clears 661? {'YES' if n >= 661 else 'NO'}  ({n} vs 661)")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=1))
    print(f"\nwritten {OUT}")


if __name__ == "__main__":
    main()
