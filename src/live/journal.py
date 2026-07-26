"""Live journal (Phase 4 Stage 6) — every decision and trade, append-only, auditable.

Two files, same blob discipline as the replay artifacts:

  journal.jsonl   — one frozen-schema JournalRecord (src/desk/journal.py) per COMPLETED
                    trade, lifted from the engine's FULL TradeRecord via
                    `from_trade_record` — not the trimmed alert TradeEvent — so a live
                    day is row-for-row comparable with the backtest trade log.
  decisions.jsonl — the WHY trail: session rolls (which book the policy picked, or a
                    stand-down), risk halts, free-form notes. One JSON object per line,
                    so a crash mid-write can cost at most the final line.

Restart-safe: on construction the journal re-reads its own files and re-arms trade AND
session-pick dedup, so a crash-looping bot never double-writes (same discipline as
PaperBroker). Reads are TOLERANT (Stage-6 review F1): a torn final line — exactly what
a crash mid-write leaves — is skipped and counted, never a startup crash; a row that
fails schema validation (drift) is likewise skipped, counted, and left on disk for
forensics. Every write is fail-soft — a full disk or bad permission can never raise
into the trading loop (the Vault isolates sinks too; belt and braces).

Wiring (alongside the Stage 3-5 sinks; `fanout` from src.live.risk combines halt hooks):
    journal = LiveJournal()
    vault.add_record_sink(journal.on_record)        # full trade records
    policy  = journal.wrap_policy(champion_policy(vector))   # logs daily book picks
    guard   = RiskGuard(..., on_halt=fanout(tg.on_halt, journal.on_halt))
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Callable

from src.desk.journal import JournalRecord, from_trade_record

DEFAULT_DIR = Path("output/live")


def _trade_key(trade_date, fill_ts) -> tuple[str, str]:
    return (str(trade_date), str(fill_ts))


def cfg_hash(cfg) -> str:
    """12-hex reproducibility stamp of an engine config (pydantic JSON is stable).
    Computed fresh on every call — an id()-keyed cache was PROVEN unsound in the
    Stage-6 review (F2): CPython reuses freed addresses, which stamped a stale hash."""
    return hashlib.sha256(cfg.model_dump_json().encode()).hexdigest()[:12]


class LiveJournal:
    def __init__(self, dir_path: Path = DEFAULT_DIR):
        self.dir = Path(dir_path)
        self.journal_path = self.dir / "journal.jsonl"
        self.decisions_path = self.dir / "decisions.jsonl"
        self.failures = 0
        self.corrupt_journal_lines = 0                 # updated on each trades() read
        self.corrupt_decision_lines = 0                # updated on each decisions() read
        self._logged: set[tuple[str, str]] = set()     # trade dedup, re-armed from disk
        for rec in self.trades():
            self._logged.add(_trade_key(rec.trade_date, rec.fill_ts))
        self._sessions_logged: set[tuple] = set()      # (date, book) dedup, re-armed too
        for d in self.decisions():
            if d.get("type") == "session":
                self._sessions_logged.add((d.get("date"), d.get("book")))

    # ---- sinks --------------------------------------------------------------
    def on_record(self, tr, book: str, cfg, ambient: dict | None = None) -> None:
        """Vault record sink: journal one completed trade with full context. `ambient` is
        the CANON ruling's per-trade instrumentation (sweep_state / spread_at_fill /
        news_calendar_state, src/live/ambient.py) — optional and merged in only when the
        Vault is wired with an ambient_fn, so a 3-arg caller journals exactly as before."""
        key = _trade_key(tr.trade_date, tr.fill_ts)
        if key in self._logged:
            return
        ctx = {"playbook": book}
        if ambient:
            ctx.update({k: v for k, v in ambient.items() if v is not None})
        rec = from_trade_record(tr, config_hash=cfg_hash(cfg), **ctx)
        if self._append(self.journal_path, rec.model_dump_json()):
            self._logged.add(key)

    def on_guard_trip(self, tr, book: str, cfg, ambient: dict | None, res) -> None:
        """Order-time spread-guard sink: journal WHY an order was not placed. This is a
        decision-trail entry, never a trade row — a tripped order is not a taken trade, so
        it must not enter journal.jsonl (that would break the Stage-7 reconcile)."""
        amb = ambient or {}
        self._decision({
            "type": "guard_trip",
            "date": str(getattr(tr, "trade_date", "")),
            "fill_ts": str(getattr(tr, "fill_ts", "")),
            "direction": getattr(tr, "direction", None),
            "book": book,
            "reason": getattr(res, "reason", None),
            "spread_at_fill": getattr(res, "observed", None),
            "spread_baseline": getattr(res, "baseline", None),
            "spread_threshold": getattr(res, "threshold", None),
            "sweep_state": amb.get("sweep_state"),
            "news_calendar_state": amb.get("news_calendar_state"),
        })

    def on_halt(self, date: str, reason: str) -> None:
        self._decision({"type": "halt", "date": date, "reason": reason})

    def on_roll(self, event: dict) -> None:
        """Journal a contract-roll event (live twin of engine.data.tag_rolls). Gives the gate a
        roll-day date-set to partition trades by (as diagnostics.py does) and the §E clock-reset
        key. `event`: {date, from, to, bar_ts}."""
        self._decision({"type": "roll", **event})

    def note(self, text: str) -> None:
        self._decision({"type": "note", "text": text})

    def wrap_policy(self, policy: Callable) -> Callable:
        """Wrap a session policy so every daily pick is journaled: which book ran the
        day, or that the policy sat it out. Transparent — returns the pick unchanged.
        A (date, book) pair is logged ONCE across restarts (review F3): a restarted
        Vault re-rolls its warmup sessions, and without dedup every restart would
        re-append the same picks and make the audit trail read like re-decisions."""
        def logged(date: str):
            picked = policy(date)
            skey = (date, None if picked is None else picked[0])
            if skey not in self._sessions_logged:
                if self._decision({"type": "session", "date": skey[0], "book": skey[1]}):
                    self._sessions_logged.add(skey)
            return picked
        return logged

    # ---- reading / reconciliation ------------------------------------------
    def trades(self) -> list[JournalRecord]:
        """All journaled trades. Tolerant read (review F1): a torn or drifted line is
        skipped and counted in `corrupt_journal_lines`, never raised — a crash
        mid-write must not become a crash on restart."""
        rows, bad = [], 0
        for line in self._lines(self.journal_path):
            try:
                rows.append(JournalRecord(**json.loads(line)))
            except Exception as e:
                bad += 1
                print(f"[journal] skipping bad journal line: {type(e).__name__}",
                      file=sys.stderr)
        self.corrupt_journal_lines = bad
        return rows

    def decisions(self) -> list[dict]:
        """The decision trail. Same tolerant-read contract as trades()."""
        rows, bad = [], 0
        for line in self._lines(self.decisions_path):
            try:
                rows.append(json.loads(line))
            except Exception as e:
                bad += 1
                print(f"[journal] skipping bad decisions line: {type(e).__name__}",
                      file=sys.stderr)
        self.corrupt_decision_lines = bad
        return rows

    def reconcile(self, expected) -> dict:
        """Row-for-row diff vs a batch backtest trade list (engine TradeRecords).
        Keys match the Stage-7 parity gate: date, fill, direction, points, dollars."""
        def k(td, fts, direction, points, dollars):
            return (str(td), str(fts), direction,
                    round(float(points), 2), round(float(dollars)))
        ours = [k(r.trade_date, r.fill_ts, r.direction, r.points, r.dollars)
                for r in self.trades()]
        theirs = [k(t.trade_date, t.fill_ts, t.direction, t.points, t.dollars)
                  for t in expected]
        return {"match": ours == theirs,
                "missing": [t for t in theirs if t not in ours],
                "unexpected": [o for o in ours if o not in theirs]}

    # ---- internals ----------------------------------------------------------
    @staticmethod
    def _lines(path: Path):
        if not path.exists():
            return []
        return [line for line in path.read_text().splitlines() if line.strip()]

    def _decision(self, row: dict) -> bool:
        return self._append(self.decisions_path,
                            json.dumps({"ts": datetime.now().astimezone().isoformat(),
                                        **row}))

    def _append(self, path: Path, line: str) -> bool:
        """Fail-soft append: a full disk / bad permission never raises into the loop."""
        try:
            self.dir.mkdir(parents=True, exist_ok=True)
            with path.open("a") as f:
                f.write(line + "\n")
            return True
        except Exception as e:
            self.failures += 1
            print(f"[journal] write failed ({path.name}): {type(e).__name__}: {e}",
                  file=sys.stderr)
            return False
