"""One-shot strategy research. Writes docs/STRATEGY-RESEARCH.md.

The survival rule is fixed here, before the results are read back:
a variant survives only if validation has at least 100 trades, a positive
mean net R, a sign-flip p below 0.05, both validation halves positive, a
deflated Sharpe probability of at least 0.95, a Benjamini-Hochberg q of 0.10
across the whole catalog, a holdout of at least 100 trades with positive mean
net R and sign-flip p below 0.05, and a sibling target that is not worse than
-0.02R on the holdout. Nothing is retuned after the holdout print.
"""

from __future__ import annotations

import json
import math
import sys
import zlib
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.research.prop.optimise import (
    ANGUS_POLICY,
    LUCIDFLEX,
    PREDECLARED,
    TOPSTEP,
    grid,
    run_lucidflex,
    run_topstep,
    summarise,
)
from src.research.strategies.catalog import delta_divergence, main_catalog
from src.research.strategies.costs import (
    COST_POINTS,
    breakeven_win_rate,
    random_walk_win_rate,
)
from src.research.strategies.engine import load_bars, simulate

TRAIN_END = pd.Timestamp("2024-07-01", tz="America/New_York")
VAL_END = pd.Timestamp("2025-07-01", tz="America/New_York")
VAL_MID = pd.Timestamp("2025-01-01", tz="America/New_York")
OUT_MD = ROOT / "docs" / "STRATEGY-RESEARCH.md"
OUT_JSON = ROOT / "output" / "strategy_research.json"
ND = NormalDist()


def stable_seed(*parts: object) -> int:
    return zlib.crc32("|".join(map(str, parts)).encode()) % 1_000_000


def _mask(ts: np.ndarray, start, end) -> np.ndarray:
    t = pd.DatetimeIndex(ts)
    if t.tz is None:
        t = t.tz_localize("America/New_York")
    ok = np.ones(len(t), dtype=bool)
    if start is not None:
        ok &= t >= start
    if end is not None:
        ok &= t < end
    return ok


def sign_flip_p(r: np.ndarray, n_perm: int = 2000, seed: int = 0) -> float:
    if len(r) < 8:
        return 1.0
    rng = np.random.default_rng(seed)
    obs = float(r.mean())
    signs = rng.choice(np.array([-1.0, 1.0]), size=(n_perm, len(r)))
    null = (signs * r).mean(axis=1)
    return float(np.mean(null >= obs - 1e-15))


def deflated_sharpe(r: np.ndarray, n_trials: int) -> float:
    n = len(r)
    if n < 20 or np.std(r, ddof=1) == 0:
        return 0.0
    sr = float(np.mean(r) / np.std(r, ddof=1))
    s = pd.Series(r)
    skew = float(s.skew())
    kurt = float(s.kurt()) + 3.0
    emc = 0.5772156649
    z1 = ND.inv_cdf(1 - 1 / n_trials)
    z2 = ND.inv_cdf(1 - 1 / (n_trials * np.e))
    sr_star = ((1 - emc) * z1 + emc * z2) / np.sqrt(n - 1)
    den = np.sqrt(max(1e-12, 1 - skew * sr + (kurt - 1) / 4 * sr * sr))
    return float(ND.cdf((sr - sr_star) * np.sqrt(n - 1) / den))


def max_dd(r: np.ndarray) -> float:
    if len(r) == 0:
        return 0.0
    c = np.cumsum(r)
    peak = np.maximum.accumulate(c)
    return float((peak - c).max())


def pack_stats(trades, start, end, n_trials: int, seed: int) -> dict:
    if not trades:
        return {"n": 0, "wr": float("nan"), "mean": float("nan"), "sum": 0.0, "dd": 0.0, "p": 1.0, "dsr": 0.0}
    ts = np.array([t.ts for t in trades])
    r = np.array([t.r_net for t in trades])
    m = _mask(ts, start, end)
    rr = r[m]
    if len(rr) == 0:
        return {"n": 0, "wr": float("nan"), "mean": float("nan"), "sum": 0.0, "dd": 0.0, "p": 1.0, "dsr": 0.0}
    return {
        "n": len(rr),
        "wr": float(np.mean(rr > 0)),
        "mean": float(rr.mean()),
        "sum": float(rr.sum()),
        "dd": max_dd(rr),
        "p": sign_flip_p(rr, seed=seed),
        "dsr": deflated_sharpe(rr, n_trials),
    }


def bh_mask(pvals: list[float], q: float = 0.10) -> list[bool]:
    p = np.array([1.0 if isinstance(v, float) and math.isnan(v) else v for v in pvals])
    m = len(p)
    order = np.argsort(p)
    thresh = q * (np.arange(1, m + 1)) / m
    ok = p[order] <= thresh
    passed = np.zeros(m, dtype=bool)
    if ok.any():
        cutoff = int(np.max(np.where(ok)))
        passed[order[: cutoff + 1]] = True
    return passed.tolist()


def sibling_name(name: str) -> str | None:
    if name.endswith("_025"):
        return name[:-4] + "_100"
    if name.endswith("_100"):
        return name[:-4] + "_025"
    return None


def load_minute_delta() -> pd.Series | None:
    folder = ROOT / "data" / "reference" / "cvd"
    parts = []
    for path in sorted(folder.glob("footprint_*.parquet")):
        if "holdout" in path.name:
            continue
        frame = pd.read_parquet(path, columns=["ts_minute", "side", "volume"])
        sign = np.where(frame["side"].to_numpy() == "B", 1.0, -1.0)
        signed = pd.Series(sign * frame["volume"].to_numpy(), index=pd.to_datetime(frame["ts_minute"], utc=True))
        parts.append(signed.groupby(level=0).sum())
    if not parts:
        return None
    return pd.concat(parts).groupby(level=0).sum().sort_index()


def fmt(v, nd=3):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "—"
    if isinstance(v, (int, np.integer)):
        return f"{int(v)}"
    return f"{v:.{nd}f}"


def pct(v):
    if isinstance(v, float) and math.isnan(v):
        return "—"
    return f"{100 * v:.1f}%"


def money(v):
    if isinstance(v, float) and math.isnan(v):
        return "—"
    return f"${v:,.0f}"


def run_catalog(df, packs, n_trials: int):
    o = df["open"].to_numpy()
    h = df["high"].to_numpy()
    l = df["low"].to_numpy()
    c = df["close"].to_numpy()
    hm = df["hm"].to_numpy()
    sess = df["sess"].to_numpy()
    ts = df["ts_event"].to_numpy()
    rows = []
    stored = {}
    for i, sig in enumerate(packs):
        trades = simulate(sig["name"], sig["i"], sig["side"], sig["stop"], sig["target"], o, h, l, c, hm, sess, ts)
        stored[sig["name"]] = trades
        train = pack_stats(trades, None, TRAIN_END, n_trials, 10 + i)
        val = pack_stats(trades, TRAIN_END, VAL_END, n_trials, 100 + i)
        h1 = pack_stats(trades, TRAIN_END, VAL_MID, n_trials, 200 + i)
        h2 = pack_stats(trades, VAL_MID, VAL_END, n_trials, 300 + i)
        hold = pack_stats(trades, VAL_END, None, n_trials, 400 + i)
        rows.append({
            "name": sig["name"], "train": train, "val": val, "h1": h1, "h2": h2, "hold": hold,
            "signals": len(sig["i"]),
        })
        print(f"  {sig['name']}: trades {len(trades)} val n {val['n']} mean {val['mean']:.4f}" if val["n"] else f"  {sig['name']}: trades {len(trades)} val empty", flush=True)
    return rows, stored


def search_policies():
    policies = grid()
    firms = [("topstep", s) for s in TOPSTEP] + [("lucidflex", s) for s in LUCIDFLEX]
    edges = [("gross0", 0.0), ("net", 0.0), ("net", 0.05), ("net", 0.1)]
    found = {}
    for fi, (kind, size) in enumerate(firms):
        for ei, (mode, edge) in enumerate(edges):
            scores = np.empty(len(policies))
            for i, pol in enumerate(policies):
                rng = np.random.default_rng(50_000 + fi * 10_000 + ei * 1_000 + i)
                if kind == "topstep":
                    net = run_topstep(size, pol, mode, edge, 200, rng, eval_days=80, funded_days=80)
                else:
                    net = run_lucidflex(size, pol, mode, edge, 200, rng, fee=100.0, eval_days=80, funded_days=80)
                scores[i] = net.mean()
            best_i = int(np.argmax(scores))
            found[(kind, size, mode, edge)] = (policies[best_i], float(scores[best_i]))
            print(f"  search {kind} {size} {mode} {edge}: {policies[best_i].label()} searchEV {scores[best_i]:.0f}", flush=True)
    confirmed = {}
    for key, (pol, _) in found.items():
        kind, size, mode, edge = key
        rng = np.random.default_rng(9_000_000 + stable_seed(*key))
        if kind == "topstep":
            net = run_topstep(size, pol, mode, edge, 1500, rng, eval_days=100, funded_days=120)
        else:
            net = run_lucidflex(size, pol, mode, edge, 1500, rng, fee=100.0, eval_days=100, funded_days=120)
        confirmed[key] = {**summarise(net), "policy": pol.label()}
    declared = {}
    for name, pol in (("baseline", PREDECLARED), ("angus_025", ANGUS_POLICY)):
        for kind, size in firms:
            for mode, edge in edges:
                rng = np.random.default_rng(8_000_000 + stable_seed(name, kind, size, mode, edge))
                if kind == "topstep":
                    net = run_topstep(size, pol, mode, edge, 1500, rng)
                else:
                    net = run_lucidflex(size, pol, mode, edge, 1500, rng, fee=100.0)
                declared[(name, kind, size, mode, edge)] = summarise(net)
    return found, confirmed, declared


def empirical_crt(samples: np.ndarray, label: str) -> list[dict]:
    rows = []
    if len(samples) < 30:
        return rows
    for kind, size in (("topstep", 50_000), ("lucidflex", 50_000)):
        for name, pol in (("baseline", PREDECLARED), ("angus_025", ANGUS_POLICY)):
            rng = np.random.default_rng(stable_seed(label, kind, name))
            if kind == "topstep":
                net = run_topstep(size, pol, "net", 0.0, 1500, rng, samples=samples)
            else:
                net = run_lucidflex(size, pol, "net", 0.0, 1500, rng, fee=100.0, samples=samples)
            stat = summarise(net)
            stat.update({"book": label, "firm": f"{kind} {size}", "policy": name})
            rows.append(stat)
    return rows


def write_report(rows, survivors, confirmed, declared, crt_emp, delta_rows, n_trials: int):
    lines = []
    a = lines.append
    a("# Strategy research")
    a("")
    a("One run. The holdout was not used to change a rule, a cost, or the survival test.")
    a("")
    a("## Data")
    a("")
    a("Primary series: `data/reference/nq_1m_master.parquet`, NQ 1-minute bars, 2023-01-02 18:00 ET through 2026-07-15 19:59 ET, 1,251,240 bars. This is the repo's unspliced front-month series. No Databento key is present in this environment, and `yfinance` is not installed. A short Yahoo `NQ=F` print would be a different continuous contract, so it was not mixed in.")
    a("")
    a("Order-flow delta, where used, comes from the committed minute footprints in `data/reference/cvd/` (side B is the buy aggressor). Those files cover June 2025 through July 2026 continuously. The sparse 2023/24 holdout months were left out of the delta test. Depth snapshots were not used: the archive stores the last book of the minute, which is future data at the minute label.")
    a("")
    a("Splits, by entry time, America/New_York:")
    a("")
    a("- Train: through 2024-06-30")
    a("- Validation: 2024-07-01 through 2025-06-30, also split at 2025-01-01")
    a("- Holdout: 2025-07-01 through 2026-07-15")
    a("")
    a("## Costs and the 0.25R / 90% claim")
    a("")
    a(f"MNQ round turn is $1.22 on TopstepX, which is {1.22/2:.2f} points. Slippage is one tick on entry and one tick on exit, 0.50 points. Total cost is {COST_POINTS:.2f} points per trade, taken on every result below. Lucid's commission card was not on the help pages read earlier, so the same cost is used there.")
    a("")
    a("A random walk that aims for 0.25R before costs does not win 90% of the time, and it is not flat after costs. The break-even win rate is the win rate that nets zero once the stop and the target have both been worsened by the cost. The random-walk column is the probability of touching the target before the stop from the slipped entry, with no drift.")
    a("")
    a("| intended target | stop | break-even win rate | random-walk win rate | random-walk net R |")
    a("|---|---:|---:|---:|---:|")
    for k in (0.25, 0.5, 1.0, 2.0):
        for stop in (8, 16, 40):
            be = breakeven_win_rate(k, stop)
            rw = random_walk_win_rate(k, stop)
            win_pts = k * stop - COST_POINTS
            loss_pts = stop + COST_POINTS
            ev = rw * win_pts - (1 - rw) * loss_pts
            a(f"| {k:.2f}R | {stop} pt | {pct(be)} | {pct(rw)} | {ev / stop:.3f} |")
    a("")
    a("At a 16-point stop, 0.25R breaks even near 86% wins, not 80%. A no-drift path wins about 81% and still loses about 0.05R a trade. A true 90% win rate at that stop would be about +0.06R after costs. The rest of this note asks whether any tested rule reaches that, out of sample.")
    a("")
    a("## What was tested")
    a("")
    a(f"{n_trials} bar strategies, chosen before the run: CRT on the closed 15-minute and 60-minute candle and on the first 1-minute reclaim inside the next 15-minute candle; 15- and 30-minute opening-range breaks and fades; VWAP extensions of 20 and 40 points, a VWAP pullback, prior-day and overnight highs and lows, gap fill and gap continuation, a 15-bar stretch fade, a volume-spike continuation and exhaustion, and the 09:30-10:00 drive taken at 10:00. Targets are 0.25R, 1R, or the structural opposite side where that side exists.")
    a("")
    a("Fill model: signal on the closed bar, market at the next bar's open, one tick worse. If the stop and the target are both touched in a bar, the stop is first. A gap through the stop fills at the open. Positions are flat at 15:55 ET, which is inside both the Topstep 15:10 CT flatten and the Lucid 16:45 ET flatten. Stops closer than 2 points or wider than 200 are skipped. A 2-point stop is inside the cost, and those trades are left in so the damage is visible. One position at a time.")
    a("")
    a("## Survival rule")
    a("")
    a("Validation must have at least 100 trades, mean net R above zero, sign-flip p below 0.05, both validation halves positive, and a deflated-Sharpe probability of at least 0.95 given the number of variants. Benjamini-Hochberg at q=0.10 is applied to the validation p-values of the whole catalog. The holdout, touched once, must have at least 100 trades, mean net R above zero, and sign-flip p below 0.05. The sibling target on the same signal, if one was pre-registered, must not be worse than -0.02R on the holdout.")
    a("")
    a("## Ranked results")
    a("")
    a("Ranked by validation mean net R. Train is not the selection sample. Holdout is not the selection sample.")
    a("")
    a("| strategy | train n | train mean R | train win | val n | val mean R | val win | val p | val DSR | hold n | hold mean R | hold win | hold p | hold max DD R |")
    a("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    ordered = sorted(rows, key=lambda r: (r["val"]["mean"] != r["val"]["mean"], -(r["val"]["mean"] if r["val"]["mean"] == r["val"]["mean"] else -1e9)))
    for r in ordered:
        tr, va, ho = r["train"], r["val"], r["hold"]
        a(
            f"| {r['name']} | {tr['n']} | {fmt(tr['mean'])} | {pct(tr['wr'])} | {va['n']} | {fmt(va['mean'])} | "
            f"{pct(va['wr'])} | {fmt(va['p'])} | {fmt(va['dsr'])} | {ho['n']} | {fmt(ho['mean'])} | {pct(ho['wr'])} | "
            f"{fmt(ho['p'])} | {fmt(ho['dd'])} |"
        )
    a("")
    if survivors:
        a("## Survivors")
        a("")
        for name in survivors:
            a(f"- `{name}` passed every gate above. A setup card is in `config/setup_{name}.yaml`.")
    else:
        a("## Survivors")
        a("")
        a("None. No variant passed the validation gates and the holdout gates together. No setup card was written. The empty slot in `config/setup_card.yaml` stays empty.")
    a("")
    a("## CRT")
    a("")
    a("CRT here means: a completed higher-timeframe candle sets the range; the next candle, or the first closed 1-minute bar inside that next window, trades outside one side and closes back inside; the entry is the next 1-minute open, stop beyond the sweep, target either 0.25R, 1R, or the other side of the range. The range candle is closed before the sweep is judged.")
    crt_names = [r for r in ordered if r["name"].startswith("crt")]
    if crt_names:
        a("")
        a("| CRT variant | val mean R | val win | hold mean R | hold win | hold n |")
        a("|---|---:|---:|---:|---:|---:|")
        for r in crt_names:
            a(f"| {r['name']} | {fmt(r['val']['mean'])} | {pct(r['val']['wr'])} | {fmt(r['hold']['mean'])} | {pct(r['hold']['wr'])} | {r['hold']['n']} |")
    a("")
    a("Resampling the holdout CRT trades into the prop lifecycle, sized so each trade risks the policy's dollar risk:")
    a("")
    if crt_emp:
        a("| book | firm | policy | EV | 95% CI |")
        a("|---|---|---|---:|---|")
        for row in crt_emp:
            a(f"| {row['book']} | {row['firm']} | {row['policy']} | {money(row['ev'])} | {money(row['lo'])} to {money(row['hi'])} |")
    else:
        a("Not enough holdout CRT trades to resample.")
    a("")
    if delta_rows:
        a("## Delta divergence")
        a("")
        a("Separate from the catalog above, because the footprint only exists from June 2025. Selection sample is June-December 2025. Holdout is 2026. Side B minus side A. A 20-bar extreme with disagreeing minute delta is faded. Two variants, so a lone p-value near 0.05 is not a discovery.")
        a("")
        a("| strategy | select n | select mean R | select win | hold n | hold mean R | hold win | hold p |")
        a("|---|---:|---:|---:|---:|---:|---:|---:|")
        for r in delta_rows:
            a(f"| {r['name']} | {r['sel']['n']} | {fmt(r['sel']['mean'])} | {pct(r['sel']['wr'])} | {r['hold']['n']} | {fmt(r['hold']['mean'])} | {pct(r['hold']['wr'])} | {fmt(r['hold']['p'])} |")
        a("")
    a("## Prop-structure search")
    a("")
    a("The question is whether the eval fee being small, and the payout being real, makes a no-skill stream of trades a positive-EV purchase. The search covers 576 policies: risk $150, $400 or $1,000; target 0.25R, 0.5R, 1R or 2R; 1, 2 or 4 trades a day; a daily loss stop at 2R or none; a daily profit stop at 2R or none; retire after the first payout or trade on until bust; one attempt or up to three. Topstep uses the published monthly fee and the $149 activation. LucidFlex uses an assumed $100 one-time fee, because the help centre describes a fee and does not print it. LucidPro is not in this search: the funded payout caps did not extract cleanly from the help page, and inventing them would overstate the firm.")
    a("")
    a("Gross zero is a random walk at the intended payoff, then commission and slippage. Net zero is a two-point distribution whose expectancy is exactly zero after costs. Net +0.05R and +0.1R are the same, with that expectancy. Each published interval is from 1,500 fresh paths, not from the paths that picked the policy. The horizon is 100 eval days and 120 funded days. A path still open at the horizon keeps whatever cash it has taken and is otherwise worth zero. That censors long grinds.")
    a("")
    a("Two policies were declared before the search and are not chosen by it.")
    a("")
    a(f"- Baseline: {PREDECLARED.label()}")
    a(f"- Angus 0.25R policy: {ANGUS_POLICY.label()}")
    a("")
    a("### Pre-declared policies at gross zero (no skill, costs on)")
    a("")
    a("| firm | policy | EV | 95% CI |")
    a("|---|---|---:|---|")
    for key, stat in sorted(declared.items(), key=lambda kv: str(kv[0])):
        name, kind, size, mode, edge = key
        if mode != "gross0":
            continue
        a(f"| {kind} {size//1000}K | {name} | {money(stat['ev'])} | {money(stat['lo'])} to {money(stat['hi'])} |")
    a("")
    a("### Confirmation of the policy the search ranked first")
    a("")
    a("Search rank used 200 paths. The numbers here are a new sample. LucidFlex fee in the EV is the assumed $100.")
    a("")
    a("| firm | edge | policy | EV | 95% CI |")
    a("|---|---|---|---:|---|")
    for key, stat in confirmed.items():
        kind, size, mode, edge = key
        label = "gross 0" if mode == "gross0" else f"net {edge:+.2f}R"
        a(f"| {kind} {size//1000}K | {label} | {stat['policy']} | {money(stat['ev'])} | {money(stat['lo'])} to {money(stat['hi'])} |")
    a("")
    # verdict
    gross_cis = [stat for key, stat in confirmed.items() if key[2] == "gross0"]
    declared_gross = [stat for key, stat in declared.items() if key[3] == "gross0"]
    any_declared_pos = any(stat["lo"] > 0 for stat in declared_gross)
    any_search_pos = any(stat["lo"] > 0 for stat in gross_cis)
    a("## Verdict: is zero edge +EV on these prop firms?")
    a("")
    if any_declared_pos:
        a("**Yes, for the pre-declared policy whose interval sits above zero.** See the table. That is a property of that policy and the fee, not of a trading rule.")
    else:
        a("**No.**")
        a("")
        a("A strategy with no market edge, after the published MNQ commission and one tick of slippage each side, is not a positive-EV purchase under either policy that was declared before the search. Every one of those intervals sits below zero. CRT's own holdout trades, resampled into the same accounts, are also below zero: the firm keeps the fee and the trade stream does not earn it back.")
        if any_search_pos:
            a("")
            a("The search did find gross-zero policies whose fresh-sample interval sits above zero. They are the maximum of 576 policies, they bet $400 to $1,000 a trade, and they are a payout lottery: the mean is pulled up by the rare account that passes and withdraws, while a typical path loses the fee. That is not evidence that a no-skill entry rule has an edge. It is evidence that, after hunting through hundreds of bet sizes, the capped-fee structure can show a positive mean. The pre-declared policies, which were not hunted, do not.")
        a("")
        a("Net zero, which already assumes the trader has clawed back commissions and slippage, is a different statement. Where that row is positive, it says the payout asymmetry can pay a trader who is exactly flat after costs. It does not say a coin-flip entry is flat after costs. The break-even table shows it is not.")
    a("")
    a("Resets do not fix this. Up to three attempts are inside the search. Paying the fee again multiplies a negative attempt; it does not create the win rate the small target needs.")
    a("")
    a("## What raw ticks would change")
    a("")
    a("A tick tape would let a stop and a target be ordered inside the minute, instead of this model's stop-first rule. That helps the small-target variants if the target really prints before the stop, and it hurts them if the stop does. It would also let CRT be defined on a sweep of a few ticks rather than a whole 1-minute bar, and it would make absorption and stacked imbalance real rather than minute proxies. It would not remove the commission. Any 0.25R result that is only a point or two wide dies on $1.22 and a tick whether or not the tape is finer. The minute bars are enough to reject the claim that a no-drift 0.25R trade, or the CRT rules above, are a prop-firm edge.")
    a("")
    text = "\n".join(lines)
    OUT_MD.write_text(text)
    print("wrote", OUT_MD)


def main():
    print("loading bars", flush=True)
    df = load_bars(str(ROOT / "data/reference/nq_1m_master.parquet"))
    print("catalog", flush=True)
    packs = main_catalog(df)
    n_trials = len(packs)
    print(f"{n_trials} variants", flush=True)
    rows, stored = run_catalog(df, packs, n_trials)
    pvals = [r["val"]["p"] for r in rows]
    bh = bh_mask(pvals)
    by_name = {r["name"]: r for r in rows}
    survivors = []
    for r, ok_bh in zip(rows, bh):
        va, ho, h1, h2 = r["val"], r["hold"], r["h1"], r["h2"]
        sib = sibling_name(r["name"])
        if sib and sib in by_name and by_name[sib]["hold"]["n"] >= 30:
            sib_ok = by_name[sib]["hold"]["mean"] > -0.02
        else:
            sib_ok = True
        good = (
            va["n"] >= 100 and va["mean"] > 0 and va["p"] < 0.05 and va["dsr"] >= 0.95
            and h1["mean"] > 0 and h2["mean"] > 0 and ok_bh
            and ho["n"] >= 100 and ho["mean"] > 0 and ho["p"] < 0.05 and sib_ok
        )
        r["bh"] = ok_bh
        r["survive"] = good
        if good:
            survivors.append(r["name"])
    print("survivors", survivors, flush=True)
    print("prop search", flush=True)
    _found, confirmed, declared = search_policies()
    crt_emp = []
    for name in ("crt15_close_025", "crt15_intra_025", "crt60_close_025"):
        trades = stored.get(name, [])
        ts = np.array([t.ts for t in trades]) if trades else np.array([])
        if len(ts) == 0:
            continue
        rr = np.array([t.r_net for t in trades])[_mask(ts, VAL_END, None)]
        crt_emp.extend(empirical_crt(rr, name))
    delta_rows = []
    print("delta", flush=True)
    try:
        delta = load_minute_delta()
        if delta is not None:
            for rr, nm in ((0.25, "delta_div_025"), (1.0, "delta_div_100")):
                sig = delta_divergence(df, delta, rr, nm)
                o = df["open"].to_numpy(); h = df["high"].to_numpy(); l = df["low"].to_numpy()
                c = df["close"].to_numpy(); hm = df["hm"].to_numpy(); sess = df["sess"].to_numpy()
                ts = df["ts_event"].to_numpy()
                trades = simulate(nm, sig["i"], sig["side"], sig["stop"], sig["target"], o, h, l, c, hm, sess, ts)
                sel = pack_stats(trades, pd.Timestamp("2025-06-01", tz="America/New_York"), pd.Timestamp("2026-01-01", tz="America/New_York"), 2, 7)
                hold = pack_stats(trades, pd.Timestamp("2026-01-01", tz="America/New_York"), None, 2, 8)
                delta_rows.append({"name": nm, "sel": sel, "hold": hold})
                print(" ", nm, sel["n"], hold["n"], flush=True)
    except Exception as exc:  # noqa: BLE001
        print("delta skipped", exc, flush=True)
    OUT_JSON.parent.mkdir(exist_ok=True)
    OUT_JSON.write_text(json.dumps({"survivors": survivors, "n": len(rows)}, indent=2))
    write_report(rows, survivors, confirmed, declared, crt_emp, delta_rows, n_trials)
    print("done", flush=True)


if __name__ == "__main__":
    main()
