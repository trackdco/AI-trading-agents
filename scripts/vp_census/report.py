"""Job 1 reporting — Tables A-G + placebos (spec section 5).

Sides are NEVER pooled (spec 3.1/5.4): every table carries a `side`
dimension. Every proportion gets a Wilson 95% interval. Lift CIs come
from a cluster bootstrap (2,000 reps, resampling clusters); where the
per-excursion and clustered reads disagree, the clustered number
governs (spec 3.2).

HOLDOUT REFUSAL (spec 6.4): this script refuses to touch
output/sealed/ unless invoked with --unseal AND
docs/PREREG-vp-excursion-census.md exists in the working tree. Job 1
never unseals.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "scripts/vp_census")
import vp_lib as V

OUT = "output/vp_census"
BOOT = 2000
SEED = 20260807
HEADLINE_K = 15


def refuse_sealed(argv):
    wants = any(a == "--unseal" for a in argv)
    prereg = os.path.exists("docs/PREREG-vp-excursion-census.md")
    if wants and not prereg:
        print("REFUSED: --unseal without docs/PREREG-vp-excursion-census.md")
        raise SystemExit(2)
    if not wants:
        return False
    return True


def wilson(k: float, n: float, z: float = 1.96):
    if n == 0:
        return (np.nan, np.nan, np.nan)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    hw = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (p, c - hw, c + hw)


def collapse_clusters(ex: pd.DataFrame) -> pd.DataFrame:
    """One observation per cluster: the cluster's FIRST excursion."""
    return (ex.sort_values(["cluster_id", "excursion_start"], kind="mergesort")
              .groupby("cluster_id", as_index=False).first())


OUTCOLS = (["touched_poc", "reached_opposite_edge"] +
           [f"poc_before_stop_{S}" for S in V.STOP_TICKS])


def rates_block(df: pd.DataFrame, label: str) -> list[dict]:
    rows = []
    for col in OUTCOLS:
        k, n = df[col].sum(), len(df)
        p, lo, hi = wilson(k, n)
        rows.append(dict(block=label, outcome=col, n=int(n), k=int(k),
                         p=p, wilson_lo=lo, wilson_hi=hi))
    rows.append(dict(block=label, outcome="median_t_touched_poc",
                     n=int(df["touched_poc"].sum()), k=np.nan,
                     p=df.loc[df.touched_poc, "t_touched_poc"].median(),
                     wilson_lo=np.nan, wilson_hi=np.nan))
    return rows


def cluster_boot_lift(ex: pd.DataFrame, cond: str, outcome: str,
                      rng: np.random.Generator) -> dict:
    """lift = P(outcome | cond) - P(outcome), cluster-bootstrapped."""
    g = ex.groupby("cluster_id").agg(
        n_all=("session_id", "size"), k_all=(outcome, "sum"),
        n_c=(cond, "sum"),
        k_c=(outcome, lambda s: 0))  # placeholder, filled below
    kc = ex[ex[cond]].groupby("cluster_id")[outcome].sum()
    g["k_c"] = kc.reindex(g.index).fillna(0)
    A = g[["n_all", "k_all", "n_c", "k_c"]].to_numpy(float)
    nclus = len(A)
    if nclus == 0 or A[:, 2].sum() == 0:
        return dict(lift=np.nan, lo=np.nan, hi=np.nan, n_cond=0)
    point = A[:, 3].sum() / A[:, 2].sum() - A[:, 1].sum() / A[:, 0].sum()
    idx = rng.integers(0, nclus, size=(BOOT, nclus))
    s = A[idx].sum(axis=1)          # BOOT x 4
    with np.errstate(invalid="ignore", divide="ignore"):
        lifts = s[:, 3] / s[:, 2] - s[:, 1] / s[:, 0]
    lifts = lifts[np.isfinite(lifts)]
    lo, hi = np.percentile(lifts, [2.5, 97.5]) if len(lifts) else (np.nan, np.nan)
    return dict(lift=point, lo=lo, hi=hi, n_cond=int(A[:, 2].sum()))


def side_tables(ex: pd.DataFrame, tag: str, rng) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Tables A/B (rates) and C (lift) for one excursion set, side-split,
    per-excursion AND clustered."""
    rate_rows, lift_rows = [], []
    for side in ("above", "below"):
        sx = ex[ex.side == side]
        cx = collapse_clusters(sx)
        for gran, df in (("per_excursion", sx), ("clustered", cx)):
            rate_rows += rates_block(df, f"{tag}|{side}|{gran}|UNCOND")
            for K in V.K_SWEEP:
                cond = f"failed_{K}"
                sub = df[df[cond]]
                rate_rows += rates_block(sub, f"{tag}|{side}|{gran}|failed_{K}")
        for K in V.K_SWEEP:
            for outcome in OUTCOLS:
                r = cluster_boot_lift(sx, f"failed_{K}", outcome, rng)
                n_clus_cond = collapse_clusters(sx[sx[f"failed_{K}"]]).shape[0] \
                    if r["n_cond"] else 0
                lift_rows.append(dict(
                    tag=tag, side=side, K=K, outcome=outcome,
                    lift=r["lift"], ci_lo=r["lo"], ci_hi=r["hi"],
                    n_cond_exc=r["n_cond"], n_cond_clusters=n_clus_cond,
                    powered=n_clus_cond >= 30,
                    null_spanning=(np.isfinite(r["lo"]) and r["lo"] <= 0 <= r["hi"])))
    return pd.DataFrame(rate_rows), pd.DataFrame(lift_rows)


# ------------------------------------------------------------- placebos

def census_with_levels(bars, prof: pd.DataFrame) -> pd.DataFrame:
    ex = V.run_census(bars, prof)
    if len(ex):
        ex["session_id"] = pd.to_datetime(ex["session_date"]).astype(str)
    return ex


def stale_profiles(prof: pd.DataFrame, shift: int = 5) -> pd.DataFrame:
    p = prof.sort_values("session_date", kind="mergesort").reset_index(drop=True)
    lv = p[["vah", "val", "poc"]].shift(shift)
    out = p.copy()
    out[["vah", "val", "poc"]] = lv
    out.loc[out[["vah", "val", "poc"]].isna().any(axis=1), "profile_status"] = "NO_DONOR"
    return out


def shuffled_profiles(prof: pd.DataFrame, rng) -> pd.DataFrame:
    p = prof.sort_values("session_date", kind="mergesort").reset_index(drop=True)
    ok = p[p.profile_status == "OK"].reset_index()
    rng_range = (ok.win_high - ok.win_low).to_numpy()
    rel = np.stack([
        (ok.vah - ok.win_low) / (ok.win_high - ok.win_low),
        (ok.val - ok.win_low) / (ok.win_high - ok.win_low),
        (ok.poc - ok.win_low) / (ok.win_high - ok.win_low)], axis=1)
    perm = rng.permutation(len(ok))
    # forbid self-assignment (redraw fixed points onto a neighbour)
    for i in np.where(perm == np.arange(len(ok)))[0]:
        j = (i + 1) % len(ok)
        perm[i], perm[j] = perm[j], perm[i]
    donor_rel = rel[perm]
    out = p.copy()
    lows = ok.win_low.to_numpy()
    spans = rng_range
    vah = np.round((lows + donor_rel[:, 0] * spans) / V.TICK) * V.TICK
    val = np.round((lows + donor_rel[:, 1] * spans) / V.TICK) * V.TICK
    poc = np.round((lows + donor_rel[:, 2] * spans) / V.TICK) * V.TICK
    out.loc[ok["index"], "vah"] = vah
    out.loc[ok["index"], "val"] = val
    out.loc[ok["index"], "poc"] = poc
    return out


def headline_lift(ex: pd.DataFrame, side: str) -> float:
    sx = collapse_clusters(ex[ex.side == side]) if len(ex) else ex
    if len(sx) == 0 or sx[f"failed_{HEADLINE_K}"].sum() == 0:
        return np.nan
    return (sx.loc[sx[f"failed_{HEADLINE_K}"], "touched_poc"].mean()
            - sx["touched_poc"].mean())


def main() -> int:
    refuse_sealed(sys.argv)   # Job 1: never called with --unseal
    rng = np.random.default_rng(SEED)
    bars = V.load_master_bars()
    ex = pd.read_parquet(f"{OUT}/excursions.parquet")
    exv = pd.read_parquet(f"{OUT}/excursions_variants.parquet")
    profiles = pd.read_parquet(f"{OUT}/profiles.parquet")

    canon_prof = profiles[(profiles.construction == "bar_uniform") &
                          (profiles.bin_width == 1.0) &
                          (profiles.va_pct == 0.70) &
                          (profiles.expansion == "paired")].copy()

    # ---- Tables A-D (pooled-era) + E (per era) ---------------------------
    rates_all, lifts_all = side_tables(ex, "FIT", rng)
    era_frames_r, era_frames_l = [], []
    for era in ("2025H2", "2026H1"):
        r, l = side_tables(ex[ex.era == era], era, rng)
        era_frames_r.append(r)
        era_frames_l.append(l)
    rates = pd.concat([rates_all] + era_frames_r, ignore_index=True)
    lifts = pd.concat([lifts_all] + era_frames_l, ignore_index=True)
    rates.to_csv(f"{OUT}/tables_rates.csv", index=False)
    lifts.to_csv(f"{OUT}/tables_lift.csv", index=False)

    # era agreement on sign and K ranking (headline outcome)
    era_check = []
    for side in ("above", "below"):
        rows = {}
        for era, lf in zip(("2025H2", "2026H1"), era_frames_l):
            sub = lf[(lf.side == side) & (lf.outcome == "touched_poc")]
            rows[era] = sub.set_index("K")["lift"]
        sgn = np.sign(rows["2025H2"]).eq(np.sign(rows["2026H1"]))
        rank_corr = rows["2025H2"].rank().corr(rows["2026H1"].rank(),
                                               method="spearman")
        era_check.append(dict(side=side,
                              sign_agree_frac=float(sgn.mean()),
                              k_rank_spearman=float(rank_corr)))
    pd.DataFrame(era_check).to_csv(f"{OUT}/table_e_era_agreement.csv", index=False)

    # ---- Table F response surface ----------------------------------------
    surf = []
    for side in ("above", "below"):
        base = lifts_all[(lifts_all.side == side) &
                         (lifts_all.outcome == "touched_poc")]
        for _, r in base.iterrows():
            surf.append(dict(axis="K", side=side, setting=r.K, lift=r.lift,
                             ci_lo=r.ci_lo, ci_hi=r.ci_hi))
        for axis, key, vals in (("bin_width", "bin_width", (0.25, 1.0, 2.0)),
                                ("va_pct", "va_pct", (0.68, 0.70, 0.75)),
                                ("expansion", "expansion", ("paired", "single"))):
            for v in vals:
                m = exv[(exv.construction == "bar_uniform") & (exv.side == side)]
                m = m[(m.bin_width == (v if key == "bin_width" else 1.0)) &
                      (m.va_pct == (v if key == "va_pct" else 0.70)) &
                      (m.expansion == (v if key == "expansion" else "paired"))]
                if len(m) == 0:
                    continue
                m = m.copy()
                m["session_id"] = pd.to_datetime(m["session_date"]).astype(str)
                r = cluster_boot_lift(m, f"failed_{HEADLINE_K}", "touched_poc", rng)
                surf.append(dict(axis=axis, side=side, setting=v, lift=r["lift"],
                                 ci_lo=r["lo"], ci_hi=r["hi"]))
    pd.DataFrame(surf).to_csv(f"{OUT}/table_f_surface.csv", index=False)

    # ---- placebos ----------------------------------------------------------
    placebo_rows = []
    real = {s: headline_lift(ex, s) for s in ("above", "below")}

    stale = stale_profiles(canon_prof)
    ex_stale = census_with_levels(bars, stale)
    for s in ("above", "below"):
        placebo_rows.append(dict(placebo="stale_5d", draw=0, side=s,
                                 lift=headline_lift(ex_stale, s),
                                 real=real[s]))
    for d in range(1, 21):
        shp = shuffled_profiles(canon_prof, rng)
        ex_sh = census_with_levels(bars, shp)
        for s in ("above", "below"):
            placebo_rows.append(dict(placebo="shuffled_rel", draw=d, side=s,
                                     lift=headline_lift(ex_sh, s),
                                     real=real[s]))
        print(f"placebo draw {d}/20 done (n={len(ex_sh)})")
    pl = pd.DataFrame(placebo_rows)
    pl.to_csv(f"{OUT}/placebos.csv", index=False)
    for s in ("above", "below"):
        dist = pl[(pl.placebo == "shuffled_rel") & (pl.side == s)]["lift"].dropna()
        if len(dist) and np.isfinite(real[s]):
            pct = (dist < real[s]).mean()
            print(f"shuffled placebo [{s}]: real {real[s]:+.4f} sits at "
                  f"percentile {pct:.2%} of {len(dist)} draws "
                  f"(p-floor 1/21={1/21:.3f})")
        st = pl[(pl.placebo == "stale_5d") & (pl.side == s)]["lift"]
        print(f"stale placebo [{s}]: {float(st.iloc[0]) if len(st) else np.nan:+.4f} "
              f"vs real {real[s]:+.4f}")

    # ---- Table G power summary --------------------------------------------
    g = (lifts_all[lifts_all.outcome == "touched_poc"]
         [["side", "K", "n_cond_exc", "n_cond_clusters", "powered"]])
    g.to_csv(f"{OUT}/table_g_power.csv", index=False)
    print("report artifacts written to", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
