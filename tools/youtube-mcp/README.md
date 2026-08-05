# YouTube Research MCP

Turns "someone on YouTube explained a strategy" into an on-disk, auditable
research corpus that the validation pipeline can consume.

## Install (one time, on the machine that runs Claude Code)

```bash
cd tools/youtube-mcp
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python -e .
```

`uv` not installed? `curl -LsSf https://astral.sh/uv/install.sh | sh`, or use
plain `python3.11 -m venv .venv && .venv/bin/pip install -e .`.

## Configure

The server is registered for this repo in `.mcp.json` at the repo root, so
Claude Code picks it up automatically when started from the project directory.
It will prompt for approval the first time.

Add to your `.env` at the repo root:

```
YOUTUBE_API_KEY=AIza...
```

Get the key: [Google Cloud Console](https://console.cloud.google.com) → create a
project → enable **YouTube Data API v3** → Credentials → Create API key.
Free tier is 10,000 quota units/day. A search costs 100 units, so roughly
**100 searches per day** — plenty. Restrict the key to the YouTube Data API.

**Transcripts do not need the key.** Without a key you lose search and
metadata; `youtube_get_transcript` and `youtube_grep_transcripts` still work if
you paste URLs directly.

Optional:

| Var | Purpose |
|---|---|
| `YOUTUBE_MCP_CACHE_DIR` | Where transcripts land. Default `research/youtube/`. |
| `YOUTUBE_TRANSCRIPT_PROXY` | HTTP proxy for transcript fetches. YouTube blocks most datacenter IPs — needed only if this runs on a VPS rather than a laptop. |

## Verify

```bash
.venv/bin/python -c "import server; print([t for t in server.server._tool_manager.list_tools()])" 2>/dev/null \
  || .venv/bin/python server.py < /dev/null
```

Then in Claude Code: `/mcp` should list `youtube-research` as connected.

## Tools

| Tool | Needs key | What it's for |
|---|---|---|
| `youtube_research_sweep` | yes | **Start here.** Search a strategy, cache every transcript, return a ranked index — not the text. |
| `youtube_grep_transcripts` | no | Regex across cached transcripts with timestamps. How you extract stated rules from 12 videos without loading 12 videos. |
| `youtube_get_transcript` | no | One transcript. Excerpt + cache path by default; `full=True` when you mean it. |
| `youtube_search` | yes | Plain search, no transcripts. |
| `youtube_video_details` | yes | Duration/views/likes/description — credibility triage. |
| `youtube_find_channel` | yes | Find a trusted trader's channel ID, then search within it only. |
| `youtube_list_transcript_languages` | no | Diagnostic when a transcript fetch fails. |
| `youtube_cache_status` | no | What's already pulled — the audit trail. |
| `youtube_start_dossier` | no | Scaffold `strategies/<slug>/00-source.md` pre-filled with the sweep's sources. |

## The context discipline that makes this usable

A 60-minute trading video is ~60,000 characters ≈ 15,000 tokens. Twelve of them
is ~180,000 tokens — a whole context window spent before any thinking happens.

So the sweep **never returns transcript text**. It returns an index with a
`rule_keyword_hits` score per video (how often the speaker says things like
"entry", "stop loss", "invalidation", "session", "filter"). The workflow is:

1. `youtube_research_sweep("<strategy name> nasdaq futures")` — cache 12 videos.
2. `youtube_grep_transcripts(r"stop.?loss|invalidat|risk to reward")` — see
   exactly where each speaker states the rules, with timestamps.
3. Read the full transcript of the two or three highest-scoring videos only.

## Known failure modes

- **"Transcripts are disabled"** — the uploader turned captions off. Nothing to
  do; the sweep reports it under `failures` and moves on.
- **`RequestBlocked` / IP ban** — YouTube blocks datacenter IPs. Fine on a
  laptop, breaks on a VPS. Set `YOUTUBE_TRANSCRIPT_PROXY` if you need it there.
- **403 from the API** — quota exhausted (100 searches/day) or the API isn't
  enabled on the key's project.
