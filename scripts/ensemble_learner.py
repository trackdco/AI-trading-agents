#!/usr/bin/env python3
"""Walk-forward LEARNING ensemble over the bias concepts (the journaling agent).

Reads the concept signals from bias_lab. Walks day by day; each concept keeps a trailing-60
record of whether it was CORRECT on days it fired. Each day, a concept that has fired >= MIN_N
times votes with a SIGNED weight = signal * (trailing_acc - 0.5): concepts beating a coin flip
push their own direction; concepts reliably WRONG get FADED (voted opposite). The ensemble bias
is the sign of the weighted sum (NEUTRAL if the net conviction is weak). Only PRIOR days feed the
weights -> no lookahead. Journals which concepts are trusted vs faded over time, and compares the
learned bias to the best single concept and the base rate, in-sample vs out-of-sample.
"""
import json
from collections import deque

import numpy as np
import pandas as pd

S = "/tmp/claude-0/-home-user-AI-trading-agents/69c9097f-44f3-585b-817f-a315126d0dbb/scratchpad"
lab = json.load(open(f"{S}/_lab.json"))
names = lab["names"]; order = lab["order"]; OUT = np.array(lab["out"]); is_train = np.array(lab["is_train"])
SIG = np.load(f"{S}/_sig.npy")     # shape (n_concepts, n_days)
nD = len(order)
TRAIL, MIN_N, CONV = 60, 15, 0.6   # min |weighted vote| (in units of votes) to call a direction

hist = {n: deque(maxlen=TRAIL) for n in names}     # correctness record per concept
ens = np.zeros(nD, int)
trusted_journal = []                                # monthly snapshot of trusted/faded concepts

for i in range(nD):
    vote = 0.0; active = 0
    for k, n in enumerate(names):
        s = int(SIG[k, i])
        if s == 0:
            continue
        h = hist[n]
        if len(h) >= MIN_N:
            acc = sum(h) / len(h)
            vote += s * (acc - 0.5)          # >0.5 push direction; <0.5 fade (push opposite)
            active += 1
    ens[i] = int(np.sign(vote)) if abs(vote) >= 0.5 else 0
    # update AFTER deciding (day i's outcome feeds i+1 onward)
    for k, n in enumerate(names):
        s = int(SIG[k, i])
        if s != 0:
            hist[n].append(1 if s == OUT[i] else 0)
    # monthly journal of the current policy
    mo = order[i][:7]
    if i == nD - 1 or order[i + 1][:7] != mo:
        snap = {}
        for n in names:
            h = hist[n]
            if len(h) >= MIN_N:
                a = round(100 * sum(h) / len(h))
                snap[n] = a
        trusted = sorted([(a, n) for n, a in snap.items() if a >= 55], reverse=True)[:5]
        faded = sorted([(a, n) for n, a in snap.items() if a <= 45])[:5]
        trusted_journal.append(dict(mo=mo, trusted=[f"{n}({a}%)" for a, n in trusted],
                                    faded=[f"{n}({a}%)" for a, n in faded]))

def acc(mask, pred):
    fire = (pred != 0) & mask
    if fire.sum() == 0:
        return 0, 0.0
    return int(fire.sum()), round(100 * ((pred == OUT) & fire).sum() / fire.sum(), 1)

def dir_acc(mask, pred):
    """Accuracy among NON-FLAT outcome days only (did we get the side right when it moved)."""
    fire = (pred != 0) & mask & (OUT != 0)
    if fire.sum() == 0:
        return 0, 0.0
    return int(fire.sum()), round(100 * ((pred == OUT) & fire).sum() / fire.sum(), 1)

def base(mask):
    return round(100 * (OUT[mask] == 1).mean(), 1)

te = ~is_train
print("=== WALK-FORWARD LEARNING ENSEMBLE ===")
print(f"base rate (predict up): train {base(is_train)}%  test {base(te)}%")
for lab_, m in [("ALL", np.ones(nD, bool)), ("TRAIN 23-24", is_train), ("TEST 25-26", te)]:
    n, a = acc(m, ens); nd, ad = dir_acc(m, ens)
    print(f"  {lab_:12s} ensemble fired {n:3d}d strict {a}%  |  side-accuracy (non-flat) {nd}d {ad}%")
# best single concept OOS strict
best = None
for k, n in enumerate(names):
    fire = (SIG[k] != 0) & te
    if fire.sum() >= 40:
        a = 100 * ((SIG[k] == OUT) & fire).sum() / fire.sum()
        if best is None or a > best[1]:
            best = (n, round(a, 1), int(fire.sum()))
print(f"\nbest single concept OOS: {best[0]} {best[1]}% (n={best[2]})")
n, ao = dir_acc(te, ens)
print(f"ensemble OOS side-accuracy: {ao}%  vs coin-flip 50%  ({n} non-flat test days)")

# save + journal tail
pd.DataFrame([dict(day=order[i], out=int(OUT[i]), ens=int(ens[i]), train=bool(is_train[i])) for i in range(nD)]
             ).to_csv(f"{S}/ensemble_days.csv", index=False)
print("\n--- LEARNER JOURNAL (end-of-month trusted / faded concepts) ---")
for j in trusted_journal[-8:]:
    print(f"  {j['mo']}  trust: {', '.join(j['trusted']) or '-'}   |   fade: {', '.join(j['faded']) or '-'}")
json.dump(trusted_journal, open(f"{S}/ensemble_journal.json", "w"))
print("\nsaved ensemble_days.csv, ensemble_journal.json")
