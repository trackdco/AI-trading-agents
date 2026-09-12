"""Turn the static export in ./out into a copy that works from any folder on any static host.

Usage:  python3 scripts/preview-export.py <output-folder>

Next.js writes root-relative paths (/_next/..., /images/...), which only work when the site is
served from the root of a domain. Hosts that serve a folder (the claude.ai artifact host, a
GitHub Pages project page, a shared preview link) need relative paths, so this rewrites every
page and points the Turbopack runtime at the relative chunk base. Output: <output-folder>/site/
plus a small redirect page at <output-folder>/index.html.
"""
import re, os, shutil, glob, json, sys, time
BUILD_ID=time.strftime('%Y%m%d%H%M%S')
SRC=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'out')
DST=sys.argv[1]
if os.path.exists(DST): shutil.rmtree(DST)
os.makedirs(f'{DST}/site')
for d in ['_next','images','media','brand']:
    shutil.copytree(f'{SRC}/{d}', f'{DST}/site/{d}')
# Client components (hero video sources, header logo) build a few asset paths in JS at runtime.
# Point those at the site root, which each page defines as self.__ART before any chunk loads.
for js in glob.glob(f'{DST}/site/_next/static/chunks/*.js'):
    t=open(js, encoding='utf-8').read()
    u=re.sub(r'"/(media|brand|images)/', r'self.__ART+"/\1/', t)
    # the artifact host refuses text files containing a literal U+FFFD; the bundle only has it inside
    # string literals of a UTF-8 decoder, where the escape sequence means exactly the same thing
    u=u.replace('"\ufffd"', '"\\ufffd"')
    if u!=t: open(js,'w',encoding='utf-8').write(u); print('patched', os.path.basename(js), t.count('"/media/')+t.count('"/brand/'), 'literals')
ASSET=re.compile(r'(?<=["\'(,\s])/(_next|images|media|brand)/')
ROUTE=re.compile(r'(?<=["\'])/((?:services|service-areas|learn|reviews|book|warranty|privacy|terms|car-detailing-canberra)/(?:[A-Za-z0-9-]+/)?)(?=["\'#?\\])')
HOME=re.compile(r'(?<=["\'])/(?=["\'#\\])')

def click_script(prefix):
    # Client components (header nav) carry root-relative hrefs in their JS, so the Next router would
    # navigate to paths the preview host doesn't have. Route every internal click to the relative file.
    return ('<script>(function(){var P=%r;var V=%r;var R=/^\\/(services|service-areas|learn|reviews|book|warranty|privacy|terms|car-detailing-canberra)\\/([A-Za-z0-9-]+\\/)?$/;'
      'function map(h){var hash=h.indexOf("#")>=0?h.slice(h.indexOf("#")):"";var path=h.split("#")[0].split("?")[0];'
      'if(path==="/")return P+"index.html"+hash;if(R.test(path))return P+path.slice(1)+"index.html"+hash;return null;}'
      'document.addEventListener("click",function(e){if(e.defaultPrevented||e.button!==0||e.metaKey||e.ctrlKey||e.shiftKey||e.altKey)return;'
      'var a=e.target&&e.target.closest?e.target.closest("a[href]"):null;if(!a)return;var h=a.getAttribute("href")||"";var t=null;'
      'if(h.charAt(0)==="/"&&h.charAt(1)!=="/"){t=map(h);if(!t)return;}else if(/^(\\.\\.?\\/|index\\.html|[a-z-]+\\/)/.test(h)){t=h;}else return;'
      'e.preventDefault();e.stopImmediatePropagation();var u=new URL(t,document.baseURI);u.searchParams.set("v",V);'
      'if(u.pathname===location.pathname&&u.hash){location.hash=u.hash;return;}location.assign(u.href);},true);})();</script>') % (prefix, BUILD_ID)

pages=[]
for path in glob.glob(f'{SRC}/**/index.html', recursive=True):
    rel=os.path.relpath(path, SRC)
    if rel.startswith('_not-found'): continue
    depth=rel.count('/')
    prefix='../'*depth
    s=open(path, encoding='utf-8').read()
    s=ASSET.sub(lambda m: f'{prefix}{m.group(1)}/', s)
    s=ROUTE.sub(lambda m: f'{prefix}{m.group(1)}index.html', s)
    s=HOME.sub(f'{prefix}index.html', s)
    # must equal the prefix used in the <script src> attributes, as a plain string (the runtime compares raw attributes)
    base=f'<script>var TURBOPACK_CHUNK_BASE_PATH="{prefix}_next/";self.__ART=new URL("{prefix}./",document.baseURI).href.replace(/\\/$/,"");</script>'+click_script(prefix)
    # if the host ever wraps a page in its own skeleton, its unlayered reset would beat Tailwind's base layer
    guard='<style>html{color-scheme:dark}body{margin:0;background:#050608;color:#f3f5f8;font-family:var(--font-instrument),"Instrument Sans",system-ui,sans-serif;font-size:17px;line-height:1.55}</style>'
    s=s.replace('<head>', '<head>'+guard+base, 1)
    if depth==0:
        s=re.sub(r'<title>[^<]*</title>', '<title>Imperium Detailing</title>', s, count=1)
    out=f'{DST}/site/{rel}'
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out,'w',encoding='utf-8').write(s)
    pages.append(rel)
# The artifact host keeps its own runtime on the main page (that's how it pushes republishes
# to open viewers), so the main page must stay put: it frames the site on desktop and only
# redirects on touch screens, where nested frames scroll badly. Every inner URL carries the
# build id so no browser can serve an old page from cache.
open(f'{DST}/index.html','w',encoding='utf-8').write(
    '<title>Imperium Detailing</title>'
    '<style>html,body{height:100%;margin:0;background:#050608}'
    '.frame{position:fixed;inset:0;width:100%;height:100%;border:0;background:#050608}'
    '.open{position:fixed;right:12px;bottom:12px;z-index:2;font:500 13px system-ui,sans-serif;color:#f3f5f8;'
    'background:rgba(12,15,20,.85);border:1px solid rgba(194,200,208,.25);border-radius:999px;padding:8px 12px;'
    'text-decoration:none;backdrop-filter:blur(8px)}.open:hover{border-color:rgba(194,200,208,.6)}</style>'
    f'<script>if(matchMedia("(pointer: coarse)").matches){{location.replace(new URL("site/index.html?v={BUILD_ID}",document.baseURI).href);}}</script>'
    f'<iframe class="frame" src="site/index.html?v={BUILD_ID}" title="Imperium Detailing website" allow="autoplay; fullscreen"></iframe>'
    f'<a class="open" href="site/index.html?v={BUILD_ID}" target="_blank" rel="noopener">Open full screen</a>')
files=[]
for root,_,fs in os.walk(DST):
    for f in fs:
        r=os.path.relpath(os.path.join(root,f), DST)
        if r!='index.html': files.append(r)
json.dump(sorted(files), open(f'{DST}.files.json','w'))
print(len(pages),'pages;',len(files),'support files; manifest:',f'{DST}.files.json')
