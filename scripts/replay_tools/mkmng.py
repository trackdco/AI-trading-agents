"""Build one tier-3 manage briefing from a small JSON spec.

Wraps mk_manage and fills the standing extras the run spec requires: the
last_committed_1m_close reconciliation block (ONLY at odd decision minutes, where
brief04.price_at lags one committed minute), the conviction partial rule as contract
text, path_ahead, thesis_context, prior_positions_this_window, the window note and
what_to_emit. Computes crowded_path from the live levels rather than by hand.

Usage:  .venv/bin/python -m scripts.replay_tools.mkmng '<json spec>'   (or a path to it)

Spec keys: sd dn dec cid shot reason level level_price side entry stop targets(list of
  {level,price}) conviction chart_levels opened_at prior_actions original_r window
  thesis_context prior_positions
Optional: out, extra(dict merged last), window_note
"""
import sys, json, subprocess, os

ROOT = "/Users/barbelldaddy/AI-trading-agents"
PY = f"{ROOT}/.venv/bin/python"
sys.path.insert(0, ROOT)


def build(s):
    from scripts.replay_tools.brief04 import levels_at, flat_levels
    from scripts.replay_tools.htf import bars
    import pandas as pd

    dec, cid, sd, dn = s["dec"], s["cid"], s["sd"], s["dn"]
    out = s.get("out") or f"{ROOT}/output/briefings/jn1_{sd}_{cid}_{dec.replace(':','')}_manage.json"
    tg = s["targets"]
    tp1 = tg[0]["price"]
    tp2 = tg[1]["price"] if len(tg) > 1 else None

    lv = flat_levels(levels_at(sd, dn, dec))
    if tp2 is None:
        crowded = {"levels_between_tp1_and_tp2": [], "count": 0, "crowded_path": False,
                   "note": f"this position has a single target ({tp1:.2f}), so there is no "
                           "TP1-to-TP2 corridor to be crowded."}
    else:
        lo, hi = min(tp1, tp2), max(tp1, tp2)
        btw = sorted(((v, k) for k, v in lv.items() if v is not None and lo < v < hi),
                     reverse=tp1 > tp2)
        crowded = {"levels_between_tp1_and_tp2": [f"{k} {v}" for v, k in btw],
                   "count": len(btw), "crowded_path": len(btw) >= 2,
                   "note": f"named structural levels strictly between TP1 {tp1:.2f} and the "
                           f"next target {tp2:.2f} at this minute."}

    r = subprocess.run(
        [PY, "-m", "scripts.replay_tools.mk_manage", sd, dn, dec, cid, s["shot"],
         s["reason"], s["level"],
         "-" if s.get("level_price") is None else str(s["level_price"]),
         s["side"], str(s["entry"]), str(s["stop"]), json.dumps(tg), s["conviction"],
         json.dumps(s["chart_levels"]), s["opened_at"], json.dumps(crowded),
         json.dumps(s["prior_actions"]), str(s["original_r"]), out],
        capture_output=True, text=True, cwd=ROOT)
    if r.returncode:
        raise SystemExit("mk_manage failed:\n" + r.stderr[-3000:])

    # HARD GATE - a capture that fails preflight never reaches an agent.
    from scripts.replay_tools.preflight import check as _pf
    _ok, _rep = _pf(sd, s["dn"], dec, s["chart_levels"], s.get("last_bar_epoch"))
    if not _ok:
        raise SystemExit("PREFLIGHT FAILED - briefing NOT written:\n" + json.dumps(_rep, indent=1))
    b = json.load(open(out))
    short = s["side"].lower().startswith("s")
    e, R = float(s["entry"]), float(s["original_r"])

    # price_at lags one committed minute at ODD decision minutes only
    if int(dec.split(":")[1]) % 2 == 1:
        hh, mm = map(int, dec.split(":"))
        t = hh * 60 + mm - 1
        prev = f"{t//60:02d}:{t%60:02d}"
        c = float(bars().loc[pd.Timestamp(f"{dn} {prev}", tz="America/New_York")].close)
        b["last_committed_1m_close"] = {
            "minute": prev, "close": c,
            "open_pnl_in_R_on_this_price": round(((e - c) if short else (c - e)) / R, 3),
            "why": (f"{dec} is an odd decision minute, so price_at_decision above is the close of "
                    "the last COMPLETE 2m bar and lags the last committed minute by one. Both are "
                    f"stated so they reconcile. Nothing here is later than {prev}:59.")}

    b["conviction_partial_rule"] = {
        "conviction_of_this_position": s["conviction"],
        "contract_default": ("B takes roughly 75% at TP1 and trails the runner. A is 50% and holds "
                             "the rest to the full target; C is 100% out with no runner."),
        "note": ("stated as the contract text, not as an instruction - partial_pct is your decision "
                 "and is a fraction of what is still open.")}
    b["crowded_path"] = crowded
    b["thesis_context"] = s["thesis_context"]
    b["prior_positions_this_window"] = s["prior_positions"]
    if s.get("window_note"):
        b["window_note"] = s["window_note"]
    b["what_to_emit"] = "your management JSON, per your contract."
    if s.get("extra"):
        b.update(s["extra"])
    json.dump(b, open(out, "w"), indent=1)
    return out, b


if __name__ == "__main__":
    a = sys.argv[1]
    spec = json.load(open(a)) if os.path.exists(a) else json.loads(a)
    p, b = build(spec)
    print(p)
    print("price_at_decision", b["price_at_decision"],
          "| last_1m", b.get("last_committed_1m_close", {}).get("close", "n/a"),
          "| open_pnl_in_R", b["position"]["open_pnl_in_R"])
