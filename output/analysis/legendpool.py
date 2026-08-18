"""A pool of captured chart legends, indexed by CURSOR EPOCH across every run.

A legend is a reading of the chart at one cursor. The cursor epoch fixes the tape day and
the minute, so a frame captured for w49, j49 or wr1 at cursor C is the same frame wr2 needs
at cursor C - identical bars, identical indicators, identical grid. Pooling them means a
manage call whose minute any earlier run already visited needs no live MCP navigation, which
is the slowest step in the loop and the one that produced wr1's wrong-tape-day frames.

cursor(dec) = anchor_0300 + (mins(dec) - 180) * 60 - 1

usage:  legendpool.py index                       -> report pool size
        legendpool.py get <dn> <HH:MM> [HH:MM...] -> emit a capture file for those minutes
"""
import glob, json, os, sys

T = "/Users/barbelldaddy/.claude/jobs/2411401a/tmp"
# Tape-day 03:00 ET anchors, DERIVED from the capture artefacts rather than typed. They were
# typed once and the jr1 values were wrong, so every jr1 manage frame missed the pool and looked
# like it needed a live capture pass. A legend file keys each frame by its wall-clock minute and
# carries that frame's cursor epoch, so the anchor falls straight out:
#     anchor = cursor - (mins(minute) - 180) * 60 + 1
# Same principle as mkps/mkesc: read it off the artefacts, never retype it.
NEXT_DAY = {"2026-05-31": "2026-06-01", "2026-06-01": "2026-06-02", "2026-06-02": "2026-06-03",
            "2026-06-03": "2026-06-04", "2026-06-04": "2026-06-05",
            "2026-06-21": "2026-06-22", "2026-06-22": "2026-06-23", "2026-06-23": "2026-06-24",
            "2026-06-24": "2026-06-25", "2026-06-25": "2026-06-26"}


def _derive_anchors():
    import collections
    votes = collections.defaultdict(collections.Counter)
    for path in glob.glob(f"{T}/*_legends.json"):
        base = os.path.basename(path)
        parts = base.split("_")
        if len(parts) < 3:
            continue
        sd = parts[1]
        if sd not in NEXT_DAY:
            continue
        try:
            d = json.load(open(path))
        except Exception:
            continue
        for k, v in (d.get("frames", d) or {}).items():
            if not isinstance(v, dict) or "cursor" not in v or ":" not in k:
                continue
            try:
                m = int(k[:2]) * 60 + int(k[3:])
            except ValueError:
                continue
            votes[NEXT_DAY[sd]][int(v["cursor"]) - (m - 180) * 60 + 1] += 1
    return {dn: c.most_common(1)[0][0] for dn, c in votes.items() if c}


ANCHOR = _derive_anchors()

NEED = ("bb_basis_2m_last_completed_plot", "vwap", "vwap_p1", "vwap_m1")

# Two capture schemas exist on disk: the flattened one written by the candidate pass, and the
# raw nested MCP shape written by the manage pass. Same numbers, different key names.
def _num(x):
    """Captures store numbers three ways: float, "30719.21", and "30,719.21"."""
    if x is None or isinstance(x, (int, float)):
        return x
    try:
        return float(str(x).replace(",", "").strip())
    except ValueError:
        return None


def _band(vw, *names):
    """Sigma bands are keyed "+1sigma" in some captures and "+1\u03c3" in others."""
    for n in names:
        if n in vw:
            return _num(vw[n])
    return None


def normalise(v):
    if all(f in v for f in NEED):
        return v
    bb = v.get("bollinger_bands") or {}
    vw = v.get("vwap_deviation_bands") or {}
    if not (bb and vw):
        return None
    out = {k: v[k] for k in ("cid", "cursor", "bar_start", "status", "screenshot") if k in v}
    out.update({
        "bb_basis_2m_last_completed_plot": _num(bb.get("Basis")),
        "bb_upper_2m": _num(bb.get("Upper")), "bb_lower_2m": _num(bb.get("Lower")),
        "vwap": _num(vw.get("VWAP")),
        "vwap_p1": _band(vw, "+1sigma", "+1\u03c3"), "vwap_m1": _band(vw, "-1sigma", "-1\u03c3"),
        "vwap_p2": _band(vw, "+2sigma", "+2\u03c3"), "vwap_m2": _band(vw, "-2sigma", "-2\u03c3"),
        "vwap_p3": _band(vw, "+3sigma", "+3\u03c3"), "vwap_m3": _band(vw, "-3sigma", "-3\u03c3"),
        "read_at": v.get("read_at"),
    })
    return out if all(out.get(f) is not None for f in NEED) else None


def cursor(dn, dec):
    m = int(dec[:2]) * 60 + int(dec[3:])
    return ANCHOR[dn] + (m - 180) * 60 - 1


def pool():
    """cursor epoch -> legend dict, from every capture artefact on disk."""
    out = {}
    pats = ["capture_out_*.json", "*_legends.json", "*_mng_all.json", "*_frames*.json"]
    for pat in pats:
        for p in glob.glob(f"{T}/{pat}"):
            if "QUARANTINE" in p:
                continue          # wrong-tape-day frames, deliberately excluded
            try:
                d = json.load(open(p))
            except Exception:
                continue
            frames = d.get("frames", d)
            if not isinstance(frames, dict):
                continue
            for k, v in frames.items():
                if not isinstance(v, dict) or "cursor" not in v:
                    continue
                if str(v.get("status", "OK")).upper() not in ("OK", "NONE"):
                    continue
                n = normalise(v)
                if n is None:
                    continue
                out.setdefault(int(v["cursor"]), (n, os.path.basename(p)))
    return out


def get(dn, decs):
    p = pool()
    frames, misses, prov = {}, [], {}
    for dec in decs:
        c = cursor(dn, dec)
        if c in p:
            v, src = p[c]
            f = dict(v)
            f["_pooled_from"] = src
            frames[dec] = f
            prov[dec] = src
        else:
            misses.append(dec)
    return frames, misses, prov


if __name__ == "__main__":
    if sys.argv[1] == "index":
        p = pool()
        print(f"legend pool: {len(p)} distinct cursors")
    else:
        dn, decs = sys.argv[2], sys.argv[3:]
        frames, misses, prov = get(dn, decs)
        print(json.dumps({"frames": frames}, indent=1))
        print(f"# hit {len(frames)}/{len(decs)}  MISSING={misses}", file=sys.stderr)
