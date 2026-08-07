"""The Desk receiver (Phase 5) — where Hermes's verdict meets the Vault's guards.

Hermes (third-party, per docs/desk-skills/hermes-coordinator.md) writes one verdict
JSON file per candidate into a watched directory. This receiver:

    1. reads each new file and runs it through src.desk.verdict.validate_verdict —
       the Python trust boundary; a schema violation or arithmetic mismatch is
       rejected here, never trusted downstream (belt matches the champion path's
       "no LLM arithmetic is load-bearing" rule).
    2. for a validated trade=true verdict, checks it against the SAME RiskGuard the
       champion bot uses (kill switch, daily loss limit, max trades) BEFORE treating
       it as approved — the guards sit in front of every trade regardless of which
       strategy proposed it.
    3. journals every outcome (rejected / vetoed / risk-gated / approved) via the
       SAME LiveJournal used by the champion bot, so the audit trail is unified.
    4. hands an approved verdict to `on_approved`, if one was wired — this receiver
       stops at "approved, guards cleared"; it does NOT execute, fill, or manage a
       position to exit. That is a separate piece not yet built (see the note at the
       bottom of docs/desk-skills/hermes-coordinator.md).

FILE-DROP CONTRACT (read this before wiring Hermes's output to this directory):
whatever writes verdict files into the watched directory MUST write to a temp path
and atomically rename/move into place — never write the final filename in place a
byte at a time. This receiver also refuses to touch a file until it has been stable
(unmodified) for `min_age_s` seconds, as a second line of defense against reading a
half-written file, but atomic rename is the correct fix and should be preferred.

Processed files are moved into `<watch_dir>/processed/` (or `/rejected/` on a
validation failure) immediately after journaling — this both prevents reprocessing
on restart (no separate state file needed; the move IS the durable marker) and
keeps every input file as forensic evidence.

    receiver = DeskReceiver(watch_dir, sizing_cfg, journal, guard)
    for outcome in receiver.poll_once():
        ...
"""

from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass, field
from datetime import time as dtime
from pathlib import Path
from typing import Callable

import pandas as pd

from src.desk.verdict import DeskVerdict, SizingConfig, validate_verdict
from src.engine.data import _session_date

_SESSION_BOUNDARY = dtime(18, 0)
DEFAULT_MIN_AGE_S = 2.0


def _trade_date(trigger_ts: str) -> str:
    """Session-date of a trigger timestamp, same 18:00 ET boundary the rest of the
    live stack uses (src/live/vault.py, src/live/vector.py) — so a Desk trade's
    risk-day lines up with the champion's."""
    return str(_session_date(pd.Series([pd.Timestamp(trigger_ts)]), _SESSION_BOUNDARY)
               .iloc[0])


@dataclass
class Outcome:
    file: str
    status: str          # rejected | vetoed | risk_gated | approved
    reason: str | None = None
    verdict: DeskVerdict | None = None


@dataclass
class DeskReceiver:
    watch_dir: Path
    sizing_cfg: SizingConfig
    journal: object                          # src.live.journal.LiveJournal
    guard: object                            # src.live.risk.RiskGuard
    on_approved: Callable[[DeskVerdict], None] | None = None
    min_age_s: float = DEFAULT_MIN_AGE_S
    failures: int = field(default=0, init=False)

    def __post_init__(self):
        self.watch_dir = Path(self.watch_dir)
        self._processed_dir = self.watch_dir / "processed"
        self._rejected_dir = self.watch_dir / "rejected"

    def poll_once(self) -> list[Outcome]:
        """Process every stable file currently sitting in the watch dir. Safe to call
        repeatedly (e.g. in a loop) — already-handled files have been moved out."""
        if not self.watch_dir.exists():
            return []
        now = time.time()
        out: list[Outcome] = []
        for path in sorted(self.watch_dir.glob("*.json")):
            try:
                if now - path.stat().st_mtime < self.min_age_s:
                    continue                 # possibly still being written; try next poll
            except FileNotFoundError:
                continue                     # raced with something else removing it
            out.append(self._process(path))
        return out

    # ---- internals ------------------------------------------------------------
    def _process(self, path: Path) -> Outcome:
        try:
            raw = path.read_text()
        except Exception as e:                # a bad file must never kill the receiver
            self.failures += 1
            print(f"[desk-receiver] read failed for {path.name}: "
                  f"{type(e).__name__}: {e}", file=sys.stderr)
            self._move(path, self._rejected_dir)
            return Outcome(file=path.name, status="rejected", reason="read_error")

        result = validate_verdict(raw, self.sizing_cfg)
        if not result.ok:
            self._note(f"desk_verdict_rejected file={path.name} "
                      f"reason={result.veto_reason}")
            self._move(path, self._rejected_dir)
            return Outcome(file=path.name, status="rejected", reason=result.veto_reason)

        v = result.verdict
        if not v.trade:
            self._note(f"desk_verdict_veto trigger_ts={v.trigger_ts} "
                      f"pattern={v.pattern} direction={v.direction} "
                      f"gates={v.gates} thesis={v.thesis}")
            self._move(path, self._processed_dir)
            return Outcome(file=path.name, status="vetoed", verdict=v)

        date = _trade_date(v.trigger_ts)
        gate = self.guard.gate(date)
        if gate is not None:
            self._note(f"desk_trade_risk_gated trigger_ts={v.trigger_ts} "
                      f"reason={gate['risk_reason']}")
            self._move(path, self._processed_dir)
            return Outcome(file=path.name, status="risk_gated",
                          reason=gate["risk_reason"], verdict=v)

        self._note(f"desk_trade_approved trigger_ts={v.trigger_ts} "
                  f"direction={v.direction} entry={v.entry} stop={v.stop} "
                  f"target={v.target} size={v.size} grade={v.grade}")
        if self.on_approved is not None:
            try:
                self.on_approved(v)
            except Exception as e:            # a downstream hook must never kill polling
                self.failures += 1
                print(f"[desk-receiver] on_approved failed: {type(e).__name__}: {e}",
                      file=sys.stderr)
        self._move(path, self._processed_dir)
        return Outcome(file=path.name, status="approved", verdict=v)

    def _note(self, text: str) -> None:
        try:
            self.journal.note(text)
        except Exception as e:                # journaling failure must never block gating
            self.failures += 1
            print(f"[desk-receiver] journal write failed: {type(e).__name__}: {e}",
                  file=sys.stderr)

    def _move(self, path: Path, dest_dir: Path) -> None:
        try:
            dest_dir.mkdir(parents=True, exist_ok=True)
            # os.replace, not Path.rename: on Windows os.rename raises if the target already
            # exists (a re-processed same-named drop), while os.replace overwrites atomically
            # on both POSIX and Windows.
            os.replace(path, dest_dir / path.name)
        except Exception as e:
            self.failures += 1
            print(f"[desk-receiver] failed to move {path.name}: "
                  f"{type(e).__name__}: {e}", file=sys.stderr)
