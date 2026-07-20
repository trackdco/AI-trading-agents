#!/usr/bin/env python3
"""Cheap 'chained + new stuff' approximation: overlay the strict post-open confluence trades
(cdr_v2_trades.csv) onto the agent stack's per-day P&L (v0.7 chained ledger) — NO agents re-run.
Shows combined month-consistency (the scorecard) vs agent-alone.

    python -m scripts.agent_plus_postopen
"""
import pandas as pd

MONTHS = ["2026-02", "2026-03", "2026-04", "2026-05", "2026-06", "2026-07"]
SP = "/tmp/claude-0/-home-user-AI-trading-agents/8f4cdd65-f942-532a-87f2-c9c07c27272a/scratchpad"


def main():
    led = pd.read_csv("output/v07/chained2026/ledger.csv")
    led["month"] = led.day.str[:7]
    agent_day = led.groupby("day").pl.sum()

    po = pd.read_csv(f"{SP}/cdr_v2_trades.csv")
    po_day = po.groupby("day").dollars.sum()

    days = sorted(set(agent_day.index) | set(po_day.index))
    rows = []
    for d in days:
        a, p = agent_day.get(d, 0.0), po_day.get(d, 0.0)
        rows.append(dict(day=d, month=d[:7], agent=a, postopen=p, combined=a + p))
    D = pd.DataFrame(rows)

    print("MONTH CONSISTENCY — agent alone vs agent + post-open confluence\n")
    print(f"  {'month':8s} {'agent$':>9s} {'postopen$':>10s} {'combined$':>10s}  green?")
    ga = gc = 0
    for m in MONTHS:
        g = D[D.month == m]
        if not len(g):
            continue
        a, p, c = g.agent.sum(), g.postopen.sum(), g.combined.sum()
        ga += a > 0; gc += c > 0
        print(f"  {m:8s} {a:>+9,.0f} {p:>+10,.0f} {c:>+10,.0f}  {'GREEN' if c>0 else 'red'}"
              f"{'  (broke!)' if a>0 and c<=0 else ''}")
    tot = D
    print(f"\n  agent alone:    ${tot.agent.sum():+,.0f}   {ga}/6 months green")
    print(f"  agent+postopen: ${tot.combined.sum():+,.0f}   {gc}/6 months green")


if __name__ == "__main__":
    main()
