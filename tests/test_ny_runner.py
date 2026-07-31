"""NYRunner — the detector -> orders -> lane -> verdict join, decided per bar.

The lane and scorer are proven elsewhere; what this file pins is the ORCHESTRATION:
the resting rule (an order rests exactly while a fill right now would be admissible),
dormancy through the 09:30-09:40 gap and revival in gold (the book counts a pre trigger's
gold fill as a gold trade), replace-with-freshest sizing, the struct-event join into the
elite tier, the scratch race, and the hard drop at 10:30.
"""
from __future__ import annotations

import json
from types import SimpleNamespace

import pandas as pd
import pytest

from src.canon.ny_lane import NYLane
from src.canon.scorer_ny import LUCID
from src.live.ny_runner import NYRunner, bracket_for

NY = "America/New_York"
DAY = "2026-04-20"


def _ts(hm: str):
    return pd.Timestamp(f"{DAY} {hm}", tz=NY)


def _feats(**over) -> dict:
    f = {"dep_thick": 5.0, "dep_wall_below_d": 8.0, "dep_wall_above_d": 6.0,
         "dep_wall_below_sz": 9.0, "dep_wall_above_sz": 9.0,
         "ent_vs_vwap_sd_dir": 0.5, "fill_delta_conf": 1, "d15_conf": 1,
         "trigdens_30": 20.0, "bp5opp": 0, "lon_slope_d": 0.0,
         "on_extreme_age_day": 500.0}
    f.update(over)
    return f


class FakeIngestor:
    """Feature dict is mutable mid-test so admissibility can flip while an order rests."""
    def __init__(self, feats):
        self.feats = feats

    def feature_row(self, fill_ts, entry, direction, trigger_times=None):
        return dict(self.feats)


def _trigger(hm="09:45", direction="long", entry=18_000.10, stop=17_989.90,
             level_stack=""):
    return SimpleNamespace(ts=str(_ts(hm)), direction=direction, entry_ref=entry,
                           stop_ref=stop, close=entry + (5 if direction == "long" else -5),
                           level_stack=level_stack)


def _runner(feats=None, buffer=5_000.0):
    ing = FakeIngestor(feats if feats is not None else _feats())
    r = NYRunner(lane=NYLane(ingestor=ing, profile=LUCID))
    r.start_day(DAY, buffer=buffer)
    return r, ing


# ---------------------------------------------------------------- bracket
def test_bracket_is_the_engines_e3_derivation():
    """limit = tick-rounded entry_ref, stop = tick-rounded stop_ref — the form the book's
    `risk` column was measured in. This closes the 28% reference-level trap at the source."""
    lim, stop = bracket_for(_trigger(entry=18_000.10, stop=17_989.90))
    assert lim == 18_000.00 and stop == 17_990.00


# ---------------------------------------------------------------- the resting rule
def test_admissible_trigger_places_with_the_verdicts_size():
    r, _ = _runner()
    acts = r.on_trigger(_trigger())
    assert [a["action"] for a in acts] == ["place"]
    assert acts[0]["size"] == acts[0]["verdict"]["micros"] >= 1
    assert r.status()["resting"] == 1


def test_refused_trigger_does_not_place_but_stays_a_candidate():
    r, ing = _runner(_feats(dep_wall_above_d=float("nan")))     # gold D gate fails
    assert r.on_trigger(_trigger()) == []
    assert r.status()["candidates"] == 1 and r.status()["resting"] == 0
    # the wall appears -> the next bar re-admits it (replace-with-freshest, both directions)
    ing.feats = _feats()
    acts = r.on_bar(_ts("09:46"), high=18_010.0, low=18_005.0)
    assert [a["action"] for a in acts] == ["place"]


def test_budget_gates_fills_not_resting_orders():
    """The book's semantics, kept deliberately: the budget counts realized + IN-FLIGHT
    (filled) risk, never resting orders — L1 rested every trigger's order and the verdict
    gated at the FILL. So multiple orders may rest even if jointly over-budget; what must
    hold is that once fills consume the room, (a) the next bar PULLS the survivors, and
    (b) a fill that races the pull is SCRATCHED, never a silent over-budget position."""
    r, ing = _runner()
    refs = [r.on_trigger(_trigger())[0],
            r.on_trigger(_trigger(hm="09:46"))[0],
            r.on_trigger(_trigger(hm="09:46"))[0],
            r.on_trigger(_trigger(hm="09:46"))[0]]
    assert r.status()["resting"] == 4                    # all rest: $225 each vs $800 budget
    for v in refs[:3]:                                   # three fills = $675 in flight
        assert r.on_fill(v["ref"], _ts("09:47"), v["size"])["action"] == "commit"
    # (a) the fourth no longer fits ($675 + $225 > $800): the next bar pulls it
    acts = r.on_bar(_ts("09:48"), high=18_010.0, low=18_005.0)
    pulls = [x for x in acts if x["action"] == "cancel" and x["ref"] == refs[3]["ref"]]
    assert pulls and "budget_exhausted" in pulls[0]["why"]
    # (b) and if the exchange had filled it before the pull landed, it scratches
    r2, _ = _runner()
    vs = [r2.on_trigger(_trigger(hm="09:46"))[0] for _ in range(4)]
    for v in vs[:3]:
        r2.on_fill(v["ref"], _ts("09:47"), v["size"])
    res = r2.on_fill(vs[3]["ref"], _ts("09:47"), vs[3]["size"])
    assert res["action"] == "scratch" and "budget_exhausted" in res["why"]


def test_gap_dormancy_and_gold_revival():
    """A pre-window trigger's order comes down for the 09:30-09:40 gap (a fill there is
    inadmissible) and comes back at the gold evaluation — the book counts that gold fill."""
    r, _ = _runner()
    acts = r.on_trigger(_trigger(hm="09:25", entry=18_000.0, stop=17_990.0))
    # pre-market long with a wall BELOW (behind) -> W fails... use a W-clean feature set:
    r2, ing2 = _runner(_feats(dep_wall_below_d=float("nan")))   # no wall behind: W ok
    acts = r2.on_trigger(_trigger(hm="09:25"))
    assert [a["action"] for a in acts] == ["place"]
    # 09:29 bar -> next fill minute 09:30 = the gap -> pull it
    acts = r2.on_bar(_ts("09:29"), high=18_010.0, low=18_005.0)
    assert [a["action"] for a in acts] == ["cancel"]
    assert "outside_window" in acts[0]["why"]
    # through the gap it stays down
    assert r2.on_bar(_ts("09:35"), high=18_010.0, low=18_005.0) == []
    # 09:39 bar -> next fill minute 09:40 = gold opens; D needs a wall ahead
    ing2.feats = _feats()                                        # gold-clean features
    acts = r2.on_bar(_ts("09:39"), high=18_010.0, low=18_005.0)
    assert [a["action"] for a in acts] == ["place"], "the freshest evaluation wins"


def test_hard_drop_at_the_gold_window_end():
    r, _ = _runner()
    r.on_trigger(_trigger(hm="10:25"))
    acts = r.on_bar(_ts("10:29"), high=18_010.0, low=18_005.0)   # next minute = 10:30
    assert [a["action"] for a in acts] == ["cancel"]
    assert acts[0]["why"] == "no_window_ahead"
    assert r.status()["candidates"] == 0, "nothing ahead is admissible — dropped for good"


def test_resize_follows_the_freshest_evaluation():
    r, _ = _runner()
    a = r.on_trigger(_trigger())[0]
    assert a["verdict"]["conviction"] == 1.5 and a["size"] == 12    # score 6 -> 1.5x, base $160
    # soft de-risk trips: realized loss at the trigger -> size halves on the next bar
    r.lane.scorer._realized = -300.0                                # <= -280 soft
    acts = r.on_bar(_ts("09:46"), high=18_010.0, low=18_005.0)
    assert [x["action"] for x in acts] == ["modify_size"]
    assert acts[0]["size"] < a["size"]


# ---------------------------------------------------------------- struct event -> elite
def test_struct_event_joins_from_the_watch_into_the_elite_tier():
    """The full join this runner exists for: the level breaks while the order rests, and the
    fill-minute verdict carries elite 2.0x."""
    stack = json.dumps([["vwap_mid", 18_010.0, "vwap"]])         # away-side level (long)
    r, _ = _runner()
    a = r.on_trigger(_trigger(level_stack=stack))[0]
    assert a["verdict"]["conviction"] == 1.5, "no struct evidence yet — not elite"
    # price touches the level and runs 5+ pts beyond it: 'broke'
    r.on_bar(_ts("09:46"), high=18_016.0, low=18_008.0)
    res = r.on_fill(a["ref"], _ts("09:47"), a["size"])
    assert res["action"] == "commit"
    assert res["verdict"]["conviction"] == 2.0 and res["verdict"]["elite"]
    # drift is reported, never silently resized: resting size was the 1.5x size
    assert res["size_drift"] == a["size"] - res["verdict"]["micros"]


def test_rejected_level_never_escalates():
    stack = json.dumps([["vwap_mid", 18_010.0, "vwap"]])
    r, _ = _runner()
    a = r.on_trigger(_trigger(level_stack=stack))[0]
    r.on_bar(_ts("09:46"), high=18_010.2, low=18_001.0)          # touched, 8+ back: rejected
    res = r.on_fill(a["ref"], _ts("09:47"), a["size"])
    assert res["verdict"]["conviction"] < 2.0


# ---------------------------------------------------------------- fills, scratches, exits
def test_fill_commits_and_exit_realizes():
    r, _ = _runner()
    a = r.on_trigger(_trigger())[0]
    res = r.on_fill(a["ref"], _ts("09:47"), a["size"])
    assert res["action"] == "commit" and res["size_drift"] == 0
    assert r.status()["open_positions"] == 1
    r.on_position_closed(a["ref"], pl=-150.0)
    st = r.status()
    assert st["open_positions"] == 0 and st["realized"] == pytest.approx(-150.0)


def test_fill_refused_at_the_fill_minute_is_a_scratch_not_a_silent_position():
    r, ing = _runner()
    a = r.on_trigger(_trigger())[0]
    ing.feats = _feats(dep_wall_above_d=float("nan"))            # the wall vanished
    res = r.on_fill(a["ref"], _ts("09:47"), a["size"])
    assert res["action"] == "scratch" and "gold_no_wall_ahead" in res["why"]
    assert r.status()["open_positions"] == 0, "a scratched fill must not consume budget"


def test_fill_for_a_pulled_order_is_a_scratch():
    r, ing = _runner()
    a = r.on_trigger(_trigger())[0]
    ing.feats = _feats(dep_wall_above_d=float("nan"))
    r.on_bar(_ts("09:46"), high=18_010.0, low=18_005.0)          # pulled
    res = r.on_fill(a["ref"], _ts("09:47"), a["size"])           # exchange raced the cancel
    assert res["action"] == "scratch"


def test_filled_candidate_is_never_reconciled_again():
    """A filled candidate is a position. Re-evaluating it as if still pending would try to
    re-place a filled order — caught in review before it ever ran."""
    r, ing = _runner()
    a = r.on_trigger(_trigger())[0]
    r.on_fill(a["ref"], _ts("09:47"), a["size"])
    ing.feats = _feats(dep_wall_above_d=float("nan"))            # would refuse if re-asked
    assert r.on_bar(_ts("09:48"), high=18_010.0, low=18_005.0) == []
    r.on_position_closed(a["ref"], pl=50.0)                      # still cleanly closable


def test_elite_slot_survives_a_scratch():
    """A scratched elite fill must not burn the day's 2.0x slot — commit is what spends it."""
    stack = json.dumps([["vwap_mid", 18_010.0, "vwap"]])
    r, ing = _runner()
    a = r.on_trigger(_trigger(level_stack=stack))[0]
    r.on_bar(_ts("09:46"), high=18_016.0, low=18_008.0)          # broke -> elite-eligible
    ing.feats = _feats(dep_wall_above_d=float("nan"))
    assert r.on_fill(a["ref"], _ts("09:47"), a["size"])["action"] == "scratch"
    ing.feats = _feats()
    b = r.on_trigger(_trigger(hm="09:50", level_stack=stack))[0]
    r.on_bar(_ts("09:51"), high=18_016.0, low=18_008.0)
    res = r.on_fill(b["ref"], _ts("09:52"), b["size"])
    assert res["verdict"]["conviction"] == 2.0, "the slot was still available"


def test_trigger_times_accumulate_for_trigdens():
    r, _ = _runner()
    for hm in ("09:41", "09:43", "09:45"):
        r.on_trigger(_trigger(hm=hm))
    assert r.status()["triggers_today"] == 3


def test_day_discipline():
    r, _ = _runner()
    with pytest.raises(RuntimeError):
        r.on_trigger(SimpleNamespace(ts="2026-04-21 09:45:00-04:00", direction="long",
                                     entry_ref=1.0, stop_ref=0.5, close=1.0,
                                     level_stack=""))
    fresh = NYRunner(lane=NYLane(ingestor=FakeIngestor(_feats()), profile=LUCID))
    with pytest.raises(RuntimeError):
        fresh.on_trigger(_trigger())
