#!/usr/bin/env python3
"""BLIND re-implementation of SPEC.md (NQ VWAP/BB/Profile strategy, v1.0 + A1..A13).

Written from SPEC.md alone.  Pure standard library (no numpy/pandas/scipy).

Outputs blind_trades.json: one object per ADMITTED trade,
    {"session_date", "signal_minute", "entry_tf", "direction", "entry", "stop", "target"}
sorted by (session_date, signal_minute, entry_tf).

NO outcome is computed.  The only forward simulation is the one needed to decide when the
one-position-at-a-time constraint (SPEC §5.6 / §10.1(2)) releases.

Every numeric constant traces to SPEC.md; see CONSTANTS block and AMBIGUITIES.md.
"""

import sys

# The Debian dist-packages tree on this box shadows stdlib modules; drop it before
# anything else is imported.
sys.path = [p for p in sys.path if p != "/usr/lib/python3/dist-packages"]

import json
import math
import os
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bars_api  # noqa: E402   (bar access only; contains no strategy logic)


# ---------------------------------------------------------------------------
# CONSTANTS  — every one traced to SPEC.md
# ---------------------------------------------------------------------------

TICK = 0.25                 # NQ tick.  A5: "10.00 points (40 ticks)" => tick = 0.25
CLUSTER_TOL = 10.00         # §3 tolerance, CALIBRATE start "~10 NQ pts"; pinned by A13
                            #   ("5.00 points ... HALF the §3 cluster tolerance")
TOL_HALF = CLUSTER_TOL / 2  # A13 right-hand side = 5.00
Z95 = 1.95996               # A13, stated literally

BB_PERIOD = 20              # §2 table "Bollinger Bands | 20, SMA, close, 2σ"
BB_SIGMA = 2.0              # §2 (bands themselves are not §3 cluster levels; basis only)

ATR_PERIOD = 20             # §3 "range >= k x ATR(20)"
ATR_K = 1.0                 # §3 CALIBRATE start k = 1.0
B_MIN = 0.6                 # §3 displacement body/range, CALIBRATE start 0.6
EXTREME_QUARTILE = 0.25     # §3 "close within the extreme quartile of the candle's range"

STOP_BUFFER = 1 * TICK      # A2 "stop buffer = 1 tick beyond the wick extreme"
STOP_MIN = 10.00            # A5 "effective stop = max(structural stop, 10.00 pt)"

RR_FLOOR = 1.5              # §6.5 / A4 "first level whose front-run-adjusted distance is >= 1.5R"
FRONT_RUN_F = 2.5           # §6.4 F: CALIBRATE (start 2-3 NQ pts) -> midpoint  [see AMBIGUITIES A-08]

POC_BIN = 1.00              # A2 "volume-profile bin = 1.00 pt"
FRACTAL_N = 2               # A2 "15m fractal swings N=2"
HTF_TF = 15                 # §1 "Context TFs: 15m for HTF trend/range flag"

CONF_MIN_WITH_TREND = 2     # §7 "Confluence minimum: 3 counter-trend; 2 with-trend"
CONF_MIN_COUNTER = 3
SESSION_CAP = 3             # §10.1(3) / §10.2 "Max trades/day: 3"

ENTRY_TFS = (1, 2, 3, 5)    # §1 "Entry TFs: 1m, 2m, 3m, 5m"

# session index arithmetic:  index = mm + 360 for mm < 1080 ; index = mm - 1080 for mm >= 1080
FIRST_SIGNAL_MIN = 9 * 60 + 36    # 576  — A1 "first tradeable signal bar 09:36"
LAST_SIGNAL_MIN = 15 * 60 + 59    # 959  — A1 entry window ends 16:00 ET
NY_ANCHOR_IDX = 9 * 60 + 30 + 360   # 930 — §2 NY VWAP anchored 09:30 ET
EOD_FLATTEN_IDX = 15 * 60 + 55 + 360  # 1315 — §1 "default 15:55 ET"
LAST_FILL_IDX = 16 * 60 + 360         # 1320 — §1 entry window closes 16:00 ET
N_SESSION_IDX = 1380

SEAL_DATE = "2025-01-31"    # TASK.md — never process a session after this


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# OPT — the genuine forks in the spec.  Defaults are the readings argued for in
# AMBIGUITIES.md; the alternatives are kept switchable so the sensitivity of the
# trade count to each fork is measurable rather than asserted.
# ---------------------------------------------------------------------------
OPT = {
    "cluster": "mutual",        # "mutual": all members within tol of each other (default)
                                # "chain" : single-linkage, consecutive gap <= tol
    "atr": "sma",               # "sma" (default) | "wilder"
    "range_conf": 2,            # confluence minimum when the HTF flag is "range"
    "invalidation": "with",     # "with": opposing band = the one the trade heads INTO
                                # "against": the band behind the trade
    "menu_prior": True,         # include prior-day / prior-week H/L in the §6 target menu
}

DEBUG = {}   # diagnostics sink; never read by the strategy logic


def idx_of_minute(mm):
    return (mm + 360) if mm < 1080 else (mm - 1080)


def _mean(xs):
    return sum(xs) / len(xs)


# ---------------------------------------------------------------------------
# per-session indicator precomputation
# ---------------------------------------------------------------------------

def running_vwap(bars, anchor_idx):
    """Volume-weighted VWAP + volume-weighted sigma of typical price, from 1-minute bars.

    §2.1/A8: both anchors computed from 1-minute bars, ONE canonical series.
    A2: typical price = HLC/3 ("standard TradingView VWAP").
    sigma^2 = sum(v*tp^2)/sum(v) - vwap^2   (volume-weighted population variance).

    Returns (mid[], sig[], n[]) indexed 0..1379 ; entries are None before the anchor
    or while cumulative volume is zero.
    """
    mid = [None] * N_SESSION_IDX
    sig = [None] * N_SESSION_IDX
    nobs = [0] * N_SESSION_IDX
    cv = cpv = cp2v = 0.0
    n = 0
    for i in range(N_SESSION_IDX):
        if i >= anchor_idx and i in bars:
            o, h, l, c, v = bars[i]
            tp = (h + l + c) / 3.0
            v = float(v)
            cv += v
            cpv += tp * v
            cp2v += tp * tp * v
            n += 1
        if i >= anchor_idx and cv > 0.0:
            m = cpv / cv
            var = cp2v / cv - m * m
            if var < 0.0:
                var = 0.0
            mid[i] = m
            sig[i] = math.sqrt(var)
        nobs[i] = n
    return mid, sig, nobs


def running_poc(bars):
    """Session volume profile POC (A8: 1-minute bars; A2: 1.00 pt bins).

    Each bar's volume is spread uniformly over the 1.00-pt bins its [low, high] spans.
    POC price is reported at the bin midpoint.  Ties -> lowest bin (deterministic).
    Returns poc[] indexed 0..1379 (None until any volume seen).
    """
    poc = [None] * N_SESSION_IDX
    prof = defaultdict(float)
    best_v = -1.0
    best_b = None
    for i in range(N_SESSION_IDX):
        if i in bars:
            o, h, l, c, v = bars[i]
            b0 = int(math.floor(l / POC_BIN))
            b1 = int(math.floor(h / POC_BIN))
            nb = b1 - b0 + 1
            share = float(v) / nb
            for b in range(b0, b1 + 1):
                prof[b] += share
                pv = prof[b]
                if pv > best_v:
                    best_v = pv
                    best_b = b
                elif pv == best_v and b < best_b:
                    best_b = b
        if best_b is not None:
            poc[i] = (best_b + 0.5) * POC_BIN
    return poc


def build_tf_bars(bars, k):
    """Aggregate 1-minute bars onto the fixed k-minute grid anchored at session index 0.

    Session index 930 = 09:30 ET is divisible by 1, 2, 3, 5 and 15, so this grid is
    identical whether anchored at 18:00 ET, at midnight ET or at the 09:30 RTH open.
    Bars are OPEN-LABELLED (bars_api docstring); the slot [s, s+k-1] closes at s+k-1.

    Returns list of dicts, ascending, only for slots holding >= 1 one-minute bar.
    """
    out = []
    for s in range(0, N_SESSION_IDX, k):
        o = h = l = c = None
        for i in range(s, min(s + k, N_SESSION_IDX)):
            b = bars.get(i)
            if b is None:
                continue
            if o is None:
                o, h, l = b[0], b[1], b[2]
            else:
                if b[1] > h:
                    h = b[1]
                if b[2] < l:
                    l = b[2]
            c = b[3]
        if o is None:
            continue
        out.append({"start": s, "last": s + k - 1, "o": o, "h": h, "l": l, "c": c})
    return out


def attach_bb_atr(tfb):
    """BB basis (20, SMA, close) per entry timeframe (A8: BB stays per-TF), and ATR(20).

    ATR uses the simple mean of the last 20 true ranges: the spec gives no smoothing
    convention and its house convention for a 20-period average is SMA (§2 table).
    """
    closes = [b["c"] for b in tfb]
    trs = []
    prev_c = None
    for b in tfb:
        tr = b["h"] - b["l"]
        if prev_c is not None:
            tr = max(tr, abs(b["h"] - prev_c), abs(b["l"] - prev_c))
        trs.append(tr)
        prev_c = b["c"]
    for j, b in enumerate(tfb):
        if j + 1 >= BB_PERIOD:
            win = closes[j + 1 - BB_PERIOD: j + 1]
            m = _mean(win)
            var = _mean([(x - m) ** 2 for x in win])
            b["bb_ma"] = m
            b["bb_up"] = m + BB_SIGMA * math.sqrt(var)
            b["bb_dn"] = m - BB_SIGMA * math.sqrt(var)
        else:
            b["bb_ma"] = None
        if j + 1 >= ATR_PERIOD:
            if OPT["atr"] == "wilder":
                prev = tfb[j - 1].get("atr") if j > 0 else None
                b["atr"] = (_mean(trs[:ATR_PERIOD]) if prev is None
                            else (prev * (ATR_PERIOD - 1) + trs[j]) / ATR_PERIOD)
            else:
                b["atr"] = _mean(trs[j + 1 - ATR_PERIOD: j + 1])
        else:
            b["atr"] = None
    return tfb


def fractal_swings(b15):
    """A2 + A10: 15m fractal swings, N = 2.

    swing high at i:  H[i] >  H[i-1..i-N]  AND  H[i] >= H[i+1..i+N]   (A10)
    swing low  at i:  L[i] <  L[i-1..i-N]  AND  L[i] <= L[i+1..i+N]
    "The first bar of a plateau is the swing."

    Confirmed once bar i+N has completed -> confirm index = last 1-minute index of bar i+N.
    Returns two lists of (confirm_idx, price), ascending by confirm_idx.
    """
    highs, lows = [], []
    n = len(b15)
    for i in range(FRACTAL_N, n - FRACTAL_N):
        H = b15[i]["h"]
        if all(H > b15[i - d]["h"] for d in range(1, FRACTAL_N + 1)) and \
           all(H >= b15[i + d]["h"] for d in range(1, FRACTAL_N + 1)):
            highs.append((b15[i + FRACTAL_N]["last"], H))
        L = b15[i]["l"]
        if all(L < b15[i - d]["l"] for d in range(1, FRACTAL_N + 1)) and \
           all(L <= b15[i + d]["l"] for d in range(1, FRACTAL_N + 1)):
            lows.append((b15[i + FRACTAL_N]["last"], L))
    return highs, lows


def htf_flag(sw_h, sw_l, e):
    """A2: HH+HL => uptrend ; LH+LL => downtrend ; else range.  Uses swings confirmed by e."""
    hs = [p for (ci, p) in sw_h if ci <= e]
    ls = [p for (ci, p) in sw_l if ci <= e]
    if len(hs) < 2 or len(ls) < 2:
        return "range"
    hh = hs[-1] > hs[-2]
    lh = hs[-1] < hs[-2]
    hl = ls[-1] > ls[-2]
    ll = ls[-1] < ls[-2]
    if hh and hl:
        return "uptrend"
    if lh and ll:
        return "downtrend"
    return "range"


# ---------------------------------------------------------------------------
# §3 confluence clusters
# ---------------------------------------------------------------------------

def find_clusters(levels):
    """levels: list of (type_tag, price).

    §3: "Confluence cluster: >=2 of {...} within proximity tolerance."
    A cluster is a maximal set of levels all MUTUALLY within CLUSTER_TOL (span <= tol),
    which is what "within proximity tolerance" states literally.  Maximal windows only.
    """
    lv = sorted(levels, key=lambda t: t[1])
    n = len(lv)
    if OPT["cluster"] == "chain":
        out, cur = [], [lv[0]] if n else []
        for k in range(1, n):
            if lv[k][1] - lv[k - 1][1] <= CLUSTER_TOL:
                cur.append(lv[k])
            else:
                if len(cur) >= 2:
                    out.append(cur)
                cur = [lv[k]]
        if len(cur) >= 2:
            out.append(cur)
        return out
    spans = []
    for i in range(n):
        j = i
        while j + 1 < n and lv[j + 1][1] - lv[i][1] <= CLUSTER_TOL:
            j += 1
        if j > i:
            spans.append((i, j))
    maximal = []
    for (a, b) in spans:
        if any((a2 <= a and b <= b2) and (a2, b2) != (a, b) for (a2, b2) in spans):
            continue
        if (a, b) not in maximal:
            maximal.append((a, b))
    return [lv[a:b + 1] for (a, b) in maximal]


def cluster_types(cl):
    return set(t for (t, _) in cl)


# ---------------------------------------------------------------------------
# main per-session engine
# ---------------------------------------------------------------------------

def process_session(date, bars, prior):
    """Returns (trades, stats) for one session.  prior = dict of prior-day / prior-week H/L."""
    assert date <= SEAL_DATE, "REFUSING to process sealed session %s" % date

    stats = defaultdict(int)

    dv_mid, dv_sig, _dv_n = running_vwap(bars, 0)
    ny_mid, ny_sig, ny_n = running_vwap(bars, NY_ANCHOR_IDX)
    poc = running_poc(bars)

    b15 = build_tf_bars(bars, HTF_TF)
    sw_h, sw_l = fractal_swings(b15)

    tfb = {}
    for k in ENTRY_TFS:
        tfb[k] = attach_bb_atr(build_tf_bars(bars, k))

    # ---- A13: NY VWAP sigma-band cluster eligibility, evaluated live per instant ----
    def ny_bands_eligible(e):
        s = ny_sig[e]
        n = ny_n[e]
        if s is None or n < 2:
            return False
        return Z95 * s / math.sqrt(2.0 * (n - 1)) <= TOL_HALF

    # ---- §3 level set at instant e (everything except the per-TF BB MA) ----
    common_cache = {}

    def common_levels(e):
        got = common_cache.get(e)
        if got is not None:
            return got
        lv = []
        if dv_mid[e] is not None:
            lv.append(("VWAP", dv_mid[e]))
            for kk in (1, 2, 3):                      # §3: daily VWAP mid/+-1/+-2/+-3 sigma
                lv.append(("VWAP", dv_mid[e] + kk * dv_sig[e]))
                lv.append(("VWAP", dv_mid[e] - kk * dv_sig[e]))
        if e >= NY_ANCHOR_IDX and ny_mid[e] is not None:
            lv.append(("VWAP", ny_mid[e]))            # §3: NY mid always (post-9:30)
            if ny_bands_eligible(e):                  # A13: sigma bands only when eligible
                lv.append(("VWAP", ny_mid[e] + ny_sig[e]))
                lv.append(("VWAP", ny_mid[e] - ny_sig[e]))
        if poc[e] is not None:
            lv.append(("POC", poc[e]))
        common_cache[e] = lv
        return lv

    # ---- §6 target menu at instant e (computable members only; see AMBIGUITIES) ----
    menu_cache = {}

    def target_menu(e):
        got = menu_cache.get(e)
        if got is not None:
            return got
        lv = []
        if dv_mid[e] is not None:
            lv.append(dv_mid[e])
            for kk in (1, 2):                          # §6 menu: "VWAP +-1sigma/+-2sigma"
                lv.append(dv_mid[e] + kk * dv_sig[e])
                lv.append(dv_mid[e] - kk * dv_sig[e])
        if e >= NY_ANCHOR_IDX and ny_mid[e] is not None:
            lv.append(ny_mid[e])
            for kk in (1, 2):
                lv.append(ny_mid[e] + kk * ny_sig[e])
                lv.append(ny_mid[e] - kk * ny_sig[e])
        if poc[e] is not None:
            lv.append(poc[e])
        if OPT["menu_prior"]:
            for key in ("pdh", "pdl", "pwh", "pwl"):
                if prior.get(key) is not None:
                    lv.append(prior[key])
        menu_cache[e] = lv
        return lv

    def pick_target(e, entry, R, direction):
        """§6.1 + A4: walk opposing menu levels outward from entry; first whose
        front-run-adjusted distance clears the RR floor.  §6.4: working target = level -+ F."""
        need = RR_FLOOR * R
        if direction == "long":
            cands = sorted(x for x in target_menu(e) if x > entry)
            for lvl in cands:
                wt = lvl - FRONT_RUN_F
                if wt - entry >= need:
                    return wt
        else:
            cands = sorted((x for x in target_menu(e) if x < entry), reverse=True)
            for lvl in cands:
                wt = lvl + FRONT_RUN_F
                if entry - wt >= need:
                    return wt
        return None

    # ---- candidate generation ----
    candidates = []
    for k in ENTRY_TFS:
        for b in tfb[k]:
            e = b["last"]
            if e >= N_SESSION_IDX:
                continue
            m = bars_api.minute_of_day(e)
            if m < FIRST_SIGNAL_MIN or m > LAST_SIGNAL_MIN:
                continue
            bb = b["bb_ma"]
            if bb is None:
                continue
            o, h, l, c = b["o"], b["h"], b["l"], b["c"]
            rng = h - l
            body_low = min(o, c)
            body_high = max(o, c)
            atr = b["atr"]

            lv = list(common_levels(e))
            lv.append(("BB", bb))
            clusters = find_clusters(lv)
            if not clusters:
                continue
            stats["bars_with_cluster"] += 1

            flag = htf_flag(sw_h, sw_l, e)
            eligible_ny = ny_bands_eligible(e)

            for cl in clusters:
                lmin = cl[0][1]
                lmax = cl[-1][1]
                prices = [p for (_t, p) in cl]

                fired = []   # (direction, kind)

                # ---- §3 rejection block ----
                # (a) trades into the cluster, (b) CLOSES back on the trade side of ALL
                # cluster levels, (c) leaves a wick through/into them.
                if l <= lmax and c > lmax and l < body_low and body_low >= lmin:
                    fired.append(("long", "rejection"))
                if h >= lmin and c < lmin and h > body_high and body_high <= lmax:
                    fired.append(("short", "rejection"))

                # ---- §3 displacement ----
                if atr is not None and rng > 0:
                    if c > o:
                        crossed = sum(1 for p in prices if o < p < c)
                        if (crossed >= 2 and (c - o) / rng >= B_MIN
                                and c >= l + (1.0 - EXTREME_QUARTILE) * rng
                                and rng >= ATR_K * atr):
                            fired.append(("long", "displacement"))
                    elif c < o:
                        crossed = sum(1 for p in prices if c < p < o)
                        if (crossed >= 2 and (o - c) / rng >= B_MIN
                                and c <= l + EXTREME_QUARTILE * rng
                                and rng >= ATR_K * atr):
                            fired.append(("short", "displacement"))

                if not fired:
                    continue

                nconf = len(cluster_types(cl))

                for direction, kind in fired:
                    stats["raw_triggers"] += 1

                    # ---- §7 confluence minimum (§4: counter-trend RAISES the requirement) ----
                    if flag == "uptrend":
                        htf = "with_trend" if direction == "long" else "counter_trend"
                    elif flag == "downtrend":
                        htf = "with_trend" if direction == "short" else "counter_trend"
                    else:
                        htf = "range"
                    if htf == "counter_trend":
                        need = CONF_MIN_COUNTER
                    elif htf == "range":
                        need = OPT["range_conf"]
                    else:
                        need = CONF_MIN_WITH_TREND
                    if nconf < need:
                        stats["rej_confluence"] += 1
                        continue

                    # ---- §7 invalidation-at-entry: trigger candle touching the opposing
                    #      NY VWAP +-1 sigma.  A8/A13: ineligible sigma bands may not serve
                    #      as the §7 invalidation reference.
                    if eligible_ny:
                        up = (direction == "long") == (OPT["invalidation"] == "with")
                        band = (ny_mid[e] + ny_sig[e]) if up else (ny_mid[e] - ny_sig[e])
                        if l <= band <= h:
                            stats["rej_invalidation"] += 1
                            continue

                    # ---- §5.3 E1: limit at the BB MA ----
                    entry_limit = bb

                    # ---- A5: entry on the wrong side of the wick extreme is invalid ----
                    if direction == "long":
                        if not (entry_limit > l):
                            stats["rej_wrongside"] += 1
                            continue
                        struct_stop = l - STOP_BUFFER
                        R = max(entry_limit - struct_stop, STOP_MIN)
                        stop = entry_limit - R
                    else:
                        if not (entry_limit < h):
                            stats["rej_wrongside"] += 1
                            continue
                        struct_stop = h + STOP_BUFFER
                        R = max(struct_stop - entry_limit, STOP_MIN)
                        stop = entry_limit + R

                    # ---- §6 target ----
                    tgt = pick_target(e, entry_limit, R, direction)
                    if tgt is None:
                        stats["rej_no_target"] += 1
                        continue

                    stats["qualified"] += 1
                    candidates.append({
                        "sig_min": m,
                        "sig_idx": e,
                        "tf": k,
                        "direction": direction,
                        "kind": kind,
                        "limit": entry_limit,
                        "stop": stop,
                        "target": tgt,
                        "nconf": nconf,
                        "cluster_low": lmin,
                        "cluster_dist": min(abs(p - entry_limit) for p in prices),
                    })

    DEBUG["candidates"] = candidates          # diagnostics only; not used by the strategy

    # ---- §10.1(4) collapse duplicates, then tie-break, one survivor per signal minute ----
    by_min = defaultdict(list)
    for cd in candidates:
        by_min[cd["sig_idx"]].append(cd)

    selected = []
    for sig_idx in sorted(by_min):
        pool = by_min[sig_idx]
        # collapse duplicate records of the same trade (same entry, stop, target)
        seen = {}
        for cd in pool:
            key = (cd["tf"], cd["direction"],
                   round(cd["limit"], 8), round(cd["stop"], 8), round(cd["target"], 8))
            if key not in seen:
                seen[key] = cd
            else:
                # keep the larger cluster's record so tie-break levels 3-5 stay well defined
                if cd["nconf"] > seen[key]["nconf"]:
                    seen[key] = cd
        pool = list(seen.values())
        if not pool:
            continue
        stats["distinct_candidates"] += len(pool)
        if len(pool) > 1:
            stats["tied_signal_minutes"] += 1

        # level 1 — highest entry TF (§1 MTF arbitration)
        top_tf = max(c["tf"] for c in pool)
        pool1 = [c for c in pool if c["tf"] == top_tf]
        if len(pool1) == 1:
            if len(pool) > 1:
                stats["tb_level1"] += 1
            selected.append(pool1[0])
            continue
        # level 2 — long and short on the same bar => stand down, take neither
        if len(set(c["direction"] for c in pool1)) > 1:
            stats["tb_level2_standdown"] += 1
            continue
        # level 3 — larger cluster (more distinct level types)
        best = max(c["nconf"] for c in pool1)
        pool3 = [c for c in pool1 if c["nconf"] == best]
        if len(pool3) == 1:
            stats["tb_level3"] += 1
            selected.append(pool3[0])
            continue
        # level 4 — cluster nearest the entry price
        best = min(c["cluster_dist"] for c in pool3)
        pool4 = [c for c in pool3 if c["cluster_dist"] == best]
        if len(pool4) == 1:
            stats["tb_level4"] += 1
            selected.append(pool4[0])
            continue
        # level 5 — lowest cluster low (arbitrary determinism backstop)
        stats["tb_level5"] += 1
        selected.append(min(pool4, key=lambda c: c["cluster_low"]))

    # ---- §10.1 Vault admission: first-come, one position at a time, 3/session cap ----
    trades = []
    busy_until = -1
    taken = 0
    for cd in selected:
        if cd["sig_idx"] <= busy_until:
            stats["blocked_position_open"] += 1
            continue
        if taken >= SESSION_CAP:
            stats["blocked_cap"] += 1
            continue
        fill_idx, fill_px = simulate_fill(bars, cd["sig_idx"] + 1, LAST_FILL_IDX,
                                          cd["limit"], cd["direction"])
        if fill_idx is None:
            stats["no_fill"] += 1
            continue
        exit_idx = simulate_exit(bars, fill_idx, cd["stop"], cd["target"], cd["direction"])
        busy_until = exit_idx
        taken += 1
        stats["admitted"] += 1
        stats["hold_minutes"] += (exit_idx - fill_idx)
        trades.append({
            "session_date": date,
            "signal_minute": cd["sig_min"],
            "entry_tf": cd["tf"],
            "direction": cd["direction"],
            "entry": round(fill_px, 4),
            "stop": round(cd["stop"], 4),
            "target": round(cd["target"], 4),
        })
    if taken >= SESSION_CAP:
        stats["cap_bound_sessions"] += 1
    return trades, stats


def simulate_fill(bars, start_idx, end_idx, limit, direction):
    """Limit order at `limit`.  Standard limit accounting: if a bar opens through the
    limit the fill is the (better) open, otherwise the fill is the limit itself.
    §5.5's T_cancel is CALIBRATE with no start value, so no cancel rule is applied
    (A2 precedent: an under-specified rule is DISABLED, not invented)."""
    for i in range(start_idx, min(end_idx, N_SESSION_IDX - 1) + 1):
        b = bars.get(i)
        if b is None:
            continue
        o, h, l, c, _v = b
        if direction == "long":
            if o <= limit:
                return i, o
            if l <= limit:
                return i, limit
        else:
            if o >= limit:
                return i, o
            if h >= limit:
                return i, limit
    return None, None


def simulate_exit(bars, fill_idx, stop, target, direction):
    """ONLY used to decide when the one-position-at-a-time constraint releases.
    No P&L, no win/loss, no R multiple, no exit reason is recorded anywhere."""
    force = max(fill_idx, EOD_FLATTEN_IDX)
    for i in range(fill_idx, min(force, N_SESSION_IDX - 1) + 1):
        b = bars.get(i)
        if b is None:
            continue
        o, h, l, c, _v = b
        if direction == "long":
            if l <= stop:
                return i
            if h >= target:
                return i
        else:
            if h >= stop:
                return i
            if l <= target:
                return i
    return min(force, N_SESSION_IDX - 1)


# ---------------------------------------------------------------------------
# prior-day / prior-week levels for the §6 target menu
# ---------------------------------------------------------------------------

def build_prior_levels(all_sessions, dates):
    import datetime
    hi_lo = {}
    for d in dates:
        bars = all_sessions[d]
        hs = [b[1] for b in bars.values()]
        ls = [b[2] for b in bars.values()]
        hi_lo[d] = (max(hs), min(ls)) if hs else (None, None)
    week_of = {}
    for d in dates:
        y, w, _ = datetime.date.fromisoformat(d).isocalendar()
        week_of[d] = (y, w)
    weeks = {}
    for d in dates:
        weeks.setdefault(week_of[d], []).append(d)
    week_keys = sorted(weeks)
    week_hilo = {}
    for wk in week_keys:
        hs = [hi_lo[d][0] for d in weeks[wk] if hi_lo[d][0] is not None]
        ls = [hi_lo[d][1] for d in weeks[wk] if hi_lo[d][1] is not None]
        week_hilo[wk] = (max(hs), min(ls)) if hs else (None, None)

    out = {}
    for i, d in enumerate(dates):
        p = {"pdh": None, "pdl": None, "pwh": None, "pwl": None}
        if i > 0:
            p["pdh"], p["pdl"] = hi_lo[dates[i - 1]]
        wk = week_of[d]
        prev = [k for k in week_keys if k < wk]
        if prev:
            p["pwh"], p["pwl"] = week_hilo[prev[-1]]
        out[d] = p
    return out


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    all_sessions = bars_api.sessions()
    dates = sorted(d for d in all_sessions if d <= SEAL_DATE)
    for d in dates:
        assert d <= SEAL_DATE, "sealed data leak"
    print("sessions in scope (session_end_date <= %s): %d  [%s .. %s]"
          % (SEAL_DATE, len(dates), dates[0], dates[-1]))

    prior = build_prior_levels(all_sessions, dates)

    all_trades = []
    total = defaultdict(int)
    for n, d in enumerate(dates):
        trades, st = process_session(d, all_sessions[d], prior[d])
        all_trades.extend(trades)
        for k, v in st.items():
            total[k] += v
        if (n + 1) % 50 == 0:
            print("  ... %d/%d sessions, %d trades" % (n + 1, len(dates), len(all_trades)),
                  flush=True)

    all_trades.sort(key=lambda t: (t["session_date"], t["signal_minute"], t["entry_tf"]))
    with open(os.path.join(here, "blind_trades.json"), "w") as f:
        json.dump(all_trades, f, indent=1)

    print("\n=== SUMMARY ===")
    print("sessions processed : %d" % len(dates))
    print("trades             : %d  (%.4f / session)"
          % (len(all_trades), len(all_trades) / len(dates)))
    for k in sorted(total):
        print("  %-26s %d" % (k, total[k]))
    if total["admitted"]:
        print("  median-ish mean hold (min) %.2f" % (total["hold_minutes"] / total["admitted"]))
    longs = sum(1 for t in all_trades if t["direction"] == "long")
    print("  long / short               %d / %d" % (longs, len(all_trades) - longs))
    print("  cap-bound sessions         %d (%.1f%%)"
          % (total["cap_bound_sessions"], 100.0 * total["cap_bound_sessions"] / len(dates)))
    tfc = defaultdict(int)
    for t in all_trades:
        tfc[t["entry_tf"]] += 1
    print("  by entry_tf                %s" % dict(sorted(tfc.items())))
    return total, len(dates), len(all_trades)


if __name__ == "__main__":
    main()
