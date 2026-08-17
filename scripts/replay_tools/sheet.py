"""Trade-by-trade sheet for a run. THE deliverable.

Not a scoreboard. For every candidate: the agent's own words verbatim, the
chop_state and level_visits in force, and - for fills - each management call in
its own words and the exit. Reads the live books, or the sealed logs by path.

Usage: sheet.py <run> [books_dir] > SHEET.md
"""
import json, sys, os, glob

ROOT = "/Users/barbelldaddy/AI-trading-agents"


def rows(run, d):
    out = []
    for p in sorted(glob.glob(f"{d}/*_{run}.jsonl")):
        sd = os.path.basename(p).split("_")[0]
        out.append((sd, [json.loads(l) for l in open(p)]))
    return out


def q(s):
    """Verbatim, as a markdown blockquote."""
    if not s:
        return "_(none given)_"
    return "\n".join("> " + ln for ln in str(s).split("\n"))


def fmt_cs(cs):
    if not cs:
        return "_not recorded_"
    return (f"`{cs.get('state')}` · zone `{cs.get('zone_now')}` · "
            f"range {cs.get('range_width')}pt over {cs.get('hours_held')}h")


def fmt_lv(lv, named=None):
    """Show what BINDS: every stale level, plus the level the agent actually named.
    Dumping all 26 buries the two or three that matter."""
    if not lv:
        return "_not recorded_"
    rows = {n: d for n, d in lv.items() if not n.startswith("_")}
    if not rows:
        return "_not recorded_"
    stale = {n: d for n, d in rows.items() if not d.get("fresh")}
    show = dict(stale)
    if named:
        for n, d in rows.items():
            if n in str(named) or str(named) in n:
                show[n] = d
    parts = []
    for n, d in show.items():
        tag = "FRESH" if d.get("fresh") else "STALE"
        parts.append(f"`{n}` {d.get('price')} — visit {d.get('visits')}, "
                     f"{d.get('tests_15m_60min')} tests/60m → **{tag}**")
    if not parts:
        parts.append(f"all {len(rows)} levels FRESH — 0.4.8 imposes no grade cap here")
    else:
        parts.append(f"_({len(rows)} levels supplied, {len(stale)} stale)_")
    s = "<br>".join(parts)
    if lv.get("_note"):
        s += f"<br>_{lv['_note']}_"
    return s


def main():
    run = sys.argv[1]
    d = sys.argv[2] if len(sys.argv) > 2 else f"{ROOT}/output/books/{run}"
    print(f"# {run} — trade-by-trade sheet\n")
    print("Every fill, every management call, every pass — in the agents' own words, "
          "with the `chop_state` and `level_visits` that were in force at each.\n")
    for sd, rs in rows(run, d):
        hdr = next((r for r in rs if r.get("row") == "run_header"), {})
        print(f"\n---\n\n## session-day {sd} → trades {hdr.get('trades_calendar_day','?')}\n")
        for w in ("LONDON", "NY_PRE", "NY_AM"):
            wr = [r for r in rs if r.get("window") == w]
            if not wr:
                continue
            print(f"### {w}\n")
            th = next((r for r in wr if r.get("row") == "thesis"), None)
            if th:
                o = th["output"]
                tg = ", ".join(f"{t['level']} {t['price']}" for t in (o.get("targets") or []))
                print(f"**Thesis {th.get('thesis_version','')}** — bias `{o.get('bias')}`"
                      f"{(' → ' + tg) if tg else ''}\n")
                print(q(o.get("reasoning")), "\n")
            for r in wr:
                t = r.get("row")
                # SUPERSEDED rows are retained in the book as evidence of a
                # correction, but they are not the scored decision and must not
                # appear in the sheet he reads.
                if r.get("SUPERSEDED"):
                    continue
                if t in ("trigger", "manage") and "output" not in r:
                    continue
                if t == "trigger":
                    o = r["output"]
                    dec = o.get("decision")
                    mark = {"take_full": "🟢 TAKE_FULL", "take_light": "🟡 TAKE_LIGHT",
                            "pass": "⚪ PASS"}.get(dec, dec)
                    prov = " · _PROVISIONAL, pending Tier 1_" if r.get(
                        "decision_is_provisional") else ""
                    seq = f"  \n_{r['sequence']}_" if r.get("sequence") else ""
                    print(f"#### {r['candidate_id']} · {r['decision_minute'].split('T')[-1]} "
                          f"· {mark}"
                          + (f" · conviction **{o.get('conviction')}**" if dec != "pass" else "")
                          + prov + seq + "\n")
                    rl = o.get("rejected_level") or {}
                    print(f"- **level:** {rl.get('level')} @ {rl.get('price')}")
                    if dec != "pass":
                        print(f"- **entry:** {o.get('entry_type')} {o.get('entry')} · "
                              f"**stop:** {o.get('stop')} · **targets:** "
                              + ", ".join(f"{x['level']} {x['price']}"
                                          for x in (o.get("targets") or [])))
                    if o.get("constraints_failed"):
                        print(f"- **constraints failed:** `{'`, `'.join(o['constraints_failed'])}`")
                    print(f"- **chop_state:** {fmt_cs(r.get('chop_state_in_force'))}")
                    print(f"- **level_visits:** {fmt_lv(r.get('level_visits_in_force'), (rl or {}).get('level'))}")
                    print("\n**its reason, verbatim:**\n")
                    print(q(o.get("reason")), "\n")
                    esc = o.get("escalation")
                    if esc:
                        print(f"- ⚡ **ESCALATED** `{esc.get('level')}` "
                              f"{esc.get('direction')} — thesis_stale\n")
                        print("**why the standing thesis could not accommodate it:**\n")
                        print(q(esc.get("why_thesis_cannot_accommodate")), "\n")
                        if o.get("entry"):
                            print(f"- the plan it carried: {o.get('entry_type')} "
                                  f"{o.get('entry')} · stop {o.get('stop')} · target "
                                  + ", ".join(f"{x['level']} {x['price']}"
                                              for x in (o.get("targets") or []))
                                  + f" · conviction {o.get('conviction')}\n")
                    if r.get("escalation_outcome"):
                        print(f"- **Tier 1 returned:** {r['escalation_outcome']}\n")
                    if r.get("grade_note"):
                        print(f"_{r['grade_note']}_\n")
                    if r.get("contract_comparison"):
                        cc = r["contract_comparison"]
                        print("> **contract comparison** — "
                              f"{cc.get('what_changed','')}\n")
                elif t == "fill":
                    print(f"**FILL {r['candidate_id']}** — {r['side']} {r['fill_price']} at "
                          f"{r['filled_at']} · stop {r['stop']} · R = {r['original_r_pts']}pt"
                          + (" · `beyond_written_cap`" if r.get("beyond_written_cap") else "") + "\n")
                elif t == "manage":
                    o = r["output"]
                    print(f"##### manage {r['candidate_id']} @ "
                          f"{r['decision_minute'].split('T')[-1]} — **{o.get('action')}**"
                          f"  _(called on: {r.get('reason_for_call')})_\n")
                    if o.get("partial_pct"):
                        print(f"- partial {o['partial_pct']}%")
                    if r.get("stop_change") and r["stop_change"].get("direction") != "unchanged":
                        sc = r["stop_change"]
                        print(f"- stop {sc.get('from')} → {sc.get('to')}")
                    print("\n**in its own words:**\n")
                    print(q(o.get("reason")), "\n")
                elif t == "exit":
                    print(f"**EXIT {r['candidate_id']}** — {r.get('exit_price')} at "
                          f"{r.get('exit_minute')} · **{r.get('r_multiple')}R** "
                          f"({r.get('exit_reason')})\n")
                    if r.get("counterfactuals"):
                        print(f"_counterfactual: {json.dumps(r['counterfactuals'])}_\n")
                elif t == "window_close":
                    fr = r.get("window_r_full_target_as_run")
                    bl = r.get("window_r_blended_as_run")
                    print(f"_**{w} closed** {fr}R full-target · {bl}R blended (75/25) — "
                          f"{r.get('candidates')} candidates, {r.get('takes')} takes, "
                          f"{r.get('fills')} fills, {r.get('passes')} passes_\n")
                elif t == "open_question":
                    print(f"> ⚠️ **open question ({r.get('topic')})** — {r.get('question')}\n")
                elif t == "orchestrator_error":
                    print(f"> ⛔ **orchestrator error** — {r.get('decision', r.get('what'))}\n")


if __name__ == "__main__":
    main()
