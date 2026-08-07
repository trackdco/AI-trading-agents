# Star Trading channel — research pull

> **BRANCH CLOSED 2026-08-07.** Cluster α is **DEAD on position sizing** — RR 0.2 against a
> level target forces a 424-point median stop, and at MNQ (the smallest listed contract) the
> median loss is 42% of a $2,000 trailing drawdown. Independent of win rate.
> **Start at [`CLOSURE.md`](CLOSURE.md)** — two minutes, and it tells you what is reusable.
> Scope: this kills α *on NQ in a trailing-drawdown account*, not α as taught on forex/gold,
> which we did not test and make no claim about.

Research material gathered for the high-win-rate / low-RR strategy question, from
[@StarTrading-n8t](https://www.youtube.com/@StarTrading-n8t). External source material,
kept deliberately outside `context/` and away from `strategy-definition-v1.0.md` so it
cannot be mistaken for anything the constitution has adopted.

## Contents

| File | What it is |
|---|---|
| [`README-pull.md`](README-pull.md) | **Pull status, the diagnosed block, and how to finish it** — read this before running the tooling |
| [`manifest.json`](manifest.json) | `video_id -> status` for all 117 videos; source of truth for what is held |
| `transcripts/<id>.txt` | Timestamped transcripts — the primary artefact for extraction |
| [`HANDOFF.md`](HANDOFF.md) | **Self-contained brief for handing the corpus to another chat** — primer to paste, extraction schema, open questions, tiered watch order |
| [`channel-index.md`](channel-index.md) | All 117 videos — titles, lengths, view counts, links — grouped by topic, with a "where to start" shortlist |
| [`negative-rr-model.md`](negative-rr-model.md) | The model as the channel states it, plus the arithmetic and how it sits against our locked rules |
| [`tools/pull_channel.sh`](tools/pull_channel.sh) | Re-runnable caption pull for the whole channel |
| [`tools/vtt_to_text.py`](tools/vtt_to_text.py) | Converts yt-dlp VTT captions into readable prose |
| [`tools/channel_videos.raw.txt`](tools/channel_videos.raw.txt) | Raw `id\|title\|duration\|views` dump behind the index |

## Status of the pull — read this

**The channel index is complete. The transcripts are not.**

The video listing came down cleanly, and one full transcript was captured before YouTube's
bot check closed the door. Every subsequent request — across four yt-dlp player clients,
direct HTML fetch, and two third-party transcript mirrors — was refused with
*"Sign in to confirm you're not a bot"*, and the IP now receives Google's CAPTCHA
interstitial on any YouTube URL. This is standard treatment for cloud and datacentre
address ranges; it is not a problem with the tooling.

So `negative-rr-model.md` rests on **one** of 117 videos. It happens to be a good one — a
full worked backtest session that states the rules, the targets and the sizing — but it is
one source, and the analysis flags where the remaining videos would confirm or overturn it.

## Finishing the pull

Run this from a home connection, where the bot check does not fire:

```bash
cd research/star-trading
./tools/pull_channel.sh captions
python3 tools/vtt_to_text.py captions transcripts
```

Roughly 45 hours of video, so expect the pull to take a while — the script is deliberately
throttled, which is cheaper than getting the address flagged and waiting the block out. If
the bot check appears anyway, pass browser cookies:

```bash
YTDLP_EXTRA="--cookies-from-browser chrome" ./tools/pull_channel.sh captions
```

`captions/` and `transcripts/` are gitignored — they are someone else's material, and this
repo should hold our reading of it rather than a wholesale copy of it.

## The short version

The channel is one thesis restated 117 times: take targets smaller than your stop and win
often enough to come out ahead. The mechanics are legible and partly mechanisable. The
evidence is not — the backtests exclude spread and commission, which at a 2-pip target is
where most of the edge would go, and the headline 95% win rate is never separated from the
~83% that costs actually demand.

Note also that a 0.5R target contradicts §6.5 of `strategy-definition-v1.0.md` outright,
which sets a 1.5R floor. Nothing here changes that, and nothing should until the usual gate
has been walked. The last section of `negative-rr-model.md` sketches how we could answer the
underlying question from our own NQ data instead, which would be worth considerably more
than the source material.
