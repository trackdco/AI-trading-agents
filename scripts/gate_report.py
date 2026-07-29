#!/usr/bin/env python3
"""Promotion-gate report — emit the A/B/C/D tables as a PASS/FAIL artifact (docs/PROMOTION-GATE.md).

"The gate must be a script's output, not a human's recollection" (Angus). This reads the live
artifacts a paper run leaves on disk and evaluates every gate in PROMOTION-GATE.md, printing
the A/B/C/D tables with a per-gate status and the evidence used. It NEVER marks a gate PASS
without evidence: a gate it cannot mechanically decide from the artifacts is INCONCLUSIVE
(which blocks promotion just like a FAIL), and a gate whose threshold is still `[SET]` in the
doc is UNSET (measured value reported, awaiting Angus's ruling). Overall promotion PASSES only
when every gate is PASS.

Artifacts (all under --dir, default output/live; missing => the gates that need them go
INCONCLUSIVE, never silently pass):
  journal.jsonl    completed trades (frozen JournalRecord)          — A4/A5/A6, B1, D
  decisions.jsonl  session picks / halts / guard-trips / notes      — A4, C4/C6
  rejects.jsonl    unified RejectLedger (src/canon/gate_evidence)   — B3
  spine.jsonl      spine events (decision/placed/flatten_halt/...)  — B2/B4, C5
  feed_lag.jsonl   per-bar file-append latency (SierraFileFeed)     — B6
  sizing.jsonl     per-trade {conviction,stop_pts,micros,available_dd} (verdict-drop export) — B5
Optional references:
  --expected FILE  batch backtest trade list (parquet/jsonl) for A4 no-missed-trades

Usage:
    python scripts/gate_report.py --dir output/live [--expected output/baseline_book.parquet]
    python scripts/gate_report.py --dir output/live --out output/live/gate_report.md
Exit 0 iff overall PASS, else 1 (so CI / the launch runbook can gate on it).
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from datetime import timedelta  # noqa: E402

from src.canon.gate_evidence import check_sizing  # noqa: E402
from src.canon.sierra_symbol import front_month_symbol  # noqa: E402

PASS, FAIL, INCONCLUSIVE, UNSET = "PASS", "FAIL", "INCONCLUSIVE", "UNSET"

# Every Tier-1/2/3 spine rule C5 requires to have fired (or been force-tested) live.
REQUIRED_SPINE_RULES = {
    "dd_proximity", "daily_loss", "contract_clamp",                       # Tier 1
    "startup_parity", "feed_stale", "book_crossed", "context_incomplete",
    "spread", "order_rate", "duplicate", "limit_only", "readback_mismatch",  # Tier 2
    "fail_closed", "manual_kill", "naked_position",                       # Tier 3
}

# US Eastern DST transitions (2026–2027) for D3.
_DST_TRANSITIONS = [date(2026, 3, 8), date(2026, 11, 1), date(2027, 3, 14), date(2027, 11, 7)]


class Gate:
    __slots__ = ("id", "name", "status", "detail")

    def __init__(self, gid: str, name: str, status: str, detail: str = ""):
        self.id, self.name, self.status, self.detail = gid, name, status, detail


# --------------------------------------------------------------------------- artifact loading
def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception:  # noqa: BLE001 — a torn line is skipped, not fatal
            continue
    return rows


def load_artifacts(d: Path) -> dict:
    from src.live.journal import LiveJournal
    lj = LiveJournal(d)
    trades = lj.trades()                               # validated JournalRecords
    return {
        "trades": trades,
        "corrupt_journal_lines": lj.corrupt_journal_lines,
        "decisions": lj.decisions(),
        "rejects": _read_jsonl(d / "rejects.jsonl"),
        "spine": _read_jsonl(d / "spine.jsonl"),
        "feed_lag": _read_jsonl(d / "feed_lag.jsonl"),
        "sizing": _read_jsonl(d / "sizing.jsonl"),
    }


# --------------------------------------------------------------------------- helpers
def _spine_rules_fired(spine: list[dict]) -> set[str]:
    fired: set[str] = set()
    for e in spine:
        ev = e.get("event")
        if ev == "decision":
            if e.get("action") in ("reject", "halt", "flatten") and e.get("rule"):
                fired.add(e["rule"])
            if e.get("clamped_size") is not None:
                fired.add("contract_clamp")
        elif ev == "flatten_halt" and e.get("rule"):
            fired.add(e["rule"])
        elif ev == "naked_position":
            fired.add("naked_position")
    return fired


def _book_label(rec) -> str:
    """Classify a trade as 'london' or 'ny' from its session/playbook (A5)."""
    tag = f"{getattr(rec, 'session', None) or ''} {getattr(rec, 'playbook', None) or ''}".lower()
    return "london" if "london" in tag else "ny"


def _trade_dates(trades) -> list[date]:
    out = []
    for t in trades:
        try:
            out.append(date.fromisoformat(str(t.trade_date)[:10]))
        except Exception:  # noqa: BLE001
            continue
    return sorted(out)


# --------------------------------------------------------------------------- A. Correctness
def eval_A(a: dict, expected: list | None) -> list[Gate]:
    trades = a["trades"]
    g: list[Gate] = []

    # A1/A2/A3 need per-day parity / verdict-replay / relay-diff artifacts that only a live
    # run produces; without them we cannot assert, so INCONCLUSIVE (blocks — never a false pass).
    for gid, name in (("A1", "Feature parity holds"),
                      ("A2", "Verdict fidelity"),
                      ("A3", "Relay integrity")):
        g.append(Gate(gid, name, INCONCLUSIVE,
                      "no parity/verdict-replay/relay artifact under --dir; run the parity "
                      "harness and commit its output for this gate"))

    # A4 — no missed trades. Needs a reference expected-trade list to diff against.
    if expected is None:
        g.append(Gate("A4", "No missed trades", INCONCLUSIVE,
                      "pass --expected <batch trade list> to diff live vs canon candidates"))
    else:
        ours = {(str(t.trade_date), str(t.fill_ts)) for t in trades}
        missing = [e for e in expected if (str(e[0]), str(e[1])) not in ours]
        g.append(Gate("A4", "No missed trades", PASS if not missing else FAIL,
                      f"{len(missing)} missed of {len(expected)} expected"
                      + (f" e.g. {missing[:2]}" if missing else "")))

    # A5 — both books exercised.
    if not trades:
        g.append(Gate("A5", "Both books exercised", INCONCLUSIVE, "no trades journaled"))
    else:
        seen = {_book_label(t) for t in trades}
        g.append(Gate("A5", "Both books exercised", PASS if {"ny", "london"} <= seen else FAIL,
                      f"books seen: {sorted(seen)}"))

    # A6 — journal completeness (zero malformed/missing records).
    bad = a["corrupt_journal_lines"]
    g.append(Gate("A6", "Journal completeness", PASS if bad == 0 else FAIL,
                  f"{bad} malformed journal line(s); {len(trades)} valid trades"))
    return g


# --------------------------------------------------------------------------- B. Execution
def eval_B(a: dict) -> list[Gate]:
    trades, spine = a["trades"], a["spine"]
    g: list[Gate] = []

    # B1 — fill vs intent (slippage). Threshold is [SET]: report the number, mark UNSET.
    slips = [t.slippage_ticks for t in trades if t.slippage_ticks is not None]
    if not slips:
        g.append(Gate("B1", "Fill vs intent (slippage)", INCONCLUSIVE, "no slippage recorded"))
    else:
        med = sorted(slips)[len(slips) // 2]
        g.append(Gate("B1", "Fill vs intent (slippage)", UNSET,
                      f"median {med} ticks over {len(slips)} fills; threshold [SET] pending"))

    # B2 — no market orders (structural). Any non-limit placement is a hard FAIL.
    market = [t for t in trades if getattr(t, "entry_variant", "") == "market"]
    market += [e for e in spine if e.get("event") == "placed" and e.get("order_type") == "market"]
    g.append(Gate("B2", "No market orders", PASS if not market else FAIL,
                  "zero market orders (limit-only enforced by the spine)" if not market
                  else f"{len(market)} market order(s) seen — disqualifying"))

    # B4 — bracket integrity / zero naked positions, any duration.
    naked = [e for e in spine if e.get("event") == "naked_position"]
    naked += [e for e in spine if e.get("event") == "flatten_halt"
              and e.get("rule") in ("naked_position", "readback_mismatch")]
    if not spine:
        g.append(Gate("B4", "Bracket integrity (zero naked)", INCONCLUSIVE,
                      "no spine.jsonl — wire SpineJournalSink to evaluate"))
    else:
        g.append(Gate("B4", "Bracket integrity (zero naked)", PASS if not naked else FAIL,
                      "zero naked positions" if not naked else
                      f"{len(naked)} naked/bracket-fail event(s) — disqualifying"))

    # B5 — micros == dollar-risk schedule, every trade, exact.
    sizing = a["sizing"]
    if not sizing:
        g.append(Gate("B5", "Sizing (micros==schedule)", INCONCLUSIVE,
                      "no sizing.jsonl (export conviction/stop_pts/micros/available_dd per trade)"))
    else:
        fails = []
        for r in sizing:
            try:
                res = check_sizing(r["conviction"], r["stop_pts"], r["micros"],
                                   r.get("available_dd"))
            except Exception as e:  # noqa: BLE001 — a bad row is itself a sizing failure
                fails.append((r, str(e)))
                continue
            if not res["ok"]:
                fails.append((r, res))
        g.append(Gate("B5", "Sizing (micros==schedule)", PASS if not fails else FAIL,
                      f"{len(sizing)} trades checked, {len(fails)} off-schedule"
                      + (f" e.g. {fails[0]}" if fails else "")))

    # B6 — feed lag characterised (measured, documented as a number).
    lag = a["feed_lag"]
    vals = [r.get("lag_s") for r in lag if isinstance(r.get("lag_s"), (int, float))]
    if not vals:
        g.append(Gate("B6", "Feed lag characterised", INCONCLUSIVE,
                      "no feed_lag.jsonl — run sierra_parity_replay.py --measure-lag on a live file"))
    else:
        sv = sorted(vals)
        p95 = sv[min(len(sv) - 1, int(round(0.95 * (len(sv) - 1))))]
        g.append(Gate("B6", "Feed lag characterised", PASS,
                      f"measured n={len(vals)} median {sv[len(sv)//2]:.3f}s p95 {p95:.3f}s"))
    return g


# --------------------------------------------------------------------------- C. Operations
def eval_C(a: dict) -> list[Gate]:
    decisions, spine = a["decisions"], a["spine"]
    g: list[Gate] = []

    # C1/C2/C3 need an uptime/heartbeat/feed-guard event log; without it, INCONCLUSIVE.
    for gid, name, note in (
        ("C1", "Uptime", "no uptime/heartbeat log; threshold [SET] pending"),
        ("C2", "Restart recovery", "no restart-event marker journaled"),
        ("C3", "Feed interruption handled", "no feed_guard gap/stall event journaled"),
    ):
        g.append(Gate(gid, name, INCONCLUSIVE, note))

    # C4 — kill switch drilled live by BOTH operators. Needs the operator id on the kill event.
    kills = [d for d in decisions if d.get("type") == "halt" and d.get("reason") == "kill_switch"]
    kills += [e for e in spine if e.get("event") == "flatten_halt" and e.get("rule") == "manual_kill"]
    operators = {d.get("operator") for d in decisions
                 if d.get("type") == "halt" and d.get("reason") == "kill_switch"} - {None}
    if not kills:
        g.append(Gate("C4", "Kill switch drilled (both operators)", INCONCLUSIVE,
                      "no /kill event journaled during paper"))
    elif len(operators) >= 2:
        g.append(Gate("C4", "Kill switch drilled (both operators)", PASS,
                      f"kill drilled by {len(operators)} operators"))
    else:
        g.append(Gate("C4", "Kill switch drilled (both operators)", FAIL,
                      f"{len(kills)} kill event(s) but only {len(operators) or '0 identified'} "
                      f"distinct operator(s) — both Pat and Angus must drill /kill"))

    # C5 — every Tier-1/2/3 spine rule fired (or was force-tested) live.
    if not spine:
        g.append(Gate("C5", "Spine guards each exercised", INCONCLUSIVE,
                      "no spine.jsonl to evaluate rule coverage"))
    else:
        fired = _spine_rules_fired(spine)
        missing = sorted(REQUIRED_SPINE_RULES - fired)
        g.append(Gate("C5", "Spine guards each exercised", PASS if not missing else FAIL,
                      f"{len(fired & REQUIRED_SPINE_RULES)}/{len(REQUIRED_SPINE_RULES)} fired"
                      + (f"; missing {missing}" if missing else "")))

    # C6 — alerting: every halt and trade reached Telegram, zero silent failures.
    g.append(Gate("C6", "Alerting (zero silent failures)", INCONCLUSIVE,
                  "no alert-delivery log; expose TelegramAlerts.failures / send receipts"))
    return g


# --------------------------------------------------------------------------- D. Sample
def eval_D(a: dict) -> list[Gate]:
    trades = a["trades"]
    g: list[Gate] = []
    dts = _trade_dates(trades)
    days = sorted({d for d in dts})
    n_days, n_trades = len(days), len(trades)

    # D1/D2 thresholds are [SET] (D2 has a proposal of 25) — report the counts, mark UNSET.
    g.append(Gate("D1", "Continuous trading days", UNSET,
                  f"{n_days} distinct trading days; minimum [SET] pending"))
    g.append(Gate("D2", "Live trades", UNSET,
                  f"{n_trades} live trades; minimum [SET] (proposal 25) pending"))

    # D3 — includes a DST transition week.
    if not days:
        g.append(Gate("D3", "DST transition week", INCONCLUSIVE, "no trades journaled"))
    else:
        lo, hi = days[0], days[-1]
        hit = [t for t in _DST_TRANSITIONS if lo <= t <= hi]
        g.append(Gate("D3", "DST transition week", PASS if hit else FAIL,
                      f"window {lo}..{hi} " + (f"covers DST {hit}" if hit else "covers no DST change")))

    # D4 — includes a full weekend gap + Sunday reopen.
    if not days:
        g.append(Gate("D4", "Weekend gap + Sunday reopen", INCONCLUSIVE, "no trades journaled"))
    else:
        lo, hi = days[0], days[-1]
        has_sunday = any(d.weekday() == 6 for d in
                         [date.fromordinal(o) for o in range(lo.toordinal(), hi.toordinal() + 1)])
        g.append(Gate("D4", "Weekend gap + Sunday reopen", PASS if has_sunday else FAIL,
                      f"window {lo}..{hi} " + ("spans a weekend" if has_sunday else "spans no weekend")))
    return g


# --------------------------------------------------------------------------- E. Roll / §E
def _journaled_roll_sessions(decisions: list[dict]) -> set[str]:
    return {d.get("date") for d in decisions if d.get("type") == "roll" and d.get("date")}


def _expected_roll_sessions(days: list[date]) -> set[str]:
    """Session-dates in the trade window on which the front-month contract changes (the live
    twin of the backtest's roll days). Uses the same calendar rule as RollTagger."""
    if not days:
        return set()
    out = set()
    lo, hi = days[0], days[-1]
    for o in range(lo.toordinal(), hi.toordinal() + 1):
        d = date.fromordinal(o)
        if front_month_symbol(d) != front_month_symbol(d - timedelta(days=1)):
            out.add(str(d))
    return out


def eval_E_roll(a: dict) -> list[Gate]:
    """Contract-roll handling (§E). The backtest SPANS rolls (roll is diagnostic-only) so live
    spans too; these gates verify the roll was TAGGED (so trades can be partitioned identically)
    and surface §E's clock-reset — a roll inside the sample resets the promotion clock unless the
    rollover handling was itself the tested period."""
    trades, decisions = a["trades"], a["decisions"]
    days = sorted({d for d in _trade_dates(trades)})
    journaled = _journaled_roll_sessions(decisions)
    expected = _expected_roll_sessions(days)
    g: list[Gate] = []

    # E1 — every roll in the window was tagged/journaled (the tag_rolls twin actually fired).
    if not expected:
        g.append(Gate("E1", "Rolls tagged", INCONCLUSIVE,
                      "trade window spans no contract roll — nothing to tag yet"))
    else:
        missing = sorted(expected - journaled)
        g.append(Gate("E1", "Rolls tagged", PASS if not missing else FAIL,
                      f"expected rolls {sorted(expected)}; journaled {sorted(journaled)}"
                      + (f"; MISSING {missing} (roll not tagged)" if missing else "")))

    # E2 — §E clock-reset: trades inside a roll session force a reset (can't auto-confirm the
    # restart, so this BLOCKS until a human confirms the sample restarted across the roll).
    roll_sessions = journaled | expected
    roll_trades = [t for t in trades if str(t.trade_date) in roll_sessions]
    if not roll_sessions:
        g.append(Gate("E2", "§E clock-reset", INCONCLUSIVE, "no roll in the sample window"))
    elif not roll_trades:
        g.append(Gate("E2", "§E clock-reset", PASS,
                      f"roll session(s) {sorted(roll_sessions)} carried no trades — no reset triggered"))
    else:
        g.append(Gate("E2", "§E clock-reset", INCONCLUSIVE,
                      f"{len(roll_trades)} trade(s) in roll session(s) {sorted(roll_sessions)} — "
                      f"§E resets the clock; confirm the sample restarts after the roll"))

    # E3 — roll-timing parity: live rolls on a CALENDAR rule, the backtest on VOLUME; they must
    # roll on the same day or near-roll levels diverge. Needs the backtest roll dates to confirm.
    g.append(Gate("E3", "Roll-timing parity (calendar vs volume)", INCONCLUSIVE,
                  "provide the backtest volume-roll date(s) to confirm live calendar-roll aligns "
                  + (f"(live rolled {sorted(journaled)})" if journaled else "(no live roll yet)")))
    return g


# --------------------------------------------------------------------------- render
def _emoji(status: str) -> str:
    return {PASS: "✅", FAIL: "❌", INCONCLUSIVE: "⬜", UNSET: "⏳"}.get(status, "?")


def render(sections: dict[str, list[Gate]]) -> tuple[str, bool]:
    lines = ["# Promotion-gate report (docs/PROMOTION-GATE.md)", "",
             "Status legend: ✅ PASS · ❌ FAIL · ⬜ INCONCLUSIVE (no evidence) · "
             "⏳ UNSET ([SET] threshold pending). Promotion requires **every** gate ✅.", ""]
    all_pass = True
    titles = {"A": "A. Correctness", "B": "B. Execution", "C": "C. Operations",
              "D": "D. Sample", "E": "E. Roll / clock-reset"}
    for sec in ("A", "B", "C", "D", "E"):
        lines += [f"## {titles[sec]}", "", "| # | Gate | Status | Evidence |",
                  "|---|---|---|---|"]
        for g in sections[sec]:
            if g.status != PASS:
                all_pass = False
            lines.append(f"| {g.id} | {g.name} | {_emoji(g.status)} {g.status} | {g.detail} |")
        lines.append("")
    verdict = "PROMOTE ✅ — every gate PASS" if all_pass else \
        "DO NOT PROMOTE — one or more gates are not PASS (FAIL / INCONCLUSIVE / UNSET all block)"
    lines += ["---", "", f"**Overall: {verdict}**", "",
              "§E roll handling (E1–E3) is computed above from the live roll tag; the remaining "
              "§E reset conditions (code changes to canon/sizer/spine/relay, any A-failure, any "
              "naked position, any box config change) and §F non-gates are policy, not computed."]
    return "\n".join(lines), all_pass


# --------------------------------------------------------------------------- expected loader
def _load_expected(path: Path) -> list[tuple]:
    """Batch trade list for A4: (trade_date, fill_ts) keys. Accepts parquet or jsonl."""
    if path.suffix == ".parquet":
        import pandas as pd
        df = pd.read_parquet(path)
        dcol = "trade_date" if "trade_date" in df.columns else "day"
        fcol = "fill_ts" if "fill_ts" in df.columns else "fill"
        return [(str(r[dcol]), str(r[fcol])) for _, r in df.iterrows()]
    return [(str(r.get("trade_date", r.get("day"))), str(r.get("fill_ts", r.get("fill"))))
            for r in _read_jsonl(path)]


# --------------------------------------------------------------------------- main
def build_report(d: Path, expected_path: Path | None) -> tuple[str, bool]:
    a = load_artifacts(d)
    expected = _load_expected(expected_path) if expected_path else None
    sections = {"A": eval_A(a, expected), "B": eval_B(a), "C": eval_C(a), "D": eval_D(a),
                "E": eval_E_roll(a)}
    return render(sections)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", default="output/live", help="artifact directory")
    ap.add_argument("--expected", default=None, help="batch trade list (parquet/jsonl) for A4")
    ap.add_argument("--out", default=None, help="write the markdown report here too")
    args = ap.parse_args(argv)

    report, all_pass = build_report(Path(args.dir),
                                    Path(args.expected) if args.expected else None)
    print(report)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(report + "\n")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
