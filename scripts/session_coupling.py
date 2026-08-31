#!/usr/bin/env python3
"""Does Asia/London character predict New York? (his question 2026-08-31)

    python -m scripts.session_coupling

Answer measured on 874 days: volatility CLUSTERS across sessions (quiet
overnight -> quiet NY, loud -> loud; NY median range pct 0.28 vs 0.74 across
overnight quartiles), direction does NOT carry (51% continuation), and NY
candidate quality in R is FLAT across regimes (the stop scales with vol).
Full reading: docs/FINDING-session-vol-coupling.md. Ranges are normalized
as trailing-120-day same-session percentiles so the 2023->2026 price
doubling cannot fake the result. Everything as-of and causal.
"""
import sys, gzip, json
sys.path.insert(0, '.')
import scripts.offline_briefings as OB
import pandas as pd, numpy as np
from collections import defaultdict


def main():
    bars = OB.get_bars()
    days = OB.all_session_days(bars)

    def sess(day, h1, m1, h2, m2):
        t0 = pd.Timestamp(f"{day} 18:00", tz=OB.NY)
        a = t0.normalize() + pd.Timedelta(hours=h1, minutes=m1)
        if a < t0: a += pd.Timedelta(days=1)
        b = t0.normalize() + pd.Timedelta(hours=h2, minutes=m2)
        if b <= t0: b += pd.Timedelta(days=1)
        return bars[(bars.index >= a) & (bars.index < b)]

    recs = []
    for d in days:
        A, L, N = sess(d, 18, 0, 3, 0), sess(d, 3, 0, 9, 30), sess(d, 9, 30, 16, 0)
        if len(A) < 300 or len(L) < 250 or len(N) < 250: continue
        rng = lambda s: float(s.high.max() - s.low.min())
        net = lambda s: float(s.close.iloc[-1] - s.open.iloc[0])
        recs.append(dict(day=d, ar=rng(A), lr=rng(L), nr=rng(N),
                         onr=rng(pd.concat([A, L])), ln=net(L), nn=net(N),
                         neff=abs(net(N)) / rng(N) if rng(N) else 0))
    df = pd.DataFrame(recs)

    def trailing_pct(col):
        v = df[col].values
        out = [np.nan] * len(v)
        for i in range(len(v)):
            w = v[max(0, i - 120):i]
            if len(w) >= 40: out[i] = (w < v[i]).mean()
        return pd.Series(out)

    for c in ('ar', 'lr', 'nr', 'onr'):
        df[c + '_p'] = trailing_pct(c)
    df = df.dropna(subset=['ar_p', 'lr_p', 'nr_p', 'onr_p']).reset_index(drop=True)
    for c in ('ar', 'lr', 'onr'):
        df[c + '_q'] = df[c + '_p'].map(lambda p: min(3, int(p * 4)))

    print(f"days usable: {len(df)}")
    print("\nNY range pct (median) by Asia q x London q:")
    print(df.pivot_table(index='ar_q', columns='lr_q', values='nr_p',
                         aggfunc='median').round(2).to_string())
    print("\novernight quartile -> NY:")
    for q in range(4):
        s = df[df.onr_q == q]
        print(f"  Q{q+1}: n={len(s):>3} NY median pct={s.nr_p.median():.2f} "
              f"P(top quartile)={(s.nr_p >= .75).mean():.0%} "
              f"efficiency={s.neff.median():.2f}")
    d2 = df[(df.ln.abs() > 0) & (df.nn.abs() > 0)]
    print(f"\nLondon->NY continuation: {(np.sign(d2.ln) == np.sign(d2.nn)).mean():.0%}")
    try:
        rows = [json.loads(l) for l in gzip.open(
            'output/analysis/candidate_corpus_fullday_v2.jsonl.gz', 'rt')]
        ny = defaultdict(list)
        for r in rows:
            if r['window'] == 'NY' and r.get('mech_outcome'):
                ny[r['sess_day']].append(r['mech_outcome'] == '2R')
        oq = dict(zip(df.day, df.onr_q))
        agg = defaultdict(lambda: [0, 0])
        for d, lst in ny.items():
            if d in oq:
                agg[oq[d]][0] += sum(lst); agg[oq[d]][1] += len(lst)
        print("NY candidate 2R-rate by overnight quartile:",
              {f"Q{q+1}": f"{agg[q][0]/agg[q][1]:.1%}" for q in range(4) if agg[q][1]})
    except FileNotFoundError:
        print("(corpus not present - candidate cut skipped)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
