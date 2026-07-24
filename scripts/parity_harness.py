#!/usr/bin/env python3
"""PARITY HARNESS — the acceptance gate for the agent build (Angus 24-Jul).

Purpose: prove an agent-produced replay book is MECHANICALLY IDENTICAL to the validated
canon. Sit the agents at Jun-2025, feed them the same historical data, run to Jul-2026, and
diff their book against the frozen ground truth (output/baseline_book.parquet) trade-for-
trade. Exact match => the agents ARE the validated edge (not a lucky/broken look-alike).
Any diff => itemized, so it's fixed before a live order. This is what makes "one account
passed, so I'll scale" a proof instead of a gamble — it removes the single-path luck.

Compares on the natural trade key (session, day, fill-minute, direction) and asserts every
decision field matches: conviction, stop points, micros, and dollar P&L (to the cent).
Reports: MISSING (in baseline, not in candidate — agent skipped a canon trade), EXTRA (in
candidate, not in baseline — agent invented a trade), and MISMATCH (same trade, wrong
size/stop/pl — drift or a feature-definition bug).

    python -m scripts.parity_harness                      # self-test (proves it catches diffs)
    python -m scripts.parity_harness agent_replay.parquet # gate a real candidate book
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

REF = "output/baseline_book.parquet"
KEY = ["session", "day", "fillmin", "direction", "seq"]
CHECK = {"conviction": 1e-6, "risk_pts": 1e-6, "micros": 0, "pl": 0.01}  # field: abs tolerance


def load(path):
    b = pd.read_parquet(path).copy()
    b["fillmin"] = pd.to_datetime(b["fill"], utc=True).dt.floor("min")
    missing = [c for c in ["session", "day", "fillmin", "direction"] + list(CHECK) if c not in b.columns]
    if missing:
        raise ValueError(f"{path} missing required columns: {missing}")
    # disambiguate trades that share session/day/fill-minute/direction
    b = b.sort_values(["session", "day", "fillmin", "direction"])
    b["seq"] = b.groupby(["session", "day", "fillmin", "direction"]).cumcount()
    return b.set_index(KEY).sort_index()


def diff_books(ref, cand):
    """Return (n_match, discrepancies[list of (kind, key, detail)])."""
    disc = []
    rkeys, ckeys = set(ref.index), set(cand.index)
    for k in sorted(rkeys - ckeys):
        r = ref.loc[k]
        disc.append(("MISSING", k, f"canon trade absent from candidate (pl ${float(r.pl):+,.2f})"))
    for k in sorted(ckeys - rkeys):
        c = cand.loc[k]
        disc.append(("EXTRA", k, f"candidate trade not in canon (pl ${float(c.pl):+,.2f})"))
    n_match = 0
    for k in sorted(rkeys & ckeys):
        r, c = ref.loc[k], cand.loc[k]
        fld = []
        for f, tol in CHECK.items():
            rv, cv = float(r[f]), float(c[f])
            if abs(rv - cv) > tol:
                fld.append(f"{f}: canon={rv:g} agent={cv:g}")
        if fld:
            disc.append(("MISMATCH", k, "; ".join(fld)))
        else:
            n_match += 1
    return n_match, disc


def report(ref, cand, label):
    n_match, disc = diff_books(ref, cand)
    n_ref = len(ref)
    print(f"\n=== PARITY: {label} ===")
    print(f"  baseline trades: {n_ref}   candidate trades: {len(cand)}   exact matches: {n_match}")
    if not disc:
        rp, cp = float(ref.pl.sum()), float(cand.pl.sum())
        print(f"  book P&L: canon ${rp:+,.2f}  agent ${cp:+,.2f}")
        print(f"  RESULT: ✓ PASS — byte-for-byte reproduction of the canon. Cleared to proceed.")
        return True
    kinds = pd.Series([d[0] for d in disc]).value_counts().to_dict()
    print(f"  RESULT: ✗ FAIL — {len(disc)} discrepancies {kinds}")
    for kind, k, detail in disc[:25]:
        print(f"    [{kind:8s}] {k}  {detail}")
    if len(disc) > 25:
        print(f"    … and {len(disc)-25} more")
    return False


def self_test():
    """Prove the harness works: baseline vs itself must PASS; a perturbed copy must FAIL."""
    ref = load(REF)
    print("Self-test 1 — baseline vs identical copy (must PASS):")
    ok_same = report(ref, load(REF), "identical")

    # perturb: drop one trade, add a fake one, resize one, nudge one P&L
    pert = pd.read_parquet(REF).copy().reset_index(drop=True)
    pert = pert.drop(index=10)                                  # -> MISSING
    pert.loc[20, "micros"] = int(pert.loc[20, "micros"]) + 3    # -> MISMATCH (size)
    pert.loc[30, "pl"] = float(pert.loc[30, "pl"]) + 25.0       # -> MISMATCH (pl)
    fake = pert.iloc[[40]].copy(); fake["fill"] = pd.to_datetime(fake["fill"], utc=True) + pd.Timedelta(minutes=7)
    pert = pd.concat([pert, fake], ignore_index=True)           # -> EXTRA
    pert.to_parquet("/tmp/_parity_perturbed.parquet")
    p = load("/tmp/_parity_perturbed.parquet")
    print("\nSelf-test 2 — baseline vs deliberately perturbed copy (must FAIL and itemize):")
    ok_pert = report(ref, p, "perturbed")

    print("\n" + "=" * 60)
    verdict = ok_same and (not ok_pert)
    print(f"HARNESS SELF-TEST: {'✓ VALID' if verdict else '✗ BROKEN'} "
          f"(clean copy passes, perturbed copy fails)")
    return verdict


if __name__ == "__main__":
    if len(sys.argv) > 1:
        ok = report(load(REF), load(sys.argv[1]), sys.argv[1])
        sys.exit(0 if ok else 1)
    else:
        sys.exit(0 if self_test() else 1)
