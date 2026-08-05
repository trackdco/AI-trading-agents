# The Strategy Book

Strategies that have passed `context/validation-gate-v1.md`. **This is the only
list the agents may trade from.** Anything not here does not exist as far as the
Desk is concerned.

Adding an entry requires an ADOPT verdict in `strategies/<slug>/05-verdict.md`
and Angus's signature on it.

---

## Current book

_Empty. First entries pending the validation pipeline._

<!--
### <Name>
- **Mechanism:** one line — who is losing money to us and why
- **Session / instrument:**
- **Trigger (plain English):**
- **Prefer it when:**
- **Stand down when:**
- **Mechanical baseline:** expectancy __R · PF __ · max DD __R · __ trades/month
- **Correlation to rest of book:** max |ρ| = __
- **Verdict:** `strategies/<slug>/05-verdict.md` · adopted YYYY-MM-DD
-->

---

## Book-level statistics

Recomputed whenever an entry is added or removed.

| Metric | Value |
|---|---|
| Strategies in book | 0 |
| Combined expectancy (R/day) | — |
| Combined max drawdown (R) | — |
| Highest pairwise correlation | — |
| Sessions covered | — |

---

## How agent discretion works against this book

The agents get to choose *which* book strategy to take when several qualify.
Two things make that safe rather than a licence to freelance:

1. **They can only choose from this list.** Discretion over selection, never
   over rules. A strategy not in the book cannot be traded, and the rules of a
   strategy in the book cannot be varied.
2. **Every entry carries its mechanical baseline.** That number is the benchmark
   discretion has to beat. If agent-selected trading underperforms the
   mechanical baseline over a meaningful sample, discretion gets switched off —
   and we'll know, because the baseline was written down first.

The Vault's limits apply regardless of which strategy fires, and regardless of
what any agent proposes. No LLM is in the risk path. Ever.
