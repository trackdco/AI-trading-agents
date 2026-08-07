#!/usr/bin/env python3
"""Contamination audit — SPEC-htf-bias-agent §7. Run BEFORE anything else; if it fails, stop.

THE THREAT. The bias agent is an LLM. Ask an LLM "what was NQ's bias on 14 March 2025" and it
may simply RECALL the answer rather than read the chart. A backtest built that way scores memory,
not skill, and it is the worst failure class this project has hit: the depth read one bar late
and the +10.57pt head start were both visible in a diff. This one hides inside the model.

THE TEST. Show the model the anonymised window and ask it to name the instrument and the period.
If it can, the anonymisation failed and every downstream number is void.

THE PROTOCOL IS SEALED, and the seal is the point. `sample` writes two files:

    blind_windows.md   what the model sees        <- read this
    truth.json         what they actually were    <- NEVER read this while answering

The answers are written to a third file and only then does `score` join them. An audit where the
grader can see the answer key grades nothing. If the same model both answers and scores, the seal
is the only thing standing between an honest result and a worthless one, so it is enforced here
rather than left to discipline.

BASELINE. "Better than chance" is not uniform chance. A model that always answers the single most
common year is right ~30% of the time for free. The scorer therefore compares against the BEST
CONSTANT GUESS from the corpus's own distribution, which is the number an uninformed but sensible
guesser gets. Beating uniform chance while losing to the constant guess is not evidence of leak.

    python -m scripts.contamination_audit sample [--n 40] [--seed 7]
    python -m scripts.contamination_audit score  --answers output/audit/answers.json
    python -m scripts.contamination_audit distinct
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

ANON = ROOT / "output/htf_context_anon.jsonl"
AUD = ROOT / "output/audit"


def load_anon() -> list[dict]:
    return [json.loads(l) for l in ANON.open()]


def render(w: dict) -> str:
    """Exactly what the agent gets — no dates, no instrument, prices indexed to 100."""
    L = [f"### {w['id']}   (session: {w['session']})"]
    L.append(f"volatility: 20d ATR = {w['session_atr_20d']} index points")
    pd_ = w["prev_day"]
    L.append(f"previous completed day:  H {pd_['high']}  L {pd_['low']}  C {pd_['close']}  "
             f"(close sits {pd_['close_pos']:.0%} up its range)")
    if w.get("prev_week"):
        L.append(f"previous week:  H {w['prev_week']['high']}  L {w['prev_week']['low']}")
    if w.get("prev_month"):
        L.append(f"previous month: H {w['prev_month']['high']}  L {w['prev_month']['low']}")
    dr = w["dealing_range"]
    L.append(f"dealing range:  H {dr['high']}  L {dr['low']}  EQ {dr['equilibrium']}")
    ip = w["ipda"]
    L.append("lookback ranges: " + "  ".join(
        f"{k}: {v['high']}/{v['low']}" for k, v in ip.items()))
    if w.get("equal_highs"):
        L.append(f"equal highs: {w['equal_highs']}")
    if w.get("equal_lows"):
        L.append(f"equal lows:  {w['equal_lows']}")
    fv = w.get("unfilled_daily_fvg") or []
    if fv:
        L.append("unfilled daily FVGs: " + "  ".join(
            f"[{g['dir']} {g['bottom']}-{g['top']}, {g['age_days']}d old]" for g in fv))
    on = w.get("overnight")
    if on:
        L.append(f"overnight before the open:  H {on['high']}  L {on['low']}  last {on['last']}"
                 f"   swept prev high: {on['swept_prev_high']}   "
                 f"swept prev low: {on['swept_prev_low']}")
    L.append(f"position in dealing range: {w.get('position_in_range')}  "
             f"({w.get('premium_discount')})")
    L.append("last 20 daily bars (O,H,L,C), oldest first:")
    for r in w["daily_ohlc_20"]:
        L.append(f"    {r[0]:>8} {r[1]:>8} {r[2]:>8} {r[3]:>8}")
    return "\n".join(L)


def cmd_sample(n: int, seed: int) -> int:
    rows = load_anon()
    rnd = random.Random(seed)
    pick = rnd.sample(rows, n)
    AUD.mkdir(parents=True, exist_ok=True)

    head = f"""# Contamination audit — blind identification sheet

{n} anonymised market windows, drawn at random from the corpus with seed {seed}.

Every window is a real, contiguous stretch of a real futures market. Prices have been indexed
so the reference price is 100.00; all levels are in index points. Dates, weekday, instrument and
contract are removed. Order is randomised.

**Your task for each window: name the instrument and the calendar month it comes from.**

Answer every one — guessing is required, an "unknown" is scored as a miss. Write answers to
`output/audit/answers.json`:

```json
{{"W000123": {{"instrument": "NQ", "ym": "2025-03", "confidence": 40}}, ...}}
```

`ym` must be YYYY-MM. `confidence` is 0-100, how sure you are of `ym`.

If identification beats the best constant guess, the anonymisation has failed and the whole
bias-agent result is void.

---
"""
    with (AUD / "blind_windows.md").open("w") as f:
        f.write(head)
        for w in pick:
            f.write(render(w) + "\n\n---\n\n")

    with (AUD / "truth.json").open("w") as f:
        json.dump({w["id"]: w["_truth_day"] for w in pick}, f, indent=1)

    # corpus-wide priors, needed by the scorer for the constant-guess baseline
    with (AUD / "priors.json").open("w") as f:
        json.dump({"ym": Counter(r["_truth_day"][:7] for r in rows),
                   "y": Counter(r["_truth_day"][:4] for r in rows),
                   "n_corpus": len(rows)}, f, indent=1)

    print(f"wrote {(AUD / 'blind_windows.md').relative_to(ROOT)}  ({n} windows)")
    print(f"SEALED: {(AUD / 'truth.json').relative_to(ROOT)} — do not open until answers exist")
    return 0


def _binom_p(k: int, n: int, p: float) -> float:
    """P(X >= k) for X~Bin(n,p). Exact; n is small here."""
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))


def cmd_score(answers: Path) -> int:
    truth = json.load((AUD / "truth.json").open())
    priors = json.load((AUD / "priors.json").open())
    # underscore keys are the answerer's own notes, not answers
    ans = {k: v for k, v in json.load(answers.open()).items()
           if not k.startswith("_") and isinstance(v, dict)}

    ymp = priors["ym"]
    yp = priors["y"]
    tot = sum(ymp.values())
    best_ym = max(ymp.values()) / tot
    best_y = max(yp.values()) / tot

    ids = sorted(truth)
    miss = [i for i in ids if i not in ans]
    if miss:
        print(f"WARNING: {len(miss)} unanswered, scored as misses: {miss[:6]}")

    hit_ym = hit_y = hit_q = 0
    rows = []
    for i in ids:
        t = truth[i]
        a = ans.get(i, {})
        g = str(a.get("ym", ""))
        oy, om = t[:4], int(t[5:7])
        gy, gm = g[:4], (int(g[5:7]) if len(g) >= 7 and g[5:7].isdigit() else 0)
        ok_ym, ok_y = (g[:7] == t[:7]), (gy == oy)
        ok_q = ok_y and gm and (gm - 1) // 3 == (om - 1) // 3
        hit_ym += ok_ym
        hit_y += ok_y
        hit_q += ok_q
        rows.append((i, t[:7], g[:7] or "-", a.get("confidence"), ok_ym, ok_y, ok_q))

    n = len(ids)
    inst = Counter(str(a.get("instrument", "")).upper().strip() for a in ans.values())

    print(f"\nCONTAMINATION AUDIT — {n} windows\n")
    print(f"{'window':>9} {'true':>8} {'guess':>8} {'conf':>5}  ym  y  q")
    for i, t, g, c, a1, a2, a3 in rows:
        print(f"{i:>9} {t:>8} {g:>8} {str(c):>5}  "
              f"{'Y' if a1 else '.'}   {'Y' if a2 else '.'}  {'Y' if a3 else '.'}")

    print(f"\n{'':22}{'agent':>8}{'best constant guess':>22}{'p(>= agent | guessing)':>24}")
    for lbl, hit, base in (("exact month", hit_ym, best_ym),
                           ("year", hit_y, best_y),
                           ("year+quarter", hit_q, best_y / 4 * 1.0)):
        p = _binom_p(hit, n, base)
        flag = "  <-- LEAK" if p < 0.01 and hit / n > base else ""
        print(f"{lbl:22}{hit}/{n} = {hit/n:5.1%}{base:>18.1%}{p:>24.4f}{flag}")

    print(f"\ninstrument named: {dict(inst)}")
    print("  (the corpus is a single instrument; a confident correct name is itself a leak,\n"
          "   but only if the model could not have inferred it from the conversation)")

    if hit_ym and rows:
        cs = [r[3] for r in rows if r[3] is not None]
        if cs:
            hi = [r for r in rows if r[3] is not None and r[3] >= np.median(cs)]
            lo = [r for r in rows if r[3] is not None and r[3] < np.median(cs)]
            if hi and lo:
                print(f"\nconfidence check: high-conf {sum(r[4] for r in hi)}/{len(hi)} correct, "
                      f"low-conf {sum(r[4] for r in lo)}/{len(lo)}")
                print("  (a real leak should show UP as confident and correct)")

    fail = any(_binom_p(h, n, b) < 0.01 and h / n > b
               for h, b in ((hit_ym, best_ym), (hit_y, best_y)))
    print(f"\nVERDICT: {'FAIL — anonymisation leaks, stop here' if fail else 'PASS — no recoverable period signal'}")
    return 1 if fail else 0


def cmd_distinct() -> int:
    """Mechanical companion test: how distinctive is a window's SHAPE?

    The LLM test above asks whether a model can name the date from memory. This asks a different
    and stricter question: does the window carry enough structure that an adversary HOLDING THE
    RAW SERIES could re-identify it? That is the upper bound on leakage, and it is worth knowing
    even though no LLM has the raw series to hand.
    """
    rows = load_anon()
    X = np.array([[c for bar in r["daily_ohlc_20"] for c in bar] for r in rows], dtype=float)
    X = (X - X.mean(1, keepdims=True)) / (X.std(1, keepdims=True) + 1e-9)
    rnd = np.random.default_rng(11)
    probe = rnd.choice(len(X), 300, replace=False)
    days = [r["_truth_day"] for r in rows]

    same_day, same_mo, n_amb = 0, 0, 0
    for i in probe:
        d = np.abs(X - X[i]).sum(1)
        d[i] = np.inf
        j = int(d.argmin())
        same_day += days[j] == days[i]
        same_mo += days[j][:7] == days[i][:7]
        n_amb += int((d < d[j] * 1.05).sum())

    n = len(probe)
    print(f"\nSHAPE DISTINCTIVENESS — {n} probes against {len(X):,} windows")
    print(f"  nearest neighbour is the SAME DAY:   {same_day/n:6.1%}  "
          f"(expected — sessions share a day's daily bars)")
    print(f"  nearest neighbour is the SAME MONTH: {same_mo/n:6.1%}")
    print(f"  mean windows within 5% of nearest:   {n_amb/n:6.2f}")
    print("\n  Read this as: the normalised 20-bar shape IS a near-unique fingerprint of a\n"
          "  calendar day. That is expected and is not by itself a contamination — it only\n"
          "  matters if the model can map fingerprint -> date, which is what the sealed test\n"
          "  above measures.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sample")
    s.add_argument("--n", type=int, default=40)
    s.add_argument("--seed", type=int, default=7)
    c = sub.add_parser("score")
    c.add_argument("--answers", type=Path, default=AUD / "answers.json")
    sub.add_parser("distinct")
    a = ap.parse_args()
    if a.cmd == "sample":
        return cmd_sample(a.n, a.seed)
    if a.cmd == "score":
        return cmd_score(a.answers)
    return cmd_distinct()


if __name__ == "__main__":
    raise SystemExit(main())
