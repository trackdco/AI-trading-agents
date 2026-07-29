#!/usr/bin/env python3
"""Winner-gap forensics (ANGUS pass-9): for each hand-log WINNER, walk the engine's actual
pipeline outcome (verdicts.csv from the current run) and attribute the miss to a mechanism:

  TAKEN       engine traded it (report engine R vs hand R)
  DETECTOR    no same-direction trigger existed within the window at all
  FILTER      nearest trigger was vetoed by a rule gate (bb_vwap / min_stop / rr_floor / ...)
  EXECUTION   trigger passed rules but the ORDER never became a position
              (tcancel / bad_geometry / no_entry_ref)
  SEQUENCING  blocked by state, not rules (halt / vault max / position open / window / news)

Hand times are TV OPEN-labeled; engine bars are CLOSE-labeled -> shift by TF, match +/-15 min.
Run scripts/run_backtest_feb.py first (needs output/verdicts.csv + output/trades.csv).
"""
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
NY = "America/New_York"
WIN = pd.Timedelta(minutes=15)

FILTER_ST = {"vetoed_bb_vwap", "vetoed_min_stop", "vetoed_rr_floor", "vetoed_confluence",
             "vetoed_no_target", "vetoed_vwap_touch"}
EXEC_ST = {"cancelled_tcancel", "vetoed_bad_geometry", "vetoed_no_entry_ref",
           "cancelled_window_end", "cancelled_eod"}
SEQ_ST = {"vetoed_halt", "vetoed_vault_max", "skipped_position_open", "skipped_order_working",
          "vetoed_window", "vetoed_news_preopen", "vetoed_vwap_warmup", "cancelled_halt"}


def tf_minutes(tf: str) -> int:
    m = re.match(r"(\d+)", str(tf).strip())
    return int(m.group(1)) if m else 1


def main():
    hand = pd.read_csv("data/reference/feb2026_hand_log.csv")
    hand.columns = [c.strip() for c in hand.columns]
    winners = hand[hand["R Multiple"] > 0].copy()

    vd = pd.read_csv("output/verdicts.csv")
    vd["ts"] = pd.to_datetime(vd["ts"])
    tr = pd.read_csv("output/trades.csv")
    tr["trigger_ts"] = pd.to_datetime(tr["trigger_ts"])

    buckets: dict[str, list] = {}
    print(f"{'hand winner':26s} {'R':>6s} | {'bucket':10s} {'nearest trigger outcome':40s}")
    print("-" * 100)
    for _, r in winners.sort_values("Date").iterrows():
        date = pd.Timestamp(r["Date"]).strftime("%Y-%m-%d")
        t_open = pd.Timestamp(f"{date} {str(r['Entry Time']).strip()}", tz=NY)
        t_close = t_open + pd.Timedelta(minutes=tf_minutes(r["Entry TF"]))
        d = str(r["Direction"]).strip().lower()

        w = vd[(vd["direction"] == d) & (vd["ts"] >= t_close - WIN) & (vd["ts"] <= t_close + WIN)]
        label = f"{date} {r['Entry Time'].strip()} {d} {r['Entry TF']}"
        hr = float(r["R Multiple"])

        if w.empty:
            bucket, det = "DETECTOR", "no same-direction trigger within ±15m"
        elif (w["status"] == "taken").any():
            # engine outcome: match trade by trigger ts among the window's taken
            taken_ts = w[w["status"] == "taken"]["ts"]
            eng = tr[tr["trigger_ts"].isin(taken_ts)]
            er = float(eng["r_multiple"].sum()) if not eng.empty else float("nan")
            bucket, det = "TAKEN", f"engine R {er:+.2f} (hand {hr:+.2f})"
        else:
            w = w.copy()
            w["dist"] = (w["ts"] - t_close).abs()
            near = w.sort_values("dist").iloc[0]
            st = near["status"]
            bucket = ("FILTER" if st in FILTER_ST else
                      "EXECUTION" if st in EXEC_ST else
                      "SEQUENCING" if st in SEQ_ST else "OTHER")
            counts = w["status"].value_counts().to_dict()
            det = f"{st} @{near['ts'].strftime('%H:%M')} {near['tf']} | window: {counts}"
        buckets.setdefault(bucket, []).append((label, hr, det))
        print(f"{label:26s} {hr:>+6.2f} | {bucket:10s} {det[:70]}")

    print()
    print("=== MECHANISM SUMMARY (hand winners only) ===")
    tot_n = len(winners)
    tot_r = winners["R Multiple"].sum()
    for b in ("TAKEN", "DETECTOR", "FILTER", "EXECUTION", "SEQUENCING", "OTHER"):
        if b not in buckets:
            continue
        n = len(buckets[b])
        rr = sum(x[1] for x in buckets[b])
        print(f"  {b:10s} {n:2d}/{tot_n} winners ({100*n/tot_n:.0f}%)  hand R at stake {rr:+.2f} ({100*rr/tot_r:.0f}%)")


if __name__ == "__main__":
    main()
