"""Live journal (Phase 4 Stage 6) — every decision and trade, append-only, auditable.

Two files, same blob discipline as the replay artifacts:

  journal.jsonl   — one frozen-schema JournalRecord (src/desk/journal.py) per COMPLETED
                    trade, lifted from the engine's FULL TradeRecord via
                    `from_trade_record` — not the trimmed alert TradeEvent — so a live
                    day is row-for-row comparable with the backtest trade log.
  decisions.jsonl — the WHY trail: session rolls (which book the policy picked, or a
                    stand-down), risk halts, free-form notes. One JSON object per line,
                    so a crash mid-write can cost at most the final line.

Restart-safe: on construction the journal re-reads its own file and re-arms trade
dedup, so a crash-looping bot never double-writes a trade (same discipline as
PaperBroker). Every write is fail-soft — a full disk or bad permission can never raise
into the trading loop (the Vault isolates sinks too; belt and braces).

Wiring (alongside the Stage 3-5 sinks):
    journal = LiveJournal()
    vault.add_record_sink(journal.on_record)        # full trade records
    policy  = journal.wrap_policy(champion_policy(vector))   # logs daily book picks
    guard   = RiskGuard(..., on_halt=multi(tg.on_halt, journal.on_halt))
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
    """12-hex reproducibility stamp of an engine config (pydantic JSON is stable)."""
    return hashlib.sha256(cfg.model_dump_json().encode()).hexdigest()[:12]


class LiveJournal:
    def __init__(self, dir_path: Path = DEFAULT_DIR):
        self.dir = Path(dir_path)
        self.journal_path = self.dir / "journal.jsonl"
        self.decisions_path = self.dir / "decisions.jsonl"
        self.failures = 0
        self._cfg_hashes: dict[int, str] = {}          # id(cfg) -> hash (per-session cfg reuse)
        self._logged: set[tuple[str, str]] = set()     # trade dedup, re-armed from disk
        if self.journal_path.exists():
            for rec in self.trades():
                self._logged.add(_trade_key(rec.trade_date, rec.fill_ts))

    # ---- sinks --------------------------------------------------------------
    def on_record(self, tr, book: str, cfg) -> None:
        """Vault record sink: journal one completed trade with full context."""
        key = _trade_key(tr.trade_date, tr.fill_ts)
        if key in self._logged:
            return
        h = self._cfg_hashes.get(id(cfg))
        if h is None:
            h = self._cfg_hashes[id(cfg)] = cfg_hash(cfg)
        rec = from_trade_record(tr, config_hash=h, playbook=book)
        if self._append(self.journal_path, rec.model_dump_json()):
            self._logged.add(key)

    def on_halt(self, date: str, reason: str) -> None:
        self._decision({"type": "halt", "date": date, "reason": reason})

    def note(self, text: str) -> None:
        self._decision({"type": "note", "text": text})

    def wrap_policy(self, policy: Callable) -> Callable:
        """Wrap a session policy so every daily pick is journaled: which book ran the
        day, or that the policy sat it out. Transparent — returns the pick unchanged."""
        def logged(date: str):
            picked = policy(date)
            self._decision({"type": "session", "date": date,
                            "book": None if picked is None else picked[0]})
            return picked
        return logged

    # ---- reading / reconciliation ------------------------------------------
    def trades(self) -> list[JournalRecord]:
        if not self.journal_path.exists():
            return []
        return [JournalRecord(**json.loads(line))
                for line in self.journal_path.read_text().splitlines() if line.strip()]

    def decisions(self) -> list[dict]:
        if not self.decisions_path.exists():
            return []
        return [json.loads(line)
                for line in self.decisions_path.read_text().splitlines() if line.strip()]

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
    def _decision(self, row: dict) -> None:
        self._append(self.decisions_path,
                     json.dumps({"ts": datetime.now().astimezone().isoformat(), **row}))

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
