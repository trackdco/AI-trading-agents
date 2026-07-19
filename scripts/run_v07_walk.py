#!/usr/bin/env python3
"""v0.7 REGIME-DIAL walk driver (Angus, docs/SPEC-v07-regime-dial.md).

The regime dial: champion book by default, agent overrides book + size, and the
ONLY path to flat is a persistent risk-off STANCE that carries forward day to day.
That stance makes this inherently CHAINED — day N sees the stance carried from N-1.

Modes:
  emit    --start --end [--sample N]   write request blobs (fresh-eyes book+size test:
          carried_stance defaults risk_on; for the true chained walk the runner
          interleaves emit1/ingest1 per day so the stance carries)
  ingest  --start --end                validate v0.7 verdicts, carry stance forward,
          grade vs floored books (champion default + override + stance-flat), checkpoint

v0.7 verdict JSON (tolerant parse): regime_stance, book(rotation|momentum|champion),
size_multiplier(0.5|1.0), expected_value_usd, rationale, cited_evidence, playbook_notes.

Grading (floored books allyears_daily_books_r1r2.csv):
  risk_off stance -> FLAT (0)
  risk_on -> book = champion pick unless overridden; pl = size * book P&L
Checkpoint: output/v07/<tag>/ledger.csv + stance.json after every ingest.
"""
import argparse, json, re, sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.backtest.engine import load_news_calendar  # noqa: E402
from src.desk.regime_agent import build_briefing, render_prompt  # noqa: E402
from src.desk.v04 import as_fresh_eyes, attach_analog_block, load_analog_block  # noqa: E402
from src.desk.briefing_v05 import build_v062_briefing  # noqa: E402

MASTER = "data/reference/nq_1m_master.parquet"
BOOKS = "output/allyears_daily_books_r1r2.csv"


def _paths(tag):
    b = Path(f"output/desk_blobs/{tag}"); o = Path(f"output/v07/{tag}")
    b.mkdir(parents=True, exist_ok=True); o.mkdir(parents=True, exist_ok=True)
    return b, o


def _days(start, end):
    v = pd.read_csv("output/regime_vector.csv")
    return [d for d in v.day if start <= d <= end]


def champ_pick(day, vec):
    r = vec[vec.day == day]
    if r.empty or pd.isna(r.iloc[0].imbal_share_20):
        return "ROTATION"
    return "MOMENTUM" if r.iloc[0].imbal_share_20 >= 0.5 else "ROTATION"


def cmd_emit(a):
    B, O = _paths(a.tag)
    df = pd.read_parquet(MASTER); vec = pd.read_csv("output/regime_vector.csv")
    cal = load_news_calendar()
    books = pd.read_csv(BOOKS).rename(columns={"E3": "pl_e3", "E4": "pl_e4"}).set_index("day")
    stance = json.loads((O / "stance.json").read_text()) if (O / "stance.json").exists() else {}
    days = _days(a.start, a.end)
    if a.sample:
        days = days[::max(1, len(days) // a.sample)][:a.sample]
    n = 0
    for d in days:
        try:
            base = build_briefing(d, df, vec, cal, None, None, playbook_notes="")
        except ValueError:
            continue
        br = build_v062_briefing(attach_analog_block(as_fresh_eyes(base), load_analog_block(d)),
                                 d, cal, books, None, asof=a.asof)
        br["carried_stance"] = stance.get("current", "risk_on")
        br["champion_book_today"] = champ_pick(d, vec)
        (B / f"{d}.briefing.json").write_text(json.dumps(br, default=str))
        (B / f"{d}.request.txt").write_text(
            render_prompt(br, agent_file=Path(a.agent_file)))
        n += 1
    print(f"emitted {n} v0.7 requests to {B}/ (carried_stance seeded from {O}/stance.json)")


_BOOK = {"rotation": "ROTATION", "momentum": "MOMENTUM", "champion": "CHAMPION"}


def parse_v07(text, day):
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("no json")
    o = json.loads(m.group(0))
    stance = str(o.get("regime_stance", "risk_on")).lower()
    book = _BOOK.get(str(o.get("book", "champion")).lower(), "CHAMPION")
    size = float(o.get("size_multiplier", 1.0))
    if stance not in ("risk_on", "risk_off"):
        stance = "risk_on"
    if size not in (0.5, 1.0):
        size = 1.0
    return dict(day=day, regime_stance=stance, book=book, size=size,
                ev=o.get("expected_value_usd"))


def cmd_ingest(a):
    B, O = _paths(a.tag)
    vec = pd.read_csv("output/regime_vector.csv")
    books = pd.read_csv(BOOKS).set_index("day")
    stance = json.loads((O / "stance.json").read_text()) if (O / "stance.json").exists() else {"current": "risk_on"}
    ledger = []
    if (O / "ledger.csv").exists():
        ledger = pd.read_csv(O / "ledger.csv").to_dict("records")
    seen = {r["day"] for r in ledger}
    failed = 0
    for d in _days(a.start, a.end):
        if d in seen:
            continue
        resp = B / f"{d}.response.txt"
        if not resp.exists() or d not in books.index:
            continue
        try:
            v = parse_v07(resp.read_text(), d)
        except Exception as e:
            failed += 1
            print(f"{d}: INVALID ({e})")
            continue
        stance["current"] = v["regime_stance"]          # carry forward
        e3, e4 = float(books.loc[d, "E3"]), float(books.loc[d, "E4"])
        if v["regime_stance"] == "risk_off":
            act, pl = "FLAT", 0.0
        else:
            act = champ_pick(d, vec) if v["book"] == "CHAMPION" else v["book"]
            pl = v["size"] * (e3 if act == "ROTATION" else e4)
        orc = max(e3, e4, 0.0)
        oracle = "FLAT" if max(e3, e4) <= 0 else ("ROTATION" if e3 >= e4 else "MOMENTUM")
        ledger.append(dict(day=d, stance=v["regime_stance"], book=v["book"], act=act,
                           size=v["size"], pl=round(pl), oracle=oracle,
                           hit=act == oracle, orc=round(orc), e3=round(e3), e4=round(e4)))
    L = pd.DataFrame(ledger)
    L.to_csv(O / "ledger.csv", index=False)
    (O / "stance.json").write_text(json.dumps(stance))
    if len(L):
        L["y"] = L.day.str[:4]
        ceil = L.orc.sum()
        print(f"\n=== v0.7 [{a.tag}] {len(L)} days, {failed} invalid ===")
        for y, g in L.groupby("y"):
            c = g.orc.sum()
            print(f"  {y}: ${g.pl.sum():+,.0f} = {g.pl.sum()/c*100:.0f}%  reads {g.hit.mean()*100:.0f}%  "
                  f"flat {(g.act=='FLAT').mean()*100:.0f}%  risk_off {(g.stance=='risk_off').mean()*100:.0f}%")
        print(f"  ALL: ${L.pl.sum():+,.0f} = {L.pl.sum()/ceil*100:.0f}% of ${ceil:,.0f}")


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    for nm in ("emit", "ingest"):
        s = sub.add_parser(nm)
        s.add_argument("--start", required=True); s.add_argument("--end", required=True)
        s.add_argument("--tag", default="v07")
        if nm == "emit":
            s.add_argument("--agent-file", default=".claude/agents/regime-context-v070.md")
            s.add_argument("--asof", default=None); s.add_argument("--sample", type=int, default=0)
    a = p.parse_args()
    (cmd_emit if a.cmd == "emit" else cmd_ingest)(a)


if __name__ == "__main__":
    main()
