"""Assemble a trigger spec from the scanner candidate + the chart legend read.

Boilerplate only. Every field that carries judgement - cand_levels, levels_closed,
position_state - is passed IN by the orchestrator; this file invents nothing.
"""
import json, re, sys

LEVEL_MAP = {"own_ma": "bb_ma_2m", "ma15": "bb_ma_15m", "vwap_p1": "vwap_p1",
             "vwap_p2": "vwap_p2", "vwap_m1": "vwap_m1", "vwap_m2": "vwap_m2",
             "VAH": "daily_vah", "VAL": "daily_val", "POC": "daily_poc"}

CAP = {"LONDON": 2, "NY_PRE": 2, "NY_AM": 2}
ENTRIES = {"LONDON": "LONDON runs 03:00-04:59.",
           "NY_PRE": "NY_PRE entries are cut off at 09:10.",
           "NY_AM": "NY_AM runs 09:30-11:00 and the earliest permitted ENTRY is 09:35."}


def scanner_detail(c):
    legs = "; ".join(c["legs"])
    return (f"{c['dec']} {c['dir']}, n={c['n']}, source {c['src']}. {legs}")


def pair_shape(c):
    """The FIRST leg's timeframe + shape, e.g. "2m sequential (+6m)"."""
    m = re.match(r"^\d\d:\d\d\s+(\d+m\s+\S+(?:\s+\([^)]*\))?)", c["legs"][0])
    return m.group(1).strip() if m else c["src"]


def cand_levels_from(c):
    """Union of every level the SCANNER named, in leg order. Mechanical."""
    out = []
    for leg in c["legs"]:
        for tok in re.findall(r"'([^']+)'", leg):
            name = tok.split("@")[0]
            m = LEVEL_MAP.get(name, name)
            if m not in out:
                out.append(m)
    return out


def build(prefix, sd, dn, c, cid, shot, thesis_path, macro_path, legend,
          last_bar_epoch, fills, position_state, escalation, levels_closed=None,
          extra=None, override=None):
    w = c["window"]
    s = {"sd": sd, "dn": dn, "dec": c["dec"], "cid": cid, "window": w, "prefix": prefix,
         "shot": shot, "thesis_path": thesis_path, "chart_levels": legend,
         "cand_levels": cand_levels_from(c),
         "side": "short" if c["dir"] == "DOWN" else "long",
         "pair_shape": pair_shape(c),
         "levels_closed": levels_closed or [],
         "fills": fills, "cap_written": CAP[w], "escalation": escalation,
         "macro_path": macro_path, "news_blackout": False,
         "scanner_detail": scanner_detail(c),
         "position_state": position_state,
         "extra": dict({"news_note": "news_blackout false. The calendar for "
                        f"{dn} is EMPTY in all three windows.",
                        "ENTRY_CUTOFF_NOTE": ENTRIES[w] +
                        f" This decision minute is {c['dec']}. Stated as a mechanical "
                        "fact; the gate is yours to apply."}, **(extra or {})),
         "last_bar_epoch": last_bar_epoch}
    if override:
        s["preflight_override"] = override
    return s

PRETTY = {"own_ma": "own {tf} BB MA", "ma15": "15m BB MA", "vwap_p1": "VWAP+1",
          "vwap_p2": "VWAP+2", "vwap_m1": "VWAP-1", "vwap_m2": "VWAP-2",
          "VAH": "daily VAH", "VAL": "daily VAL", "POC": "daily POC"}


def levels_closed_from(c):
    """Human-readable version of the SCANNER's closed-through list. Mechanical:
    the same tokens cand_levels_from reads, rendered for the briefing text."""
    out = []
    for leg in c["legs"]:
        tf = re.match(r"^\d\d:\d\d\s+(\d+m)", leg)
        tf = tf.group(1) if tf else "2m"
        body = leg.split("rej=")[0]
        for tok in re.findall(r"'([^']+)'", body):
            name, _, when = tok.partition("@")
            txt = PRETTY.get(name, name).format(tf=tf)
            if when:
                txt += f" (closed at {when})"
            if txt not in out:
                out.append(txt)
    return out
