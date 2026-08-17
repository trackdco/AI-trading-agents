import sys, json, os
sys.path.insert(0, "/Users/barbelldaddy/.claude/jobs/2411401a/tmp")
from levelset import levelset
T = "/Users/barbelldaddy/.claude/jobs/2411401a/tmp"
sd, dn = sys.argv[1], sys.argv[2]
cands = json.load(open(f"{T}/cands/{sd}.json"))
p = f"{T}/lsets/{sd}.json"
out = json.load(open(p)) if os.path.exists(p) else {}
for c in cands:
    if c["dec"] in out:
        continue
    out[c["dec"]] = levelset(sd, dn, c["dec"])
    json.dump(out, open(p, "w"), indent=1)
    print(sd, c["dec"], "ok", flush=True)
print(sd, "DONE", len(out))
