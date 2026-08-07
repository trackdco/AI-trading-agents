# Gate report — Job 1 VP excursion census

- **G1 lookahead** — **PASS** — 20 sessions perturbed after 09:30; levels bit-identical
- **G2 DST** — **PASS** — expected-minute histogram {930: 292}; normal-month windows 930 in both regimes: True
- **G3 roll** — **PASS** — 18 sessions sampled vs raw max-volume contract, 0 mismatched; 0 sessions with straddled front symbol (raw pull ends 2026-01-31; later sessions inherit the volume-roll construction of nq_1m_master per docs/CONTRACT-ROLL-DATES.md)
- **G4 determinism** — **PASS** — two consecutive builds over 40 sessions: identical (d124d97dc269)
- **G5 completeness** — **PASS** — status counts {'OK': 290, 'INCOMPLETE': 2}; weekdays in span without a session row: 2 -> ['2025-12-25', '2026-01-01']
- **G6 independence** — **PASS** — excursions/session median 3 max 13; excursions/cluster median 1 max 6; 747 clusters over 1049 excursions

OVERALL: PASS (INCONCLUSIVE blocks like FAIL)
