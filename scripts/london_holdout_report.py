#!/usr/bin/env python3
"""The pre-registered London holdout report — and its dress rehearsals.

ONE SCRIPT, TWO SPANS, TWO CONFIGS, IDENTICAL CODE PATHS. `--span fit` is the
rehearsal: it computes every number the prereg commits to, on the fit span where each
has a committed anchor, and HARD-FAILS unless all reproduce exactly. `--span holdout`
is the sealed run: same functions, only input paths change.

`--config` selects which strategy revision is reported (Angus signs exactly one):
  rev2a   prereg rev 2a as written: window 08:00-10:00, wall gate, V8 management,
          no veto, no serialization — the 187-trade book.
  rev3    the rev-3 bundle (docs/LONDON-REV3-BUNDLE.md): window 08:00-09:45, wall
          gate, score-0 veto at the FROZEN literals (src/canon/scorer.py
          LON_VETO_*), one-position-at-a-time, V1 management (BE at +1R) — the
          130-trade stack. Requires the holdout V1 L2 arm
          (build_l2_outcomes_london --span holdout --mgmt V1) at sealed-run time.

SEALED-SPAN GUARDS, in order:
  1. `--span holdout` refuses to run without `--authorized-by "<name, date>"`
     (prereg §6: ANGUS signature; draft is NOT sufficient).
  2. The holdout report is written ONCE — one file, whichever config was signed. If
     `docs/LONDON-HOLDOUT-REPORT.md` exists the script refuses; a second run over the
     sealed span is the "quiet second look" the discipline forbids.
  3. Span/year cross-checks: fit inputs must be 2025/2026 only, holdout inputs
     2023/2024 only with every day in the sealed list. Violation = hard exit.

WHAT IS REPORTED (prereg §2 items 1-10 + the two gated tests + declared
descriptives; adding a number after sign-off is a prereg violation):
  items 1-8   book counts, net, WR, mean R, maxDD (TRADE-level chronological — the
              prereg reference convention, pinned by rehearsal), months green,
              worst month, trades/week
  item 9      W/FAR lift on the floor-passing candidate population (per config's
              window/management), either vs neither, per era
  item 10     the either-cell split both-W+FAR vs exactly-one, on the BOOK (S2,
              DESCRIPTIVE — prereg §4 makes acting on it a 3-test family)
  PRIMARY     book mean R > 0, two-sided Student-t, Sidak alpha 0.0253
  S1          sub-9.5 wall-passing band mean R > 0, same test ("reported, not acted
              on" — standing ANGUS ruling). Under rev3 the band keeps its original
              definition (floor-5 lon_book, no veto/serial) on the rev-3
              window+management, declared in the bundle.
  buckets     half-hour fill-time profile (declared prior: the late window is the
              weak one on fit)

DECLARED TEST RESOLUTION (fixed before the sealed run): two-sided Student-t with
n-1 df (exact, via incomplete beta — no scipy), PASS = mean R > 0 AND p <= 0.0253,
matching the prereg power arithmetic.

trades/week = book trades / (calendar span of the population's days / 7).

    python -m scripts.london_holdout_report --span fit --config rev2a
    python -m scripts.london_holdout_report --span fit --config rev3
    python -m scripts.london_holdout_report --span holdout --config <signed> \
        --authorized-by "ANGUS, YYYY-MM-DD"
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.london_combined_job import lon_book, maxdd  # frozen selection path
from src.canon.scorer import (LON_VETO_RESIST, LON_VETO_THICK, LON_VETO_TRIGDENS,
                              london_checks)

ET = "America/New_York"
LON = "Europe/London"
NQ_PT = 20.0
ALPHA = 0.0253                    # Sidak over 2 gated tests, prereg §4
EXPECT_FWD = 0.48                 # declared forward expectation (BOTH configs — a
                                  # guard-failed cut may not inherit into the prior)

SPANS = {
    "fit": dict(features="output/l3_features_london_fit.parquet",
                fills="output/l1_fills_london_fit.parquet",
                v1="output/l2_outcomes_london_fit_v1.parquet",
                years={2025, 2026}),
    "holdout": dict(features="output/l3_features_london_holdout.parquet",
                    fills="output/l1_fills_london_holdout.parquet",
                    v1="output/l2_outcomes_london_holdout_v1.parquet",
                    years={2023, 2024}),
}

CONFIGS = {
    "rev2a": dict(cut_min=None, mgmt="V8", veto=False, serial=False,
                  rehearsal="LONDON-HOLDOUT-REHEARSAL.md",
                  buckets=[(480, 510, "08:00-08:30"), (510, 540, "08:30-09:00"),
                           (540, 570, "09:00-09:30"), (570, 600, "09:30-10:00")]),
    "rev3": dict(cut_min=585, mgmt="V1", veto=True, serial=True,
                 rehearsal="LONDON-HOLDOUT-REHEARSAL-REV3.md",
                 buckets=[(480, 510, "08:00-08:30"), (510, 540, "08:30-09:00"),
                          (540, 570, "09:00-09:30"), (570, 585, "09:30-09:45")]),
}

# ---- rev 2a fit anchors: prereg §2 reference / era-diagnosis / late-bucket doc.
ANCHORS = {
    "rev2a": dict(
        n=187, days=107, net=22795, wr_pct=57, mean_r=0.513, green=11, months=14,
        dd_era={"2025": 1720, "2026": 2550},
        lift_era={"2025": 0.444, "2026": 0.637},
        band_n={"2025": 164, "2026": 136},
        band_r={"2025": 0.904, "2026": 0.211},
        band_net={"2025": 18746, "2026": 3085},
        bucket_r=[0.371, 0.759, 0.734, 0.119],
    ),
    # rev 3 fit anchors: committed from this pipeline's own verified fit run
    # (2026-07-30). Consistency cross-checks: n=130 matches the tournament/MC stack;
    # maxDD $1,310 matches the V1 tournament; WR 29% is the V1 scratch optic
    # (BE exits book as ~-0.02R).
    "rev3": dict(
        n=130, days=93, net=22665, wr_pct=29, mean_r=0.758, green=10, months=14,
        dd_era={"2025": 775, "2026": 1310},
        lift_era={"2025": 0.584, "2026": 0.874},
        band_n={"2025": 153, "2026": 122},
        band_r={"2025": 0.751, "2026": 0.237},
        band_net={"2025": 14705, "2026": 2875},
        bucket_r=[0.349, 0.967, 1.252, 0.077],
    ),
}


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


def swap_v1(P: pd.DataFrame, span: str) -> pd.DataFrame:
    """Replace V8 outcomes with the V1 (BE at +1R) engine arm's, by trigger key."""
    apath = ROOT / SPANS[span]["v1"]
    if not apath.exists():
        raise SystemExit(f"MISSING ARTIFACT: {apath} — run "
                         f"build_l2_outcomes_london --span {span} --mgmt V1 first")
    A = pd.read_parquet(apath).rename(columns={"dollars_1lot": "dollars"})
    A["exit_ts"] = pd.to_datetime(A.exit_ts, format="mixed", utc=True)
    key = ["ts", "tf", "direction"]
    out = ["dollars", "R", "exit_ts", "exit_reason"]
    P = P.drop(columns=out, errors="ignore").merge(
        A[key + out].drop_duplicates(key), on=key, how="left", validate="1:1")
    if P.dollars.isna().any():
        raise SystemExit(f"V1 SWAP FAILURE: {int(P.dollars.isna().sum())} rows "
                         f"without outcomes from {apath.name} — investigate before "
                         "anything downstream is trusted")
    return P


def lonmins(s: pd.Series):
    f = pd.to_datetime(s, format="mixed", utc=True).dt.tz_convert(LON)
    return (f.dt.hour * 60 + f.dt.minute).values


def serial_walk(cand: pd.DataFrame, day_stop: float = 400.0) -> pd.DataFrame:
    """One position at a time, chronological, causal — same realized day-stop
    accounting as the L4 walk. (Self-contained mirror of the audited
    london_tf_conviction implementation; kept inline so the frozen runner has no
    dependency on analysis scripts.)"""
    rows = cand.sort_values(["day", "fill_ts"], kind="mergesort").reset_index(drop=True)
    f = pd.to_datetime(rows.fill_ts, utc=True)
    x = pd.to_datetime(rows.exit_ts, utc=True)
    taken = [False] * len(rows)
    for day, g in rows.groupby("day", sort=False):
        open_until = pd.Timestamp.min.tz_localize("UTC")
        pl = 0.0
        for i in g.index:
            if pl <= -day_stop or f[i] < open_until:
                continue
            taken[i] = True
            open_until = x[i]
            pl += rows.at[i, "dollars"]
    return rows[taken].reset_index(drop=True)


def build_book(P: pd.DataFrame, config: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Returns (book, floor-passing population) for the config's pipeline."""
    c = CONFIGS[config]
    if c["cut_min"] is not None:
        P = P[lonmins(P.fill) < c["cut_min"]]
    b = lon_book(P, floor=9.5, lifetime=math.inf, cap=999).reset_index(drop=True)
    if c["veto"]:
        conv = ((b.W == 1) & (b.FAR == 1)).astype(int)
        for f, t in (("dep_thick", LON_VETO_THICK), ("dep_resist", LON_VETO_RESIST),
                     ("trigdens_30", LON_VETO_TRIGDENS)):
            conv = conv + (b[f].astype(float) > t).astype(int)
        b = b[conv.values > 0].reset_index(drop=True)
    if c["serial"]:
        b = serial_walk(b)
    return b, P


def guard_holdout_days(book: pd.DataFrame) -> None:
    sealed = set(pd.read_csv(ROOT / "data/reference/holdout_2023_24_days.csv",
                             dtype=str)["day"])
    extra = set(book.day.astype(str).str[:10]) - sealed
    if extra:
        raise SystemExit(f"SPAN VIOLATION: {len(extra)} book days outside the sealed "
                         f"list, e.g. {sorted(extra)[:3]}")


# ------------------------------------------------------------------ report pieces
def book_stats(t: pd.DataFrame, pop_days: pd.Series) -> dict:
    # maxDD is TRADE-LEVEL chronological equity — the prereg §2 reference's own
    # convention (grid audit and loser autopsy match it); day-level is the
    # late-bucket doc's convention, NOT this report's. Pinned by rehearsal.
    t = t.sort_values(["day", "fill_ts"], kind="mergesort")
    mo = t.assign(mo=t.day.astype(str).str[:7]).groupby("mo").dollars.sum()
    span_days = (pd.to_datetime(pop_days.max()) - pd.to_datetime(pop_days.min())).days + 1
    per_era = {}
    for era, g in t.groupby("era"):
        per_era[era] = dict(n=len(g), net=float(g.dollars.sum()),
                            wr=float((g.R > 0).mean()), mean_r=float(g.R.mean()),
                            dd=maxdd(g.dollars.reset_index(drop=True)))
    return dict(n=len(t), days=int(t.day.nunique()), net=float(t.dollars.sum()),
                wr=float((t.R > 0).mean()), mean_r=float(t.R.mean()),
                dd=maxdd(t.dollars.reset_index(drop=True)),
                green=int((mo > 0).sum()), months=len(mo),
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


def bucket_profile(t: pd.DataFrame, buckets) -> pd.DataFrame:
    mins = pd.Series(lonmins(t.fill), index=t.index)
    lab = pd.cut(mins, [b[0] for b in buckets] + [buckets[-1][1]], right=False,
                 labels=[b[2] for b in buckets])
    rows = []
    for name in [b[2] for b in buckets]:
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


# ------------------------------------------------------------------ anchor gate (fit)
def check_anchors(config: str, bs: dict, lifts: dict, band_stats: dict,
                  buckets: pd.DataFrame) -> list:
    A = ANCHORS[config]
    got = {
        "book trades": (bs["n"], A["n"]),
        "book days": (bs["days"], A["days"]),
        "net $": (round(bs["net"]), A["net"]),
        "WR %": (round(bs["wr"] * 100), A["wr_pct"]),
        "mean R": (round(bs["mean_r"], 3), A["mean_r"]),
        "months green": (bs["green"], A["green"]),
        "months total": (bs["months"], A["months"]),
    }
    for era in ("2025", "2026"):
        got[f"maxDD {era} $"] = (round(bs["per_era"][era]["dd"]), A["dd_era"][era])
        got[f"W/FAR lift {era}"] = (round(lifts[era]["lift"], 3), A["lift_era"][era])
        got[f"S1 band n {era}"] = (band_stats[era]["n"], A["band_n"][era])
        got[f"S1 band mean R {era}"] = (round(band_stats[era]["mean_r"], 3),
                                        A["band_r"][era])
        got[f"S1 band net {era} $"] = (round(band_stats[era]["net"]),
                                       A["band_net"][era])
    for i, name in enumerate(buckets.bucket):
        got[f"bucket {name} mean R"] = (round(float(buckets.iloc[i].mean_r), 3),
                                        A["bucket_r"][i])
    fails = []
    print(f"\nREHEARSAL ANCHOR GATE [{config}] (every number must reproduce a "
          "committed figure)")
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


def build_report(span: str, config: str, authorized_by: str, bs: dict, primary: dict,
                 s1: dict, band_stats: dict, lifts: dict, split: dict,
                 buckets: pd.DataFrame) -> str:
    is_fit = span == "fit"
    cdesc = ("rev 2a: 08:00-10:00 / V8 / no veto / no serialization" if config == "rev2a"
             else "rev 3: 08:00-09:45 / V1 BE@1R / score-0 veto (frozen literals) / "
                  "one-position-at-a-time")
    title = (f"London holdout — REHEARSAL on the fit span [{config}]" if is_fit
             else f"London holdout — THE sealed 2023/24 run [{config}] (opens once)")
    L = [f"# {title}\n\n**Config: {cdesc}.**\n\n"]
    if is_fit:
        L.append("**This is not a result — it is the dress rehearsal: the same "
                 "script, pointed at the fit span, gated on exact reproduction of "
                 "every committed anchor.** The sealed run is `--span holdout "
                 f"--config {config} --authorized-by \"...\"` with zero code "
                 "changes.\n\n")
    else:
        L.append(f"**Authorized by: {authorized_by}.** Prereg: "
                 "`docs/LONDON-PREREGISTRATION.md` rev 2a + the signed revision "
                 "(`docs/LONDON-REV3-BUNDLE.md` if rev3). Two gated tests at Sidak "
                 "alpha 0.0253. Declared resolution: a near-miss on mean R "
                 f"+{EXPECT_FWD} is not decay; a sign flip is.\n\n")
    L.append("## Items 1-8 — the book (flat 1 NQ lot)\n\n| item | value |\n|---|---|\n")
    L.append(f"| 1. trades / days with a take | {bs['n']} / {bs['days']} |\n")
    L.append(f"| 2. net P&L | ${bs['net']:+,.0f} |\n")
    L.append(f"| 3. win rate | {bs['wr'] * 100:.0f}% |\n")
    L.append(f"| 4. mean R | {bs['mean_r']:+.3f} |\n")
    L.append(f"| 5. maxDD (chronological, trade-level) | ${bs['dd']:,.0f} |\n")
    L.append(f"| 6. months green | {bs['green']}/{bs['months']} |\n")
    L.append(f"| 7. worst month | ${bs['worst_mo']:+,.0f} ({bs['worst_mo_name']}) |\n")
    L.append(f"| 8. trades per week | {bs['tpw']:.1f} |\n")
    if config == "rev3":
        L.append("\n(Under rev 3 the WR optic is structural, not a health metric: "
                 "V1 scratches ~40% of trades at BE, so wins concentrate — mean R "
                 "and net are the health metrics.)\n")
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
             "Prereg §4: no decision may be taken on this number in this run — doing "
             "so retroactively makes the family 3 tests.\n")
    L.append("\n## The two gated tests (two-sided Student t, PASS = mean > 0 and p <= alpha)\n\n")
    L.append("| test | n | mean R | SE | t | p | alpha | verdict |\n"
             "|---|---|---|---|---|---|---|---|\n")
    L.append(fmt_gate("PRIMARY — book mean R", primary))
    L.append(fmt_gate("S1 — sub-9.5 band mean R", s1))
    L.append("\nS1 is **reported, not acted on** (standing ANGUS ruling — the floor "
             "stays 9.5 regardless; the era crossing already rejected floor 5).\n")
    L.append("\nS1 band per era:\n\n| era | n | net | WR | mean R |\n|---|---|---|---|---|\n")
    for era, e in sorted(band_stats.items()):
        L.append(f"| {era} | {e['n']} | ${e['net']:+,.0f} | {e['wr'] * 100:.0f}% | "
                 f"{e['mean_r']:+.3f} |\n")
    L.append("\n## Bucket profile (DESCRIPTIVE)\n\n")
    era_cols = [c for c in buckets.columns if c.startswith("r_")]
    L.append("| bucket | n | share | WR | mean R | net |" +
             "".join(f" R {c[2:]} |" for c in era_cols) + "\n")
    L.append("|---|---|---|---|---|---|" + "---|" * len(era_cols) + "\n")
    for _, r in buckets.iterrows():
        L.append(f"| {r.bucket} | {r.n} | {r.share * 100:.0f}% | {r.wr * 100:.0f}% | "
                 f"{r.mean_r:+.3f} | ${r.net:+,.0f} |" +
                 "".join(f" {r[c]:+.3f} |" for c in era_cols) + "\n")
    if not is_fit:
        L.append("\nIf the late window is again the weakest here — on data owing "
                 "nothing to the fit-side analysis — that is properly evidenced "
                 "grounds for the window question, later, on its own prereg.\n")
    return "".join(L)


# ------------------------------------------------------------------ main
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--span", required=True, choices=["fit", "holdout"])
    ap.add_argument("--config", default="rev2a", choices=["rev2a", "rev3"])
    ap.add_argument("--authorized-by", default="",
                    help="required for --span holdout: who authorised opening the "
                         "sealed set, e.g. \"ANGUS, 2026-08-02\"")
    a = ap.parse_args()
    c = CONFIGS[a.config]

    if a.span == "holdout":
        if not a.authorized_by.strip():
            raise SystemExit(
                "SEALED SPAN REFUSED. The holdout opens once, only after ANGUS signs "
                "off (draft signature is NOT sufficient — prereg §6). If that "
                "sign-off exists, re-run with --authorized-by \"<name, date>\".")
        out_path = ROOT / "docs" / "LONDON-HOLDOUT-REPORT.md"
        if out_path.exists():
            raise SystemExit(
                f"REFUSED: {out_path.name} already exists — the holdout has been "
                "opened. A second run over the sealed span is exactly what the "
                "prereg forbids. If this is a genuine re-issue (first run crashed "
                "BEFORE reading outcomes), delete the file manually and record why "
                "in the session log.")
    else:
        out_path = ROOT / "docs" / c["rehearsal"]

    P = load_pop(a.span)
    if c["mgmt"] == "V1":
        P = swap_v1(P, a.span)
    book, Pw = build_book(P, a.config)
    band = lon_book(Pw[(Pw.risk >= 5.0) & (Pw.risk < 9.5)], floor=5.0,
                    lifetime=math.inf, cap=999)
    if a.span == "holdout":
        guard_holdout_days(book)

    bs = book_stats(book, Pw.day)
    lifts = wfar_lift(Pw)
    split = both_one_split(book)
    buckets = bucket_profile(book, c["buckets"])
    band_stats = {era: dict(n=len(g), net=float(g.dollars.sum()),
                            wr=float((g.R > 0).mean()), mean_r=float(g.R.mean()))
                  for era, g in band.groupby("era")}
    primary = t_test_two_sided(book.R)
    s1 = t_test_two_sided(band.R)

    print(f"[{a.span}/{a.config}] book: {bs['n']} trades / {bs['days']} days / net "
          f"${bs['net']:+,.0f} / WR {bs['wr'] * 100:.0f}% / mean R {bs['mean_r']:+.3f} "
          f"/ maxDD ${bs['dd']:,.0f}")
    print(f"[{a.span}/{a.config}] PRIMARY p={primary['p']:.2e}  S1 p={s1['p']:.2e}  "
          f"(alpha {ALPHA})")

    body = build_report(a.span, a.config, a.authorized_by, bs, primary, s1,
                        band_stats, lifts, split, buckets)
    out_path.write_text(body)
    print(f"\nwrote docs/{out_path.name} ({len(body):,} chars)")

    if a.span == "fit":
        fails = check_anchors(a.config, bs, lifts, band_stats, buckets)
        if fails:
            raise SystemExit(f"\nREHEARSAL FAIL [{a.config}] — {len(fails)} anchor(s) "
                             f"did not reproduce: {fails}. Fix on FIT data; the "
                             "sealed run stays shut.")
        print(f"\nREHEARSAL PASS [{a.config}] — every committed anchor reproduced. "
              "The sealed run is one command away and requires no code changes.")
    else:
        print("\nHOLDOUT REPORTED. Read at the declared resolution: a near-miss on "
              f"+{EXPECT_FWD} is not decay; a sign flip is.")


if __name__ == "__main__":
    main()
