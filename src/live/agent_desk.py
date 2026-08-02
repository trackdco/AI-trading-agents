"""R15 agent layer, LIVE — the desk-run reference (scripts/capture_desk_run.py) ported
to the per-bar loop. Transport, not redesign (HANDOVER §7): every decision rule, guard,
threshold, prompt string and journal field is the reference's, verbatim where the shape
allows and behavior-for-behavior where batch->incremental forces a different shape.

The split, per ANGUS's mandate: entries stay mechanical (the certified R13 path places
and cancels brackets); once a fill COMMITS, the agent owns the trade to flat — within
driver-enforced guardrails. The mechanical laws override the agent unconditionally:
stop-first every bar, the 09:30 pre-flatten, the 15:55 EOD, the close-and-reverse flip,
and the kill file.

ISOLATION LAW (§7 row 8): a hung, dead, or malformed agent NEVER blocks orders, stops,
flattens, or flips. Concretely:
  * REPLAY (certification): agent calls are synchronous — batch causality, exactly the
    reference. The replay clock is not wall time, so blocking is free.
  * LIVE: agent calls run on a worker thread; the loop never waits. A reply is applied
    at the first bar boundary after it lands — which is the reference's own execution
    convention (actions at NEXT bar) arriving at most one bar later than the batch
    equivalent. While a call is in flight the standing plan executes mechanically.
  * Failure of any kind (timeout, dead CLI, non-JSON) degrades to "hold" — the
    reference's own fail-closed parse — and the trade continues on its standing plan.

SHADOW V8 (§7 row 7): every managed trade also runs the CERTIFIED mechanical exit walk
in shadow — a private DryRunBroker seeded with the same fill, driven by the same
LiveExitExecutor the R13 cert exercised. Its exit is the "MECHANICAL EXIT NOW" event
(take it or refuse it), and its realized R is the journal's `v8_R` counterfactual.
Without that column the learning loop is dead.
"""
from __future__ import annotations

import json
import re
import subprocess
import threading
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

NY = "America/New_York"
TICK = 0.25
SLIP = 1                       # ticks, market actions (reference convention)
PV = 2.0                       # $/pt per MICRO (MNQ) — the live account trades micros;
                               # the reference's 20.0 was the mini-contract grading unit.
COMMISSION = 5.0
MAX_TURNS = 10
CLI_TIMEOUT = 240
SPEC = Path(".claude/agents/trade-manager-v3.md")    # FROZEN — deploy byte-identical

TURN_CONTRACT = (
    'Reply with EXACTLY one JSON object, nothing else: {"action":"hold"|"revise"|'
    '"exit_now","stop_r":<num,optional>,"target_r":<num or null,optional>,'
    '"partial_pct":<0-1,optional>,"note":"<=120 chars"}. "hold"=no change. "revise" '
    'adjusts the standing plan: stop_r only ever TIGHTENS (in R from entry; 0=BE), '
    'target_r replaces the target (null = run on the stop; >=2.0R unless a partial is '
    'already booked), partial_pct books that fraction of what is OPEN at next bar. '
    '"exit_now" flattens at next bar. Rule-breaking fields are ignored by the harness.')


# ------------------------------------------------------------------ CLI conversations

def call_claude(prompt: str, session: str | None, *, cwd: Path,
                spec: Path = SPEC, timeout: int = CLI_TIMEOUT) -> tuple[str, str | None]:
    """The reference's call, verbatim semantics: spec as system prompt, ALL tools
    disabled, JSON output, --resume per trade, one retry, then __ERROR__ (-> hold)."""
    cmd = ["claude", "-p", "--system-prompt-file", str(spec),
           "--disallowedTools", "*", "--output-format", "json"]
    if session:
        cmd += ["--resume", session]
    cmd.append(prompt)
    for attempt in (1, 2):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                               cwd=str(cwd))
            out = json.loads(r.stdout.strip().splitlines()[-1])
            return out.get("result", ""), out.get("session_id") or session
        except Exception as e:                     # noqa: BLE001 — fail closed to hold
            if attempt == 2:
                return f"__ERROR__ {e}", session
    return "__ERROR__", session


def parse_reply(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return {"action": "hold", "note": "unparseable -> no change"}
    try:
        d = json.loads(m.group(0))
    except Exception:                              # noqa: BLE001
        return {"action": "hold", "note": "bad json -> no change"}
    if d.get("action") not in ("hold", "revise", "exit_now"):
        d["action"] = "hold"
    return d


# ------------------------------------------------------------------ market data views

def flow_line(tape: pd.DataFrame, minute, s: int) -> str:
    w = tape.loc[:minute]
    if not len(w):
        return "flow: no tape"
    d1 = float(w.delta.iloc[-1]) * s
    c5 = float(w.delta.tail(5).sum()) * s
    c15 = float(w.delta.tail(15).sum()) * s
    opp = int((np.sign(w.delta.tail(5).to_numpy() * s) < 0).sum())
    v = float(w.vol.iloc[-1])
    vmed = float(w.vol.tail(60).median()) or 1.0
    return (f"flow(signed to trade): delta1m {d1:+.0f} cvd5m {c5:+.0f} cvd15m {c15:+.0f} "
            f"opposed {opp}/5 vol {v / vmed:.1f}x")


def book_line_from_levels(levels: list[dict], last: float, s: int) -> str:
    """The reference's book_line over the live DepthBook's long_form(10) snapshot —
    same imbalance and wall-ahead arithmetic, live book instead of archive CSV."""
    if not levels:
        return "book: n/a"
    bid = [lv for lv in levels if lv.get("side") == "bid"]
    ask = [lv for lv in levels if lv.get("side") == "ask"]
    if not bid or not ask:
        return "book: n/a"
    tb = float(sum(lv["size"] for lv in bid))
    ta = float(sum(lv["size"] for lv in ask))
    ahead = ask if s > 0 else bid
    wa = max(ahead, key=lambda lv: lv["size"])
    return (f"book: imbalance {((tb - ta) / max(tb + ta, 1)) * s:+.2f} "
            f"wall-ahead {abs(float(wa['price']) - last):.2f}pt x{float(wa['size']):.0f}")


# ------------------------------------------------------------------ journal

def journal_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


def journal_digest(rows: list[dict]) -> str:
    if not rows:
        return "journal: no completed trades yet — judge on the tape alone."
    n = len(rows)
    da = sum(r["agent_R"] for r in rows)
    dv = sum(r["v8_R"] for r in rows)
    ext = sum(1 for r in rows if r.get("extended"))
    parts = sum(1 for r in rows if r.get("partials"))
    lines = [f"journal: {n} trades managed | your total {da:+.1f}R vs V8 {dv:+.1f}R "
             f"(delta {da - dv:+.1f}R) | held past mechanical exit {ext}x | partials {parts}x"]
    for sess in ("pre", "gold"):
        g = [r for r in rows if r["sess"] == sess]
        if g:
            lines.append(f"  {sess}: n{len(g)} you {sum(r['agent_R'] for r in g):+.1f}R "
                         f"vs V8 {sum(r['v8_R'] for r in g):+.1f}R")
    dying = [r for r in rows if r["v8_R"] < -0.1]
    winning = [r for r in rows if r["v8_R"] > 0.1]
    if dying:
        lines.append(f"  defense (mech losers, n{len(dying)}): you "
                     f"{sum(r['agent_R'] - r['v8_R'] for r in dying):+.1f}R vs mech")
    if winning:
        lines.append(f"  offense (mech winners, n{len(winning)}): you "
                     f"{sum(r['agent_R'] - r['v8_R'] for r in winning):+.1f}R vs mech")
    cuts = [r for r in rows if r["exit_reason"] == "agent_exit"
            and r.get("left_peak_R") is not None]
    if cuts:
        for label, sel in (
                ("flow still WITH you", [r for r in cuts if r.get("cvd5_at_exit", 0) > 0]),
                ("flow AGAINST you", [r for r in cuts if r.get("cvd5_at_exit", 0) <= 0])):
            if not sel:
                continue
            lp = sorted(r["left_peak_R"] for r in sel)
            died = sum(1 for r in sel if r["would_have_stopped"])
            lines.append(
                f"  your exits with {label} (n{len(sel)}): {died} would have hit the "
                f"stop anyway; median run AFTER you left: {lp[len(lp) // 2]:+.1f}R")
    caps = [r["capture"] for r in rows if r.get("capture") is not None]
    if caps:
        caps.sort()
        lines.append(f"  capture (realized/peak, trades that reached +0.5R): median "
                     f"{caps[len(caps) // 2]:+.2f}")
    lines.append("last trades (you vs V8):")
    for r in rows[-5:]:
        lines.append(f"  {r['day']} {r['sess']} {r['direction']}: {r['agent_R']:+.2f}R vs "
                     f"{r['v8_R']:+.2f}R ({r['exit_reason']}; {r.get('last_note', '')[:60]})")
    return "\n".join(lines)


# ------------------------------------------------------------------ managed trade

def _sgn(direction: str) -> int:
    return 1 if direction == "long" else -1


@dataclass
class ManagedTrade:
    """One filled position under agent management — the reference's manage_trade loop
    re-shaped as an incremental per-bar state machine. All thresholds verbatim."""
    ref: str
    day: str
    sess: str                                   # pre | gold
    direction: str
    entry: float
    stop: float                                 # engine stop at fill; agent may TIGHTEN
    risk: float                                 # points, |entry - engine stop|
    size: int                                   # micros open (informational; fractions rule)
    fill_ts: pd.Timestamp
    flatten: pd.Timestamp                       # 09:30 (pre) / 15:55 ET, day-local
    target: float | None = None                 # structural working target (None = stop-run)
    pattern: str = "?"
    is_reversal: bool = False
    thesis: str = ""
    reread: str | None = None

    desk: object = None                         # backref (AgentDesk)
    legs: list = field(default_factory=list)
    frac: float = 1.0
    pending: list = field(default_factory=list)
    turns: int = 0
    transcript: list = field(default_factory=list)
    partial_done: bool = False
    extended: bool = False
    last_note: str = ""
    peak_r: float = 0.0
    seen_r: set = field(default_factory=set)
    last_turn_min: object = None
    r3: float | None = None
    r5: float | None = None
    sid: str | None = None
    gb_peak: float = 0.0
    done: bool = False
    cx_min: object = None                       # shadow-V8 exit minute (set by the desk)
    cx_price: float | None = None
    # in-flight agent call (LIVE mode): (thread, result_holder)
    _inflight: object = None

    def r_of(self, px: float) -> float:
        return _sgn(self.direction) * (px - self.entry) / self.risk

    # ---- reply application (guardrails, verbatim thresholds) --------------------
    def apply_reply(self, rep: dict) -> None:
        s = _sgn(self.direction)
        self.last_note = str(rep.get("note", ""))[:120]
        act = rep["action"]
        if act == "exit_now":
            self.pending.append(("exit", None))
            return
        if act != "revise":
            return
        if rep.get("stop_r") is not None:
            try:
                cand = self.entry + s * float(rep["stop_r"]) * self.risk
                if s * (cand - self.stop) > 0:                  # tighten only
                    self.stop = round(round(cand / TICK) * TICK, 10)
            except Exception:                                   # noqa: BLE001
                pass
        if "target_r" in rep:
            tr = rep.get("target_r")
            if tr is None:
                self.target = None
            else:
                try:
                    tr = float(tr)
                    floor = 0.1 if self.partial_done else 2.0
                    if tr >= floor:
                        self.target = round(
                            round((self.entry + s * tr * self.risk) / TICK) * TICK, 10)
                except Exception:                               # noqa: BLE001
                    pass
        if rep.get("partial_pct") is not None:
            try:
                p = float(rep["partial_pct"])
                if 0.0 < p < 1.0:
                    self.pending.append(("partial", p))
            except Exception:                                   # noqa: BLE001
                pass

    # ---- settle (schema identical to the seed; reference field for field) --------
    def _settle_row(self, reason_final: str, ts, tape: pd.DataFrame) -> dict:
        s = _sgn(self.direction)
        pts = sum(fr * s * (px - self.entry) for fr, px, _ in self.legs)
        net = pts * PV * self.size - COMMISSION
        w = tape.loc[:ts] if tape is not None else tape
        fx = {}
        if w is not None and len(w) >= 5:
            fx = {"cvd5_at_exit": round(float(w.delta.tail(5).sum()) * s, 0),
                  "cvd15_at_exit": round(float(w.delta.tail(15).sum()) * s, 0),
                  "opposed_at_exit": int((np.sign(w.delta.tail(5).to_numpy() * s) < 0).sum())}
        unit = self.risk * PV * self.size
        agent_r = round(net / unit, 4) if unit else 0.0
        return {"trade_id": self.ref, "day": self.day, "sess": self.sess,
                "direction": self.direction, "risk": self.risk,
                "agent_R": agent_r, "agent_dollars": round(net, 2),
                "v8_R": None, "v8_dollars": None,        # filled by the desk's shadow V8
                "exit_reason": reason_final, "exit_ts": str(ts), "turns": self.turns,
                "partials": sum(1 for _, _, r in self.legs if r == "partial"),
                "extended": self.extended,
                "held_min": int((ts - self.fill_ts).total_seconds() // 60),
                "mfe_R": round(self.peak_r, 3),
                "capture": (round(agent_r / self.peak_r, 3)
                            if self.peak_r > 0.5 else None),
                "left_peak_R": None, "would_have_stopped": None,
                "settle_after_R": None, **fx,
                "last_note": self.last_note,
                "legs": [(f, p, r) for f, p, r in self.legs]}

    def _close(self, fr: float, px: float, reason: str) -> None:
        self.legs.append((fr, px, reason))
        self.frac = round(self.frac - fr, 10)


class _PostExit:
    """The reference settle()'s look-ahead, incremental: after the exit, watch bars to
    the session boundary on the ORIGINAL stop, then finalize left_peak_R /
    would_have_stopped / settle_after_R and release the journal row (causal — read only
    by LATER trades, exactly the reference's cutoff)."""

    def __init__(self, row: dict, trade: ManagedTrade, exit_ts, last_leg_px: float):
        self.row, self.t = row, trade
        self.exit_ts = exit_ts
        self.last_px = float(last_leg_px)
        self.left_peak, self.would_stop, self.end_after = 0.0, False, 0.0
        self.done = False

    def on_bar(self, minute, bar) -> None:
        if self.done:
            return
        t, s = self.t, _sgn(self.t.direction)
        if minute <= self.exit_ts:
            return
        if minute >= t.flatten:
            self.finish()
            return
        orig_stop = t.entry - s * t.risk        # the ORIGINAL engine stop (-1R)
        if (s > 0 and bar.low <= orig_stop) or (s < 0 and bar.high >= orig_stop):
            self.would_stop = True
            self.end_after = t.r_of(orig_stop)
            self.finish()
            return
        fav = (bar.high - self.last_px) if s > 0 else (self.last_px - bar.low)
        self.left_peak = max(self.left_peak, float(fav) / t.risk)
        self.end_after = t.r_of(float(bar.close))

    def finish(self) -> None:
        self.row["left_peak_R"] = round(self.left_peak, 3)
        self.row["would_have_stopped"] = bool(self.would_stop)
        self.row["settle_after_R"] = round(self.end_after, 3)
        self.done = True


class ShadowV8:
    """The certified mechanical exit walk on a PRIVATE DryRunBroker — same
    LiveExitExecutor, same config, seeded with the same fill. Its exit is the
    'MECHANICAL EXIT NOW' event and its realized R is the journal's v8_R."""

    def __init__(self, rec_trigger, verdict: dict, filled_size: int,
                 fill_ts, exit_cfg, account: str):
        from src.canon.exit_live import LiveExitExecutor
        from src.canon.spine import OrderIntent
        from src.live.ny_execution import DryRunBroker
        self.entry = float(verdict["entry"])
        self.stop = float(verdict["stop"])
        self.side = "B" if verdict["direction"] == "long" else "S"
        self.size = int(filled_size)
        bk = DryRunBroker()
        bref = bk.submit_bracket(OrderIntent(
            side=self.side, order_type="limit", entry_ref=self.entry, stop=self.stop,
            target=None, size=self.size, setup_id="shadow-v8", account=account))
        bk.on_bar(fill_ts, self.entry, self.entry, self.entry)   # seed the fill
        bk.take_fills()
        self.bk = bk
        self.exe = LiveExitExecutor(
            broker=bk, ref=bref, account=account, trigger=rec_trigger, cfg=exit_cfg,
            canon_entry=self.entry, canon_stop=self.stop, size=self.size,
            armed=True, journal=None)
        self.legs: list = []
        self.exit_min = None
        self.exit_price: float | None = None
        self.exit_reason: str | None = None

    @property
    def done(self) -> bool:
        return self.exit_min is not None

    def on_bar(self, bars_df: pd.DataFrame, minute, bar) -> None:
        if self.done:
            return
        self.bk.on_bar(minute, float(bar.high), float(bar.low), float(bar.close))
        stop_fired = self.bk.take_stop_fires()
        if self.exe is not None and not getattr(self.exe, "done", False):
            for a in (self.exe.on_bar(bars_df, minute) or []):
                if a["kind"] == "partial":
                    self.legs.append((int(a.get("qty", 0)), float(a.get("price") or 0)))
                elif a["kind"] == "exit":
                    px = a.get("price")
                    self.exit_price = float(px) if px is not None else (
                        self.stop if a.get("reason") in ("stop", "be_stop") else self.entry)
                    self.exit_reason = str(a.get("reason"))
                    self.exit_min = minute
                    return
        if stop_fired and self.exit_min is None:
            self.exit_price = self.stop
            self.exit_reason = "stop"
            self.exit_min = minute

    def flatten_now(self, minute, px: float) -> None:
        """Session boundary: the shadow book flattens too (two-session law)."""
        if not self.done:
            self.exit_price = float(px)
            self.exit_reason = "session_flatten"
            self.exit_min = minute

    def realized(self) -> tuple[float, float]:
        """(v8_R, v8_dollars) from the shadow legs + final exit, book arithmetic."""
        sgn = 1.0 if self.side == "B" else -1.0
        closed = sum(q for q, _ in self.legs)
        pl = sum(sgn * (px - self.entry) * PV * q for q, px in self.legs)
        px = self.exit_price if self.exit_price is not None else self.entry
        pl += sgn * (px - self.entry) * PV * max(self.size - closed, 0)
        pl -= COMMISSION
        unit = abs(self.entry - self.stop) * PV * self.size
        return (round(pl / unit, 4) if unit else 0.0), round(pl, 2)


# ------------------------------------------------------------------ the desk

class AgentDesk:
    """Owns the day reads and every ManagedTrade; the NYLive loop drives it per bar.

    Modes: `sync=True` (replay/cert) blocks on each agent call — the reference's batch
    causality. `sync=False` (live) launches calls on a worker thread and applies the
    reply at the first bar after it lands; the mechanical plan runs regardless.
    """

    def __init__(self, *, execution, exit_cfg, journal_path: Path,
                 transcripts_dir: Path, runs_cwd: Path, journal_sink=None,
                 sync: bool = True, call_fn=call_claude):
        self.execution = execution
        self.exit_cfg = exit_cfg
        self.journal_path = Path(journal_path)
        self.transcripts = Path(transcripts_dir)
        self.transcripts.mkdir(parents=True, exist_ok=True)
        self.runs_cwd = Path(runs_cwd)
        self.sync = sync
        self.call = call_fn
        # `if ... is not None`, NOT `or`: the live sink is a list-like that is FALSY
        # while empty — `or` silently discarded it (caught by the integration test)
        self.note = journal_sink if journal_sink is not None else (lambda row: None)
        self.trades: dict[str, ManagedTrade] = {}
        self.shadows: dict[str, ShadowV8] = {}
        self.post_exit: dict[str, _PostExit] = {}
        self.thesis: str = ""
        self.reread: str | None = None
        self._tape_rows: list[tuple] = []           # (minute_ny, delta, vol)
        self._tape_df: pd.DataFrame | None = None
        self._reads_day: str | None = None
        self._read_sid: str | None = None
        self._reread_done = False

    # ---- tape (the reference's fp_minutes frame, built live) ---------------------
    def push_tape(self, minute_ny: pd.Timestamp, delta: float, vol: float) -> None:
        self._tape_rows.append((minute_ny, delta, vol))
        if len(self._tape_rows) > 2000:
            self._tape_rows = self._tape_rows[-1200:]
        self._tape_df = None                        # rebuild lazily

    def tape_frame(self) -> pd.DataFrame | None:
        if not self._tape_rows:
            return None
        if self._tape_df is None:
            self._tape_df = pd.DataFrame(
                self._tape_rows, columns=["ts", "delta", "vol"]).set_index("ts")
        return self._tape_df

    # ---- day reads (reference day_reads, live frame in) --------------------------
    def maybe_day_reads(self, bts_ny: pd.Timestamp, bars_ny: pd.DataFrame) -> None:
        day = bts_ny.strftime("%Y-%m-%d")
        hm = bts_ny.strftime("%H:%M")
        if self._reads_day != day and hm >= "07:45":
            self._reads_day, self._reread_done = day, False
            self.thesis, self._read_sid = self._thesis_read(day, bars_ny)
            self.reread = None
            self.note({"type": "agent_day_read", "day": day, "which": "thesis",
                       "text": self.thesis[:400]})
        if (self._reads_day == day and not self._reread_done and hm >= "09:40"
                and self._read_sid):
            self._reread_done = True
            self.reread = self._reread(day, bars_ny)
            self.note({"type": "agent_day_read", "day": day, "which": "reread",
                       "text": (self.reread or "")[:300]})

    def _thesis_read(self, day: str, bars: pd.DataFrame) -> tuple[str, str | None]:
        b = bars.set_index("ts_event") if "ts_event" in bars.columns else bars
        d0 = pd.Timestamp(f"{day} 07:40", tz=NY)
        prior = b.loc[:d0 - pd.Timedelta(hours=16)]
        on = b.loc[d0 - pd.Timedelta(hours=13, minutes=40):d0]
        if not len(on):
            return "no overnight data", None
        pd_day = (prior[prior.index >= prior.index[-1] - pd.Timedelta("24h")]
                  if len(prior) else on)
        last = float(on.close.iloc[-1])
        journal = journal_rows(self.journal_path)
        gap_note = ""
        if journal:
            last_day = max(r["day"] for r in journal)
            gap = (pd.Timestamp(day) - pd.Timestamp(last_day)).days
            if gap > 4:
                gap_note = (f"NOTE: {gap} calendar days since your last journaled day "
                            f"({last_day}) — a sample/time gap. The regime may have "
                            f"shifted; weight your older journal entries accordingly.\n")
        ctx = (f"PRE-MARKET READ, {day} 07:45 ET. You trade NQ pullback rejections: pre "
               f"08:00-09:30 (ALL pre positions flattened at 09:30 — two sessions), gold "
               f"09:40-10:30, mechanical entries, you manage them.\n{gap_note}"
               f"prior day: O {pd_day.open.iloc[0]:.0f} H {pd_day.high.max():.0f} "
               f"L {pd_day.low.min():.0f} C {pd_day.close.iloc[-1]:.0f}\n"
               f"overnight (18:00->07:40): H {on.high.max():.0f} L {on.low.min():.0f} "
               f"last {last:.0f} (gap {last - float(pd_day.close.iloc[-1]):+.0f} vs prior close)\n"
               f"last 5 bars (t,h,l,c): "
               + "; ".join(f"{t.strftime('%H:%M')} {r.high:.0f}/{r.low:.0f}/{r.close:.0f}"
                           for t, r in on.tail(5).iterrows())
               + f"\n{journal_digest(journal)}\n"
               'Reply EXACTLY one JSON: {"bias":"long|short|neutral","day_type":"<=30 chars",'
               '"thesis":"<=200 chars","invalidates":"<=120 chars"}')
        txt, sid = self.call(ctx, None, cwd=self.runs_cwd)
        return txt.strip(), sid

    def _reread(self, day: str, bars: pd.DataFrame) -> str | None:
        b = bars.set_index("ts_event") if "ts_event" in bars.columns else bars
        o = b.loc[pd.Timestamp(f"{day} 09:30", tz=NY):pd.Timestamp(f"{day} 09:39", tz=NY)]
        if not len(o):
            return None
        rr = (f"09:40 RE-READ. The cash open printed: 09:30-09:39 "
              f"O {o.open.iloc[0]:.0f} H {o.high.max():.0f} L {o.low.min():.0f} "
              f"C {o.close.iloc[-1]:.0f}. Update or confirm your read. "
              'Reply EXACTLY one JSON: {"bias":"long|short|neutral","note":"<=150 chars"}')
        txt, _ = self.call(rr, self._read_sid, cwd=self.runs_cwd)
        return txt.strip()

    # ---- trade lifecycle ---------------------------------------------------------
    def on_committed_fill(self, ref: str, verdict: dict, filled_size: int,
                          fill_ts: pd.Timestamp, trigger, pre: bool,
                          is_reversal: bool) -> None:
        """The runner committed a fill — the agent inherits the mechanical plan."""
        day = fill_ts.tz_convert(NY).strftime("%Y-%m-%d")
        sess = "pre" if pre else "gold"
        entry, stop = float(verdict["entry"]), float(verdict["stop"])
        t = ManagedTrade(
            ref=ref, day=day, sess=sess, direction=verdict["direction"],
            entry=entry, stop=stop, risk=abs(entry - stop) or TICK,
            size=int(filled_size), fill_ts=fill_ts.tz_convert(NY),
            flatten=pd.Timestamp(f"{day} {'09:30' if pre else '15:55'}", tz=NY),
            target=None, pattern=getattr(trigger, "pattern", "?"),
            is_reversal=is_reversal, thesis=self.thesis, reread=self.reread, desk=self)
        self.trades[ref] = t
        # the shadow walk is evidence, not control — its failure NEVER blocks the trade
        try:
            if self.exit_cfg is not None:
                self.shadows[ref] = ShadowV8(trigger, verdict, filled_size,
                                             fill_ts, self.exit_cfg,
                                             self.execution.account)
        except Exception as e:                     # noqa: BLE001
            self.note({"type": "agent_shadow_failed", "ref": ref, "error": repr(e)})
        self.note({"type": "agent_trade_open", "ref": ref, "sess": sess,
                   "entry": entry, "stop": stop, "size": int(filled_size)})

    def on_position_closed_externally(self, ref: str, reason: str, ts, px: float,
                                      tape) -> None:
        """A mechanical law closed the position outside the desk (rule J flip, rule K
        flatten, broker stop): record the leg and settle."""
        t = self.trades.get(ref)
        if t is None or t.done:
            return
        rmap = {"rule_j_flip": "flip", "rule_k_flatten": "open_flatten", "stop": "stop"}
        t._close(t.frac, float(px), rmap.get(reason, reason))
        self._settle(t, rmap.get(reason, reason), ts, px, tape)

    # ---- per-bar drive -----------------------------------------------------------
    def on_bar(self, minute_ny: pd.Timestamp, bar, bars_ny: pd.DataFrame,
               tape: pd.DataFrame, book_levels: list[dict]) -> None:
        self.maybe_day_reads(minute_ny, bars_ny)
        for sh in self.shadows.values():
            if not sh.done:
                sh.on_bar(bars_ny, minute_ny, bar)
        for pe in list(self.post_exit.values()):
            pe.on_bar(minute_ny, bar)
        for ref, pe in list(self.post_exit.items()):
            if pe.done:
                self._write_row(ref, pe.row)
                del self.post_exit[ref]
        for ref, t in list(self.trades.items()):
            if t.done:
                continue
            self._drive_trade(ref, t, minute_ny, bar, bars_ny, tape, book_levels)

    def _drive_trade(self, ref, t: ManagedTrade, minute, bar, bars_ny, tape, levels):
        s = _sgn(t.direction)
        sh = self.shadows.get(ref)
        # 0. a reply that landed since the last bar (async mode) applies NOW
        if t._inflight is not None:
            th, holder = t._inflight
            if not th.is_alive():
                t._inflight = None
                txt = holder.get("txt", "__ERROR__")
                t.sid = holder.get("sid") or t.sid
                rep = parse_reply(txt)
                t.transcript.append({"minute": str(minute), "why": holder.get("why", ""),
                                     "sent": holder.get("sent", ""), "reply": txt})
                t.turns += 1
                t.last_turn_min = minute
                before = t.stop
                t.apply_reply(rep)
                if t.stop != before:
                    self.execution.modify_agent_stop(ref, t.stop)
        # 1. session flatten (the desk enforces 15:55 for gold; rule K owns pre 09:30
        #    upstream, this is the belt for both)
        if minute >= t.flatten and t.frac > 0:
            reason = "open_flatten" if t.sess == "pre" else "eod"
            px = float(bar.open) - s * SLIP * TICK
            self.execution.close_now(ref, reason)
            t._close(t.frac, px, reason)
            if sh is not None:
                sh.flatten_now(minute, px)
            self._settle(t, reason, minute, px, tape)
            return
        # 2. pending market actions at this bar's open
        pend, t.pending = t.pending, []
        for kind, val in pend:
            px = float(bar.open) - s * SLIP * TICK
            if kind == "exit" and t.frac > 0:
                self.execution.close_now(ref, "agent_exit")
                t._close(t.frac, px, "agent_exit")
            elif kind == "partial" and t.frac > 0:
                fr = round(t.frac * val, 10)
                qty = max(1, int(round(t.size * fr)))
                self.execution.close_partial_qty(ref, qty)
                t._close(fr, px, "partial")
                t.partial_done = True
        if t.frac <= 0:
            self._settle(t, "agent_exit", minute, float(bar.open), tape)
            return
        # 3. stop, stop-first (the BROKER stop is the enforcement; this mirrors it and
        #    settles when the broker's stop fired this bar)
        if (s > 0 and bar.low <= t.stop) or (s < 0 and bar.high >= t.stop):
            px = (min(t.stop, float(bar.open)) if s > 0
                  else max(t.stop, float(bar.open))) - s * SLIP * TICK
            self.execution.on_agent_stop(ref)
            t._close(t.frac, px, "stop")
            self._settle(t, "stop", minute, px, tape)
            return
        # 4. target, trade-through
        if t.target is not None and ((s > 0 and bar.high >= t.target + TICK)
                                     or (s < 0 and bar.low <= t.target - TICK)):
            self.execution.close_now(ref, "target")
            t._close(t.frac, float(t.target), "target")
            self._settle(t, "target", minute, float(t.target), tape)
            return
        # 5. state + event detection (reference thresholds, verbatim)
        fav = t.r_of(float(bar.high) if s > 0 else float(bar.low))
        t.peak_r = max(t.peak_r, fav)
        why = None
        mins_in = int((minute - t.fill_ts).total_seconds() // 60)
        if mins_in == 3:
            t.r3 = t.r_of(float(bar.close))
        elif mins_in == 5:
            t.r5 = t.r_of(float(bar.close))
        if t.turns == 0 and t._inflight is None and mins_in >= 1:
            why = "position opened — read the tape and set your initial plan"
        elif mins_in == 3:
            why = "press check (fill+3m)"
        for k in range(1, 20):
            if fav >= k and k not in t.seen_r:
                t.seen_r.add(k)
                why = f"touched +{k}R"
        if (t.peak_r >= 1.0 and t.peak_r - t.r_of(float(bar.close)) >= 0.75
                and t.peak_r - 0.25 > t.gb_peak):
            t.gb_peak = t.peak_r
            why = why or f"giving back off the +{t.peak_r:.1f}R peak"
        w = tape.loc[:minute] if tape is not None else None
        if w is not None and len(w) >= 5 and t.r_of(float(bar.close)) >= 0.5:
            c5 = float(w.delta.tail(5).sum()) * s
            opp = int((np.sign(w.delta.tail(5).to_numpy() * s) < 0).sum())
            if (c5 < 0 or opp >= 4) and (t.last_turn_min is None
                                         or minute - t.last_turn_min >= pd.Timedelta(minutes=5)):
                why = why or "flow turning against a green position"
        if abs(t.r_of(float(bar.close)) - t.r_of(t.stop)) <= 0.3 and mins_in > 3:
            why = why or "price near your stop"
        cx = sh.exit_min if sh is not None else None
        if cx is not None and not t.extended:
            t.cx_min, t.cx_price = cx, sh.exit_price
            why = (f"MECHANICAL EXIT NOW: V8 exits this position here at {sh.exit_price}"
                   f" ({t.r_of(sh.exit_price):+.2f}R). Take it (exit_now) or refuse it "
                   f"with a plan.")
            t.extended = True
        elif t.extended and cx is not None and (t.last_turn_min is None or
                                                minute - t.last_turn_min >= pd.Timedelta(minutes=10)):
            why = why or "extended recheck (10m)"
        if int((t.flatten - minute).total_seconds() // 60) == 30:
            why = why or "30 minutes to EOD flatten"
        if why:
            self._send(t, minute, why, bar, tape, levels)

    # ---- the turn ---------------------------------------------------------------
    def _send(self, t: ManagedTrade, minute, why, bar, tape, levels) -> None:
        if (t.turns >= MAX_TURNS
                or (t.last_turn_min is not None and minute <= t.last_turn_min)
                or t._inflight is not None):
            return
        s = _sgn(t.direction)
        last = float(bar.close)
        press = bool(((((t.r3 or 0) >= 0.5) or ((t.r5 or 0) >= 0.5))
                      and t.r_of(last) > 0 and (t.peak_r - t.r_of(last)) <= 0.25))
        state = (f"[{minute.strftime('%H:%M')}] EVENT: {why}\n"
                 f"bar {bar.open:.2f}/{bar.high:.2f}/{bar.low:.2f}/{bar.close:.2f} | "
                 f"R_now {t.r_of(last):+.2f} peak {t.peak_r:+.2f} | press_state {press} | "
                 f"open {t.frac:.2f} | stop {t.r_of(t.stop):+.2f}R target "
                 f"{'none' if t.target is None else f'{t.r_of(t.target):+.2f}R'} | "
                 f"{flow_line(tape, minute, s) if tape is not None else 'flow: no tape'} | "
                 f"{book_line_from_levels(levels, last, s)} | "
                 f"mins_to_session_end {int((t.flatten - minute).total_seconds() // 60)}")
        if t.turns == 0:
            journal = journal_rows(self.journal_path)
            state = (f"NEW POSITION {t.direction.upper()} {t.sess} | entry {t.entry} "
                     f"risk {t.risk}pt | engine stop {t.stop} (-1R, INVIOLATE FLOOR) | "
                     f"structural target {t.target} "
                     f"({'n/a' if t.target is None else f'{t.r_of(t.target):+.1f}R'}) | "
                     f"pattern {t.pattern} | session ends "
                     f"{'09:30 HARD (pre)' if t.sess == 'pre' else '15:55'}\n"
                     + ("reversal context: this entry CLOSED an opposing position — you "
                        "are trading the book's strongest signal\n"
                        if t.is_reversal else "")
                     + f"day thesis: {t.thesis}\n"
                     + (f"open re-read: {t.reread}\n" if t.reread and t.sess == "gold" else "")
                     + f"{journal_digest(journal)}\n{TURN_CONTRACT}\n\n" + state)
        if self.sync:
            try:
                txt, sid = self.call(state, t.sid, cwd=self.runs_cwd)
            except Exception as e:                 # noqa: BLE001 — ISOLATION LAW:
                txt, sid = f"__ERROR__ {e}", t.sid  # a raising call is a dead agent
            t.sid = sid or t.sid
            rep = parse_reply(txt)
            t.turns += 1
            t.last_turn_min = minute
            t.transcript.append({"minute": str(minute), "why": why,
                                 "sent": state, "reply": txt})
            before = t.stop
            t.apply_reply(rep)
            if t.stop != before:
                self.execution.modify_agent_stop(t.ref, t.stop)
        else:
            holder = {"why": why, "sent": state}

            def _worker(prompt=state, session=t.sid, h=holder):
                try:
                    txt, sid = self.call(prompt, session, cwd=self.runs_cwd)
                except Exception as e:             # noqa: BLE001 — ISOLATION LAW
                    txt, sid = f"__ERROR__ {e}", session
                h["txt"], h["sid"] = txt, sid

            th = threading.Thread(target=_worker, daemon=True)
            t._inflight = (th, holder)
            th.start()

    # ---- settle ------------------------------------------------------------------
    def _settle(self, t: ManagedTrade, reason, ts, last_px: float, tape) -> None:
        t.done = True
        row = t._settle_row(reason, ts, tape)
        sh = self.shadows.get(t.ref)
        if sh is not None:
            if not sh.done:
                sh.flatten_now(ts, float(last_px))
            row["v8_R"], row["v8_dollars"] = sh.realized()
        (self.transcripts / f"{t.ref.replace(':', '_')}.json").write_text(
            json.dumps({"thesis": t.thesis, "reread": t.reread,
                        "turns": t.transcript}, indent=1))
        self.post_exit[t.ref] = _PostExit(row, t, ts, last_px)
        self.note({"type": "agent_trade_settled", "ref": t.ref,
                   "exit_reason": reason, "agent_R": row["agent_R"],
                   "v8_R": row["v8_R"], "turns": t.turns})

    def _write_row(self, ref: str, row: dict) -> None:
        self.journal_path.parent.mkdir(parents=True, exist_ok=True)
        with self.journal_path.open("a") as f:
            f.write(json.dumps(row) + "\n")
        self.trades.pop(ref, None)
        self.shadows.pop(ref, None)

    def finalize(self) -> None:
        """Loop shutdown: flush any post-exit watchers so no journal row is lost."""
        for ref, pe in list(self.post_exit.items()):
            pe.finish()
            self._write_row(ref, pe.row)
            del self.post_exit[ref]
