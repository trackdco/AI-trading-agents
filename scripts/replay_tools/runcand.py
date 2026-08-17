"""Build one trigger briefing: scanner candidate + saved legend -> mkspec -> mk49.

Usage: runcand.py <run> <sd> <dn> <dec> <cid> <thesis> <macro_out> <fills> \
                  <position_state.json|-> <escalation.json> <levels_closed.json> \
                  [prior_take ...]
Everything carrying judgement is passed in; this file only wires the pieces.
"""
import json, sys, os
T = "/Users/barbelldaddy/.claude/jobs/2411401a/tmp"
sys.path.insert(0, T)
import mkspec, mk49


def main():
    run, sd, dn, dec, cid, thesis, macro, fills = sys.argv[1:9]
    ps = json.load(open(sys.argv[9])) if sys.argv[9] != "-" else {"state": "FLAT"}
    esc = json.loads(sys.argv[10])
    closed = None if sys.argv[11] == "-" else json.loads(sys.argv[11])
    prior = sys.argv[12:]

    cands = json.load(open(f"{T}/cands/{sd}.json"))
    c = next(x for x in cands if x["dec"] == dec)
    legends = json.load(open(f"{T}/{run}_{sd}_legends.json"))
    lg = legends[dec]
    legend = {k: v for k, v in lg.items() if k not in ("cid", "cursor", "bar_start")}

    ov = None
    if os.path.exists(f"{T}/override_{run}_{sd}_{dec.replace(':','')}.json"):
        ov = json.load(open(f"{T}/override_{run}_{sd}_{dec.replace(':','')}.json"))

    spec = mkspec.build(run, sd, dn, c, cid,
                        f"{run}_{sd}_{cid}_{dec.replace(':','')}.png",
                        thesis, macro, legend, lg["bar_start"], int(fills),
                        ps, esc,
                        levels_closed=closed or mkspec.levels_closed_from(c),
                        override=ov)
    json.dump(spec, open(f"{T}/{run}_{sd}_{cid}.json", "w"), indent=1)

    lsets = json.load(open(f"{T}/lsets/{sd}.json"))
    out, fires, lv, cs = mk49.build(spec, lsets[dec], prior)
    print(out)
    print("  outer_band_gate_fires", fires)
    print("  chop_state", cs["state"], "| zone", cs["zone_now"], "|", cs["reason"])
    stale = {n: d for n, d in lv.items() if not d["fresh"]}
    print("  STALE levels:", {n: (d["level"], d["level_visits_this_session"], d["tests_15m_60min"])
                              for n, d in stale.items()} or "none")


if __name__ == "__main__":
    main()
