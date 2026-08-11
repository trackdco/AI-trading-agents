"""LEG-SCALE ARM -- Task 4, part B: apply the OTE stop formula to the
time-bucketed MIN_LEG_HEIGHT sweep, and compare against the fit-era-derived
bar (Task 4 part A), NOT the discarded M-TABLE anchor and NOT the prior run's
1.5x-noise-floor proxy.

Valid because stop_dist_leg(x) = (1-r)*x + buffer is a strictly increasing
LINEAR function of leg_height: median/p90 of a monotonic transform equals the
transform of the median/p90, so this can be applied directly to the sweep's
already-computed leg_height_pts distributions without re-deriving raw rows.
"""
import json

from p_table_lib import CONFIG

R_VALUES = [0.50, 0.62, 0.705, 0.79]


def apply_r(leg_dist, r, buf):
    if not leg_dist:
        return None
    return {k: round((1 - r) * leg_dist[k] + buf, 3)
           for k in ("median", "p25", "p75", "p90") if k in leg_dist}


def main():
    sweep = json.load(open("output/p_table_geometry_sweep_timebucketed.json"))
    bar = json.load(open("output/p_table_leg_scale_bar.json"))
    buf = CONFIG["STOP_BUFFER_PTS"]
    bar_pts = {"ny_am": bar["ny_am"]["DECLARED_BAR_pts"],
              "london": bar["london"]["DECLARED_BAR_pts"]}

    out = {}
    for cell_key, cell in sweep["cells"].items():
        cell_out = {}
        for tf, tv in cell["per_tf"].items():
            bucket_out = {}
            for bucket_key, bd in tv.get("by_time_bucket", {}).items():
                session = bucket_key.split("|")[0]
                leg_dist = bd.get("leg_height_pts")
                if not leg_dist:
                    continue
                per_r = {}
                for r in R_VALUES:
                    sd = apply_r(leg_dist, r, buf)
                    bar_here = bar_pts.get(session)
                    per_r[str(r)] = dict(
                        stop_dist_leg_pts=sd,
                        clears_fit_era_bar=(bool(sd["median"] >= bar_here)
                                            if sd and bar_here else None))
                bucket_out[bucket_key] = dict(
                    n=bd["n"], leg_height_pts=leg_dist, per_r=per_r)
            if bucket_out:
                cell_out[tf] = bucket_out
        if cell_out:
            out[cell_key] = cell_out

    json.dump(dict(fit_era_bar_pts=bar_pts, by_cell=out),
             open("output/p_table_leg_scale_sweep_applied.json", "w"), indent=1)

    # headline scan: any cell/tf/bucket/r clearing the bar with n>=5?
    hits = []
    for cell_key, cell in out.items():
        for tf, buckets in cell.items():
            for bucket_key, bd in buckets.items():
                if bd["n"] < 5:
                    continue
                for r, rv in bd["per_r"].items():
                    if rv["clears_fit_era_bar"]:
                        hits.append(dict(cell=cell_key, tf=tf, bucket=bucket_key,
                                         r=r, n=bd["n"],
                                         median_leg=bd["leg_height_pts"]["median"],
                                         stop_leg=rv["stop_dist_leg_pts"]["median"]))
    print(f"cells/tf/bucket/r combinations clearing the fit-era bar "
         f"(n>=5): {len(hits)}")
    for h in hits[:30]:
        print(" ", h)
    json.dump(hits, open("output/p_table_leg_scale_sweep_hits.json", "w"), indent=1)


if __name__ == "__main__":
    main()
