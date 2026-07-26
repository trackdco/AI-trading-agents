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
import time
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


# A 24/5 autonomous desk must have at least this many humans able to hit the /kill switch.
# One reachable operator (asleep, no signal, dead phone) is a single point of failure.
MIN_KILL_OPERATORS = 2


def kill_switch_redundancy_warning(cfg: "TelegramConfig") -> str | None:
    """Return a warning string when fewer than MIN_KILL_OPERATORS operators can reach the
    Telegram /kill switch, else None. Advisory: callers WARN and broadcast, they never block
    startup (Angus ruling — a single reachable human is a design fault, not a launch gate)."""
    n = len(cfg.allowed_user_ids)
    if n >= MIN_KILL_OPERATORS:
        return None
    return (f"⚠️ KILL-SWITCH SINGLE POINT OF FAILURE: {n} authorized Telegram operator"
            f"{'' if n == 1 else 's'} configured (need ≥{MIN_KILL_OPERATORS}). A 24/5 "
            f"autonomous desk with one reachable human cannot be halted if that person is "
            f"unreachable. Add more ids to TELEGRAM_ALLOWED_USER_IDS in .env "
            f"(find them with `python -m src.live.telegram --whoami`).")


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


class KillFileListener:
    """The CANON stack's /kill + /status consumer (scripts/kill_listener.py runs it).

    CommandListener above belongs to the paper Vault stack (its /kill trips a RiskGuard in
    the same process). The canon spine halts on a KILL FILE (paths.kill_file), and the thing
    that writes that file must be a SEPARATE PROCESS: a kill switch living inside the
    process you may need to kill is a single point of failure — a wedged runner would take
    its own off-switch down with it.

    /kill   -> write the KILL file (who + when inside) and confirm. The spine halts on its
               next check and STAYS halted; there is deliberately no /reset — removing the
               file requires a human at the box.
    /status -> kill-file state + how fresh the runner's log is (a stale log = the runner is
               not writing = investigate).
    Locked to allowed_user_ids; strangers and other text are silently ignored/counted."""

    def __init__(self, cfg: TelegramConfig, kill_file, run_log=None,
                 transport: Callable = _http_transport, clock: Callable = time.time):
        self.cfg = cfg
        self.kill_file = Path(kill_file)
        self.run_log = Path(run_log) if run_log else None
        self._transport = transport
        self._clock = clock
        self._offset = 0
        self.ignored = 0

    def _status_text(self) -> str:
        killed = self.kill_file.exists()
        lines = [f"{'⛔ KILLED' if killed else '🟢 not killed'} | kill file "
                 f"{'PRESENT' if killed else 'absent'}: {self.kill_file}"]
        if self.run_log is not None:
            if self.run_log.exists():
                age = max(0.0, self._clock() - self.run_log.stat().st_mtime)
                lines.append(f"runner log last wrote {age:,.0f}s ago"
                             + (" ⚠️ STALE" if age > 300 else ""))
            else:
                lines.append(f"⚠️ runner log missing ({self.run_log}) — runner never started?")
        return "\n".join(lines)

    def poll_once(self, timeout: int = 0) -> int:
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
            if text == "/kill":
                self.kill_file.parent.mkdir(parents=True, exist_ok=True)
                self.kill_file.write_text(
                    f"killed via telegram by user {user} at epoch {self._clock():.0f}\n")
                self._reply(f"⛔ KILL file set — the spine halts on its next check and stays "
                            f"halted. Removing it requires a human at the box "
                            f"({self.kill_file}).")
                handled += 1
            elif text == "/status":
                self._reply(self._status_text())
                handled += 1
        return handled

    def _reply(self, text: str) -> None:
        try:
            self._transport("sendMessage",
                            {"chat_id": self.cfg.chat_id, "text": text}, self.cfg.token)
        except Exception as e:
            print(f"[telegram] reply failed: {type(e).__name__}: {e}", file=sys.stderr)


# ------------------------------------------------------------------ setup helpers

def whoami(cfg: TelegramConfig, transport: Callable = _http_transport) -> list[dict]:
    """List everyone who messaged OUR bot recently, with their Telegram user id.

    This exists so the team never has to trust a third-party "user info" bot to learn
    their id — Telegram is full of impostor clones of @userinfobot/@RawDataBot that
    mimic the display name but never reply. DM our own bot instead, then run
    `python -m src.live.telegram --whoami`. (getUpdates keeps messages ~24h, and this
    read does not ack offsets, so the live CommandListener still sees everything.)"""
    out = transport("getUpdates", {"timeout": 0}, cfg.token)
    seen: dict[int, dict] = {}
    for upd in out.get("result", []):
        msg = upd.get("message") or {}
        frm = msg.get("from") or {}
        if "id" in frm:
            name = " ".join(x for x in (frm.get("first_name"), frm.get("last_name")) if x)
            seen[frm["id"]] = {"user_id": frm["id"], "name": name,
                               "username": frm.get("username"),
                               "chat_id": (msg.get("chat") or {}).get("id")}
    return list(seen.values())


# ------------------------------------------------------------------ smoke test

if __name__ == "__main__":
    if "--test" in sys.argv:
        cfg = TelegramConfig.from_env()
        ok = TelegramAlerts(cfg).say("✅ NQ desk bot: Telegram wiring OK (stage-5 smoke test)")
        print("sent" if ok else "FAILED — check token/chat id in .env")
        raise SystemExit(0 if ok else 1)
    if "--whoami" in sys.argv:
        rows = whoami(TelegramConfig.from_env())
        if not rows:
            print("no messages seen yet — send our bot a direct message (say 'hello'), "
                  "then run this again (messages stay visible for ~24h)")
        for r in rows:
            u = f"@{r['username']}" if r["username"] else "(no username)"
            print(f"user_id={r['user_id']}  name={r['name']}  {u}  "
                  f"(seen in chat {r['chat_id']})")
        raise SystemExit(0)
    print(__doc__)
