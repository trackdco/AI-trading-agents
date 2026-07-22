#!/usr/bin/env python3
"""FOOTPRINT REVERSAL CONFIRMATION AT ENTRY (Angus 22 Jul). Dale's guide: absorption, delta
divergence and stacked imbalances predict reversals -- but ONLY at significant zones. Our LTF
reversal / HTF continuation entries fire exactly at such zones (VWAP/BB/VP). So the test is
per-TRADE, at each entry's level: do entries with footprint confirmation win more than those
without? Uses the 2026 chained trades (full detail + footprint coverage). One-period, so this is
suggestive, not out-of-fit proven -- confirming needs 2025 H2 trades reconstructed.

Patterns (guide's fixed rules, computed over the 3 minutes ending at the fill, within +/-2pt of
entry -> causal at the entry decision):
  absorption      : a minute with >=2.5x median volume AND two-sided min(B,A)/max(B,A) >= 0.7
  delta_confirm   : net delta over the window favors the trade's (reversal) direction
  imbalance_stack : >=2 stacked 300% diagonal imbalances on the trade's side near the level

    python -m scripts.eval_footprint_entries
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
NY = "America/New_York"


def load_fp_2026():
    fr = []
    for f in ("footprint_feb_mar2026", "footprint_apr2026", "footprint_may_jul2026"):
        p = Path(f"data/reference/cvd/{f}.parquet")
        if p.exists():
            fr.append(pd.read_parquet(p, columns=["ts_minute", "price", "side", "volume"]))
    d = pd.concat(fr, ignore_index=True)
    d["mi"] = d.ts_minute.dt.tz_convert(NY).dt.floor("min")
    d["sd"] = np.where(d.side == "B", d.volume, -d.volume)
    return d.sort_values("mi").set_index("mi")


def main():
    T = pd.read_csv("output/chained_trades.csv")
    T["fill"] = pd.to_datetime(T.fill_ts, utc=True).dt.tz_convert(NY).dt.floor("min")
    T["win"] = T.dollars > 0
    fp = load_fp_2026()
    # per-minute two-sidedness totals + per-day median minute volume (for absorption)
    piv = fp.groupby([fp.index, "side"]).volume.sum().unstack(fill_value=0)
    piv.columns = [str(c) for c in piv.columns]
    minute_tot = piv.sum(axis=1)
    day_med = minute_tot.groupby(minute_tot.index.strftime("%Y-%m-%d")).median()

    def imbalances_at(day_fp, direction):
        """count stacked 300% diagonal imbalances on the trade's side within the level window."""
        lv = day_fp.pivot_table(index="price", columns="side", values="volume", aggfunc="sum").fillna(0)
        lv.columns = [str(c) for c in lv.columns]
        if "A" not in lv or "B" not in lv or len(lv) < 2:
            return 0
        lv = lv.sort_index()
        prices = lv.index.values
        stack = 0; best = 0
        for i in range(1, len(prices)):
            # buy imbalance: ask at level i vs bid at level i-1 (diagonal), 3x+
            ask_i = lv["A"].iloc[i]; bid_below = lv["B"].iloc[i - 1]
            sell_i = lv["B"].iloc[i - 1]; ask_above = lv["A"].iloc[i]
            buy_imb = ask_i >= 3 * max(bid_below, 1)
            sell_imb = lv["B"].iloc[i - 1] >= 3 * max(lv["A"].iloc[i], 1)
            hit = buy_imb if direction == "long" else sell_imb
            stack = stack + 1 if hit else 0
            best = max(best, stack)
        return best

    recs = []
    for t in T.itertuples():
        w0 = t.fill - pd.Timedelta(minutes=2)          # 3 minutes ending at fill
        try:
            sl = fp.loc[w0:t.fill]                       # sorted-index slice -> fast
        except KeyError:
            recs.append((t.Index, None)); continue
        win_fp = sl[(sl.price >= t.entry - 2.0) & (sl.price <= t.entry + 2.0)]
        if win_fp.empty:
            recs.append((t.Index, None)); continue
        day = t.fill.strftime("%Y-%m-%d")
        med = day_med.get(day, np.nan)
        # absorption
        absorp = 0
        for mi, gmi in win_fp.groupby(level=0):
            b = gmi[gmi.side == "B"].volume.sum(); a = gmi[gmi.side == "A"].volume.sum()
            tot = b + a
            twoside = min(b, a) / max(max(b, a), 1)
            if med == med and tot >= 2.5 * med and twoside >= 0.7:
                absorp = 1
        # delta confirm: net delta favors trade direction
        net = win_fp.sd.sum()
        delta_confirm = int((net > 0 and t.direction == "long") or (net < 0 and t.direction == "short"))
        # stacked imbalance on trade side
        imb = int(imbalances_at(win_fp, t.direction) >= 2)
        recs.append((t.Index, dict(absorp=absorp, delta_confirm=delta_confirm, imb=imb)))

    R = {i: d for i, d in recs}
    T["has_fp"] = T.index.map(lambda i: R.get(i) is not None)
    for k in ("absorp", "delta_confirm", "imb"):
        T[k] = T.index.map(lambda i: (R.get(i) or {}).get(k, 0))
    T["confirm_score"] = T.absorp + T.delta_confirm + T.imb
    D = T[T.has_fp].copy()

    print(f"2026 chained trades with footprint at entry: {len(D)}/{len(T)}  "
          f"base win-rate {D.win.mean()*100:.0f}%  base $/trade ${D.dollars.mean():+.0f}\n")
    print("=== win-rate & expectancy by footprint confirmation at the entry level ===")
    print(f"  {'signal':22s} {'n':>4s} {'win%':>6s} {'$/trade':>9s}   {'vs base':>8s}")
    base_w, base_e = D.win.mean(), D.dollars.mean()
    for name, mask in [
        ("absorption present", D.absorp == 1),
        ("delta confirms dir", D.delta_confirm == 1),
        ("stacked imbalance", D.imb == 1),
        ("ANY 1+ pattern", D.confirm_score >= 1),
        ("2+ patterns agree", D.confirm_score >= 2),
        ("ZERO patterns", D.confirm_score == 0),
    ]:
        s = D[mask]
        if len(s) == 0:
            print(f"  {name:22s} {0:4d}"); continue
        print(f"  {name:22s} {len(s):4d} {s.win.mean()*100:5.0f}% ${s.dollars.mean():+8.0f}   "
              f"{(s.win.mean()-base_w)*100:+6.0f}pp")
    print("\n  by score:")
    for sc in sorted(D.confirm_score.unique()):
        s = D[D.confirm_score == sc]
        print(f"    score {sc}: n={len(s):3d}  win {s.win.mean()*100:3.0f}%  ${s.dollars.mean():+6.0f}/trade  tot ${s.dollars.sum():+,.0f}")

    # signature-matched: absorption for E3/ROTATION reversals, initiation for E4/MOMENTUM displacement.
    # Every trade is an LTF reversal into HTF continuation (Angus) -> match the confirmation to the mechanic.
    D["sig_confirm"] = np.where(D.book == "ROTATION",
                                ((D.absorp == 1) | (D.delta_confirm == 1)).astype(int),   # E3: absorption/flip
                                ((D.delta_confirm == 1) | (D.imb == 1)).astype(int))       # E4: initiation
    print("\n=== signature-matched confirmation (absorption->E3, initiation->E4) ===")
    for book in ("ROTATION", "MOMENTUM"):
        b = D[D.book == book]
        for lab, mask in [("  confirmed", b.sig_confirm == 1), ("  unconfirmed", b.sig_confirm == 0)]:
            s = b[mask]
            if len(s):
                print(f"  {book:9s}{lab:13s} n={len(s):3d}  win {s.win.mean()*100:3.0f}%  "
                      f"${s.dollars.mean():+6.0f}/trade  tot ${s.dollars.sum():+,.0f}")
    allc = D[D.sig_confirm == 1]; allu = D[D.sig_confirm == 0]
    print(f"  {'ALL':9s}{'  confirmed':13s} n={len(allc):3d}  win {allc.win.mean()*100:3.0f}%  "
          f"${allc.dollars.mean():+6.0f}/trade  tot ${allc.dollars.sum():+,.0f}")
    print(f"  {'ALL':9s}{'  unconfirmed':13s} n={len(allu):3d}  win {allu.win.mean()*100:3.0f}%  "
          f"${allu.dollars.mean():+6.0f}/trade  tot ${allu.dollars.sum():+,.0f}")


if __name__ == "__main__":
    main()
