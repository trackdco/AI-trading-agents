"""Validate a tv-manage row before the orchestrator simulates it.

Two rules are enforced mechanically, both from his rulings:

  1. breakeven is ONLY legal after TP1 has printed (2026-08-16). Before TP1 the
     action is rejected. Measured cost of not enforcing this: day-4 L1 turned a
     +1.776R winner into 0.00R when breakeven was called at +0.08R on a 49pt R.
  2. a stop may only ever tighten, and it may not be set through the market -
     a stop on the wrong side of current price is an immediate exit, not
     protection (day-3 A4).
"""
import sys
sys.path.insert(0, "/Users/barbelldaddy/AI-trading-agents")


def check(action, side, entry, cur_stop, new_stop, tp1_printed, last_price):
    short = str(side).lower().startswith("s")
    errs = []
    if action == "breakeven" and not tp1_printed:
        errs.append("BREAKEVEN BEFORE TP1 - not a legal action. His ruling of 2026-08-16 and "
                    "RUNBOOK section 6: break-even only after TP1 has printed.")
    if new_stop is not None and cur_stop is not None:
        tighter = (new_stop < cur_stop) if short else (new_stop > cur_stop)
        if not tighter and abs(new_stop - cur_stop) > 1e-9:
            errs.append(f"stop widened {cur_stop} -> {new_stop} for a {'short' if short else 'long'}")
    if new_stop is not None and last_price is not None:
        through = (new_stop <= last_price) if short else (new_stop >= last_price)
        if through:
            errs.append(f"stop {new_stop} is THROUGH the market ({last_price}) for a "
                        f"{'short' if short else 'long'} - that is an immediate exit, not protection")
    return (len(errs) == 0), errs


if __name__ == "__main__":
    import json
    a = json.loads(sys.argv[1])
    ok, errs = check(a["action"], a["side"], a["entry"], a.get("cur_stop"), a.get("new_stop"),
                     a.get("tp1_printed", False), a.get("last_price"))
    print(json.dumps({"ok": ok, "errors": errs}, indent=1))
    sys.exit(0 if ok else 1)
