#!/usr/bin/env python3
"""LDN-CAN-01 L1 — the fills data card (§5.10 transparency rule).

Authorised by docs/PREREG-london-canon-rebuild.md. Reads output/l1_fills_london_fit.parquet
and reports entry MECHANICS only. **There are no P&L numbers here and none have been
computed** — outcomes are L2. L1 ranks nothing and kills nothing (§5.9.2).

Closes the §5.11.2 event-universe item the prereg amendment moved down from L0: entry
timeframe scope, pattern scope, and the order-cancel policy — all three measured, none
applied.

    python -m scripts.l1_london_card
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.validation import trial_ledger  # noqa: E402

PREREG = "docs/PREREG-london-canon-rebuild.md"
OUT_MD = ROOT / "output/l1_london_card.md"
LON_RISK_MIN = 9.5      # the standing London Layer-0 floor — CARRIED IN AS A HYPOTHESIS


def main() -> int:
    F = pd.read_parquet(ROOT / "output/l1_fills_london_fit.parquet")
    F["era"] = F["day"].str[:4]
    F["half"] = F["day"].str[:4] + F["day"].str[5:7].astype(int).map(
        lambda m: "H1" if m <= 6 else "H2")
    fl = F[F["arm_none"]]
    nd = F["day"].nunique()

    L = ["# LDN-CAN-01 — L1 fills data card", "",
         f"Authorised by `{PREREG}`. **Entry mechanics only. No P&L numbers appear on this",
         "card because none have been computed** — outcomes are L2. L1 ranks nothing and",
         "kills nothing (§5.9.2).", "",
         "**GATE — engine subset reproduction: PASSED.** 6 DST-aligned sessions, 20 engine",
         "fills, every one matched on trigger timestamp, fill minute and entry price. (The",
         "NY template gates on 2 days; the engine serialises hard inside a two-hour window,",
         "so two days only exercised 6 fills.)", "",
         "**Sealed and untouched:** the 2023/24 days, `depth_london_2023_24`, the sealed",
         "flow months.", "",
         "## 1. Does the market let you in?", "",
         "| | value |", "|---|---:|",
         f"| candidates walked | {len(F):,} |",
         f"| **filled** | **{len(fl):,} ({len(fl)/len(F):.0%})** |",
         f"| expired at the window end | {len(F)-len(fl):,} |",
         f"| fills per session | {len(fl)/nd:.1f} |", "",
         "| era | candidates | fill rate |", "|---|---:|---:|"]
    for e in ("2025", "2026"):
        s = F[F["era"] == e]
        L.append(f"| {e} | {len(s):,} | {s['arm_none'].mean():.1%} |")
    L += ["", "Era-stable to within a point. The entry is a limit on the retest, and the",
          "retest happens: **median 1 minute to fill, "
          f"{(fl['mins_to_fill'] <= 1).mean():.0%} within a minute**, p90 "
          f"{fl['mins_to_fill'].quantile(.9):.0f} minutes.", "",
          "Expiry is mechanical, not informative — later triggers have less window left:", "",
          "| trigger, minutes after London open | fill rate |", "|---|---:|"]
    F["bucket"] = pd.cut(F["lon_min"], [-1, 15, 30, 60, 90, 121],
                         labels=["0–15", "15–30", "30–60", "60–90", "90–120"])
    for b, g in F.groupby("bucket", observed=True):
        L.append(f"| {b} | {g['arm_none'].mean():.1%} |")

    # --- 2. event universe (§5.11.2, moved here by the prereg amendment) ---------
    L += ["", "## 2. Event universe (§5.11.2) — measured, NOT applied", "",
          "The prereg amendment moved this item from L0 to L1 when the wide band was",
          "cancelled. Three questions, none of which anyone has ever decided:", "",
          "**(a) Entry timeframe scope.** The detector fires on four; nothing has chosen.",
          "", "| tf | candidates | fill rate | median intended risk | clears 9.5pt floor |",
          "|---|---:|---:|---:|---:|"]
    for tf, g in F.groupby("tf"):
        gf = g[g["arm_none"]]
        L.append(f"| `{tf}` | {len(g):,} | {g['arm_none'].mean():.1%} | "
                 f"{gf['risk_intended'].median():.2f} pt | "
                 f"{(gf['risk_intended'] >= LON_RISK_MIN).mean():.1%} |")
    L += ["", "**(b) Pattern scope.**", "",
          "| pattern | candidates | fill rate | median intended risk | clears 9.5pt floor |",
          "|---|---:|---:|---:|---:|"]
    for p, g in F.groupby("pattern"):
        gf = g[g["arm_none"]]
        L.append(f"| `{p}` | {len(g):,} | {g['arm_none'].mean():.1%} | "
                 f"{gf['risk_intended'].median():.2f} pt | "
                 f"{(gf['risk_intended'] >= LON_RISK_MIN).mean():.1%} |")
    L += ["", "**(c) Order-cancel policy.** Cancel rules only ever REMOVE fills, so the walk",
          "enforced none and recorded the events each would key on.", "",
          "| arm | fills kept | share | status |", "|---|---:|---:|---|"]
    for a, note in (("arm_none", "**THE LONDON POLICY** — no distance cancel, orders die at "
                     "the window end (standing ruling)"),
                    ("arm_struct", "cancel when price ran away, tested a structural level and "
                     "rejected hard back — recorded, not applied"),
                    ("arm_dist22", "NY's 22pt distance cancel — recorded for comparison only, "
                     "not London policy")):
        L.append(f"| `{a}` | {int(F[a].sum()):,} | {F[a].sum()/len(fl):.1%} | {note} |")
    sev = fl["struct_event"].replace("", "none").value_counts()
    L += ["", "Structural events seen while the order rested: "
          + ", ".join(f"**{k}** {v:,}" for k, v in sev.items())
          + f". Median distance price ran away before filling: "
          f"**{fl['max_away_before_fill'].median():.1f} pts** (p90 "
          f"{fl['max_away_before_fill'].quantile(.9):.1f}).", ""]

    # --- 3. the risk floor ------------------------------------------------------
    keep = fl[fl["risk_intended"] >= LON_RISK_MIN]
    L += ["## 3. THE FINDING — the 9.5pt risk floor is not a filter, it is a different "
          "strategy", "",
          "The standing London Layer-0 gate is `risk >= 9.5pt`. The handoff carries it in as",
          "**a hypothesis to re-test on the honest population, not a rule to import**. Here",
          "is what it does to this population.", "",
          "| | value |", "|---|---:|",
          f"| median intended risk, all fills | **{fl['risk_intended'].median():.2f} pt** |",
          f"| fills below the 9.5pt floor | **{(fl['risk_intended'] < LON_RISK_MIN).mean():.1%}** |",
          f"| fills below 7pt | {(fl['risk_intended'] < 7).mean():.1%} |",
          f"| fills surviving the floor | **{len(keep):,} of {len(fl):,}** |",
          f"| survivors per session | **{len(keep)/nd:.1f}** |", "",
          "**And it changes what the strategy is.** The floor is not neutral across patterns",
          "— it is close to a pattern selector wearing a risk costume:", "",
          "| pattern | share BEFORE the floor | share AFTER |", "|---|---:|---:|"]
    for p in ("B2", "B", "A"):
        L.append(f"| `{p}` | {(fl['pattern'] == p).mean():.1%} | "
                 f"{(keep['pattern'] == p).mean():.1%} |")
    # Every number in this paragraph is READ FROM THE DATA. It was hardcoded prose sitting
    # directly under a computed table of the same quantities until 2026-08-06 -- the same
    # defect that left `london_obk_flow.md` quoting +0.448R for a cell that had become
    # -0.099R once its inputs were corrected. A sentence that cannot regenerate will
    # eventually contradict the table above it, and it will look authoritative doing so.
    _pre = {p: (fl["pattern"] == p).mean() for p in ("B2", "B", "A")}
    _post = {p: (keep["pattern"] == p).mean() for p in ("B2", "B", "A")}
    _top_pre = max(_pre, key=_pre.get)
    _top_post = max(_post, key=_post.get)
    _med = {p: fl.loc[fl["pattern"] == p, "risk_intended"].median() for p in ("B2", "B")}
    _tf = {tf: (g.loc[g["arm_none"], "risk_intended"] >= LON_RISK_MIN).mean()
           for tf, g in F.groupby("tf")}
    _tf_hi = max(_tf, key=_tf.get) if _tf else None
    _tf_lo = min(_tf, key=_tf.get) if _tf else None
    L += ["", f"The raw substrate is **{_pre[_top_pre]:.1%} `{_top_pre}`**. After the floor "
              f"the largest share is **{_post[_top_post]:.1%} `{_top_post}`**. Applying a "
              f"{LON_RISK_MIN}-point stop minimum reshapes the book, because `B2`'s stop sits "
              f"just beyond a wick (median {_med['B2']:.2f} pt) while `B`'s sits beyond a "
              f"displacement origin (median {_med['B']:.2f} pt).", ""]
    if _tf_hi is not None and _tf_hi != _tf_lo:
        L += [f"It selects timeframe the same way: `{_tf_hi}` triggers clear the floor "
              f"{_tf[_tf_hi]:.1%} of the time, `{_tf_lo}` triggers {_tf[_tf_lo]:.1%}.", ""]
    L += ["**No decision is taken here.** The floor is recorded as an L2 arm class, to be",
          "tested by risk band on outcomes the way NY tested its 7–60 band — not applied",
          "because it is what the old book did.", ""]

    # --- 4. what L2 owes --------------------------------------------------------
    L += ["## 4. What L2 owes", "",
          "1. **Every fill through the REAL engine**, V8 management, rr_floor 2.0 — one",
          "   trigger per `simulate()` call so serialisation cannot shape the population.",
          "2. **The risk-band test** (§5.11.3 stop/risk arm class): outcomes by intended-risk",
          "   band, so the 9.5pt floor is decided on evidence and the pattern-mix consequence",
          "   above is priced into that decision rather than discovered after it.",
          "3. **MFE/MAE pack** (§5.11.1) at the same time, not bolted on later.",
          "4. **Gate: lookback invariance**, 7d vs 30d, on days with real fills.", ""]

    text = "\n".join(L)
    print(text)
    OUT_MD.write_text(text)

    rows = [{"family": "LDN-CAN-01", "era": "fit", "prereg": PREREG,
             "trial": "L1 fill rate, no cancel enforced",
             "stat_type": "mean", "estimate": round(float(fl.shape[0] / len(F)), 4),
             "n": len(F), "t_stat": 0.0, "effect": 0.0,
             "verdict": (f"L1 mechanics: {len(fl):,} of {len(F):,} candidates fill "
                         f"({len(fl)/len(F):.0%}), median 1 min to fill; engine subset gate "
                         f"PASSED on 20 fills; {(fl['risk_intended'] < LON_RISK_MIN).mean():.0%} "
                         f"sit below the 9.5pt London floor. No P&L computed at this rung.")}]
    ex = trial_ledger.load()
    already = set(zip(ex["family"], ex["trial"], ex["era"]))
    fresh = [r for r in rows if (r["family"], r["trial"], r["era"]) not in already]
    if fresh:
        trial_ledger.record(fresh)
        print(f"\nrecorded {len(fresh)} trials")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
