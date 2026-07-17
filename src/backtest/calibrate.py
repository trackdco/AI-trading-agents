"""Spec 1 Step 8 — calibration report vs Angus's 28 February hand trades.

Matches the engine's Feb 2-27 W1/E1/V0 trades (output/trades.csv, produced by
scripts/run_backtest_feb.py) against the reference log (data/reference/feb2026_hand_log.csv)
on (date, direction, entry time ±15 min) and writes output/calibration_report.md with:

  * MATCHED  — reference trade the engine also took, side by side (entry/stop/target/R).
  * MISSED   — reference trade the engine did NOT take, with the nearest rejected trigger
               and which gate (verdict status) killed it.
  * EXTRA    — engine trade Angus did NOT take (the day-selection / detector-looseness signal).

TIME CONVENTION (critical): the hand log's "Entry Time" is the OPEN of the entry candle
(TradingView labels bars by open). The engine stamps a trigger at its candle's CLOSE. So the
engine's entry-candle open = trigger_ts − TF, and we match OPEN-to-OPEN. The ±15 min window
absorbs the human-reads-forming-candle vs robot-waits-for-close offset Angus flagged.

NO TUNING (spec-1 Step 8 / code-standards §5): this script only measures and reports. It never
changes a parameter or rule to move the numbers. Divergences are the deliverable, not a defect.

    python -m src.backtest.calibrate      # (run scripts/run_backtest_feb.py first)
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

NY = "America/New_York"
MATCH_WINDOW_MIN = 15          # spec-1 Step 8: entry time ±15 min
ROOT = Path(__file__).resolve().parents[2]
HANDLOG = ROOT / "data/reference/feb2026_hand_log.csv"
TRADES = ROOT / "output/trades.csv"
VERDICTS = ROOT / "output/verdicts.csv"
REPORT = ROOT / "output/calibration_report.md"


def _tf_minutes(tf: str) -> int:
    """'2M' | '2min' | '5 mnq'(never here) -> minutes. Defaults to 0 if unparseable."""
    s = str(tf).strip().lower().replace("min", "").replace("m", "")
    try:
        return int(float(s))
    except ValueError:
        return 0


def _parse_handlog() -> pd.DataFrame:
    h = pd.read_csv(HANDLOG)
    h.columns = [c.strip() for c in h.columns]
    rows = []
    for _, r in h.iterrows():
        d = datetime.strptime(str(r["Date"]).strip(), "%B %d, %Y").date()
        tstr = str(r["Entry Time"]).strip()
        hh, mm = (int(x) for x in tstr.split(":")[:2])
        open_ts = pd.Timestamp(f"{d} {hh:02d}:{mm:02d}", tz=NY)
        rows.append({
            "date": d, "direction": str(r["Direction"]).strip().lower(),
            "tf": str(r["Entry TF"]).strip(), "open_ts": open_ts,
            "pattern": str(r["Pattern"]).strip(),
            "r_mult": float(r["R Multiple"]), "stop_pts": float(r["Stop pts"]),
            "exit_reason": str(r["Exit Reason"]).strip(),
            "news": str(r["News Today"]).strip(),
        })
    return pd.DataFrame(rows)


def _parse_trades() -> pd.DataFrame:
    if not TRADES.exists():
        sys.exit(f"missing {TRADES} — run scripts/run_backtest_feb.py first")
    t = pd.read_csv(TRADES)
    if t.empty:
        return t
    t["trigger_ts"] = pd.to_datetime(t["trigger_ts"])
    t["date"] = t["trigger_ts"].dt.date
    t["open_ts"] = t.apply(
        lambda r: r["trigger_ts"] - pd.Timedelta(minutes=_tf_minutes(r["tf"])), axis=1)
    t["direction"] = t["direction"].str.lower()
    return t


def _parse_verdicts() -> pd.DataFrame:
    if not VERDICTS.exists():
        return pd.DataFrame(columns=["ts", "tf", "direction", "pattern", "status", "reason"])
    v = pd.read_csv(VERDICTS)
    if v.empty:
        return v
    v["ts"] = pd.to_datetime(v["ts"])
    v["date"] = v["ts"].dt.date
    v["open_ts"] = v.apply(
        lambda r: r["ts"] - pd.Timedelta(minutes=_tf_minutes(r["tf"])), axis=1)
    v["direction"] = v["direction"].str.lower()
    return v


def _within(a: pd.Timestamp, b: pd.Timestamp) -> float:
    return abs((a - b).total_seconds()) / 60.0


def calibrate() -> dict:
    hand = _parse_handlog()
    trades = _parse_trades()
    verdicts = _parse_verdicts()

    used_trades: set[int] = set()
    matched, missed = [], []

    for _, hr in hand.iterrows():
        cands = []
        if not trades.empty:
            for ti, tr in trades.iterrows():
                if ti in used_trades:
                    continue
                if tr["date"] != hr["date"] or tr["direction"] != hr["direction"]:
                    continue
                dt = _within(tr["open_ts"], hr["open_ts"])
                if dt <= MATCH_WINDOW_MIN:
                    cands.append((dt, ti, tr))
        if cands:
            cands.sort(key=lambda x: x[0])
            dt, ti, tr = cands[0]
            used_trades.add(ti)
            matched.append({"hand": hr, "engine": tr, "dt_min": dt})
        else:
            # nearest rejected trigger on this date + direction (widen a little for context)
            near = []
            if not verdicts.empty:
                vv = verdicts[(verdicts["date"] == hr["date"])
                              & (verdicts["direction"] == hr["direction"])]
                for _, vr in vv.iterrows():
                    near.append((_within(vr["open_ts"], hr["open_ts"]), vr))
            near.sort(key=lambda x: x[0])
            window_gates = {}
            for dt, vr in near:
                if dt <= MATCH_WINDOW_MIN:
                    window_gates[vr["status"]] = window_gates.get(vr["status"], 0) + 1
            missed.append({"hand": hr,
                           "nearest": near[0] if near else None,
                           "window_gates": window_gates})

    extra = [] if trades.empty else [tr for ti, tr in trades.iterrows() if ti not in used_trades]
    return {"hand": hand, "matched": matched, "missed": missed, "extra": extra,
            "n_trades": 0 if trades.empty else len(trades)}


def _fmt_engine(tr) -> str:
    return (f"{tr['tf']} {tr['pattern']} | entry {tr['entry']:.2f} stop {tr['stop_initial']:.2f} "
            f"target {tr['working_target']:.2f} | {tr['r_multiple']:+.2f}R {tr['exit_reason']}")


def write_report(res: dict) -> None:
    hand, matched, missed, extra = res["hand"], res["matched"], res["missed"], res["extra"]
    L = []
    L.append("# Spec 1 — February 2026 calibration report")
    L.append("")
    L.append("Engine run: **W1 (08:00–11:00) / E1 (limit at BB basis) / V0 (set-and-forget)**, "
             "Feb 2–27 2026, strategy-definition-v1.1.")
    L.append("")
    L.append("Match key: (date, direction, entry time ±15 min), OPEN-clock (engine trigger_ts − TF "
             "vs hand entry time). **No tuning** — divergences are reported, not fixed "
             "(spec-1 Step 8 / code-standards §5).")
    L.append("")
    L.append("| bucket | count |")
    L.append("|---|---|")
    L.append(f"| reference (hand) trades | {len(hand)} |")
    L.append(f"| engine trades | {res['n_trades']} |")
    L.append(f"| **MATCHED** | {len(matched)} |")
    L.append(f"| **MISSED** (hand took, engine didn't) | {len(missed)} |")
    L.append(f"| **EXTRA** (engine took, hand didn't) | {len(extra)} |")
    L.append("")

    # headline gate distribution across MISSED (observation only — not a fix)
    tally: dict[str, int] = {}
    for m in missed:
        if m["nearest"] is not None:
            _, vr = m["nearest"]
            if _within(vr["open_ts"], m["hand"]["open_ts"]) <= MATCH_WINDOW_MIN:
                tally[vr["status"]] = tally.get(vr["status"], 0) + 1
            else:
                tally["(no trigger in window)"] = tally.get("(no trigger in window)", 0) + 1
        else:
            tally["(no trigger at all)"] = tally.get("(no trigger at all)", 0) + 1
    L.append("## Headline patterns (observations, not fixes)")
    L.append("")
    L.append("Nearest gate on each MISSED reference trade (what stopped the engine from taking a "
             "trade Angus took):")
    L.append("")
    for k, v in sorted(tally.items(), key=lambda kv: -kv[1]):
        L.append(f"- **{k}** × {v}")
    L.append("")
    L.append("Reading (for Angus to rule, not for the engine to self-correct):")
    L.append("")
    L.append("- **`vetoed_confluence` dominates.** In several cases the engine detected the *same* "
             "trigger Angus took (same time/TF/pattern) but counted only 2 confluence types and "
             "the §7 minimum for counter-trend is 3. This collides with the v1.1 sizing ladder "
             "(§9), which treats a 2-type **BB+VWAP** cluster as *tradeable at half size*. **Do the "
             "type-ladder and the §7 count-minimum STACK (both must pass) or does the ladder "
             "SUPERSEDE the count for counter-trend?** Decision-log says the ladder \"refines §7/§9\" "
             "— needs an explicit ruling; it is the biggest single driver of MISSED.")
    L.append("- **`vetoed_halt` is a cascade.** The engine takes EXTRA early losers, trips the §10 "
             "2-loss / −2R daily halt, then MISSES Angus's later winners on the same day (Feb 12, "
             "17). Fewer EXTRA entries would remove most halt-blocks — i.e. this is downstream of "
             "the confluence/selection question, not an independent halt problem.")
    L.append("- **`vetoed_news_preopen` × Feb 20 08:06** is the tightened news rule vetoing Angus's "
             "own pre-PCE entry (open item P5.14 — strict FF-red vs named-list ruling decides it).")
    L.append("")

    L.append("## MATCHED")
    L.append("")
    if matched:
        L.append("| date | dir | Δopen | hand (TF/pat, R, exit) | engine (TF/pat, entry/stop/tgt, R, exit) |")
        L.append("|---|---|---|---|---|")
        for m in matched:
            h, e = m["hand"], m["engine"]
            L.append(f"| {h['date']} | {h['direction']} | {m['dt_min']:.0f}m "
                     f"| {h['tf']} {h['pattern']}, {h['r_mult']:+.2f}R, {h['exit_reason']} "
                     f"| {_fmt_engine(e)} |")
    else:
        L.append("_none_")
    L.append("")

    L.append("## MISSED — reference trades the engine did not take")
    L.append("")
    L.append("For each: the nearest rejected trigger (same date+direction) and which gate stopped it. "
             "`window_gates` tallies every verdict within ±15 min.")
    L.append("")
    for m in missed:
        h = m["hand"]
        L.append(f"- **{h['date']} {h['direction']} {h['tf']} {h['open_ts'].strftime('%H:%M')}** "
                 f"({h['pattern']}, {h['r_mult']:+.2f}R, {h['exit_reason']}; news={h['news']})")
        if m["nearest"] is not None:
            dt, vr = m["nearest"]
            L.append(f"  - nearest trigger: {vr['open_ts'].strftime('%H:%M')} {vr['tf']} "
                     f"{vr['pattern']} → **{vr['status']}** ({vr['reason']}) — {dt:.0f}m away")
        else:
            L.append("  - no trigger detected on this date+direction at all")
        if m["window_gates"]:
            tally = ", ".join(f"{k}×{v}" for k, v in sorted(m["window_gates"].items(),
                                                            key=lambda kv: -kv[1]))
            L.append(f"  - gates within ±15m: {tally}")
        L.append("")

    L.append("## EXTRA — engine trades Angus did not take")
    L.append("")
    if extra:
        L.append("| date | dir | open | engine (TF/pat, entry/stop/tgt, R, exit) |")
        L.append("|---|---|---|---|")
        for e in extra:
            L.append(f"| {e['date']} | {e['direction']} | {e['open_ts'].strftime('%H:%M')} "
                     f"| {_fmt_engine(e)} |")
    else:
        L.append("_none_")
    L.append("")

    L.append("## For Angus — the GATE")
    L.append("")
    L.append("Rule every MISSED and EXTRA: *\"my setup, I missed it\"* (accept the divergence) vs "
             "*\"not my setup — detector too loose\"* (tighten a rule, with an approved hypothesis + "
             "out-of-sample check + doc bump; never tuned to February).")
    L.append("")

    REPORT.write_text("\n".join(L))


def main() -> None:
    res = calibrate()
    write_report(res)
    print(f"reference {len(res['hand'])} | engine {res['n_trades']} | "
          f"MATCHED {len(res['matched'])} | MISSED {len(res['missed'])} | EXTRA {len(res['extra'])}")
    print(f"wrote {REPORT}")


if __name__ == "__main__":
    main()
