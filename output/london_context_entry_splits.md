# LONDON — market context and entry selection on the rr0 book

Base book: **667 deduped displacement setups**, rr0 (next structural level), over 264 fit sessions. Base rate **-3.64 pt/trade**, **30% green days** (all sessions, flat days counted flat).

**16 cells tested.** Every cell is shown in both eras. A cell is bolded only if it is net-positive in 2025 AND 2026 — the burn-list bar (§8.1), not a full-span average that one good era can carry.

The prop bar for reference: net ≥ 4 pt, T ≥ 2, N ≥ 200, green ≥ 55%.

## Market context (handoff §6, §12 step 2)

**trend_align**

| cell | N | net pt | green | T | 2025 net | 2025 green | 2026 net | 2026 green |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| against_trend | 261 | -4.01 | 20% | -4.15 | -1.38 | 25% | -7.46 | 15% |
| neutral ᴺ | 147 | -3.72 | 7% | -3.20 | -2.45 | 9% | -8.87 | 4% |
| with_trend | 259 | -3.21 | 20% | -3.13 | -1.47 | 19% | -5.54 | 21% |

ᴺ = under the N ≥ 200 bar; the cell is too small to carry a verdict.

**trend_state**

| cell | N | net pt | green | T | 2025 net | 2025 green | 2026 net | 2026 green |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| bear ᴺ | 155 | -6.72 | 6% | -4.69 | -2.81 | 6% | -9.25 | 7% |
| bull ᴺ | 146 | -2.77 | 5% | -2.86 | -1.83 | 7% | -5.44 | 3% |
| neutral ᴺ | 145 | -3.71 | 7% | -3.16 | -2.45 | 9% | -9.20 | 4% |
| no_context ᴺ | 2 | -4.38 | 0% | -0.52 | — | — | -4.38 | 0% |
| strong_bear ᴺ | 54 | -1.64 | 4% | -0.47 | +3.24 | 3% | -4.52 | 5% |
| strong_bull ᴺ | 165 | -2.10 | 8% | -2.06 | -1.10 | 8% | -3.94 | 7% |

ᴺ = under the N ≥ 200 bar; the cell is too small to carry a verdict.

**vol_state**

| cell | N | net pt | green | T | 2025 net | 2025 green | 2026 net | 2026 green |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| high ᴺ | 160 | -5.43 | 9% | -3.17 | +0.07 | 7% | -7.72 | 11% |
| low | 226 | -3.64 | 7% | -4.71 | -2.81 | 10% | -7.39 | 3% |
| no_context ᴺ | 2 | -4.38 | 0% | -0.52 | — | — | -4.38 | 0% |
| normal | 279 | -2.60 | 14% | -3.04 | -1.07 | 15% | -5.48 | 12% |

ᴺ = under the N ≥ 200 bar; the cell is too small to carry a verdict.

**balance_state**

| cell | N | net pt | green | T | 2025 net | 2025 green | 2026 net | 2026 green |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| balance ᴺ | 46 | -1.83 | 2% | -0.74 | -1.27 | 2% | -2.78 | 3% |
| edge ᴺ | 96 | -3.06 | 6% | -1.89 | -0.36 | 9% | -8.71 | 3% |
| imbalance | 523 | -3.90 | 22% | -5.74 | -2.03 | 22% | -6.85 | 21% |
| no_context ᴺ | 2 | -4.38 | 0% | -0.52 | — | — | -4.38 | 0% |

ᴺ = under the N ≥ 200 bar; the cell is too small to carry a verdict.

## Entry selection — the §8.7 tension, B2 removed

`e3_NEVER_filled` are setups the LIMIT entry would have missed entirely; the displacement entry is the only reason they exist as trades.

> ⚠️ **THIS IS NOT A TRADEABLE FILTER — it is a lookahead split.** Whether the E3 limit ever fills is settled AFTER the displacement entry: measured, E3 fills a minimum of **1 minute** after its trigger (median 1, max 110), and **0.0%** fill on the trigger bar itself. At the moment you enter the displacement you cannot know which side of this split you are on. Read it as a DIAGNOSTIC — it says *which* London displacements pay — never as a rule to trade.

**e3_entry**

| cell | N | net pt | green | T | 2025 net | 2025 green | 2026 net | 2026 green |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| e3_NEVER_filled ᴺ | 99 | **+4.58** | 22% | 2.93 | +6.79 | 26% | +1.17 | 16% |
| e3_would_have_filled | 568 | -5.07 | 22% | -7.94 | -3.16 | 25% | -8.23 | 19% |

ᴺ = under the N ≥ 200 bar; the cell is too small to carry a verdict.

