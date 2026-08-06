# LDN-OBK-01 / LDN-PO3-01 — depth pass (canon variable map)

Authorised by `docs/PREREG-london-depth-pass.md`. Eight checks at frozen canon thresholds, each
evaluated ALONE (§5.12.2). NaN stands down — excluded from BOTH arms.
`thin` = fewer than 15 rows a side, and thin means **no verdict**, not a
fail. Survival requires the same direction in EVERY era.

Depth resolved on **1168 of 1528** trades.
2025 is H2 only (depth starts June). 2023/24 depth not read.

## F1

| check | era | cost | n pass | n fail | R pass | R fail | lift_R |
|---|---|---|---:|---:|---:|---:|---:|
| `W` | 2025 | — | 5 | 147 | — | — | **thin** |
| `W` | 2026 | — | 1 | 124 | — | — | **thin** |
| `D` | 2025 | — | 149 | 3 | — | — | **thin** |
| `D` | 2026 | — | 123 | 2 | — | — | **thin** |
| `WALLSZ` | 2025 | base | 70 | 82 | -0.246 | -0.317 | **+0.071** |
| `WALLSZ` | 2025 | strict | 70 | 82 | -0.365 | -0.428 | **+0.063** |
| `WALLSZ` | 2026 | base | 29 | 96 | +0.204 | -0.059 | **+0.263** |
| `WALLSZ` | 2026 | strict | 29 | 96 | +0.128 | -0.129 | **+0.257** |
| `WALLFAR` | 2025 | base | 22 | 125 | -0.241 | -0.258 | **+0.017** |
| `WALLFAR` | 2025 | strict | 22 | 125 | -0.354 | -0.373 | **+0.019** |
| `WALLFAR` | 2026 | base | 30 | 94 | +0.463 | -0.133 | **+0.597** |
| `WALLFAR` | 2026 | strict | 30 | 94 | +0.400 | -0.207 | **+0.606** |
| `IMBWITH` | 2025 | base | 38 | 114 | -0.442 | -0.232 | **-0.210** |
| `IMBWITH` | 2025 | strict | 38 | 114 | -0.571 | -0.342 | **-0.229** |
| `IMBWITH` | 2026 | base | 43 | 82 | -0.164 | +0.089 | **-0.253** |
| `IMBWITH` | 2026 | strict | 43 | 82 | -0.243 | +0.022 | **-0.265** |
| `SUPRES` | 2025 | base | 38 | 114 | -0.442 | -0.232 | **-0.210** |
| `SUPRES` | 2025 | strict | 38 | 114 | -0.571 | -0.342 | **-0.229** |
| `SUPRES` | 2026 | base | 43 | 82 | -0.164 | +0.089 | **-0.253** |
| `SUPRES` | 2026 | strict | 43 | 82 | -0.243 | +0.022 | **-0.265** |
| `THICKHI` | 2025 | base | 74 | 78 | -0.219 | -0.346 | **+0.128** |
| `THICKHI` | 2025 | strict | 74 | 78 | -0.340 | -0.455 | **+0.115** |
| `THICKHI` | 2026 | base | 15 | 110 | +0.406 | -0.053 | **+0.459** |
| `THICKHI` | 2026 | strict | 15 | 110 | +0.288 | -0.118 | **+0.406** |
| `BUILD` | 2025 | base | 61 | 71 | -0.195 | -0.280 | **+0.085** |
| `BUILD` | 2025 | strict | 61 | 71 | -0.313 | -0.389 | **+0.076** |
| `BUILD` | 2026 | base | 45 | 59 | -0.013 | +0.141 | **-0.154** |
| `BUILD` | 2026 | strict | 45 | 59 | -0.085 | +0.079 | **-0.164** |

## A/S1

| check | era | cost | n pass | n fail | R pass | R fail | lift_R |
|---|---|---|---:|---:|---:|---:|---:|
| `W` | 2025 | base | 37 | 125 | +0.309 | -0.425 | **+0.734** |
| `W` | 2025 | strict | 37 | 125 | +0.204 | -0.550 | **+0.754** |
| `W` | 2026 | base | 38 | 100 | +0.561 | -0.195 | **+0.756** |
| `W` | 2026 | strict | 38 | 100 | +0.478 | -0.270 | **+0.748** |
| `D` | 2025 | base | 116 | 46 | -0.091 | -0.675 | **+0.584** |
| `D` | 2025 | strict | 116 | 46 | -0.212 | -0.795 | **+0.583** |
| `D` | 2026 | base | 92 | 46 | +0.216 | -0.393 | **+0.609** |
| `D` | 2026 | strict | 92 | 46 | +0.134 | -0.460 | **+0.593** |
| `WALLSZ` | 2025 | base | 65 | 97 | -0.126 | -0.345 | **+0.219** |
| `WALLSZ` | 2025 | strict | 65 | 97 | -0.255 | -0.460 | **+0.205** |
| `WALLSZ` | 2026 | base | 28 | 110 | +0.299 | -0.059 | **+0.358** |
| `WALLSZ` | 2026 | strict | 28 | 110 | +0.205 | -0.133 | **+0.338** |
| `WALLFAR` | 2025 | base | 63 | 62 | -0.532 | -0.315 | **-0.217** |
| `WALLFAR` | 2025 | strict | 63 | 62 | -0.645 | -0.453 | **-0.192** |
| `WALLFAR` | 2026 | base | 58 | 42 | -0.331 | -0.007 | **-0.323** |
| `WALLFAR` | 2026 | strict | 58 | 42 | -0.403 | -0.087 | **-0.316** |
| `IMBWITH` | 2025 | base | 86 | 76 | -0.114 | -0.419 | **+0.305** |
| `IMBWITH` | 2025 | strict | 86 | 76 | -0.227 | -0.548 | **+0.320** |
| `IMBWITH` | 2026 | base | 79 | 59 | -0.024 | +0.064 | **-0.088** |
| `IMBWITH` | 2026 | strict | 79 | 59 | -0.100 | -0.016 | **-0.084** |
| `SUPRES` | 2025 | base | 86 | 76 | -0.114 | -0.419 | **+0.305** |
| `SUPRES` | 2025 | strict | 86 | 76 | -0.227 | -0.548 | **+0.320** |
| `SUPRES` | 2026 | base | 79 | 59 | -0.024 | +0.064 | **-0.088** |
| `SUPRES` | 2026 | strict | 79 | 59 | -0.100 | -0.016 | **-0.084** |
| `THICKHI` | 2025 | base | 77 | 85 | -0.191 | -0.318 | **+0.127** |
| `THICKHI` | 2025 | strict | 77 | 85 | -0.337 | -0.415 | **+0.078** |
| `THICKHI` | 2026 | base | 21 | 117 | +0.330 | -0.043 | **+0.373** |
| `THICKHI` | 2026 | strict | 21 | 117 | +0.231 | -0.117 | **+0.347** |
| `BUILD` | 2025 | base | 73 | 64 | -0.157 | -0.400 | **+0.242** |
| `BUILD` | 2025 | strict | 73 | 64 | -0.278 | -0.520 | **+0.242** |
| `BUILD` | 2026 | base | 58 | 48 | -0.118 | -0.039 | **-0.079** |
| `BUILD` | 2026 | strict | 58 | 48 | -0.198 | -0.115 | **-0.083** |

## F2

| check | era | cost | n pass | n fail | R pass | R fail | lift_R |
|---|---|---|---:|---:|---:|---:|---:|
| `W` | 2025 | — | 5 | 147 | — | — | **thin** |
| `W` | 2026 | — | 1 | 124 | — | — | **thin** |
| `D` | 2025 | — | 149 | 3 | — | — | **thin** |
| `D` | 2026 | — | 123 | 2 | — | — | **thin** |
| `WALLSZ` | 2025 | base | 70 | 82 | -0.113 | -0.457 | **+0.344** |
| `WALLSZ` | 2025 | strict | 70 | 82 | -0.232 | -0.568 | **+0.336** |
| `WALLSZ` | 2026 | base | 29 | 96 | +1.007 | +0.089 | **+0.918** |
| `WALLSZ` | 2026 | strict | 29 | 96 | +0.930 | +0.019 | **+0.912** |
| `WALLFAR` | 2025 | base | 22 | 125 | -0.402 | -0.247 | **-0.155** |
| `WALLFAR` | 2025 | strict | 22 | 125 | -0.515 | -0.362 | **-0.153** |
| `WALLFAR` | 2026 | base | 30 | 94 | +0.960 | +0.106 | **+0.854** |
| `WALLFAR` | 2026 | strict | 30 | 94 | +0.896 | +0.033 | **+0.864** |
| `IMBWITH` | 2025 | base | 38 | 114 | -0.701 | -0.164 | **-0.537** |
| `IMBWITH` | 2025 | strict | 38 | 114 | -0.830 | -0.274 | **-0.556** |
| `IMBWITH` | 2026 | base | 43 | 82 | +0.055 | +0.431 | **-0.376** |
| `IMBWITH` | 2026 | strict | 43 | 82 | -0.024 | +0.363 | **-0.388** |
| `SUPRES` | 2025 | base | 38 | 114 | -0.701 | -0.164 | **-0.537** |
| `SUPRES` | 2025 | strict | 38 | 114 | -0.830 | -0.274 | **-0.556** |
| `SUPRES` | 2026 | base | 43 | 82 | +0.055 | +0.431 | **-0.376** |
| `SUPRES` | 2026 | strict | 43 | 82 | -0.024 | +0.363 | **-0.388** |
| `THICKHI` | 2025 | base | 74 | 78 | -0.168 | -0.422 | **+0.253** |
| `THICKHI` | 2025 | strict | 74 | 78 | -0.289 | -0.530 | **+0.241** |
| `THICKHI` | 2026 | base | 15 | 110 | +1.418 | +0.149 | **+1.269** |
| `THICKHI` | 2026 | strict | 15 | 110 | +1.301 | +0.084 | **+1.217** |
| `BUILD` | 2025 | base | 61 | 71 | -0.054 | -0.304 | **+0.250** |
| `BUILD` | 2025 | strict | 61 | 71 | -0.171 | -0.413 | **+0.242** |
| `BUILD` | 2026 | base | 45 | 59 | +0.170 | +0.481 | **-0.310** |
| `BUILD` | 2026 | strict | 45 | 59 | +0.098 | +0.419 | **-0.321** |

## B/S1

| check | era | cost | n pass | n fail | R pass | R fail | lift_R |
|---|---|---|---:|---:|---:|---:|---:|
| `W` | 2025 | — | 3 | 163 | — | — | **thin** |
| `W` | 2026 | — | 1 | 147 | — | — | **thin** |
| `D` | 2025 | — | 161 | 5 | — | — | **thin** |
| `D` | 2026 | — | 145 | 3 | — | — | **thin** |
| `WALLSZ` | 2025 | base | 89 | 77 | -0.340 | -0.163 | **-0.177** |
| `WALLSZ` | 2025 | strict | 89 | 77 | -0.506 | -0.300 | **-0.206** |
| `WALLSZ` | 2026 | base | 38 | 110 | +0.237 | -0.125 | **+0.362** |
| `WALLSZ` | 2026 | strict | 38 | 110 | +0.133 | -0.226 | **+0.359** |
| `WALLFAR` | 2025 | base | 29 | 134 | -0.467 | -0.216 | **-0.251** |
| `WALLFAR` | 2025 | strict | 29 | 134 | -0.613 | -0.372 | **-0.241** |
| `WALLFAR` | 2026 | base | 23 | 124 | +0.300 | -0.085 | **+0.385** |
| `WALLFAR` | 2026 | strict | 23 | 124 | +0.200 | -0.187 | **+0.387** |
| `IMBWITH` | 2025 | base | 65 | 101 | -0.199 | -0.296 | **+0.098** |
| `IMBWITH` | 2025 | strict | 65 | 101 | -0.345 | -0.452 | **+0.106** |
| `IMBWITH` | 2026 | base | 72 | 76 | -0.090 | +0.023 | **-0.113** |
| `IMBWITH` | 2026 | strict | 72 | 76 | -0.187 | -0.083 | **-0.104** |
| `SUPRES` | 2025 | base | 65 | 101 | -0.199 | -0.296 | **+0.098** |
| `SUPRES` | 2025 | strict | 65 | 101 | -0.345 | -0.452 | **+0.106** |
| `SUPRES` | 2026 | base | 72 | 76 | -0.090 | +0.023 | **-0.113** |
| `SUPRES` | 2026 | strict | 72 | 76 | -0.187 | -0.083 | **-0.104** |
| `THICKHI` | 2025 | base | 87 | 79 | -0.336 | -0.172 | **-0.164** |
| `THICKHI` | 2025 | strict | 87 | 79 | -0.512 | -0.298 | **-0.215** |
| `THICKHI` | 2026 | base | 21 | 127 | +0.150 | -0.062 | **+0.212** |
| `THICKHI` | 2026 | strict | 21 | 127 | +0.015 | -0.158 | **+0.173** |
| `BUILD` | 2025 | base | 72 | 52 | -0.294 | -0.079 | **-0.214** |
| `BUILD` | 2025 | strict | 72 | 52 | -0.460 | -0.228 | **-0.232** |
| `BUILD` | 2026 | base | 59 | 46 | -0.177 | -0.026 | **-0.152** |
| `BUILD` | 2026 | strict | 59 | 46 | -0.279 | -0.133 | **-0.146** |

## Scorecard — §5.12.3 kill classes

| arm | check | lifts by era (base cost) | class |
|---|---|---|---|
| F1 | `W` | — | no verdict (thin) |
| F1 | `D` | — | no verdict (thin) |
| F1 | `WALLSZ` | +0.071, +0.263 | **SURVIVES — positive every era** |
| F1 | `WALLFAR` | +0.017, +0.597 | **SURVIVES — positive every era** |
| F1 | `IMBWITH` | -0.210, -0.253 | kill — negative every era |
| F1 | `SUPRES` | -0.210, -0.253 | kill — negative every era |
| F1 | `THICKHI` | +0.128, +0.459 | **SURVIVES — positive every era** |
| F1 | `BUILD` | +0.085, -0.154 | era-flip — never ship (§5.12.3) |
| A/S1 | `W` | +0.734, +0.756 | **SURVIVES — positive every era** |
| A/S1 | `D` | +0.584, +0.609 | **SURVIVES — positive every era** |
| A/S1 | `WALLSZ` | +0.219, +0.358 | **SURVIVES — positive every era** |
| A/S1 | `WALLFAR` | -0.217, -0.323 | kill — negative every era |
| A/S1 | `IMBWITH` | +0.305, -0.088 | era-flip — never ship (§5.12.3) |
| A/S1 | `SUPRES` | +0.305, -0.088 | era-flip — never ship (§5.12.3) |
| A/S1 | `THICKHI` | +0.127, +0.373 | **SURVIVES — positive every era** |
| A/S1 | `BUILD` | +0.242, -0.079 | era-flip — never ship (§5.12.3) |
| F2 | `W` | — | no verdict (thin) |
| F2 | `D` | — | no verdict (thin) |
| F2 | `WALLSZ` | +0.344, +0.918 | **SURVIVES — positive every era** |
| F2 | `WALLFAR` | -0.155, +0.854 | era-flip — never ship (§5.12.3) |
| F2 | `IMBWITH` | -0.537, -0.376 | kill — negative every era |
| F2 | `SUPRES` | -0.537, -0.376 | kill — negative every era |
| F2 | `THICKHI` | +0.253, +1.269 | **SURVIVES — positive every era** |
| F2 | `BUILD` | +0.250, -0.310 | era-flip — never ship (§5.12.3) |
| B/S1 | `W` | — | no verdict (thin) |
| B/S1 | `D` | — | no verdict (thin) |
| B/S1 | `WALLSZ` | -0.177, +0.362 | era-flip — never ship (§5.12.3) |
| B/S1 | `WALLFAR` | -0.251, +0.385 | era-flip — never ship (§5.12.3) |
| B/S1 | `IMBWITH` | +0.098, -0.113 | era-flip — never ship (§5.12.3) |
| B/S1 | `SUPRES` | +0.098, -0.113 | era-flip — never ship (§5.12.3) |
| B/S1 | `THICKHI` | -0.164, +0.212 | era-flip — never ship (§5.12.3) |
| B/S1 | `BUILD` | -0.214, -0.152 | kill — negative every era |

## Why `W` and `D` are thin on three arms and not on the fourth

Not an artifact — a real property of where each arm enters, and it is the
reason the canon's gate is meaningful here at all.

`F1`, `F2` and `B/S1` all enter **inside the book**: at a fail-bar close or a
trigger-candle close, with resting size on both sides. So there is nearly
always a wall both above and below — `W` passes 4–6 times out of 277–314 and
`D` passes almost always. Degenerate, correctly flagged thin, no verdict.

`A/S1` enters **at a price extreme**, filled by a resting stop order when price
trades through the trigger candle. At that minute the book is genuinely
one-sided: `W` splits 75/225 and `D` splits 208/92. **A wall behind is only a
meaningful question when you have just pushed to a new extreme** — which is
exactly the condition the canon's pre-market book is in, and exactly why the
same gate transfers.

## Verdict

**9 of 32 check×arm cells survive every era.**

- `WALLSZ` on **F1**: lifts [0.071, 0.263]
- `WALLFAR` on **F1**: lifts [0.017, 0.597]
- `THICKHI` on **F1**: lifts [0.128, 0.459]
- `W` on **A/S1**: lifts [0.734, 0.756]
- `D` on **A/S1**: lifts [0.584, 0.609]
- `WALLSZ` on **A/S1**: lifts [0.219, 0.358]
- `THICKHI` on **A/S1**: lifts [0.127, 0.373]
- `WALLSZ` on **F2**: lifts [0.344, 0.918]
- `THICKHI` on **F2**: lifts [0.253, 1.269]

A survivor is **not** adopted here. Per the prereg it becomes a
declared arm in a later prereg, after a permutation null (§5.12.4) and a
state-conditional re-test (§5.11.4).

### Which survivors are positive at STRICT cost in both eras

Lift is not profit. A check can separate a bad population into worse and
less-bad and survive every era while never crossing zero — most of the
family's conditioning so far has done exactly that.

| arm | check | 2025 R pass (strict) | 2026 R pass (strict) | n pass | pays |
|---|---|---:|---:|---:|---|
| F1 | `WALLSZ` | -0.365 | +0.128 | 70/29 | no |
| F1 | `WALLFAR` | -0.354 | +0.400 | 22/30 | no |
| F1 | `THICKHI` | -0.340 | +0.288 | 74/15 | no |
| A/S1 | `W` | +0.204 | +0.478 | 37/38 | **YES** |
| A/S1 | `D` | -0.212 | +0.134 | 116/92 | no |
| A/S1 | `WALLSZ` | -0.255 | +0.205 | 65/28 | no |
| A/S1 | `THICKHI` | -0.337 | +0.231 | 77/21 | no |
| F2 | `WALLSZ` | -0.232 | +0.930 | 70/29 | no |
| F2 | `THICKHI` | -0.289 | +1.301 | 74/15 | no |
