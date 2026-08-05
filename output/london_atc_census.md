# LDN-ATC-01 — L0 census (the pre-London pullback)

Authorised by `docs/PREREG-london-atc-census.md`. **Counting only — no P&L computed, none may kill**
(§5.9.1). Bars only. 2023/24 untouched, no holdout look spent.

Basis (§5.12.13): NQ 1m, 396 sessions with >= 200 bars in
00:00-10:00 London; windows declared in London local time, converted per day.

## 1. Terminal-status funnel (§5.12.1 — every session accounted, no silent drops)

| status | 2025 | 2026 | total | share |
|---|---:|---:|---:|---:|
| `no_bias` | 59 | 28 | 87 | 22% |
| `bias_no_pullback` | 5 | 1 | 6 | 2% |
| `pullback_no_lta` | 102 | 58 | 160 | 40% |
| `lta_no_trigger` | 18 | 12 | 30 | 8% |
| `fallback_only` | 4 | 1 | 5 | 1% |
| `triggered` | 69 | 39 | 108 | 27% |

## 2. Census kill line — declared floor 15% of sessions triggered

| era | sessions | triggered | rate | verdict |
|---|---:|---:|---:|---|
| 2025 | 257 | 69 | **27%** | PASS |
| 2026 | 139 | 39 | **28%** | PASS |

**PASSES in both eras.**

## 3. Half-year decomposition (§5.11.5 — year pooling has hidden a bad half twice)

| half | sessions | triggered | rate |
|---|---:|---:|---:|
| 2025H1 | 127 | 37 | 29% |
| 2025H2 | 130 | 32 | 25% |
| 2026H1 | 128 | 33 | 26% |
| 2026H2 | 11 | 6 | 55% |

## 4. Event-universe sensitivity (§5.11.2) — declared at census, before economics

| era | first-trigger/day | all triggers | ratio | fallback-arm days |
|---|---:|---:|---:|---:|
| 2025 | 69 | 107 | 1.55x | 4 |
| 2026 | 39 | 59 | 1.51x | 1 |

## 5. LTA semantics cross-tab (§5.12.15 — what the column actually computes)

The prereg mechanised his LTA rule as **>=2 consecutive 15m closes in the
pullback direction**. That translation is mine. Distribution of the longest
such run, over sessions that reached the pullback stage:

| longest run | sessions | share | passes LTA test |
|---|---:|---:|---|
| 0 | 23 | 8% | no |
| 1 | 137 | 45% | no |
| 2 | 86 | 28% | yes |
| 3 | 45 | 15% | yes |
| 4 | 12 | 4% | yes |

Median 15m bars available in the pullback window: **4** (a 60-minute window holds 4). So the
'>=2 consecutive' bar is being cleared inside a 4-bar window — a materially
looser test than the word 'low traffic area' suggests, and the verdict must
say so rather than let the name carry weight the column has not earned.

## 6. When the trigger fires (London local)

| time | count |
|---|---:|
| 07:30 | 29 |
| 08:00 | 37 |
| 08:30 | 26 |
| 09:00 | 16 |

**29 of 108 (27%) fire BEFORE the 08:00 open** — consistent with the taught setup, which enters on the pullback rather than at the open.

## 7. Lookahead audit (§5.11.7) — certified, not assumed

- Bias reads 03:30-07:00 only and is fixed at 07:00.
- Pullback reads 07:00-08:00 and is measured against the 07:00 close.
- Triggers use right-closed, right-labelled resampling, so a 15m/30m/60m bar
  labelled `T` contains only data strictly before `T`. A trigger at 08:15 uses
  the bar that closed at 08:15 and nothing after it.
- No column in this census reads a bar that closes after the decision minute.
