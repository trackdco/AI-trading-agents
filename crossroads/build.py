#!/usr/bin/env python3
"""Builds the Crossroads site.

    python3 build.py

Reads the pages in content_a.py and content_b.py, the shared facts in
data.py, and writes plain HTML into this folder: index.html at the root and
<slug>/index.html for everything else. No dependencies beyond Python 3.
If Pillow is installed the build also reads image sizes to write srcsets;
without it the pages still build, just with a single image size each.
"""
import html
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import data as D  # noqa: E402
from content_a import PAGES as PAGES_A  # noqa: E402
from content_b import PAGES as PAGES_B  # noqa: E402

ROOT = Path(__file__).parent
IMG = ROOT / "assets" / "img"
YEAR = "2026"

# ---------------------------------------------------------------- images
_sizes = {}
try:
    from PIL import Image  # type: ignore
    for p in IMG.rglob("*.webp"):
        with Image.open(p) as im:
            _sizes[str(p.relative_to(IMG)).replace(os.sep, "/")] = im.size[0]
except Exception:  # Pillow missing: no srcsets, still builds
    pass

def esc(s):
    return html.escape(str(s), quote=True)

def variants(name):
    """All files for an image name: 'hero' -> [('hero-2400.webp', 2400), ...]."""
    out = []
    base = IMG / name
    if base.with_suffix(".webp").exists():
        rel = f"{name}.webp"
        out.append((rel, _sizes.get(rel, 0)))
    for p in sorted(base.parent.glob(f"{base.name}-*.webp")):
        m = re.fullmatch(rf"{re.escape(base.name)}-(\d+)\.webp", p.name)
        if m:
            rel = str(p.relative_to(IMG)).replace(os.sep, "/")
            out.append((rel, _sizes.get(rel, int(m.group(1)))))
    return out

def img(name, alt="", sizes="100vw", cls="", loading="lazy", attrs=""):
    vs = variants(name)
    if not vs:
        raise SystemExit(f"missing image: {name}")
    vs.sort(key=lambda v: v[1])
    src = f"/assets/img/{vs[-1][0]}"
    srcset = ", ".join(f"/assets/img/{f} {w}w" for f, w in vs if w) if len(vs) > 1 else ""
    a = [f'src="{src}"']
    if srcset:
        a.append(f'srcset="{srcset}" sizes="{sizes}"')
    w = vs[-1][1]
    if w:
        a.append(f'width="{w}"')
    a.append(f'alt="{esc(alt)}"')
    if loading:
        a.append(f'loading="{loading}" decoding="async"')
    if cls:
        a.append(f'class="{cls}"')
    if attrs:
        a.append(attrs)
    return f"<img {' '.join(a)}>"

# ---------------------------------------------------------------- small parts
ARROW = '<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M4 10h11m-4-4 4 4-4 4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'
PLAY = '<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M5 3.5v13l11-6.5z" fill="currentColor"/></svg>'
FB = '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M13.5 22v-8h2.7l.4-3.2h-3.1V8.8c0-.9.3-1.6 1.6-1.6h1.7V4.4c-.3 0-1.3-.1-2.5-.1-2.5 0-4.1 1.5-4.1 4.2v2.3H7.4V14h2.8v8z"/></svg>'
IG = '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="1.8" d="M7.5 3h9A4.5 4.5 0 0 1 21 7.5v9a4.5 4.5 0 0 1-4.5 4.5h-9A4.5 4.5 0 0 1 3 16.5v-9A4.5 4.5 0 0 1 7.5 3z"/><circle cx="12" cy="12" r="3.8" fill="none" stroke="currentColor" stroke-width="1.8"/><circle cx="17.3" cy="6.7" r="1.1" fill="currentColor"/></svg>'

def ext(href):
    return href.startswith("http") or href.startswith("mailto:")

def a(href, label, cls="", extra=""):
    rel = ' rel="noopener"' if href.startswith("http") else ""
    c = f' class="{cls}"' if cls else ""
    return f'<a href="{esc(href)}"{c}{rel}{extra}>{label}</a>'

def btn(href, label, kind=""):
    cls = "btn" + (f" {kind}" if kind else "")
    return a(href, f"{label}", cls)

def video(vid, title, dur="", wide=False):
    poster = f"posters/{vid}"
    src = f"https://player.vimeo.com/video/{vid}?autoplay=1&dnt=1"
    small = f"<small>{esc(dur)}</small>" if dur else ""
    return (f'<div class="video{" wide" if wide else ""}">'
            f'{img(poster, "", "(min-width: 900px) 50vw, 100vw")}'
            f'<button class="play" type="button" data-src="{esc(src)}" data-title="{esc(title)}">'
            f'<span class="t">{esc(title)}{small}</span><span class="disc">{PLAY}</span></button></div>')

def embed(src, title, button, note="", tall=False, bg=None):
    if bg:
        return (f'<div class="embed{" tall" if tall else ""}"><div class="frame"><div class="load on-photo">'
                f'{img(bg, "", "(min-width: 900px) 50vw, 100vw")}<h3>{esc(title)}</h3><p>{note}</p>'
                f'<button class="btn" type="button" data-src="{esc(src)}" data-title="{esc(title)}">{esc(button)}</button>'
                f'</div></div></div>')
    return (f'<div class="embed{" tall" if tall else ""}"><div class="frame"><div class="load">'
            f'<p>{note}</p><button class="btn ink" type="button" data-src="{esc(src)}" data-title="{esc(title)}">{esc(button)}</button>'
            f'</div></div></div>')

def subsplash(media_id):
    return f"https://subsplash.com/u/-KQBRDK/media/embed/d/{media_id}?&info=0"

# ---------------------------------------------------------------- blocks
def b_prose(d, o):
    return f'<div class="prose">{d}</div>'

def b_raw(d, o):
    return d

def b_split(d, o):
    fig = (f'<figure class="split-media{" tall" if d.get("tall") else ""}">'
           f'{img(d["img"], d.get("alt", ""), "(min-width: 860px) 50vw, 100vw")}'
           + (f'<figcaption>{d["cap"]}</figcaption>' if d.get("cap") else "") + "</figure>")
    body = f'<div class="prose">{d["html"]}</div>'
    cls = "split rev" if d.get("rev") else "split"
    return f'<div class="{cls}">{fig}{body}</div>'

def b_facts(d, o):
    rows = "".join(f"<div><dt>{esc(k)}</dt><dd>{v}</dd></div>" for k, v in d)
    return f'<dl class="facts">{rows}</dl>'

def b_cards(d, o):
    cls = "cards" + (" three" if o.get("three") else "")
    out = []
    for c in d:
        pic = img(c["img"], c.get("alt", ""), "(min-width: 900px) 33vw, 100vw") if c.get("img") else ""
        when = f'<p class="when">{esc(c["when"])}</p>' if c.get("when") else ""
        go = f'<span class="go">{esc(c.get("go", "Find out more"))}</span>' if c.get("href") else ""
        body = f'<div class="card-body"><h3>{esc(c["title"])}</h3>{when}<p>{c.get("text", "")}</p>{go}</div>'
        kind = "card plain" if o.get("plain") else "card"
        if c.get("href"):
            out.append(a(c["href"], pic + body, kind))
        else:
            out.append(f'<div class="{kind}">{pic}{body}</div>')
    return f'<div class="{cls}">{"".join(out)}</div>'

def b_people(d, o):
    out = []
    for p in d:
        name, role, im, email = p[0], p[1], p[2], (p[3] if len(p) > 3 else None)
        bio = p[4] if len(p) > 4 else None
        folder = o.get("folder", "staff")
        pic = img(f"{folder}/{im}", f"{name}", "(min-width: 900px) 20vw, 50vw") if im else ""
        mail = f'<p>{a("mailto:" + email, "Email " + esc(name.split()[0]))}</p>' if email else ""
        b = f'<p class="bio">{esc(bio)}</p>' if bio else ""
        out.append(f'<div class="person">{pic}<h3>{esc(name)}</h3><p>{esc(role)}</p>{b}{mail}</div>')
    return f'<div class="people{" wide" if o.get("wide") else ""}">{"".join(out)}</div>'

def b_video(d, o):
    vid, title, dur = d
    return video(vid, title, dur, wide=True)

def b_videos(d, o):
    return f'<div class="videos">{"".join(video(v, t, du) for v, t, du in d)}</div>'

def b_embed(d, o):
    return embed(d["src"], d["title"], d["button"], d.get("note", ""), d.get("tall", False))

def b_links(d, o):
    items = []
    for row in d:
        label, href = row[0], row[1]
        meta = row[2] if len(row) > 2 else ("Opens on another site" if href.startswith("http") else "")
        if href.startswith("mailto:"):
            meta = meta or "Email"
        items.append(f'<li>{a(href, esc(label) + (f"<span>{esc(meta)}</span>" if meta else ""))}</li>')
    return f'<ul class="links">{"".join(items)}</ul>'

def b_timeline(d, o):
    return '<ol class="timeline">' + "".join(f"<li><time>{esc(t)}</time><p>{h}</p></li>" for t, h in d) + "</ol>"

def b_beliefs(d, o):
    return '<dl class="beliefs">' + "".join(f"<div><dt>{esc(t)}</dt><dd>{esc(x)}</dd></div>" for t, x in d) + "</dl>"

def b_dates(d, o):
    return '<ul class="dates">' + "".join(f"<li>{esc(x)}</li>" for x in d) + "</ul>"

def b_form(d, o):
    fields = []
    for f in d["fields"]:
        name, label, kind = f[0], f[1], f[2]
        req = " required" if (len(f) > 3 and f[3]) else ""
        if kind == "textarea":
            fields.append(f'<label><span>{esc(label)}</span><textarea name="{name}"{req}></textarea></label>')
        elif kind == "radios":
            opts = "".join(f'<label><input type="radio" name="{name}" value="{esc(v)}"{req}>{esc(v)}</label>' for v in f[4])
            fields.append(f'<fieldset><legend>{esc(label)}</legend><div class="radios">{opts}</div></fieldset>')
        else:
            auto = {"email": ' autocomplete="email"', "tel": ' autocomplete="tel"'}.get(kind, "")
            if name == "first":
                auto = ' autocomplete="given-name"'
            if name == "last":
                auto = ' autocomplete="family-name"'
            fields.append(f'<label><span>{esc(label)}</span><input type="{kind}" name="{name}"{auto}{req}></label>')
    note = d.get("note", "Pressing the button opens your mail app with this filled in, addressed to us. Nothing is sent until you press send there.")
    to = d["to"]
    return (f'<form class="form" method="post" action="mailto:{esc(to)}" data-mailto="{esc(to)}" data-subject="{esc(d["subject"])}">'
            + "".join(fields)
            + f'<p class="note">{note} If the button does nothing, email {a("mailto:" + to, esc(to))}.</p>'
            + f'<p><button class="btn" type="submit">{esc(d.get("submit", "Send"))}</button></p>'
            + '<p class="sent" hidden tabindex="-1">Your mail app should now be open with your message. Press send there and we will be in touch.</p>'
            + "</form>")

def b_band(d, o):
    inner = f'<div><h2>{d["h2"]}</h2><p class="lede">{d["html"]}</p></div>'
    if d.get("href"):
        inner += f'<div>{btn(d["href"], d["label"], d.get("kind", ""))}</div>'
    return f'<div class="wrap">{inner}</div>'

def b_notice(d, o):
    return f'<div class="notice">{d}</div>'

def b_address(d, o):
    c = D.CENTRE
    out = (f'<div class="split"><div class="prose"><address class="address"><strong>{esc(c["name"])}</strong>'
           f'<span>{esc(c["line1"])}</span><span>{esc(c["line2"])}</span><span class="muted">{esc(c["note"])}</span></address>'
           f'<div class="map-links">{btn(c["maps"], "Open in Google Maps", "ghost")}{btn("mailto:" + D.OFFICE_EMAIL, "Email the office", "ghost")}</div>'
           f'{d.get("html", "")}</div>'
           f'<figure class="split-media">{img("parking-map", "Map of parking around the Crossroads Ministry Centre: Westfield car parks and street parking on Chandler Street, with the entrance off Margaret Timpson Park", "(min-width: 860px) 50vw, 100vw")}'
           f'<figcaption>Where to park on Friday nights and Sundays.</figcaption></figure></div>')
    return out

def b_partners(d, o):
    out = []
    for s in D.SERVICES:
        cards = "".join(
            f'<figure class="partner">{img("partners/" + im, alt, "(min-width: 900px) 25vw, 50vw")}<figcaption>{esc(alt)}</figcaption></figure>'
            for im, alt in D.PARTNERS[s["slug"]])
        out.append(f'<div class="sub"><h3>{esc(s["full"])}</h3><div class="partners">{cards}</div></div>')
    return "".join(out)

def b_stories(d, o):
    out = []
    for slug, name, where, media, blurb, im in d:
        out.append(f'<a class="story" href="/stories/{slug}/">'
                   f'<div class="video">{img(im, "", "(min-width: 900px) 33vw, 100vw")}<span class="play"><span class="t">{esc(name)}<small>{esc(where)}</small></span><span class="disc">{PLAY}</span></span></div>'
                   f'</a>')
    return f'<div class="stories">{"".join(out)}</div>'

def b_services(d, o):
    return svc_cards()


def b_sermons(d, o):
    lib = embed(D.SERMON_LIBRARY, "The sermon library", "Open the sermon library",
                "Talks from all four services, newest first. Loads from Crossroads’ media library when you press the button.", tall=True, bg="hall")
    yt = (f'<div class="video">{img("preach-2", "", "(min-width: 900px) 50vw, 100vw")}'
          f'<button class="play" type="button" data-src="{esc(D.SERMON_VIDEO)}" data-title="Watch a Crossroads sermon">'
          f'<span class="t">Watch a sermon<small>From YouTube</small></span><span class="disc">{PLAY}</span></button></div>')
    pods = ('<ul class="links">'
            f'<li>{a(D.APPLE_PODCASTS, "Sermons on Apple Podcasts<span>Subscribe</span>")}</li>'
            f'<li>{a(D.SPOTIFY, "Sermons on Spotify<span>Subscribe</span>")}</li>'
            f'<li>{a("/word-to-life/", "Word to Life, our podcast<span>Beyond Sunday</span>")}</li></ul>')
    return f'<div class="split"><div>{lib}</div><div style="display:grid;gap:24px">{yt}{pods}</div></div>'

def b_episodes(d, o):
    items = []
    for title, date, hosts, media in d:
        src = subsplash(media)
        items.append(f'<li class="ep"><div class="ep-row"><div><h3>{esc(title)}</h3><p class="muted">{esc(date)} · {esc(hosts)}</p></div>'
                     f'<button class="btn ghost" type="button" data-src="{esc(src)}" data-title="{esc(title)}">Play</button></div>'
                     f'<div class="embed"><div class="frame ep-frame" hidden></div></div></li>')
    return f'<ol class="episodes">{"".join(items)}</ol>'

def b_reviews(d, o):
    items = "".join(
        f'<figure class="review"><blockquote>“{esc(q)}”</blockquote><figcaption>{esc(n)}<span>{esc(m)}</span></figcaption></figure>'
        for q, n, m in d)
    return f'<div class="reviews">{items}</div><p class="muted reviews-note">From public Google reviews of Crossroads.</p>'

BLOCKS = {k[2:]: v for k, v in globals().items() if k.startswith("b_")}

def svc_cards():
    out = []
    for s in D.SERVICES:
        pic = img(s["img"], f"{s['full']} meeting at {s['venue']}", "(min-width: 1000px) 25vw, (min-width: 600px) 50vw, 100vw", attrs=f'style="view-transition-name: svc-{s["slug"]}"')
        out.append(f'<a class="svc" href="/sundays/{s["slug"]}/">{pic}<div class="svc-body">'
                   f'<span class="svc-time">{s["time"]}<small>{s["ampm"]}</small></span>'
                   f'<h3>{esc(s["full"])}</h3><p>{esc(s["venue"])}<br>{esc(s["addr"])}</p>'
                   f'<span class="svc-more">Plan a visit</span></div></a>')
    return f'<div class="svcs">{"".join(out)}</div>'

# ---------------------------------------------------------------- chrome
def head_html(p):
    title = p["title"] if p["slug"] == "" else f'{p["title"]} · {D.SITE_SHORT}'
    desc = p.get("desc", D.TAGLINE)
    url = D.BASE_URL + ("/" if p["slug"] == "" else f"/{p['slug']}/")
    share = p.get("share", "share.jpg")
    return f"""<!doctype html>
<html lang="en-AU">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{esc(url)}">
<meta property="og:site_name" content="{esc(D.SITE)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{esc(url)}">
<meta property="og:image" content="{D.BASE_URL}/assets/img/{share}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#1B1A17">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/assets/img/icon-192.png" sizes="192x192" type="image/png">
<link rel="apple-touch-icon" href="/assets/img/apple-touch-icon.png">
<link rel="manifest" href="/manifest.webmanifest">
<link rel="preload" href="/assets/fonts/bricolage-grotesque.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/styles.css">
<script>document.documentElement.classList.add(matchMedia('(prefers-reduced-motion: reduce)').matches?'no-motion':'has-motion')</script>
{p.get("head_extra", "")}
</head>"""

def header_html(p):
    home = p["slug"] == ""
    on_dark = " on-dark" if p.get("dark_head", home) else ""
    solid = "" if p.get("dark_head", home) else " always-solid"
    links = "".join(a(h, esc(l)) for l, h in D.NAV)
    cta = a("/giving/", "Give", "give") + btn(D.CTA[1], D.CTA[0])
    menu_groups = "".join(
        f'<div class="menu-group"><h2>{esc(g)}</h2><ul>' + "".join(f"<li>{a(h, esc(l))}</li>" for l, h in items) + "</ul></div>"
        for g, items in D.MENU)
    return f"""<a class="skip" href="#main">Skip to content</a>
<div class="road" aria-hidden="true"></div>
<header class="site-head{on_dark}{solid}">
  <div class="wrap">
    <a class="brand" href="/" aria-label="Crossroads Christian Church, home">
      <img class="logo-dark" src="/assets/img/logo-ink.png" width="499" height="156" alt="">
      <img class="logo-light" src="/assets/img/logo-white.png" width="499" height="156" alt="">
    </a>
    <nav class="site-nav" aria-label="Main">{links}</nav>
    {cta}
    <button class="menu-btn" type="button" aria-expanded="false" aria-controls="menu"><span class="label">Menu</span><span class="bars" aria-hidden="true"><i></i><i></i></span></button>
  </div>
</header>
<nav class="menu" id="menu" hidden aria-label="All pages">
  {menu_groups}
  <div class="menu-group small"><ul><li>{a(D.GIVENOW, "Give online")}</li><li>{a(D.ELVANTO, "Elvanto login")}</li></ul></div>
  <p class="menu-foot">{esc(D.CENTRE["name"])}, {esc(D.CENTRE["line1"])}, {esc(D.CENTRE["line2"])} · {a("mailto:" + D.OFFICE_EMAIL, esc(D.OFFICE_EMAIL))}</p>
</nav>"""

def footer_html():
    svcs = "".join(
        f'<li class="svc-line"><a href="/sundays/{s["slug"]}/"><b>{s["time"]}{s["ampm"]}</b>{esc(s["full"])}<small>{esc(s["venue"])}, {esc(s["addr"].split(",")[0] if s["slug"] != "lake-g" else "Belconnen")}</small></a></li>'
        for s in D.SERVICES)
    col2 = "".join(f"<li>{a(h, esc(l))}</li>" for l, h in [
        ("I'm new", "/im-new/"), ("Kids", "/kids/"), ("Youth", "/youth/"), ("Growth groups", "/growth-groups/"),
        ("Jesus on Life", "/jesus-on-life/"), ("Serve", "/serving/"), ("Give", "/giving/"), ("Apps", "/apps/")])
    col3 = "".join(f"<li>{a(h, esc(l))}</li>" for l, h in [
        ("Who we are", "/who-we-are/"), ("What we believe", "/what-we-believe/"), ("Stories", "/stories/"),
        ("Sermons", "/sermons/"), ("Policies and safe ministry", "/policies/"), ("Employment", "/employment/"),
        ("Events and venue hire", "/events/"), ("Contact", "/contact/")])
    c = D.CENTRE
    return f"""<footer class="site-foot">
  <div class="wrap">
    <div class="cols">
      <div class="brand-foot">
        <img src="/assets/img/logo-white.png" width="499" height="156" alt="Crossroads Christian Church">
        <address>
          <span>{esc(c["name"])}</span><span>{esc(c["line1"])}, {esc(c["line2"])}</span>
          <span>{a("mailto:" + D.OFFICE_EMAIL, esc(D.OFFICE_EMAIL))}</span>
        </address>
        <div class="socials">
          {a(D.FACEBOOK, FB, extra=' aria-label="Crossroads on Facebook"')}
          {a(D.INSTAGRAM, IG, extra=' aria-label="Crossroads on Instagram"')}
        </div>
      </div>
      <div><h2>Sundays</h2><ul>{svcs}</ul></div>
      <div><h2>Get involved</h2><ul>{col2}</ul></div>
      <div><h2>About</h2><ul>{col3}</ul></div>
    </div>
    <div class="base">
      <span>© {YEAR} Crossroads Christian Church Canberra. A member of the {a(D.FIEC, "Fellowship of Independent Evangelical Churches")}.</span>
      <span>{a("/all-pages/", "All pages")} · {a(D.ELVANTO, "Elvanto login")} · {a(D.GIVENOW, "Give online")}</span>
    </div>
  </div>
</footer>
<script src="/site.js" defer></script>
</body>
</html>"""

def section_html(sec, i):
    kind = sec["kind"]
    inner = BLOCKS[kind](sec.get("data"), sec)
    if kind == "band":
        cls = "band junction" + (" dark" if sec.get("dark", True) else " chalk")
        return f'<section class="{cls}">{inner}</section>'
    classes = ["sec", "junction"]
    if sec.get("dark"):
        classes.append("dark")
    if sec.get("chalk"):
        classes.append("chalk")
    if sec.get("tight"):
        classes.append("tight")
    head = ""
    if sec.get("title") or sec.get("lede"):
        hcls = "sec-head" + (" row" if sec.get("cta") else "")
        t = f'<h2>{sec["title"]}</h2>' if sec.get("title") else ""
        l = f'<p class="lede">{sec["lede"]}</p>' if sec.get("lede") else ""
        c = f'<div>{btn(sec["cta"][1], sec["cta"][0], "ghost")}</div>' if sec.get("cta") else ""
        head = f'<div class="{hcls}"><div>{t}{l}</div>{c}</div>'
    sid = f' id="{sec["id"]}"' if sec.get("id") else ""
    return f'<section class="{" ".join(classes)}"{sid}><div class="wrap">{head}{inner}</div></section>'

def page_html(p):
    crumb = f'<p class="crumb">{a(p["crumb"][1], esc(p["crumb"][0]))}</p>' if p.get("crumb") else ""
    lede = f'<p class="lede">{p["lede"]}</p>' if p.get("lede") else ""
    actions = ""
    if p.get("actions"):
        actions = '<p class="hero-cta">' + "".join(
            btn(h, l, k) for l, h, k in [(x[0], x[1], x[2] if len(x) > 2 else "") for x in p["actions"]]) + "</p>"
    photo = ""
    mode = p.get("head", "photo" if p.get("photo") else "plain")
    if p.get("photo"):
        vt = f' style="view-transition-name: {p["vt"]}"' if p.get("vt") else ""
        cap = f'<figcaption>{p["photo_cap"]}</figcaption>' if p.get("photo_cap") else ""
        photo = f'<figure class="page-photo">{img(p["photo"], p.get("photo_alt", ""), "(min-width: 1000px) 1200px, 100vw", loading="eager", attrs=vt.strip())}{cap}</figure>'
    head_cls = "page-head" + (f" {mode}" if mode != "plain" else "")
    inner = f'{crumb}<h1>{p.get("h1", p["title"])}</h1>{lede}{actions}'
    if mode == "side":
        header = f'<header class="{head_cls}"><div class="wrap">{inner}{photo}</div></header>'
    else:
        header = f'<header class="{head_cls}"><div class="wrap">{inner}</div>{("<div class=wrap>" + photo + "</div>") if photo else ""}</header>'
    body = "".join(section_html(s, i) for i, s in enumerate(p["sections"]))
    return (head_html(p) + "\n<body>\n" + header_html(p) + f'\n<main id="main">\n{header}\n{body}\n</main>\n' + footer_html())

# ---------------------------------------------------------------- home
def home_html(p):
    arms = []
    for s in D.SERVICES:
        arms.append(f'<li class="arm {s["pos"]}"><a href="/sundays/{s["slug"]}/"><b>{s["time"]}<small>{s["ampm"]}</small></b>'
                    f'<span>{esc(s["full"])}</span><small class="v">{esc(s["venue"])}</small></a></li>')
    cross = f"""<figure class="cross">
  <svg viewBox="0 0 600 600" focusable="false" aria-hidden="true">
    <defs><filter id="paint" x="-5%" y="-5%" width="110%" height="110%"><feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="2" seed="11" result="n"/><feDisplacementMap in="SourceGraphic" in2="n" scale="7" xChannelSelector="R" yChannelSelector="G"/></filter></defs>
    <g filter="url(#paint)">
      <path class="kerb k1" pathLength="1" d="M126 126 L474 474"/>
      <path class="kerb k2" pathLength="1" d="M474 126 L126 474"/>
      <path class="r r1" pathLength="1" d="M126 126 L474 474"/>
      <path class="r r2" pathLength="1" d="M474 126 L126 474"/>
    </g>
    <path class="c" d="M142 142 L458 458"/>
    <path class="c" d="M458 142 L142 458"/>
    <circle class="dot" cx="300" cy="300" r="9"/>
  </svg>
  <ul class="arms" aria-label="Sunday services">{"".join(arms)}</ul>
</figure>"""
    hero = f"""<section class="hero" aria-labelledby="hero-h">
  <div class="hero-bg">{img("hero", "", "100vw", loading="eager", attrs='fetchpriority="high"')}</div>
  <div class="hero-shade" aria-hidden="true"></div>
  <div class="wrap hero-grid">
    <div class="hero-copy">
      <h1 id="hero-h">Jesus, for all of Canberra.</h1>
      <p class="lede">One church, four Sunday services. <strong>9.30am</strong> in Braddon and Belconnen, <strong>6.30pm</strong> at ANU and in Belconnen. Come as you are.</p>
      <p class="hero-cta">{btn("/sundays/", "Find your Sunday")}<a class="link" href="/im-new/">What to expect</a></p>
    </div>
    {cross}
  </div>
</section>
<div id="top-sentinel" aria-hidden="true"></div>"""
    body = "".join(section_html(s, i) for i, s in enumerate(p["sections"]))
    return (head_html(p) + "\n<body class=\"home\">\n" + header_html(p) + f'\n<main id="main">\n{hero}\n{body}\n</main>\n' + footer_html())

# ---------------------------------------------------------------- build
def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

def all_pages_page():
    groups = "".join(
        f'<div class="sub"><h2>{esc(g)}</h2><ul class="links">' + "".join(f"<li>{a(h, esc(l))}</li>" for l, h in items) + "</ul></div>"
        for g, items in D.MENU)
    return dict(slug="all-pages", title="All pages", lede="Every page on this site, in one list.",
                desc="Every page on the Crossroads Christian Church Canberra website.",
                sections=[S_raw(f'<div class="wrap">{groups}</div>')])

def S_raw(html_):
    return dict(kind="raw", data=html_)

def build():
    pages = PAGES_A + PAGES_B + [all_pages_page()]
    slugs = {p["slug"] for p in pages}
    for p in pages:
        out = ROOT / "index.html" if p["slug"] == "" else ROOT / p["slug"] / "index.html"
        write(out, home_html(p) if p["slug"] == "" else page_html(p))
    # sitemap + robots
    urls = "".join(f"<url><loc>{D.BASE_URL}/{(s + '/') if s else ''}</loc></url>" for s in sorted(slugs))
    write(ROOT / "sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
    write(ROOT / "robots.txt", f"User-agent: *\nAllow: /\nSitemap: {D.BASE_URL}/sitemap.xml\n")
    # vercel.json: clean urls + redirects from the old site's addresses
    vercel = {
        "cleanUrls": True,
        "trailingSlash": True,
        "redirects": [{"source": k, "destination": v, "permanent": True} for k, v in D.REDIRECTS.items()],
        "headers": [
            {"source": "/assets/(.*)", "headers": [{"key": "Cache-Control", "value": "public, max-age=31536000, immutable"}]},
            {"source": "/(.*)", "headers": [
                {"key": "X-Content-Type-Options", "value": "nosniff"},
                {"key": "Referrer-Policy", "value": "strict-origin-when-cross-origin"},
                {"key": "Permissions-Policy", "value": "camera=(), microphone=(), geolocation=()"},
            ]},
        ],
    }
    write(ROOT / "vercel.json", json.dumps(vercel, indent=2) + "\n")
    # check every internal link points at a page or a file that exists
    bad = []
    for p in pages:
        out = ROOT / "index.html" if p["slug"] == "" else ROOT / p["slug"] / "index.html"
        text = out.read_text(encoding="utf-8")
        for href in re.findall(r'(?:href|src|srcset)="([^"]+)"', text):
            for h in href.split(","):
                h = h.strip().split(" ")[0].split("#")[0].split("?")[0]
                if not h.startswith("/"):
                    continue
                target = ROOT / h.lstrip("/")
                if h.endswith("/"):
                    target = target / "index.html"
                if not target.exists():
                    bad.append((p["slug"] or "/", h))
    if bad:
        for s, h in sorted(set(bad)):
            print(f"  broken link on /{s}: {h}")
        raise SystemExit(f"{len(set(bad))} broken links")
    print(f"built {len(pages)} pages")


# ---------------------------------------------------------------- portable copy
def portable(outdir):
    """Writes a copy of the built site with relative links, so it can be opened
    from a folder on a computer (double-click index.html) with no web server."""
    import shutil
    out = Path(outdir)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    shutil.copytree(ROOT / "assets", out / "assets")
    css = (ROOT / "styles.css").read_text(encoding="utf-8").replace('url("/assets/', 'url("assets/')
    (out / "styles.css").write_text(css, encoding="utf-8")
    shutil.copy(ROOT / "site.js", out / "site.js")
    shutil.copy(ROOT / "favicon.svg", out / "favicon.svg")

    def relink(html_text, depth):
        prefix = "../" * depth
        def fix(m):
            attr, path = m.group(1), m.group(2)
            if path == "/":
                return f'{attr}="{prefix}index.html"'
            if path.endswith("/"):
                return f'{attr}="{prefix}{path[1:]}index.html"'
            return f'{attr}="{prefix}{path[1:]}"'
        html_text = re.sub(r'\b(href|src|content)="(/[^"]*)"', lambda m: fix(m) if not m.group(2).startswith("//") else m.group(0), html_text)
        html_text = re.sub(r'<link rel="preload"[^>]*>\n', "", html_text)  # a font preload needs a web server
        html_text = re.sub(r'srcset="([^"]+)"', lambda m: 'srcset="' + ", ".join(
            (prefix + c.strip()[1:]) if c.strip().startswith("/") else c.strip() for c in m.group(1).split(",")) + '"', html_text)
        return html_text

    for p in ROOT.rglob("index.html"):
        rel = p.relative_to(ROOT)
        depth = len(rel.parts) - 1
        text = p.read_text(encoding="utf-8")
        (out / rel).parent.mkdir(parents=True, exist_ok=True)
        (out / rel).write_text(relink(text, depth), encoding="utf-8")
    print(f"portable copy in {out}")

if __name__ == "__main__":
    build()
    if len(sys.argv) > 2 and sys.argv[1] == "--portable":
        portable(sys.argv[2])
