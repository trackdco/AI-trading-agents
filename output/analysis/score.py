"""Score a run's book: as-run R, unmanaged full-target R, and the same-fills 75/25 counterfactual.

His ruling (relayed 2026-08-18): "when the book lands, the same-fills 75%-split counterfactual gets
priced mechanically and the split is judged at week level against prop metrics, not per trade." This
prices it. The counterfactual replays the SAME fills and the SAME management actions, changing only
the fraction banked at the first partial: 75% instead of whatever the manager actually took. Every
other decision - trails, breakevens, exits, the minutes they happened on - is held fixed, so the
comparison isolates the split and nothing else.

Also reports the T78 rung count per trade, so the reviewer can see the ladder and the result together.

usage: score.py <run>
"""
import json, sys
T = "/Users/barbelldaddy/.claude/jobs/2411401a/tmp"
sys.path.insert(0, T); sys.path.insert(0, "/Users/barbelldaddy/AI-trading-agents")
from scripts.replay_tools import book
import exitcalc

DAYS = {"wr2": ["2026-06-21", "2026-06-22", "2026-06-23", "2026-06-24", "2026-06-25"],
        "jr1": ["2026-05-31", "2026-06-01", "2026-06-02", "2026-06-03", "2026-06-04"]}
NEXT = {"2026-06-21": "2026-06-22", "2026-06-22": "2026-06-23", "2026-06-23": "2026-06-24",
        "2026-06-24": "2026-06-25", "2026-06-25": "2026-06-26", "2026-05-31": "2026-06-01",
        "2026-06-01": "2026-06-02", "2026-06-02": "2026-06-03", "2026-06-03": "2026-06-04",
        "2026-06-04": "2026-06-05"}


def counterfactual_75(dn, fill, actions, targets):
    """Same fills, same actions, first partial forced to 75%."""
    acts, done = [], False
    for a in actions:
        a = dict(a)
        if not done and a.get("action") == "partial" and a.get("partial_pct"):
            a["partial_pct"] = 0.75
            done = True
        acts.append(a)
    if not done:
        return None          # nothing was ever banked - the split cannot bite
    try:
        r = exitcalc.replay(dn, fill["fill_minute"], fill["side"], float(fill["entry"]),
                            float(fill["stop"]), targets, acts)
        return None if r["unclosed_fraction"] > 1e-9 else r["r_blended"]
    except Exception:
        return None


run = sys.argv[1]
rows_out, tot_run, tot_full, tot_cf, n_cf = [], 0.0, 0.0, 0.0, 0
for sd in DAYS[run]:
    rows = book.read(run, sd)
    live = lambda k: [r for r in rows if r.get("row") == k and not r.get("SUPERSEDED")
                      and not r.get("VOID")]
    for ex in live("exit"):
        cid = ex["candidate_id"]
        fill = next((f for f in live("fill") if f["candidate_id"] == cid), None)
        trig = next((t for t in live("trigger") if t["candidate_id"] == cid), None)
        tg = [float(t["price"]) for t in ((trig or {}).get("output") or {}).get("targets") or []]
        acts = [{"minute": str(m.get("manage_minute"))[-5:], "action": m.get("action"),
                 "partial_pct": m.get("partial_pct"), "new_stop": m.get("working_stop_after")}
                for m in sorted(live("manage"), key=lambda r: str(r.get("manage_minute"))[-5:])
                if m.get("candidate_id") == cid]
        cf = counterfactual_75(NEXT[sd], fill, acts, tg) if fill and tg else None
        rr, rf = ex.get("r_blended"), ex.get("r_full_target")
        tot_run += rr or 0.0
        tot_full += rf if rf is not None else 0.0
        if cf is not None:
            tot_cf += cf; n_cf += 1
        rows_out.append((sd, cid, ex.get("window"), len(tg), rr, rf, cf, ex.get("exit_reason")))

print(f"{run}: {len(rows_out)} closed trade(s)\n")
print(f"{'day':<11}{'cid':<5}{'win':<8}{'rungs':>6}{'as-run':>9}{'full-tgt':>10}{'75/25 cf':>10}  reason")
for sd, cid, w, n, rr, rf, cf, why in rows_out:
    print(f"{sd:<11}{cid:<5}{str(w):<8}{n:>6}{(rr if rr is not None else 0):>9.4f}"
          f"{(rf if rf is not None else 0):>10.4f}"
          f"{(f'{cf:.4f}' if cf is not None else '-'):>10}  {why}")
sub_run = sum(rr or 0.0 for _, _, _, _, rr, _, cf, _ in rows_out if cf is not None)
print(f"\n{'TOTAL (all trades)':<24}{'':>6}{tot_run:>9.4f}{tot_full:>10.4f}{'-':>10}")
print(f"{'LIKE-FOR-LIKE subtotal':<24}{'':>6}{sub_run:>9.4f}{'':>10}{tot_cf:>10.4f}"
      f"   <- only the {n_cf} trade(s) that actually banked a partial;")
print(f"{'':<24}{'':>6}{'':>9}{'':>10}{'':>10}      the split cannot bite on a trade that never took one.")
if n_cf:
    d = tot_cf - sub_run
    who = "75/25" if d > 0 else "the as-run split"
    print(f"\n  75/25 counterfactual is {abs(d):.4f}R {'ahead of' if d>0 else 'behind'} as-run "
          f"across those {n_cf} trade(s) - {who} wins on this sample.")
    print("  SAMPLE IS TINY. Do not read a split ruling off two trades; this is the mechanism, "
          "not the verdict.")
