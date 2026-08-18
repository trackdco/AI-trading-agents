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
# tape-day 03:00 ET anchors
ANCHOR = {
    "2026-06-01": 1780635600, "2026-06-02": 1780722000, "2026-06-03": 1780808400,
    "2026-06-04": 1780894800, "2026-06-05": 1780981200,
    "2026-06-22": 1782111600, "2026-06-23": 1782198000, "2026-06-24": 1782284400,
    "2026-06-25": 1782370800, "2026-06-26": 1782457200,
}
NEED = ("bb_basis_2m_last_completed_plot", "vwap", "vwap_p1", "vwap_m1")

# Two capture schemas exist on disk: the flattened one written by the candidate pass, and the
# raw nested MCP shape written by the manage pass. Same numbers, different key names.
def normalise(v):
    if all(f in v for f in NEED):
        return v
    bb = v.get("bollinger_bands") or {}
    vw = v.get("vwap_deviation_bands") or {}
    if not (bb and vw):
        return None
    out = {k: v[k] for k in ("cid", "cursor", "bar_start", "status", "screenshot") if k in v}
    out.update({
        "bb_basis_2m_last_completed_plot": bb.get("Basis"),
        "bb_upper_2m": bb.get("Upper"), "bb_lower_2m": bb.get("Lower"),
        "vwap": vw.get("VWAP"), "vwap_p1": vw.get("+1sigma"), "vwap_m1": vw.get("-1sigma"),
        "vwap_p2": vw.get("+2sigma"), "vwap_m2": vw.get("-2sigma"),
        "vwap_p3": vw.get("+3sigma"), "vwap_m3": vw.get("-3sigma"),
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
