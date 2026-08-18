#!/usr/bin/env python3
"""THE DESK — a local dashboard for the agent stack. No terminal on the screen.

    python -m scripts.desk_server --run w49            # follow a live/lagging book
    python -m scripts.desk_server --run w49 --replay 60  # play a finished book back, 60x
    open http://127.0.0.1:8787

THE BRIDGE, and why nothing in the stack has to change: the run log is
already the event stream. Every decision the stack makes is appended to
`output/books/<run>/<sess_day>_<run>.jsonl` as one structured JSON row, in
order, carrying the agent's own words. So the dashboard is a tail, a socket
and a page — the agents are untouched and do not know it exists.

Because replay and live write the SAME schema, this renders both. A finished
book can be replayed at any speed, which is how you look at a day without a
terminal in the picture.

READ-ONLY BY CONSTRUCTION. The server opens the log files for reading and
never writes to them. The one exception is the KILL SWITCH: pressing it
writes a single `halt` file that the orchestrator checks before every
decision. It cannot place, modify or cancel an order — it can only stop the
stack. That asymmetry is deliberate: the button a human reaches for in a
hurry should only ever be able to make the system do less.
"""
from __future__ import annotations

import argparse
import json
import queue
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = Path(__file__).resolve().parent / "desk" / "index.html"
HALT = ROOT / "output" / "HALT"

SUBS: list[queue.Queue] = []
SUBS_LOCK = threading.Lock()
STATE: dict = {"rows": [], "run": "", "day": ""}


def publish(ev: dict):
    STATE["rows"].append(ev)
    with SUBS_LOCK:
        dead = []
        for q in SUBS:
            try:
                q.put_nowait(ev)
            except queue.Full:
                dead.append(q)
        for q in dead:
            SUBS.remove(q)


def day_files(run: str):
    d = ROOT / "output" / "books" / run
    if not d.is_dir():
        d = ROOT / "output" / "agent_runs"
        return sorted(d.glob(f"*_{run}.jsonl"))
    return sorted(d.glob("*.jsonl"))


def rows_of(p: Path):
    out = []
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return out


def pump_replay(run: str, speed: float):
    """Play a finished book back in order. Speed is rows/second."""
    for p in day_files(run):
        STATE["day"] = p.name[:10]
        for r in rows_of(p):
            r["_day"] = p.name[:10]
            publish(r)
            time.sleep(1.0 / max(speed, 0.1))
    publish({"row": "_end", "note": "book complete"})


def pump_follow(run: str):
    """Tail every day file, emitting new rows as the orchestrator writes them."""
    seen: dict[str, int] = {}
    while True:
        for p in day_files(run):
            rs = rows_of(p)
            n = seen.get(p.name, 0)
            for r in rs[n:]:
                r["_day"] = p.name[:10]
                STATE["day"] = p.name[:10]
                publish(r)
            seen[p.name] = len(rs)
        time.sleep(1.0)


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, ctype, body: bytes):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/" or self.path.startswith("/index"):
            self._send(200, "text/html; charset=utf-8", PAGE.read_bytes())
        elif self.path == "/api/state":
            body = json.dumps({"run": STATE["run"], "day": STATE["day"],
                               "rows": STATE["rows"],
                               "halted": HALT.exists()}).encode()
            self._send(200, "application/json", body)
        elif self.path == "/api/stream":
            q: queue.Queue = queue.Queue(maxsize=2000)
            with SUBS_LOCK:
                SUBS.append(q)
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            try:
                while True:
                    try:
                        ev = q.get(timeout=15)
                        self.wfile.write(b"data: " + json.dumps(ev).encode() + b"\n\n")
                    except queue.Empty:
                        self.wfile.write(b": ping\n\n")
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
            finally:
                with SUBS_LOCK:
                    if q in SUBS:
                        SUBS.remove(q)
        else:
            self._send(404, "text/plain", b"no")

    def do_POST(self):
        if self.path == "/api/halt":
            HALT.parent.mkdir(parents=True, exist_ok=True)
            HALT.write_text(json.dumps({"halted_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                                        "by": "desk kill switch"}))
            publish({"row": "_halt", "note": "KILL SWITCH — halt file written. "
                                             "The orchestrator stops before its next decision."})
            self._send(200, "application/json", b'{"halted":true}')
        elif self.path == "/api/resume":
            if HALT.exists():
                HALT.unlink()
            publish({"row": "_resume", "note": "halt cleared"})
            self._send(200, "application/json", b'{"halted":false}')
        else:
            self._send(404, "text/plain", b"no")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", required=True, help="run prefix, e.g. w49")
    ap.add_argument("--replay", type=float, default=0,
                    help="replay a finished book at N rows/sec (0 = follow live)")
    ap.add_argument("--port", type=int, default=8787)
    a = ap.parse_args()
    STATE["run"] = a.run

    t = threading.Thread(target=pump_replay if a.replay else pump_follow,
                         args=(a.run, a.replay) if a.replay else (a.run,),
                         daemon=True)
    t.start()
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), H)
    print(f"  THE DESK — http://127.0.0.1:{a.port}   run={a.run}"
          f"{'  replay %gx' % a.replay if a.replay else '  following live'}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
