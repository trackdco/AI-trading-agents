"""SCREEN: does the best target rise with displacement?

PREREGISTERED (written before the sweep finished, no results seen):
  A conditional target is worth BUILDING only if the target with the best
  net EV rises monotonically with the displacement bucket, and that
  ordering holds in BOTH halves with n >= 400 per half in each cell used.
  If the best target is 1.0R at every displacement level, the idea is
  dead and is logged as a kill next to the runners (S16).
  If it is worth building, ADOPT only if the in-engine conditional rule
  beats the flat-1R armed book by >= 5% drawdown-matched R/day in BOTH
  halves — the same bar as every layer before it.
EV is net of the 0.5pt/RT cost, in units of each trade's own initial
risk, so targets are directly comparable. WR is expected to FALL with
higher targets; EV is the metric, not WR.
"""
import gzip, json, sys
import numpy as np
from collections import defaultdict

C, MID = 0.5, "2024-10-21"
D = "/tmp/claude-0/-home-user-AI-trading-agents/8561fb22-7a6d-585e-9576-98688737845d/scratchpad/ql18/output/analysis/"


def load(f):
    return [json.loads(l) for l in gzip.open(D + f, "rt")]


def buck(e):
    return "<1R" if e < 1 else "1-2R" if e < 2 else "2-3R" if e < 3 else "3R+"


def screen(name, fn):
    ts = load(fn)
    tg = sorted({t["target_r"] for t in ts})
    print(f"\n{name}: {len(ts):,} trades, targets {tg}")
    agg = defaultdict(lambda: {"i": [], "o": [], "w": 0, "l": 0})
    for t in ts:
        k = (buck(t.get("excur_r", 0.0)), t["target_r"])
        a = agg[k]
        a["o" if t["day"] >= MID else "i"].append(t["r"] - C / t["risk"])
        if t["res"] == "TARGET":
            a["w"] += 1
        elif t["res"] == "STOP":
            a["l"] += 1
    print(f"  {'displacement':<14}{'target':>8}{'n':>8}{'WR':>8}{'net EV':>9}"
          f"{'IS':>9}{'OOS':>9}{'net R':>9}")
    best = {}
    for b in ("<1R", "1-2R", "2-3R", "3R+"):
        for tr in tg:
            a = agg.get((b, tr))
            if not a:
                continue
            allr = a["i"] + a["o"]
            if not allr:
                continue
            ev, i_, o_ = np.mean(allr), np.mean(a["i"] or [0]), np.mean(a["o"] or [0])
            ok = len(a["i"]) >= 400 and len(a["o"]) >= 400
            best.setdefault(b, []).append((ev, tr, i_, o_, ok))
            print(f"  {b:<14}{tr:>8.1f}{len(allr):>8,}"
                  f"{a['w']/max(a['w']+a['l'],1):>8.3f}{ev:>9.4f}{i_:>9.4f}"
                  f"{o_:>9.4f}{sum(allr):>9.0f}{'' if ok else '   (thin)'}")
        print()
    print("  best target by displacement bucket (overall / IS / OOS):")
    rows = []
    for b in ("<1R", "1-2R", "2-3R", "3R+"):
        if b not in best:
            continue
        v = best[b]
        bo = max(v, key=lambda x: x[0])[1]
        bi = max(v, key=lambda x: x[2])[1]
        bs = max(v, key=lambda x: x[3])[1]
        rows.append((b, bo, bi, bs))
        print(f"    {b:<8} {bo:>4.1f} / {bi:>4.1f} / {bs:>4.1f}")
    mono = all(rows[i][1] <= rows[i + 1][1] for i in range(len(rows) - 1))
    mono_h = (all(rows[i][2] <= rows[i + 1][2] for i in range(len(rows) - 1))
              and all(rows[i][3] <= rows[i + 1][3] for i in range(len(rows) - 1)))
    rising = rows[-1][1] > rows[0][1] if rows else False
    print(f"  -> best target non-decreasing with displacement: {mono} "
          f"(both halves: {mono_h}); strictly higher at the top bucket: {rising}")
    print(f"  -> VERDICT: {'BUILD the conditional rule' if (mono and mono_h and rising) else 'DEAD - flat 1R stands'}")


B = "pd_va_trades_lvall_xr30_sar_through_tf1_ng"
screen("UN-ARMED level book", B + "_tg.jsonl.gz")
screen("ARMED 1R level book", B + "_arm1_tg.jsonl.gz")
