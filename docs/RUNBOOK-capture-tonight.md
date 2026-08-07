# RUNBOOK — capture night 2026-07-31 → armed Monday

Pat's operational sequence, agreed 2026-07-31: **no arm tonight.** Tonight closes R10b
(depth parity on a real capture) and records the phase-2 fixtures; the weekend closes R13
(runner wiring certified) and builds R15 (agent layer per handover §7); Monday runs the
two-party arm. Every step here is a gate — a red one stops the sequence, per
`docs/ARMING-REFERENCE.md`.

---

## 0. FIRST — before the session: check the box for historical `.depth` files

Sierra writes one `.depth` file per day it runs and keeps them per
*Global Settings → Data/Trade Service Settings → Maximum Historical Market Depth Days*.
The archive has NY-window coverage through **2026-07-08**. If the box still holds a
`.depth` file for ANY archive-covered day, R10b can be closed **today, before the
session**, on real box data — no waiting on tonight.

On the VPS, look in the Sierra data folder (default `C:\SierraChart\Data\`) for:

    NQU6.CME.2026-07-08.depth        # or 07-07, 07-06, 07-03, 07-02, 07-01, 06-30 …
    NQM6.CME.2026-06-*.depth         # June contract days are fine too if pre-roll

If one exists (pick the NEWEST archive-covered day), on the box at the current branch tip:

    python -m scripts.depth_capture --scid NQU6.CME.scid \
        --depth NQU6.CME.<DAY>.depth --day <DAY> --out capture_<DAY>.jsonl
    python -m scripts.depth_parity --day <DAY> --events capture_<DAY>.jsonl --book depth

PASS = 100% gate agreement (W / D / WALLSZ / wall-quality cut), wall distances within a
tick. That is R10b, closed on evidence. Commit the parity output (not the raw capture) and
note the day used. If it FAILS → stop; the feed pipe is wrong; nothing arms until the
diff is understood. Either way, still do §1–§3 tonight.

## 1. Tonight, during the session (07:45–11:00 ET)

1. Confirm Sierra market-depth recording is ON for NQ (it is, if `.depth` files exist).
2. Run the disarmed shadow entrypoint (`scripts/ny_run.py`, this branch):

       python -m scripts.ny_run                  # reads config/live.yaml

   Config additions over canon_run's keys: `ny.profile` (lucid), and the budget buffer —
   set `ny.buffer` (dollars of room above the trailing line) or `account.trailing_line`;
   the loop refuses to guess a risk input. It is structurally orderless (`_NoBroker`):
   it scores and journals every verdict/action the rebuilt canon would have taken
   (`<journal_dir>/ny/ny_verdicts.jsonl`, `ny_actions.jsonl`, `decisions.jsonl`) and
   records the phase-2 fixture streams (minute tape + MBP-10 snapshots,
   `fixtures.jsonl`). Zero orders possible.
3. Touch nothing during the window. The deliverables are the journals and Sierra's own
   `.depth` file for today.

## 2. Tonight, after the close

1. Capture today's session:

       python -m scripts.depth_capture --scid NQU6.CME.scid \
           --depth NQU6.CME.2026-07-31.depth --day 2026-07-31 --out capture_2026-07-31.jsonl

2. Archive side for today: pull today's NQ MBP-10 from Databento when it posts
   (same evening/next morning), then

       python scripts/condense_depth.py <raw>.dbn.zst --outdir depth_out
       # produces nq_depth_2026-07-31_ny.csv → place in data/reference/depth_2026/

3. Parity on today (skip if §0 already closed R10b — still worth running as a second
   data point):

       python -m scripts.depth_parity --day 2026-07-31 --events capture_2026-07-31.jsonl --book depth

## 3. Weekend

- **R13**: certify the runner wiring on the box — shadow journals from tonight diffed
  against expectations (no trade-count halt, no distance cancels, per-session expiry,
  sizes matching `check_sizing`, rows J/K/L semantics visible in the action log).
- **R15 build**: port the agent layer per handover §7 against tonight's recorded
  fixtures; dry-run day + agent kill-test per the certification criteria there.
- **R14**: `pytest tests/test_canon_scorer_ny.py -q` on the box's arming checkout.

## 4. Monday — the two-party arm (unchanged, no shortcuts)

1. Pat's written confirmation, per PROMOTION-GATE, against the certified commit.
2. Angus commits `config/arming.yaml` (token SHA-256, certified SHA, account).
3. On the box: `canon_run --arm`, present the phrase. `verify_for_arming` enforces
   HEAD == certified commit. Every check fails closed.

Phasing per ANGUS 2026-07-31 (final): R15a mech-only vs R15b agent-on is decided by
which certification is actually green by Monday — if the agent dry-run isn't certified,
mech-only arms first and the agent switch-on re-runs the two-party step later. Nothing
in this runbook changes if phase 2 slips.
