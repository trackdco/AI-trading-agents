"""Job 2 — breakout arm (accepted_K) analysis. Spec sections 1, 3-6.

Tables A-H, G7 reconciliation, proximity-matched placebo (100 draws)
plus the stale comparator, ledger append. Holdout stays sealed; this
script never reads output/sealed/.
"""
from __future__ import annotations

import subprocess
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "scripts/vp_census")
sys.path.insert(0, "src")
import vp_lib as V
from research import placebo as P
import job2_outcomes as J2

OUT = "output/vp_census"
BOOT = 2000
SEED = 20260808
HEADLINE_K = 15
HEADLINE_T = 1.0
N_DRAWS = 100

CONT_COLS = ([f"cont_before_reentry_{T}" for T in J2.CONT_T] +
             [f"cont_before_stop_{S}" for S in J2.STOP_S] +
             ["returned_to_poc"])


def wilson(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan, np.nan)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    hw = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (p, c - hw, c + hw)


def collapse(ex):
    return (ex.sort_values(["cluster_id", "excursion_start"], kind="mergesort")
              .groupby("cluster_id", as_index=False).first())


def boot_lift(ex, cond, outcome, rng):
    g = ex.groupby("cluster_id").agg(n_all=("session_id", "size"),
                                     k_all=(outcome, "sum"),
                                     n_c=(cond, "sum"))
    kc = ex[ex[cond]].groupby("cluster_id")[outcome].sum()
    g["k_c"] = kc.reindex(g.index).fillna(0)
    A = g[["n_all", "k_all", "n_c", "k_c"]].to_numpy(float)
    if len(A) == 0 or A[:, 2].sum() == 0:
        return dict(lift=np.nan, lo=np.nan, hi=np.nan, n_cond=0)
    point = A[:, 3].sum() / A[:, 2].sum() - A[:, 1].sum() / A[:, 0].sum()
    idx = rng.integers(0, len(A), size=(BOOT, len(A)))
    s = A[idx].sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        lifts = s[:, 3] / s[:, 2] - s[:, 1] / s[:, 0]
    lifts = lifts[np.isfinite(lifts)]
    lo, hi = (np.percentile(lifts, [2.5, 97.5]) if len(lifts)
              else (np.nan, np.nan))
    return dict(lift=point, lo=lo, hi=hi, n_cond=int(A[:, 2].sum()))


def headline(ex, side):
    sx = collapse(ex[ex.side == side]) if len(ex) else ex
    cond = f"accepted_{HEADLINE_K}"
    col = f"cont_before_reentry_{HEADLINE_T}"
    if len(sx) == 0 or sx[cond].sum() == 0:
        return np.nan
    return sx.loc[sx[cond], col].mean() - sx[col].mean()


def add_accepted(ex):
    for K in V.K_SWEEP:
        ex[f"accepted_{K}"] = ~ex[f"failed_{K}"]
    return ex


def main() -> int:
    rng = np.random.default_rng(SEED)
    git_sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                             capture_output=True, text=True).stdout.strip()
    bars = V.load_master_bars()
    ex = add_accepted(pd.read_parquet(f"{OUT}/excursions_job2.parquet"))

    # ---- G7 population reconciliation --------------------------------------
    g7_ok = True
    for K in V.K_SWEEP:
        for side in ("above", "below"):
            s = ex[ex.side == side]
            if s[f"failed_{K}"].sum() + s[f"accepted_{K}"].sum() != len(s):
                g7_ok = False
    print(f"G7 population reconciliation: {'PASS' if g7_ok else 'FAIL'} "
          f"(failed+accepted==n for all K x side)")
    if not g7_ok:
        return 1

    # ---- Tables A-E ---------------------------------------------------------
    rate_rows, lift_rows = [], []

    def block(df, label):
        for col in CONT_COLS:
            k, n = df[col].sum(), len(df)
            p, lo, hi = wilson(k, n)
            rate_rows.append(dict(block=label, outcome=col, n=int(n),
                                  k=int(k), p=p, wilson_lo=lo, wilson_hi=hi))

    frames = {"FIT": ex}
    for era in ("2025H2", "2026H1"):
        frames[era] = ex[ex.era == era]
    for tag, fr in frames.items():
        for side in ("above", "below"):
            sx = fr[fr.side == side]
            cx = collapse(sx)
            for gran, df in (("per_excursion", sx), ("clustered", cx)):
                block(df, f"{tag}|{side}|{gran}|UNCOND")
                for K in V.K_SWEEP:
                    block(df[df[f"accepted_{K}"]],
                          f"{tag}|{side}|{gran}|accepted_{K}")
            for K in V.K_SWEEP:
                for col in CONT_COLS:
                    r = boot_lift(sx, f"accepted_{K}", col, rng)
                    ncl = collapse(sx[sx[f"accepted_{K}"]]).shape[0] if r["n_cond"] else 0
                    lift_rows.append(dict(
                        tag=tag, side=side, K=K, outcome=col, lift=r["lift"],
                        ci_lo=r["lo"], ci_hi=r["hi"], n_cond_exc=r["n_cond"],
                        n_cond_clusters=ncl, powered=ncl >= 30,
                        null_spanning=(np.isfinite(r["lo"]) and
                                       r["lo"] <= 0 <= r["hi"])))
    pd.DataFrame(rate_rows).to_csv(f"{OUT}/job2_tables_rates.csv", index=False)
    lifts = pd.DataFrame(lift_rows)
    lifts.to_csv(f"{OUT}/job2_tables_lift.csv", index=False)

    era_check = []
    hcol = f"cont_before_reentry_{HEADLINE_T}"
    for side in ("above", "below"):
        r25 = lifts[(lifts.tag == "2025H2") & (lifts.side == side) &
                    (lifts.outcome == hcol)].set_index("K")["lift"]
        r26 = lifts[(lifts.tag == "2026H1") & (lifts.side == side) &
                    (lifts.outcome == hcol)].set_index("K")["lift"]
        era_check.append(dict(side=side,
                              sign_agree_frac=float(np.sign(r25).eq(np.sign(r26)).mean()),
                              k_rank_spearman=float(r25.rank().corr(r26.rank(),
                                                                    method="spearman"))))
    pd.DataFrame(era_check).to_csv(f"{OUT}/job2_table_e.csv", index=False)

    # ---- Table F response surface (variants at K=15) -----------------------
    exv = pd.read_parquet(f"{OUT}/excursions_variants.parquet")
    surf = []
    fit_l = lifts[lifts.tag == "FIT"]
    for side in ("above", "below"):
        for _, r in fit_l[(fit_l.side == side) & (fit_l.outcome == hcol)].iterrows():
            surf.append(dict(axis="K", side=side, setting=r.K, lift=r.lift,
                             ci_lo=r.ci_lo, ci_hi=r.ci_hi))
    variant_axes = [("bin_width", 0.25), ("bin_width", 2.0),
                    ("va_pct", 0.68), ("va_pct", 0.75),
                    ("expansion", "single")]
    for key, v in variant_axes:
        sel = exv[(exv.construction == "bar_uniform") &
                  (exv.bin_width == (v if key == "bin_width" else 1.0)) &
                  (exv.va_pct == (v if key == "va_pct" else 0.70)) &
                  (exv.expansion == (v if key == "expansion" else "paired"))].copy()
        sel["session_id"] = pd.to_datetime(sel["session_date"]).astype(str)
        vj = add_accepted(J2.compute(sel, bars))
        for side in ("above", "below"):
            sx = vj[vj.side == side]
            r = boot_lift(sx, f"accepted_{HEADLINE_K}", hcol, rng)
            surf.append(dict(axis=key, side=side, setting=v, lift=r["lift"],
                             ci_lo=r["lo"], ci_hi=r["hi"]))
        print(f"surface variant {key}={v} done (n={len(vj)})")
    pd.DataFrame(surf).to_csv(f"{OUT}/job2_table_f_surface.csv", index=False)

    # ---- Table G power -------------------------------------------------------
    (lifts[(lifts.tag == "FIT") & (lifts.outcome == hcol)]
     [["side", "K", "n_cond_exc", "n_cond_clusters", "powered"]]
     ).to_csv(f"{OUT}/job2_table_g_power.csv", index=False)

    # ---- Table H complementarity --------------------------------------------
    hrows = []
    for side in ("above", "below"):
        for scope, df in (("all", ex[ex.side == side]),
                          (f"accepted_{HEADLINE_K}",
                           ex[(ex.side == side) & ex[f"accepted_{HEADLINE_K}"]])):
            t_rot = df["t_touched_poc"].to_numpy(float)
            t_cont = df[f"t_cont_{HEADLINE_T}"].to_numpy(float)
            rot_first = (~np.isnan(t_rot)) & (np.isnan(t_cont) | (t_rot <= t_cont))
            cont_first = (~np.isnan(t_cont)) & (np.isnan(t_rot) | (t_cont < t_rot))
            neither = np.isnan(t_rot) & np.isnan(t_cont)
            ties = int(((~np.isnan(t_rot)) & (~np.isnan(t_cont)) &
                        (t_rot == t_cont)).sum())
            hrows.append(dict(side=side, scope=scope, n=len(df),
                              rotated_first=int(rot_first.sum()),
                              continued_first=int(cont_first.sum()),
                              neither=int(neither.sum()),
                              same_minute_ties_counted_rotated=ties))
    th = pd.DataFrame(hrows)
    th.to_csv(f"{OUT}/job2_table_h.csv", index=False)
    print(th.to_string(index=False))

    # ---- placebos ------------------------------------------------------------
    profiles = pd.read_parquet(f"{OUT}/profiles.parquet")
    canon = profiles[(profiles.construction == "bar_uniform") &
                     (profiles.bin_width == 1.0) & (profiles.va_pct == 0.70) &
                     (profiles.expansion == "paired")].copy()
    anchors = P.anchor_prices(bars)
    real = {s: headline(ex, s) for s in ("above", "below")}
    print(f"real headline lifts (clustered, K={HEADLINE_K}, T={HEADLINE_T}W): "
          f"{ {k: round(v, 4) for k, v in real.items()} }")

    def run_levels(prof):
        cx = V.run_census(bars, prof)
        if len(cx) == 0:
            return cx
        cx["session_id"] = pd.to_datetime(cx["session_date"]).astype(str)
        return add_accepted(J2.compute(cx, bars))

    rows = []
    st = run_levels(P.stale(canon))
    for s in ("above", "below"):
        rows.append(dict(placebo="stale_5d", draw=0, side=s,
                         lift=headline(st, s), real=real[s]))
    for d in range(1, N_DRAWS + 1):
        pm = run_levels(P.proximity_matched(canon, anchors, rng))
        for s in ("above", "below"):
            rows.append(dict(placebo="proximity_matched", draw=d, side=s,
                             lift=headline(pm, s), real=real[s]))
        if d % 10 == 0:
            print(f"placebo draw {d}/{N_DRAWS}")
    pl = pd.DataFrame(rows)
    pl.to_csv(f"{OUT}/job2_placebos.csv", index=False)
    for s in ("above", "below"):
        dist = pl[(pl.placebo == "proximity_matched") &
                  (pl.side == s)]["lift"].dropna()
        pct = float((dist < real[s]).mean()) if len(dist) else np.nan
        stv = pl[(pl.placebo == "stale_5d") & (pl.side == s)]["lift"].iloc[0]
        print(f"[{s}] real {real[s]:+.4f} | matched median {dist.median():+.4f} "
              f"range [{dist.min():+.4f},{dist.max():+.4f}] | real pctile "
              f"{pct:.1%} of {len(dist)} | stale {stv:+.4f}")

    # ---- ledger append --------------------------------------------------------
    led = pd.read_csv(f"{OUT}/trial_ledger.csv")
    new = []
    ts_now = pd.Timestamp.now(tz="UTC").isoformat()
    for K in V.K_SWEEP:
        new.append(dict(run_id=f"job2_accepted_K{K}", K=K, bin_width=1.0,
                        va_pct=0.70, va_expansion_rule="paired",
                        construction="bar_uniform", placebo_type="none",
                        timestamp=ts_now, git_sha=git_sha))
    for key, v in variant_axes:
        new.append(dict(run_id=f"job2_surface_{key}_{v}", K=HEADLINE_K,
                        bin_width=v if key == "bin_width" else 1.0,
                        va_pct=v if key == "va_pct" else 0.70,
                        va_expansion_rule=v if key == "expansion" else "paired",
                        construction="bar_uniform", placebo_type="none",
                        timestamp=ts_now, git_sha=git_sha))
    new.append(dict(run_id="job2_placebo_stale5d", K=HEADLINE_K, bin_width=1.0,
                    va_pct=0.70, va_expansion_rule="paired",
                    construction="bar_uniform", placebo_type="stale_5d",
                    timestamp=ts_now, git_sha=git_sha))
    for d in range(1, N_DRAWS + 1):
        new.append(dict(run_id=f"job2_placebo_pm_{d:03d}", K=HEADLINE_K,
                        bin_width=1.0, va_pct=0.70, va_expansion_rule="paired",
                        construction="bar_uniform",
                        placebo_type="proximity_matched",
                        timestamp=ts_now, git_sha=git_sha))
    pd.concat([led, pd.DataFrame(new)], ignore_index=True).to_csv(
        f"{OUT}/trial_ledger.csv", index=False)
    print("job2 artifacts written; ledger rows:", len(led) + len(new))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
