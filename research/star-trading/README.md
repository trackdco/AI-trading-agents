# Star Trading channel — research pull

> **BRANCH CLOSED 2026-08-07.** Cluster α is **DEAD on position sizing** — RR 0.2 against a
> level target forces a 424-point median stop, and at MNQ (the smallest listed contract) the
> median loss is 42% of a $2,000 trailing drawdown. Independent of win rate.
> **Start at [`CLOSURE.md`](CLOSURE.md)** — two minutes, and it tells you what is reusable.
> For the next candidate, start at [`star-testing-runbook.md`](star-testing-runbook.md) and run
> PRE-FLIGHT before acquiring anything.
> Scope: this kills α *on NQ in a trailing-drawdown account*, not α as taught on forex/gold,
> which we did not test and make no claim about.

Research material gathered for the high-win-rate / low-RR strategy question, from
[@StarTrading-n8t](https://www.youtube.com/@StarTrading-n8t). External source material,
kept deliberately outside `context/` and away from `strategy-definition-v1.0.md` so it
cannot be mistaken for anything the constitution has adopted.

## Contents

| File | What it is |
|---|---|
| [`CLOSURE.md`](CLOSURE.md) | **Branch closure — start here.** Verdict, cost, what is reusable |
| [`star-testing-runbook.md`](star-testing-runbook.md) | **Staged process for the next candidate**, incl. the PRE-FLIGHT gates |
| [`ledger/README.md`](ledger/README.md) | Cluster verdicts, model census, structural findings |
| [`alpha-feasibility.md`](alpha-feasibility.md) | The DEAD verdict and its full evidence trail |
| [`README-pull.md`](README-pull.md) | Pull status and the diagnosed block — read before running the tooling |
| [`manifest.json`](manifest.json) | `video_id -> status` for all 117 videos; source of truth for what is held |
| `transcripts/<id>.txt` | Timestamped transcripts — the primary artefact for extraction |
| [`HANDOFF.md`](HANDOFF.md) | **Self-contained brief for handing the corpus to another chat** — primer to paste, extraction schema, open questions, tiered watch order |
| [`channel-index.md`](channel-index.md) | All 117 videos — titles, lengths, view counts, links — grouped by topic, with a "where to start" shortlist |
| [`negative-rr-model.md`](negative-rr-model.md) | The model as the channel states it, plus the arithmetic and how it sits against our locked rules |
| [`tools/pull_channel.sh`](tools/pull_channel.sh) | Re-runnable caption pull for the whole channel |
| [`tools/vtt_to_text.py`](tools/vtt_to_text.py) | Converts yt-dlp VTT captions into readable prose |
| [`tools/channel_videos.raw.txt`](tools/channel_videos.raw.txt) | Raw `id\|title\|duration\|views` dump behind the index |

## Status of the pull

**Index complete (117 videos). 7 transcripts held. Pull retired with the branch.**

The listing came down cleanly. Captions were then refused by a two-layer block — HTTP 429
redirecting to Google's CAPTCHA interstitial (IP reputation) plus *"Sign in to confirm you're
not a bot"* (account-level). Diagnosed rather than inferred: a cold, isolated request after a
long idle period failed identically to the hundredth in a sweep, so slowing down alone could
never clear it. The block is intermittent (~1 in 8 served), which is why paced resumable runs
still recovered 7 of the 20-video priority set.

The priority set is **retired**, not abandoned — see [`CLOSURE.md`](CLOSURE.md). #6 is
deprioritised with its reason recorded in the manifest: it was wanted for cluster α's exit
rule and win-rate denominator, and α is dead on a criterion neither can affect. Tooling and
manifest are intact and reusable for the next candidate.

To finish this or any channel, from a home connection with a logged-in browser:

```bash
cd research/star-trading
./tools/pull_channel.sh --cookies-from-browser chrome --limit 20
./tools/pull_channel.sh --status
```

Timestamped `transcripts/*.txt` are committed — the container is ephemeral and the block makes
them expensive to re-obtain. Raw `captions/*.vtt` and the prose variants are gitignored.

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
