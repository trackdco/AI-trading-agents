# YouTube Research MCP

Transcript sourcing for the research lane (`research/README.md`).

**The gap it closes.** The 2026-08-04 sweeps in `research/articles/` are
WebSearch extracts, because direct page fetches are 403-blocked at egress —
so URLs are recorded as *leads for the deep-dive round*, not as sources. For
video sources this server closes that: it fetches the actual transcript, stamps
every line with a timestamp, and commits it under `research/youtube/`. A thesis
can then quote what a trader said, at the second they said it, and anyone can
re-check it.

It does not change the process. Stage 1 broad sweep → theses in
`candidates/`; Angus greenlights; stage 2 deep dive. This just makes the
sourcing real for one class of source.

## Install (one time, on the workstation running Claude Code)

```bash
cd tools/youtube-mcp
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python -e ".[dev]"
```

Its own venv on purpose: `mcp` and `youtube-transcript-api` are not on the
engine's approved-dependency list and have no business in `requirements.txt`.

## Configure

Registered for this repo in `.mcp.json`, so Claude Code picks it up when
started from the project directory (it prompts for approval the first time).

Add to `.env`:

```
YOUTUBE_API_KEY=AIza...
```

[Google Cloud Console](https://console.cloud.google.com) → new project → enable
**YouTube Data API v3** → Credentials → API key. Restrict the key to that API.
Free tier is 10,000 units/day; a search costs 100, so ~100 searches/day.

**Nothing here needs the key any more.** Search and channel listing scrape the
public pages; transcripts never needed it. A key only adds exact view counts and
server-side duration/date filtering on `youtube_search`.

| Optional var | Purpose |
|---|---|
| `YOUTUBE_MCP_CACHE_DIR` | Cache root. Default `research/youtube/`. |
| `YOUTUBE_TRANSCRIPT_PROXY` | HTTP proxy for transcript fetches. **The durable fix for datacenter IPs** — see below. |
| `YOUTUBE_TRANSCRIPT_DELAY` | Seconds between transcript fetches in a dive. Default `1.5`. Raise it if you are getting blocked. |

## Verify

```bash
tools/youtube-mcp/.venv/bin/python -m pytest tools/youtube-mcp/test_server.py -q
```

Then `/mcp` in Claude Code should list `youtube-research` as connected.

## Tools

| Tool | Key? | What it's for |
|---|---|---|
| `youtube_channel_deep_dive` | no | **Start here for a trader.** Enumerate a whole channel, transcribe everything passing the filters, return a ranked index. |
| `youtube_channel_videos` | no | A channel's full upload catalogue — titles, durations, views, ages. Triage before spending transcript budget. |
| `youtube_research_sweep` | no | Topic sweep: search, cache every transcript, return a ranked index — never the text. |
| `youtube_grep_transcripts` | no | Regex across cached transcripts with timestamps. Extract stated rules from twelve videos without loading twelve videos. |
| `youtube_get_transcript` | no | One transcript. Excerpt + cache path by default; `full=True` when you mean it. |
| `youtube_article_record` | no | Writes the `research/articles/` file with correct frontmatter and the source table filled in. |
| `youtube_search` | no | Plain search, no transcripts. Scrapes when no key is set. |
| `youtube_video_details` | yes | Duration/views/likes/description — credibility triage. |
| `youtube_find_channel` | yes | Find a trusted trader's channel ID, then search within it only. |
| `youtube_list_transcript_languages` | no | Diagnostic when a fetch fails. |
| `youtube_cache_status` | no | What's already pulled. |

## The context discipline

A 60-minute trading video is ~60,000 characters ≈ 15,000 tokens. Twelve is
~180,000 — a context window spent before any thinking happens.

So the sweep **never returns transcript text**. It returns an index with a
`rule_keyword_hits` score per video: how often the speaker says "entry",
"stop loss", "invalidation", "session", "filter" — i.e. how often they state a
rule rather than narrate. It ranks reading order; it is not a quality score.

```
youtube_research_sweep("london open sweep nasdaq futures", max_videos=12)
youtube_grep_transcripts(r"stop.?loss|invalidat|risk to reward|session")
youtube_get_transcript("<top hit>", full=True)     # the two that matter, no more
youtube_article_record(title=..., sweep_label=..., session="london",
                       mechanism_families=["order-flow"])
```

`youtube_article_record` validates `session` and `mechanism_families` against
the controlled vocabulary in `docs/VAULT-SCHEMA.md` §5 and refuses improvised
values — the vault treats those as lint failures, so it is cheaper to fail here
than to write a file that breaks retrieval later.

## Known failure modes

- **"Transcripts are disabled"** — the uploader turned captions off. The sweep
  records it under `failures` and carries on; `youtube_article_record` lists
  those videos in a "No transcript available" section so the gap is visible
  rather than silent.
- **`RequestBlocked` / `IpBlocked`** — the big one, and it is *rate*-driven as
  much as IP-driven. A channel dive is a burst of dozens of requests, which is
  exactly what YouTube throttles; once tripped, every client context returns
  *"Sign in to confirm you're not a bot"* and the block persists for a cooldown.
  Three mitigations, all in place: `YOUTUBE_TRANSCRIPT_DELAY` paces the dive,
  each fetch retries with exponential backoff, and a second caption path (the
  innertube player endpoint) is tried when the first is throttled. On a
  datacenter IP none of that is sufficient on its own — set
  `YOUTUBE_TRANSCRIPT_PROXY` (a residential proxy) and it stops being an issue.
  Cached transcripts are never affected: the cache is read before any network
  call, so a dive resumes cleanly and only re-fetches what is missing.
- **403 from the API** — quota exhausted (~100 searches/day) or the API isn't
  enabled on the key's project.
