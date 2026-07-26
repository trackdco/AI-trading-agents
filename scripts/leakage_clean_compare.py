#!/usr/bin/env python3
"""LEAKAGE-CLEAN RE-DERIVATION (comparison artifact — canon scripts UNCHANGED).

Builds a PARALLEL book that swaps the pre-window C check's `conf_PM` (whole PM window
08:00-09:30, a lookahead for pre fills — see docs/FINDING-conf_PM-lookahead-pre-window.md) for
`pm_sofar_conf` (PM CVD truncated AT fill, leakage-clean). It does NOT modify canon_mechanical
or the thresholds: it reuses build_canon()/size_book() verbatim and overrides only the value of
the `conf_PM` column fed in — the single place build_canon reads it (canon_mechanical.py:76).

Reports total P&L vs the +$56,065.18 anchor, trade counts, how many trades change, the
score-ladder (3/4/5) shift, and the NY vs London split. Writes output/leakage_clean_report.md.

    python -m scripts.leakage_clean_compare
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.baseline_dollar_risk import size_book          # noqa: E402
from scripts.canon_mechanical import build_canon            # noqa: E402

ANCHOR = 56_065.18


def _sized_book(ny_canon: pd.DataFrame, lon: pd.DataFrame) -> pd.DataFrame:
    """The dollar-risk sized book exactly as baseline_dollar_risk.main() builds it."""
    b = pd.concat([size_book(ny_canon, "NY"), size_book(lon, "LONDON")], ignore_index=True)
    return b.sort_values("fill").reset_index(drop=True)


def _key(df: pd.DataFrame) -> pd.Series:
    fill = pd.to_datetime(df["fill"], utc=True).dt.strftime("%Y-%m-%d %H:%M")
    return df["day"].astype(str) + "|" + fill + "|" + df["direction"]


def main() -> None:
    T = pd.read_parquet("output/trade_matrix.parquet")
    lon = pd.read_parquet("output/london_canon_book.parquet")

    base_ny = build_canon(T.copy())                          # leaky baseline (== canon_book)
    T_clean = T.copy()
    T_clean["conf_PM"] = T_clean["pm_sofar_conf"]            # ONLY swap: pre-window C source
    clean_ny = build_canon(T_clean)

    base = _sized_book(base_ny, lon)
    clean = _sized_book(clean_ny, lon)

    def stats(book, ny_canon):
        taken = book                                          # size_book already keeps size>0
        ny = taken[taken.session == "NY"]
        lo = taken[taken.session == "LONDON"]
        # score-ladder counts on the NY taken canon rows (score 3/4/5 -> size 0.5/1/1.5)
        nyc = ny_canon[ny_canon["size"] > 0]
        ladder = {int(s): int((nyc.score == s).sum()) for s in (3, 4, 5)}
        return dict(pl=taken.pl.sum(), n=len(taken), ny_pl=ny.pl.sum(), n_ny=len(ny),
                    lon_pl=lo.pl.sum(), n_lon=len(lo), ladder=ladder)

    sb, sc = stats(base, base_ny), stats(clean, clean_ny)

    bk, ck = _key(base), _key(clean)
    base_k = dict(zip(bk, zip(base.micros, base.pl.round(2))))
    clean_k = dict(zip(ck, zip(clean.micros, clean.pl.round(2))))
    dropped = [k for k in base_k if k not in clean_k]          # in base, gone in clean
    added = [k for k in clean_k if k not in base_k]            # new in clean
    changed = [k for k in base_k if k in clean_k and base_k[k] != clean_k[k]]  # size/pl differ
    of_400_changed = len(dropped) + len(changed)

    lines = [
        "# Leakage-clean re-derivation — pm_sofar_conf vs conf_PM (pre-window C)", "",
        f"Canon scripts UNCHANGED; only the pre-window C source is swapped. Anchor = +${ANCHOR:,.2f}.",
        "",
        "| metric | baseline (leaky conf_PM) | clean (pm_sofar_conf) | delta |",
        "|---|---|---|---|",
        f"| total P&L | ${sb['pl']:+,.2f} | ${sc['pl']:+,.2f} | ${sc['pl']-sb['pl']:+,.2f} |",
        f"| trades (size>0) | {sb['n']} | {sc['n']} | {sc['n']-sb['n']:+d} |",
        f"| NY P&L / trades | ${sb['ny_pl']:+,.0f} / {sb['n_ny']} | ${sc['ny_pl']:+,.0f} / {sc['n_ny']} "
        f"| ${sc['ny_pl']-sb['ny_pl']:+,.0f} / {sc['n_ny']-sb['n_ny']:+d} |",
        f"| London P&L / trades | ${sb['lon_pl']:+,.0f} / {sb['n_lon']} | ${sc['lon_pl']:+,.0f} / {sc['n_lon']} "
        f"| ${sc['lon_pl']-sb['lon_pl']:+,.0f} / {sc['n_lon']-sb['n_lon']:+d} |",
        f"| NY score-ladder 3/4/5 | {sb['ladder']} | {sc['ladder']} | — |",
        "",
        f"**Trades that change vs the {sb['n']}-trade baseline:** {of_400_changed} "
        f"(dropped {len(dropped)}, size/PL-changed {len(changed)}); {len(added)} new appear.",
        f"Baseline reproduces the anchor: ${sb['pl']:+,.2f} vs +${ANCHOR:,.2f} "
        f"(delta ${sb['pl']-ANCHOR:+,.2f} — should be ~0).",
        "",
        "London is unaffected by construction (no conf_PM); all change is in the NY pre window.",
    ]
    out = Path("output/leakage_clean_report.md")
    out.write_text("\n".join(lines) + "\n")
    clean.to_parquet("output/baseline_book_clean.parquet")
    print("\n".join(lines))
    print(f"\nwrote {out} and output/baseline_book_clean.parquet")


if __name__ == "__main__":
    main()
