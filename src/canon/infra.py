"""Infra seams (LIVE-STACK cross-cutting + LAUNCH-RUNBOOK storage ruling).

Deterministic, testable pieces of the live plumbing. External transports (Backblaze B2, the
DTC feed) are INJECTED so tests run offline; the real clients drop into the marked seams.

  StartupParityGate  : boot-time reconciliation gate — read-only until it is green.
  Heartbeat          : desk-liveness watchdog — miss => fail-closed callback (trip KILL).
  SpineJournalSink   : append each spine event (halt/clamp/reject) to a JSONL on disk.
  MBOCapture         : rolling raw-MBO buffer; dump the window around each trade.
  B2Offload          : nightly offload of the capture dir via an injected uploader.
"""
from __future__ import annotations

import json
from collections import deque
from collections.abc import Callable
from pathlib import Path

import pandas as pd


# --------------------------------------------------------------------------- startup parity
class StartupParityGate:
    """Runs the reconciliation/parity on boot. `may_trade` is False until `run()` is green —
    the desk runs READ-ONLY until a human-cleared green (LAUNCH-RUNBOOK.md:98 GATE)."""

    def __init__(self, checker: Callable[[], bool]):
        self._checker = checker
        self.green: bool | None = None

    def run(self) -> bool:
        try:
            self.green = bool(self._checker())
        except Exception:  # noqa: BLE001 — a failing gate is NOT green (fail-closed)
            self.green = False
        return self.green

    @property
    def may_trade(self) -> bool:
        return self.green is True


# --------------------------------------------------------------------------- heartbeat
class Heartbeat:
    """Desk-liveness watchdog. `beat(now)` each loop; `check(now)` fires `on_lost` ONCE when
    no beat has arrived within `miss_after_s` — the 'box froze mid-position' case."""

    def __init__(self, miss_after_s: float, on_lost: Callable[[pd.Timestamp], None]):
        self.miss_after = pd.Timedelta(seconds=miss_after_s)
        self._on_lost = on_lost
        self._last: pd.Timestamp | None = None
        self.lost = False

    def beat(self, now) -> None:
        self._last = pd.Timestamp(now)
        self.lost = False

    def check(self, now) -> bool:
        if self._last is None:
            return True
        alive = pd.Timestamp(now) - self._last <= self.miss_after
        if not alive and not self.lost:
            self.lost = True
            self._on_lost(self._last)
        return alive


# --------------------------------------------------------------------------- spine journal
class SpineJournalSink:
    """Append-only JSONL sink for spine events. Wire as SpineExecutor(journal=sink). Fail-soft:
    a write error can never raise into the trade loop."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.failures = 0

    def __call__(self, event: dict) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a") as f:
                f.write(json.dumps(event) + "\n")
        except Exception:  # noqa: BLE001 — journaling never breaks trading
            self.failures += 1

    def events(self) -> list[dict]:
        if not self.path.exists():
            return []
        return [json.loads(x) for x in self.path.read_text().splitlines() if x.strip()]


# --------------------------------------------------------------------------- MBO capture
class MBOCapture:
    """Rolling buffer of raw MBO events; dump the window around each trade for the research
    substrate (LIVE-STACK.md:151-157). Keeps only the last `window_s` of events in memory."""

    def __init__(self, window_s: float = 120.0):
        self.window = pd.Timedelta(seconds=window_s)
        self.buf: deque[tuple[pd.Timestamp, dict]] = deque()

    def on_event(self, ts, ev: dict) -> None:
        ts = pd.Timestamp(ts)
        self.buf.append((ts, ev))
        cutoff = ts - self.window
        while self.buf and self.buf[0][0] < cutoff:
            self.buf.popleft()

    def window_around(self, trade_ts) -> list[dict]:
        """Events within +/- window of the trade (forward side needs the buffer to have run
        `window_s` past the trade before dumping — a live scheduling detail)."""
        t = pd.Timestamp(trade_ts)
        lo, hi = t - self.window, t + self.window
        return [ev for ts, ev in self.buf if lo <= ts <= hi]

    def dump_around(self, trade_ts, out_path: str | Path) -> int:
        rows = self.window_around(trade_ts)
        p = Path(out_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("\n".join(json.dumps(r) for r in rows))
        return len(rows)


# --------------------------------------------------------------------------- B2 offload
class B2Offload:
    """Nightly offload of the MBO-capture dir to Backblaze B2 (LAUNCH-RUNBOOK.md:21,92).
    `uploader(bucket, key, data: bytes) -> None` is injected — the real b2sdk client is the
    seam; tests pass a fake. Idempotent-ish: returns the keys uploaded."""

    def __init__(self, bucket: str, uploader: Callable[[str, str, bytes], None],
                 prefix: str = "mbo"):
        self.bucket = bucket
        self._upload = uploader
        self.prefix = prefix

    def offload(self, capture_dir: str | Path, glob: str = "*.jsonl") -> list[str]:
        d = Path(capture_dir)
        keys = []
        for f in sorted(d.glob(glob)):
            key = f"{self.prefix}/{f.name}"
            self._upload(self.bucket, key, f.read_bytes())
            keys.append(key)
        return keys


def b2_uploader_seam(*_a, **_k):
    """<<REAL B2 UPLOADER>> — wraps b2sdk (B2Api authorize + bucket.upload_bytes). Needs
    B2_KEY_ID / B2_APP_KEY in the environment. NOT built (no creds offline)."""
    raise NotImplementedError("real Backblaze B2 uploader not built — inject one")
