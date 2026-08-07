# Caption pull — status and how to finish it

## Where things live

| Path | In git | What |
|---|---|---|
| `manifest.json` | yes | `video_id -> status` for all 117 videos. Source of truth for what is held |
| `transcripts/<id>.txt` | yes | **Timestamped transcript — the primary artefact.** Feed this to extraction |
| `transcripts/<id>.plain.txt` | no | Flowing prose, derivable from the above |
| `captions/<id>.en.vtt` | no | Raw VTT. Bulky; the timestamped transcript supersedes it |
| `tools/` | yes | Puller, manifest builder, converter |

`captions/` and the prose variants are gitignored. **They live only in the session
container, which is ephemeral** — the committed `transcripts/*.txt` are the durable copy.

## Status

The pull is blocked by two stacked mechanisms, diagnosed rather than inferred:

```
HTTP 429  ->  redirect to google.com/sorry/index      IP-level penalty box
ERROR: Sign in to confirm you're not a bot            account-level bot check
```

`youtube.com` root returns 200 while watch pages return 429, so this is Google's
reputation system gating video-metadata endpoints for this address range, not a
network fault.

**The block is intermittent, not absolute** — roughly one request in eight is served.
That is why the puller is resumable and capped rather than aggressive: repeated small,
slow runs make progress where a single sweep does not.

**Slowing down alone will not clear it.** A completely cold, isolated request after a
long idle period failed identically to the hundredth request in a sweep. The binding
constraint is IP reputation, not velocity.

## Finishing the pull

From a home connection, with a browser logged in to YouTube:

```bash
cd research/star-trading
./tools/pull_channel.sh --cookies-from-browser chrome --limit 20
```

Cookies are the part that matters — the diagnosis is a bot check, and no amount of
additional patience substitutes for authentication. Re-run until the manifest shows
the priority set complete; each run resumes where the last stopped.

```bash
./tools/pull_channel.sh --status                      # what is held
./tools/pull_channel.sh --retry-failed --limit 10     # re-queue failures
./tools/pull_channel.sh --all --limit 20              # beyond the priority set
```

## Priority set

19 ranked videos plus the one held before the block. Ordering rationale:

- **Tier A** (#1) — the break-even video. The only known source for how a break-even
  trade is counted in a win rate; a "95% win rate" that drops break-evens from the
  denominator is a different claim from one that counts them as losses.
- **Tier B** (#2–#11) — the longest videos. Masterclasses state rules explicitly;
  short videos demonstrate them and leave the rule implicit.
- **Tier C** (#12–#19) — titles carrying a backtest claim or a win-rate percentage.
  These hold the samples the contradiction ledger is built from.

## Tooling notes

`pull_captions.py` commits the manifest atomically after every single video, so a
killed run loses at most the one in flight. It stops after 3 consecutive failures
rather than hammering, backs off exponentially (capped at 5 minutes), and jitters the
sleep so requests do not form a fixed cadence. Manual subtitle tracks are preferred
over auto-generated ones where both exist; the discrimination is done by inspecting
the VTT for inline timing tags rather than by making a second request.

`vtt_to_text.py` keeps timestamps. The extraction schema requires a timestamp on every
quoted rule, and the first conversion pass stripped them and had to be redone.
