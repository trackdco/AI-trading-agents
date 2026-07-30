#!/usr/bin/env python3
"""The pre-registered London holdout report — and its dress rehearsal.

ONE SCRIPT, TWO SPANS, IDENTICAL CODE PATH. `--span fit` is the rehearsal: it computes every
number `docs/LONDON-PREREGISTRATION.md` §2 commits to, on the fit span where each has a known
anchor, and HARD-FAILS unless all anchors reproduce exactly. `--span holdout` is the sealed
run itself: same functions, same selection code (`lon_book` imported from
`scripts/london_combined_job.py`, never copied), only the input paths change. The rehearsal
exists so the sealed run is one command with zero debugging on sealed data — any bug is found
here, on fit data, where bugs are free.

SEALED-SPAN GUARDS, in order:
  1. `--span holdout` refuses to run without `--authorized-by "<name, date>"`. Prereg §6: the
     holdout may be opened only after ANGUS sign-off; a draft signature is NOT sufficient. The
     flag records who authorised in the report header. This script cannot check a signature —
     it can only make silent opening impossible.
  2. The holdout report is written ONCE. If `docs/LONDON-HOLDOUT-REPORT.md` already exists the
     script refuses — the prereg says the holdout opens once, and a re-run over an existing
     report is exactly the "quiet second look" the discipline forbids.
  3. Span/year cross-checks: fit inputs must contain only 2025/2026, holdout inputs only
     2023/2024 with every day in `data/reference/holdout_2023_24_days.csv`. Either violation
     is a hard exit — wrong artifact wiring, nothing downstream is valid.

WHAT IS REPORTED (prereg §2 items 1-10, plus the two gated tests and the declared
descriptives — nothing else; adding a number here after sign-off is a prereg violation):
  items 1-8   book counts, net, WR, mean R, maxDD, months green, worst month, trades/week
  item 9      W/FAR lift: mean R `either` vs `neither` on the floor-passing candidate
              population, per era and pooled
  item 10     the `either` cell split both-W+FAR vs exactly-one, on the BOOK (S2, DESCRIPTIVE
              — no inference, no decision; prereg §4 makes acting on it a retroactive
              3-test family)
  PRIMARY     book mean R > 0, gated at Sidak alpha = 0.0253
  S1          sub-9.5 wall-passing band mean R > 0, gated at the same alpha ("reported, not
              acted on" — ANGUS ruling; the floor is not moving on this run)
  buckets     the four half-hour fill-time buckets (declared prior from
              docs/LONDON-LATE-BUCKET.md: 09:30-10:00 weakest on fit, +0.119; checked here
              descriptively at zero alpha cost)

DECLARED TEST RESOLUTION (fixing an ambiguity BEFORE the sealed run, which is the only time
it can be fixed): the prereg's power arithmetic (78% primary) matches a TWO-SIDED test at
alpha 0.0253 on the normal approximation. This script gates on the two-sided Student-t
p-value with n-1 df (exact, slightly conservative vs the normal), PASS requiring mean R > 0
AND p <= 0.0253. S1 identical. No scipy: t CDF via the incomplete-beta continued fraction.

trades/week (item 8) = book trades / (calendar span of the POPULATION's days / 7) — calendar
weeks, not weeks-with-a-trade, so thin stretches lower the number instead of hiding.

    python -m scripts.london_holdout_report --span fit
    python -m scripts.london_holdout_report --span holdout --authorized-by "ANGUS, YYYY-MM-DD"
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.london_combined_job import lon_book, maxdd  # frozen selection path, never copied
from src.canon.scorer import london_checks

ET = "America/New_York"
LON = "Europe/London"
NQ_PT = 20.0
ALPHA = 0.0253                    # Sidak over 2 gated tests, prereg §4
EXPECT_FWD = 0.48                 # declared forward expectation, prereg §2

SPANS = {
    "fit": dict(features="output/l3_features_london_fit.parquet",
                fills="output/l1_fills_london_fit.parquet",
                years={2025, 2026}, out="LONDON-HOLDOUT-REHEARSAL.md"),
    "holdout": dict(features="output/l3_features_london_holdout.parquet",
                    fills="output/l1_fills_london_holdout.parquet",
                    years={2023, 2024}, out="LONDON-HOLDOUT-REPORT.md"),
}

BUCKETS = [(480, 510, "08:00-08:30"), (510, 540, "08:30-09:00"),
           (540, 570, "09:00-09:30"), (570, 600, "09:30-10:00")]

# ---- fit anchors: every number below is already on the record in a committed doc.
# book: prereg §2 fit reference. lift: prereg §2 item-9 reference. band: prereg §3 S1 table
# (= docs/LONDON-ERA-DIAGNOSIS.md). buckets: docs/LONDON-LATE-BUCKET.md profile table.
ANCHORS = dict(
    n=187, days=107, net=22795, wr_pct=57, mean_r=0.513, green=11, months=14,
    dd_era={"2025": 1720, "2026": 2550},
    lift_era={"2025": 0.444, "2026": 0.637},
    band_n={"2025": 164, "2026": 136},
    band_r={"2025": 0.904, "2026": 0.211},
    band_net={"2025": 18746, "2026": 3085},
    bucket_r=[0.371, 0.759, 0.734, 0.119],
)


# ------------------------------------------------------------------ stats, no scipy
def _betacf(a: float, b: float, x: float) -> float:
    """Continued fraction for the regularized incomplete beta (Lentz)."""
    TINY, EPS = 1e-30, 3e-12
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > TINY else TINY)
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > TINY else TINY)
        c = 1.0 + aa / (c if abs(c) > TINY else TINY)
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > TINY else TINY)
        c = 1.0 + aa / (c if abs(c) > TINY else TINY)
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < EPS:
            return h
    raise RuntimeError("betacf failed to converge")


def _ibeta(a: float, b: float, x: float) -> float:
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    ln_front = (math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
                + a * math.log(x) + b * math.log(1.0 - x))
    front = math.exp(ln_front)
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - front * _betacf(b, a, 1.0 - x) / b


def t_test_two_sided(r: pd.Series) -> dict:
    """One-sample two-sided Student t of mean(r)=0. Returns mean, se, t, df, p."""
    n = len(r)
    mean = float(r.mean())
    sd = float(r.std(ddof=1))
    se = sd / math.sqrt(n)
    t = mean / se if se > 0 else float("inf")
    df = n - 1
    p = _ibeta(df / 2.0, 0.5, df / (df + t * t))   # exact two-sided t p-value
    return dict(n=n, mean=mean, sd=sd, se=se, t=t, df=df, p=p)


# ------------------------------------------------------------------ data
def load_pop(span: str) -> pd.DataFrame:
    """Mirror of london_combined_job.lon_pop, span-parameterized, with year guards."""
    cfg = SPANS[span]
    fpath, lpath = ROOT / cfg["features"], ROOT / cfg["fills"]
    for p in (fpath, lpath):
        if not p.exists():
            raise SystemExit(f"MISSING ARTIFACT: {p} — build L0-L3 for span '{span}' first")
    F = pd.read_parquet(fpath)
    yrs = set(pd.to_datetime(F.day).dt.year)
    if yrs - cfg["years"]:
        raise SystemExit(f"SPAN VIOLATION: years {sorted(yrs)} in {fpath.name}, "
                         f"expected subset of {sorted(cfg['years'])}")
    F = pd.concat([F, F.apply(london_checks, axis=1, result_type="expand")], axis=1)
    F["era"] = pd.to_datetime(F.day).dt.year.astype(str)
    F["session"] = "london"
    F["fill_ts"] = pd.to_datetime(F.fill, format="mixed", utc=True).dt.tz_convert(ET)
    F["exit_ts"] = pd.to_datetime(F["exit"], format="mixed", utc=True).dt.tz_convert(ET)
    F["dollars"] = F.dollars / F.get("size_engine", 1.0)
    F["wall"] = ((F.W == 1) | (F.FAR == 1)).astype(float)
    L1 = pd.read_parquet(lpath)
    F = F.merge(L1[["ts", "max_away_before_fill"]].drop_duplicates("ts"), on="ts", how="left")
    F["max_away_before_fill"] = F.max_away_before_fill.fillna(0.0)
    return F


def guard_holdout_days(book: pd.DataFrame) -> None:
    sealed = set(pd.read_csv(ROOT / "data/reference/holdout_2023_24_days.csv",
                             dtype=str)["day"])
    extra = set(book.day.astype(str).str[:10]) - sealed
    if extra:
        raise SystemExit(f"SPAN VIOLATION: {len(extra)} book days outside the sealed list, "
                         f"e.g. {sorted(extra)[:3]}")


# ------------------------------------------------------------------ report pieces
def book_stats(t: pd.DataFrame, pop_days: pd.Series) -> dict:
    # maxDD is TRADE-LEVEL chronological equity (sorted day, fill_ts) — the prereg §2 fit
    # reference's own convention ($1,720/$2,550; verified: the grid audit and loser autopsy
    # match it). Day-level daily sums give $2,440 for 2026-fit — that is the late-bucket
    # doc's convention, NOT this report's. Pinned by the rehearsal anchor gate.
    t = t.sort_values(["day", "fill_ts"], kind="mergesort")
    mo = t.assign(mo=t.day.astype(str).str[:7]).groupby("mo").dollars.sum()
    span_days = (pd.to_datetime(pop_days.max()) - pd.to_datetime(pop_days.min())).days + 1
    per_era = {}
    for era, g in t.groupby("era"):
        per_era[era] = dict(n=len(g), net=float(g.dollars.sum()),
                            wr=float((g.R > 0).mean()), mean_r=float(g.R.mean()),
                            dd=maxdd(g.dollars))
    return dict(n=len(t), days=int(t.day.nunique()), net=float(t.dollars.sum()),
                wr=float((t.R > 0).mean()), mean_r=float(t.R.mean()),
                dd=maxdd(t.dollars), green=int((mo > 0).sum()), months=len(mo),
                worst_mo=float(mo.min()), worst_mo_name=str(mo.idxmin()),
                tpw=len(t) / (span_days / 7.0), per_era=per_era)


def wfar_lift(P: pd.DataFrame) -> dict:
    """Item 9 on the floor-passing candidate population: either (W|FAR) vs neither."""
    Q = P[P.risk >= 9.5]
    out = {}
    for label, g in [("pooled", Q)] + [(e, Q[Q.era == e]) for e in sorted(Q.era.unique())]:
        a, b = g[g.wall == 1], g[g.wall == 0]
        out[label] = dict(n_e=len(a), r_e=float(a.R.mean()),
                          n_n=len(b), r_n=float(b.R.mean()),
                          lift=float(a.R.mean() - b.R.mean()))
    return out


def both_one_split(t: pd.DataFrame) -> dict:
    """Item 10 / S2 on the book: both W AND FAR vs exactly one. DESCRIPTIVE."""
    both = t[(t.W == 1) & (t.FAR == 1)]
    one = t[t.wall == 1].loc[lambda d: (d.W == 1) ^ (d.FAR == 1)]
    return dict(n_b=len(both), r_b=float(both.R.mean()) if len(both) else float("nan"),
                n_o=len(one), r_o=float(one.R.mean()) if len(one) else float("nan"))


def bucket_profile(t: pd.DataFrame) -> pd.DataFrame:
    f = pd.to_datetime(t.fill_ts, utc=True).dt.tz_convert(LON)
    mins = f.dt.hour * 60 + f.dt.minute
    lab = pd.cut(mins, [b[0] for b in BUCKETS] + [600], right=False,
                 labels=[b[2] for b in BUCKETS])
    rows = []
    for name in [b[2] for b in BUCKETS]:
        g = t[lab == name]
        row = dict(bucket=name, n=len(g),
                   share=len(g) / len(t) if len(t) else float("nan"),
                   wr=float((g.R > 0).mean()) if len(g) else float("nan"),
                   mean_r=float(g.R.mean()) if len(g) else float("nan"),
                   net=float(g.dollars.sum()))
        for era in sorted(t.era.unique()):
            ge = g[g.era == era]
            row[f"r_{era}"] = float(ge.R.mean()) if len(ge) else float("nan")
        rows.append(row)
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ anchor gate (fit only)
def check_anchors(bs: dict, lifts: dict, band_stats: dict, buckets: pd.DataFrame) -> list:
    got = {
        "book trades": (bs["n"], ANCHORS["n"]),
        "book days": (bs["days"], ANCHORS["days"]),
        "net $": (round(bs["net"]), ANCHORS["net"]),
        "WR %": (round(bs["wr"] * 100), ANCHORS["wr_pct"]),
        "mean R": (round(bs["mean_r"], 3), ANCHORS["mean_r"]),
        "months green": (bs["green"], ANCHORS["green"]),
        "months total": (bs["months"], ANCHORS["months"]),
    }
    for era in ("2025", "2026"):
        got[f"maxDD {era} $"] = (round(bs["per_era"][era]["dd"]), ANCHORS["dd_era"][era])
        got[f"W/FAR lift {era}"] = (round(lifts[era]["lift"], 3), ANCHORS["lift_era"][era])
        got[f"S1 band n {era}"] = (band_stats[era]["n"], ANCHORS["band_n"][era])
        got[f"S1 band mean R {era}"] = (round(band_stats[era]["mean_r"], 3),
                                        ANCHORS["band_r"][era])
        got[f"S1 band net {era} $"] = (round(band_stats[era]["net"]),
                                       ANCHORS["band_net"][era])
    for i, (_, _, name) in enumerate(BUCKETS):
        got[f"bucket {name} mean R"] = (round(float(buckets.iloc[i].mean_r), 3),
                                        ANCHORS["bucket_r"][i])
    fails = []
    print("\nREHEARSAL ANCHOR GATE (every number must reproduce a committed figure)")
    for k, (g, e) in got.items():
        ok = g == e
        if not ok:
            fails.append(k)
        print(f"  {k:>22}: {g:>10}  expected {e:>10}  {'OK' if ok else 'MISMATCH'}")
    return fails


# ------------------------------------------------------------------ report body
def fmt_gate(name: str, res: dict) -> str:
    verdict = "PASS" if (res["mean"] > 0 and res["p"] <= ALPHA) else "FAIL"
    p = f"{res['p']:.4f}" if res["p"] >= 1e-4 else f"{res['p']:.1e}"
    return (f"| {name} | {res['n']} | {res['mean']:+.3f} | {res['se']:.3f} | "
            f"{res['t']:+.2f} | {p} | {ALPHA} | **{verdict}** |\n")


def build_report(span: str, authorized_by: str, bs: dict, primary: dict, s1: dict,
                 band_stats: dict, lifts: dict, split: dict,
                 buckets: pd.DataFrame) -> str:
    is_fit = span == "fit"
    title = ("London holdout — REHEARSAL on the fit span (anchor verification only)"
             if is_fit else "London holdout — THE sealed 2023/24 run (opens once)")
    L = [f"# {title}\n\n"]
    if is_fit:
        L.append("**This is not a result. It is the dress rehearsal required before the "
                 "sealed run: the same script, pointed at the fit span, gated on exact "
                 "reproduction of every committed anchor.** The sealed run is "
                 "`--span holdout --authorized-by \"...\"` with zero code changes.\n\n")
    else:
        L.append(f"**Authorized by: {authorized_by}.** Prereg: "
                 "`docs/LONDON-PREREGISTRATION.md` rev 2a. Frozen config §1; two gated "
                 "tests at Sidak alpha 0.0253 (§4). Declared resolution: a near-miss on "
                 f"mean R +{EXPECT_FWD} is not decay; a sign flip is.\n\n")
    L.append("## Items 1-8 — the book (frozen config, flat 1 NQ lot)\n\n")
    L.append("| item | value |\n|---|---|\n")
    L.append(f"| 1. trades / days with a take | {bs['n']} / {bs['days']} |\n")
    L.append(f"| 2. net P&L | ${bs['net']:+,.0f} |\n")
    L.append(f"| 3. win rate | {bs['wr'] * 100:.0f}% |\n")
    L.append(f"| 4. mean R | {bs['mean_r']:+.3f} |\n")
    L.append(f"| 5. maxDD (chronological) | ${bs['dd']:,.0f} |\n")
    L.append(f"| 6. months green | {bs['green']}/{bs['months']} |\n")
    L.append(f"| 7. worst month | ${bs['worst_mo']:+,.0f} ({bs['worst_mo_name']}) |\n")
    L.append(f"| 8. trades per week | {bs['tpw']:.1f} |\n")
    L.append("\nPer era:\n\n| era | n | net | WR | mean R | maxDD |\n|---|---|---|---|---|---|\n")
    for era, e in sorted(bs["per_era"].items()):
        L.append(f"| {era} | {e['n']} | ${e['net']:+,.0f} | {e['wr'] * 100:.0f}% | "
                 f"{e['mean_r']:+.3f} | ${e['dd']:,.0f} |\n")
    L.append("\n## Item 9 — W/FAR lift (floor-passing candidates, either vs neither)\n\n")
    L.append("| slice | either n | either R | neither n | neither R | lift |\n"
             "|---|---|---|---|---|---|\n")
    for k, v in lifts.items():
        L.append(f"| {k} | {v['n_e']} | {v['r_e']:+.3f} | {v['n_n']} | {v['r_n']:+.3f} | "
                 f"**{v['lift']:+.3f}** |\n")
    L.append("\n## Item 10 / S2 — the either cell split (DESCRIPTIVE, no inference)\n\n")
    L.append(f"both W+FAR: n={split['n_b']}, mean R {split['r_b']:+.3f} · exactly one: "
             f"n={split['n_o']}, mean R {split['r_o']:+.3f}\n\n"
             "Prereg §4: no decision may be taken on this number in this run — doing so "
             "retroactively makes the family 3 tests. It exists so the post-holdout sizing "
             "decision is judged against a pre-declared value.\n")
    L.append("\n## The two gated tests (two-sided Student t, PASS = mean > 0 and p <= alpha)\n\n")
    L.append("| test | n | mean R | SE | t | p | alpha | verdict |\n"
             "|---|---|---|---|---|---|---|---|\n")
    L.append(fmt_gate("PRIMARY — book mean R", primary))
    L.append(fmt_gate("S1 — sub-9.5 band mean R", s1))
    L.append("\nS1 is **reported, not acted on** (standing ANGUS ruling — the floor stays "
             "9.5 regardless of this cell; the era crossing already rejected floor 5).\n")
    L.append("\nS1 band per era:\n\n| era | n | net | WR | mean R |\n|---|---|---|---|---|\n")
    for era, e in sorted(band_stats.items()):
        L.append(f"| {era} | {e['n']} | ${e['net']:+,.0f} | {e['wr'] * 100:.0f}% | "
                 f"{e['mean_r']:+.3f} |\n")
    L.append("\n## Bucket profile (DESCRIPTIVE — declared prior: 09:30-10:00 weakest on fit)\n\n")
    era_cols = [c for c in buckets.columns if c.startswith("r_")]
    L.append("| bucket | n | share | WR | mean R | net |" +
             "".join(f" R {c[2:]} |" for c in era_cols) + "\n")
    L.append("|---|---|---|---|---|---|" + "---|" * len(era_cols) + "\n")
    for _, r in buckets.iterrows():
        L.append(f"| {r.bucket} | {r.n} | {r.share * 100:.0f}% | {r.wr * 100:.0f}% | "
                 f"{r.mean_r:+.3f} | ${r.net:+,.0f} |" +
                 "".join(f" {r[c]:+.3f} |" for c in era_cols) + "\n")
    if not is_fit:
        L.append("\nIf 09:30-10:00 is again the weakest bucket here — on data owing nothing "
                 "to the fit-side analysis — that is properly evidenced grounds to raise a "
                 "window-change hypothesis LATER, on its own prereg. Nothing is gated on it "
                 "in this run.\n")
    return "".join(L)


# ------------------------------------------------------------------ main
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--span", required=True, choices=["fit", "holdout"])
    ap.add_argument("--authorized-by", default="",
                    help="required for --span holdout: who authorised opening the sealed "
                         "set, e.g. \"ANGUS, 2026-08-02\"")
    a = ap.parse_args()

    out_path = ROOT / "docs" / SPANS[a.span]["out"]
    if a.span == "holdout":
        if not a.authorized_by.strip():
            raise SystemExit(
                "SEALED SPAN REFUSED. The holdout opens once, only after ANGUS signs off on "
                "prereg §1/§3/§4 (draft signature is NOT sufficient — prereg §6). If that "
                "sign-off exists, re-run with --authorized-by \"<name, date>\".")
        if out_path.exists():
            raise SystemExit(
                f"REFUSED: {out_path.name} already exists — the holdout has been opened. "
                "A second run over the sealed span is exactly what the prereg forbids. If "
                "this is a genuine re-issue (e.g. the first run crashed BEFORE reading "
                "outcomes), delete the file manually and record why in the session log.")

    P = load_pop(a.span)
    book = lon_book(P, floor=9.5, lifetime=math.inf, cap=999)
    band = lon_book(P[(P.risk >= 5.0) & (P.risk < 9.5)], floor=5.0,
                    lifetime=math.inf, cap=999)
    if a.span == "holdout":
        guard_holdout_days(book)

    bs = book_stats(book, P.day)
    lifts = wfar_lift(P)
    split = both_one_split(book)
    buckets = bucket_profile(book)
    band_stats = {era: dict(n=len(g), net=float(g.dollars.sum()),
                            wr=float((g.R > 0).mean()), mean_r=float(g.R.mean()))
                  for era, g in band.groupby("era")}
    primary = t_test_two_sided(book.R)
    s1 = t_test_two_sided(band.R)

    print(f"[{a.span}] book: {bs['n']} trades / {bs['days']} days / net ${bs['net']:+,.0f} / "
          f"WR {bs['wr'] * 100:.0f}% / mean R {bs['mean_r']:+.3f} / maxDD ${bs['dd']:,.0f}")
    print(f"[{a.span}] PRIMARY p={primary['p']:.4f}  S1 p={s1['p']:.4f}  (alpha {ALPHA})")

    if a.span == "fit":
        fails = check_anchors(bs, lifts, band_stats, buckets)
        body = build_report(a.span, "", bs, primary, s1, band_stats, lifts, split, buckets)
        out_path.write_text(body)
        print(f"\nwrote docs/{out_path.name} ({len(body):,} chars)")
        if fails:
            raise SystemExit(f"\nREHEARSAL FAIL — {len(fails)} anchor(s) did not reproduce: "
                             f"{fails}. Fix on FIT data; the sealed run stays shut.")
        print("\nREHEARSAL PASS — every committed anchor reproduced. The sealed run is "
              "one command away and requires no code changes.")
    else:
        body = build_report(a.span, a.authorized_by, bs, primary, s1, band_stats, lifts,
                            split, buckets)
        out_path.write_text(body)
        print(f"\nwrote docs/{out_path.name} ({len(body):,} chars)")
        print("\nHOLDOUT REPORTED. Read at the declared resolution: a near-miss on "
              f"+{EXPECT_FWD} is not decay; a sign flip is.")


if __name__ == "__main__":
    main()
