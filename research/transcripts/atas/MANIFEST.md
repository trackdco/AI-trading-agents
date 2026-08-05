# ATAS_EN — channel survey (enumeration only, transcripts BLOCKED)

Source: `https://www.youtube.com/@ATAS_EN/videos`, 60 most recent pulled 2026-08-05.

**Status: transcripts NOT retrieved.** Channel enumeration succeeded; the transcript pulls
tripped YouTube's bot check (`HTTP 429`, then "Sign in to confirm you're not a bot"), and
`youtube-transcript-api` returns `IpBlocked`. This is a datacenter-IP block, not a code
fault — see "How to unblock" below.

---

## What this channel is

**ATAS is an order-flow charting software vendor.** The channel is product marketing plus
education built around features their platform sells: footprint, heatmap, DOM, delta,
volume profile. That is not disqualifying, but it sets the evidence bar:

- Strategies are shaped by what the product can draw.
- There is no incentive to publish a negative result, and none appear.
- No track records, no sample sizes, no out-of-sample claims anywhere in the titles.

Treat everything here as **hypothesis generation only** — the same status as the nine
candidates that all died.

## Content split (60 videos surveyed)

| type | share | usable? |
|---|---|---|
| Product/feature demos (heatmap, DOM, widgets, statistics, updates) | ~40% | no |
| Market-news commentary ("ATAS News", Fed/oil/crypto takes) | ~30% | no |
| **Strategy / method teaching** | ~30% | **yes — the target set** |

## Priority extraction targets

Ordered by views × strategy density:

| id | views | min | title |
|---|---|---|---|
| `jVomJTjmxL4` | 83k | 16 | SMC & Order Flow Trading Strategy |
| `ozgcDPrBxI4` | 78k | 28 | 4 Day Trading Strategies Using Footprint (RAIN) |
| `OuC5rgiIadg` | 27k | 16 | Identify Support/Resistance on a Footprint Chart |
| `tCSISuPe6CI` | 26k | 14 | Footprint Chart Explained: Intro to Strategies |
| `Rq0akXVNgDc` | 20k | 8 | Workshop on the Big Trades (Ronan) |
| `i50dCxemLko` | 18k | 22 | Use THIS Tool to Increase Your Win Rate (Heatmap) |
| `3XwILOWkpoI` | 14k | 9 | Delta Profile & Footprint Strategy (Yuriy Bishko) |
| `5Wvw_ffyJFg` | 14k | 20 | 5 Strategies Using Volume Profile |
| `DKCozl03rbo` | 10k | 12 | VWAP Trading Strategies |
| `5Fg1VQUDWKE` | 6k | 12 | How to Analyze Stop Bars on a Footprint Chart |
| `DAImaXN51b0` | 6.7k | 10 | Stops Hunting, Icebergs and Sweeps |
| `mxanPenW1AY` | 5.5k | 12 | How to Trade on Dead Cat Bounce |

## ⚠️ Overlap with what we have already disproved

**Read this before spending anything on extraction.** Judging by titles alone, the majority
of the strategy content sits inside families this desk has already measured as null:

| ATAS topic | our result |
|---|---|
| Footprint / delta strategies | **LDN-FLOW-01** — minute-aggregate delta, AUC 0.45–0.56 vs 0.5 coin flip |
| Absorption / big trades at levels | **LDN-DEF-01** — price-level absorption, all 3 measures FAIL, n=99/89 |
| Support/resistance on footprint | **LDN-TRAP-01** — level reclaim, well-powered null, n=161/89 |
| Volume profile / POC levels | **LDN-VT-01** — naked POC touched 49.1% vs 50.9% for an arbitrary equidistant level |
| VWAP strategies | **LDN-VWAP-01** — 2σ VWAP fade negative in both eras |

That is roughly **8 of the 12** priority targets landing in already-tombstoned families.

**Genuinely untested here:**
- **Heatmap / resting-liquidity over time** (`i50dCxemLko`, `WzV0PPsx3Xg`). We hold MBP-10
  at one snapshot per minute, so cancellation and refill dynamics are not measurable — but
  static book imbalance is.
- **Stop-hunt / sweep detection** (`DAImaXN51b0`). Adjacent to our ICEBERG proxy (null) but
  the sweep-and-reverse framing is a distinct event definition.
- **MBO DOM** (`Egsuop3crUA`). We have no MBO data at all.

**Recommendation: extract the untested three first**, not the highest-view ones. The 83k-view
SMC/order-flow video is almost certainly a restatement of things measured at AUC 0.5.

## How to unblock

The container IP is blocked by YouTube. Options, cheapest first:

1. **Paste a transcript directly into chat.** Works immediately, zero setup.
2. **Run on your machine and commit** — same transport as the news sentinel:
   ```
   yt-dlp --skip-download --write-auto-subs --sub-langs "en.*" --sub-format vtt \
          -o "%(id)s.%(ext)s" https://www.youtube.com/watch?v=<ID>
   ```
   Drop the `.vtt` files in this directory, commit, push.
3. Wait out the rate limit — unreliable on a datacenter IP and may not clear.

Enumeration worked, so the video list above is real and complete for the 60 most recent.
