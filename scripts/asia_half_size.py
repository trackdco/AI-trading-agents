"""ASIA AT HALF SIZE — a pure multiplier, priced on the railed dumps.

Preregistered rule (same as conviction sizing): ADOPT if, after scaling the
sized book so its max drawdown equals the flat book's, R/day improves by
>= 5% in BOTH halves. Applied to flat AND armed (the adopted layer), all
three eras. Asia = fills before 03:00 ET (fill_hrs < 9 from the 18:00 anchor).
0.5 is a size, not a skip, so occupancy is untouched and the dump is the truth.
"""
import sys, gzip, json
import numpy as np
sys.path.insert(0, "."); import scripts.conviction_sizing as CS
COST = 0.5
ERAS = {
 "2017-19": ("pd_va_trades_nq17a_lvall_xr30_sar_through_tf1{a}.jsonl.gz","vwap_rev_tf1_retest_nq17a_ng0_xr30_dd{a}.jsonl.gz","vwap_rev_tf1_retest_nq17a_ng0_xr30_nyanc_dd{a}.jsonl.gz", "2017-01-01"),
 "2020-22": ("pd_va_trades_nq20a_lvall_xr30_sar_through_tf1{a}.jsonl.gz","vwap_rev_tf1_retest_nq20a_ng0_xr30_dd{a}.jsonl.gz","vwap_rev_tf1_retest_nq20a_ng0_xr30_nyanc_dd{a}.jsonl.gz", "2020-01-01"),
 "2023-26": ("pd_va_trades_lvall_xr30_sar_through_tf1_ng{a}.jsonl.gz","vwap_rev_tf1_retest_xr30_dd{a}.jsonl.gz","vwap_rev_tf1_retest_xr30_nyanc_dd{a}.jsonl.gz", "2023-01-01"),
}
def L(n, c, frm):
    ts=[json.loads(l) for l in gzip.open("output/analysis/"+n,"rt")]
    return [t for t in ts if t["day"]>=frm and ((not c) or (t["depth"]==3.0 and t["target_r"]==1.0))]
def net(t): return t["r"]-COST/t["risk"]
def dd(v): e=np.cumsum(v); return float((e-np.maximum.accumulate(e)).min())
print(f"{'era':<9}{'book':<7}{'half':<5}{'flat R/d':>9}{'asia½ R/d':>10}{'dd-matched':>11}{'lift':>8}   {'maxDD flat→½':>16}")
print("-"*80)
verd = {}
for era,(lv,sv,nv,frm) in ERAS.items():
    for arm in (False, True):
        a = "_arm1" if arm else ""
        kept = CS.rail_pass([L(lv.format(a=a),False,frm), L(sv.format(a=a),True,frm), L(nv.format(a=a),True,frm)])
        days = sorted(kept)
        vF = np.array([sum(net(t) for t in kept[d]) for d in days])
        vH = np.array([sum((0.5 if t["fill_hrs"]<9 else 1.0)*net(t) for t in kept[d]) for d in days])
        sc = abs(dd(vF))/abs(dd(vH)); vHs = vH*sc
        MID = days[len(days)//2]; m = np.array([d<MID for d in days])
        lifts=[]
        for h,msk in (("IS",m),("OOS",~m)):
            lift = vHs[msk].mean()/vF[msk].mean()-1; lifts.append(lift)
            print(f"{era:<9}{'armed' if arm else 'flat':<7}{h:<5}{vF[msk].mean():>+9.3f}{vH[msk].mean():>+10.3f}{vHs[msk].mean():>+11.3f}{lift:>+8.1%}   {dd(vF):>+7.1f} → {dd(vH):>+6.1f}")
        ok = all(l>=0.05 for l in lifts); verd[(era,arm)] = (ok, lifts)
        print(f"{'':<9}{'':<7}{'ALL':<5}{vF.mean():>+9.3f}{vH.mean():>+10.3f}{vHs.mean():>+11.3f}{vHs.mean()/vF.mean()-1:>+8.1%}   -> {'PASS' if ok else 'FAIL'}  (raw R {vF.sum():+.0f} → {vH.sum():+.0f}, scale x{sc:.3f})")
        print()
print("VERDICT (>= +5% dd-matched in BOTH halves):")
for (era,arm),(ok,l) in verd.items(): print(f"  {era} {'armed' if arm else 'flat ':<5}  {'PASS' if ok else 'FAIL'}  IS {l[0]:+.1%}  OOS {l[1]:+.1%}")
