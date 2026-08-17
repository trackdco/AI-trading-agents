"""Derive cursor and 2m bar-start epochs for a session-day from one verified anchor.

The cursor convention has held on every capture of this run: replay_start(dec) leaves
the chart at dec-1s, and the last COMPLETE 2m bar starts at grid_2m(dec)-2min. These
are DERIVED, not assumed safe - preflight's cursor check re-derives the expected
bar-start independently and is a hard gate, so an arithmetic slip halts the build
rather than reaching an agent.
"""
def mins(hhmm):
    return int(hhmm[:2]) * 60 + int(hhmm[3:5])

def make(anchor_epoch_at_0300):
    """anchor_epoch_at_0300 = epoch of 03:00:00 ET on the traded day."""
    def cursor(dec):
        return anchor_epoch_at_0300 + (mins(dec) - 180) * 60 - 1
    def bar_start(dec):
        t = mins(dec)
        g = t if t % 2 == 0 else t - 1          # grid_2m(dec)
        return anchor_epoch_at_0300 + ((g - 2) - 180) * 60
    return cursor, bar_start
