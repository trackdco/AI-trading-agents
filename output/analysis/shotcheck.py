"""Does every manage briefing actually have the screenshot it names?

A manager whose image is missing decides on the briefing text alone and says so in its
reason - it is not a wrong answer, but it is a degraded one, and nothing in the pipeline
noticed. legendpool serves a frame's LEGEND by cursor across candidates, but the PNG is
named per candidate, so a minute pooled from another cid resolves its numbers and loses
its picture.

Repairs by copying any same-run, same-day, same-minute PNG (identical cursor, so it is the
same chart), and reports anything it cannot repair.

usage: shotcheck.py <run> [--fix]
"""
import glob, json, os, re, shutil, sys

run = sys.argv[1]
fix = "--fix" in sys.argv
SHOTS = "/Users/barbelldaddy/tradingview-mcp/screenshots"
missing, repaired, unrepairable = 0, [], []

for bp in sorted(glob.glob(f"output/briefings/{run}_*_manage.json")):
    b = json.load(open(bp))
    p = b.get("screenshot")
    if not p:
        continue
    if not os.path.isabs(p):
        p = os.path.join(SHOTS, p)
    if os.path.exists(p):
        continue
    missing += 1
    m = re.match(rf"{run}_(\d{{4}}-\d{{2}}-\d{{2}})_([A-Z]\d+)_(\d{{4}})_manage\.png",
                 os.path.basename(p))
    if not m:
        unrepairable.append(os.path.basename(p)); continue
    sd, cid, hhmm = m.groups()
    # A frame is a property of the TAPE and the CURSOR, not of the run or the candidate that
    # captured it, so ANY run's PNG at the same session-day and minute is the same chart.
    # This is frameget's own rule; restricting the search to this run's own prefix was what
    # made eight of these look unrepairable.
    alt = sorted(glob.glob(f"{SHOTS}/*_{sd}_*_{hhmm}_manage.png"))
    if alt and fix:
        shutil.copy(alt[0], p); repaired.append(f"{sd} {cid} {hhmm} <- {os.path.basename(alt[0])}")
    elif alt:
        repaired.append(f"{sd} {cid} {hhmm} (repairable from {os.path.basename(alt[0])})")
    else:
        unrepairable.append(f"{sd} {cid} {hhmm}")

print(f"{run}: {missing} manage briefing(s) name a screenshot that is not on disk")
for r in repaired: print("  REPAIRED " if fix else "  fixable  ", r)
for u in unrepairable: print("  NO SOURCE", u)
