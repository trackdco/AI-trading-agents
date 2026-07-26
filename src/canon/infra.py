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
    """Transport to Backblaze B2. `uploader(bucket, key, data: bytes) -> None` is injected —
    the real b2sdk client (`make_b2_uploader`) is the seam; tests pass a fake. `offload()`
    globs a dir; `upload_path()` sends one file (used by SierraArchiver)."""

    def __init__(self, bucket: str, uploader: Callable[[str, str, bytes], None],
                 prefix: str = "sierra"):
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

    def upload_path(self, path: str | Path, key: str | None = None) -> str:
        """Upload a single file. `key` defaults to `<prefix>/<filename>`. Returns the key."""
        p = Path(path)
        key = key or f"{self.prefix}/{p.name}"
        self._upload(self.bucket, key, p.read_bytes())
        return key


class SierraArchiver:
    """Nightly archive of Sierra's own **.scid + .depth** files to B2 — the live-book record.

    Repoints the old MBO offload: the funded feed is **MBP-10** (Aggregated, Lucid Market Depth
    add-on), so there is NO raw MBO to capture (MBOCapture is moot). What must be preserved is
    the depth/intraday files Sierra writes — and Sierra retains historical **.depth only ~30
    days** and they **cannot be re-downloaded once they age out**, so during paper this offload
    is the ONLY durable copy of the live book. It must be running before paper starts.

    Idempotent via an on-disk manifest `{key: size}` — a nightly run only sends new/changed
    files (safe to re-run, and it catches up any un-archived recent .depth day before it ages
    out). `.depth` is per-day + immutable → uploaded once. `.scid` is per-contract and GROWS →
    uploaded under a date-stamped key each night its size changed (the tick record, versioned).
    """

    def __init__(self, data_dir: str | Path, offload: B2Offload, manifest_path: str | Path,
                 root: str = "NQ", suffix: str = "-CME", depth_subdir: str = "MarketDepthData"):
        self.data_dir = Path(data_dir)
        self.offload = offload
        self.manifest_path = Path(manifest_path)
        self.root, self.suffix, self.depth_subdir = root, suffix, depth_subdir

    def _load(self) -> dict:
        if self.manifest_path.exists():
            try:
                return json.loads(self.manifest_path.read_text())
            except Exception:  # noqa: BLE001 — a torn manifest re-archives, never crashes
                return {}
        return {}

    def _save(self, m: dict) -> None:
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        self.manifest_path.write_text(json.dumps(m, sort_keys=True))

    def _candidates(self, now) -> list[tuple[str, Path]]:
        """(key, path) to consider tonight. `.depth`: every day file (catch-up before ageout).
        `.scid`: every front/recently-rolled contract file, date-stamped for a nightly snapshot."""
        out: list[tuple[str, Path]] = []
        depth_dir = self.data_dir / self.depth_subdir
        if depth_dir.exists():
            # match on ROOT only, not root+suffix: Sierra's depth naming varies BY BOX and
            # does not follow the .scid's (Pat's VPS writes NQU26-CME.scid but
            # NQU6.CME.<date>.depth — found 2026-07-26 when a dry-run archived the .scid and
            # silently skipped every .depth, the one file class that cannot be re-downloaded).
            for f in sorted(depth_dir.glob(f"{self.root}*.depth")):
                out.append((f"{self.offload.prefix}/depth/{f.name}", f))     # immutable per day
        day = pd.Timestamp(now).tz_convert("America/New_York").date()
        for f in sorted(self.data_dir.glob(f"{self.root}*{self.suffix}.scid")):
            out.append((f"{self.offload.prefix}/scid/{day}/{f.name}", f))    # nightly snapshot
        return out

    def pending(self, now=None) -> list[tuple[str, Path]]:
        """(key, path) that WOULD be uploaded tonight — candidates whose size differs from the
        manifest. Read-only (no upload, no manifest write) — the dry-run view."""
        now = pd.Timestamp.now(tz="UTC") if now is None else pd.Timestamp(now)
        manifest = self._load()
        return [(k, p) for k, p in self._candidates(now) if manifest.get(k) != p.stat().st_size]

    def archive(self, now=None) -> list[str]:
        """Upload every new/changed candidate; update the manifest; return the keys sent."""
        manifest = self._load()
        sent: list[str] = []
        for key, path in self.pending(now):
            self.offload.upload_path(path, key)
            manifest[key] = path.stat().st_size
            sent.append(key)
        self._save(manifest)
        return sent


def make_b2_uploader(key_id: str | None = None, app_key: str | None = None):
    """Real Backblaze B2 uploader: returns `(bucket, key, data) -> None` backed by b2sdk.
    Credentials from args or B2_KEY_ID / B2_APP_KEY. b2sdk is imported lazily so the offline
    suite never needs it; on the box `pip install b2sdk`. Tests inject a fake instead."""
    import os

    key_id = key_id or os.environ.get("B2_KEY_ID")
    app_key = app_key or os.environ.get("B2_APP_KEY")
    if not key_id or not app_key:
        raise RuntimeError("B2_KEY_ID / B2_APP_KEY not set — cannot build the B2 uploader")
    from b2sdk.v2 import B2Api, InMemoryAccountInfo  # noqa: PLC0415 — lazy, box-only dep

    api = B2Api(InMemoryAccountInfo())
    api.authorize_account("production", key_id, app_key)
    _buckets: dict[str, object] = {}

    def upload(bucket: str, key: str, data: bytes) -> None:
        b = _buckets.get(bucket) or _buckets.setdefault(bucket, api.get_bucket_by_name(bucket))
        b.upload_bytes(data, key)

    return upload


def b2_uploader_seam(*_a, **_k):
    """Deprecated alias — use `make_b2_uploader`. Kept so older wiring imports still resolve."""
    return make_b2_uploader(*_a, **_k)
