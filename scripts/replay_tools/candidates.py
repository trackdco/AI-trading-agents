"""Merge two_level_check + rejscan into one clustered candidate list per window."""
import sys, subprocess, re, json
V="/Users/barbelldaddy/AI-trading-agents/.venv/bin/python"
R="/Users/barbelldaddy/AI-trading-agents"
WIN={"LONDON":(180,299),"NY_PRE":(480,569),"NY_AM":(570,660)}
def mins(s):
    h,m=s.split(":"); return int(h)*60+int(m)
def run(cmd,cwd=R):
    return subprocess.run(cmd,shell=True,capture_output=True,text=True,cwd=cwd).stdout
def collect(day):
    out=[]
    tl=run(f"{V} -m scripts.two_level_check {day} ALL")
    for ln in tl.splitlines():
        m=re.match(r"\s+(\d\d:\d\d) (\d)m (UP|DOWN)\s+O\s*([\d.]+) C\s*([\d.]+)\s+(\S+(?: \(\S+\))?)\s+\[(.*?)\](.*)$", ln)
        if not m: continue
        start,tf,d,o,c,shape,lv,tail=m.groups()
        rej=re.search(r"rejected \[(.*?)\]",tail)
        out.append({"src":"two_level","start":start,"tf":int(tf),"dir":d,"open":float(o),"close":float(c),
                    "shape":shape.strip(),"levels":[x.strip() for x in lv.split(",")],
                    "rejected":[x.strip() for x in rej.group(1).split(",")] if rej else [],
                    "dec":mins(start)+int(tf)})
    for tf in (2,3):
        rj=run(f"{V} -m scripts.replay_tools.rejscan {day} {tf}")
        for ln in rj.splitlines():
            m=re.match(r"\s+(\d\d:\d\d) (\w+)\s+(UP|DOWN) own_ma\s+([\d.]+) C ([\d.]+) vol\s+(\d+) \| rejected: (.*?) \| same-candle 2nd: (\[.*\])", ln)
            if not m: continue
            t,win,d,ma,c,vol,rej,snd=m.groups()
            out.append({"src":"rejscan","start":t,"tf":tf,"dir":d,"close":float(c),"own_ma":float(ma),
                        "vol":int(vol),"rejected_detail":rej,"second":snd,"dec":mins(t)})
    return out
def cluster(cands, window_min=3):
    """Group 2m/3m duplicates that describe the same move.

    THE BUG THIS REPLACES: the first version bucketed by dec//2*2, which rounds a
    decision minute DOWN to the even 2m boundary. A 3m bar starting 09:42 closes at
    09:45; bucketing it to 09:44 presented its close one minute before it existed.
    That is a lookahead leak, and it reached two briefings before a trigger agent
    refused to trade on one of them.

    The rule now: a cluster's decision minute is the MAXIMUM of its members' own
    decision minutes, never the minimum and never a rounded-down boundary. Waiting
    a minute costs a minute of price; showing an unclosed bar costs the whole run.
    """
    out=[]
    for c in sorted(cands,key=lambda x:(x["dec"],x["dir"])):
        placed=False
        for cl in out:
            if cl["dir"]==c["dir"] and abs(cl["dec_min"]-c["dec"])<=window_min:
                cl["members"].append(c)
                cl["dec_min"]=max(cl["dec_min"],c["dec"])   # never earlier than any member
                placed=True; break
        if not placed:
            out.append({"dec_min":c["dec"],"dir":c["dir"],"members":[c]})
    for cl in out:
        assert cl["dec_min"]==max(m["dec"] for m in cl["members"]), "cluster minute precedes a member"
    return sorted(out,key=lambda x:x["dec_min"])
if __name__=="__main__":
    day=sys.argv[1]; win=sys.argv[2] if len(sys.argv)>2 else "ALL"
    cl=cluster(collect(day))
    lo,hi=(0,1440) if win=="ALL" else WIN[win]
    for c in cl:
        if not (lo<=c["dec_min"]<=hi): continue
        hh,mm=divmod(c["dec_min"],60)
        srcs=sorted({m["src"] for m in c["members"]})
        print(f"{hh:02d}:{mm:02d} {c['dir']:<4} n={len(c['members'])} {'+'.join(srcs)}")
        for m in c["members"]:
            if m["src"]=="two_level":
                print(f"        {m['start']} {m['tf']}m {m['shape']:<18} O{m['open']} C{m['close']} {m['levels']} rej={m['rejected']}")
            else:
                print(f"        {m['start']} {m['tf']}m rejection-first     C{m['close']} ma={m['own_ma']} vol={m['vol']} rej[{m['rejected_detail']}] 2nd={m['second']}")
