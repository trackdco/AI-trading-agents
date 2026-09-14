"""Pre-deploy check on the static export in ./out.

Run `npm run build` first, then `python3 scripts/check-site.py`. Exits non-zero if
anything fails, so it can gate a deploy.

Each check exists because the thing it looks for actually went wrong once:
og:image was missing from 29 of 30 pages because a page's openGraph object
replaces the layout's rather than merging with it; a markdown heading was pasted
into a page's body and rendered as "## ..." to visitors; and a price typed by
hand in one file drifted from lib/pricing.ts in another.
"""
import json, os, re, sys, glob
from html import unescape

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "out")
if not os.path.isdir(OUT):
    sys.exit("no ./out — run `npm run build` first")

def pages():
    for p in sorted(glob.glob(f"{OUT}/**/index.html", recursive=True)):
        r = "/" + os.path.relpath(os.path.dirname(p), OUT).replace(os.sep, "/")
        if "404" in r or "_not-found" in r:
            continue
        yield ("/" if r == "/." else r + "/"), p

ROUTES = {r for r, _ in pages()}
fails = []
def check(name, bad, note=""):
    print(f"  {'PASS' if not bad else 'FAIL'}  {name}" + (f"  {list(bad)[:4]}" if bad else ""))
    if bad:
        fails.append(name + (f" — {note}" if note else ""))

bad_links, no_slash, meta_bad, og_missing, ld_bad, md_leak = [], [], [], [], [], []
titles, descs = [], []
for r, p in pages():
    h = open(p, encoding="utf-8").read()
    titles.append(unescape(re.search(r"<title>(.*?)</title>", h, re.S).group(1)))
    descs.append(unescape(re.search(r'<meta name="description" content="([^"]*)"', h).group(1)))
    if len(titles[-1]) > 60 or not (70 <= len(descs[-1]) <= 160):
        meta_bad.append(r)
    if len(re.findall(r"<h1[^>]*>", h)) != 1:
        meta_bad.append(r + " (h1 count)")
    if not re.search(r'property="og:image"', h):
        og_missing.append(r)
    for href in set(re.findall(r'href="(/[^"#?]*)"', h)):
        if href.startswith("/_next/") or re.search(r"\.\w{2,5}$", href):
            continue
        (no_slash if not href.endswith("/") else bad_links if href not in ROUTES else []).append((r, href))
    for bl in re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S):
        try:
            json.loads(bl)
        except Exception:
            ld_bad.append(r)
    # Markdown that leaked into copy instead of being rendered.
    body = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", " ", h, flags=re.S)
    text = re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", body)))
    if re.search(r"(?:^|\s)(?:#{2,}\s+\w|\*\*\w|\[object Object\]|Lorem ipsum)", text):
        md_leak.append(r)

sitemap = set(re.findall(r"<loc>https://www\.imperiumdetailing\.com\.au(/[^<]*)</loc>", open(f"{OUT}/sitemap.xml").read()))
manifest = json.load(open(f"{ROOT}/lib/image-manifest.json"))
missing_img = [f"{n}-{w}.webp" for n, m in manifest.items() for w in m["variants"]
               if not os.path.exists(f"{ROOT}/public/images/{n}-{w}.webp")]

print(f"\n{len(ROUTES)} routes exported\n")
check("no broken internal links", bad_links)
check("every internal link keeps its trailing slash", no_slash, "trailingSlash is on, so /foo costs a redirect hop")
check("title <=60, description 70-160, exactly one h1", meta_bad)
check("titles unique", [] if len(titles) == len(set(titles)) else ["duplicates"])
check("descriptions unique", [] if len(descs) == len(set(descs)) else ["duplicates"])
check("og:image on every page", og_missing, "a page setting openGraph replaces the layout's; use og() from lib/seo")
check("every JSON-LD block parses", ld_bad)
check("no markdown or placeholders in rendered copy", md_leak)
check("sitemap matches the exported routes", sorted(ROUTES ^ sitemap))
check("every manifest image is on disk", missing_img)

print()
if fails:
    print(f"{len(fails)} check(s) failed:")
    for f in fails:
        print("  -", f)
    sys.exit(1)
print("all checks passed")
