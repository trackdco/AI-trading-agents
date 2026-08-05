# strategies/

One folder per candidate strategy. The folder *is* the audit trail — if a claim
isn't in here with a source, it didn't happen.

```
strategies/
├── README.md              this file
├── BOOK.md                strategies that passed. What the agents may trade.
├── GRAVEYARD.md           strategies that failed. Kept so we don't retest them.
├── _TEMPLATE/             copy this to start
└── <strategy-slug>/
    ├── 00-source.md            where it came from, who said it, why we trust them
    ├── 01-research-dossier.md  what the sources actually claim, quoted
    ├── 02-hypothesis.md        the mechanism, in plain English, + what would falsify it
    ├── 03-mechanical-spec.md   rules precise enough to code blind
    ├── 04-refinement-ledger.md every variant tested, including failures
    ├── 05-verdict.md           scored against the gate. ADOPT / PARK / REJECT.
    └── output/                 generated: trigger tables, slice reports, equity curves
```

## Starting one

```
/youtube_start_dossier "London Open Sweep"     # creates the folder + 00-source.md
cp strategies/_TEMPLATE/*.md strategies/london-open-sweep/   # the rest
```

Then follow `context/strategy-research-protocol.md` from Stage 1.

## Rules

1. **Numbered order is the order.** Don't write `03-mechanical-spec.md` before
   `02-hypothesis.md` exists. The sequence is the discipline — specifying rules
   before articulating why they should work is how you end up with a
   well-documented coincidence.
2. **Failures stay.** A rejected strategy keeps its folder. The reason it failed
   is worth more six months from now than the fact that it did.
3. **Every artifact opens with a Plain English block.** If Angus can't audit it,
   it isn't finished.
4. **`output/` is gitignored** — regenerate it from the documented command.
   Everything else here is committed.
