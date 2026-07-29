#!/usr/bin/env python3
"""CONFLUENCE STUDY — shard worker. ONE WRITER PER FILE, append-only, into raw/.

    python3 run_shard.py --mode perm   --shard K --nshards N     -> raw/perm_K.jsonl
    python3 run_shard.py --mode random --shard K --nshards N     -> raw/random_K.jsonl

Deterministic: the seed is a pure function of (mode, permutation index), so a shard's output is
identical no matter which worker runs it or in what order. No shard reads another shard's file.
The aggregator is a separate non-agent process.
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pipeline import (BLIND, POOL, block_shuffle, headline, load,  # noqa: E402
                      spearman, walk_forward)

RAW = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw")
N_PERM, N_RANDOM = 2000, 500

ap = argparse.ArgumentParser()
ap.add_argument("--mode", required=True, choices=["perm", "random"])
ap.add_argument("--shard", type=int, required=True)
ap.add_argument("--nshards", type=int, required=True)
a = ap.parse_args()

J = load()
os.makedirs(RAW, exist_ok=True)
path = os.path.join(RAW, f"{a.mode}_{a.shard:02d}.jsonl")
total = N_PERM if a.mode == "perm" else N_RANDOM
mine = [k for k in range(total) if k % a.nshards == a.shard]

done = set()
if os.path.exists(path):
    with open(path) as fh:
        for line in fh:
            try:
                done.add(json.loads(line)["k"])
            except Exception:
                pass

with open(path, "a", buffering=1) as fh:          # append-only, single writer
    for k in mine:
        if k in done:
            continue
        rs = np.random.default_rng(900_000 + k if a.mode == "perm" else 500_000 + k)
        if a.mode == "perm":
            y = block_shuffle(J, rs)
            W = walk_forward(J, POOL, y_override=y, seed=k)
            rec = dict(k=k, mode="perm", metric=headline(J, W, y_override=y), n=int(len(W)))
        else:
            W = walk_forward(J, POOL, weights="random", seed=500_000 + k)
            rec = dict(k=k, mode="random", metric=headline(J, W), n=int(len(W)))
        fh.write(json.dumps(rec, default=float) + "\n")
print(f"shard {a.shard}/{a.nshards} mode={a.mode}: wrote {len(mine)} records -> {path}")
