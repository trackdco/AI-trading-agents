# Next extraction targets — queued, blocked on YouTube rate limit

**Status 2026-08-05:** container IP blocked by YouTube (`yt-dlp` → "Sign in to confirm you're
not a bot"; `youtube-transcript-api` → `IpBlocked`). Triggered by the full 602-video
enumeration. Cleared in ~30–40 min on the previous occurrence.

These four close every open question on `ash-unicorn-sb` except order-block identification.

| # | id | title | what it should resolve | dur |
|---|---|---|---|---|
| 1 | `qngA8aIfV0M` | The ONLY ICT Silver Bullet Video You Need — Simplified PROFITABLE Model | Likely his canonical statement of the model. Should settle **Contradiction #1 (macro required?)** and **#4 (target: fixed 2R or take-the-draw)** | 11:52 |
| 2 | `01xGCvuY3p8` | Read Price Action & Correctly Manage Your Trades — Breakeven, Trailing Stops & MORE | **Contradiction #5** — the trailing rule, stated then overridden in all three carded videos. A dedicated management video should be decisive | 23:52 |
| 3 | `N1EXytfVsiI` | HOW TO DEAL WITH GETTING COOKED \*FULL TRANSPARENCY\* (im still up on the month) | The highest-value video for honest assessment: a **losing** period discussed directly. Tests whether the model's failure modes are disclosed | 6:45 |
| 4 | `Ee_tC5P-F20` | +$0 on NASDAQ! LDN AM Macro LONGZ — 3:45–4:15AM ICT LDN | The **uncarded London variant**, and a non-winner. Two gaps in one video | 5:39 |

## To pull (either party)

```bash
cd research/ash10hazard/transcripts
for v in qngA8aIfV0M 01xGCvuY3p8 N1EXytfVsiI Ee_tC5P-F20; do
  yt-dlp --skip-download --write-auto-subs --sub-langs "en.*" --sub-format vtt \
         -o "%(id)s.%(ext)s" "https://www.youtube.com/watch?v=$v"
  sleep 25
done
```

Then convert to timestamped text with `scratchpad/vtt_ts.py` (timestamps are required —
every card rule needs an `[videoId @ mm:ss]` citation).

## Open questions these do NOT close

**Order-block identification.** He states the judgement layer cannot be taught
(`1cMWnAxElA0 @ 04:42`), so no additional video is likely to specify it. Any test must
either supply our own definition — labelled as ours — or omit the component.

— added by ash10hazard-analyst, 2026-08-05
