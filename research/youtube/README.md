# research/youtube/ — video source cache

Written by `tools/youtube-mcp/`. See `research/README.md` § "Video sources" for
where this sits in the research flow.

```
transcripts/<video_id>.txt     transcript, [mm:ss] timestamp on every line
transcripts/<video_id>.json    language, segment count, characters, fetch date
sweeps/<label>.json            a sweep's query, parameters, and ranked index
```

**Committed on purpose.** These are the provenance for every video-sourced claim
in `research/articles/`. A quote with a video ID and a timestamp can be checked;
a quote from a transcript that only ever existed in a context window cannot.
Text is small — a few hundred KB per video.

Don't hand-edit. Re-fetch with `refresh=True` if a transcript looks wrong, and
note in the article file why it was re-fetched.

Auto-generated captions are common and imperfect: they mangle tickers ("NQ" →
"NASDAQ", "MNQ" → "M and Q") and drop punctuation. When a quoted rule hangs on
an exact number, check it against the video before citing it.
