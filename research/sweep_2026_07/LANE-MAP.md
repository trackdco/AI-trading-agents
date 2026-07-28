# Lane-to-directory map — sweep_2026_07

Declared before any agent was spawned. One agent per lane; each wrote ONLY to its own
subdirectory. No write access to src/, scripts/, config/, output/ artifacts, or any
canon/arming path. Journal is append-only, advisory, no write access to any bot/config/matrix.

| Lane | Directory | Phase |
|---|---|---|
| validity: lookahead audit (0c) | lane_validity/ | 0 |
| validity: contract & clock (0d) | lane_clock/ | 0 |
| excursion (1a) | lane_excursion/ | 1 |
| fast losers (1b) | lane_fastlosers/ | 1 |
| time-of-day (1c) | lane_timeofday/ | 1 |
| bias-of-day (1d) | lane_biasofday/ | 1 |
| cost & sizing (§4) | lane_costsizing/ | 1 |
| PHASE 2 (approved 2026-07-28 + 6 amendments) | phase2/ | 2 |

NOTE 2026-07-28: the container hosting this session was reclaimed TWICE mid-study; the lane
subdirectories' raw artefacts were lost both times (nothing was committed, per Brake's
instruction). The three deliverables (dashboard, 00_data_validity.md, 01_hypotheses.md) were
delivered to Brake in-chat before each loss. Phase 0/1 findings are preserved in the workflow
journal and in the delivered files; Phase 2 was re-run from regenerated inputs
(baseline_book_clean.parquet reproduces to the cent from the committed script).
