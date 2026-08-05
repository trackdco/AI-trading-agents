# research/ — the centralized research memory (ANGUS 2026-08-04)

Everything the research lane learns gets documented HERE, on this branch, as it
happens: article summaries, key findings, cross-strategy observations, interesting
London structure — one place, actively maintained. "GitHub is just a much messier
version of Obsidian — but one place where it could be actively documenting
discovery." When Pat's Obsidian vault stands up, this folder migrates as-is: every
file is markdown with YAML frontmatter, which is Obsidian's native format, and the
tags follow the vault vocabulary (docs/VAULT-SCHEMA.md §5) so retrieval works the
same in both places.

## Layout

- `articles/` — one file per source read: summary, what's usable, what's noise,
  URL. Nothing gets cited in a thesis that doesn't have a file here.
- `findings/` — cross-cutting discoveries: London-session structure observations,
  correlations between things, base rates, dead ends worth remembering. The
  "interesting things it finds around London" file lives here and grows.
- `candidates/` — one file per strategy candidate: the thesis (trading terms, the
  thesis-gate artifact Angus reads), then — after Angus greenlights — the deep-dive
  research round appended to the same file (everything findable about that
  mechanism: variants, known failure modes, who trades it, what conditions it).
  Testing itself happens on the candidate's own branch (`claude/london-<slug>`);
  the research record stays here.

## File conventions

YAML frontmatter on every file:

```yaml
---
date: 2026-08-04
status: active | thesis-pending | greenlit | killed | reference
tags: [london, order-flow, ...]        # vault vocabulary, VAULT-SCHEMA §5
sources: ["https://..."]               # for articles/ and any cited claim
---
```

Rules carried over from the shop's standing law:
- Every number cited has a source (a file in `articles/`, a repo artifact, or a
  measurement made and named). No vibes.
- Dead ideas stay documented — a killed candidate's file records why, same
  discipline as tombstones.
- Nothing here authorizes anything: research informs theses; Angus's greenlight
  moves a candidate to testing; the validation process governs from there.

## The two-stage research flow (ANGUS 2026-08-04)

1. **Broad sweep** → theses in `candidates/`, status `thesis-pending` → Angus reads
   and picks.
2. **On greenlight** ("okay, let's do this strategy") → the deep-dive round:
   extensive research around that specific mechanism, appended to the candidate's
   file, before and alongside testing on its branch.

## Video sources — `youtube/` and the MCP (2026-08-05)

The 2026-08-04 sweeps record URLs as *leads*, because direct page fetches are
403-blocked at egress (`findings/london-session-clock.md`) — so the claims in
those files come from search snippets, not from the sources themselves. For
video sources that gap is now closed: `tools/youtube-mcp/` fetches the actual
transcript, timestamps every line, and commits it under `youtube/`.

```
youtube/transcripts/<video_id>.txt    transcript, [mm:ss] on every line
youtube/transcripts/<video_id>.json   language, segments, characters, fetch date
youtube/sweeps/<label>.json           what a sweep found: query, params, ranked index
```

**Committed on purpose.** The standing law is that every cited number has a
source; a transcript that only ever existed in a context window can't be
re-checked. With these committed, a thesis quotes a trader at `[video_id @ 12:34]`
and anyone can verify it.

Typical run — Angus arrives with "I found this strategy, here's the video":

```
youtube_research_sweep("<mechanism> nasdaq futures", max_videos=12)
youtube_grep_transcripts(r"stop.?loss|invalidat|risk to reward|session")
youtube_get_transcript("<top hit>", full=True)      # the two that matter, no more
youtube_article_record(title=..., sweep_label=..., session="london",
                       mechanism_families=["order-flow"])   # writes articles/
```

The sweep deliberately never returns transcript text — twelve videos is ~180k
tokens. It returns a ranked index; you grep the corpus and read the two worth
reading. `youtube_article_record` validates `session` and `mechanism_families`
against the VAULT-SCHEMA §5 controlled vocabulary and refuses improvised values.

Where this sits in the flow: it is stage-1 sourcing (and stage-2 deep-dive
sourcing) for one class of source. It authorizes nothing. A candidate still needs
a thesis, Angus's greenlight, and the validation process — the transcripts just
mean the thesis is built on what was actually said.

Setup and failure modes: `tools/youtube-mcp/README.md`. Needs a free
`YOUTUBE_API_KEY` for search; transcripts work without one. Runs on a
workstation — YouTube blocks datacenter IPs, so remote sessions need
`YOUTUBE_TRANSCRIPT_PROXY`.
