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
