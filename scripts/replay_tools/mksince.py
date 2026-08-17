"""Since-block: price facts only, strictly between two minutes of the traded day.
No characterisation - the orchestrator states the range, never what it means."""
import sys
sys.path.insert(0, "/Users/barbelldaddy/AI-trading-agents")
from scripts.replay_tools.brief04 import agg

def build(dn, frm, to):
    a = agg(dn, frm, to)
    return (f"Since your {frm} read, stated as price facts only: between {frm} and this "
            f"decision minute the session traded a high of {a['high']:.2f} and a low of "
            f"{a['low']:.2f}. All levels in levels_at_decision_BUILD are recomputed as of "
            f"this minute.")

if __name__ == "__main__":
    print(build(*sys.argv[1:4]))
