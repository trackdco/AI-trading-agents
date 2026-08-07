# FINDINGS INDEX — Phases A-D (2026-08-07)

Four self-contained findings files, written for upload to a strategist
context. Read this index first; each file carries its own context header.

| file | phase | one-line verdict |
|---|---|---|
| FINDINGS-A-validation.md | A (blocking) | Book sign is X-robust (+0.10..+0.15 at every clustering width); the "CIs clear zero both eras" claim was 0.5W-specific and is now qualified. S1's lift survives every convention (+0.05..+0.16, monotone in X). Unconditional re-entry loses −0.22R/attempt — first-of-fight stands; the remembered winning re-entry was sweep-conditioned, not indexed by the table. S1 multiplicity: p_fw 0.017–0.042 under the design's two-stage frame; 0.07–0.15 under a flat ×18/×36 — decisive validation is the forward recorder. |
| FINDINGS-B-dollar-layer.md | B | The size premise inverts: score falls with size at every target (87.8% @ $150 → 37.5% @ $600, T=3) because the $2k trailing DD is fixed while variance scales — the eval is won by survival, not throughput. Two-phase sizing dominates: (150→150) busts 24.4%/yr, (150→300) extracts $36k/yr median. Stop-once-green raises qualifying days and still lowers P(pass) at every X — rejected. Recommended eval config: T=3, $150, ~88% pass, median 21 days. |
| FINDINGS-C-recorder.md | C (time-perishable) | Log-only flow recorder SHIPPED and replay-certified (2 sessions, bit-identical to research — same code imported, parity by construction). Startup gates refuse to log a sign-inverted or stale feed. Delta convention verified empirically (+0.46 corr with price): S1 = flow-confirmation. Side effect: build_cvd_minute.py's delta is likely inverted — audit before next use. Next action: replay-certify on the VPS, then run --live under the watchdog. |
| FINDINGS-D-selection.md | D | closeloc captures ~70% of S1 from pure OHLC (lift +0.078 vs +0.107; S1 keeps +0.057 marginal) — bar-only holdout claim DECLARED and queued (look not spent). S1×exit 2×2: no fight, tails not fatter in S1-kept, adopted exit stands. Both declared increments (magnitude rank, 3-bar delta) died in both halves exactly as Law 7 priced. Two-axis scoring (R/fight + fights/day + qday rate) adopted in the runner. |

Standing after A-D: break arm parked; both holdout looks unspent; A-3 not
built; A-1 spec untouched. The one open validation route on holdout is the
queued closeloc claim (bar-only venue, ±4pp); the decisive S1 validation
is the forward flow journal, which starts accruing the day the recorder
goes live on the VPS.
