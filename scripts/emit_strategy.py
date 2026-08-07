#!/usr/bin/env python3
"""EMISSION REFERENCE IMPLEMENTATION — docs/CONTRACT-strategy-emission.md, v0.1-proposed.

Emits the two existing books through the contract interface, exactly per the worked
examples (§6 NY canon, §7 old London): one parquet of taken trades per strategy per
span + one manifest YAML, at output/emission_{strategy}_{span}.parquet /
.manifest.yaml. This is the executable form of the contract — Brake's 30-minute
ratification conversation happens against this, and every future candidate that
emits this shape gets the correlation battery and all selector baselines for the
cost of two files.

Emitted today:
  ny_canon    fit + holdout   (funded lucid accounting; the holdout twin is free —
                               the sealed-span book already exists as the certified
                               +$48,211 reference, so emitting it spends nothing)
  london_old  fit only        (research-native sizing, contract §7 gaps declared in
                               the manifest; NO holdout — building that book is a
                               declared ledger look, docs/VALIDATION-PROCESS.md §4)

exit_reason law (§6): overlay-hit rows take cr_exit_reason from
output/aikido_cr_{span}.parquet joined on ts+direction — funded_book.load_book
merges the overlay's dollars/exit_ts/exit_price but NOT cr_exit_reason, so the book
column alone leaves stale V8 reasons on the flipped rows (102 of 762, fit).

--check verifies every emission on disk against its manifest counts (drift check:
rows, days, span_days, net_pl recomputed from the parquet) and proves interface
parity: day-level P&L from the fit emissions must equal the correlation battery's
committed series (output/correlation_daily_ny_london.parquet) exactly.

    python -m scripts.emit_strategy            # emit all + check
    python -m scripts.emit_strategy --check    # check existing emissions only
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.funded_book import load_book, run  # noqa: E402

SCHEMA = "emission-v0.1-proposed"
REQUIRED = ["strategy", "day", "ts", "direction", "fill_ts", "exit_ts", "entry",
            "stop", "exit_price", "exit_reason", "risk_pts", "qty_mnq",
            "risk_dollars", "pl", "sess", "conviction"]


def _head_commit() -> str:
    r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True,
                       text=True, cwd=ROOT)
    return r.stdout.strip() or "unknown"


def emit_ny(span: str) -> tuple[pd.DataFrame, dict]:
    V = load_book(span)
    B = run(V, "lucid")
    Vi = V.set_index("ts")
    # exit_reason: cr_exit_reason on overlay-hit rows (contract §6 — load_book does
    # not merge it), book V8 reason otherwise
    O = pd.read_parquet(ROOT / f"output/aikido_cr_{span}.parquet")
    O = O[~O.cr_suppressed].set_index(["ts", "direction"])
    idx = pd.MultiIndex.from_arrays([Vi.loc[B.ts].index, Vi.loc[B.ts, "direction"]])
    reason = Vi.loc[B.ts, "exit_reason"].to_numpy(object)
    hit = idx.isin(O.index)
    reason[hit] = O.loc[idx[hit], "cr_exit_reason"].to_numpy(object)
    E = pd.DataFrame({
        "strategy": "ny_canon", "day": B.day.to_numpy(),
        "ts": B.ts.to_numpy(), "direction": Vi.loc[B.ts, "direction"].to_numpy(),
        "fill_ts": Vi.loc[B.ts, "fill_ts"].to_numpy(),
        "exit_ts": Vi.loc[B.ts, "exit_ts"].to_numpy(),   # overlay-applied by load_book
        "entry": Vi.loc[B.ts, "entry"].to_numpy(float),
        "stop": Vi.loc[B.ts, "stop"].to_numpy(float),
        "exit_price": Vi.loc[B.ts, "exit_price"].to_numpy(float),
        "exit_reason": reason,
        "risk_pts": Vi.loc[B.ts, "risk"].to_numpy(float),
        "qty_mnq": B.micros.to_numpy(int),
        "risk_dollars": B.risk_d.to_numpy(float),
        "pl": B.pl.to_numpy(float),
        "sess": B.sess.map({"pre": "ny-pre", "gold": "ny-gold"}).to_numpy(),
        "conviction": B.tier.to_numpy(float),
    })
    ref = {"fit": "+$82,543", "holdout": "+$48,211"}[span]
    man = {
        "schema": SCHEMA, "strategy": "ny_canon", "vault_id": "strategy:ny-canon",
        "span": span, "key": ["strategy", "ts", "direction"],
        "sessions": ["ny-pre", "ny-gold"],
        "session_window": "pre 08:00-09:30 ET, gold 09:40-10:30 ET "
                          "(src/canon/scorer_ny.py PRE_WIN/GOLD_WIN)",
        "signal_ts_is_fill": False,
        "mechanism_families": ["depth-walls", "overnight-structure", "order-flow",
                               "vwap", "trigger-density", "structural-events"],
        "input_columns": ["dep_wall_below_d", "WALLSZ", "on_extreme_age",
                          "fill_delta_conf", "d15_conf", "bp5opp", "lon_slope_d",
                          "ent_vs_vwap_sd_dir", "trigdens_30", "struct_event"],
        "sizing_regime": "funded-governed (profile lucid, base 160, budget 853.33)",
        "execution_semantics": {"two_sessions": True, "close_reverse": True,
                                "one_per_level": True},
        "commission_included": True,
        "exit_reason_vocab": sorted(set(E.exit_reason)),
        "counts": {"rows": int(len(E)), "days": int(E.day.nunique()),
                   "span_days": f"{E.day.min()}..{E.day.max()}",
                   "net_pl": int(round(E.pl.sum()))},
        "provenance": {
            "commit": _head_commit(),
            "book": {"generator": "scripts/funded_book.py",
                     "artifact": f"output/funded_book_lucid_{span}.parquet",
                     "span": span, "profile": "lucid", "base": 160, "overlay": "cr"},
            "reproduce": f"python -m scripts.funded_book --span {span} --profile lucid",
            "expected": ref, "holdout_looks_spent": 0,
        },
    }
    return E, man


def emit_london() -> tuple[pd.DataFrame, dict]:
    L = pd.read_parquet(ROOT / "output/london_canon_book.parquet")
    L = L[L["size"] > 0].copy()
    E = pd.DataFrame({
        "strategy": "london_old", "day": L.day.to_numpy(),
        "ts": L.fill.to_numpy(),          # [GAP — waiver] no trigger stamp, ts := fill
        "direction": L.direction.to_numpy(),
        "fill_ts": L.fill.to_numpy(), "exit_ts": L["exit"].to_numpy(),
        "entry": L.entry.to_numpy(float), "stop": L.stop.to_numpy(float),
        "exit_price": L.exit_price.to_numpy(float),
        "exit_reason": L.exit_reason.to_numpy(object),
        "risk_pts": L.risk.to_numpy(float),
        "qty_mnq": (L["size"] * 10).to_numpy(float),
        "risk_dollars": (L.risk * 20.0 * L["size"]).to_numpy(float),
        "pl": L.pl.to_numpy(float),
        "sess": "london", "conviction": L["size"].to_numpy(float),
        "pattern": L.pattern.to_numpy(object), "tf": L.tf.to_numpy(object),
    })
    man = {
        "schema": SCHEMA, "strategy": "london_old",
        "vault_id": "strategy:london-old-book", "span": "fit",
        "key": ["strategy", "ts", "direction", "entry"],
        "sessions": ["london"],
        "session_window": "08:00-10:00 Europe/London -> ET per-day via "
                          "scripts.run_triggers_london.london_window_et "
                          "(03:00-05:00 or 04:00-06:00 ET; never hardcode)",
        "signal_ts_is_fill": True,
        "mechanism_families": ["depth-walls", "overnight-structure", "order-flow",
                               "pattern-taxonomy"],
        "input_columns": ["dep_wall_below_d", "dep_wall_above_d", "ent_on_pos",
                          "on_range", "cvd_ASIA", "pattern", "score"],
        "sizing_regime": "research-native (Layer-2 size 0.5/1.0/1.5; NOT budget-governed)",
        "execution_semantics": "none",
        "commission_included": "[OPEN — needs Brake]",
        "exit_reason_vocab": sorted(set(E.exit_reason)),
        "counts": {"rows": int(len(E)), "days": int(E.day.nunique()),
                   "span_days": f"{E.day.min()}..{E.day.max()}",
                   "net_pl": int(round(E.pl.sum()))},
        "provenance": {
            "commit": _head_commit(),
            "book": {"generator": "scripts/london_canon.py",
                     "artifact": "output/london_canon_book.parquet",
                     "span": "fit", "profile": "native", "base": "n/a",
                     "overlay": "none"},
            "reproduce": "python -m scripts.london_canon",
            "expected": "136 taken, net +$35,219", "holdout_looks_spent": 0,
        },
    }
    return E, man


def write(E: pd.DataFrame, man: dict) -> None:
    stem = ROOT / f"output/emission_{man['strategy']}_{man['span']}"
    missing = [c for c in REQUIRED if c not in E.columns]
    assert not missing, f"contract violation — missing required columns {missing}"
    key = man["key"]
    assert not E.duplicated(subset=key).any(), f"key {key} not unique"
    E.to_parquet(f"{stem}.parquet", index=False)
    Path(f"{stem}.manifest.yaml").write_text(
        yaml.safe_dump(man, sort_keys=False, allow_unicode=True, width=100))
    print(f"wrote {Path(stem).name}.parquet ({len(E)} rows) + manifest")


def check() -> bool:
    ok = True
    for mp in sorted(ROOT.glob("output/emission_*.manifest.yaml")):
        man = yaml.safe_load(mp.read_text())
        E = pd.read_parquet(mp.with_name(mp.name.replace(".manifest.yaml", ".parquet")))
        got = {"rows": len(E), "days": E.day.nunique(),
               "span_days": f"{E.day.min()}..{E.day.max()}",
               "net_pl": int(round(E.pl.sum()))}
        drift = {k: (v, man["counts"][k]) for k, v in got.items()
                 if v != man["counts"][k]}
        vocab = set(E.exit_reason) - set(man["exit_reason_vocab"])
        status = "OK" if not drift and not vocab else f"DRIFT {drift or ''}{vocab or ''}"
        ok &= status == "OK"
        print(f"  {mp.name}: {status}")
    # interface parity: day P&L via the contract == the battery's committed series
    ref = pd.read_parquet(ROOT / "output/correlation_daily_ny_london.parquet")
    ny = pd.read_parquet(ROOT / "output/emission_ny_canon_fit.parquet").groupby("day").pl.sum()
    ldn = pd.read_parquet(ROOT / "output/emission_london_old_fit.parquet").groupby("day").pl.sum()
    lo, hi = ref.index.min(), ref.index.max()
    p_ny = ny.loc[lo:hi].equals(ref.ny.dropna())
    p_ldn = ldn.loc[lo:hi].equals(ref.ldn.dropna())
    print(f"  interface parity vs battery series: NY {'PASS' if p_ny else 'FAIL'}, "
          f"London {'PASS' if p_ldn else 'FAIL'}")
    return ok and p_ny and p_ldn


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="verify existing emissions only")
    a = ap.parse_args()
    if not a.check:
        for span in ("fit", "holdout"):
            write(*emit_ny(span))
        write(*emit_london())
    sys.exit(0 if check() else 1)


if __name__ == "__main__":
    main()
