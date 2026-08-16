"""R15 agent layer — the desk's own obligations (HANDOVER §7, reference
scripts/capture_desk_run.py). What this file pins: fail-closed parsing, the guardrails
(stop tightens only, target floors, partial bounds), the mechanical-law overrides, the
isolation law (a dead agent never blocks the trade), the journal row schema vs the seed,
and the broker routing of agent actions. Agent calls are SCRIPTED — no CLI here; the
real-CLI path is the on-box certification replay.
"""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from src.live.agent_desk import (
    AgentDesk,
    ManagedTrade,
    parse_reply,
)

NY = "America/New_York"
DAY = "2026-04-20"
ROOT = Path(__file__).resolve().parents[1]


def _ts(hm):
    return pd.Timestamp(f"{DAY} {hm}", tz=NY)


# ------------------------------------------------------------------ parsing/guardrails

def test_parse_reply_fail_closed():
    assert parse_reply("garbage")["action"] == "hold"
    assert parse_reply('{"action":"buy_more"}')["action"] == "hold"
    assert parse_reply('nonsense {"action":"exit_now"} trailing')["action"] == "exit_now"
    assert parse_reply('{"action":"revise","stop_r":-0.5}')["action"] == "revise"


def _trade(**over):
    kw = dict(ref="ny:t:1", day=DAY, sess="gold", direction="long",
              entry=18_000.0, stop=17_990.0, risk=10.0, size=10,
              fill_ts=_ts("09:45"), flatten=_ts("15:55"))
    kw.update(over)
    return ManagedTrade(**kw)


def test_stop_only_tightens():
    t = _trade()
    t.apply_reply({"action": "revise", "stop_r": -2.0})     # WIDEN -> ignored
    assert t.stop == 17_990.0
    t.apply_reply({"action": "revise", "stop_r": -0.5})     # tighten -> applied
    assert t.stop == 17_995.0
    t.apply_reply({"action": "revise", "stop_r": -0.8})     # re-widen -> ignored
    assert t.stop == 17_995.0
    t.apply_reply({"action": "revise", "stop_r": 0.0})      # breakeven -> applied
    assert t.stop == 18_000.0


def test_target_floor_2R_until_partial_then_01():
    t = _trade()
    t.apply_reply({"action": "revise", "target_r": 1.0})    # under floor -> ignored
    assert t.target is None
    t.apply_reply({"action": "revise", "target_r": 2.5})
    assert t.target == 18_025.0
    t.partial_done = True
    t.apply_reply({"action": "revise", "target_r": 0.5})    # post-partial floor 0.1
    assert t.target == 18_005.0
    t.apply_reply({"action": "revise", "target_r": None})   # run on the stop
    assert t.target is None


def test_partial_bounds():
    t = _trade()
    t.apply_reply({"action": "revise", "partial_pct": 1.5})   # >1 -> ignored
    t.apply_reply({"action": "revise", "partial_pct": 0.0})   # 0 -> ignored
    assert t.pending == []
    t.apply_reply({"action": "revise", "partial_pct": 0.5})
    assert t.pending == [("partial", 0.5)]


# ------------------------------------------------------------------ desk end-to-end

class _Exec:
    """Execution surface the desk drives — records every routed action."""
    account = "FUNDED"

    def __init__(self):
        self.calls = []

    def close_now(self, ref, why):
        self.calls.append(("close_now", ref, why))
        return 0.0

    def close_partial_qty(self, ref, qty):
        self.calls.append(("partial", ref, qty))

    def modify_agent_stop(self, ref, price):
        self.calls.append(("modify_stop", ref, price))

    def on_agent_stop(self, ref):
        self.calls.append(("stop_realized", ref))


def _desk(tmp_path, script, sync=True):
    """A desk with a SCRIPTED agent: script = list of reply strings, consumed per call."""
    replies = list(script)

    def call_fn(prompt, session, *, cwd, spec=None, timeout=None):
        if not replies:
            return '{"action":"hold"}', "sess-1"
        r = replies.pop(0)
        if isinstance(r, Exception):
            raise r
        return r, "sess-1"

    return AgentDesk(execution=_Exec(), exit_cfg=None,
                     journal_path=tmp_path / "journal.jsonl",
                     transcripts_dir=tmp_path / "transcripts",
                     runs_cwd=tmp_path, journal_sink=None, sync=sync,
                     call_fn=call_fn)


def _verdict(direction="long", entry=18_000.0, stop=17_990.0):
    return {"direction": direction, "entry": entry, "stop": stop}


def _bar(o, h, low, c):
    return SimpleNamespace(open=o, high=h, low=low, close=c)


def _drive(desk, hm, o, h, low, c):
    desk.on_bar(_ts(hm), _bar(o, h, low, c), pd.DataFrame(), None, [])


def _open_trade(desk, ref="ny:t:1", pre=False):
    trig = SimpleNamespace(pattern="A")
    desk.thesis = "test thesis"
    desk.on_committed_fill(ref, _verdict(), 10, _ts("09:45"), trig, pre, False)
    return desk.trades[ref]


def test_agent_exit_now_executes_at_next_bar_and_journals(tmp_path):
    desk = _desk(tmp_path, ['{"action":"exit_now","note":"cutting"}'])
    t = _open_trade(desk)
    _drive(desk, "09:46", 18_002, 18_004, 18_001, 18_003)   # turn 0 -> exit_now pends
    assert t.pending == [("exit", None)]
    _drive(desk, "09:47", 18_004, 18_005, 18_002, 18_004)   # executes at bar open
    assert t.done
    assert ("close_now", "ny:t:1", "agent_exit") in desk.execution.calls
    desk.finalize()
    rows = [json.loads(x) for x in (tmp_path / "journal.jsonl").read_text().splitlines()]
    assert len(rows) == 1 and rows[0]["exit_reason"] == "agent_exit"
    assert rows[0]["turns"] == 1 and rows[0]["last_note"] == "cutting"


def test_dead_agent_never_blocks_the_trade(tmp_path):
    """ISOLATION LAW: every agent call errors; the stop still executes mechanically."""
    desk = _desk(tmp_path, [RuntimeError("agent dead")] * 20)
    t = _open_trade(desk)
    _drive(desk, "09:46", 18_002, 18_004, 18_001, 18_003)   # turn attempt -> dies
    _drive(desk, "09:47", 18_000, 18_001, 17_989, 17_990)   # stop bar
    assert t.done
    assert ("stop_realized", "ny:t:1") in desk.execution.calls
    desk.finalize()
    rows = [json.loads(x) for x in (tmp_path / "journal.jsonl").read_text().splitlines()]
    assert rows[0]["exit_reason"] == "stop"
    assert rows[0]["agent_R"] < 0                            # honest -1R-ish loss


def test_session_flatten_overrides_agent(tmp_path):
    """The 15:55 flatten fires regardless of what the agent wants."""
    desk = _desk(tmp_path, ['{"action":"revise","target_r":5.0}'] * 20)
    t = _open_trade(desk)
    _drive(desk, "09:46", 18_002, 18_004, 18_001, 18_003)
    assert t.target == 18_050.0                              # agent set a far target
    desk.on_bar(_ts("15:55"), _bar(18_010, 18_012, 18_008, 18_011),
                pd.DataFrame(), None, [])
    assert t.done
    assert ("close_now", "ny:t:1", "eod") in desk.execution.calls
    desk.finalize()
    rows = [json.loads(x) for x in (tmp_path / "journal.jsonl").read_text().splitlines()]
    assert rows[0]["exit_reason"] == "eod"


def test_rule_j_flip_closes_the_managed_trade(tmp_path):
    desk = _desk(tmp_path, ['{"action":"hold"}'] * 5)
    t = _open_trade(desk)
    _drive(desk, "09:46", 18_002, 18_004, 18_001, 18_003)
    desk.on_position_closed_externally("ny:t:1", "rule_j_flip", _ts("09:50"),
                                       18_006.0, None)
    assert t.done
    desk.finalize()
    rows = [json.loads(x) for x in (tmp_path / "journal.jsonl").read_text().splitlines()]
    assert rows[0]["exit_reason"] == "flip"


def test_stop_tighten_routes_to_broker(tmp_path):
    desk = _desk(tmp_path, ['{"action":"revise","stop_r":0.0,"note":"BE"}'])
    t = _open_trade(desk)
    _drive(desk, "09:46", 18_002, 18_004, 18_001, 18_003)
    assert t.stop == 18_000.0
    assert ("modify_stop", "ny:t:1", 18_000.0) in desk.execution.calls


def test_partial_shrinks_and_routes_qty(tmp_path):
    desk = _desk(tmp_path, ['{"action":"revise","partial_pct":0.5}',
                            '{"action":"hold"}'])
    t = _open_trade(desk)
    _drive(desk, "09:46", 18_002, 18_004, 18_001, 18_003)
    _drive(desk, "09:47", 18_004, 18_006, 18_003, 18_005)   # partial executes
    assert t.partial_done and t.frac == 0.5
    assert ("partial", "ny:t:1", 5) in desk.execution.calls


def test_max_turns_cap(tmp_path):
    desk = _desk(tmp_path, ['{"action":"hold"}'] * 50)
    t = _open_trade(desk)
    # feed events that WOULD trigger turns every bar: giveback etc. Turn cap = 10.
    t.turns = 10
    _drive(desk, "09:46", 18_002, 18_004, 18_001, 18_003)
    assert t.turns == 10                                    # no call went out


def test_journal_schema_matches_the_seed(tmp_path):
    seed = [json.loads(x) for x in
            (ROOT / "runs/live/journal.jsonl").read_text().splitlines() if x.strip()]
    seed_keys = set(seed[0].keys())
    desk = _desk(tmp_path, ['{"action":"exit_now"}'])
    _open_trade(desk)
    _drive(desk, "09:46", 18_002, 18_004, 18_001, 18_003)
    _drive(desk, "09:47", 18_004, 18_005, 18_002, 18_004)
    desk.finalize()
    row = json.loads((tmp_path / "journal.jsonl").read_text().splitlines()[0])
    missing = seed_keys - set(row.keys())
    # flow-at-exit fields are conditional in the reference too (need >=5 tape minutes)
    missing -= {"cvd5_at_exit", "cvd15_at_exit", "opposed_at_exit"}
    assert not missing, f"journal row missing seed fields: {missing}"


# ---------------------------------------------------------------- trade-level alerts
def test_agent_open_and_settle_alert_when_a_sink_is_given(tmp_path):
    alerts = []
    replies = ['{"action":"exit_now","note":"done"}']

    def call_fn(prompt, session, *, cwd, spec=None, timeout=None):
        return (replies.pop(0) if replies else '{"action":"hold"}'), "s1"

    desk = AgentDesk(execution=_Exec(), exit_cfg=None,
                     journal_path=tmp_path / "journal.jsonl",
                     transcripts_dir=tmp_path / "tr", runs_cwd=tmp_path,
                     sync=True, call_fn=call_fn, alert_sink=alerts.append)
    t = _open_trade(desk)
    assert any("AGENT MANAGING" in a for a in alerts)
    _drive(desk, "09:46", 18_002, 18_004, 18_001, 18_003)
    _drive(desk, "09:47", 18_004, 18_005, 18_002, 18_004)
    assert t.done
    assert any("AGENT SETTLED" in a for a in alerts)   # exit_cfg=None here -> no shadow V8


def test_agent_desk_defaults_to_silent_alerts(tmp_path):
    """No alert_sink given (the cert-replay default) -> nothing raises, nothing sent."""
    desk = _desk(tmp_path, ['{"action":"exit_now"}'])
    _open_trade(desk)
    _drive(desk, "09:46", 18_002, 18_004, 18_001, 18_003)
    _drive(desk, "09:47", 18_004, 18_005, 18_002, 18_004)   # must not raise


# ------------------------------------------------------------------ call_claude subprocess
# 2026-08-04 incident: a replay's first agent turn hung the box 3+ hours despite
# call_claude passing timeout=240 — plain subprocess.run(timeout=) only kills the
# immediate process; on Windows `claude` is an npm .cmd shim over a node.exe child
# that survives and keeps the output pipes open, so communicate() never sees EOF.
# These pin the Popen + hard tree-kill replacement so that class of hang can't recur
# silently (nothing in this file exercised the real subprocess path before).

import subprocess as _subprocess  # noqa: E402 — grouped with the section it tests

from src.live.agent_desk import call_claude, _kill_process_tree  # noqa: E402


class _FakeProc:
    def __init__(self, communicate_effects):
        self.pid = 4242
        self._effects = list(communicate_effects)
        self.killed_via_tree = False

    def communicate(self, timeout=None):
        effect = self._effects.pop(0)
        if isinstance(effect, Exception):
            raise effect
        return effect


def test_call_claude_returns_the_result_on_a_clean_call(tmp_path, monkeypatch):
    reply = json.dumps({"result": '{"action":"hold"}', "session_id": "s9"})
    proc = _FakeProc([(reply, "")])
    monkeypatch.setattr(_subprocess, "Popen", lambda *a, **k: proc)
    txt, sid = call_claude("prompt", None, cwd=tmp_path)
    assert txt == '{"action":"hold"}'
    assert sid == "s9"


def test_call_claude_hard_kills_the_process_tree_on_timeout_not_just_the_pid(
        tmp_path, monkeypatch):
    """The exact 2026-08-04 failure: both attempts time out. Must call the tree-kill
    helper (not proc.kill()) and degrade to __ERROR__ (-> hold) rather than hang."""
    proc = _FakeProc([
        _subprocess.TimeoutExpired(cmd="claude", timeout=240),
        ("", ""),                                       # reap after the tree-kill
        _subprocess.TimeoutExpired(cmd="claude", timeout=240),
        ("", ""),
    ])
    killed = []
    monkeypatch.setattr(_subprocess, "Popen", lambda *a, **k: proc)
    monkeypatch.setattr("src.live.agent_desk._kill_process_tree",
                        lambda pid: killed.append(pid))
    txt, sid = call_claude("prompt", "s1", cwd=tmp_path, timeout=1)
    assert killed == [4242, 4242]                       # one hard kill per attempt
    assert txt.startswith("__ERROR__")
    assert "Timeout" in txt
    assert sid == "s1"                                  # session preserved for the retry


def test_call_claude_recovers_if_the_retry_succeeds_after_a_timeout(tmp_path, monkeypatch):
    reply = json.dumps({"result": '{"action":"hold"}', "session_id": "s1"})
    proc = _FakeProc([
        _subprocess.TimeoutExpired(cmd="claude", timeout=240),
        ("", ""),
        (reply, ""),
    ])
    monkeypatch.setattr(_subprocess, "Popen", lambda *a, **k: proc)
    monkeypatch.setattr("src.live.agent_desk._kill_process_tree", lambda pid: None)
    txt, sid = call_claude("prompt", "s1", cwd=tmp_path, timeout=1)
    assert txt == '{"action":"hold"}'


def test_kill_process_tree_uses_taskkill_with_the_force_and_tree_flags_on_windows(
        monkeypatch):
    calls = []
    monkeypatch.setattr(_subprocess, "run", lambda cmd, **k: calls.append(cmd))
    monkeypatch.setattr("src.live.agent_desk.sys.platform", "win32")
    _kill_process_tree(4242)
    assert calls == [["taskkill", "/F", "/T", "/PID", "4242"]]


def test_kill_process_tree_never_raises_even_if_the_pid_is_already_gone(monkeypatch):
    def _boom(cmd, **k):
        raise OSError("no such process")
    monkeypatch.setattr(_subprocess, "run", _boom)
    monkeypatch.setattr("src.live.agent_desk.sys.platform", "win32")
    _kill_process_tree(999999)                          # must not raise
