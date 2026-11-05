"""No-edge pass rates under the rules in config/prop_rules.yaml.

Does not place orders. Prints a markdown table. Seed and sim count are fixed
so a re-run matches docs/PROP-BASELINE.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.research.prop.montecarlo import (
    TradeDistribution,
    run_paths,
    static_floor_pass_rate,
)
from src.research.prop.rules import load_accounts

SEED = 20261103
N = 1500
DAYS = 60


def _line(result, risk: float, note: str) -> str:
    cost = "inf" if result.expected_cost_per_payout == float("inf") else f"{result.expected_cost_per_payout:,.0f}"
    fee = "unconfirmed" if result.fee_unconfirmed else f"{result.expected_fees:,.0f}"
    return (
        f"| {result.key} | {risk:,.0f} | {result.pass_rate:.1%} | {result.bust_rate:.1%} | "
        f"{fee} | {result.expected_payout_count:.2f} | {result.expected_trader_cash:,.0f} | "
        f"{cost} | {result.ev_per_eval:,.0f} | {note} |"
    )


def main() -> None:
    accounts = load_accounts()
    header = (
        "| account | risk $ | pass | bust | E[fees] | E[payouts] | E[trader $] | "
        "cost per payout | EV / eval | note |"
    )
    rule = "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|"
    rows = [
        "# No-edge baseline",
        "",
        (
            f"Seed {SEED}, {N} paths, {DAYS} trading days, 2 trades a day, win rate 50%, "
            "average win equal to average loss. No slippage and no commission. "
            "A pass is the eval target under that firm's consistency rule. "
            "Where a funded account is chained, it is a fresh account and the "
            "payout columns include it. Lucid fees are 0 because the help centre "
            "did not print a price."
        ),
        "",
        header,
        rule,
    ]
    jobs = [
        ("topstep_combine_50k", "topstep_xfa_50k_standard", 200, "standard path, $49/mo + $149"),
        ("topstep_combine_50k", "topstep_xfa_50k_standard", 400, "standard path, $49/mo + $149"),
        ("topstep_combine_50k", "topstep_xfa_50k_standard", 1000, "standard path, $49/mo + $149"),
        ("topstep_combine_100k", "topstep_xfa_100k_standard", 400, "standard path, $99/mo + $149"),
        ("topstep_combine_150k", "topstep_xfa_150k_standard", 400, "standard path, $199/mo + $149"),
        ("lucidflex_eval_50k", "lucidflex_funded_50k", 400, "40% consistency, fee not published"),
        ("lucidflex_eval_100k", None, 400, "eval only, fee not published"),
        ("lucidflex_eval_150k", None, 400, "eval only, fee not published"),
        ("lucidpro_eval_25k", None, 400, "no eval consistency, DLL none"),
        ("lucidpro_eval_50k", None, 400, "no eval consistency, DLL $1,200"),
        ("lucidpro_eval_100k", None, 400, "no eval consistency, DLL $1,800"),
        ("lucidpro_eval_150k", None, 400, "no eval consistency, DLL $2,700"),
    ]
    for i, (eval_key, funded_key, risk, note) in enumerate(jobs):
        result = run_paths(
            accounts[eval_key],
            TradeDistribution.no_edge(risk),
            n_sims=N,
            max_days=DAYS,
            seed=SEED + i,
            funded=None if funded_key is None else accounts[funded_key],
            funded_days=DAYS,
        )
        rows.append(_line(result, risk, note))

    rows += [
        "",
        "## Same firm, with an edge",
        "",
        (
            "Win rate 50%, average win 1.5× the loss. Expectancy is +0.25R per trade. "
            "This is a hypothetical distribution, not a measured setup."
        ),
        "",
        header,
        rule,
    ]
    for i, risk in enumerate((200, 1000)):
        dist = TradeDistribution(win_rate=0.5, avg_win=1.5 * risk, avg_loss=risk, trades_per_day=2)
        result = run_paths(
            accounts["topstep_combine_50k"],
            dist,
            n_sims=N,
            max_days=DAYS,
            seed=SEED + 100 + i,
            funded=accounts["topstep_xfa_50k_standard"],
            funded_days=DAYS,
        )
        rows.append(_line(result, risk, "+0.25R, Topstep 50K standard"))

    static = static_floor_pass_rate(
        2000, 3000, TradeDistribution.no_edge(250), n_sims=N, max_days=400, seed=SEED
    )
    rows += [
        "",
        (
            f"Static floor, no consistency, no trail, risk $250, up to 400 days: "
            f"pass rate {static:.1%}. The closed form is 2,000 / 5,000 = 40%."
        ),
        "",
    ]
    text = "\n".join(rows) + "\n"
    out = ROOT / "docs" / "PROP-BASELINE.md"
    out.write_text(text)
    print(text)


if __name__ == "__main__":
    main()
