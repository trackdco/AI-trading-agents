# Crossroads Christian Church — site remake

A from-scratch rebuild of [crossroads.org.au](https://crossroads.org.au): 50 pages,
plain HTML, no framework, no build step needed to deploy.

    index.html, <page>/index.html   the site, generated — deploy these
    build.py                        turns the content into the pages
    data.py                         the facts: services, addresses, people, links
    content_a.py, content_b.py      every page's words and sections
    styles.css, site.js             the look, and the little script it needs
    assets/img, assets/fonts        photos (their own, converted to webp), the font
    vercel.json                     clean URLs, redirects from the old addresses, cache headers

**Every word and photo is Crossroads' own**, taken from the current site, tidied
and re-set. Nothing about the church was invented. The four services, times,
venues, staff, council, beliefs, giving details, dates and forms are as published
on the old site in September 2026.

---

## The idea

The church is named for a crossing of roads, and it is one church that meets on
four roads across Canberra. So the site is built like a road.

- **The hero** is one photograph of Canberra with the colour taken out, and the
  roads put back in their brand yellow. Two roads draw themselves on when the
  page opens, and the four Sunday services sit at the four ends: mornings at the
  top, evenings at the bottom. This is the only thing on the site that moves on
  its own.
- **Yellow is road paint.** It draws the road line down the left margin, marks
  each section as a junction on it, dashes the top of the Sunday cards, and
  fills the one button that matters. It is never used as text on white.
- **The road line is drawn by scrolling**, not by time: it lengthens as you
  travel down the page (CSS scroll-driven animation, static in browsers that
  lack it).
- **Moving between pages** keeps the header and the road where they are while
  the page changes underneath (cross-document view transitions). Tap a service
  on the home page and the photo you tapped becomes the photo you arrive on.
- **One typeface**, Bricolage Grotesque, self-hosted, using its optical-size and
  width axes so the big headlines and the small print come from the same family.
- Plain words, sentence case, no labels in capitals, and the times set biggest
  because that is what a visitor actually needs.
- `prefers-reduced-motion` turns all of it off: the roads are simply there.
- Text contrast is AA or better on every pairing; 44px targets; keyboard focus
  is visible everywhere; the four hero links are real links.

## Putting it up

Plain static files, so any host works. On Vercel: **Add New → Project** →
import the repo → set **Root Directory** to `crossroads` → Deploy. That's it.
`vercel.json` already handles clean URLs, the redirects from every old page
address, and long caching for `/assets`.

To point `crossroads.org.au` at it, add the domain in the Vercel project and
change the DNS where the domain is registered. **Do that only once the church
has seen it and said yes** — it is their name and their site.

## Changing things

Edit the Python, then run:

    python3 build.py

It rewrites every page and checks that every internal link and image exists.
Python 3 is all it needs. (With Pillow installed it also writes responsive
`srcset`s; without it the pages still build.)

- A time, venue, email, staff member, council member, partner, podcast episode
  or story: `data.py`.
- Words on a page, or a new page: `content_a.py` / `content_b.py`. A page is a
  list of sections, and each section is one block type: `prose`, `split`,
  `facts`, `cards`, `people`, `video`, `videos`, `embed`, `links`, `timeline`,
  `beliefs`, `dates`, `form`, `band`, `notice`, `address`, `services`,
  `stories`, `partners`, `sermons`, `episodes`.
- Colours, type, layout: `styles.css` (the tokens are at the top).

## What is wired to what

- **Sermons, stories, podcast episodes** play from Crossroads' existing
  Subsplash media library; **videos** from their Vimeo. Nothing loads from
  those services until someone presses play.
- **Connect Cards, kids and youth visitor registration** go to their existing
  Google Forms. **Partnership, newsletters and safe ministry** go to their
  existing Elvanto forms. **Reports, events and venue hire** go to their
  existing Jotform forms. **Giving** goes to GiveNow and their bank details.
- **The five forms the old site handled itself** (contact, Jesus on Life,
  Crosstrain, serve, giving questions, and "ask us anything") are built as real
  forms that open the visitor's mail app with the answers filled in and
  addressed to the office. That works everywhere with no backend. To have them
  submit silently instead, give the `<form>` a Formspree or Elvanto action in
  `b_form()` in `build.py` — one line.

## Things to finish with the church

1. **Photos for North and Belconnen.** The only photos of those two services on
   the old site are 550 pixels wide. They are used small, but sharper originals
   would let them go big.
2. **The events calendar.** The old site embedded a calendar from its page
   builder. This site says what happens when in words, and sends people to a
   Connect Card for the next date. If they want a live calendar, Elvanto can
   publish one to embed.
3. **Check the dates.** Crosstrain Semester 2 and the DivorceCare start date are
   as the old site listed them; they will need updating each term.
4. **Analytics.** The old site had Google Analytics and a Facebook pixel. None
   is included here; add a tag to `head_html()` in `build.py` if wanted.
