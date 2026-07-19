"""Telegram alerting + locked commands (Phase 4 Stage 5).

ARCHITECTURE BOUNDARY (strategy §11, architecture invariant 6): alerts fire from the
VAULT side only, after the risk check — this is the ONLY module that talks to Telegram,
and no LLM/agent code imports it or is imported by it.

Outbound (sinks on the Vault/guard):
    tg = TelegramAlerts(TelegramConfig.from_env())
    vault.add_sink(tg.on_trade)                 # completed trades
    guard = RiskGuard(..., on_halt=tg.on_halt)  # risk halts, once per (date, reason)
    tg.daily_summary(broker, date)              # end-of-session rollup
Every send is fail-soft: a Telegram outage can never raise into the trading loop
(the Vault isolates sinks too — belt and braces).

Inbound (CommandListener): long-poll getUpdates, LOCKED to allowed Telegram user ids —
messages from anyone else are ignored and counted. Commands only ever ADD safety:
    /status -> guard + account snapshot        /kill -> arm the kill switch (file)
There is deliberately no /reset command — disarming the kill switch requires a human at
the machine deleting the file.

Transport is injectable (stdlib urllib by default, no new deps): tests run against a
fake; the real token/chat id come from .env (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID /
TELEGRAM_ALLOWED_USER_IDS) and are never committed. Plain-text messages (no parse_mode)
so no escaping pitfalls.

Smoke test once .env is filled:  python -m src.live.telegram --test
"""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from src.live.vault import TradeEvent

API = "https://api.telegram.org"


def _load_env(path: Path = Path(".env")) -> None:
    """Minimal .env loader (no new deps): fills os.environ without overriding."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())


def _http_transport(method: str, params: dict, token: str, timeout: float = 10.0) -> dict:
    """Default transport: POST to the Bot API. Returns the parsed JSON reply."""
    url = f"{API}/bot{token}/{method}"
    data = urllib.parse.urlencode(params).encode()
    with urllib.request.urlopen(url, data=data, timeout=timeout) as r:  # noqa: S310
        return json.loads(r.read().decode())


@dataclass(frozen=True)
class TelegramConfig:
    token: str
    chat_id: str
    allowed_user_ids: tuple[int, ...] = ()

    @classmethod
    def from_env(cls) -> "TelegramConfig":
        _load_env()
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        chat = os.environ.get("TELEGRAM_CHAT_ID", "")
        if not token or not chat:
            raise ValueError("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID missing — fill .env")
        raw = os.environ.get("TELEGRAM_ALLOWED_USER_IDS", "")
        allowed = tuple(int(x) for x in raw.replace(";", ",").split(",") if x.strip())
        return cls(token=token, chat_id=chat, allowed_user_ids=allowed)


# ------------------------------------------------------------------ formatting

def fmt_trade(ev: TradeEvent) -> str:
    arrow = "🟢" if ev.dollars > 0 else ("🔴" if ev.dollars < 0 else "⚪")
    return (f"{arrow} TRADE {ev.trade_date} [{ev.book}] {ev.direction.upper()} "
            f"{ev.pattern}\n"
            f"in  {ev.entry:.2f} @ {ev.fill_ts[11:16]}\n"
            f"out {ev.exit_price:.2f} @ {ev.exit_ts[11:16]} ({ev.exit_reason})\n"
            f"{ev.points:+.2f} pts | ${ev.dollars:+,.0f} | {ev.r_multiple:+.2f}R "
            f"| size {ev.size:g}")


def fmt_halt(date: str, reason: str) -> str:
    return f"⛔ RISK HALT {date}: {reason} — no new trades this session."


def fmt_daily(date: str, trades: int, wins: int, losses: int, points: float,
              dollars: float, equity: float) -> str:
    return (f"📊 DAY {date}: {trades} trades ({wins}W/{losses}L)\n"
            f"{points:+.2f} pts | ${dollars:+,.0f} | equity ${equity:,.0f}")


# ------------------------------------------------------------------ outbound

class TelegramAlerts:
    def __init__(self, cfg: TelegramConfig, transport: Callable = _http_transport):
        self.cfg = cfg
        self._transport = transport
        self.failures = 0

    def _send(self, text: str) -> bool:
        """Fail-soft send: never raises into the trading loop."""
        try:
            out = self._transport("sendMessage",
                                  {"chat_id": self.cfg.chat_id, "text": text},
                                  self.cfg.token)
            ok = bool(out.get("ok", False))
        except Exception as e:
            print(f"[telegram] send failed: {type(e).__name__}: {e}", file=sys.stderr)
            ok = False
        if not ok:
            self.failures += 1
        return ok

    # sink adapters ----------------------------------------------------------
    def on_trade(self, ev: TradeEvent) -> bool:
        return self._send(fmt_trade(ev))

    def on_halt(self, date: str, reason: str) -> bool:
        return self._send(fmt_halt(date, reason))

    def daily_summary(self, broker, date: str) -> bool:
        d = broker.day_summary(date)
        return self._send(fmt_daily(date, d.trades, d.wins, d.losses, d.points,
                                    d.dollars, broker.equity()))

    def say(self, text: str) -> bool:
        return self._send(text)


# ------------------------------------------------------------------ inbound

class CommandListener:
    """Long-poll /status and /kill, locked to `allowed_user_ids`. Anything from an
    unlisted user (or any other text) is ignored and counted, never answered — the bot
    stays silent to strangers. Commands can only ADD safety; there is no remote reset."""

    def __init__(self, cfg: TelegramConfig, guard, broker,
                 transport: Callable = _http_transport):
        self.cfg = cfg
        self.guard = guard
        self.broker = broker
        self._transport = transport
        self._offset = 0
        self.ignored = 0

    def poll_once(self, timeout: int = 0) -> int:
        """One getUpdates pass; returns number of commands handled."""
        try:
            out = self._transport("getUpdates",
                                  {"offset": self._offset, "timeout": timeout},
                                  self.cfg.token)
        except Exception as e:
            print(f"[telegram] poll failed: {type(e).__name__}: {e}", file=sys.stderr)
            return 0
        handled = 0
        for upd in out.get("result", []):
            self._offset = max(self._offset, upd.get("update_id", 0) + 1)
            msg = upd.get("message") or {}
            user = (msg.get("from") or {}).get("id")
            text = (msg.get("text") or "").strip().split("@")[0]
            if user not in self.cfg.allowed_user_ids:
                self.ignored += 1
                continue
            if text == "/status":
                s = self.guard.status()
                lines = [f"status | killed={s['killed']} floor={s['floor_tripped']} "
                         f"cumP&L ${s['cum_dollars']:+,.0f} | equity ${self.broker.equity():,.0f}"]
                for d, st in list(s["days"].items())[-3:]:
                    lines.append(f"  {d}: {st['trades']} trades ${st['dollars']:+,.0f}")
                self._reply("\n".join(lines))
                handled += 1
            elif text == "/kill":
                self.guard.trip()
                self._reply("⛔ kill switch ARMED — no new trades until a human removes "
                            "the kill file at the machine.")
                handled += 1
        return handled

    def _reply(self, text: str) -> None:
        try:
            self._transport("sendMessage",
                            {"chat_id": self.cfg.chat_id, "text": text}, self.cfg.token)
        except Exception as e:
            print(f"[telegram] reply failed: {type(e).__name__}: {e}", file=sys.stderr)


# ------------------------------------------------------------------ smoke test

if __name__ == "__main__":
    if "--test" in sys.argv:
        cfg = TelegramConfig.from_env()
        ok = TelegramAlerts(cfg).say("✅ NQ desk bot: Telegram wiring OK (stage-5 smoke test)")
        print("sent" if ok else "FAILED — check token/chat id in .env")
        raise SystemExit(0 if ok else 1)
    print(__doc__)
