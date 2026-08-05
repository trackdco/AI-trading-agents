# research/youtube/

Written by the `youtube-research` MCP server (`tools/youtube-mcp/`).

```
transcripts/<video_id>.txt     transcript with [mm:ss] timestamps on every line
transcripts/<video_id>.json    language, segment count, character count, fetch date
sweeps/<label>.json            what a research sweep found: query, params, ranked index
```

**These are committed on purpose.** They are the provenance for every claim in
`strategies/*/01-research-dossier.md`. A quote with a video ID and timestamp can
be checked; a quote from a transcript that only ever existed in a context window
cannot. Text is small — a few hundred KB per video — and worth the space.

Don't hand-edit anything in here. Re-fetch with `refresh=True` if a transcript
looks wrong.
